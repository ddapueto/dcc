"""Pipeline CRUD + generation + execution routes."""

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from dcc.db import repository
from dcc.engine.agent_router import get_available_agents, suggest_agent
from dcc.engine.gh_client import GhError, gh_api
from dcc.engine.pipeline_executor import PipelineExecutor
from dcc.engine.plan_builder import (
    build_planner_prompt_from_issues,
    build_planner_prompt_from_spec,
    enrich_steps_with_routing,
    parse_planner_output,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])

# Active executors indexed by pipeline_id
_active_executors: dict[str, PipelineExecutor] = {}


# --- Request models ---


class CreatePipelineRequest(BaseModel):
    workspace_id: str
    name: str
    description: str | None = None
    spec: str | None = None
    source_type: str | None = None
    source_ref: str | None = None


class AddStepRequest(BaseModel):
    position: int
    name: str
    description: str | None = None
    agent: str | None = None
    skill: str | None = None
    model: str | None = None
    prompt_template: str | None = None
    depends_on: list[str] | None = None


class UpdateStepRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    agent: str | None = None
    skill: str | None = None
    model: str | None = None
    prompt_template: str | None = None
    position: int | None = None
    depends_on: list[str] | None = None


class StatusUpdateRequest(BaseModel):
    status: str


class GeneratePipelineRequest(BaseModel):
    workspace_id: str
    name: str
    description: str | None = None
    spec: str | None = None
    milestone_number: int | None = None


# --- CRUD endpoints ---


@router.get("")
async def list_pipelines(
    workspace_id: str | None = None,
    limit: int = Query(50, le=200),
):
    """Listar pipelines, opcionalmente filtrados por workspace."""
    pipelines = await repository.get_pipelines(workspace_id=workspace_id, limit=limit)
    return {"pipelines": pipelines}


@router.post("")
async def create_pipeline(req: CreatePipelineRequest):
    """Crear pipeline vacío (draft)."""
    ws = await repository.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    pipeline_id = await repository.create_pipeline(
        workspace_id=req.workspace_id,
        name=req.name,
        description=req.description,
        spec=req.spec,
        source_type=req.source_type,
        source_ref=req.source_ref,
    )
    return {"pipeline_id": pipeline_id}


@router.get("/agents")
async def list_agents():
    """Listar agentes disponibles con sus keywords."""
    return {"agents": get_available_agents()}


@router.get("/{pipeline_id}")
async def get_pipeline(pipeline_id: str):
    """Obtener pipeline con sus steps."""
    pipeline = await repository.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    steps = await repository.get_pipeline_steps(pipeline_id)
    return {"pipeline": pipeline, "steps": steps}


@router.delete("/{pipeline_id}")
async def delete_pipeline(pipeline_id: str):
    """Eliminar pipeline y sus steps."""
    deleted = await repository.delete_pipeline(pipeline_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return {"deleted": True}


@router.patch("/{pipeline_id}/status")
async def update_pipeline_status(pipeline_id: str, req: StatusUpdateRequest):
    """Cambiar status del pipeline (draft ↔ ready)."""
    pipeline = await repository.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    valid_transitions = {
        "draft": ["ready"],
        "ready": ["draft"],
        "completed": ["draft"],
        "failed": ["draft"],
    }
    current = pipeline["status"]
    allowed = valid_transitions.get(current, [])
    if req.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{current}' to '{req.status}'",
        )

    await repository.update_pipeline_status(pipeline_id, req.status)
    return {"status": req.status}


# --- Step endpoints ---


@router.post("/{pipeline_id}/steps")
async def add_step(pipeline_id: str, req: AddStepRequest):
    """Agregar step al pipeline (auto-suggest agent si no se especifica)."""
    pipeline = await repository.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    agent = req.agent
    if not agent:
        agent = suggest_agent(req.name, req.description)

    step_id = await repository.create_pipeline_step(
        pipeline_id=pipeline_id,
        position=req.position,
        name=req.name,
        description=req.description,
        agent=agent,
        skill=req.skill,
        model=req.model,
        prompt_template=req.prompt_template,
        depends_on=req.depends_on,
    )
    return {"step_id": step_id, "suggested_agent": agent}


@router.patch("/{pipeline_id}/steps/{step_id}")
async def update_step(pipeline_id: str, step_id: str, req: UpdateStepRequest):
    """Editar un step del pipeline."""
    step = await repository.get_pipeline_step(step_id)
    if not step or step["pipeline_id"] != pipeline_id:
        raise HTTPException(status_code=404, detail="Step not found")

    await repository.update_pipeline_step(
        step_id=step_id,
        name=req.name,
        description=req.description,
        agent=req.agent,
        skill=req.skill,
        model=req.model,
        prompt_template=req.prompt_template,
        position=req.position,
        depends_on=req.depends_on,
    )
    return {"updated": True}


@router.delete("/{pipeline_id}/steps/{step_id}")
async def delete_step(pipeline_id: str, step_id: str):
    """Eliminar un step del pipeline."""
    step = await repository.get_pipeline_step(step_id)
    if not step or step["pipeline_id"] != pipeline_id:
        raise HTTPException(status_code=404, detail="Step not found")

    from dcc.db.database import get_db

    db = await get_db()
    await db.execute("DELETE FROM pipeline_steps WHERE id = ?", (step_id,))
    await db.commit()
    return {"deleted": True}


# --- Generate pipeline ---


