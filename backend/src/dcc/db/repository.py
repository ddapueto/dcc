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
) -> str:
    session_id = str(uuid.uuid4())
    db = await get_db()
    await db.execute(
        """INSERT INTO sessions (id, workspace_id, prompt, skill, agent, model, status)
           VALUES (?, ?, ?, ?, ?, ?, 'running')""",
        (session_id, workspace_id, prompt, skill, agent, model),
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
