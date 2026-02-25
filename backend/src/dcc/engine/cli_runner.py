import asyncio
import logging
import os
import time
from collections.abc import AsyncIterator

from dcc.config import settings
from dcc.engine.event_converter import convert_cli_event
from dcc.engine.stream_parser import parse_cli_line
from dcc.engine.types import AgUiEvent, AgUiEventType

logger = logging.getLogger(__name__)

RESULT_TIMEOUT_S = 300  # 5 min max for a CLI run


class CliRunner:
    """Spawns Claude CLI as subprocess and yields AG-UI events."""

    def __init__(
        self,
        session_id: str,
        workspace_path: str,
        config_dir: str,
        prompt: str,
        skill: str | None = None,
        agent: str | None = None,
        model: str | None = None,
    ):
        self.session_id = session_id
        self.workspace_path = workspace_path
        self.config_dir = config_dir
        self.prompt = prompt
        self.skill = skill
        self.agent = agent
        self.model = model
        self._process: asyncio.subprocess.Process | None = None
        self._cancelled = False

    def _build_command(self) -> list[str]:
        cmd = [
            settings.claude_bin,
            "--print",
            "--output-format",
            "stream-json",
            "--verbose",
            "--dangerously-skip-permissions",
        ]

        if self.model:
            cmd.extend(["--model", self.model])

        # Build the prompt: if skill, prefix with /skill_name
        prompt = self.prompt
        if self.skill:
            prompt = f"/{self.skill} {prompt}"

        cmd.append(prompt)
        return cmd

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["CLAUDE_CONFIG_DIR"] = self.config_dir
        # Bug #573: unset CLAUDECODE to prevent inherited env issues
        env.pop("CLAUDECODE", None)
        return env

    async def run(self) -> AsyncIterator[AgUiEvent]:
        """Run CLI subprocess and yield AG-UI events."""
        cmd = self._build_command()
        env = self._build_env()

        logger.info("Starting CLI: %s (cwd=%s)", " ".join(cmd), self.workspace_path)

        # Emit RunStarted
        yield AgUiEvent(
            type=AgUiEventType.RUN_STARTED,
            session_id=self.session_id,
        )

        start_time = time.monotonic()
        got_result = False

        try:
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace_path,
                env=env,
            )

            assert self._process.stdout is not None

            async for raw_line in self._process.stdout:
                if self._cancelled:
                    break

                line = raw_line.decode("utf-8", errors="replace")
                cli_event = parse_cli_line(line)
                if cli_event is None:
                    continue

                ag_events = convert_cli_event(cli_event, self.session_id)
                for ev in ag_events:
                    yield ev
                    if ev.type == AgUiEventType.RUN_FINISHED:
                        got_result = True
                    elif ev.type == AgUiEventType.RUN_ERROR:
                        got_result = True

            await self._process.wait()

            # Check stderr for errors
            if self._process.returncode != 0 and not got_result:
                stderr = ""
                if self._process.stderr:
                    stderr_bytes = await self._process.stderr.read()
                    stderr = stderr_bytes.decode("utf-8", errors="replace")[:500]
                yield AgUiEvent(
                    type=AgUiEventType.RUN_ERROR,
                    session_id=self.session_id,
                    error=f"CLI exited with code {self._process.returncode}: {stderr}",
                )
                got_result = True

        except Exception as e:
            logger.exception("CLI runner error")
            yield AgUiEvent(
                type=AgUiEventType.RUN_ERROR,
                session_id=self.session_id,
                error=str(e),
            )
            got_result = True

        finally:
            # Fallback: synthetic RunFinished if no result event arrived (bug #1920)
            if not got_result:
                elapsed_ms = int((time.monotonic() - start_time) * 1000)
                logger.warning("No result event from CLI, emitting synthetic RunFinished")
                yield AgUiEvent(
                    type=AgUiEventType.RUN_FINISHED,
                    session_id=self.session_id,
                    duration_ms=elapsed_ms,
                )

    async def cancel(self):
        """Cancel the running CLI subprocess."""
        self._cancelled = True
        if self._process and self._process.returncode is None:
            logger.info("Cancelling CLI subprocess (pid=%s)", self._process.pid)
            try:
                self._process.terminate()
                try:
                    await asyncio.wait_for(self._process.wait(), timeout=5)
                except asyncio.TimeoutError:
                    self._process.kill()
                    await self._process.wait()
            except ProcessLookupError:
                pass