@router.post("/generate")
async def generate_pipeline(req: GeneratePipelineRequest):
    """Generar pipeline desde spec o milestone usando Claude como planner."""
    ws = await repository.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agents = get_available_agents()
    agent_names = [a["name"] for a in agents]

    # Construir prompt según modo
    if req.milestone_number is not None:
        # Modo Milestone: cargar issues
        owner = ws.get("repo_owner")
        repo = ws.get("repo_name")
        if not owner or not repo:
            raise HTTPException(
                status_code=400,
                detail="Workspace has no GitHub repository configured",
            )
        try:
            issues_data = await gh_api(
                f"/repos/{owner}/{repo}/issues?"
                f"milestone={req.milestone_number}&state=all&per_page=50"
            )
            issues = issues_data if isinstance(issues_data, list) else []
        except GhError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        if not issues:
            raise HTTPException(
                status_code=400, detail="No issues found for this milestone"
            )

        planner_prompt = build_planner_prompt_from_issues(issues, agent_names)
        source_type = "milestone"
        source_ref = str(req.milestone_number)
    elif req.spec:
        planner_prompt = build_planner_prompt_from_spec(req.spec, agent_names)
        source_type = "spec"
        source_ref = None
    else:
        raise HTTPException(
            status_code=400, detail="Either spec or milestone_number is required"
        )

    # Ejecutar Claude como planner via CliRunner
    from dcc.engine.cli_runner import CliRunner

    planner_session_id = await repository.create_session(
        workspace_id=req.workspace_id,
        prompt=planner_prompt[:200] + "...",
        model="sonnet",
    )

    runner = CliRunner(
        session_id=planner_session_id,
        workspace_path=ws["path"],
        config_dir=ws.get("config_dir", "~/.claude-personal"),
        prompt=planner_prompt,
        model="sonnet",
    )

    # Recoger output completo
    full_output = ""
    async for event in runner.run():
        if hasattr(event, "text") and event.text:
            full_output += event.text

    # Parsear steps del output
    steps = parse_planner_output(full_output)
    if not steps:
        raise HTTPException(
            status_code=500,
            detail="Planner failed to generate valid steps",
        )

    steps = enrich_steps_with_routing(steps)

    # Crear pipeline + steps en DB
    pipeline_id = await repository.create_pipeline(
        workspace_id=req.workspace_id,
        name=req.name,
        description=req.description,
        spec=req.spec,
        source_type=source_type,
        source_ref=source_ref,
    )

    # Convertir índices de depends_on a step IDs
    step_ids: list[str] = []
    for i, step_data in enumerate(steps):
        # Convertir depends_on de índices a IDs (se resuelve después)
        raw_deps = step_data.get("depends_on", [])
        depends_on_ids = []
        for dep in raw_deps:
            if isinstance(dep, int) and 0 <= dep < len(step_ids):
                depends_on_ids.append(step_ids[dep])

        step_id = await repository.create_pipeline_step(
            pipeline_id=pipeline_id,
            position=i,
            name=step_data.get("name", f"Step {i + 1}"),
            description=step_data.get("description"),
            agent=step_data.get("agent"),
            prompt_template=step_data.get("prompt_template"),
            depends_on=depends_on_ids,
        )
        step_ids.append(step_id)

    pipeline = await repository.get_pipeline(pipeline_id)
    pipeline_steps = await repository.get_pipeline_steps(pipeline_id)

    return {"pipeline": pipeline, "steps": pipeline_steps}


# --- Execution endpoints ---


@router.post("/{pipeline_id}/execute")
async def execute_pipeline(
    pipeline_id: str,
    max_parallel: int = Query(3, ge=1, le=10),
):
    """Ejecutar pipeline — retorna SSE stream con pipeline events."""
    pipeline = await repository.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    if pipeline["status"] not in ("draft", "ready", "failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot execute pipeline in '{pipeline['status']}' status",
        )

    if pipeline_id in _active_executors:
        raise HTTPException(status_code=409, detail="Pipeline is already running")

    # Reset steps a pending antes de ejecutar
    steps = await repository.get_pipeline_steps(pipeline_id)
    for step in steps:
        if step["status"] != "pending":
            await repository.update_pipeline_step_status(step["id"], "pending")

    executor = PipelineExecutor(pipeline_id, max_parallel=max_parallel)
    _active_executors[pipeline_id] = executor

    async def event_generator():
        try:
            async for event in executor.run():
                data = event.model_dump_json(exclude_none=True)
                yield {"event": event.type.value, "data": data}
        except asyncio.CancelledError:
            logger.info("Pipeline SSE cancelled for %s", pipeline_id)
            await executor.cancel()
        finally:
            _active_executors.pop(pipeline_id, None)

    return EventSourceResponse(event_generator())


@router.post("/{pipeline_id}/cancel")
async def cancel_pipeline(pipeline_id: str):
    """Cancelar ejecución del pipeline."""
    executor = _active_executors.get(pipeline_id)
    if not executor:
        raise HTTPException(status_code=404, detail="No active executor for this pipeline")

    await executor.cancel()
    return {"status": "cancelled"}


@router.post("/{pipeline_id}/pause")
async def pause_pipeline(pipeline_id: str):
    """Pausar pipeline (no lanza nuevos steps)."""
    executor = _active_executors.get(pipeline_id)
    if not executor:
        raise HTTPException(status_code=404, detail="No active executor for this pipeline")

    executor.pause()
    await repository.update_pipeline_status(pipeline_id, "paused")
    return {"status": "paused"}


@router.post("/{pipeline_id}/resume")
async def resume_pipeline(pipeline_id: str):
    """Reanudar pipeline pausado."""
    executor = _active_executors.get(pipeline_id)
    if not executor:
        raise HTTPException(status_code=404, detail="No active executor for this pipeline")

    executor.resume()
    await repository.update_pipeline_status(pipeline_id, "running")
    return {"status": "running"}
