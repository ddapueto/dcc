import json

from dcc.engine.stream_parser import parse_cli_line


def test_parse_empty_line():
    assert parse_cli_line("") is None
    assert parse_cli_line("   ") is None


def test_parse_invalid_json():
    assert parse_cli_line("not json") is None
    assert parse_cli_line("{broken") is None


def test_parse_non_dict():
    assert parse_cli_line('"just a string"') is None
    assert parse_cli_line("[1, 2, 3]") is None


def test_parse_system_init():
    data = {
        "type": "system",
        "subtype": "init",
        "session_id": "abc123",
        "tools": ["Read", "Write"],
        "model": "claude-sonnet-4-20250514",
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "system"
    assert event.subtype == "init"
    assert event.session_id == "abc123"


def test_parse_assistant_text():
    data = {
        "type": "assistant",
        "message": {
            "content": [{"type": "text", "text": "Hello world"}]
        },
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "assistant"
    assert event.subtype == "text"


def test_parse_assistant_tool_use():
    data = {
        "type": "assistant",
        "message": {
            "content": [
                {
                    "type": "tool_use",
                    "id": "tool_1",
                    "name": "Read",
                    "input": {"file_path": "/tmp/test.py"},
                }
            ]
        },
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "assistant"
    assert event.subtype == "tool_use"


def test_parse_user_tool_result():
    data = {
        "type": "user",
        "message": {
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool_1",
                    "content": "File contents here",
                }
            ]
        },
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "user"
    assert event.subtype == "tool_result"


def test_parse_result():
    data = {
        "type": "result",
        "session_id": "abc123",
        "cost_usd": 0.042,
        "duration_ms": 15000,
        "num_turns": 3,
        "is_error": False,
        "usage": {
            "input_tokens": 5000,
            "output_tokens": 1200,
        },
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "result"
    assert event.cost_usd == 0.042
    assert event.duration_ms == 15000
    assert event.num_turns == 3
    assert event.is_error is False


def test_parse_result_error():
    data = {
        "type": "result",
        "is_error": True,
        "error": "Something went wrong",
    }
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "result"
    assert event.is_error is True


def test_parse_unknown_type():
    data = {"type": "stream_event", "subtype": "text_delta"}
    event = parse_cli_line(json.dumps(data))
    assert event is not None
    assert event.type == "stream_event"
