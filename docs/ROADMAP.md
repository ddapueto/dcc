# DCC Product Roadmap

## Vision

Convertir DCC de un "visual terminal wrapper" a un **AI Project Manager** capaz de:
- Tomar un milestone o spec de GitHub
- Descomponer en tareas con dependencias
- Orquestar múltiples agentes de Claude Code (paralelo + secuencial)
- Evaluar resultados en cada paso y decidir next action
- Mostrar todo visualmente con métricas en tiempo real

## Estado actual (Fases 1-3 completadas)

| Fase | Entregable | Status |
|------|-----------|--------|
| Fase 1 | Workspace scanner, CLI runner, SSE streaming, UI base | Done |
| Fase 2 | Session history, config viewer, tabs, CRUD workspaces/tenants | Done |
| Fase 3 | Markdown rendering, model selector, prompt history, shortcuts, toasts, analytics dashboard | Done |

**Infraestructura disponible**: 51 tests, 5 analytics endpoints, multi-tab SSE, AG-UI event system, Svelte 5 runes.

---

## Fase 4: Integration & Visibility

> **Objetivo**: Antes de orquestar, necesitás VER qué pasó y conectar con las fuentes de trabajo (GitHub).

### 4.1 GitHub Integration

Leer datos de GitHub directamente desde DCC usando el MCP de GitHub que ya está configurado.

**Backend**:
- Nuevo router `api/routes/github.py`
- Endpoints proxy que usan `gh` CLI (ya disponible en el sistema):
  - `GET /api/github/milestones?repo=owner/repo` — listar milestones
  - `GET /api/github/milestone/{number}/issues?repo=...` — issues de un milestone
  - `GET /api/github/issue/{number}?repo=...` — detalle de issue
  - `GET /api/github/prs?repo=...` — PRs abiertas
  - `POST /api/github/issue` — crear issue desde DCC

**Frontend**:
- Panel lateral en `/run` que muestra issues del workspace actual
- Vista de milestone con issues agrupados por estado
- Click en issue → pre-llena el prompt con contexto del issue

### 4.2 Diff Viewer

Ver qué archivos modificó cada sesión de Claude.

**Backend**:
- `CliRunner` captura git diff antes y después de la ejecución
- Nuevo campo `artifacts` en tabla `sessions` (JSON: files changed, insertions, deletions)
- Endpoint `GET /api/sessions/{id}/diff` retorna el diff

**Frontend**:
- Componente `DiffViewer.svelte` — muestra archivos modificados con +/- coloreado
- Integrado en StreamOutput como panel colapsable post-ejecución
- En `/history` — ver diff de sesiones pasadas

### 4.3 Session Artifacts & Context Sharing

Permitir que el output de una sesión sea input de otra.

**Backend**:
- Tabla `session_artifacts` (session_id, type, content, metadata)
- Types: `text_output`, `diff`, `file_list`, `summary`
- Endpoint `GET /api/sessions/{id}/artifacts`

**Frontend**:
- Botón "Use as context" en una tab completada → copia el output como prefijo del prompt en otra tab
- Artifacts panel en `/history` para seleccionar outputs anteriores

### 4.4 MCP Registry

Mostrar qué MCPs están configurados por workspace.

**Backend**:
- Scanner lee `.mcp.json` y `settings.local.json` del workspace
- Endpoint `GET /api/workspaces/{id}/mcps` → lista de MCPs con status

**Frontend**:
- Sección en `/config` que muestra MCPs configurados
- Badges en workspace picker indicando MCPs disponibles

---

## Fase 5: Pipeline Engine (Orquestación)

> **Objetivo**: El corazón del producto — definir y ejecutar workflows multi-agente.

### 5.1 Pipeline Data Model

