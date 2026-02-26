"""Sugiere agentes para steps de pipeline basándose en keywords."""

AGENT_ROUTING: dict[str, str] = {
    "implement": "backend-dev",
    "code": "backend-dev",
    "build": "backend-dev",
    "feature": "backend-dev",
    "test": "qa-engineer",
    "tests": "qa-engineer",
    "testing": "qa-engineer",
    "review": "code-reviewer",
    "refactor": "code-reviewer",
    "docs": "doc-expert",
    "document": "doc-expert",
    "readme": "doc-expert",
    "security": "compliance-officer",
    "auth": "compliance-officer",
    "architecture": "dev-architect",
    "design": "dev-architect",
    "database": "data-architect",
    "schema": "data-architect",
    "migration": "data-architect",
    "deploy": "devops",
    "ci": "devops",
    "docker": "devops",
    "ml": "ai-developer",
    "model": "ai-developer",
    "performance": "performance-analyst",
    "optimize": "performance-analyst",
}


def suggest_agent(step_name: str, step_description: str | None = None) -> str | None:
    """Sugiere un agente basándose en keywords del nombre o descripción del step."""
    text = step_name.lower()
    if step_description:
        text += " " + step_description.lower()

    for keyword, agent in AGENT_ROUTING.items():
        if keyword in text:
            return agent
    return None


def get_available_agents() -> list[dict[str, str]]:
    """Retorna lista de agentes con sus keywords."""
    agents: dict[str, list[str]] = {}
    for keyword, agent in AGENT_ROUTING.items():
        agents.setdefault(agent, []).append(keyword)
    return [{"name": name, "keywords": kws} for name, kws in agents.items()]
