"""Tests for git repo detection from .git/config."""

import os

import pytest

from dcc.workspace.scanner import detect_git_repo


@pytest.fixture
def workspace(tmp_path):
    """Create a workspace dir with .git/config."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


def _write_git_config(workspace, url: str):
    config = workspace / ".git" / "config"
    config.write_text(
        f'[remote "origin"]\n\turl = {url}\n\tfetch = +refs/heads/*:refs/remotes/origin/*\n'
    )


def test_ssh_url(workspace):
    _write_git_config(workspace, "git@github.com:ddapueto/dcc.git")
    owner, repo = detect_git_repo(str(workspace))
    assert owner == "ddapueto"
    assert repo == "dcc"


def test_https_url(workspace):
    _write_git_config(workspace, "https://github.com/Verifix-360/verifix-platform.git")
    owner, repo = detect_git_repo(str(workspace))
    assert owner == "Verifix-360"
    assert repo == "verifix-platform"


def test_https_url_no_git_suffix(workspace):
    _write_git_config(workspace, "https://github.com/ddapueto/dcc")
    owner, repo = detect_git_repo(str(workspace))
    assert owner == "ddapueto"
    assert repo == "dcc"


def test_no_git_dir(tmp_path):
    owner, repo = detect_git_repo(str(tmp_path))
    assert owner is None
    assert repo is None


def test_no_remote(workspace):
    config = workspace / ".git" / "config"
    config.write_text("[core]\n\trepositoryformatversion = 0\n")
    owner, repo = detect_git_repo(str(workspace))
    assert owner is None
    assert repo is None


def test_non_github_remote(workspace):
    _write_git_config(workspace, "git@gitlab.com:user/project.git")
    owner, repo = detect_git_repo(str(workspace))
    assert owner is None
    assert repo is None
