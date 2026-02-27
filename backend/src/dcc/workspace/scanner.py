import re
from pathlib import Path

import yaml

from dcc.workspace.types import AgentInfo, SkillInfo


def _ensure_list(val: str | list | None) -> list[str]:
    """Convert a comma-separated string or list to list[str]."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(v).strip() for v in val if v]
    if isinstance(val, str):
        return [s.strip() for s in val.split(",") if s.strip()]
    return []


def _parse_agent_frontmatter(content: str) -> tuple[dict, str]:
    """Parse YAML frontmatter from agent .md file.

    Returns (frontmatter_dict, body_after_frontmatter).
    If no frontmatter, returns ({}, full_content).
    """
    if not content.startswith("---"):
        return {}, content

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content

    yaml_text = parts[1]
    body = parts[2].strip()

    try:
        data = yaml.safe_load(yaml_text)
        if not isinstance(data, dict):
            return {}, content
        return data, body
    except yaml.YAMLError:
        return {}, content


def scan_agents(workspace_path: str) -> list[AgentInfo]:
    """Scan .claude/agents/*.md for agent definitions."""
    agents_dir = Path(workspace_path) / ".claude" / "agents"
    if not agents_dir.is_dir():
        return []

    agents = []
    for md_file in sorted(agents_dir.glob("*.md")):
        name = md_file.stem
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm, body = _parse_agent_frontmatter(content)

        if fm:
            # YAML frontmatter found — extract all fields
            description = fm.get("description", "") or _extract_first_line(body)
            model = fm.get("model") or _extract_model(body)
            if model:
                model = str(model).lower()

            agents.append(AgentInfo(
                name=name,
                filename=md_file.name,
                description=str(description)[:200] if description else "",
                model=model,
                tools=_ensure_list(fm.get("allowed_tools") or fm.get("tools")),
                disallowed_tools=_ensure_list(fm.get("disallowed_tools")),
                permission_mode=fm.get("permission_mode"),
                max_turns=fm.get("max_turns"),
                skills=_ensure_list(fm.get("skills")),
                memory=fm.get("memory"),
                background=bool(fm.get("background", False)),
                isolation=fm.get("isolation"),
                system_prompt=body[:5000] if body else "",
            ))
        else:
            # Fallback: regex-based extraction
            description = _extract_first_line(content)
            model = _extract_model(content)
            agents.append(
                AgentInfo(
                    name=name,
                    filename=md_file.name,
                    description=description,
                    model=model,
                    system_prompt=content[:5000],
                )
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


def detect_git_repo(workspace_path: str) -> tuple[str | None, str | None]:
    """Detect GitHub owner/repo from .git/config remote origin URL.

    Supports: git@github.com:owner/repo.git, https://github.com/owner/repo[.git]
    Returns (owner, repo_name) or (None, None).
    """
    git_config = Path(workspace_path) / ".git" / "config"
    if not git_config.is_file():
        return None, None

    try:
        content = git_config.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None

    # Look for remote "origin" url
    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("url ="):
            continue
        url = line.split("=", 1)[1].strip()

        # SSH: git@github.com:owner/repo.git
        ssh_match = re.match(r"git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$", url)
        if ssh_match:
            return ssh_match.group(1), ssh_match.group(2)

        # HTTPS: https://github.com/owner/repo[.git]
        https_match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?$", url)
        if https_match:
            return https_match.group(1), https_match.group(2)

    return None, None


def read_mcp_json(workspace_path: str) -> dict | None:
    """Read and parse .mcp.json from workspace root."""
    import json

    path = Path(workspace_path) / ".mcp.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return None


def get_mcp_servers(workspace_path: str, config_dir: str | None = None) -> list[dict]:
    """Get combined MCP servers from .mcp.json + config_dir settings.local.json.

    Returns list of { name, command, args, env, source }.
    """
    import json

    servers: list[dict] = []

    # Workspace-level .mcp.json
    mcp_data = read_mcp_json(workspace_path)
    if mcp_data and isinstance(mcp_data.get("mcpServers"), dict):
        for name, cfg in mcp_data["mcpServers"].items():
            servers.append({
                "name": name,
                "command": cfg.get("command", ""),
                "args": cfg.get("args", []),
                "source": "workspace",
            })

    # Global settings.local.json from config_dir
    if config_dir:
        settings_path = Path(config_dir) / "settings.local.json"
        if settings_path.is_file():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8", errors="replace"))
                if isinstance(data.get("mcpServers"), dict):
                    for name, cfg in data["mcpServers"].items():
                        # Avoid duplicates — workspace overrides global
                        if not any(s["name"] == name for s in servers):
                            servers.append({
                                "name": name,
                                "command": cfg.get("command", ""),
                                "args": cfg.get("args", []),
                                "source": "global",
                            })
            except (json.JSONDecodeError, OSError):
                pass

    return servers


def scan_workspace(
    workspace_path: str,
) -> tuple[list[AgentInfo], list[SkillInfo], bool, str | None, str | None]:
    """Full scan of a workspace. Returns (agents, skills, has_claude_md, repo_owner, repo_name)."""
    owner, repo = detect_git_repo(workspace_path)
    return (
        scan_agents(workspace_path),
        scan_skills(workspace_path),
        has_claude_md(workspace_path),
        owner,
        repo,
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
