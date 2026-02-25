# DCC Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                     Browser (:5173)                      │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────────┐  │
│  │Workspace│ │  Skill   │ │ Prompt │ │   Stream     │  │
│  │ Picker  │ │ Picker   │ │ Input  │ │   Output     │  │
│  └────┬────┘ └────┬─────┘ └───┬────┘ └──────▲───────┘  │
│       │           │           │              │           │
│       └───────────┴───────┬───┘              │           │
│                           │ REST             │ SSE       │
└───────────────────────────┼──────────────────┼───────────┘
                            │ Vite proxy       │
┌───────────────────────────┼──────────────────┼───────────┐
│                    FastAPI (:8000)            │           │
│  ┌────────────────┐  ┌────────────┐  ┌───────┴────────┐ │
│  │   Workspace    │  │  Session   │  │    SSE Event   │ │
│  │   Scanner      │  │  Manager   │  │    Emitter     │ │
│  │ (.claude/ dir) │  │            │  │                │ │
│  └───────┬────────┘  └─────┬──────┘  └───────▲────────┘ │
│          │                 │                  │          │
│          │          ┌──────▼──────┐   ┌───────┴────────┐ │
│          │          │  CLI Runner │──▶│Event Converter │ │
│          │          │ (subprocess)│   │ CLI→AG-UI      │ │
│          │          └──────┬──────┘   └────────────────┘ │
│          │                 │                             │
│   ┌──────▼─────────────────▼──────┐                     │
│   │         SQLite DB             │                     │
│   │ tenants│workspaces│sessions   │                     │
│   └───────────────────────────────┘                     │
└─────────────────────────────────────────────────────────┘
                         │
              ┌──────────▼──────────┐
              │   Claude CLI        │
              │   subprocess        │
              │                     │
              │ claude-personal     │
              │ claude-eron         │
              │ claude-jarix        │
              │                     │
              │ --output-format     │
              │   stream-json       │
              └─────────────────────┘
```

## Data Flow: Execute Skill

1. User selects workspace + skill in browser
2. Frontend POSTs to `/api/sessions` with workspace_id, skill, prompt
3. Backend creates session in SQLite, returns session_id
4. Frontend connects to `/api/sessions/{id}/stream` (SSE)
5. Backend spawns CLI subprocess with correct alias/config_dir
6. CLI streams NDJSON to stdout
7. `stream_parser` parses each line into `CliEvent`
8. `event_converter` maps `CliEvent` → `AgUiEvent`(s)
9. SSE emitter sends events to frontend
10. Frontend updates stores reactively
11. On `result` event → RunFinished with cost/tokens

## Event Mapping: CLI → AG-UI

| CLI Event Type | AG-UI Event(s) |
|---------------|----------------|
| system (init) | StateSnapshot |
| assistant (text) | TextMessageStart + Content + End |
| assistant (tool_use) | ToolCallStart + ToolCallEnd |
| user (tool_result) | ToolCallResult |
| stream_event (text_delta) | TextMessageContent |
| result | RunFinished |

## Multi-Tenant Model

Each tenant maps to a CLI alias with its own config directory:

```
Tenant "personal" → CLAUDE_CONFIG_DIR=~/.claude-personal
Tenant "empresa"  → CLAUDE_CONFIG_DIR=~/.claude-eron
Tenant "jarix"    → CLAUDE_CONFIG_DIR=~/.claude-jarix
```

Workspaces belong to tenants. The CLI subprocess inherits the tenant's
config dir, which determines authentication and loaded config.
