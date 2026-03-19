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
| 7 | **AGENT/TOOL** | `AgentService`: `run()` (batch) + `astream()` (streaming), both modes. Tools: `document_retrieval` (`ContentRetrieverTool`) and `web_research` (`WebResearchTool` via `SkillLoader`) | Tool execution via `create_agent()` (Phase 2.3) |
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
| **2.1** | File UI | File upload component, approval dialog | ✅ Done |
| **2.2** | File Processing | Docling pipeline (PDF/DOCX → structured text), file handling in state | ✅ Done |
| **2.3** | Agent Service + debug logging | `AgentGraph` with compile-time tool binding, `ToolNode`, debug logging throughout | ✅ Done |
| **2.3d** | AsyncSqliteSaver | `AsyncSqliteSaver` checkpointer for cross-restart conversation persistence | ✅ Done |
| **2.4** | ContentRetriever Tool | `ContentRetrieverTool` wrapping `DocumentContextGraph`; `SemanticRetriever` shared pipeline; multi-turn document caching | ✅ Done |
| **2.5** | Web Research Skills | Hierarchical skill routing via `SKILLS.md`; `WebResearchGraph`; `FirecrawlClient`; `SkillLoader`; graceful degradation when API key absent | ✅ Done |
| **2.6+** | Middleware | PII redaction, summarization, human-in-the-loop; then custom memory/tracking | — |

### Phase 3: Auth, PWA & Production

| Phase | Name | Key deliverable | Pre-built infra |
|-------|------|-----------------|-----------------|
| **3.0** | User Authentication | HF OAuth, session management, user profiles | `auth_service.py` |
| **3.1** | PWA + Settings | PWA manifest, settings page, user settings persistence | `user_settings_service.py` |
| **3.2** | Production Hardening | Rate limiting, error boundaries, monitoring, concurrency | — |

**Migration path:** `AgentService.run()` / `astream()` replace the retired `SimpleChatWorkflow`.
`create_agent()` (LangChain v1) is introduced in Phase 2.3 when tools arrive — feature-flagged until stable.

---

## Hierarchical Skill Routing

Introduced in Phase 2.5. Governs how web research capability is discovered, routed, and executed without polluting the main conversation state.

### Two-tier routing

```
Agent (LangGraph StateGraph)
  └── picks domain tool (coarse)       ← tool description from SKILLS.md frontmatter
        └── WebResearchGraph (subgraph)
              └── match_skill_node (fine-grained)  ← reads skills catalog from subgraph state
                    └── dispatches: scrape | search | crawl | extract
```

The agent sees only the top-level tool description written in the SKILLS.md frontmatter. The sub-skill catalog (the markdown body) is injected into `WebResearchState` by `load_skills_node` and is never visible in `MessagesState`.

### SKILLS.md as a routing artifact

Each skill domain lives in its own directory under `skills/` and contains a single `SKILLS.md` file:

```
skills/
├── shared/                    # loaded for all modes
│   └── web_research/
│       └── SKILLS.md
└── {mode}/                    # loaded for this mode only; overrides shared on name clash
    └── ...
```

The file has YAML frontmatter followed by the sub-skill catalog body:

```
---
name: web_research
description: "Tool description the agent sees in its tool list."
---

## scrape
...

## search
...
```

`SkillLoader` parses this structure. The `description` field becomes the `BaseTool.description` the agent reasons over. The body is stored in `SkillDefinition.skills_catalog` and flows only into subgraph state.

### Context isolation guarantee

Raw web content, chunk embeddings, and `matched_skill` all live exclusively in `WebResearchState`. Only the final synthesized answer string is returned as a `ToolMessage` to `MessagesState`. The agent never sees URLs, raw markdown, or embedding vectors.

```
MessagesState  ←──── synthesized answer (str)
                           |
                    WebResearchState
                    ├── skills_catalog
                    ├── matched_skill
                    ├── chunks
                    ├── chunk_embeddings
                    └── answer
```

This is the same isolation contract established by `DocumentContextGraph` in Phase 2.4.

### Multi-turn caching

`WebResearchGraph` maintains two module-level dicts keyed by `(conversation_id, cache_key)`:

| Cache | Key | Skips |
|-------|-----|-------|
| `_web_chunk_cache` | URL (scrape/crawl/extract) or query string (search) | Firecrawl API call + chunking |
| `_web_embedding_cache` | same as above | `all-MiniLM-L6-v2` re-embedding |

On a cache hit, `execute_node` returns stored chunks directly. On a cache hit in `embed_chunks_node`, embedding is skipped. Both checks happen before any I/O. This means follow-up questions on the same URL or query within a conversation are served entirely from memory.

### Graceful degradation

If `FIRECRAWL_API_KEY` is not set, `consolidated_service.py` sets `firecrawl_client=None` and `web_tools=[]`. The agent starts without any web tools. The application runs normally — no startup error, no broken state.

When `firecrawl_client is None`, `execute_node` returns a plain-text message explaining the missing key rather than raising. The synthesis node still runs and returns a coherent answer to the user.

### WebResearchGraph node sequence

```
load_skills → match_skill → execute → embed_chunks → retrieve → END
```

| Node | Responsibility |
|------|---------------|
| `load_skills_node` | Injects `skills_catalog` string into subgraph state |
| `match_skill_node` | LLM call: reads catalog + query + url → returns one of `scrape`, `search`, `crawl`, `extract` |
| `execute_node` | Cache check → Firecrawl dispatch (or stub) → chunk via `SemanticRetriever.chunk_text` |
| `embed_chunks_node` | Cache check → `SemanticRetriever.embed_chunks` (thread pool) |
| `retrieve_node` | Cosine similarity selection → LLM synthesis → returns `answer` |

The graph is compiled without a checkpointer (same as `DocumentContextGraph`). Caching is handled by module-level dicts, not LangGraph persistence.

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

### 6. Tool subgraphs enforce context isolation
`DocumentContextGraph` (Phase 2.4) and `WebResearchGraph` (Phase 2.5) are compiled without checkpointers. Their internal state — chunks, embeddings, matched skills, raw web content — never enters `MessagesState`. Only the synthesized answer string crosses the boundary as a `ToolMessage`.

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
| Semantic retrieval | sentence-transformers (`all-MiniLM-L6-v2`) | Shared embedding pipeline for document retrieval (Phase 2.4) and web content retrieval (Phase 2.5) |
| Web content | Firecrawl (`FirecrawlClient`, async httpx) | Scrape, search, crawl, and extract via Firecrawl REST API; optional — app degrades gracefully without API key |

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
