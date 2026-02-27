"""Workflow CRUD + launch routes."""

import logging
import re

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from dcc.db import repository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


# --- Request models ---


class CreateWorkflowRequest(BaseModel):
    workspace_id: str
    name: str
    prompt_template: str
    description: str | None = None
    category: str = "custom"
    icon: str = "Workflow"
    parameters: list[dict] | None = None
    model: str | None = None


class UpdateWorkflowRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    icon: str | None = None
    prompt_template: str | None = None
    parameters: list[dict] | None = None
    model: str | None = None


class LaunchWorkflowRequest(BaseModel):
    workspace_id: str
    params: dict[str, str] = {}
    model: str | None = None


# --- Helpers ---


def resolve_prompt_template(template: str, context: dict[str, str]) -> str:
    """Reemplaza placeholders {{key}} con valores del contexto."""
    result = template
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", value)
    return result


# --- Endpoints ---


@router.get("")
async def list_workflows(
    workspace_id: str | None = None,
    category: str | None = None,
):
    """Listar workflows, opcionalmente filtrados por workspace y categoria."""
    workflows = await repository.get_workflows(
        workspace_id=workspace_id, category=category
    )
    return {"workflows": workflows}


@router.post("")
async def create_workflow(req: CreateWorkflowRequest):
    """Crear workflow custom."""
    ws = await repository.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    workflow_id = await repository.create_workflow(
        workspace_id=req.workspace_id,
        name=req.name,
        prompt_template=req.prompt_template,
        description=req.description,
        category=req.category,
        icon=req.icon,
        parameters=req.parameters,
        model=req.model,
    )
    return {"workflow_id": workflow_id}


@router.get("/categories")
async def list_categories():
    """Listar categorias de workflows."""
    return {
        "categories": [
            {"id": "development", "label": "Development"},
            {"id": "testing", "label": "Testing"},
            {"id": "review", "label": "Review"},
            {"id": "devops", "label": "DevOps"},
            {"id": "custom", "label": "Custom"},
        ]
    }


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Obtener workflow por ID."""
    wf = await repository.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow": wf}


@router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, req: UpdateWorkflowRequest):
    """Actualizar workflow (solo custom)."""
    wf = await repository.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    updates = req.model_dump(exclude_none=True)
    if not updates:
        return {"updated": False}

    await repository.update_workflow(workflow_id, **updates)
    return {"updated": True}


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Eliminar workflow (solo custom, builtin bloqueado)."""
    wf = await repository.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if wf["is_builtin"]:
        raise HTTPException(status_code=403, detail="Cannot delete built-in workflow")

    deleted = await repository.delete_workflow(workflow_id)
    return {"deleted": deleted}


@router.post("/{workflow_id}/launch")
async def launch_workflow(workflow_id: str, req: LaunchWorkflowRequest):
    """Lanzar workflow: resuelve template, crea session, retorna session_id."""
    wf = await repository.get_workflow(workflow_id)
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    ws = await repository.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # Validar parametros requeridos
    for param in wf["parameters"]:
        if param.get("required") and not req.params.get(param["key"]):
            # Usar default si existe
            if param.get("default"):
                req.params[param["key"]] = param["default"]
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required parameter: {param['key']}",
                )

    # Rellenar defaults para parametros no enviados
    for param in wf["parameters"]:
        if param["key"] not in req.params and param.get("default"):
            req.params[param["key"]] = param["default"]

    # Resolver prompt template
    prompt = resolve_prompt_template(wf["prompt_template"], req.params)

    # Usar modelo del workflow o del request
    model = req.model or wf.get("model")

    # Crear session con workflow_id
    session_id = await repository.create_session(
        workspace_id=req.workspace_id,
        prompt=prompt,
        model=model,
        workflow_id=workflow_id,
    )

    # Incrementar uso
    await repository.increment_workflow_usage(workflow_id)

    return {"session_id": session_id, "redirect": "/run"}


# --- Monitor tasks endpoint (bajo /api/sessions para coherencia) ---
# Este endpoint se registra en sessions.py via import
