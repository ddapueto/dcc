"""Tests for plan builder: prompt construction and output parsing."""

import json

from dcc.engine.plan_builder import (
    build_planner_prompt_from_issues,
    build_planner_prompt_from_spec,
    enrich_steps_with_routing,
    parse_planner_output,
    resolve_prompt_template,
)


def test_parse_planner_output_json():
    """Parsea JSON directo."""
    raw = json.dumps([{"name": "Step 1"}, {"name": "Step 2"}])
    result = parse_planner_output(raw)
    assert len(result) == 2
    assert result[0]["name"] == "Step 1"


def test_parse_planner_output_with_fences():
    """Parsea JSON dentro de markdown fences."""
    raw = """Here is the plan:
```json
[{"name": "Build API"}, {"name": "Write tests"}]
```
Done!"""
    result = parse_planner_output(raw)
    assert len(result) == 2
    assert result[1]["name"] == "Write tests"


def test_parse_planner_output_fallback_bracket():
    """Fallback: busca primer [ ... último ]."""
    raw = "The steps are: [{\"name\": \"Deploy\"}] and that's it."
    result = parse_planner_output(raw)
    assert len(result) == 1
    assert result[0]["name"] == "Deploy"


def test_parse_planner_output_invalid():
    """Retorna lista vacía si no puede parsear."""
    result = parse_planner_output("This is not JSON at all")
    assert result == []


def test_enrich_steps_with_routing():
    steps = [
        {"name": "Implement auth", "agent": None},
        {"name": "Write tests", "agent": "custom-agent"},
        {"name": "Deploy service"},
    ]
    enriched = enrich_steps_with_routing(steps)
    # Primer step debería tener agente sugerido
    assert enriched[0]["agent"] is not None
    # Segundo step mantiene su agente custom
    assert enriched[1]["agent"] == "custom-agent"
    # Tercer step debería tener devops
    assert enriched[2]["agent"] == "devops"


def test_resolve_prompt_template():
    template = "Fix the issue: {{spec}}. Previous output: {{prev_output}}"
    context = {"spec": "Add login page", "prev_output": "Schema created"}
    result = resolve_prompt_template(template, context)
    assert result == "Fix the issue: Add login page. Previous output: Schema created"


def test_build_planner_prompt_from_spec():
    prompt = build_planner_prompt_from_spec("Build a REST API", ["backend-dev", "qa-engineer"])
    assert "Build a REST API" in prompt
    assert "backend-dev" in prompt
    assert "JSON array" in prompt


def test_build_planner_prompt_from_issues():
    issues = [
        {"number": 1, "title": "Fix login", "body": "Login is broken"},
        {"number": 2, "title": "Add tests", "body": None},
    ]
    prompt = build_planner_prompt_from_issues(issues, ["backend-dev"])
    assert "#1" in prompt
    assert "Fix login" in prompt
    assert "No description" in prompt  # body=None fallback