**Nuevas tablas**:
```sql
pipelines (
  id TEXT PRIMARY KEY,
  workspace_id TEXT REFERENCES workspaces(id),
  name TEXT NOT NULL,
  description TEXT,
  spec TEXT,              -- El spec original (markdown/text)
  status TEXT DEFAULT 'draft',  -- draft | ready | running | completed | failed
  source_type TEXT,       -- 'manual' | 'milestone' | 'issue'
  source_ref TEXT,        -- GitHub milestone/issue number
  total_cost REAL DEFAULT 0,
  created_at TEXT,
  started_at TEXT,
  finished_at TEXT
)

pipeline_steps (
  id TEXT PRIMARY KEY,
  pipeline_id TEXT REFERENCES pipelines(id),
  position INTEGER,       -- Orden visual
  name TEXT NOT NULL,
  description TEXT,
  agent TEXT,             -- Agent asignado (o null = prompt directo)
  skill TEXT,             -- Skill asignado (o null)
  model TEXT,             -- Model override (o null = default)
  prompt_template TEXT,   -- Prompt con placeholders {{prev_output}}, {{issue_body}}
  status TEXT DEFAULT 'pending',  -- pending | running | completed | failed | skipped
  session_id TEXT REFERENCES sessions(id),  -- Sesión CLI ejecutada
  output_summary TEXT,    -- Resumen del output (para pasar a steps siguientes)
  depends_on TEXT,        -- JSON array de step IDs (dependencias)
  created_at TEXT,
  started_at TEXT,
  finished_at TEXT
)
```

### 5.2 Plan Builder

Dos modos de crear pipelines:

**Modo A: Desde GitHub Milestone**
1. Usuario selecciona milestone del workspace
2. DCC carga los issues del milestone
3. Un agente "planner" (Claude) analiza los issues y genera un pipeline:
   - Agrupa issues por dependencia
   - Asigna agentes según el tipo de tarea
   - Define orden (paralelo donde se puede, secuencial donde hay deps)
4. Usuario revisa, ajusta, y aprueba el plan

**Modo B: Desde Spec Manual**
1. Usuario escribe un spec en texto libre (markdown)
2. Agente planner descompone en steps
3. Mismo flow de revisión y aprobación

**Backend**:
- Endpoint `POST /api/pipelines/generate` — recibe spec/milestone, retorna pipeline draft
- Internamente ejecuta una sesión Claude con el skill `orchestrate` o `plan-sprint`
- Parsea el output y crea los `pipeline_steps`

**Frontend**:
- Página `/pipelines/new` — wizard de creación (select source → generate → review → approve)
- Editor visual de steps (drag & drop para reordenar, edit agent/prompt por step)

### 5.3 Agent Router

Asignación inteligente de agentes a steps.

**Lógica de routing** (en backend):
```python
AGENT_ROUTING = {
    'implement': 'backend-dev',
    'test': 'qa-engineer',
    'review': 'code-reviewer',
    'docs': 'doc-expert',
    'security': 'compliance-officer',
    'architecture': 'dev-architect',
    'database': 'data-architect',
    'deploy': 'devops',
    'ml': 'ai-developer',
    'performance': 'performance-analyst',
    'fraud-rules': 'fraud-domain-expert',
}
```

- El planner sugiere agentes, pero el usuario puede override
- Basado en keywords del step + historial de éxito (Fase 7)

### 5.4 Execution Engine

El motor que ejecuta el pipeline respetando dependencias.

**Backend** — Nuevo módulo `engine/pipeline_executor.py`:
```
PipelineExecutor:
  1. Cargar pipeline con steps y dependencias
  2. Construir DAG (directed acyclic graph)
  3. Loop:
     a. Encontrar steps "ready" (deps completadas, status pending)
     b. Lanzar todos los ready en paralelo (cada uno = CliRunner session)
     c. Esperar que al menos uno termine
     d. Actualizar estado del step
     e. Si falló → marcar pipeline como needs_review (ver Fase 6)
     f. Si completó → extraer output_summary, pasar a steps dependientes
     g. Repetir hasta que todos los steps terminen o fallen
  4. Calcular totales (cost, tokens, duration)
```

- Cada step ejecuta `CliRunner` con el agent/skill/model asignado
- El prompt del step puede incluir `{{prev_output}}` que se reemplaza con el summary del step anterior
- SSE stream del pipeline entero (evento nuevo: `PipelineStepStarted`, `PipelineStepCompleted`)
- Límite configurable de paralelismo (max N sesiones simultáneas)

