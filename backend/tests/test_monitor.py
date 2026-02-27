"""Tests for MonitorProcessor."""

import pytest
import pytest_asyncio

from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db
from dcc.engine.monitor import MonitorProcessor
from dcc.engine.types import AgUiEvent, AgUiEventType


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
async def test_tool_call_start_creates_task():
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    event = AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_1",
        tool_name="Read",
        tool_input='{"file_path": "/tmp/file.py"}',
    )
    result = await monitor.process_event(event)

    assert result is not None
    assert result["action"] == "created"
    assert result["tool_name"] == "Read"
    assert result["depth"] == 0
    assert result["parent_id"] is None

    tasks = await repository.get_monitor_tasks(session_id)
    assert len(tasks) == 1
    assert tasks[0]["tool_name"] == "Read"
    assert tasks[0]["description"] == "/tmp/file.py"


@pytest.mark.asyncio
async def test_tool_call_result_completes_task():
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    # Start
    await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_1",
        tool_name="Bash",
        tool_input='{"command": "ls -la"}',
    ))

    # Result
    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        session_id=session_id,
        tool_call_id="tc_1",
        tool_result="file1.py\nfile2.py",
    ))

    assert result is not None
    assert result["action"] == "updated"
    assert result["status"] == "completed"
    assert result["duration_ms"] is not None

    tasks = await repository.get_monitor_tasks(session_id)
    assert tasks[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_tool_call_error_marks_failed():
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_1",
        tool_name="Bash",
    ))

    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        session_id=session_id,
        tool_call_id="tc_1",
        tool_result="error: command not found",
        tool_is_error=True,
    ))

    assert result["status"] == "failed"


@pytest.mark.asyncio
async def test_task_tool_nesting():
    """Task tool crea subtasks anidados."""
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    # Parent Task tool
    await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_parent",
        tool_name="Task",
        tool_input='{"description": "Explore codebase", "prompt": "find files"}',
    ))

    # Child Read tool (dentro del Task)
    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_child",
        tool_name="Read",
        tool_input='{"file_path": "/tmp/a.py"}',
    ))

    assert result["depth"] == 1
    assert result["parent_id"] is not None

    # Close child
    await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        session_id=session_id,
        tool_call_id="tc_child",
        tool_result="content",
    ))

    # Close parent
    await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_RESULT,
        session_id=session_id,
        tool_call_id="tc_parent",
        tool_result="done",
    ))

    tasks = await repository.get_monitor_tasks(session_id)
    assert len(tasks) == 2
    parent = [t for t in tasks if t["tool_name"] == "Task"][0]
    child = [t for t in tasks if t["tool_name"] == "Read"][0]
    assert child["parent_id"] == parent["id"]
    assert child["depth"] == 1
    assert parent["depth"] == 0


@pytest.mark.asyncio
async def test_extract_task_metadata():
    md = MonitorProcessor._extract_task_metadata
    assert md("Read", '{"file_path": "/a/b.py"}') == {
        "description": "/a/b.py", "subagent_type": None, "subagent_model": None,
    }
    assert md("Bash", '{"command": "npm test"}') == {
        "description": "npm test", "subagent_type": None, "subagent_model": None,
    }
    assert md("Grep", '{"pattern": "TODO"}') == {
        "description": "TODO", "subagent_type": None, "subagent_model": None,
    }
    assert md("Unknown", None) == {
        "description": "Unknown", "subagent_type": None, "subagent_model": None,
    }


@pytest.mark.asyncio
async def test_extract_task_metadata_with_subagent():
    result = MonitorProcessor._extract_task_metadata(
        "Task",
        '{"description": "explore codebase", "subagent_type": "Explore", "model": "haiku", "prompt": "find files"}',
    )
    assert result["description"] == "explore codebase"
    assert result["subagent_type"] == "Explore"
    assert result["subagent_model"] == "haiku"


@pytest.mark.asyncio
async def test_task_with_subagent_type_stored():
    """Task tool with subagent_type should be stored in monitor_tasks."""
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
        tool_call_id="tc_explore",
        tool_name="Task",
        tool_input='{"description": "search code", "subagent_type": "Explore", "model": "haiku", "prompt": "find stuff"}',
    ))

    assert result is not None
    assert result["subagent_type"] == "Explore"
    assert result["subagent_model"] == "haiku"

    tasks = await repository.get_monitor_tasks(session_id)
    assert len(tasks) == 1
    assert tasks[0]["subagent_type"] == "Explore"
    assert tasks[0]["subagent_model"] == "haiku"


@pytest.mark.asyncio
async def test_ignores_events_without_tool_call_id():
    session_id = await repository.create_session("w1", "test")
    monitor = MonitorProcessor(session_id)

    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TOOL_CALL_START,
        session_id=session_id,
    ))
    assert result is None

    result = await monitor.process_event(AgUiEvent(
        type=AgUiEventType.TEXT_MESSAGE_CONTENT,
        session_id=session_id,
        text="hello",
    ))
    assert result is None


def test_cli_runner_agent_flag():
    """CliRunner should include --agent flag when agent is specified."""
    from dcc.engine.cli_runner import CliRunner

    runner = CliRunner(
        session_id="test-session",
        workspace_path="/tmp",
        config_dir="/tmp/config",
        prompt="do something",
        agent="code-reviewer",
        model="sonnet",
    )
    cmd = runner._build_command()
    assert "--agent" in cmd
    agent_idx = cmd.index("--agent")
    assert cmd[agent_idx + 1] == "code-reviewer"


def test_cli_runner_no_agent_flag():
    """CliRunner should NOT include --agent flag when agent is None."""
    from dcc.engine.cli_runner import CliRunner

    runner = CliRunner(
        session_id="test-session",
        workspace_path="/tmp",
        config_dir="/tmp/config",
        prompt="do something",
    )
    cmd = runner._build_command()
    assert "--agent" not in cmd
