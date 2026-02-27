SCHEMA = """
CREATE TABLE IF NOT EXISTS tenants (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    config_dir TEXT NOT NULL,
    claude_alias TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    tenant_id TEXT NOT NULL REFERENCES tenants(id),
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    agents_count INTEGER NOT NULL DEFAULT 0,
    skills_count INTEGER NOT NULL DEFAULT 0,
    has_claude_md INTEGER NOT NULL DEFAULT 0,
    repo_owner TEXT,
    repo_name TEXT,
    last_scanned_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    cli_session_id TEXT,
    skill TEXT,
    agent TEXT,
    prompt TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    model TEXT,
    cost_usd REAL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    num_turns INTEGER,
    duration_ms INTEGER,
    workflow_id TEXT REFERENCES workflows(id),
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT
);

CREATE TABLE IF NOT EXISTS token_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    input_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cache_read_tokens INTEGER NOT NULL DEFAULT 0,
    cache_write_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd REAL NOT NULL DEFAULT 0,
    recorded_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    seq INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_session_events_session ON session_events(session_id);

CREATE TABLE IF NOT EXISTS session_diffs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE REFERENCES sessions(id),
    diff_stat TEXT,
    diff_content TEXT,
    files_changed INTEGER DEFAULT 0,
    insertions INTEGER DEFAULT 0,
    deletions INTEGER DEFAULT 0,
    captured_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_session_diffs_session ON session_diffs(session_id);

CREATE TABLE IF NOT EXISTS workflows (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT DEFAULT 'custom',
    icon TEXT DEFAULT 'Workflow',
    prompt_template TEXT NOT NULL,
    parameters TEXT DEFAULT '[]',
    model TEXT,
    is_builtin INTEGER NOT NULL DEFAULT 0,
    usage_count INTEGER NOT NULL DEFAULT 0,
    last_used_at TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS monitor_tasks (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    parent_id TEXT REFERENCES monitor_tasks(id),
    tool_call_id TEXT,
    tool_name TEXT NOT NULL,
    description TEXT,
    subagent_type TEXT,
    subagent_model TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    input_summary TEXT,
    output_summary TEXT,
    depth INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    finished_at TEXT,
    duration_ms INTEGER
);
CREATE INDEX IF NOT EXISTS idx_monitor_tasks_session ON monitor_tasks(session_id);

CREATE TABLE IF NOT EXISTS agent_registry (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL REFERENCES workspaces(id),
    name TEXT NOT NULL,
    filename TEXT NOT NULL,
    description TEXT DEFAULT '',
    model TEXT,
    tools TEXT DEFAULT '[]',
    disallowed_tools TEXT DEFAULT '[]',
    permission_mode TEXT,
    max_turns INTEGER,
    skills TEXT DEFAULT '[]',
    memory TEXT,
    background INTEGER NOT NULL DEFAULT 0,
    isolation TEXT,
    system_prompt TEXT DEFAULT '',
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(workspace_id, name)
);
CREATE INDEX IF NOT EXISTS idx_agent_registry_workspace ON agent_registry(workspace_id);
"""
