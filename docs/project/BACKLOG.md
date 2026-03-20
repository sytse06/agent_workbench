# Backlog

Items move from Later to Next to Now. Each "Now" item becomes a feature branch and a PR.

See `docs/project/ARCHITECTURE.md` for the dot on the horizon.

---

## Now — Cleanup Phase 2: Dead Code Removal (in progress)

- [x] PR-04: Delete dead UI files (app.py, seo_coach_app.py, mode_factory.py v1, orphaned components)
- [x] PR-05: Delete dead routes (context.py, conversations.py, messages.py, files.py)
- [x] PR-06: main.py bloat removal + test quality fixes
  - Removed ~470 lines of dead fallback interfaces and DI functions from main.py
  - Fixed SQLAlchemy `declarative_base` deprecation warning (database.py)
  - Fixed `AsyncMock` / real DB engine leaking in unit tests
  - NOTE: `auth_service`, `user_settings_service`, `langgraph_service`, `workflow_nodes`
    were restored — they are Phase 2 pre-built infrastructure, not dead code
- [x] PR-07: Dead Pydantic models + aliases
  - Deleted 12 backward-compat aliases from `schemas.py` (Conversation×5, Message×5, AgentConfig×2)
  - Deleted 2 unused shadow models from `consolidated_state.py` (CreateConversationRequest, ConversationResponse)
  - Kept `ContextUpdateRequest` in `consolidated_state.py` — actively imported by `chat_workflow.py`
    (plan assumed unused; grep proved otherwise — follow-up PR should redirect import to `api_models.py`)
  - Provider ABCs in `providers.py` (~160 lines): confirmed used at runtime via `PROVIDER_FACTORIES`
    in `simple_chat.py`; deferred to later PR

---

## Next — Cleanup Phase 3: Structural Improvements

- [x] PR-08: Fix known bugs (response.reply, await delete, debug prints)
  - `response.reply` → `response.message` in simple_chat.py
  - `api_key_source` initialized before try block (removes fragile `locals()` check)
  - `await session.delete()` — assessment was wrong; SQLAlchemy 2.0 AsyncSession.delete() IS async; `await` kept
  - Debug `print()` → `logger.debug()` in chat.py and mode_factory_v2.py
  - NOTE: `type="messages"` removal deferred — project pinned to Gradio <6.0.0; belongs in Gradio 6 upgrade PR
- [x] PR-08b: Gradio 6 upgrade — bump `gradio>=6.0.0`, remove `type="messages"`, adopt `gr.ChatMessage`, `MessageConverter`, `response_metadata` passthrough, Pydantic/LangChain boundary fixes
- [x] PR-08c: LangChain v1 + LangGraph v1 upgrade — bump core packages, remove dead `langchain-community` dependency, verify breaking changes; positions codebase for Phase 2 `create_agent` + middleware
- [x] PR-09: Externalize inline JavaScript (246 lines) + stable elem_id selectors
  - Extracted 246-line JS block → static/js/ui-init.js (IIFE, SEO Coach only)
  - Added elem_id= to layout components (aw-main, aw-top-bar, aw-input-bar)
  - Replaced all #component-N selectors in JS with named IDs
  - Workbench: load_custom_js=False (zero JS loaded)
