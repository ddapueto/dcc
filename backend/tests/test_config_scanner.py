"""Tests for config reader functions in scanner."""

import json
import os
import tempfile

from dcc.workspace.scanner import read_claude_md, read_rules, read_settings_json


def _make_workspace(tmp_dir, claude_md=None, rules=None, settings=None):
    """Create workspace with config files."""
    if claude_md is not None:
        with open(os.path.join(tmp_dir, "CLAUDE.md"), "w") as f:
            f.write(claude_md)

    if rules:
        rules_dir = os.path.join(tmp_dir, ".claude", "rules")
        os.makedirs(rules_dir, exist_ok=True)
        for name, content in rules.items():
            with open(os.path.join(rules_dir, name), "w") as f:
                f.write(content)

    if settings is not None:
        settings_dir = os.path.join(tmp_dir, ".claude")
        os.makedirs(settings_dir, exist_ok=True)
        with open(os.path.join(settings_dir, "settings.json"), "w") as f:
            json.dump(settings, f)


# --- read_claude_md ---


def test_read_claude_md_exists():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, claude_md="# My Project\nInstructions here.")
        result = read_claude_md(tmp)
        assert result is not None
        assert "# My Project" in result


def test_read_claude_md_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        result = read_claude_md(tmp)
        assert result is None


# --- read_rules ---


def test_read_rules_basic():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, rules={
            "performance.md": "# Performance\nUse caching always.",
            "security.md": "# Security\nNever expose secrets.",
        })
        rules = read_rules(tmp)
        assert len(rules) == 2
        # Sorted alphabetically
        assert rules[0]["name"] == "performance"
        assert rules[0]["filename"] == "performance.md"
        assert "caching" in rules[0]["content"]
        assert rules[1]["name"] == "security"


def test_read_rules_empty():
    with tempfile.TemporaryDirectory() as tmp:
        result = read_rules(tmp)
        assert result == []


def test_read_rules_no_dir():
    result = read_rules("/nonexistent/path")
    assert result == []


# --- read_settings_json ---


def test_read_settings_basic():
    with tempfile.TemporaryDirectory() as tmp:
        settings_data = {"model": "opus", "permissions": {"allow": ["Read"]}}
        _make_workspace(tmp, settings=settings_data)
        result = read_settings_json(tmp)
        assert result is not None
        assert result["model"] == "opus"
        assert "permissions" in result


def test_read_settings_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        result = read_settings_json(tmp)
        assert result is None


def test_read_settings_invalid_json():
    with tempfile.TemporaryDirectory() as tmp:
        settings_dir = os.path.join(tmp, ".claude")
        os.makedirs(settings_dir, exist_ok=True)
        with open(os.path.join(settings_dir, "settings.json"), "w") as f:
            f.write("not valid json {{{")
        result = read_settings_json(tmp)
        assert result is None
