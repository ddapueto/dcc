# DCC — Claude Code Instructions

## Project Overview

DCC (Dev Command Center) is a personal multi-tenant dashboard for managing Claude Code CLI visually. Phases 1–3 complete.

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
      api/routes/        # REST + SSE + analytics endpoints
      db/                # SQLite: models, database, repository, seed
      engine/            # CLI runner, stream parser, event converter
      workspace/         # Scanner for .claude/ directories
    tests/               # pytest tests (51 tests)
  frontend/
    src/
      lib/
        actions/         # Keyboard shortcuts (shortcuts.ts)
        components/      # Svelte 5 components
          dashboard/     # Analytics charts (StatCard, StatusDonut, CostBarChart, CostTrendChart, TopSkillsList)
        services/        # API + SSE clients
        stores/          # Svelte 5 rune-based stores (tabs, workspaces, history, toasts, analytics)
        types/           # TypeScript interfaces
      routes/            # SvelteKit pages
        dashboard/       # Analytics dashboard
        run/             # CLI runner with tabs
        history/         # Session history + replay
        config/          # CLAUDE.md / rules / settings viewer
        manage/          # CRUD workspaces / tenants
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
cd backend && make test     # Run tests (51 tests)
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
