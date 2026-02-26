"""Tests for agent routing logic."""

from dcc.engine.agent_router import get_available_agents, suggest_agent


def test_suggest_agent_implement():
    assert suggest_agent("Implement feature X") == "backend-dev"


def test_suggest_agent_test():
    assert suggest_agent("Write tests for module") == "qa-engineer"


def test_suggest_agent_no_match():
    assert suggest_agent("Do something random") is None


def test_suggest_agent_description_fallback():
    """Si el nombre no matchea, busca en la descripción."""
    result = suggest_agent("Step 1", step_description="Deploy the service to production")
    assert result == "devops"


def test_get_available_agents():
    agents = get_available_agents()
    assert len(agents) > 0
    names = [a["name"] for a in agents]
    assert "backend-dev" in names
    assert "qa-engineer" in names
    for agent in agents:
        assert "name" in agent
        assert "keywords" in agent
        assert len(agent["keywords"]) > 0
