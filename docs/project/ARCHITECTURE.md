# Architecture: Agent Workbench

**Purpose:** The dot on the horizon. Every design decision — small or large — should map back to something here. If it doesn't fit, question the decision, not the document.

---

## Vision

A **LangGraph-centered dual-mode AI platform** built for two audiences from one codebase:
- **Workbench** — AI developers who need transparent workflow control and model tuning
- **SEO Coach** — Dutch small businesses who need guided AI coaching without technical complexity

The platform evolves in phases: from stable Phase 1 foundations toward full agentic capabilities in Phase 2, while keeping Phase 1 working as the default until Phase 2 is validated.

---

## The 8 Domain Objects

Every feature, service, and API endpoint belongs to one of these. When something doesn't fit, that's a signal.

| # | Object | Current (Phase 1) | Phase 2 Extension |
|---|--------|-------------------|-------------------|
| 1 | **MESSAGE** | `StandardMessage` + `MessageModel` | Structured `AgentResponse` outputs |
| 2 | **CONVERSATION** | CRUD + `ConversationModel` (has `user_id` field already) | Linked to authenticated user |
| 3 | **STATE** | `WorkbenchState` (TypedDict) + `ConversationState` (Pydantic) | Extended with `user_id`, `user_settings` |
| 4 | **WORKFLOW** | `SimpleChatWorkflow` (2-node) + `ConsolidatedWorkbenchService` | 4-node StateGraph + LangChain v1 agent |
| 5 | **CONTEXT** | Placeholder in `ContextService` | Populated from user settings |
| 6 | **USER MODE** | Persona switch via `APP_MODE` env var (`mode_factory_v2.py`) | Full User domain: auth, profiles, settings |
| 7 | **AGENT/TOOL** | Config storage only (`AgentConfigModel`) | Live agent execution via `create_agent()` |
| 8 | **BRIDGE** | `LangGraphStateBridge`: ConversationState ↔ WorkbenchState | Extended with user context loading |

**Source:** `.claude/docs/domain-objects.md` — keep in sync when architecture changes.

---

## Phase 2 Roadmap

Phase 2 releases as **v0.2.0**. All sub-phases build on Phase 1 without breaking it.
LangChain v1 `create_agent()` is alpha — feature-flagged (`ENABLE_LANGCHAIN_V1=true/false`).

### Sub-phases in order (each is a prerequisite for the next)

| Phase | Name | Key deliverable | Pre-built infra |
|-------|------|-----------------|-----------------|
| **2.0** | User Authentication | HF OAuth, session management, user profiles | `auth_service.py` |
| **2.1** | PWA + Settings | PWA manifest, settings page, user settings persistence | `user_settings_service.py` |
| **2.2** | File UI Stubs | File upload component (stub), approval dialog (stub) | — |
| **2.3** | Agent Service + Logging | `create_agent()`, structured outputs, `AgentExecutionLogModel`, `DebugLoggingMiddleware` | `langgraph_service.py`, `workflow_nodes.py` |
| **2.4** | ContentRetriever Tool | LangChain `BaseTool` wrapping Docling document processor | — |
| **2.5** | Built-in Middleware | PII redaction, summarization, human-in-the-loop | — |
| **2.6** | Custom Middleware | Context, memory, execution tracking | — |
| **2.7** | Firecrawl MCP | MCP server connection, Firecrawl adapter | — |
| **2.8** | Production Hardening | Rate limiting, error boundaries, monitoring, concurrency | — |

**Migration path:** Phase 1 workflow remains default. Phase 2 agent runs behind feature flag.
Phase 2.3 makes v1 agent experimental. Full transition only after GA release of LangChain v1.

---

## Critical Architectural Rules

### 1. LangGraph owns conversation state
`WorkbenchState` (TypedDict) is the single source of truth during workflow execution.
LangGraph's `checkpointer` is keyed by `conversation_id`.

### 2. Agent uses ephemeral task-scoped working memory
When calling the Phase 2 LangChain agent, generate a unique `task_id = uuid4()`.
Pass it as the agent's `thread_id`. **Never** use `conversation_id` as the agent's thread.
Agent's internal state (tool calls, reasoning steps) is ephemeral — not persisted to DB.

```
LangGraph StateGraph  →  conversation state  →  persistent  →  keyed by conversation_id
LangChain Agent       →  working memory      →  ephemeral   →  keyed by task_id
```

**Source:** `docs/phase2/state_management_critical_pattern.md`

### 3. Gradio + FastAPI mounting pattern is production-validated
Do not modify `main.py` mounting without explicit approval.
Rules: DB init BEFORE interface creation. `app.mount()` NOT `gr.mount_gradio_app()`.
Both `queue()` and `run_startup_events()` are required.

**Source:** `.claude/docs/gradio-fastapi-pattern.md`

### 4. Phase 2 services are pre-built infrastructure, not dead code
`auth_service.py`, `user_settings_service.py`, `langgraph_service.py`, `workflow_nodes.py`
are intentionally unwired until their phase begins. Do not delete them.

### 5. Database protocol abstraction
All DB access through `AdaptiveDatabase` → `DatabaseBackend` protocol.
Phase 2 adds user methods to the protocol. SQLiteBackend implements them first; HubBackend follows.

---

## Technology Choices

| Layer | Choice | Why |
|-------|--------|-----|
| Workflow engine | LangGraph StateGraph | TypedDict state, conditional routing, checkpointing |
| Agent framework | LangChain v1 `create_agent()` | Standardized API, built-in middleware, MCP adapters |
| Backend | FastAPI (async) | Lightweight, Pydantic integration, OpenAPI docs |
| UI | Gradio (mounted on FastAPI) | Rapid UI, mode-specific config, no JS framework needed |
| Database | SQLite + SQLAlchemy async | Zero-ops local; Hub DB for HF Spaces |
| Package manager | uv | Fast, lockfile-based, replaces pip/poetry |
| LLM providers | OpenRouter, Ollama, Anthropic, OpenAI | Via LangChain ChatModels abstraction |

---

## Deployment Topology

```
Local dev:     APP_MODE=workbench  →  http://localhost:8000/
SEO Coach:     APP_MODE=seo_coach  →  same binary, different UI + config
HF Spaces:     SPACE_ID detected   →  HubBackend for DB, docker sdk
Docker:        make docker-dev / docker-staging / docker-prod
```

---

## What Phase 2 Does NOT Include

- Multi-agent coordination (Phase 3+)
- Visual workflow builder
- Enterprise multi-tenancy
- Kubernetes deployment
- Custom model fine-tuning
