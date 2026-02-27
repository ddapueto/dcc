"""Tests for workflows API endpoints."""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from dcc.app import app
from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    settings.db_path = str(tmp_path / "test.db")
    await close_db()
    await init_db()

    await repository.upsert_tenant("t1", "Test", "/tmp/cfg", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/ws")

    yield

    await close_db()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_create_and_list_workflows(client: AsyncClient):
    # Crear
    resp = await client.post("/api/workflows", json={
        "workspace_id": "w1",
        "name": "My Workflow",
        "prompt_template": "Do {{task}}",
        "category": "development",
        "parameters": [{"key": "task", "label": "Task", "type": "textarea", "required": True}],
    })
    assert resp.status_code == 200
    wf_id = resp.json()["workflow_id"]

    # Listar
    resp = await client.get("/api/workflows", params={"workspace_id": "w1"})
    assert resp.status_code == 200
    workflows = resp.json()["workflows"]
    assert any(w["id"] == wf_id for w in workflows)


@pytest.mark.asyncio
async def test_get_workflow(client: AsyncClient):
    wf_id = await repository.create_workflow("w1", "Test", "prompt {{x}}")

    resp = await client.get(f"/api/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["workflow"]["name"] == "Test"


@pytest.mark.asyncio
async def test_update_workflow(client: AsyncClient):
    wf_id = await repository.create_workflow("w1", "Old", "old prompt")

    resp = await client.put(f"/api/workflows/{wf_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["updated"] is True

    wf = await repository.get_workflow(wf_id)
    assert wf["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_builtin_blocked(client: AsyncClient):
    wf_id = await repository.create_workflow("w1", "Builtin", "p", is_builtin=True)

    resp = await client.delete(f"/api/workflows/{wf_id}")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_launch_workflow(client: AsyncClient):
    wf_id = await repository.create_workflow(
        "w1", "Launcher", "Do {{task}} with {{tool}}",
        parameters=[
            {"key": "task", "label": "Task", "type": "text", "required": True},
            {"key": "tool", "label": "Tool", "type": "text", "required": False, "default": "pytest"},
        ],
    )

    resp = await client.post(f"/api/workflows/{wf_id}/launch", json={
        "workspace_id": "w1",
        "params": {"task": "implement auth"},
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["redirect"] == "/run"

    # Verificar session creada con prompt resuelto
    session = await repository.get_session(data["session_id"])
    assert session["prompt"] == "Do implement auth with pytest"
    assert session["workflow_id"] == wf_id

    # Verificar usage incrementado
    wf = await repository.get_workflow(wf_id)
    assert wf["usage_count"] == 1


@pytest.mark.asyncio
async def test_launch_workflow_missing_required_param(client: AsyncClient):
    wf_id = await repository.create_workflow(
        "w1", "Strict", "Do {{task}}",
        parameters=[{"key": "task", "label": "Task", "type": "text", "required": True}],
    )

    resp = await client.post(f"/api/workflows/{wf_id}/launch", json={
        "workspace_id": "w1",
        "params": {},
    })
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient):
    resp = await client.get("/api/workflows/categories")
    assert resp.status_code == 200
    cats = resp.json()["categories"]
    assert len(cats) == 5
    ids = [c["id"] for c in cats]
    assert "development" in ids
    assert "testing" in ids
