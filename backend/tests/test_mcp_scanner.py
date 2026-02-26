"""Tests for MCP server scanner."""

import json

import pytest

from dcc.workspace.scanner import get_mcp_servers, read_mcp_json


@pytest.fixture
def workspace(tmp_path):
    return tmp_path


def test_read_mcp_json_valid(workspace):
    mcp_data = {
        "mcpServers": {
            "github": {"command": "gh", "args": ["mcp"]},
        }
    }
    (workspace / ".mcp.json").write_text(json.dumps(mcp_data))
    result = read_mcp_json(str(workspace))
    assert result is not None
    assert "github" in result["mcpServers"]


def test_read_mcp_json_not_found(workspace):
    result = read_mcp_json(str(workspace))
    assert result is None


def test_read_mcp_json_invalid(workspace):
    (workspace / ".mcp.json").write_text("not valid json {{{")
    result = read_mcp_json(str(workspace))
    assert result is None


def test_get_mcp_servers_workspace_only(workspace):
    mcp_data = {
        "mcpServers": {
            "github": {"command": "gh", "args": ["mcp"]},
            "devin": {"command": "npx", "args": ["devin-mcp"]},
        }
    }
    (workspace / ".mcp.json").write_text(json.dumps(mcp_data))

    servers = get_mcp_servers(str(workspace))
    assert len(servers) == 2
    assert servers[0]["name"] == "github"
    assert servers[0]["command"] == "gh"
    assert servers[0]["args"] == ["mcp"]
    assert servers[0]["source"] == "workspace"


def test_get_mcp_servers_merged(workspace, tmp_path):
    # Workspace .mcp.json
    (workspace / ".mcp.json").write_text(
        json.dumps({"mcpServers": {"github": {"command": "gh", "args": ["mcp"]}}})
    )

    # Global settings.local.json
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "settings.local.json").write_text(
        json.dumps({
            "mcpServers": {
                "github": {"command": "gh-global", "args": []},  # dupe — workspace wins
                "slack": {"command": "slack-mcp", "args": ["--token", "xyz"]},
            }
        })
    )

    servers = get_mcp_servers(str(workspace), str(config_dir))
    assert len(servers) == 2
    names = [s["name"] for s in servers]
    assert "github" in names
    assert "slack" in names
    # github should be workspace version
    gh = next(s for s in servers if s["name"] == "github")
    assert gh["command"] == "gh"
    assert gh["source"] == "workspace"
    sl = next(s for s in servers if s["name"] == "slack")
    assert sl["source"] == "global"


def test_get_mcp_servers_empty(workspace):
    servers = get_mcp_servers(str(workspace))
    assert servers == []
