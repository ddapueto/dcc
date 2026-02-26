from pathlib import Path

from dcc.db import repository
from dcc.workspace.scanner import detect_git_repo

HOME = Path.home()

# Known tenants
# projects/personal/* → claude-personal (~/.claude-personal)
# projects/eron/*     → claude-eron     (~/.claude-eron)
TENANTS = [
    {
        "id": "personal",
        "name": "Personal",
        "config_dir": str(HOME / ".claude-personal"),
        "claude_alias": "claude-personal",
    },
    {
        "id": "empresa",
        "name": "Empresa",
        "config_dir": str(HOME / ".claude-eron"),
        "claude_alias": "claude-eron",
    },
    {
        "id": "jarix",
        "name": "Jarix",
        "config_dir": str(HOME / ".claude-jarix"),
        "claude_alias": "claude-jarix",
    },
]

# Known workspaces
# personal = ~/projects/personal/*
# empresa  = ~/projects/eron/*
WORKSPACES = [
    # --- Personal (claude-personal) ---
    {
        "id": "verifix-platform",
        "tenant_id": "personal",
        "name": "Verifix Platform",
        "path": str(HOME / "projects" / "personal" / "verifix" / "verifix-platform"),
    },
    {
        "id": "auronai",
        "tenant_id": "personal",
        "name": "AuronAI",
        "path": str(HOME / "projects" / "personal" / "AuronAI"),
    },
    {
        "id": "auronai-trading",
        "tenant_id": "personal",
        "name": "AuronAI Trading",
        "path": str(HOME / "projects" / "personal" / "AuronAI-Trading"),
    },
    {
        "id": "cinco-de-oro",
        "tenant_id": "personal",
        "name": "Cinco de Oro",
        "path": str(HOME / "projects" / "personal" / "cinco-de-oro"),
    },
    {
        "id": "banco",
        "tenant_id": "personal",
        "name": "Banco",
        "path": str(HOME / "projects" / "personal" / "banco"),
    },
    {
        "id": "dcc",
        "tenant_id": "personal",
        "name": "DCC",
        "path": str(HOME / "projects" / "personal" / "dcc"),
    },
    {
        "id": "transcripcion",
        "tenant_id": "personal",
        "name": "Transcripcion",
        "path": str(HOME / "projects" / "personal" / "transcripcion"),
    },
    {
        "id": "asistente-bancario",
        "tenant_id": "personal",
        "name": "Asistente Bancario",
        "path": str(HOME / "projects" / "personal" / "asistente-bancario-inteligente"),
    },
    # --- Empresa (claude-eron) ---
    {
        "id": "eron-devs-marketplace",
        "tenant_id": "empresa",
        "name": "Eron Devs Marketplace",
        "path": str(HOME / "projects" / "eron" / "eron-devs-marketplace"),
    },
    {
        "id": "ml-jiraiya",
        "tenant_id": "empresa",
        "name": "ML Jiraiya",
        "path": str(HOME / "projects" / "eron" / "ml-jiraiya"),
    },
    {
        "id": "newrelic-mcp",
        "tenant_id": "empresa",
        "name": "NewRelic MCP",
        "path": str(HOME / "projects" / "eron" / "newrelic-mcp"),
    },
    {
        "id": "ml-fraud-app",
        "tenant_id": "empresa",
        "name": "ML Fraud App",
        "path": str(HOME / "projects" / "eron" / "ml-fraud-app"),
    },
    {
        "id": "ml-hivemind",
        "tenant_id": "empresa",
        "name": "ML Hivemind",
        "path": str(HOME / "projects" / "eron" / "ml-hivemind"),
    },
    {
        "id": "kaibot",
        "tenant_id": "empresa",
        "name": "Kaibot",
        "path": str(HOME / "projects" / "eron" / "kaibot"),
    },
    {
        "id": "ml-cx-fraud-nexus",
        "tenant_id": "empresa",
        "name": "ML CX Fraud Nexus",
        "path": str(HOME / "projects" / "eron" / "ml-cx-fraud-nexus"),
    },
]


async def seed_defaults():
    for t in TENANTS:
        await repository.upsert_tenant(t["id"], t["name"], t["config_dir"], t["claude_alias"])

    for w in WORKSPACES:
        owner, repo = detect_git_repo(w["path"])
        await repository.upsert_workspace(
            w["id"], w["tenant_id"], w["name"], w["path"],
            repo_owner=owner, repo_name=repo,
        )
