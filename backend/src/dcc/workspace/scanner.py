import re
from pathlib import Path

from dcc.workspace.types import AgentInfo, SkillInfo


def scan_agents(workspace_path: str) -> list[AgentInfo]:
    """Scan .claude/agents/*.md for agent definitions."""
    agents_dir = Path(workspace_path) / ".claude" / "agents"
    if not agents_dir.is_dir():
        return []

    agents = []
    for md_file in sorted(agents_dir.glob("*.md")):
        name = md_file.stem
        content = md_file.read_text(encoding="utf-8", errors="replace")
        description = _extract_first_line(content)
        model = _extract_model(content)
        agents.append(
            AgentInfo(name=name, filename=md_file.name, description=description, model=model)
        )
    return agents


def scan_skills(workspace_path: str) -> list[SkillInfo]:
    """Scan .claude/commands/*.md for skill/command definitions."""
    commands_dir = Path(workspace_path) / ".claude" / "commands"
    if not commands_dir.is_dir():
        return []

    skills = []
    for md_file in sorted(commands_dir.glob("*.md")):
        name = md_file.stem
        content = md_file.read_text(encoding="utf-8", errors="replace")
        description = _extract_first_line(content)
        skills.append(SkillInfo(name=name, filename=md_file.name, description=description))

    # Also scan subdirectories (e.g., .claude/commands/subdir/*.md)
    for subdir in sorted(commands_dir.iterdir()):
        if subdir.is_dir():
            for md_file in sorted(subdir.glob("*.md")):
                name = f"{subdir.name}/{md_file.stem}"
                content = md_file.read_text(encoding="utf-8", errors="replace")
                description = _extract_first_line(content)
                skills.append(
                    SkillInfo(name=name, filename=f"{subdir.name}/{md_file.name}", description=description)
                )

    return skills


def has_claude_md(workspace_path: str) -> bool:
    """Check if CLAUDE.md exists in workspace root."""
    return (Path(workspace_path) / "CLAUDE.md").is_file()


def scan_workspace(workspace_path: str) -> tuple[list[AgentInfo], list[SkillInfo], bool]:
    """Full scan of a workspace. Returns (agents, skills, has_claude_md)."""
    return (
        scan_agents(workspace_path),
        scan_skills(workspace_path),
        has_claude_md(workspace_path),
    )


def _extract_first_line(content: str) -> str:
    """Extract first non-empty, non-heading line as description."""
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        # Skip markdown headings and frontmatter
        if line.startswith("#") or line.startswith("---"):
            continue
        # Remove markdown bold/italic
        line = re.sub(r"[*_]{1,2}(.+?)[*_]{1,2}", r"\1", line)
        return line[:200]
    return ""


def _extract_model(content: str) -> str | None:
    """Try to extract model hint from agent file (e.g., 'model: opus')."""
    match = re.search(r"model:\s*(opus|sonnet|haiku)", content, re.IGNORECASE)
    return match.group(1).lower() if match else None


# --- Config readers ---


def read_claude_md(workspace_path: str) -> str | None:
    """Read CLAUDE.md from workspace root. Returns None if not found."""
    path = Path(workspace_path) / "CLAUDE.md"
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8", errors="replace")


def read_rules(workspace_path: str) -> list[dict]:
    """Read all .claude/rules/*.md files. Returns list of {name, filename, content}."""
    rules_dir = Path(workspace_path) / ".claude" / "rules"
    if not rules_dir.is_dir():
        return []

    rules = []
    for md_file in sorted(rules_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        rules.append({
            "name": md_file.stem,
            "filename": md_file.name,
            "content": content,
        })
    return rules


def read_settings_json(workspace_path: str) -> dict | None:
    """Read and parse .claude/settings.json. Returns None if not found."""
    import json

    path = Path(workspace_path) / ".claude" / "settings.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except json.JSONDecodeError:
        return None
