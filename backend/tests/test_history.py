"""Tests for session history: events persistence and search."""

import pytest
import pytest_asyncio

from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    """Init in-memory DB for each test."""
    settings.db_path = str(tmp_path / "test.db")
    await close_db()
    await init_db()

    # Seed a tenant + workspace for FK constraints
    await repository.upsert_tenant("t1", "Test Tenant", "/tmp/config", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/test-ws")
    await repository.upsert_tenant("t2", "Other Tenant", "/tmp/config2", "claude-other")
    await repository.upsert_workspace("w2", "t2", "OtherWS", "/tmp/other-ws")

    yield

    await close_db()


# --- insert_session_events_batch + get_session_events ---


@pytest.mark.asyncio
async def test_insert_and_get_events():
    sid = await repository.create_session("w1", "test prompt")
    events = [
        (sid, 0, "RunStarted", '{"type":"RunStarted"}'),
        (sid, 1, "TextMessageContent", '{"type":"TextMessageContent","text":"hello"}'),
        (sid, 2, "RunFinished", '{"type":"RunFinished"}'),
    ]
    await repository.insert_session_events_batch(events)

    result = await repository.get_session_events(sid)
    assert len(result) == 3
    assert result[0]["seq"] == 0
    assert result[0]["event_type"] == "RunStarted"
    assert result[1]["seq"] == 1
    assert result[2]["seq"] == 2
    assert result[2]["event_type"] == "RunFinished"


@pytest.mark.asyncio
async def test_insert_empty_batch():
    await repository.insert_session_events_batch([])
    # No error — just a no-op


@pytest.mark.asyncio
async def test_get_events_empty():
    sid = await repository.create_session("w1", "no events")
    result = await repository.get_session_events(sid)
    assert result == []


@pytest.mark.asyncio
async def test_events_ordered_by_seq():
    sid = await repository.create_session("w1", "ordering test")
    events = [
        (sid, 2, "RunFinished", '{"seq":2}'),
        (sid, 0, "RunStarted", '{"seq":0}'),
        (sid, 1, "TextMessageContent", '{"seq":1}'),
    ]
    await repository.insert_session_events_batch(events)

    result = await repository.get_session_events(sid)
    assert [e["seq"] for e in result] == [0, 1, 2]


# --- get_sessions_with_search ---


@pytest.mark.asyncio
async def test_search_no_filters():
    await repository.create_session("w1", "prompt one")
    await repository.create_session("w1", "prompt two")
    await repository.create_session("w2", "prompt three")

    sessions, total = await repository.get_sessions_with_search()
    assert total == 3
    assert len(sessions) == 3
    # Has workspace_name from JOIN
    assert "workspace_name" in sessions[0]
    assert "tenant_name" in sessions[0]


@pytest.mark.asyncio
async def test_search_by_workspace():
    await repository.create_session("w1", "in w1")
    await repository.create_session("w2", "in w2")

    sessions, total = await repository.get_sessions_with_search(workspace_id="w1")
    assert total == 1
    assert sessions[0]["workspace_id"] == "w1"


@pytest.mark.asyncio
async def test_search_by_tenant():
    await repository.create_session("w1", "tenant1 session")
    await repository.create_session("w2", "tenant2 session")

    sessions, total = await repository.get_sessions_with_search(tenant_id="t1")
    assert total == 1
    assert sessions[0]["tenant_name"] == "Test Tenant"


@pytest.mark.asyncio
async def test_search_by_status():
    s1 = await repository.create_session("w1", "running one")
    await repository.create_session("w1", "running two")
    await repository.update_session_finished(s1, status="completed")

    sessions, total = await repository.get_sessions_with_search(status="completed")
    assert total == 1
    assert sessions[0]["id"] == s1


@pytest.mark.asyncio
async def test_search_by_prompt_text():
    await repository.create_session("w1", "fix authentication bug")
    await repository.create_session("w1", "add new feature")
    await repository.create_session("w1", "refactor auth module")

    sessions, total = await repository.get_sessions_with_search(search="auth")
    assert total == 2


@pytest.mark.asyncio
async def test_search_pagination():
    for i in range(10):
        await repository.create_session("w1", f"prompt {i}")

    sessions, total = await repository.get_sessions_with_search(limit=3, offset=0)
    assert total == 10
    assert len(sessions) == 3

    sessions2, total2 = await repository.get_sessions_with_search(limit=3, offset=3)
    assert total2 == 10
    assert len(sessions2) == 3
    # No overlap
    ids1 = {s["id"] for s in sessions}
    ids2 = {s["id"] for s in sessions2}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_search_combined_filters():
    s1 = await repository.create_session("w1", "fix auth in t1")
    s2 = await repository.create_session("w2", "fix auth in t2")
    await repository.update_session_finished(s1, status="completed")
    await repository.update_session_finished(s2, status="completed")

    sessions, total = await repository.get_sessions_with_search(
        tenant_id="t1", status="completed", search="auth"
    )
    assert total == 1
    assert sessions[0]["id"] == s1


# --- Session Diffs ---


@pytest.mark.asyncio
async def test_insert_and_get_session_diff():
    sid = await repository.create_session("w1", "diff test")
    await repository.insert_session_diff(
        session_id=sid,
        diff_stat="3 files changed, 42 insertions(+), 5 deletions(-)",
        diff_content="diff --git a/foo.py b/foo.py\n+new line",
        files_changed=3,
        insertions=42,
        deletions=5,
    )
    diff = await repository.get_session_diff(sid)
    assert diff is not None
    assert diff["files_changed"] == 3
    assert diff["insertions"] == 42
    assert diff["deletions"] == 5
    assert "foo.py" in diff["diff_content"]


@pytest.mark.asyncio
async def test_get_session_diff_not_found():
    sid = await repository.create_session("w1", "no diff")
    diff = await repository.get_session_diff(sid)
    assert diff is None
