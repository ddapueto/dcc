"""Tests for workflow templates structure."""

import pytest

from dcc.engine.workflow_templates import BUILTIN_WORKFLOWS


def test_all_templates_have_required_fields():
    required = {"name", "description", "category", "icon", "prompt_template", "parameters"}
    for tmpl in BUILTIN_WORKFLOWS:
        missing = required - set(tmpl.keys())
        assert not missing, f"Template '{tmpl.get('name')}' missing: {missing}"


def test_all_parameters_have_required_fields():
    param_required = {"key", "label", "type", "required"}
    for tmpl in BUILTIN_WORKFLOWS:
        for param in tmpl["parameters"]:
            missing = param_required - set(param.keys())
            assert not missing, (
                f"Param '{param.get('key')}' in '{tmpl['name']}' missing: {missing}"
            )
            assert param["type"] in ("text", "textarea", "number", "select")


def test_templates_have_valid_categories():
    valid_categories = {"development", "testing", "review", "devops", "custom"}
    for tmpl in BUILTIN_WORKFLOWS:
        assert tmpl["category"] in valid_categories, (
            f"Template '{tmpl['name']}' has invalid category: {tmpl['category']}"
        )


def test_template_count():
    assert len(BUILTIN_WORKFLOWS) == 6
