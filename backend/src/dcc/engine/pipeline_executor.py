"""Pipeline execution engine — ejecuta steps con dependencias en paralelo/secuencial."""

import asyncio
import logging
import time
from collections.abc import AsyncIterator

from dcc.db import repository
from dcc.engine.cli_runner import CliRunner
from dcc.engine.plan_builder import resolve_prompt_template
from dcc.engine.types import AgUiEvent, AgUiEventType

logger = logging.getLogger(__name__)

OUTPUT_SUMMARY_MAX = 2000


class PipelineExecutor:
    """Ejecuta un pipeline respetando dependencias entre steps."""

    def __init__(self, pipeline_id: str, max_parallel: int = 3):
        self.pipeline_id = pipeline_id
        self.max_parallel = max_parallel
        self._cancelled = False
        self._paused = False
        self._active_runners: dict[str, CliRunner] = {}
        self._step_outputs: dict[str, str] = {}

    async def run(self) -> AsyncIterator[AgUiEvent]:
        """Loop principal del executor."""
        pipeline = await repository.get_pipeline(self.pipeline_id)
        if not pipeline:
            return

        ws = await repository.get_workspace(pipeline["workspace_id"])
        if not ws:
            return

        steps = await repository.get_pipeline_steps(self.pipeline_id)
        if not steps:
            return

        total_steps = len(steps)
        completed_count = 0
        failed_ids: set[str] = set()
        completed_ids: set[str] = set()
        running_tasks: dict[str, asyncio.Task] = {}
        total_cost = 0.0
        start_time = time.monotonic()

        # Marcar pipeline como running
        await repository.update_pipeline_status(self.pipeline_id, "running")

        yield AgUiEvent(
            type=AgUiEventType.PIPELINE_STARTED,
            session_id=self.pipeline_id,
            pipeline_id=self.pipeline_id,
            steps_total=total_steps,
        )

        try:
            while not self._cancelled:
                if self._paused:
                    await asyncio.sleep(0.5)
                    continue

                # Refresh steps
                steps = await repository.get_pipeline_steps(self.pipeline_id)
                step_map = {s["id"]: s for s in steps}

                # Encontrar steps listos (pending + todas deps completadas)
                ready = []
                for step in steps:
                    if step["status"] != "pending":
                        continue
                    if step["id"] in running_tasks:
                        continue
                    deps = step.get("depends_on", [])
                    # Skip si alguna dep falló
                    if any(d in failed_ids for d in deps):
                        await repository.update_pipeline_step_status(
                            step["id"], "skipped"
                        )
                        completed_count += 1
                        continue
                    # Listo si todas las deps están completadas
                    if all(d in completed_ids for d in deps):
                        ready.append(step)

                # Limitar paralelismo
                slots = self.max_parallel - len(running_tasks)
                to_launch = ready[:slots]

                for step in to_launch:
                    task = asyncio.create_task(
                        self._execute_step(step, ws, pipeline)
                    )
                    running_tasks[step["id"]] = task

                # Si no hay running ni ready, terminamos
                if not running_tasks:
                    # Verificar si quedan pendientes
                    pending = [s for s in steps if s["status"] == "pending"]
                    if not pending:
                        break
                    # Todos pendientes están bloqueados por failures
                    if not to_launch:
                        # Marcar restantes como skipped
                        for s in pending:
                            if s["id"] not in running_tasks:
                                await repository.update_pipeline_step_status(
                                    s["id"], "skipped"
                                )
                                completed_count += 1
                        break

                # Esperar a que termine al menos una tarea
                if running_tasks:
                    done, _ = await asyncio.wait(
                        running_tasks.values(), return_when=asyncio.FIRST_COMPLETED
                    )
                    for task in done:
                        # Encontrar step_id de esta task
                        step_id = None
                        for sid, t in running_tasks.items():
                            if t is task:
                                step_id = sid
                                break
                        if step_id:
                            del running_tasks[step_id]

                        try:
                            result = task.result()
                            r_step_id, success, cost, events = result
                            if cost:
                                total_cost += cost
                            if success:
                                completed_ids.add(r_step_id)
                            else:
                                failed_ids.add(r_step_id)
                            completed_count += 1

                            for ev in events:
                                yield ev
                        except Exception:
                            logger.exception("Step task failed unexpectedly")
                            if step_id:
                                failed_ids.add(step_id)
                                completed_count += 1

        except asyncio.CancelledError:
            self._cancelled = True
            for runner in self._active_runners.values():
                await runner.cancel()

        # Determinar status final
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        final_status = "completed" if not failed_ids else "failed"
        if self._cancelled:
            final_status = "failed"

        await repository.update_pipeline_status(
            self.pipeline_id,
            final_status,
            total_cost=total_cost,
            total_duration_ms=elapsed_ms,
        )

        final_event_type = (
            AgUiEventType.PIPELINE_COMPLETED
            if final_status == "completed"
            else AgUiEventType.PIPELINE_FAILED
        )
        yield AgUiEvent(
            type=final_event_type,
            session_id=self.pipeline_id,
            pipeline_id=self.pipeline_id,
            steps_completed=completed_count,
            steps_total=total_steps,
            cost_usd=total_cost,
            duration_ms=elapsed_ms,
        )

    async def _execute_step(
        self, step: dict, workspace: dict, pipeline: dict
    ) -> tuple[str, bool, float | None, list[AgUiEvent]]:
        """Ejecuta un step individual. Retorna (step_id, success, cost, events)."""
        step_id = step["id"]
        events: list[AgUiEvent] = []

        # Build context para prompt template
        context = self._build_step_context(step, pipeline)
        prompt = step.get("prompt_template") or step.get("description") or step["name"]
        prompt = resolve_prompt_template(prompt, context)

        # Crear sesión real
        session_id = await repository.create_session(
            workspace_id=pipeline["workspace_id"],
            prompt=prompt[:500],
            agent=step.get("agent"),
            skill=step.get("skill"),
            model=step.get("model"),
        )

        # Marcar step running
        await repository.update_pipeline_step_status(
            step_id, "running", session_id=session_id
        )

        events.append(AgUiEvent(
            type=AgUiEventType.PIPELINE_STEP_STARTED,
            session_id=session_id,
            pipeline_id=self.pipeline_id,
            step_id=step_id,
            step_name=step["name"],
            step_position=step["position"],
            step_agent=step.get("agent"),
        ))

        # Ejecutar CliRunner
        runner = CliRunner(
            session_id=session_id,
            workspace_path=workspace["path"],
            config_dir=workspace.get("config_dir", "~/.claude-personal"),
            prompt=prompt,
            skill=step.get("skill"),
            agent=step.get("agent"),
            model=step.get("model"),
        )
        self._active_runners[step_id] = runner

        output_text = ""
        cost: float | None = None
        success = True

        try:
            async for event in runner.run():
                if hasattr(event, "text") and event.text:
                    output_text += event.text
                if event.type == AgUiEventType.RUN_FINISHED:
                    cost = event.cost_usd
                    await repository.update_session_finished(
                        session_id=session_id,
                        status="completed",
                        model=event.model,
                        cost_usd=event.cost_usd,
                        input_tokens=event.input_tokens,
                        output_tokens=event.output_tokens,
                        num_turns=event.num_turns,
                        duration_ms=event.duration_ms,
                        cli_session_id=event.cli_session_id,
                    )
                elif event.type == AgUiEventType.RUN_ERROR:
                    success = False
                    await repository.update_session_finished(
                        session_id=session_id,
                        status="error",
                        model=event.model,
                        cost_usd=event.cost_usd,
                    )

            # Guardar output summary
            summary = output_text[:OUTPUT_SUMMARY_MAX] if output_text else None
            self._step_outputs[step_id] = output_text

            if success:
                await repository.update_pipeline_step_status(
                    step_id, "completed", output_summary=summary
                )
                events.append(AgUiEvent(
                    type=AgUiEventType.PIPELINE_STEP_COMPLETED,
                    session_id=session_id,
                    pipeline_id=self.pipeline_id,
                    step_id=step_id,
                    step_name=step["name"],
                    step_position=step["position"],
                    cost_usd=cost,
                ))
            else:
                await repository.update_pipeline_step_status(
                    step_id, "failed", output_summary=summary
                )
                events.append(AgUiEvent(
                    type=AgUiEventType.PIPELINE_STEP_FAILED,
                    session_id=session_id,
                    pipeline_id=self.pipeline_id,
                    step_id=step_id,
                    step_name=step["name"],
                    step_position=step["position"],
                    error=output_text[:500] if output_text else "Step failed",
                ))

        except Exception as e:
            logger.exception("Step %s execution error", step_id)
            success = False
            await repository.update_pipeline_step_status(step_id, "failed")
            events.append(AgUiEvent(
                type=AgUiEventType.PIPELINE_STEP_FAILED,
                session_id=session_id,
                pipeline_id=self.pipeline_id,
                step_id=step_id,
                step_name=step["name"],
                error=str(e),
            ))
        finally:
            self._active_runners.pop(step_id, None)

        return step_id, success, cost, events

    def _build_step_context(self, step: dict, pipeline: dict) -> dict[str, str]:
        """Build contexto para resolver prompt templates."""
        context: dict[str, str] = {}

        if pipeline.get("spec"):
            context["spec"] = pipeline["spec"]

        # {{prev_output}} = output de la primera dependencia
        deps = step.get("depends_on", [])
        if deps and deps[0] in self._step_outputs:
            context["prev_output"] = self._step_outputs[deps[0]][:OUTPUT_SUMMARY_MAX]

        # {{step.ID.output}} para cada step previo
        for sid, output in self._step_outputs.items():
            context[f"step.{sid}.output"] = output[:OUTPUT_SUMMARY_MAX]

        return context

    async def cancel(self):
        """Cancelar la ejecución del pipeline."""
        self._cancelled = True
        for runner in self._active_runners.values():
            await runner.cancel()

    def pause(self):
        """Pausar (no lanza nuevos steps)."""
        self._paused = True

    def resume(self):
        """Reanudar ejecución."""
        self._paused = False
