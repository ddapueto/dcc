import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from dcc.db import repository
from dcc.db.seed import sync_agents_for_workspace
from dcc.workspace.scanner import scan_workspace
from dcc.workspace.types import WorkspaceDetail

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


class CreateWorkspaceRequest(BaseModel):
    tenant_id: str
    name: str
    path: str


class CreateTenantRequest(BaseModel):
    name: str
    config_dir: str
    claude_alias: str


@router.get("")
async def list_workspaces():
    """List all workspaces with tenant info and agent/skill counts."""
    workspaces = await repository.get_workspaces()
    tenants = await repository.get_tenants()
    return {"tenants": tenants, "workspaces": workspaces}


@router.post("")
async def create_workspace(req: CreateWorkspaceRequest):
    """Create a new workspace."""
    tenant = await repository.get_tenant(req.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    workspace_id = str(uuid.uuid4())
    agents, skills, has_md, owner, repo = scan_workspace(req.path)
    await repository.upsert_workspace(
        workspace_id=workspace_id,
        tenant_id=req.tenant_id,
        name=req.name,
        path=req.path,
        agents_count=len(agents),
        skills_count=len(skills),
        has_claude_md=has_md,
        repo_owner=owner,
        repo_name=repo,
    )
    return {"id": workspace_id}


@router.get("/{workspace_id}")
async def get_workspace(workspace_id: str):
    """Get workspace detail including agents and skills list."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    agents, skills, has_md, owner, repo = scan_workspace(ws["path"])

    # Sync agents to registry
    await sync_agents_for_workspace(workspace_id, ws["path"])

    return WorkspaceDetail(
        id=ws["id"],
        tenant_id=ws["tenant_id"],
        tenant_name=ws["tenant_name"],
        name=ws["name"],
        path=ws["path"],
        has_claude_md=has_md,
        repo_owner=owner or ws.get("repo_owner"),
        repo_name=repo or ws.get("repo_name"),
        agents=agents,
        skills=skills,
    )


@router.delete("/{workspace_id}")
async def delete_workspace(workspace_id: str):
    """Delete a workspace."""
    deleted = await repository.delete_workspace(workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"deleted": True}


@router.post("/tenants")
async def create_tenant(req: CreateTenantRequest):
    """Create a new tenant."""
    tenant_id = str(uuid.uuid4())
    await repository.upsert_tenant(
        tenant_id=tenant_id,
        name=req.name,
        config_dir=req.config_dir,
        claude_alias=req.claude_alias,
    )
    return {"id": tenant_id}


@router.delete("/tenants/{tenant_id}")
async def delete_tenant(tenant_id: str):
    """Delete a tenant."""
    deleted = await repository.delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"deleted": True}


@router.post("/scan")
async def scan_all_workspaces():
    """Re-scan .claude/ directories for all workspaces."""
    workspaces = await repository.get_workspaces()
    results = []

    for ws in workspaces:
        try:
            agents, skills, has_md, owner, repo = scan_workspace(ws["path"])
            await repository.update_workspace_scan(
                ws["id"], len(agents), len(skills), has_md,
                repo_owner=owner, repo_name=repo,
            )
            # Sync agents to registry
            await sync_agents_for_workspace(ws["id"], ws["path"])
            results.append({
                "id": ws["id"],
                "name": ws["name"],
                "agents_count": len(agents),
                "skills_count": len(skills),
                "has_claude_md": has_md,
                "repo_owner": owner,
                "repo_name": repo,
            })
        except Exception as e:
            results.append({
                "id": ws["id"],
                "name": ws["name"],
                "error": str(e),
            })

    return {"scanned": len(results), "results": results}


@router.get("/{workspace_id}/agents")
async def list_workspace_agents(workspace_id: str):
    """List agents from the registry for a workspace."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    agents = await repository.get_agents_for_workspace(workspace_id)
    return {"agents": agents}


@router.get("/{workspace_id}/agents/{agent_name}")
async def get_workspace_agent(workspace_id: str, agent_name: str):
    """Get detail of a specific agent from the registry."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    agent = await repository.get_agent_by_name(workspace_id, agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {"agent": agent}
