"""Tests for Agent Registry CRUD operations."""

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
    await repository.upsert_workspace("w2", "t1", "TestWS2", "/tmp/ws2")

    yield

    await close_db()


@pytest.mark.asyncio
async def test_upsert_agent_creates():
    agent_id = await repository.upsert_agent(
        workspace_id="w1",
        name="code-reviewer",
        filename="code-reviewer.md",
        description="Reviews code for quality",
        model="sonnet",
        tools=["Read", "Glob", "Grep"],
        max_turns=15,
    )
    assert agent_id

    agent = await repository.get_agent_by_name("w1", "code-reviewer")
    assert agent is not None
    assert agent["name"] == "code-reviewer"
    assert agent["model"] == "sonnet"
    assert agent["tools"] == ["Read", "Glob", "Grep"]
    assert agent["max_turns"] == 15
    assert agent["is_active"] is True


@pytest.mark.asyncio
async def test_upsert_agent_updates_on_conflict():
    await repository.upsert_agent("w1", "explorer", "explorer.md", description="v1")
    await repository.upsert_agent("w1", "explorer", "explorer.md", description="v2", model="haiku")

    agent = await repository.get_agent_by_name("w1", "explorer")
    assert agent["description"] == "v2"
    assert agent["model"] == "haiku"


@pytest.mark.asyncio
async def test_get_agents_for_workspace():
    await repository.upsert_agent("w1", "agent-a", "agent-a.md")
    await repository.upsert_agent("w1", "agent-b", "agent-b.md")
    await repository.upsert_agent("w2", "agent-c", "agent-c.md")

    agents = await repository.get_agents_for_workspace("w1")
    assert len(agents) == 2
    names = [a["name"] for a in agents]
    assert "agent-a" in names
    assert "agent-b" in names


@pytest.mark.asyncio
async def test_deactivate_missing_agents():
    await repository.upsert_agent("w1", "keep", "keep.md")
    await repository.upsert_agent("w1", "remove", "remove.md")

    await repository.deactivate_missing_agents("w1", ["keep"])

    agents = await repository.get_agents_for_workspace("w1", active_only=True)
    assert len(agents) == 1
    assert agents[0]["name"] == "keep"

    all_agents = await repository.get_agents_for_workspace("w1", active_only=False)
    assert len(all_agents) == 2


@pytest.mark.asyncio
async def test_get_agent_by_name_not_found():
    result = await repository.get_agent_by_name("w1", "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_agent_json_fields_parsing():
    await repository.upsert_agent(
        "w1", "full-agent", "full-agent.md",
        tools=["Read", "Write"],
        disallowed_tools=["Bash"],
        skills=["commit", "test"],
        background=True,
    )

    agent = await repository.get_agent_by_name("w1", "full-agent")
    assert agent["tools"] == ["Read", "Write"]
    assert agent["disallowed_tools"] == ["Bash"]
    assert agent["skills"] == ["commit", "test"]
    assert agent["background"] is True
