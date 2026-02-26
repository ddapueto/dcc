"""Construye prompts de planificación y parsea outputs del planner."""

import json
import re

from dcc.engine.agent_router import suggest_agent


def build_planner_prompt_from_spec(spec: str, available_agents: list[str]) -> str:
    """Prompt para que Claude descomponga una spec en steps JSON."""
    agents_str = ", ".join(available_agents)
    return f"""You are a pipeline planner. Decompose the following specification into a sequence of steps.

Each step should be a JSON object with these fields:
- "name": short descriptive name for the step
- "description": what the step should accomplish
- "agent": one of [{agents_str}] or null if unsure
- "prompt_template": the prompt to send to the agent (can use {{{{spec}}}} for original spec, {{{{prev_output}}}} for previous step output)
- "depends_on": array of step indices (0-based) this step depends on, or empty array

Return ONLY a JSON array of steps. No explanation, no markdown fences.

Specification:
{spec}"""


def build_planner_prompt_from_issues(
    issues: list[dict], available_agents: list[str]
) -> str:
    """Prompt para planificar desde issues de un milestone."""
    agents_str = ", ".join(available_agents)
    issues_text = "\n".join(
        f"- Issue #{i.get('number', '?')}: {i.get('title', 'untitled')}\n"
        f"  {(i.get('body') or 'No description')[:500]}"
        for i in issues
    )
    return f"""You are a pipeline planner. Create a pipeline plan from these GitHub issues.

Each step should be a JSON object with these fields:
- "name": short descriptive name for the step
- "description": what the step should accomplish
- "agent": one of [{agents_str}] or null if unsure
- "prompt_template": the prompt to send to the agent (can use {{{{issue_body}}}} for issue content, {{{{prev_output}}}} for previous step output)
- "depends_on": array of step indices (0-based) this step depends on, or empty array

Return ONLY a JSON array of steps. No explanation, no markdown fences.

Issues:
{issues_text}"""


def parse_planner_output(raw_output: str) -> list[dict]:
    """Extrae JSON array del output del planner. Maneja fences y fallbacks."""
    text = raw_output.strip()

    # Intento 1: parsear directo como JSON
    try:
        result = json.loads(text)
        if isinstance(result, list):
            return result
    except json.JSONDecodeError:
        pass

    # Intento 2: extraer de markdown fences ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
    if fence_match:
        try:
            result = json.loads(fence_match.group(1).strip())
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    # Intento 3: buscar primer [ ... último ]
    bracket_start = text.find("[")
    bracket_end = text.rfind("]")
    if bracket_start != -1 and bracket_end > bracket_start:
        try:
            result = json.loads(text[bracket_start : bracket_end + 1])
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass

    return []


def enrich_steps_with_routing(steps: list[dict]) -> list[dict]:
    """Aplica agent_router.suggest_agent a steps sin agente asignado."""
    for step in steps:
        if not step.get("agent"):
            suggested = suggest_agent(
                step.get("name", ""), step.get("description")
            )
            if suggested:
                step["agent"] = suggested
    return steps


def resolve_prompt_template(template: str, context: dict[str, str]) -> str:
    """Reemplaza placeholders {{key}} con valores del contexto."""
    result = template
    for key, value in context.items():
        result = result.replace("{{" + key + "}}", value)
    return result
