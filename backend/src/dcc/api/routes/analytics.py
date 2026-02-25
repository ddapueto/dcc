from fastapi import APIRouter, Query

from dcc.db import repository

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
async def analytics_summary():
    return await repository.get_analytics_summary()


@router.get("/cost-by-workspace")
async def cost_by_workspace():
    return await repository.get_cost_by_workspace()


@router.get("/cost-trend")
async def cost_trend(days: int = Query(default=30, ge=1, le=365)):
    return await repository.get_cost_trend(days=days)


@router.get("/top-skills")
async def top_skills(limit: int = Query(default=10, ge=1, le=100)):
    return await repository.get_top_skills(limit=limit)


@router.get("/token-efficiency")
async def token_efficiency():
    return await repository.get_token_efficiency()
