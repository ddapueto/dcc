# DCC — Dev Command Center

Dashboard personal multi-tenant para gestionar Claude Code CLI desde el browser.

## Stack

- **Frontend**: SvelteKit + Svelte 5 (runes) + Tailwind v4 + shadcn-svelte
- **Backend**: FastAPI + aiosqlite + sse-starlette
- **Motor**: Claude CLI subprocess (`--output-format stream-json`)
- **DB**: SQLite (local)

## Requisitos

- Node v24+ / Bun 1.3+
- Python 3.13+ / uv 0.9+
- Claude CLI v2.1+ con suscripción activa
- Aliases configurados: `claude-personal`, `claude-eron`, `claude-jarix`

## Levantar

### Backend

```bash
cd backend
uv sync
make dev
# → FastAPI en http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → SvelteKit en http://localhost:5173
```

## Verificación rápida

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}

curl http://localhost:8000/api/workspaces
# → lista de workspaces con agents/skills
```

## Arquitectura

```
frontend/ (SvelteKit SPA :5173)
  ↕ SSE + REST (Vite proxy → :8000)
backend/ (FastAPI :8000)
  ├── Workspace Manager (escanea .claude/)
  ├── Session Manager (spawn CLI, parsea stream-json, emite SSE)
  ├── Event Converter (stream-json → AG-UI events)
  └── SQLite (tenants, workspaces, sessions, token_usage)
        ↕
Claude CLI subprocess (claude-personal | claude-eron | claude-jarix)
```

## Tenants

| Tenant   | Alias            | Config Dir          |
|----------|------------------|---------------------|
| personal | claude-personal  | ~/.claude-personal  |
| empresa  | claude-eron      | ~/.claude-eron      |
| jarix    | claude-jarix     | ~/.claude-jarix     |
