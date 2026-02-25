import json
import uuid
from datetime import datetime, timezone

from dcc.engine.types import AgUiEvent, AgUiEventType, CliEvent

MAX_TOOL_RESULT_LEN = 2000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_message_id() -> str:
    return str(uuid.uuid4())[:8]


def convert_cli_event(cli: CliEvent, session_id: str) -> list[AgUiEvent]:
    """Convert a CLI event to one or more AG-UI events."""
    events: list[AgUiEvent] = []
    ts = _now_iso()

    # --- system/init → StateSnapshot ---
    if cli.type == "system" and cli.subtype == "init":
        raw = cli.raw or {}
        events.append(
            AgUiEvent(
                type=AgUiEventType.STATE_SNAPSHOT,
                session_id=session_id,
                timestamp=ts,
                cli_session_id=raw.get("session_id"),
                state={
                    "tools": raw.get("tools", []),
                    "model": raw.get("model"),
                    "mcp_servers": raw.get("mcp_servers", []),
                },
            )
        )
        return events

    # --- assistant with text → TextMessage* ---
    if cli.type == "assistant":
        message = cli.message or {}
        content_list = message.get("content", [])

        for block in content_list:
            if not isinstance(block, dict):
                continue

            block_type = block.get("type")

            if block_type == "text":
                msg_id = _make_message_id()
                text = block.get("text", "")
                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TEXT_MESSAGE_START,
                        session_id=session_id,
                        timestamp=ts,
                        message_id=msg_id,
                        role="assistant",
                    )
                )
                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TEXT_MESSAGE_CONTENT,
                        session_id=session_id,
                        timestamp=ts,
                        message_id=msg_id,
                        text=text,
                    )
                )
                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TEXT_MESSAGE_END,
                        session_id=session_id,
                        timestamp=ts,
                        message_id=msg_id,
                    )
                )

            elif block_type == "tool_use":
                tool_id = block.get("id", _make_message_id())
                tool_name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                input_str = (
                    json.dumps(tool_input, ensure_ascii=False)
                    if isinstance(tool_input, dict)
                    else str(tool_input)
                )
                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TOOL_CALL_START,
                        session_id=session_id,
                        timestamp=ts,
                        tool_call_id=tool_id,
                        tool_name=tool_name,
                        tool_input=input_str,
                    )
                )
                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TOOL_CALL_END,
                        session_id=session_id,
                        timestamp=ts,
                        tool_call_id=tool_id,
                    )
                )

        return events

    # --- user with tool_result → ToolCallResult ---
    if cli.type == "user":
        message = cli.message or {}
        content_list = message.get("content", [])

        for block in content_list:
            if not isinstance(block, dict):
                continue

            if block.get("type") == "tool_result":
                tool_id = block.get("tool_use_id", "")
                content = block.get("content", "")

                # Content can be string or list of content blocks
                if isinstance(content, list):
                    parts = []
                    for part in content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            parts.append(part.get("text", ""))
                    result_text = "\n".join(parts)
                else:
                    result_text = str(content)

                # Truncate large results
                if len(result_text) > MAX_TOOL_RESULT_LEN:
                    result_text = result_text[:MAX_TOOL_RESULT_LEN] + "\n... [truncated]"

                events.append(
                    AgUiEvent(
                        type=AgUiEventType.TOOL_CALL_RESULT,
                        session_id=session_id,
                        timestamp=ts,
                        tool_call_id=tool_id,
                        tool_result=result_text,
                        tool_is_error=block.get("is_error", False),
                    )
                )

        return events

    # --- result → RunFinished ---
    if cli.type == "result":
        raw = cli.raw or {}
        usage = raw.get("usage", {})

        if cli.is_error:
            events.append(
                AgUiEvent(
                    type=AgUiEventType.RUN_ERROR,
                    session_id=session_id,
                    timestamp=ts,
                    error=raw.get("error", "Unknown error"),
                )
            )
        else:
            events.append(
                AgUiEvent(
                    type=AgUiEventType.RUN_FINISHED,
                    session_id=session_id,
                    timestamp=ts,
                    cost_usd=cli.cost_usd,
                    duration_ms=cli.duration_ms,
                    num_turns=cli.num_turns,
                    input_tokens=usage.get("input_tokens"),
                    output_tokens=usage.get("output_tokens"),
                    cache_read_tokens=usage.get("cache_read_tokens"),
                    cache_write_tokens=usage.get("cache_write_tokens"),
                    model=raw.get("model"),
                )
            )

        return events

    return events
