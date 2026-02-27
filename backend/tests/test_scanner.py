import os
import tempfile

from dcc.workspace.scanner import scan_agents, scan_skills, has_claude_md, scan_workspace


def _make_workspace(tmp_dir: str, agents: dict[str, str] = {}, commands: dict[str, str] = {}, create_claude_md: bool = False):
    """Create a mock workspace with .claude/ structure."""
    claude_dir = os.path.join(tmp_dir, ".claude")
    os.makedirs(os.path.join(claude_dir, "agents"), exist_ok=True)
    os.makedirs(os.path.join(claude_dir, "commands"), exist_ok=True)

    for name, content in agents.items():
        with open(os.path.join(claude_dir, "agents", name), "w") as f:
            f.write(content)

    for name, content in commands.items():
        # Handle subdirectory commands like "subdir/skill.md"
        path = os.path.join(claude_dir, "commands", name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

    if create_claude_md:
        with open(os.path.join(tmp_dir, "CLAUDE.md"), "w") as f:
            f.write("# Project Instructions\n")


def test_scan_agents_empty():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp)
        agents = scan_agents(tmp)
        assert agents == []


def test_scan_agents_basic():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, agents={
            "code-reviewer.md": "# Code Reviewer\nReviews code for quality and correctness.\nmodel: sonnet",
            "doc-expert.md": "Generates documentation for the project.",
        })
        agents = scan_agents(tmp)
        assert len(agents) == 2

        reviewer = next(a for a in agents if a.name == "code-reviewer")
        assert reviewer.description == "Reviews code for quality and correctness."
        assert reviewer.model == "sonnet"

        doc = next(a for a in agents if a.name == "doc-expert")
        assert doc.description == "Generates documentation for the project."
        assert doc.model is None


def test_scan_skills_basic():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, commands={
            "commit.md": "Creates a well-formatted git commit.",
            "test.md": "# Test\nRuns the project test suite.",
        })
        skills = scan_skills(tmp)
        assert len(skills) == 2

        commit = next(s for s in skills if s.name == "commit")
        assert commit.description == "Creates a well-formatted git commit."


def test_scan_skills_subdirectory():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, commands={
            "deploy/production.md": "Deploys to production environment.",
        })
        skills = scan_skills(tmp)
        assert len(skills) == 1
        assert skills[0].name == "deploy/production"


def test_has_claude_md():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, create_claude_md=False)
        assert has_claude_md(tmp) is False

        _make_workspace(tmp, create_claude_md=True)
        assert has_claude_md(tmp) is True


def test_scan_workspace_full():
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(
            tmp,
            agents={"agent-a.md": "Agent A description."},
            commands={"skill-1.md": "Skill 1 description."},
            create_claude_md=True,
        )
        agents, skills, has_md, owner, repo = scan_workspace(tmp)
        assert len(agents) == 1
        assert len(skills) == 1
        assert has_md is True
        assert owner is None  # tmp dir has no .git
        assert repo is None


def test_scan_nonexistent_dir():
    agents = scan_agents("/nonexistent/path")
    skills = scan_skills("/nonexistent/path")
    assert agents == []
    assert skills == []


def test_scan_agents_yaml_frontmatter():
    """Agent with YAML frontmatter should extract all fields."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, agents={
            "explorer.md": """---
description: Explores codebases efficiently
model: haiku
allowed_tools: Read, Glob, Grep
disallowed_tools: Write, Edit
max_turns: 10
permission_mode: bypassPermissions
isolation: worktree
---
You are an exploration agent that searches code.""",
        })
        agents = scan_agents(tmp)
        assert len(agents) == 1

        agent = agents[0]
        assert agent.name == "explorer"
        assert agent.description == "Explores codebases efficiently"
        assert agent.model == "haiku"
        assert agent.tools == ["Read", "Glob", "Grep"]
        assert agent.disallowed_tools == ["Write", "Edit"]
        assert agent.max_turns == 10
        assert agent.permission_mode == "bypassPermissions"
        assert agent.isolation == "worktree"
        assert "exploration agent" in agent.system_prompt


def test_scan_agents_yaml_list_tools():
    """Tools as YAML list should work too."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, agents={
            "builder.md": """---
model: sonnet
allowed_tools:
  - Read
  - Write
  - Bash
skills:
  - commit
  - test
---
Builder agent body.""",
        })
        agents = scan_agents(tmp)
        agent = agents[0]
        assert agent.tools == ["Read", "Write", "Bash"]
        assert agent.skills == ["commit", "test"]
        assert agent.model == "sonnet"


def test_scan_agents_no_frontmatter_fallback():
    """Agent without frontmatter should use regex fallback."""
    with tempfile.TemporaryDirectory() as tmp:
        _make_workspace(tmp, agents={
            "simple.md": "This is a simple agent.\nmodel: opus",
        })
        agents = scan_agents(tmp)
        assert len(agents) == 1
        assert agents[0].description == "This is a simple agent."
        assert agents[0].model == "opus"
        assert agents[0].tools == []


def test_ensure_list():
    from dcc.workspace.scanner import _ensure_list

    assert _ensure_list(None) == []
    assert _ensure_list("Read, Glob, Grep") == ["Read", "Glob", "Grep"]
    assert _ensure_list(["Read", "Glob"]) == ["Read", "Glob"]
    assert _ensure_list("") == []
    assert _ensure_list([]) == []
