import json
import logging

from dcc.engine.types import CliEvent

logger = logging.getLogger(__name__)


def parse_cli_line(line: str) -> CliEvent | None:
    """Parse a single NDJSON line from Claude CLI stream-json output.

    Returns None for empty lines or unparseable content.
    """
    line = line.strip()
    if not line:
        return None

    try:
        data = json.loads(line)
    except json.JSONDecodeError:
        logger.warning("Failed to parse CLI line: %s", line[:200])
        return None

    if not isinstance(data, dict):
        return None

    event_type = data.get("type", "")

    if event_type == "system":
        return CliEvent(
            type="system",
            subtype=data.get("subtype"),
            session_id=data.get("session_id"),
            message=data,
            raw=data,
        )

    if event_type == "assistant":
        message = data.get("message", {})
        content_list = message.get("content", [])

        # Determine subtype from content
        subtype = None
        if content_list:
            first = content_list[0] if isinstance(content_list, list) else {}
            subtype = first.get("type") if isinstance(first, dict) else None

        return CliEvent(
            type="assistant",
            subtype=subtype,
            session_id=data.get("session_id"),
            message=message,
            raw=data,
        )

    if event_type == "user":
        message = data.get("message", {})
        content_list = message.get("content", [])

        subtype = None
        if content_list:
            first = content_list[0] if isinstance(content_list, list) else {}
            subtype = first.get("type") if isinstance(first, dict) else None

        return CliEvent(
            type="user",
            subtype=subtype,
            session_id=data.get("session_id"),
            message=message,
            raw=data,
        )

    if event_type == "result":
        return CliEvent(
            type="result",
            session_id=data.get("session_id"),
            cost_usd=data.get("cost_usd"),
            duration_ms=data.get("duration_ms"),
            duration_api_ms=data.get("duration_api_ms"),
            num_turns=data.get("num_turns"),
            is_error=data.get("is_error", False),
            message=data,
            raw=data,
        )

    # Catch-all for unknown types (e.g., stream_event for partial messages)
    return CliEvent(
        type=event_type,
        subtype=data.get("subtype"),
        session_id=data.get("session_id"),
        message=data,
        raw=data,
    )
