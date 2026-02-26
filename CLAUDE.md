# DCC — Claude Code Instructions

## Project Overview

DCC (Dev Command Center) is a personal multi-tenant dashboard for managing Claude Code CLI visually. Phases 1–5 complete.

## Tech Stack

- **Frontend**: SvelteKit + Svelte 5 (runes) + Tailwind v4 + marked + highlight.js
- **Backend**: FastAPI (Python 3.13) + aiosqlite + sse-starlette
- **Package manager**: uv (backend), npm (frontend)
- **DB**: SQLite local file

## Project Structure

```
dcc/
  backend/
    src/dcc/
      api/routes/        # REST + SSE + analytics + GitHub proxy + pipeline endpoints
      db/                # SQLite: models, database, repository, seed
      engine/            # CLI runner, stream parser, event converter, gh client, git diff, pipeline executor, agent router, plan builder
      workspace/         # Scanner for .claude/ directories, git detection, MCP scanner
    tests/               # pytest tests (105 tests)
  frontend/
    src/
      lib/
        actions/         # Keyboard shortcuts (shortcuts.ts)
        components/      # Svelte 5 components
          dashboard/     # Analytics charts (StatCard, StatusDonut, CostBarChart, CostTrendChart, TopSkillsList)
        services/        # API + SSE clients
        stores/          # Svelte 5 rune-based stores (tabs, workspaces, history, toasts, analytics, github, pipelines)
        types/           # TypeScript interfaces
      routes/            # SvelteKit pages
        dashboard/       # Analytics dashboard
        run/             # CLI runner with tabs
        history/         # Session history + replay
        config/          # CLAUDE.md / rules / settings viewer
        manage/          # CRUD workspaces / tenants
        pipelines/       # Pipeline list, detail (DAG view), creation wizard
  docs/                  # Technical docs
```

## Conventions

- **Language**: Spanish for comments, English for code identifiers
- **Backend**: Async everywhere, Pydantic models for all data
- **Frontend**: Svelte 5 runes ($state, $derived, $effect), NO legacy stores or `<svelte:component>`
- **Naming**: snake_case (Python), camelCase (TypeScript)
- **Tests**: pytest + pytest-asyncio for backend
- **Charts**: SVG + HTML bars only (no chart libraries), glassmorphism style

## Key Commands

```bash
# Backend
cd backend && make dev      # Run FastAPI dev server (:8000)
cd backend && make test     # Run tests (105 tests)
cd backend && make lint     # Run ruff check + mypy

# Frontend
cd frontend && npm run dev  # Run SvelteKit dev server (:5173)
cd frontend && npm run build # Build for production
cd frontend && npx svelte-check  # Type check
```

## Architecture Notes

- SSE events follow AG-UI naming convention (RunStarted, TextMessageContent, etc.)
- CLI subprocess uses `--output-format stream-json` for NDJSON streaming
- Unset `CLAUDECODE` env var when spawning CLI subprocess (bug #573)
- Use `--dangerously-skip-permissions` in Phase 1
- Truncate tool results > 2000 chars in event converter
- Theme: dark glassmorphism, teal accent #00d4aa, Inter font
- Markdown rendering: `marked` (GFM + breaks) + `highlight.js` (ts, py, bash, json, html, css)
- Model selector: pills in PromptInput, value passed through TabSession.start() → createSession API
- Prompt history: localStorage `dcc:prompt-history`, ArrowUp/Down navigation, max 50 entries
- Keyboard shortcuts: Cmd+K (new tab), Cmd+W (close tab), Cmd+1–9 (switch), Esc (cancel) — in `lib/actions/shortcuts.ts`
- Toast notifications: auto-dismiss 4s, background tab completion triggers toastStore from TabSession
- Analytics: 5 SQL aggregation functions in repository.py, 5 GET endpoints at `/api/analytics/*`
- Dashboard charts are pure SVG/HTML (StatusDonut, CostTrendChart, CostBarChart, TopSkillsList, StatCard)
- Git repo auto-detection: parses `.git/config` remote origin (SSH + HTTPS GitHub URLs) → `repo_owner`/`repo_name` on workspaces
- MCP server scanner: reads `.mcp.json` (workspace-level) + `settings.local.json` (global config_dir), workspace overrides global on name conflict
- GitHub integration: `gh_client.py` wraps `gh api` subprocess (15s timeout), `github.py` router proxies milestones/issues/PRs at `/api/github/*`
- Git diff capture: CliRunner snapshots HEAD before run, computes `git diff` + `git log` after run, stores in `session_diffs` table (50KB max)
- DiffViewer: lazy-loads diff on expand, colored lines (+green/-red/@@cyan), badge shows "N files +ins -del"
- GitHubPanel: collapsible sections (issues/PRs/milestones) in /run sidebar, click issue pre-fills prompt with `Issue #N: title\n\nbody`
- Context sharing: "Use as context" button on completed sessions opens new tab with output as prefill
- ConfigViewer MCPs tab: shows MCP servers with name, command, args, source badge (workspace/global)
- Schema changes require deleting `dcc.db` to recreate (no migrations) — `session_diffs` table, `repo_owner`/`repo_name` columns on workspaces
- DB tables: tenants, workspaces, sessions, token_usage, session_events, session_diffs, pipelines, pipeline_steps
- Pipeline engine: PipelineExecutor runs steps respecting depends_on DAG, parallel execution (max_parallel), SSE streaming of pipeline-level events
- Pipeline events: PipelineStarted, PipelineStepStarted, PipelineStepCompleted, PipelineStepFailed, PipelineCompleted, PipelineFailed
- Agent router: keyword-based agent suggestion for pipeline steps (agent_router.py)
- Plan builder: constructs planner prompts from spec or milestone issues, parses Claude output to steps (plan_builder.py)
- Pipeline API: CRUD at `/api/pipelines/*`, generate from spec/milestone, execute via SSE, cancel/pause/resume
- Pipeline steps use depends_on as JSON TEXT array of step IDs (no junction table)
- Pipeline context passing: {{prev_output}}, {{step.ID.output}}, {{spec}} in prompt templates
- Pipeline DAG visualization: SVG with topological sort layering, foreignObject for node HTML (PipelineGraph.svelte)
- Pipeline creation wizard: 3-step flow (Source → Review → Confirm) with From Spec / From Milestone modes
