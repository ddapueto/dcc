"""Tests for git diff parsing utilities."""

import pytest

from dcc.engine.git_diff import capture_head_ref, parse_diff_stat


def test_parse_diff_stat_basic():
    stat = " foo.py | 10 ++++----\n bar.py | 5 +++++\n 3 files changed, 42 insertions(+), 5 deletions(-)"
    files, ins, dels = parse_diff_stat(stat)
    assert files == 3
    assert ins == 42
    assert dels == 5


def test_parse_diff_stat_no_deletions():
    stat = " 1 file changed, 10 insertions(+)"
    files, ins, dels = parse_diff_stat(stat)
    assert files == 1
    assert ins == 10
    assert dels == 0


def test_parse_diff_stat_no_insertions():
    stat = " 2 files changed, 3 deletions(-)"
    files, ins, dels = parse_diff_stat(stat)
    assert files == 2
    assert ins == 0
    assert dels == 3


def test_parse_diff_stat_empty():
    files, ins, dels = parse_diff_stat("")
    assert files == 0
    assert ins == 0
    assert dels == 0


@pytest.mark.asyncio
async def test_capture_head_ref_not_git_repo(tmp_path):
    result = await capture_head_ref(str(tmp_path))
    assert result is None
