"""Tests for pipeline and pipeline_steps CRUD in repository."""

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

    await repository.upsert_tenant("t1", "Test Tenant", "/tmp/config", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/test-ws")

    yield

    await close_db()


# --- Pipelines ---


@pytest.mark.asyncio
async def test_create_pipeline():
    pid = await repository.create_pipeline("w1", "My Pipeline", description="desc")
    assert pid
    pipeline = await repository.get_pipeline(pid)
    assert pipeline is not None
    assert pipeline["name"] == "My Pipeline"
    assert pipeline["description"] == "desc"
    assert pipeline["status"] == "draft"
    assert pipeline["workspace_id"] == "w1"
    assert pipeline["total_cost"] == 0


@pytest.mark.asyncio
async def test_get_pipelines_by_workspace():
    await repository.create_pipeline("w1", "P1")
    await repository.create_pipeline("w1", "P2")

    # Otro workspace
    await repository.upsert_workspace("w2", "t1", "OtherWS", "/tmp/other-ws")
    await repository.create_pipeline("w2", "P3")

    all_pipelines = await repository.get_pipelines()
    assert len(all_pipelines) == 3

    w1_pipelines = await repository.get_pipelines(workspace_id="w1")
    assert len(w1_pipelines) == 2
    assert all(p["workspace_id"] == "w1" for p in w1_pipelines)


@pytest.mark.asyncio
async def test_update_pipeline_status():
    pid = await repository.create_pipeline("w1", "Status Test")

    await repository.update_pipeline_status(pid, "running")
    p = await repository.get_pipeline(pid)
    assert p["status"] == "running"
    assert p["started_at"] is not None

    await repository.update_pipeline_status(
        pid, "completed", total_cost=1.5, total_duration_ms=30000
    )
    p = await repository.get_pipeline(pid)
    assert p["status"] == "completed"
    assert p["finished_at"] is not None
    assert p["total_cost"] == 1.5
    assert p["total_duration_ms"] == 30000


@pytest.mark.asyncio
async def test_delete_pipeline_cascades_steps():
    pid = await repository.create_pipeline("w1", "Delete Test")
    await repository.create_pipeline_step(pid, 0, "Step 1")
    await repository.create_pipeline_step(pid, 1, "Step 2")

    steps = await repository.get_pipeline_steps(pid)
    assert len(steps) == 2

    deleted = await repository.delete_pipeline(pid)
    assert deleted is True

    # Pipeline gone
    assert await repository.get_pipeline(pid) is None
    # Steps gone too
    assert await repository.get_pipeline_steps(pid) == []


# --- Pipeline Steps ---


@pytest.mark.asyncio
async def test_create_pipeline_step():
    pid = await repository.create_pipeline("w1", "Step Test")
    sid = await repository.create_pipeline_step(
        pid, 0, "Implement feature",
        description="Build the feature",
        agent="backend-dev",
        prompt_template="Implement {{spec}}",
        depends_on=["dep-1"],
    )
    assert sid
    step = await repository.get_pipeline_step(sid)
    assert step is not None
    assert step["name"] == "Implement feature"
    assert step["agent"] == "backend-dev"
    assert step["depends_on"] == ["dep-1"]
    assert step["status"] == "pending"


@pytest.mark.asyncio
async def test_get_pipeline_steps_ordered():
    pid = await repository.create_pipeline("w1", "Order Test")
    await repository.create_pipeline_step(pid, 2, "Step C")
    await repository.create_pipeline_step(pid, 0, "Step A")
    await repository.create_pipeline_step(pid, 1, "Step B")

    steps = await repository.get_pipeline_steps(pid)
    assert [s["position"] for s in steps] == [0, 1, 2]
    assert [s["name"] for s in steps] == ["Step A", "Step B", "Step C"]


@pytest.mark.asyncio
async def test_update_step_status_running():
    pid = await repository.create_pipeline("w1", "Run Test")
    sid = await repository.create_pipeline_step(pid, 0, "Run step")

    # Crear sesión real para FK constraint
    sess_id = await repository.create_session("w1", "test prompt")
    await repository.update_pipeline_step_status(sid, "running", session_id=sess_id)
    step = await repository.get_pipeline_step(sid)
    assert step["status"] == "running"
    assert step["session_id"] == sess_id
    assert step["started_at"] is not None


@pytest.mark.asyncio
async def test_update_step_status_completed():
    pid = await repository.create_pipeline("w1", "Complete Test")
    sid = await repository.create_pipeline_step(pid, 0, "Complete step")

    await repository.update_pipeline_step_status(
        sid, "completed", output_summary="All good"
    )
    step = await repository.get_pipeline_step(sid)
    assert step["status"] == "completed"
    assert step["output_summary"] == "All good"
    assert step["finished_at"] is not None


@pytest.mark.asyncio
async def test_update_pipeline_step_fields():
    pid = await repository.create_pipeline("w1", "Update Test")
    sid = await repository.create_pipeline_step(pid, 0, "Original name")

    await repository.update_pipeline_step(
        sid,
        name="Updated name",
        agent="qa-engineer",
        position=5,
        depends_on=["other-step"],
    )
    step = await repository.get_pipeline_step(sid)
    assert step["name"] == "Updated name"
    assert step["agent"] == "qa-engineer"
    assert step["position"] == 5
    assert step["depends_on"] == ["other-step"]
