from pydantic import BaseModel


class AgentInfo(BaseModel):
    name: str
    filename: str
    description: str = ""
    model: str | None = None


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
    agents: list[AgentInfo]
    skills: list[SkillInfo]
