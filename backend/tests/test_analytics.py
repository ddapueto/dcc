"""Tests for analytics repository functions."""

import pytest
import pytest_asyncio

from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    """Init fresh DB for each test."""
    settings.db_path = str(tmp_path / "test.db")
    await close_db()
    await init_db()

    # Seed tenant + workspace for FK constraints
    await repository.upsert_tenant("t1", "Test Tenant", "/tmp/config", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/test-ws")
    await repository.upsert_tenant("t2", "Other Tenant", "/tmp/config2", "claude-other")
    await repository.upsert_workspace("w2", "t2", "OtherWS", "/tmp/other-ws")

    yield

    await close_db()


# --- get_analytics_summary ---


@pytest.mark.asyncio
async def test_summary_empty():
    result = await repository.get_analytics_summary()
    assert result["total_sessions"] == 0
    assert result["total_cost"] == 0
    assert result["total_input_tokens"] == 0
    assert result["total_output_tokens"] == 0
    assert result["cost_7d"] == 0
    assert result["cost_24h"] == 0
    assert result["by_status"] == {}


@pytest.mark.asyncio
async def test_summary_with_sessions():
    s1 = await repository.create_session("w1", "prompt 1")
    await repository.update_session_finished(
        s1, status="completed", cost_usd=0.05, input_tokens=1000, output_tokens=500
    )
    s2 = await repository.create_session("w1", "prompt 2")
    await repository.update_session_finished(
        s2, status="error", cost_usd=0.02, input_tokens=500, output_tokens=200
    )

    result = await repository.get_analytics_summary()
    assert result["total_sessions"] == 2
    assert result["total_cost"] == pytest.approx(0.07)
    assert result["total_input_tokens"] == 1500
    assert result["total_output_tokens"] == 700
    assert result["by_status"]["completed"] == 1
    assert result["by_status"]["error"] == 1


# --- get_cost_by_workspace ---


@pytest.mark.asyncio
async def test_cost_by_workspace():
    s1 = await repository.create_session("w1", "p1")
    await repository.update_session_finished(s1, status="completed", cost_usd=0.10)
    s2 = await repository.create_session("w1", "p2")
    await repository.update_session_finished(s2, status="completed", cost_usd=0.05)
    s3 = await repository.create_session("w2", "p3")
    await repository.update_session_finished(s3, status="completed", cost_usd=0.20)

    result = await repository.get_cost_by_workspace()
    assert len(result) == 2
    # Ordered by cost DESC → w2 first
    assert result[0]["workspace_name"] == "OtherWS"
    assert result[0]["total_cost"] == pytest.approx(0.20)
    assert result[0]["session_count"] == 1
    assert result[1]["workspace_name"] == "TestWS"
    assert result[1]["total_cost"] == pytest.approx(0.15)
    assert result[1]["session_count"] == 2


# --- get_cost_trend ---


@pytest.mark.asyncio
async def test_cost_trend_returns_series():
    s1 = await repository.create_session("w1", "p1")
    await repository.update_session_finished(s1, status="completed", cost_usd=0.10)
    s2 = await repository.create_session("w1", "p2")
    await repository.update_session_finished(s2, status="completed", cost_usd=0.05)

    result = await repository.get_cost_trend(days=7)
    assert len(result) >= 1
    point = result[0]
    assert "date" in point
    assert "sessions" in point
    assert "cost" in point
    assert point["sessions"] == 2
    assert point["cost"] == pytest.approx(0.15)


# --- get_top_skills ---


@pytest.mark.asyncio
async def test_top_skills_ordered():
    # Create sessions with different skills/agents
    db = await repository.get_db()
    for _ in range(3):
        sid = await repository.create_session("w1", "p")
        await db.execute("UPDATE sessions SET skill = 'commit' WHERE id = ?", (sid,))
    for _ in range(2):
        sid = await repository.create_session("w1", "p")
        await db.execute("UPDATE sessions SET agent = 'reviewer' WHERE id = ?", (sid,))
    await repository.create_session("w1", "plain prompt")
    await db.commit()

    result = await repository.get_top_skills(limit=10)
    assert len(result) == 3
    assert result[0]["name"] == "/commit"
    assert result[0]["count"] == 3
    assert result[0]["kind"] == "skill"
    assert result[1]["name"] == "@reviewer"
    assert result[1]["count"] == 2
    assert result[1]["kind"] == "agent"


# --- get_token_efficiency ---


@pytest.mark.asyncio
async def test_token_efficiency_empty():
    result = await repository.get_token_efficiency()
    assert result["total_input"] == 0
    assert result["total_output"] == 0
    assert result["cache_read"] == 0
    assert result["cache_write"] == 0
    assert result["cache_hit_ratio"] == 0
