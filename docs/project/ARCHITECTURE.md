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

| # | Object | Current (Phase 1 + 2.0) | Phase 2 Extension |
|---|--------|-------------------------|-------------------|
| 1 | **MESSAGE** | `StandardMessage` + `MessageModel` + `AgentResponse` | Richer tool/thinking metadata |
| 2 | **CONVERSATION** | CRUD + `ConversationModel` (has `user_id` field already) | Linked to authenticated user |
| 3 | **STATE** | `WorkbenchState` (TypedDict) + `ConversationState` (Pydantic) | Extended with `user_id`, `user_settings` |
| 4 | **WORKFLOW** | `LangGraphService` (5-node StateGraph, both modes) + `ConsolidatedWorkbenchService` | LangChain v1 `create_agent()` for tool use |
| 5 | **CONTEXT** | Placeholder in `ContextService` | Populated from user settings |
| 6 | **USER MODE** | Persona switch via `APP_MODE` env var (`mode_factory_v2.py`) | Full User domain: auth, profiles, settings |
| 7 | **AGENT/TOOL** | `AgentService`: `run()` (batch) + `astream()` (streaming), both modes | Tool execution via `create_agent()` (Phase 2.3) |
| 8 | **BRIDGE** | `LangGraphStateBridge`: ConversationState ↔ WorkbenchState | Extended with user context loading |

**Source:** `.claude/docs/domain-objects.md` — keep in sync when architecture changes.

---

## Phase 2 Roadmap

Phase 2 releases as **v0.2.0**. All sub-phases build on Phase 1 without breaking it.
Auth, PWA, and user management are deferred to Phase 3 — orthogonal to agent functionality.

### Sub-phases in order (each is a prerequisite for the next)

| Phase | Name | Key deliverable | Status |
|-------|------|-----------------|--------|
| **2.0** | Agent Core | `AgentService` (`run`/`astream`), `LangGraphService` (5-node StateGraph), SSE streaming, multi-turn history wired | ✅ Done |
| **2.1** | File UI | File upload component, approval dialog stub | — |
| **2.2** | File Processing | Docling pipeline (PDF/DOCX/HTML → structured text), file handling in state | — |
| **2.3** | ContentRetriever Tool | LangChain `@tool` wrapping vector store; introduces `create_agent()` | — |
| **2.4** | Firecrawl MCP Tool | Web content retrieval as agent tool via MCP adapter | — |
| **2.5** | Middleware | PII redaction, summarization, human-in-the-loop; then custom memory/tracking | — |

### Phase 3: Auth, PWA & Production

| Phase | Name | Key deliverable | Pre-built infra |
|-------|------|-----------------|-----------------|
| **3.0** | User Authentication | HF OAuth, session management, user profiles | `auth_service.py` |
| **3.1** | PWA + Settings | PWA manifest, settings page, user settings persistence | `user_settings_service.py` |
| **3.2** | Production Hardening | Rate limiting, error boundaries, monitoring, concurrency | — |

**Migration path:** `AgentService.run()` / `astream()` replace the retired `SimpleChatWorkflow`.
`create_agent()` (LangChain v1) is introduced in Phase 2.3 when tools arrive — feature-flagged until stable.

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

### 4. Phase 2/3 services are pre-built infrastructure, not dead code
`auth_service.py` and `user_settings_service.py` are intentionally unwired until Phase 3.
`langgraph_service.py` is now **live** (wired in Phase 2.0). Do not delete any of these.

### 5. Database protocol abstraction
All DB access through `AdaptiveDatabase` → `DatabaseBackend` protocol.
Phase 2 adds user methods to the protocol. SQLiteBackend implements them first; HubBackend follows.

---

## Technology Choices

| Layer | Choice | Why |
|-------|--------|-----|
| Workflow engine | LangGraph StateGraph | TypedDict state, conditional routing, checkpointing |
| Agent execution | `AgentService` (`model.ainvoke` / `model.astream`) → Phase 2.3: LangChain v1 `create_agent()` | Direct LangChain ChatModel now; `create_agent()` when tools arrive |
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
