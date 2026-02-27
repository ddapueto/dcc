"""Built-in workflow templates para DCC."""

BUILTIN_WORKFLOWS: list[dict] = [
    {
        "name": "Spec-Driven Development",
        "description": "Implementa una feature completa desde una especificacion detallada. Claude Code orquesta subtasks nativamente.",
        "category": "development",
        "icon": "FileCode",
        "prompt_template": (
            "Implement the following specification. Break it into subtasks as needed, "
            "write code, tests, and documentation.\n\n"
            "## Specification\n\n{{spec}}"
        ),
        "parameters": [
            {
                "key": "spec",
                "label": "Specification",
                "type": "textarea",
                "required": True,
            },
        ],
    },
    {
        "name": "TDD Flow",
        "description": "Desarrollo guiado por tests: primero escribe tests, luego implementa hasta que pasen.",
        "category": "testing",
        "icon": "TestTube",
        "prompt_template": (
            "Use Test-Driven Development to implement the following feature.\n\n"
            "1. First write failing tests using {{test_framework}}\n"
            "2. Then implement the minimum code to make them pass\n"
            "3. Refactor if needed\n\n"
            "## Feature\n\n{{feature}}"
        ),
        "parameters": [
            {
                "key": "feature",
                "label": "Feature description",
                "type": "textarea",
                "required": True,
            },
            {
                "key": "test_framework",
                "label": "Test framework",
                "type": "text",
                "required": False,
                "default": "pytest",
            },
        ],
    },
    {
        "name": "Issue to PR",
        "description": "Toma un issue de GitHub y genera una implementacion completa con PR.",
        "category": "development",
        "icon": "GitPullRequest",
        "prompt_template": (
            "Implement GitHub Issue #{{issue_number}}: {{issue_title}}\n\n"
            "## Issue Description\n\n{{issue_body}}\n\n"
            "## Instructions\n\n"
            "1. Analyze the issue requirements\n"
            "2. Implement the solution\n"
            "3. Write tests\n"
            "4. Create a commit with a descriptive message"
        ),
        "parameters": [
            {
                "key": "issue_number",
                "label": "Issue number",
                "type": "number",
                "required": True,
            },
            {
                "key": "issue_title",
                "label": "Issue title",
                "type": "text",
                "required": True,
            },
            {
                "key": "issue_body",
                "label": "Issue body",
                "type": "textarea",
                "required": True,
            },
        ],
    },
    {
        "name": "Security Audit",
        "description": "Analiza el codebase buscando vulnerabilidades de seguridad (OWASP Top 10, secrets, deps).",
        "category": "review",
        "icon": "Shield",
        "prompt_template": (
            "Perform a security audit of this codebase. Check for:\n\n"
            "- OWASP Top 10 vulnerabilities\n"
            "- Hardcoded secrets or credentials\n"
            "- Dependency vulnerabilities\n"
            "- Input validation issues\n"
            "- Authentication/authorization flaws\n\n"
            "{{focus_areas}}"
        ),
        "parameters": [
            {
                "key": "focus_areas",
                "label": "Focus areas (optional)",
                "type": "textarea",
                "required": False,
                "default": "",
            },
        ],
    },
    {
        "name": "Code Review",
        "description": "Revisa codigo buscando bugs, mejoras de performance, y adherencia a convenciones.",
        "category": "review",
        "icon": "Eye",
        "prompt_template": (
            "Review the code in this project. Focus on:\n\n"
            "- Potential bugs and edge cases\n"
            "- Performance improvements\n"
            "- Code style and conventions\n"
            "- Error handling\n\n"
            "Scope: {{review_scope}}"
        ),
        "parameters": [
            {
                "key": "review_scope",
                "label": "Review scope (e.g. 'src/auth/')",
                "type": "text",
                "required": False,
                "default": "entire project",
            },
        ],
    },
    {
        "name": "Refactor Module",
        "description": "Refactoriza un modulo con objetivos claros, manteniendo tests verdes.",
        "category": "development",
        "icon": "RefreshCw",
        "prompt_template": (
            "Refactor the module at {{target_path}}.\n\n"
            "## Goals\n\n{{refactor_goals}}\n\n"
            "## Constraints\n\n"
            "- Keep all existing tests passing\n"
            "- Maintain backward compatibility of public APIs\n"
            "- Add tests for any new functionality"
        ),
        "parameters": [
            {
                "key": "target_path",
                "label": "Target path",
                "type": "text",
                "required": True,
            },
            {
                "key": "refactor_goals",
                "label": "Refactoring goals",
                "type": "textarea",
                "required": True,
            },
        ],
    },
]
