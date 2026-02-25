# Technical Decisions

## 1. Frontend: SvelteKit + Svelte 5 (runes)

- Real-time performance: 60fps at 100 events/sec without optimization
- 35% less code than React (runes vs hooks + external state)
- Built-in state management ($state, $derived, $effect)
- New project, no legacy code to migrate

## 2. Backend: FastAPI (Python)

- Async native (asyncio) for subprocess + SSE
- Existing experience from Verifix
- asyncio.create_subprocess_exec for CLI spawn
- sse-starlette for SSE, pydantic-settings for config

## 3. Agent Engine: Claude CLI subprocess

- $0 extra cost — uses existing subscriptions
- Reads .claude/ config automatically
- --output-format stream-json gives structured NDJSON
- 2 subscriptions = 2 aliases (personal + empresa)

## 4. Protocol: SSE with AG-UI naming

- Standard event names (RunStarted, TextMessageContent, etc.)
- No AG-UI SDK dependency (v0.1.x unstable)
- Easy future migration when AG-UI stabilizes
- Custom fields (agent, phase) for DCC-specific needs

## 5. Database: SQLite

- Personal tool, not multi-user production service
- Zero config, local file
- aiosqlite for async access
- Low volume: hundreds of sessions, not millions

## 6. Theme: Dark glassmorphism, teal #00d4aa

- Differentiated from Verifix (which uses orange #ff6b35)
- Inter font (consistent with Verifix)
- Tailwind v4 with @tailwindcss/vite plugin
