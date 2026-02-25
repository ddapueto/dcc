from dcc.engine.event_converter import convert_cli_event
from dcc.engine.types import AgUiEventType, CliEvent


SESSION = "test-session-1"


def test_system_init_to_state_snapshot():
    cli = CliEvent(
        type="system",
        subtype="init",
        session_id="abc123",
        raw={
            "session_id": "abc123",
            "tools": ["Read", "Write", "Bash"],
            "model": "claude-sonnet-4-20250514",
            "mcp_servers": [],
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    ev = events[0]
    assert ev.type == AgUiEventType.STATE_SNAPSHOT
    assert ev.cli_session_id == "abc123"
    assert ev.state["model"] == "claude-sonnet-4-20250514"
    assert "Read" in ev.state["tools"]


def test_assistant_text_to_three_events():
    cli = CliEvent(
        type="assistant",
        subtype="text",
        message={"content": [{"type": "text", "text": "Hello world"}]},
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 3
    assert events[0].type == AgUiEventType.TEXT_MESSAGE_START
    assert events[0].role == "assistant"
    assert events[1].type == AgUiEventType.TEXT_MESSAGE_CONTENT
    assert events[1].text == "Hello world"
    assert events[2].type == AgUiEventType.TEXT_MESSAGE_END


def test_assistant_tool_use_to_two_events():
    cli = CliEvent(
        type="assistant",
        subtype="tool_use",
        message={
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_abc",
                    "name": "Read",
                    "input": {"file_path": "/tmp/test.py"},
                }
            ]
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 2
    assert events[0].type == AgUiEventType.TOOL_CALL_START
    assert events[0].tool_call_id == "tool_abc"
    assert events[0].tool_name == "Read"
    assert events[1].type == AgUiEventType.TOOL_CALL_END


def test_user_tool_result():
    cli = CliEvent(
        type="user",
        subtype="tool_result",
        message={
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_abc",
                    "content": "File contents here",
                    "is_error": False,
                }
            ]
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    assert events[0].type == AgUiEventType.TOOL_CALL_RESULT
    assert events[0].tool_call_id == "tool_abc"
    assert events[0].tool_result == "File contents here"
    assert events[0].tool_is_error is False


def test_tool_result_truncation():
    long_content = "x" * 3000
    cli = CliEvent(
        type="user",
        subtype="tool_result",
        message={
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_abc",
                    "content": long_content,
                }
            ]
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    assert len(events[0].tool_result) < 2100
    assert "[truncated]" in events[0].tool_result


def test_tool_result_list_content():
    cli = CliEvent(
        type="user",
        subtype="tool_result",
        message={
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_abc",
                    "content": [
                        {"type": "text", "text": "Part 1"},
                        {"type": "text", "text": "Part 2"},
                    ],
                }
            ]
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    assert "Part 1" in events[0].tool_result
    assert "Part 2" in events[0].tool_result


def test_result_to_run_finished():
    cli = CliEvent(
        type="result",
        cost_usd=0.042,
        duration_ms=15000,
        num_turns=3,
        is_error=False,
        raw={
            "model": "claude-sonnet-4-20250514",
            "usage": {
                "input_tokens": 5000,
                "output_tokens": 1200,
                "cache_read_tokens": 3000,
                "cache_write_tokens": 500,
            },
        },
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    ev = events[0]
    assert ev.type == AgUiEventType.RUN_FINISHED
    assert ev.cost_usd == 0.042
    assert ev.duration_ms == 15000
    assert ev.num_turns == 3
    assert ev.input_tokens == 5000
    assert ev.output_tokens == 1200
    assert ev.model == "claude-sonnet-4-20250514"


def test_result_error_to_run_error():
    cli = CliEvent(
        type="result",
        is_error=True,
        raw={"error": "Permission denied"},
    )
    events = convert_cli_event(cli, SESSION)
    assert len(events) == 1
    assert events[0].type == AgUiEventType.RUN_ERROR
    assert events[0].error == "Permission denied"


def test_unknown_event_returns_empty():
    cli = CliEvent(type="something_else")
    events = convert_cli_event(cli, SESSION)
    assert events == []
