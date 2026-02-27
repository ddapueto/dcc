"""Tests for workflow repository functions."""

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
    await repository.upsert_workspace("w2", "t1", "OtherWS", "/tmp/other-ws")

    yield

    await close_db()


# --- Workflow CRUD ---


@pytest.mark.asyncio
async def test_create_and_get_workflow():
    wf_id = await repository.create_workflow(
        workspace_id="w1",
        name="Test Workflow",
        prompt_template="Do {{task}}",
        description="A test workflow",
        category="development",
        parameters=[{"key": "task", "label": "Task", "type": "textarea", "required": True}],
    )
    assert wf_id

    wf = await repository.get_workflow(wf_id)
    assert wf is not None
    assert wf["name"] == "Test Workflow"
    assert wf["category"] == "development"
    assert wf["prompt_template"] == "Do {{task}}"
    assert isinstance(wf["parameters"], list)
    assert len(wf["parameters"]) == 1
    assert wf["parameters"][0]["key"] == "task"
    assert wf["is_builtin"] is False
    assert wf["usage_count"] == 0


@pytest.mark.asyncio
async def test_get_workflows_filter_by_workspace():
    await repository.create_workflow("w1", "WF1", "prompt1", category="dev")
    await repository.create_workflow("w2", "WF2", "prompt2", category="dev")

    all_wf = await repository.get_workflows()
    assert len(all_wf) == 2

    w1_wf = await repository.get_workflows(workspace_id="w1")
    assert len(w1_wf) == 1
    assert w1_wf[0]["name"] == "WF1"


@pytest.mark.asyncio
async def test_get_workflows_filter_by_category():
    await repository.create_workflow("w1", "Dev WF", "prompt", category="development")
    await repository.create_workflow("w1", "Test WF", "prompt", category="testing")

    dev = await repository.get_workflows(category="development")
    assert len(dev) == 1
    assert dev[0]["name"] == "Dev WF"


@pytest.mark.asyncio
async def test_update_workflow():
    wf_id = await repository.create_workflow("w1", "Original", "old prompt")

    await repository.update_workflow(wf_id, name="Updated", prompt_template="new prompt")

    wf = await repository.get_workflow(wf_id)
    assert wf["name"] == "Updated"
    assert wf["prompt_template"] == "new prompt"


@pytest.mark.asyncio
async def test_delete_custom_workflow():
    wf_id = await repository.create_workflow("w1", "Custom", "prompt", is_builtin=False)

    deleted = await repository.delete_workflow(wf_id)
    assert deleted is True

    wf = await repository.get_workflow(wf_id)
    assert wf is None


@pytest.mark.asyncio
async def test_delete_builtin_workflow_blocked():
    wf_id = await repository.create_workflow("w1", "Builtin", "prompt", is_builtin=True)

    deleted = await repository.delete_workflow(wf_id)
    assert deleted is False

    wf = await repository.get_workflow(wf_id)
    assert wf is not None


@pytest.mark.asyncio
async def test_increment_workflow_usage():
    wf_id = await repository.create_workflow("w1", "Used", "prompt")

    wf = await repository.get_workflow(wf_id)
    assert wf["usage_count"] == 0
    assert wf["last_used_at"] is None

    await repository.increment_workflow_usage(wf_id)

    wf = await repository.get_workflow(wf_id)
    assert wf["usage_count"] == 1
    assert wf["last_used_at"] is not None

    await repository.increment_workflow_usage(wf_id)
    wf = await repository.get_workflow(wf_id)
    assert wf["usage_count"] == 2


# --- Monitor Tasks ---


@pytest.mark.asyncio
async def test_monitor_task_crud():
    session_id = await repository.create_session("w1", "test prompt")

    task_id = await repository.create_monitor_task(
        session_id=session_id,
        tool_call_id="tc_1",
        tool_name="Read",
        description="Reading file.py",
        input_summary="/path/to/file.py",
    )
    assert task_id

    tasks = await repository.get_monitor_tasks(session_id)
    assert len(tasks) == 1
    assert tasks[0]["tool_name"] == "Read"
    assert tasks[0]["status"] == "running"

    await repository.update_monitor_task(
        task_id, status="completed", output_summary="file content...", duration_ms=150
    )

    tasks = await repository.get_monitor_tasks(session_id)
    assert tasks[0]["status"] == "completed"
    assert tasks[0]["duration_ms"] == 150


@pytest.mark.asyncio
async def test_monitor_task_nesting():
    session_id = await repository.create_session("w1", "test prompt")

    parent_id = await repository.create_monitor_task(
        session_id=session_id,
        tool_call_id="tc_parent",
        tool_name="Task",
        description="Explore codebase",
        depth=0,
    )

    child_id = await repository.create_monitor_task(
        session_id=session_id,
        tool_call_id="tc_child",
        tool_name="Read",
        parent_id=parent_id,
        description="Read file",
        depth=1,
    )

    tasks = await repository.get_monitor_tasks(session_id)
    assert len(tasks) == 2
    assert tasks[0]["parent_id"] is None
    assert tasks[1]["parent_id"] == parent_id
    assert tasks[1]["depth"] == 1
