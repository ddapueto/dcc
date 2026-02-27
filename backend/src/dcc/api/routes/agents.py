from fastapi import APIRouter, Query

from dcc.db import repository

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("/stats")
async def agent_usage_stats(workspace_id: str | None = None):
    """Per-agent usage statistics: sessions, cost, duration, success rate."""
    stats = await repository.get_agent_usage_stats(workspace_id)
    return {"stats": stats}


@router.get("/stats/{agent_name}/trend")
async def agent_cost_trend(agent_name: str, days: int = 30):
    """Daily cost trend for a specific agent."""
    trend = await repository.get_agent_cost_trend(agent_name, days)
    return {"trend": trend}


@router.get("/delegations")
async def subagent_delegation_stats():
    """Which agents delegate to which subagents (from monitor_tasks)."""
    delegations = await repository.get_subagent_delegation_stats()
    return {"delegations": delegations}


@router.get("/comparison")
async def agent_comparison(agents: str = Query(default="")):
    """Side-by-side comparison of agent metrics. Pass comma-separated agent names."""
    agent_names = [a.strip() for a in agents.split(",") if a.strip()]
    if not agent_names:
        return {"comparison": []}
    comparison = await repository.get_agent_comparison(agent_names)
    return {"comparison": comparison}