- [x] PR-10: CSS conditional loading + cleanup (-1,229 lines deleted)
  - Deleted agent-workbench-design.css (766 lines, exact duplicate of tokens.css)
  - Deleted fonts.css (206 lines, replaced by gr.themes.GoogleFont())
  - Deleted main.css (12 lines, replaced by Python-side _load_css())
  - Trimmed styles.css: 1,152 → ~450 lines (removed #component-N, font-family overrides)
  - Workbench: css=None, show_conv_browser=False, gr.themes.GoogleFont("Roboto")
  - SEO Coach: full CSS stack loaded via _load_css(), gr.themes.GoogleFont("Open Sans")
- [ ] PR-11: Add critical missing tests (bridge, orchestrator, mode handlers, state manager)

---

## Next — Phase 2 Feature Implementation

Sub-phases must be implemented in order — each is a prerequisite for the next.
Reference: `docs/phase2/phase2_architecture_plan.md`, `docs/project/ARCHITECTURE.md`

Auth, PWA, and user management are deferred to Phase 3 — orthogonal to agent
functionality and would delay the core agent work.

- [x] Phase 2.0: Agent core (PR-20)
  - `AgentService` with `run()` + `astream()`, extended thinking blocks, SSE streaming
  - `ConsolidatedWorkbenchService` orchestrator, mode handlers, LangGraph bridge
- [x] Phase 2.1: File UI (PR-21)
  - `MultimodalTextbox`, drag-and-drop, approval bar
- [x] Phase 2.2: File processing (PR-22)
  - Docling → chunks → DB → SystemMessage context injection
  - Multi-file support, `documents` + `document_chunks` tables
- [x] Phase 2.2b: Standard content blocks + Gradio mapping layer (PR-22b)
  - `agent_service.py`: replace manual block parsing with `chunk.content_blocks`
  - `message_converter.py`: `_BLOCK_LABELS` symbol registry + `streaming_event_to_chat_messages()`
  - `chat.py`: remove duplicated `gr.ChatMessage` construction from both handlers
  - `<think>` tag parsing for Ollama/Qwen3 reasoning models
- [x] Phase 2.3: LangGraph ReAct agent sub-graph (PR-23)
  - Inner `AgentGraph` with `MessagesState`, `llm_node`, `ToolNode`, conditional back-edge
  - Outer `WorkbenchState` pipeline unchanged — clean separation of concerns
  - Runs `tools=[]` in this PR (identical behaviour); tool-ready for PR-2.4
- [x] Phase 2.3b: LangGraph v2 streaming + LangGraph 1.1 bump (PR-23b)
  - Bump `langgraph>=1.1.0`; adopt native `stream_mode=["messages","custom"]` with `version="v2"`
  - `AgentGraph.astream_events()` → `astream()` — yields typed `StreamPart` dicts
  - `consolidated_service.py` dispatches on `chunk["type"]` instead of LangChain event bus
  - `"custom"` mode pre-wired; `get_stream_writer()` calls from nodes/tools flow through automatically (PR-2.4+)
- [x] Phase 2.3c: Native LangGraph Infrastructure (PR-23c)
  - `MemorySaver` checkpointer wired into `AgentGraph` (module-level singleton → persists across requests)
  - `AgentGraph.ainvoke()` / `astream()` accept `thread_id` → keyed by `conversation_id`
  - `consolidated_service.py` passes `thread_id`; avoids message duplication via `get_state()` check
  - `langgraph-checkpoint-sqlite>=3.0.3` added to deps (swap `MemorySaver` → `AsyncSqliteSaver` for cross-restart persistence — PR-2.6a concern)
  - NOTE: `@task(mode="exit/async")` dropped — those params don't exist; StateGraph checkpointer provides equivalent durability automatically
  - `LangGraphStateBridge` simplification deferred (complex interaction with history injection; tackle in PR-2.6a)
- [x] Phase 2.3d: AsyncSqliteSaver for cross-restart checkpointer persistence
  - `init_checkpointer(db_path)` / `close_checkpointer()` wired into FastAPI lifespan
  - Default path `data/langgraph_checkpoints.db`, overridable via `LANGGRAPH_CHECKPOINT_DB`
  - Falls back to `MemorySaver` on init failure (graceful degradation)
  - Deferred: `@task` for `llm_node` — zero benefit until tool loops exist (PR-2.4+); tools aren't serializable so `@task` can't bind tools anyway
  - Deferred: `FileProcessingService` in `@task` — not inside a graph context; needs `@entrypoint` restructuring
  - Deferred: `LangGraphStateBridge` simplification — PR-2.6a design concern (checkpointer + UI history coexist)
- [x] Phase 2.4: ContentRetriever Tool (PR-24)
  - `ContentRetrieverTool` as first `BaseTool` wired through `AgentGraph`
  - `AgentGraph` compile-once singleton; tools fixed at build time via `tools: list` param
  - `DocumentContextGraph` inner subgraph: load_chunks → embed_chunks → retrieve → synthesize
  - `EmbeddingService` lazy-loads `all-MiniLM-L6-v2`; multi-turn cache via module-level dicts
  - Multi-turn bug fixed: `conversation_id` round-tripped through Gradio `additional_outputs`
  - NOTE: embedding + cosine selection logic is inline in `DocumentContextGraph` —
    to be extracted into shared `SemanticRetriever` in PR-2.5a
- [x] Phase 2.5: WebResearch Skills (PR-25) — see `docs/project/PR-25-webresearch-skills.md`
  - Hierarchical skill routing: one domain tool → subgraph selects skill from `SKILLS.md` catalog
  - PR-2.5a: Extract `SemanticRetriever` from `DocumentContextGraph` (shared retrieval pipeline)
    — refactors ContentRetrieverTool to use it; no behavior change, proven before new code added
  - PR-2.5b: `SkillLoader` + `WebResearchGraph` skeleton (execute_node stubbed, SemanticRetriever wired)
  - PR-2.5c: `FirecrawlClient` (httpx, direct REST API) + wire into `consolidated_service`
  - Multi-turn web cache: `_web_chunk_cache` / `_web_embedding_cache` by (conv_id, url)
  - Graceful degradation: no `FIRECRAWL_API_KEY` → web_research tool disabled, app still works
  - ContentRetrieverTool + WebResearchTool retrofitted into SKILLS.md pattern; routing fix
- [x] Phase 2.6a: Dual persistence removal + thread metadata + listing API (PR-26a)
  - `state_bridge.load_into_langgraph_state()` + `save_turn()` removed from `stream_workflow()`
  - `get_conversation_state()` replaced with direct `agent_graph.get_state()` call
  - `thread_metadata` table created (thread_id, title, preview, created_at, last_updated_at)
  - `_upsert_thread_metadata()` writes row after each turn (non-fatal)
  - Alembic migration `4ea9663c23e2`: creates `thread_metadata` + index
  - `GET /api/v1/threads` endpoint returning `ThreadSummary` list ordered by `last_updated_at DESC`
  - **Deferred**: `documents.conversation_id` → `thread_id` rename + `conversations` table drop
    (SQLite ALTER TABLE limitations; FK is inactive; deferring to follow-up migration in PR-2.6b+)
  - 426 unit tests passing, all quality checks green
- [x] Phase 2.6b: Thread switching + deletion + sidebar UI (PR-26b)
  - `DELETE /api/v1/threads/{id}` — deletes `thread_metadata` row + `documents`; 404 if not found
  - `GET /api/v1/threads/{id}/messages` — reconstructs display history from checkpointer state
  - Workbench sidebar: `gr.State`-backed thread list fetched from `GET /api/v1/threads/`
  - Thread switching via `conv_dataset.select` → async message load; `delete_thread_btn` visible on selection
  - `mode_factory_v2.py`: `isinstance(gr.BrowserState)` branch — API path for workbench, BrowserState for SEO Coach
  - 436 tests passing, all quality checks green
- [x] Phase 2.6c: Context compaction / summarization node (PR-26c)
  - Conditional `compact_node` fires above `COMPACTION_TOKEN_THRESHOLD` (4 000 tokens ≈ 16 000 chars)
  - `RemoveMessage` ops replace old messages; `SystemMessage("[Conversation summary]\n…")` preserved
  - `_should_compact` routing via `add_conditional_edges(START, …)` — compact_node → llm_node
  - `COMPACTION_KEEP_RECENT = 6` messages kept verbatim after compaction
  - 436 tests passing, all quality checks green
- [x] Phase 2.6d: Long-term memory Store (PR-26d)
  - `AsyncSqliteStore` initialized at startup (`data/langgraph_store.db`), namespace `(session_id, "memories")`
  - Session UUID via `gr.BrowserState("aw_session_id")` — generated on first page load, persists in localStorage
  - Memory read before each `AgentGraph.astream()` call; injected as ephemeral `SystemMessage` inside `llm_node` via `AgentContext.memory_context` — never stored in checkpointer
  - `UpdateMemoryTool`: `@tool` using `InjectedStore` + `RunnableConfig` for session_id; wired as `memory` skill domain (workbench only)
  - `GET/PUT /api/v1/memory/{key}` endpoints ready for memory panel UI
  - Phase 3 migration path: swap `session_id` source from BrowserState → authenticated user ID; Store logic unchanged
  - **Deferred**: settings page memory panel UI (API wired, UI not yet built); cross-device memory (blocked on Phase 3 auth); SEO Coach memory wiring
  - 450 tests passing, all quality checks green
- [ ] Phase 2.6e: Middleware
  - Built-in: `interrupt_before=[\"tool_node\"]`, PII redaction
  - Custom: context injection, execution tracking
- [ ] Phase 2.6f: SEO Coach sidebar (follow-up after 2.6b — `show_conv_browser` already feature-flagged)
- [ ] Phase 2.6g: LLM-generated thread titles (later enhancement — no schema change needed, layers on top of 2.6a)

---

## Later — Phase 3: Auth, PWA & Production

Deferred from Phase 2 — implement after agent functionality is stable.

- [ ] Phase 3.0: User Authentication
  - HF OAuth via Gradio `Request`, session management (30-min timeout reuse)
  - Alembic migration: `users`, `user_settings`, `user_sessions` tables
  - Extend `DatabaseBackend` protocol + `AdaptiveDatabase` with user methods
  - Wire `auth_service.py` into Gradio `on_load` event
- [ ] Phase 3.1: PWA + Settings Page
  - `static/manifest.json`, `static/service-worker.js`
  - Wire `user_settings_service.py` into settings page save/load
  - Share target handler (`/share` endpoint)
- [ ] Phase 3.2: Production Hardening (rate limiting, concurrency, monitoring)
- [ ] Phase 3.3: Tool dispatch UX — streaming progress indicators
  - Surface WIP state to the user during multi-step tool use: "searching...", "reading document...", "fetching URL..."
  - `get_stream_writer()` is already pre-wired in `AgentGraph.astream()` via `stream_mode=["messages","custom"]` — ready to use
  - Implement per skill domain when specialized skills ship (coding, data management, etc.) — each domain defines its own progress events
  - Keeps streaming latency transparent; critical UX for long-running tool chains
- [ ] Phase 3.4: Postgres checkpointer + Store migration
  - Swap `AsyncSqliteSaver` → `langgraph-checkpoint-postgres` (required before multi-worker deployment)
  - Swap `AsyncSqliteStore` → `PostgresStore` for long-term memory
  - `AsyncSqliteSaver` is a latent bomb for multi-worker Uvicorn: each worker gets its own SQLite connection
  - Must be planned before memory architecture is locked in; independent of auth but pairs naturally with Phase 3

---

## Later — Security & Environment

- [ ] Review credentials strategy: audit what's in config/*.env, document rationale for gitignore approach, ensure dev/staging/prod secrets are properly separated and not cross-contaminating

---

## Later — Design Decisions (discuss before implementing)

- [ ] Messages table: normalize into it or delete it?
- [ ] AdaptiveDatabase: add real adapter logic or replace with factory?
- [ ] Hub backend stubs: implement properly or mark HF Spaces read-only?
- [ ] ContextService: implement properly or remove entirely?
- [ ] Pydantic-LangChain symbiosis: ModelConfig.to_chat_model(), LangChain messages as storage
- [ ] WorkbenchState: switch from TypedDict to Pydantic model?
- [ ] PWA: wire service worker registration or defer/remove?
- [ ] State pipeline: one format instead of three?
- [ ] Conversation browser sidebar — moved to PR-2.6a Thread Management (revert/delete controls + history view)
- [ ] State pipeline: consolidate to one format instead of three? (WorkbenchState TypedDict → Pydantic?)

---

## Phase 4: Multi-Agent Coordination

Prerequisite: Phase 3 complete (auth + Postgres infrastructure), Phase 2.6d long-term memory Store live.

- [ ] Phase 4.0: Multi-agent orchestration via LangGraph
  - Pattern: main orchestrator agent delegates tasks to an assembly of specialist subagents
  - Each subagent is a compiled `StateGraph` with its own tools and `SKILLS.md` domain
  - Orchestrator routes by intent (e.g. web research → `web_research` subagent, document work → `document_retrieval` subagent, SEO → `seo_coach` subagent)
  - Communication via LangGraph subgraph protocol — subgraph outputs flow back into orchestrator `MessagesState`
  - Shared long-term memory: all agents read/write the same `/memories/agents.md` + `/memories/domain_context.md` via the Store
  - Design decision required: deepagents filesystem metaphor vs. raw `Store` KV — evaluate before implementing
  - Note: deepagents library not a dependency; the self-improving instructions pattern is adoptable independently

---

## Later — Features

- [ ] SEO Coach production deployment to HuggingFace Spaces
- [x] Agent memory and learning — planned in PR-2.6a (short-term via checkpointer, long-term via Store)
- [x] Streaming support — upgraded to LangGraph v2 native streaming in PR-2.3b

---

## Done

- [x] App running locally (make start-app, chat works, conversation history persists)
- [x] Streamlined CLAUDE.md and developer workflow
- [x] Added make pr command and PR guidelines
- [x] Created project docs (BACKLOG, DEPLOYMENT, BUSINESS)
- [x] Cleaned up 28 stale local branches
- [x] Verified HF Spaces deployment (fixed Gradio 6.x crash, switched to sdk:docker)
- [x] Backend assessment 1/3: FastAPI + database
- [x] Backend assessment 2/3: LangChain + Pydantic
- [x] Backend assessment 3/3: Gradio
- [x] Backend assessment: test infrastructure
- [x] Cleanup plan — 11 PRs across 4 phases
- [x] Phase 1: PR-01 E501 fix (27 violations), PR-02 dead tests (466→324), PR-03 smoke tests (6 tests)
- [x] Cleanup Phase 2: PR-04 dead UI files (-3,689 lines), PR-05 dead routes
- [x] Cleanup Phase 3: PR-09 externalize JS + stable elem_ids, PR-10 CSS conditional loading (-1,229 lines CSS deleted)
