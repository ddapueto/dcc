# DCC — Claude Code Instructions

## Project Overview

DCC (Dev Command Center) is a personal multi-tenant dashboard for managing Claude Code CLI visually.

## Tech Stack

- **Frontend**: SvelteKit + Svelte 5 (runes) + Tailwind v4 + shadcn-svelte
- **Backend**: FastAPI (Python 3.13) + aiosqlite + sse-starlette
- **Package manager**: uv (backend), npm (frontend)
- **DB**: SQLite local file

## Project Structure

```
dcc/
  backend/
    src/dcc/           # FastAPI application
      api/routes/      # REST + SSE endpoints
      db/              # SQLite database layer
      engine/          # CLI runner, stream parser, event converter
      workspace/       # Scanner for .claude/ directories
    tests/             # pytest tests
  frontend/
    src/
      lib/
        components/    # Svelte 5 components
        services/      # API + SSE clients
        stores/        # Svelte 5 rune-based stores
        types/         # TypeScript interfaces
      routes/          # SvelteKit pages
  docs/                # Technical docs
```

## Conventions

- **Language**: Spanish for comments, English for code identifiers
- **Backend**: Async everywhere, Pydantic models for all data
- **Frontend**: Svelte 5 runes ($state, $derived, $effect), NO legacy stores
- **Naming**: snake_case (Python), camelCase (TypeScript)
- **Tests**: pytest + pytest-asyncio for backend

## Key Commands

```bash
# Backend
cd backend && make dev      # Run FastAPI dev server (:8000)
cd backend && make test     # Run tests
cd backend && make lint     # Run ruff check + mypy

# Frontend
cd frontend && npm run dev  # Run SvelteKit dev server (:5173)
cd frontend && npm run build # Build for production
```

## Important Notes

- SSE events follow AG-UI naming convention (RunStarted, TextMessageContent, etc.)
- CLI subprocess uses `--output-format stream-json` for NDJSON streaming
- Unset `CLAUDECODE` env var when spawning CLI subprocess (bug #573)
- Use `--dangerously-skip-permissions` in Phase 1
- Truncate tool results > 2000 chars in event converter
- Theme: dark glassmorphism, teal accent #00d4aa, Inter font