### 5.5 Pipeline UI

**Nueva página**: `/pipelines`

**Vista lista**: pipelines con status, cost, duración
**Vista detalle**: `/pipelines/{id}`

Layout del pipeline detail:
```
┌─────────────────────────────────────────────────────┐
│  Pipeline: "Sprint 3 - Velocity Module"             │
│  Status: Running  ●●●○○ (3/5 steps)   Cost: $0.45  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────┐   ┌──────────┐                        │
│  │ 1. Spec  │──→│ 2. Arch  │──┐                     │
│  │ @doc     │   │ @dev-arch│  │                      │
│  │ ✅ Done  │   │ ✅ Done  │  │  ┌──────────┐       │
│  └──────────┘   └──────────┘  ├─→│ 4. Tests │       │
│                               │  │ @qa      │       │
│  ┌──────────┐                 │  │ ⏳ Wait  │       │
│  │ 3. Impl  │─────────────────┘  └──────────┘       │
│  │ @backend │                         │              │
│  │ 🔄 Run   │                         ▼              │
│  └──────────┘                    ┌──────────┐       │
│                                  │ 5. Review│       │
│                                  │ @reviewer│       │
│                                  │ ○ Pending│       │
│                                  └──────────┘       │
│                                                     │
├─────────────────────────────────────────────────────┤
│  Step 3 Output (streaming):                         │
│  ┌─────────────────────────────────────────────┐    │
│  │ Implementando velocity service...            │    │
│  │ ```python                                    │    │
│  │ class VelocityService:                       │    │
│  │     ...                                      │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

**Componentes**:
- `PipelineGraph.svelte` — DAG visual con nodos y flechas (SVG)
- `StepNode.svelte` — Nodo individual con status, agent badge, cost
- `StepDetail.svelte` — Panel lateral con output streaming del step seleccionado
- `PipelineControls.svelte` — Play, pause, cancel, retry failed

---

## Fase 6: Evaluator & Human-in-the-Loop

> **Objetivo**: El pipeline no es fire-and-forget. Un evaluator revisa cada paso y el usuario puede intervenir.

### 6.1 Evaluator Agent

Después de cada step, un agente evaluador revisa el output.

**Implementación**:
- Nuevo agent template `evaluator.md` en el workspace
- Se ejecuta automáticamente post-step con prompt:
  ```
  Evaluate the output of step "{step_name}" ({agent}).
  Original task: {step_description}
  Output: {step_output_summary}

  Respond with JSON: { "passed": bool, "score": 0-10, "issues": [...], "suggestion": "..." }
  ```
- Score < 6 → marca step como `needs_review`
- Score >= 6 → auto-approve y continuar

**Configuración por pipeline**:
- `auto_evaluate`: true/false (default true)
- `min_score`: threshold para auto-approve (default 6)
- `evaluate_model`: qué modelo usar para evaluar (default haiku — barato y rápido)

### 6.2 Approval Workflow

**Tres modos**:
1. **Full auto** — evaluator decide, pipeline avanza solo
2. **Gate on failure** — auto-approve si pasa, pausa si falla (default)
3. **Manual** — pausa después de cada step, requiere click para continuar

**Frontend**:
- Step en `needs_review` muestra botones: Approve / Retry / Skip / Edit prompt
- Retry re-ejecuta el step con el mismo o diferente agent
- Edit prompt permite modificar el prompt antes de re-ejecutar
- Notificación toast cuando un step necesita review

### 6.3 Context Passing

Output de un step como input del siguiente.

**Mecanismo**:
- Al completar un step, el executor genera un `output_summary` (primeros 2000 chars o el evaluator summary)
- Steps dependientes reciben este summary via `{{prev_output}}` en su prompt template
- También pueden acceder a `{{step.N.output}}` para referir a steps específicos
- Artifacts (diffs, file lists) también disponibles como contexto

### 6.4 Mid-Execution Intervention

Permitir al usuario intervenir mientras el pipeline corre.

