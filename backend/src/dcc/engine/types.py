from enum import Enum
from typing import Any

from pydantic import BaseModel


# --- CLI Events (from claude --output-format stream-json) ---


class CliEvent(BaseModel):
    """Raw event from Claude CLI NDJSON stream."""

    type: str  # system, assistant, user, result
    subtype: str | None = None  # init, text, tool_use, tool_result, etc.
    session_id: str | None = None
    message: dict[str, Any] | None = None
    # For result events
    cost_usd: float | None = None
    duration_ms: int | None = None
    duration_api_ms: int | None = None
    num_turns: int | None = None
    is_error: bool = False
    # Raw data for anything we don't parse
    raw: dict[str, Any] | None = None


# --- AG-UI Events (emitted via SSE to frontend) ---


class AgUiEventType(str, Enum):
    RUN_STARTED = "RunStarted"
    RUN_FINISHED = "RunFinished"
    RUN_ERROR = "RunError"
    TEXT_MESSAGE_START = "TextMessageStart"
    TEXT_MESSAGE_CONTENT = "TextMessageContent"
    TEXT_MESSAGE_END = "TextMessageEnd"
    TOOL_CALL_START = "ToolCallStart"
    TOOL_CALL_END = "ToolCallEnd"
    TOOL_CALL_RESULT = "ToolCallResult"
    STATE_SNAPSHOT = "StateSnapshot"
    CUSTOM = "Custom"


class AgUiEvent(BaseModel):
    type: AgUiEventType
    session_id: str
    timestamp: str | None = None
    # Text message fields
    message_id: str | None = None
    text: str | None = None
    role: str | None = None
    # Tool call fields
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_input: str | None = None
    tool_result: str | None = None
    tool_is_error: bool | None = None
    # Run fields
    model: str | None = None
    cost_usd: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cache_read_tokens: int | None = None
    cache_write_tokens: int | None = None
    num_turns: int | None = None
    duration_ms: int | None = None
    cli_session_id: str | None = None
    # State snapshot
    state: dict[str, Any] | None = None
    # Error
    error: str | None = None
    # Custom
    custom_type: str | None = None
    data: dict[str, Any] | None = None
