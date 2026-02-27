import json
import uuid

from dcc.db.database import get_db

# --- Tenants ---


async def get_tenants() -> list[dict]:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM tenants WHERE is_active = 1 ORDER BY name")
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_tenant(tenant_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def upsert_tenant(tenant_id: str, name: str, config_dir: str, claude_alias: str) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO tenants (id, name, config_dir, claude_alias)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET name=?, config_dir=?, claude_alias=?""",
        (tenant_id, name, config_dir, claude_alias, name, config_dir, claude_alias),
    )
    await db.commit()


# --- Workspaces ---


async def get_workspaces() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT w.*, t.name as tenant_name, t.claude_alias
           FROM workspaces w JOIN tenants t ON w.tenant_id = t.id
           ORDER BY t.name, w.name"""
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_workspace(workspace_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        """SELECT w.*, t.name as tenant_name, t.claude_alias, t.config_dir
           FROM workspaces w JOIN tenants t ON w.tenant_id = t.id
           WHERE w.id = ?""",
        (workspace_id,),
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


async def upsert_workspace(
    workspace_id: str,
    tenant_id: str,
    name: str,
    path: str,
    agents_count: int = 0,
    skills_count: int = 0,
    has_claude_md: bool = False,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT INTO workspaces
             (id, tenant_id, name, path, agents_count, skills_count, has_claude_md, repo_owner, repo_name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             name=?, agents_count=?, skills_count=?, has_claude_md=?,
             repo_owner=?, repo_name=?,
             last_scanned_at=datetime('now')""",
        (
            workspace_id,
            tenant_id,
            name,
            path,
            agents_count,
            skills_count,
            int(has_claude_md),
            repo_owner,
            repo_name,
            name,
            agents_count,
            skills_count,
            int(has_claude_md),
            repo_owner,
            repo_name,
        ),
    )
    await db.commit()


async def update_workspace_scan(
    workspace_id: str,
    agents_count: int,
    skills_count: int,
    has_claude_md: bool,
    repo_owner: str | None = None,
    repo_name: str | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        """UPDATE workspaces
           SET agents_count=?, skills_count=?, has_claude_md=?,
               repo_owner=?, repo_name=?,
               last_scanned_at=datetime('now')
           WHERE id=?""",
        (agents_count, skills_count, int(has_claude_md), repo_owner, repo_name, workspace_id),
    )
    await db.commit()


# --- Sessions ---


async def create_session(
    workspace_id: str,
    prompt: str,
    skill: str | None = None,
    agent: str | None = None,
    model: str | None = None,
    workflow_id: str | None = None,
) -> str:
    session_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        """INSERT INTO sessions (id, workspace_id, prompt, skill, agent, model, workflow_id, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'running')""",
        (session_id, workspace_id, prompt, skill, agent, model, workflow_id),
    )
    await db.commit()
    return session_id


async def update_session_finished(
    session_id: str,
    status: str = "completed",
    model: str | None = None,
    cost_usd: float | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    num_turns: int | None = None,
    duration_ms: int | None = None,
    cli_session_id: str | None = None,
) -> None:
    db = await get_db()
    await db.execute(
        """UPDATE sessions SET
             status=?, model=?, cost_usd=?, input_tokens=?, output_tokens=?,
             num_turns=?, duration_ms=?, cli_session_id=?,
             finished_at=datetime('now')
           WHERE id=?""",
        (
            status,
            model,
            cost_usd,
            input_tokens,
            output_tokens,
            num_turns,
            duration_ms,
            cli_session_id,
            session_id,
        ),
    )
    await db.commit()


async def get_session(session_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def get_sessions(workspace_id: str | None = None, limit: int = 50) -> list[dict]:
    db = await get_db()
    if workspace_id:
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE workspace_id = ? ORDER BY started_at DESC LIMIT ?",
            (workspace_id, limit),
        )
    else:
        cursor = await db.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# --- Session Events ---


async def insert_session_events_batch(
    events: list[tuple[str, int, str, str]],
) -> None:
    """Batch insert session events. Each tuple: (session_id, seq, event_type, data)."""
    if not events:
        return
    db = await get_db()
    await db.executemany(
        "INSERT INTO session_events (session_id, seq, event_type, data) VALUES (?, ?, ?, ?)",
        events,
    )
    await db.commit()


async def get_session_events(session_id: str) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM session_events WHERE session_id = ? ORDER BY seq",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


async def get_sessions_with_search(
    workspace_id: str | None = None,
    tenant_id: str | None = None,
    status: str | None = None,
    search: str | None = None,
    agent: str | None = None,
    limit: int = 25,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """Get sessions with filters, search, and pagination. Returns (sessions, total)."""
    db = await get_db()

    base = """FROM sessions s
              JOIN workspaces w ON s.workspace_id = w.id
              JOIN tenants t ON w.tenant_id = t.id"""
    conditions: list[str] = []
    params: list[str | int] = []

    if workspace_id:
        conditions.append("s.workspace_id = ?")
        params.append(workspace_id)
    if tenant_id:
        conditions.append("w.tenant_id = ?")
        params.append(tenant_id)
    if status:
        conditions.append("s.status = ?")
        params.append(status)
    if search:
        conditions.append("s.prompt LIKE ?")
        params.append(f"%{search}%")
    if agent:
        conditions.append("s.agent = ?")
        params.append(agent)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    # Count
    count_cursor = await db.execute(f"SELECT COUNT(*) {base}{where}", params)
    total = (await count_cursor.fetchone())[0]

    # Fetch
    select = f"""SELECT s.*, w.name as workspace_name, w.tenant_id, t.name as tenant_name
                 {base}{where}
                 ORDER BY s.started_at DESC LIMIT ? OFFSET ?"""
    cursor = await db.execute(select, [*params, limit, offset])
    rows = await cursor.fetchall()
    return [dict(r) for r in rows], total


# --- Session Diffs ---


async def insert_session_diff(
    session_id: str,
    diff_stat: str | None,
    diff_content: str | None,
    files_changed: int = 0,
    insertions: int = 0,
    deletions: int = 0,
) -> None:
    db = await get_db()
    await db.execute(
        """INSERT OR REPLACE INTO session_diffs
             (session_id, diff_stat, diff_content, files_changed, insertions, deletions)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (session_id, diff_stat, diff_content, files_changed, insertions, deletions),
    )
    await db.commit()


async def get_session_diff(session_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM session_diffs WHERE session_id = ?", (session_id,)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None


# --- Delete ---


async def delete_workspace(workspace_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM workspaces WHERE id = ?", (workspace_id,))
    await db.commit()
    return cursor.rowcount > 0


async def delete_tenant(tenant_id: str) -> bool:
    db = await get_db()
    cursor = await db.execute("DELETE FROM tenants WHERE id = ?", (tenant_id,))
    await db.commit()
    return cursor.rowcount > 0


# --- Analytics ---


async def get_analytics_summary() -> dict:
    db = await get_db()

    cursor = await db.execute(
        """SELECT
             COUNT(*) as total_sessions,
             COALESCE(SUM(cost_usd), 0) as total_cost,
             COALESCE(SUM(input_tokens), 0) as total_input_tokens,
             COALESCE(SUM(output_tokens), 0) as total_output_tokens
           FROM sessions"""
    )
    totals = dict(await cursor.fetchone())

    cursor = await db.execute(
        """SELECT COALESCE(SUM(cost_usd), 0) as cost_7d, COUNT(*) as sessions_7d
           FROM sessions
           WHERE started_at >= datetime('now', '-7 days')"""
    )
    week = dict(await cursor.fetchone())

    cursor = await db.execute(
        """SELECT COALESCE(SUM(cost_usd), 0) as cost_24h, COUNT(*) as sessions_24h
           FROM sessions
           WHERE started_at >= datetime('now', '-1 day')"""
    )
    day = dict(await cursor.fetchone())

    cursor = await db.execute(
        """SELECT status, COUNT(*) as count
           FROM sessions GROUP BY status"""
    )
    by_status = {row["status"]: row["count"] for row in await cursor.fetchall()}

    return {**totals, **week, **day, "by_status": by_status}


async def get_cost_by_workspace() -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT w.name as workspace_name, t.name as tenant_name,
                  COUNT(*) as session_count,
                  COALESCE(SUM(s.cost_usd), 0) as total_cost,
                  COALESCE(SUM(s.input_tokens), 0) as total_input_tokens,
                  COALESCE(SUM(s.output_tokens), 0) as total_output_tokens
           FROM sessions s
           JOIN workspaces w ON s.workspace_id = w.id
           JOIN tenants t ON w.tenant_id = t.id
           GROUP BY s.workspace_id
           ORDER BY total_cost DESC"""
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_cost_trend(days: int = 30) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        """SELECT DATE(started_at) as date,
                  COUNT(*) as sessions,
                  COALESCE(SUM(cost_usd), 0) as cost
           FROM sessions
           WHERE started_at >= datetime('now', ? || ' days')
           GROUP BY DATE(started_at)
           ORDER BY date""",
        (f"-{days}",),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_top_skills(limit: int = 10) -> list[dict]:
    db = await get_db()
    # Combine skills and agents into one ranking
    cursor = await db.execute(
        """SELECT
             CASE
               WHEN skill IS NOT NULL THEN '/' || skill
               WHEN agent IS NOT NULL THEN '@' || agent
               ELSE '(prompt)'
             END as name,
             CASE
               WHEN skill IS NOT NULL THEN 'skill'
               WHEN agent IS NOT NULL THEN 'agent'
               ELSE 'prompt'
             END as kind,
             COUNT(*) as count,
             COALESCE(SUM(cost_usd), 0) as total_cost
           FROM sessions
           GROUP BY name, kind
           ORDER BY count DESC
           LIMIT ?""",
        (limit,),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_token_efficiency() -> dict:
    db = await get_db()
    cursor = await db.execute(
        """SELECT
             COALESCE(SUM(input_tokens), 0) as total_input,
             COALESCE(SUM(output_tokens), 0) as total_output
           FROM sessions"""
    )
    session_totals = dict(await cursor.fetchone())

    cursor = await db.execute(
        """SELECT
             COALESCE(SUM(cache_read_tokens), 0) as cache_read,
             COALESCE(SUM(cache_write_tokens), 0) as cache_write
           FROM token_usage"""
    )
    cache_totals = dict(await cursor.fetchone())

    total_input = session_totals["total_input"]
    cache_read = cache_totals["cache_read"]
    cache_hit_ratio = (cache_read / total_input) if total_input > 0 else 0

    return {
        **session_totals,
        **cache_totals,
        "cache_hit_ratio": round(cache_hit_ratio, 4),
    }


# --- Workflows ---


def _parse_workflow(row: dict) -> dict:
    """Parse parameters JSON string to list."""
    wf = dict(row)
    raw = wf.get("parameters", "[]")
    try:
        wf["parameters"] = json.loads(raw) if raw else []
    except (json.JSONDecodeError, TypeError):
        wf["parameters"] = []
    wf["is_builtin"] = bool(wf.get("is_builtin", 0))
    return wf


async def create_workflow(
    workspace_id: str,
    name: str,
    prompt_template: str,
    description: str | None = None,
    category: str = "custom",
    icon: str = "Workflow",
    parameters: list[dict] | None = None,
    model: str | None = None,
    is_builtin: bool = False,
) -> str:
    workflow_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        """INSERT INTO workflows
             (id, workspace_id, name, prompt_template, description, category, icon, parameters, model, is_builtin)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            workflow_id,
            workspace_id,
            name,
            prompt_template,
            description,
            category,
            icon,
            json.dumps(parameters or []),
            model,
            int(is_builtin),
        ),
    )
    await db.commit()
    return workflow_id


async def get_workflow(workflow_id: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,))
    row = await cursor.fetchone()
    return _parse_workflow(row) if row else None


async def get_workflows(
    workspace_id: str | None = None,
    category: str | None = None,
) -> list[dict]:
    db = await get_db()
    conditions: list[str] = []
    params: list[str] = []

    if workspace_id:
        conditions.append("workspace_id = ?")
        params.append(workspace_id)
    if category:
        conditions.append("category = ?")
        params.append(category)

    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    cursor = await db.execute(
        f"SELECT * FROM workflows{where} ORDER BY is_builtin DESC, usage_count DESC",
        params,
    )
    rows = await cursor.fetchall()
    return [_parse_workflow(r) for r in rows]


async def update_workflow(workflow_id: str, **kwargs: str | list | None) -> None:
    sets: list[str] = []
    params: list = []
    for key, value in kwargs.items():
        if key == "parameters" and isinstance(value, list):
            sets.append("parameters = ?")
            params.append(json.dumps(value))
        elif value is not None:
            sets.append(f"{key} = ?")
            params.append(value)

    if not sets:
        return

    db = await get_db()
    params.append(workflow_id)
    await db.execute(
        f"UPDATE workflows SET {', '.join(sets)} WHERE id = ?", params
    )
    await db.commit()


async def delete_workflow(workflow_id: str) -> bool:
    db = await get_db()
    # Solo custom (is_builtin=0)
    cursor = await db.execute(
        "DELETE FROM workflows WHERE id = ? AND is_builtin = 0", (workflow_id,)
    )
    await db.commit()
    return cursor.rowcount > 0


async def increment_workflow_usage(workflow_id: str) -> None:
    db = await get_db()
    await db.execute(
        """UPDATE workflows SET usage_count = usage_count + 1, last_used_at = datetime('now')
           WHERE id = ?""",
        (workflow_id,),
    )
    await db.commit()


# --- Monitor Tasks ---


async def create_monitor_task(
    session_id: str,
    tool_call_id: str,
    tool_name: str,
    parent_id: str | None = None,
    description: str | None = None,
    input_summary: str | None = None,
    depth: int = 0,
    subagent_type: str | None = None,
    subagent_model: str | None = None,
) -> str:
    task_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        """INSERT INTO monitor_tasks
             (id, session_id, tool_call_id, tool_name, parent_id, description,
              input_summary, depth, subagent_type, subagent_model)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            task_id, session_id, tool_call_id, tool_name, parent_id,
            description, input_summary, depth, subagent_type, subagent_model,
        ),
    )
    await db.commit()
    return task_id


async def update_monitor_task(
    task_id: str,
    status: str,
    output_summary: str | None = None,
    duration_ms: int | None = None,
) -> None:
    db = await get_db()
    sets = ["status = ?"]
    params: list = [status]

    if output_summary is not None:
        sets.append("output_summary = ?")
        params.append(output_summary)
    if duration_ms is not None:
        sets.append("duration_ms = ?")
        params.append(duration_ms)

    if status in ("completed", "failed"):
        sets.append("finished_at = datetime('now')")

    params.append(task_id)
    await db.execute(
        f"UPDATE monitor_tasks SET {', '.join(sets)} WHERE id = ?", params
    )
    await db.commit()


async def get_monitor_tasks(session_id: str) -> list[dict]:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM monitor_tasks WHERE session_id = ? ORDER BY started_at",
        (session_id,),
    )
    rows = await cursor.fetchall()
    return [dict(r) for r in rows]


# --- Agent Registry ---


def _parse_agent_row(row: dict) -> dict:
    """Parse JSON fields in agent_registry row."""
    agent = dict(row)
    for field in ("tools", "disallowed_tools", "skills"):
        raw = agent.get(field, "[]")
        try:
            agent[field] = json.loads(raw) if raw else []
        except (json.JSONDecodeError, TypeError):
            agent[field] = []
    agent["background"] = bool(agent.get("background", 0))
    agent["is_active"] = bool(agent.get("is_active", 1))
    return agent


async def upsert_agent(
    workspace_id: str,
    name: str,
    filename: str,
    description: str = "",
    model: str | None = None,
    tools: list[str] | None = None,
    disallowed_tools: list[str] | None = None,
    permission_mode: str | None = None,
    max_turns: int | None = None,
    skills: list[str] | None = None,
    memory: str | None = None,
    background: bool = False,
    isolation: str | None = None,
    system_prompt: str = "",
) -> str:
    agent_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        """INSERT INTO agent_registry
             (id, workspace_id, name, filename, description, model, tools,
              disallowed_tools, permission_mode, max_turns, skills, memory,
              background, isolation, system_prompt)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(workspace_id, name) DO UPDATE SET
             filename=excluded.filename, description=excluded.description,
             model=excluded.model, tools=excluded.tools,
             disallowed_tools=excluded.disallowed_tools,
             permission_mode=excluded.permission_mode,
             max_turns=excluded.max_turns, skills=excluded.skills,
             memory=excluded.memory, background=excluded.background,
             isolation=excluded.isolation, system_prompt=excluded.system_prompt,
             last_seen_at=datetime('now'), is_active=1""",
        (
            agent_id, workspace_id, name, filename, description, model,
            json.dumps(tools or []), json.dumps(disallowed_tools or []),
            permission_mode, max_turns, json.dumps(skills or []),
            memory, int(background), isolation, system_prompt,
        ),
    )
    await db.commit()
    # Return actual id (may differ if conflict)
    cursor = await db.execute(
        "SELECT id FROM agent_registry WHERE workspace_id = ? AND name = ?",
        (workspace_id, name),
    )
    row = await cursor.fetchone()
    return row["id"]


async def get_agents_for_workspace(
    workspace_id: str, active_only: bool = True
) -> list[dict]:
    db = await get_db()
    query = "SELECT * FROM agent_registry WHERE workspace_id = ?"
    params: list = [workspace_id]
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY name"
    cursor = await db.execute(query, params)
    rows = await cursor.fetchall()
    return [_parse_agent_row(r) for r in rows]


async def deactivate_missing_agents(
    workspace_id: str, active_names: list[str]
) -> None:
    db = await get_db()
    if not active_names:
        await db.execute(
            "UPDATE agent_registry SET is_active = 0 WHERE workspace_id = ?",
            (workspace_id,),
        )
    else:
        placeholders = ",".join("?" for _ in active_names)
        await db.execute(
            f"""UPDATE agent_registry SET is_active = 0
                WHERE workspace_id = ? AND name NOT IN ({placeholders})""",
            [workspace_id, *active_names],
        )
    await db.commit()


async def get_agent_by_name(workspace_id: str, name: str) -> dict | None:
    db = await get_db()
    cursor = await db.execute(
        "SELECT * FROM agent_registry WHERE workspace_id = ? AND name = ?",
        (workspace_id, name),
    )
    row = await cursor.fetchone()
    return _parse_agent_row(row) if row else None


# --- Agent Analytics ---


async def get_agent_usage_stats(workspace_id: str | None = None) -> list[dict]:
    """Per-agent: sessions count, total cost, avg duration, success rate."""
    db = await get_db()
    conditions = ["s.agent IS NOT NULL"]
    params: list = []
    if workspace_id:
        conditions.append("s.workspace_id = ?")
        params.append(workspace_id)
    where = " WHERE " + " AND ".join(conditions)

    cursor = await db.execute(
        f"""SELECT s.agent as name,
                   COUNT(*) as sessions,
                   COALESCE(SUM(s.cost_usd), 0) as total_cost,
                   ROUND(AVG(s.duration_ms)) as avg_duration_ms,
                   ROUND(100.0 * SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END)
                         / COUNT(*), 1) as success_rate
            FROM sessions s{where}
            GROUP BY s.agent
            ORDER BY sessions DESC""",
        params,
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_agent_cost_trend(agent_name: str, days: int = 30) -> list[dict]:
    """Cost trend diario para un agent especifico."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT DATE(started_at) as date,
                  COUNT(*) as sessions,
                  COALESCE(SUM(cost_usd), 0) as cost
           FROM sessions
           WHERE agent = ? AND started_at >= datetime('now', ? || ' days')
           GROUP BY DATE(started_at)
           ORDER BY date""",
        (agent_name, f"-{days}"),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_subagent_delegation_stats() -> list[dict]:
    """Que agents delegan a que subagents (de monitor_tasks)."""
    db = await get_db()
    cursor = await db.execute(
        """SELECT s.agent as parent_agent,
                  mt.subagent_type,
                  COUNT(*) as count,
                  ROUND(AVG(mt.duration_ms)) as avg_duration_ms
           FROM monitor_tasks mt
           JOIN sessions s ON mt.session_id = s.id
           WHERE mt.tool_name = 'Task' AND mt.subagent_type IS NOT NULL
           GROUP BY s.agent, mt.subagent_type
           ORDER BY count DESC"""
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_agent_comparison(agent_names: list[str]) -> list[dict]:
    """Comparacion side-by-side de metricas por agent."""
    if not agent_names:
        return []
    db = await get_db()
    placeholders = ",".join("?" for _ in agent_names)
    cursor = await db.execute(
        f"""SELECT s.agent as name,
                   COUNT(*) as sessions,
                   COALESCE(SUM(s.cost_usd), 0) as total_cost,
                   ROUND(AVG(s.duration_ms)) as avg_duration_ms,
                   ROUND(100.0 * SUM(CASE WHEN s.status = 'completed' THEN 1 ELSE 0 END)
                         / COUNT(*), 1) as success_rate,
                   COALESCE(SUM(s.input_tokens), 0) as total_input_tokens,
                   COALESCE(SUM(s.output_tokens), 0) as total_output_tokens
            FROM sessions s
            WHERE s.agent IN ({placeholders})
            GROUP BY s.agent
            ORDER BY sessions DESC""",
        agent_names,
    )
    return [dict(r) for r in await cursor.fetchall()]
