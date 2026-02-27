"""Procesa AG-UI events y construye arbol de tareas por sesion."""

import json
import logging
import time

from dcc.db import repository
from dcc.engine.types import AgUiEvent, AgUiEventType

logger = logging.getLogger(__name__)


class MonitorProcessor:
    """Procesa AG-UI events y construye arbol de tareas por sesion."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._task_stack: list[str] = []  # monitor_task_ids para detectar nesting
        self._tool_to_task: dict[str, str] = {}  # tool_call_id → monitor_task_id
        self._task_start_times: dict[str, float] = {}

    async def process_event(self, event: AgUiEvent) -> dict | None:
        """Procesa un evento. Retorna update dict si creo/actualizo un monitor task."""
        if event.type == AgUiEventType.TOOL_CALL_START:
            return await self._handle_tool_start(event)
        elif event.type == AgUiEventType.TOOL_CALL_RESULT:
            return await self._handle_tool_result(event)
        elif event.type == AgUiEventType.TOOL_CALL_END:
            return await self._handle_tool_end(event)
        return None

    async def _handle_tool_start(self, event: AgUiEvent) -> dict | None:
        if not event.tool_call_id or not event.tool_name:
            return None

        # Parent es el top del stack (task que spawnea subtasks)
        parent_id = self._task_stack[-1] if self._task_stack else None
        depth = len(self._task_stack)

        metadata = self._extract_task_metadata(event.tool_name, event.tool_input)
        input_summary = self._truncate(event.tool_input, 500)

        try:
            task_id = await repository.create_monitor_task(
                session_id=self.session_id,
                tool_call_id=event.tool_call_id,
                tool_name=event.tool_name,
                parent_id=parent_id,
                description=metadata["description"],
                input_summary=input_summary,
                depth=depth,
                subagent_type=metadata["subagent_type"],
                subagent_model=metadata["subagent_model"],
            )
        except Exception:
            logger.exception("Failed to create monitor task")
            return None

        self._tool_to_task[event.tool_call_id] = task_id
        self._task_start_times[task_id] = time.monotonic()

        # Si es un Task tool, push al stack (sus children seran subtasks)
        if event.tool_name == "Task":
            self._task_stack.append(task_id)

        return {
            "action": "created",
            "task_id": task_id,
            "tool_name": event.tool_name,
            "description": metadata["description"],
            "parent_id": parent_id,
            "depth": depth,
            "subagent_type": metadata["subagent_type"],
            "subagent_model": metadata["subagent_model"],
        }

    async def _handle_tool_result(self, event: AgUiEvent) -> dict | None:
        if not event.tool_call_id:
            return None

        task_id = self._tool_to_task.get(event.tool_call_id)
        if not task_id:
            return None

        status = "failed" if event.tool_is_error else "completed"
        duration_ms = None
        start = self._task_start_times.get(task_id)
        if start:
            duration_ms = int((time.monotonic() - start) * 1000)

        output_summary = self._truncate(event.tool_result, 500)

        try:
            await repository.update_monitor_task(
                task_id, status=status, output_summary=output_summary, duration_ms=duration_ms
            )
        except Exception:
            logger.exception("Failed to update monitor task")
            return None

        # Pop del stack si era un Task tool
        if task_id in self._task_stack:
            self._task_stack.remove(task_id)

        return {
            "action": "updated",
            "task_id": task_id,
            "status": status,
            "duration_ms": duration_ms,
        }

    async def _handle_tool_end(self, event: AgUiEvent) -> dict | None:
        """Fallback close si ToolCallResult no llego."""
        if not event.tool_call_id:
            return None

        task_id = self._tool_to_task.get(event.tool_call_id)
        if not task_id:
            return None

        # Solo actualizar si aun esta running (ToolCallResult ya lo cerro)
        try:
            tasks = await repository.get_monitor_tasks(self.session_id)
            for t in tasks:
                if t["id"] == task_id and t["status"] == "running":
                    duration_ms = None
                    start = self._task_start_times.get(task_id)
                    if start:
                        duration_ms = int((time.monotonic() - start) * 1000)

                    await repository.update_monitor_task(
                        task_id, status="completed", duration_ms=duration_ms
                    )

                    if task_id in self._task_stack:
                        self._task_stack.remove(task_id)

                    return {"action": "updated", "task_id": task_id, "status": "completed"}
        except Exception:
            logger.exception("Failed to handle tool end")
        return None

    @staticmethod
    def _extract_task_metadata(tool_name: str, tool_input: str | None) -> dict:
        """Extrae description, subagent_type y subagent_model del tool input."""
        result = {"description": tool_name, "subagent_type": None, "subagent_model": None}
        if not tool_input:
            return result

        try:
            parsed = json.loads(tool_input)
        except (json.JSONDecodeError, TypeError):
            return result

        if tool_name == "Task":
            result["description"] = (
                parsed.get("description") or parsed.get("prompt") or tool_name
            )[:200]
            result["subagent_type"] = parsed.get("subagent_type")
            result["subagent_model"] = parsed.get("model")
        elif tool_name in ("Read", "Write", "Edit"):
            result["description"] = parsed.get("file_path", tool_name)
        elif tool_name == "Bash":
            result["description"] = (parsed.get("command") or "")[:100] or tool_name
        elif tool_name in ("Glob", "Grep"):
            result["description"] = parsed.get("pattern", tool_name)
        return result

    @staticmethod
    def _truncate(text: str | None, max_len: int) -> str | None:
        if not text:
            return None
        return text[:max_len] if len(text) > max_len else text