- **Pause pipeline** — no lanza nuevos steps, espera a que los running terminen
- **Cancel step** — cancela un step específico sin matar el pipeline
- **Inject context** — agrega texto adicional al prompt de un step pendiente
- **Re-prioritize** — cambiar orden de steps pendientes
- **Add step** — insertar un step nuevo en el pipeline en ejecución

---

## Fase 7: Intelligence & Metrics

> **Objetivo**: Aprender del uso, optimizar costos, recomendar mejores prácticas.

### 7.1 Pipeline Metrics

**Nuevos analytics**:
- Cost per pipeline (total, by agent, by step)
- Pipeline success rate (% completed vs failed)
- Average duration by pipeline type
- Steps que más fallan (hotspots)
- Cost trend de pipelines vs sesiones individuales

**Dashboard expansion**:
- Row nueva en `/dashboard` con pipeline stats
- Pipeline-specific dashboard `/pipelines/analytics`

### 7.2 Agent Performance

Trackear qué tan bien funciona cada agente.

**Métricas por agente**:
- Success rate (pasos completados vs fallidos)
- Average evaluator score
- Average cost per invocation
- Average tokens (efficiency)
- Most common failure reasons

**Backend**: Nueva tabla `agent_metrics` (aggregated daily)

### 7.3 Smart Recommendations

Basado en historial, sugerir optimizaciones:
- "El backend-dev tiene 95% success rate con Sonnet — no necesitás Opus para implementación"
- "El code-reviewer falla 40% en steps de ML — considerá usar ai-architect"
- "Este tipo de pipeline te cuesta en promedio $2.50 — presupuesto sugerido: $3"

### 7.4 Cost Budgets & Alerts

- Budget por pipeline (hard limit o warning)
- Budget por workspace (mensual)
- Alerta cuando un step individual supera X costo
- Toast notification en real-time cuando se acerca al límite

### 7.5 Export & Reporting

- Exportar pipeline como markdown (spec + resultados)
- Exportar a GitHub: crear issues automáticamente desde steps fallidos
- Weekly report: resumen de pipelines, costos, recomendaciones

---

## Resumen del Roadmap

```
Fase 4: Integration & Visibility     ← VER y CONECTAR
  4.1 GitHub integration (milestones, issues, PRs)
  4.2 Diff viewer (qué cambió cada sesión)
  4.3 Session artifacts & context sharing
  4.4 MCP registry

Fase 5: Pipeline Engine               ← ORQUESTAR
  5.1 Pipeline data model (DAG)
  5.2 Plan builder (desde milestone o spec)
  5.3 Agent router (asignación inteligente)
  5.4 Execution engine (paralelo + secuencial)
  5.5 Pipeline UI (DAG visual + streaming)

Fase 6: Evaluator & Human-in-the-Loop ← EVALUAR e INTERVENIR
  6.1 Evaluator agent (auto-review post-step)
  6.2 Approval workflow (auto/gate/manual)
  6.3 Context passing (output → input)
  6.4 Mid-execution intervention

Fase 7: Intelligence & Metrics        ← APRENDER y OPTIMIZAR
  7.1 Pipeline metrics
  7.2 Agent performance tracking
  7.3 Smart recommendations
  7.4 Cost budgets & alerts
  7.5 Export & reporting
```

## Diferenciadores vs Terminal

| Capacidad | Terminal | DCC (Fase 7) |
|-----------|---------|-------------|
| Ejecutar Claude | 1 sesión a la vez | N sesiones paralelas |
| Ver output | Texto plano | Markdown + syntax highlighting |
| Coordinar agentes | Manual, copy-paste | DAG automático con dependencias |
| Evaluar resultados | Lectura manual | Evaluator agent + scoring |
| Ver cambios | git diff manual | Diff viewer integrado |
| Costos | No tracking | Dashboard, budgets, alertas |
| GitHub | Cambiar a browser | Integrado (issues → pipeline → PR) |
| Historial | Scroll back | Búsqueda, replay, artifacts |
| Intervenir | Ctrl+C y re-start | Pause, retry, inject, re-route |
| Aprender | Memoria personal | Métricas por agente, recommendations |
