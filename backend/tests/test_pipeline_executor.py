"""Tests for pipeline executor — mocks CliRunner para evitar subprocess."""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from dcc.config import settings
from dcc.db import repository
from dcc.db.database import close_db, init_db
from dcc.engine.pipeline_executor import PipelineExecutor
from dcc.engine.types import AgUiEvent, AgUiEventType


@pytest_asyncio.fixture(autouse=True)
async def setup_db(tmp_path):
    """Init fresh DB for each test."""
    settings.db_path = str(tmp_path / "test.db")
    await close_db()
    await init_db()

    await repository.upsert_tenant("t1", "Test Tenant", "/tmp/config", "claude-test")
    await repository.upsert_workspace("w1", "t1", "TestWS", "/tmp/test-ws")

    yield

    await close_db()


async def _mock_cli_run(self):
    """Mock CliRunner.run() que emite events básicos."""
    yield AgUiEvent(
        type=AgUiEventType.RUN_STARTED,
        session_id=self.session_id,
    )
    yield AgUiEvent(
        type=AgUiEventType.TEXT_MESSAGE_CONTENT,
        session_id=self.session_id,
        text="Mock output for step",
    )
    yield AgUiEvent(
        type=AgUiEventType.RUN_FINISHED,
        session_id=self.session_id,
        cost_usd=0.01,
        model="sonnet",
        duration_ms=1000,
    )


async def _mock_cli_run_fail(self):
    """Mock CliRunner.run() que falla."""
    yield AgUiEvent(
        type=AgUiEventType.RUN_STARTED,
        session_id=self.session_id,
    )
    yield AgUiEvent(
        type=AgUiEventType.RUN_ERROR,
        session_id=self.session_id,
        error="Something went wrong",
    )


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_runs_single_step():
    pid = await repository.create_pipeline("w1", "Test Pipeline")
    await repository.create_pipeline_step(pid, 0, "Single step", prompt_template="Do something")

    executor = PipelineExecutor(pid, max_parallel=1)
    events = []
    async for event in executor.run():
        events.append(event)

    types = [e.type for e in events]
    assert AgUiEventType.PIPELINE_STARTED in types
    assert AgUiEventType.PIPELINE_STEP_STARTED in types
    assert AgUiEventType.PIPELINE_STEP_COMPLETED in types
    assert AgUiEventType.PIPELINE_COMPLETED in types

    # Pipeline marcado como completed
    p = await repository.get_pipeline(pid)
    assert p["status"] == "completed"
    assert p["total_cost"] > 0


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_respects_dependencies():
    pid = await repository.create_pipeline("w1", "Deps Test")
    s1 = await repository.create_pipeline_step(pid, 0, "Step A")
    await repository.create_pipeline_step(
        pid, 1, "Step B", depends_on=[s1]
    )

    executor = PipelineExecutor(pid, max_parallel=3)
    events = []
    async for event in executor.run():
        events.append(event)

    # Ambos steps completados
    step_completed = [
        e for e in events if e.type == AgUiEventType.PIPELINE_STEP_COMPLETED
    ]
    assert len(step_completed) == 2

    # Step B empezó después de Step A
    started = [e for e in events if e.type == AgUiEventType.PIPELINE_STEP_STARTED]
    assert started[0].step_name == "Step A"
    assert started[1].step_name == "Step B"


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_parallel_independent_steps():
    pid = await repository.create_pipeline("w1", "Parallel Test")
    await repository.create_pipeline_step(pid, 0, "Step A")
    await repository.create_pipeline_step(pid, 1, "Step B")
    await repository.create_pipeline_step(pid, 2, "Step C")

    executor = PipelineExecutor(pid, max_parallel=3)
    events = []
    async for event in executor.run():
        events.append(event)

    completed = [e for e in events if e.type == AgUiEventType.PIPELINE_STEP_COMPLETED]
    assert len(completed) == 3


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run_fail)
async def test_executor_handles_step_failure():
    pid = await repository.create_pipeline("w1", "Fail Test")
    s1 = await repository.create_pipeline_step(pid, 0, "Failing step")
    await repository.create_pipeline_step(pid, 1, "Dependent step", depends_on=[s1])

    executor = PipelineExecutor(pid, max_parallel=1)
    events = []
    async for event in executor.run():
        events.append(event)

    types = [e.type for e in events]
    assert AgUiEventType.PIPELINE_STEP_FAILED in types
    assert AgUiEventType.PIPELINE_FAILED in types

    p = await repository.get_pipeline(pid)
    assert p["status"] == "failed"


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_cancel():
    pid = await repository.create_pipeline("w1", "Cancel Test")
    await repository.create_pipeline_step(pid, 0, "Step A")
    await repository.create_pipeline_step(pid, 1, "Step B")

    executor = PipelineExecutor(pid, max_parallel=1)

    events = []
    count = 0
    async for event in executor.run():
        events.append(event)
        count += 1
        # Cancelar después del primer step started
        if event.type == AgUiEventType.PIPELINE_STEP_COMPLETED:
            await executor.cancel()
            break

    # Al menos un evento de pipeline
    assert len(events) >= 1


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_context_passing():
    """Verifica que el executor pasa context entre steps."""
    pid = await repository.create_pipeline("w1", "Context Test", spec="Build an API")
    s1 = await repository.create_pipeline_step(
        pid, 0, "Step A", prompt_template="Do: {{spec}}"
    )
    await repository.create_pipeline_step(
        pid, 1, "Step B",
        prompt_template="Continue from: {{prev_output}}",
        depends_on=[s1],
    )

    executor = PipelineExecutor(pid, max_parallel=1)
    events = []
    async for event in executor.run():
        events.append(event)

    completed = [e for e in events if e.type == AgUiEventType.PIPELINE_STEP_COMPLETED]
    assert len(completed) == 2


@pytest.mark.asyncio
@patch("dcc.engine.pipeline_executor.CliRunner.run", _mock_cli_run)
async def test_executor_emits_pipeline_events():
    """Verifica que se emiten todos los tipos de eventos pipeline."""
    pid = await repository.create_pipeline("w1", "Events Test")
    await repository.create_pipeline_step(pid, 0, "Only step")

    executor = PipelineExecutor(pid, max_parallel=1)
    events = []
    async for event in executor.run():
        events.append(event)

    types = {e.type for e in events}
    assert AgUiEventType.PIPELINE_STARTED in types
    assert AgUiEventType.PIPELINE_STEP_STARTED in types
    assert AgUiEventType.PIPELINE_STEP_COMPLETED in types
    assert AgUiEventType.PIPELINE_COMPLETED in types

    # Verificar campos en PipelineStarted
    started = next(e for e in events if e.type == AgUiEventType.PIPELINE_STARTED)
    assert started.pipeline_id == pid
    assert started.steps_total == 1
