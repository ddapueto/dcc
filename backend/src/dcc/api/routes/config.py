from fastapi import APIRouter, HTTPException

from dcc.db import repository
from dcc.workspace.scanner import get_mcp_servers, read_claude_md, read_rules, read_settings_json

router = APIRouter(prefix="/api/config", tags=["config"])


@router.get("/{workspace_id}/claude-md")
async def get_claude_md(workspace_id: str):
    """Get CLAUDE.md content for a workspace."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    content = read_claude_md(ws["path"])
    return {"content": content, "exists": content is not None}


@router.get("/{workspace_id}/rules")
async def get_rules(workspace_id: str):
    """Get .claude/rules/*.md files for a workspace."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    rules = read_rules(ws["path"])
    return {"rules": rules}


@router.get("/{workspace_id}/settings")
async def get_settings(workspace_id: str):
    """Get .claude/settings.json for a workspace."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    content = read_settings_json(ws["path"])
    return {"content": content, "exists": content is not None}


@router.get("/{workspace_id}/mcps")
async def get_mcps(workspace_id: str):
    """Get MCP server configurations for a workspace."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    servers = get_mcp_servers(ws["path"], ws.get("config_dir"))
    return {"servers": servers}
