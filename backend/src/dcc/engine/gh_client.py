"""GitHub API client via `gh` CLI subprocess."""

import asyncio
import json
import logging

logger = logging.getLogger(__name__)

GH_TIMEOUT_S = 15


class GhError(Exception):
    """Error from gh CLI."""

    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


async def gh_api(
    path: str, method: str = "GET", body: dict | None = None
) -> dict | list:
    """Execute GitHub API call via `gh api` subprocess.

    Uses asyncio.create_subprocess_exec (same pattern as CliRunner).
    Timeout: 15s.
    """
    cmd = ["gh", "api", path, "--method", method]

    if body is not None:
        cmd.extend(["--input", "-"])

    logger.debug("gh api: %s %s", method, path)

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE if body else None,
        )

        stdin_data = json.dumps(body).encode() if body else None

        stdout, stderr = await asyncio.wait_for(
            proc.communicate(input=stdin_data),
            timeout=GH_TIMEOUT_S,
        )

        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip()
            raise GhError(f"gh api error: {err_msg}", exit_code=proc.returncode or 1)

        output = stdout.decode("utf-8", errors="replace").strip()
        if not output:
            return {}

        return json.loads(output)

    except asyncio.TimeoutError as e:
        raise GhError(f"gh api timeout after {GH_TIMEOUT_S}s: {method} {path}") from e
    except json.JSONDecodeError as e:
        raise GhError(f"gh api returned invalid JSON: {e}") from e
