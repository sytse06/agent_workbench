# Backlog

Items move from Later to Next to Now. Each "Now" item becomes a feature branch and a PR.

## Now — Phase 2: Dead Code Removal

- [ ] PR-04: Delete dead UI files (app.py, seo_coach_app.py, mode_factory.py, orphaned components)
- [ ] PR-05: Delete dead routes (context.py, conversations.py, messages.py, files.py)
- [ ] PR-06: Delete dead services + main.py bloat (langgraph_service, workflow_nodes, ~565 lines main.py)
- [ ] PR-07: Delete dead Pydantic models and aliases (6 shadows, 15 aliases, provider ABCs)

## Next — Phase 3: Structural Improvements

- [ ] PR-08: Fix known bugs (response.reply, await delete, debug prints, Gradio 6 prep)
- [ ] PR-09: Externalize inline JavaScript (246 lines) + stable elem_id selectors
- [ ] PR-10: Strip custom CSS to Gradio-native styling (~800 -> ~100 lines)
- [ ] PR-11: Add critical missing tests (bridge, orchestrator, mode handlers, state manager)

## Later — Design Decisions (discuss before implementing)

- [ ] Messages table: normalize into it or delete it?
- [ ] AdaptiveDatabase: add real adapter logic or replace with factory?
- [ ] Hub backend stubs: implement properly or mark HF Spaces read-only?
- [ ] ContextService: implement properly or remove entirely?
- [ ] Pydantic-LangChain symbiosis: ModelConfig.to_chat_model(), LangChain messages as storage
- [ ] WorkbenchState: switch from TypedDict to Pydantic model?
- [ ] PWA: wire service worker registration or defer/remove?
- [ ] State pipeline: one format instead of three?

## Later — Features

- [ ] MCP tool integration (Firecrawl for SEO analysis)
- [ ] SEO Coach production deployment to HuggingFace Spaces
- [ ] Multi-agent coordination via LangGraph
- [ ] Agent memory and learning
- [ ] File upload handling in chat interface
- [ ] Streaming support (stream_workflow)

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
