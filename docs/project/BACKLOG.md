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
- [ ] PR-08b: Gradio 6 upgrade — bump `gradio>=6.0.0`, remove `type="messages"` from gr.Chatbot (chat.py:168)
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

- [ ] Phase 2.0: User Authentication
  - HF OAuth via Gradio `Request`, session management (30-min timeout reuse)
  - Alembic migration: `users`, `user_settings`, `user_sessions` tables
  - Extend `DatabaseBackend` protocol + `AdaptiveDatabase` with user methods
  - Wire `auth_service.py` into Gradio `on_load` event
- [ ] Phase 2.1: PWA + Settings Page
  - `static/manifest.json`, `static/service-worker.js`
  - Wire `user_settings_service.py` into settings page save/load
  - Share target handler (`/share` endpoint)
- [ ] Phase 2.2: File UI Stubs
  - File upload component (stubbed), approval dialog (auto-approve stub)
- [ ] Phase 2.3: Agent Service + Debug Logging
  - LangChain v1 `create_agent()` behind `ENABLE_LANGCHAIN_V1` feature flag
  - Structured `AgentResponse` outputs (Pydantic)
  - `AgentExecutionLogModel`, `ToolCallLogModel`, `DebugLoggingMiddleware`
  - `AnalyticsService` with indexed queries
  - Wire `langgraph_service.py` + `workflow_nodes.py` into 4-node StateGraph
  - CRITICAL: agent uses `task_id` (not `conversation_id`) for working memory
- [ ] Phase 2.4: ContentRetriever Tool (LangChain BaseTool + Docling)
- [ ] Phase 2.5: Built-in Middleware (PII redaction, summarization, human-in-the-loop)
- [ ] Phase 2.6: Custom Middleware (context, memory, execution tracking)
- [ ] Phase 2.7: Firecrawl MCP Tool
- [ ] Phase 2.8: Production Hardening (rate limiting, concurrency, monitoring)

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
- [ ] Conversation browser sidebar (workbench-first, feature-flagged) — see `docs/phase2/Feat-dev-plan-chat-history-in-sidebar-in-chatpage.md`

---

## Later — Features

- [ ] SEO Coach production deployment to HuggingFace Spaces
- [ ] Multi-agent coordination via LangGraph (Phase 3+)
- [ ] Agent memory and learning
- [ ] Streaming support (stream_workflow)

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
