import asyncio
import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from dcc.db import repository
from dcc.engine.cli_runner import CliRunner
from dcc.engine.types import AgUiEventType

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

# Active runners indexed by session_id
_active_runners: dict[str, CliRunner] = {}


class CreateSessionRequest(BaseModel):
    workspace_id: str
    prompt: str
    skill: str | None = None
    agent: str | None = None
    model: str | None = None


@router.post("")
async def create_session(req: CreateSessionRequest):
    """Create a new session and return its ID."""
    ws = await repository.get_workspace(req.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    session_id = await repository.create_session(
        workspace_id=req.workspace_id,
        prompt=req.prompt,
        skill=req.skill,
        agent=req.agent,
        model=req.model,
    )

    return {"session_id": session_id}


@router.get("/history")
async def session_history(
    workspace_id: str | None = None,
    tenant_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    limit: int = 25,
    offset: int = 0,
):
    """Get session history with filters, search, and pagination."""
    sessions, total = await repository.get_sessions_with_search(
        workspace_id=workspace_id,
        tenant_id=tenant_id,
        status=status,
        search=search,
        limit=limit,
        offset=offset,
    )
    return {"sessions": sessions, "total": total, "limit": limit, "offset": offset}


@router.get("/{session_id}/events")
async def get_session_events(session_id: str):
    """Get all stored events for a session (for replay)."""
    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    events = await repository.get_session_events(session_id)
    return {"session": session, "events": events}


@router.get("/{session_id}/stream")
async def stream_session(session_id: str):
    """SSE endpoint that streams AG-UI events for a session."""
    session = await repository.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session["status"] not in ("running", "pending"):
        raise HTTPException(status_code=400, detail=f"Session is {session['status']}")

    ws = await repository.get_workspace(session["workspace_id"])
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")

    runner = CliRunner(
        session_id=session_id,
        workspace_path=ws["path"],
        config_dir=ws["config_dir"],
        prompt=session["prompt"],
        skill=session.get("skill"),
        agent=session.get("agent"),
        model=session.get("model"),
    )
    _active_runners[session_id] = runner

    async def event_generator():
        start_time = time.monotonic()
        event_buffer: list[tuple[str, int, str, str]] = []
        seq = 0
        try:
            async for event in runner.run():
                data = event.model_dump_json(exclude_none=True)
                yield {"event": event.type.value, "data": data}

                # Buffer event for persistence
                event_buffer.append((session_id, seq, event.type.value, data))
                seq += 1

                # Update DB on finish
                if event.type in (AgUiEventType.RUN_FINISHED, AgUiEventType.RUN_ERROR):
                    elapsed_ms = int((time.monotonic() - start_time) * 1000)
                    status = (
                        "completed" if event.type == AgUiEventType.RUN_FINISHED else "error"
                    )
                    await repository.update_session_finished(
                        session_id=session_id,
                        status=status,
                        model=event.model,
                        cost_usd=event.cost_usd,
                        input_tokens=event.input_tokens,
                        output_tokens=event.output_tokens,
                        num_turns=event.num_turns,
                        duration_ms=event.duration_ms or elapsed_ms,
                        cli_session_id=event.cli_session_id,
                    )
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled for session %s", session_id)
            await runner.cancel()
        finally:
            # Persist buffered events
            if event_buffer:
                try:
                    await repository.insert_session_events_batch(event_buffer)
                except Exception:
                    logger.exception("Failed to persist events for session %s", session_id)

            # Persist diff capture
            if runner.diff_capture and (
                runner.diff_capture.diff_stat or runner.diff_capture.diff_content
            ):
                try:
                    dc = runner.diff_capture
                    await repository.insert_session_diff(
                        session_id=session_id,
                        diff_stat=dc.diff_stat,
                        diff_content=dc.diff_content,
                        files_changed=dc.files_changed,
                        insertions=dc.insertions,
                        deletions=dc.deletions,
                    )
                except Exception:
                    logger.exception("Failed to persist diff for session %s", session_id)

            _active_runners.pop(session_id, None)

    return EventSourceResponse(event_generator())


@router.post("/{session_id}/cancel")
async def cancel_session(session_id: str):
    """Cancel a running session."""
    runner = _active_runners.get(session_id)
    if not runner:
        raise HTTPException(status_code=404, detail="No active runner for this session")

    await runner.cancel()
    await repository.update_session_finished(session_id=session_id, status="cancelled")
    return {"status": "cancelled"}


@router.get("/{session_id}/diff")
async def get_session_diff(session_id: str):
    """Get captured git diff for a session."""
    diff = await repository.get_session_diff(session_id)
    return {"has_diff": bool(diff), "diff": diff}


@router.get("")
async def list_sessions(workspace_id: str | None = None, limit: int = 50):
    """List recent sessions, optionally filtered by workspace."""
    sessions = await repository.get_sessions(workspace_id=workspace_id, limit=limit)
    return {"sessions": sessions}
