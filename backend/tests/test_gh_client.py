"""Tests for gh CLI client (mocked subprocess)."""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dcc.engine.gh_client import GhError, gh_api


def _make_process(stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0):
    """Create a mock asyncio.subprocess.Process."""
    proc = MagicMock()
    proc.returncode = returncode
    proc.communicate = AsyncMock(return_value=(stdout, stderr))
    return proc


@pytest.mark.asyncio
async def test_gh_api_success():
    data = [{"number": 1, "title": "Issue 1"}]
    proc = _make_process(stdout=json.dumps(data).encode())

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc):
        result = await gh_api("/repos/owner/repo/issues")

    assert isinstance(result, list)
    assert result[0]["number"] == 1


@pytest.mark.asyncio
async def test_gh_api_error_exit():
    proc = _make_process(stderr=b"Not Found", returncode=1)

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(GhError, match="Not Found"):
            await gh_api("/repos/owner/repo/issues")


@pytest.mark.asyncio
async def test_gh_api_timeout():
    async def slow_communicate(input=None):
        await asyncio.sleep(100)
        return b"", b""

    proc = MagicMock()
    proc.communicate = slow_communicate

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc):
        with patch("dcc.engine.gh_client.GH_TIMEOUT_S", 0.01):
            with pytest.raises(GhError, match="timeout"):
                await gh_api("/repos/owner/repo/issues")


@pytest.mark.asyncio
async def test_gh_api_invalid_json():
    proc = _make_process(stdout=b"not json {{{")

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc):
        with pytest.raises(GhError, match="invalid JSON"):
            await gh_api("/repos/owner/repo/issues")


@pytest.mark.asyncio
async def test_gh_api_post_with_body():
    response = {"number": 42, "title": "New Issue"}
    proc = _make_process(stdout=json.dumps(response).encode())

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc) as mock_exec:
        result = await gh_api(
            "/repos/owner/repo/issues",
            method="POST",
            body={"title": "New Issue", "body": "Description"},
        )

    assert result["number"] == 42
    # Verify --input - was passed for stdin
    call_args = mock_exec.call_args
    assert "--input" in call_args[0]


@pytest.mark.asyncio
async def test_gh_api_empty_response():
    proc = _make_process(stdout=b"")

    with patch("dcc.engine.gh_client.asyncio.create_subprocess_exec", return_value=proc):
        result = await gh_api("/repos/owner/repo/milestones")

    assert result == {}
