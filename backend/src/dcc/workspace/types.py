from pydantic import BaseModel


class AgentInfo(BaseModel):
    name: str
    filename: str
    description: str = ""
    model: str | None = None
    # YAML frontmatter fields
    tools: list[str] = []
    disallowed_tools: list[str] = []
    permission_mode: str | None = None
    max_turns: int | None = None
    skills: list[str] = []
    memory: str | None = None
    background: bool = False
    isolation: str | None = None
    system_prompt: str = ""


class SkillInfo(BaseModel):
    name: str
    filename: str
    description: str = ""


class WorkspaceDetail(BaseModel):
    id: str
    tenant_id: str
    tenant_name: str
    name: str
    path: str
    has_claude_md: bool
    repo_owner: str | None = None
    repo_name: str | None = None
    agents: list[AgentInfo]
    skills: list[SkillInfo]


class McpServerInfo(BaseModel):
    name: str
    command: str
    args: list[str] = []
    source: str  # "workspace" | "global"
