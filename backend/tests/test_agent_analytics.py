"""Tests for Agent Analytics functions."""

import pytest
import pytest_asyncio

from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    settings.db_path = str(tmp_path / "test.db")
    await close_db()
    await init_db()

    await repository.upsert_tenant("t1", "Test", "/tmp/cfg", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/ws")

    yield

    await close_db()


@pytest.mark.asyncio
async def test_agent_usage_stats_empty():
    stats = await repository.get_agent_usage_stats()
    assert stats == []


@pytest.mark.asyncio
async def test_agent_usage_stats():
    # Create sessions with agents
    s1 = await repository.create_session("w1", "prompt1", agent="code-reviewer")
    await repository.update_session_finished(s1, status="completed", cost_usd=0.05, duration_ms=5000)

    s2 = await repository.create_session("w1", "prompt2", agent="code-reviewer")
    await repository.update_session_finished(s2, status="completed", cost_usd=0.03, duration_ms=3000)

    s3 = await repository.create_session("w1", "prompt3", agent="explorer")
    await repository.update_session_finished(s3, status="error", cost_usd=0.01, duration_ms=1000)

    # Session without agent should not appear
    s4 = await repository.create_session("w1", "prompt4")
    await repository.update_session_finished(s4, status="completed", cost_usd=0.02)

    stats = await repository.get_agent_usage_stats()
    assert len(stats) == 2

    reviewer = next(s for s in stats if s["name"] == "code-reviewer")
    assert reviewer["sessions"] == 2
    assert reviewer["success_rate"] == 100.0

    explorer = next(s for s in stats if s["name"] == "explorer")
    assert explorer["sessions"] == 1
    assert explorer["success_rate"] == 0.0


@pytest.mark.asyncio
async def test_agent_usage_stats_workspace_filter():
    await repository.upsert_workspace("w2", "t1", "TestWS2", "/tmp/ws2")

    s1 = await repository.create_session("w1", "p1", agent="reviewer")
    await repository.update_session_finished(s1, status="completed")

    s2 = await repository.create_session("w2", "p2", agent="reviewer")
    await repository.update_session_finished(s2, status="completed")

    all_stats = await repository.get_agent_usage_stats()
    ws1_stats = await repository.get_agent_usage_stats(workspace_id="w1")

    assert all_stats[0]["sessions"] == 2
    assert ws1_stats[0]["sessions"] == 1


@pytest.mark.asyncio
async def test_agent_cost_trend():
    s1 = await repository.create_session("w1", "p1", agent="explorer")
    await repository.update_session_finished(s1, status="completed", cost_usd=0.10)

    trend = await repository.get_agent_cost_trend("explorer", days=7)
    assert len(trend) >= 1
    assert trend[0]["cost"] == 0.10


@pytest.mark.asyncio
async def test_subagent_delegation_stats():
    s1 = await repository.create_session("w1", "p1", agent="main-agent")
    await repository.create_monitor_task(
        session_id=s1, tool_call_id="tc1", tool_name="Task",
        subagent_type="Explore", subagent_model="haiku",
    )
    await repository.create_monitor_task(
        session_id=s1, tool_call_id="tc2", tool_name="Task",
        subagent_type="Explore",
    )
    await repository.create_monitor_task(
        session_id=s1, tool_call_id="tc3", tool_name="Read",
    )

    delegations = await repository.get_subagent_delegation_stats()
    assert len(delegations) == 1
    assert delegations[0]["parent_agent"] == "main-agent"
    assert delegations[0]["subagent_type"] == "Explore"
    assert delegations[0]["count"] == 2


@pytest.mark.asyncio
async def test_agent_comparison():
    s1 = await repository.create_session("w1", "p1", agent="agent-a")
    await repository.update_session_finished(s1, status="completed", cost_usd=0.10)

    s2 = await repository.create_session("w1", "p2", agent="agent-b")
    await repository.update_session_finished(s2, status="completed", cost_usd=0.20)

    comparison = await repository.get_agent_comparison(["agent-a", "agent-b"])
    assert len(comparison) == 2

    empty = await repository.get_agent_comparison([])
    assert empty == []
