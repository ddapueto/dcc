"""GitHub integration routes — proxies gh CLI for repo data."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from dcc.db import repository
from dcc.engine.gh_client import GhError, gh_api

router = APIRouter(prefix="/api/github", tags=["github"])


async def _get_repo(workspace_id: str) -> tuple[str, str]:
    """Resolve workspace to (owner, repo). Raises 400 if no repo configured."""
    ws = await repository.get_workspace(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    owner = ws.get("repo_owner")
    repo = ws.get("repo_name")
    if not owner or not repo:
        raise HTTPException(
            status_code=400,
            detail="Workspace has no GitHub repository configured",
        )
    return owner, repo


@router.get("/milestones")
async def list_milestones(
    workspace_id: str = Query(...),
    state: str = Query("open"),
):
    """List milestones for the workspace's GitHub repo."""
    owner, repo = await _get_repo(workspace_id)
    try:
        data = await gh_api(f"/repos/{owner}/{repo}/milestones?state={state}&per_page=20")
        return {"milestones": data if isinstance(data, list) else []}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/milestones/{number}/issues")
async def list_milestone_issues(
    number: int,
    workspace_id: str = Query(...),
):
    """List issues for a specific milestone."""
    owner, repo = await _get_repo(workspace_id)
    try:
        data = await gh_api(
            f"/repos/{owner}/{repo}/issues?milestone={number}&state=all&per_page=50"
        )
        return {"issues": data if isinstance(data, list) else []}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/issues")
async def list_issues(
    workspace_id: str = Query(...),
    state: str = Query("open"),
    limit: int = Query(30, le=100),
):
    """List issues for the workspace's GitHub repo."""
    owner, repo = await _get_repo(workspace_id)
    try:
        data = await gh_api(
            f"/repos/{owner}/{repo}/issues?state={state}&per_page={limit}"
        )
        # gh api /issues also returns PRs — filter them out
        issues = [
            i for i in (data if isinstance(data, list) else [])
            if "pull_request" not in i
        ]
        return {"issues": issues}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/issues/{number}")
async def get_issue(
    number: int,
    workspace_id: str = Query(...),
):
    """Get a single issue by number."""
    owner, repo = await _get_repo(workspace_id)
    try:
        data = await gh_api(f"/repos/{owner}/{repo}/issues/{number}")
        return {"issue": data}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


@router.get("/pulls")
async def list_pulls(
    workspace_id: str = Query(...),
    state: str = Query("open"),
):
    """List pull requests for the workspace's GitHub repo."""
    owner, repo = await _get_repo(workspace_id)
    try:
        data = await gh_api(
            f"/repos/{owner}/{repo}/pulls?state={state}&per_page=20"
        )
        return {"pulls": data if isinstance(data, list) else []}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e


class CreateIssueRequest(BaseModel):
    workspace_id: str
    title: str
    body: str = ""
    labels: list[str] = []


@router.post("/issues")
async def create_issue(req: CreateIssueRequest):
    """Create a new issue in the workspace's GitHub repo."""
    owner, repo = await _get_repo(req.workspace_id)
    payload: dict = {"title": req.title, "body": req.body}
    if req.labels:
        payload["labels"] = req.labels
    try:
        data = await gh_api(f"/repos/{owner}/{repo}/issues", method="POST", body=payload)
        return {"issue": data}
    except GhError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
