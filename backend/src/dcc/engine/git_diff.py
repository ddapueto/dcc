"""Git diff utilities for capturing changes before/after CLI runs."""

import asyncio
import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

MAX_DIFF_SIZE = 50_000  # 50KB max diff content


@dataclass
class DiffCapture:
    diff_stat: str | None = None
    diff_content: str | None = None
    files_changed: int = 0
    insertions: int = 0
    deletions: int = 0


async def _run_git(workspace_path: str, *args: str) -> str | None:
    """Run a git command and return stdout, or None on error."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workspace_path,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
        if proc.returncode != 0:
            return None
        return stdout.decode("utf-8", errors="replace").strip()
    except (asyncio.TimeoutError, FileNotFoundError, OSError):
        return None


async def capture_head_ref(workspace_path: str) -> str | None:
    """Get current HEAD commit hash."""
    return await _run_git(workspace_path, "rev-parse", "HEAD")


async def compute_session_diff(
    workspace_path: str, head_before: str | None
) -> DiffCapture:
    """Compute diff after CLI run.

    If head_before is available, shows committed changes (log + diff).
    Also captures any uncommitted changes (working tree diff).
    """
    capture = DiffCapture()

    parts: list[str] = []

    # Committed changes since head_before
    if head_before:
        head_after = await _run_git(workspace_path, "rev-parse", "HEAD")
        if head_after and head_after != head_before:
            # Log of commits
            log = await _run_git(
                workspace_path, "log", "--oneline", f"{head_before}..{head_after}"
            )
            if log:
                parts.append(f"# Commits\n{log}\n")

            # Diff stat
            stat = await _run_git(
                workspace_path, "diff", "--stat", f"{head_before}..{head_after}"
            )
            if stat:
                capture.diff_stat = stat
                fc, ins, dels = parse_diff_stat(stat)
                capture.files_changed = fc
                capture.insertions = ins
                capture.deletions = dels

            # Diff content
            diff = await _run_git(
                workspace_path, "diff", f"{head_before}..{head_after}"
            )
            if diff:
                parts.append(diff)

    # Uncommitted changes (working tree)
    wt_stat = await _run_git(workspace_path, "diff", "--stat")
    if wt_stat:
        if not capture.diff_stat:
            capture.diff_stat = wt_stat
            fc, ins, dels = parse_diff_stat(wt_stat)
            capture.files_changed = fc
            capture.insertions = ins
            capture.deletions = dels

        wt_diff = await _run_git(workspace_path, "diff")
        if wt_diff:
            parts.append(f"\n# Uncommitted changes\n{wt_diff}")

    if parts:
        full = "\n".join(parts)
        # Truncate if too large
        capture.diff_content = full[:MAX_DIFF_SIZE]

    return capture


def parse_diff_stat(stat_output: str) -> tuple[int, int, int]:
    """Parse git diff --stat summary line.

    Example: '3 files changed, 42 insertions(+), 5 deletions(-)'
    Returns (files_changed, insertions, deletions).
    """
    # The summary line is typically the last line
    last_line = stat_output.strip().splitlines()[-1] if stat_output.strip() else ""

    files = 0
    ins = 0
    dels = 0

    m = re.search(r"(\d+)\s+files?\s+changed", last_line)
    if m:
        files = int(m.group(1))

    m = re.search(r"(\d+)\s+insertions?\(\+\)", last_line)
    if m:
        ins = int(m.group(1))

    m = re.search(r"(\d+)\s+deletions?\(-\)", last_line)
    if m:
        dels = int(m.group(1))

    return files, ins, dels
