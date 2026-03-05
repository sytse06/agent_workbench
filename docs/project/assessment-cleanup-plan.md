# Cleanup Plan

**Branch:** feature/backend-cleanup-plan
**Date:** 2026-03-05
**Inputs:** All 4 assessments (FastAPI+DB, LangChain+Pydantic, Gradio, Tests)

---

## Principles

1. Every PR results in working software (at minimum: `make pre-commit` passes, app starts locally)
2. Delete before refactoring — remove dead code first, then improve what remains
3. Tests and linting first — establish clean baseline before structural changes
4. Small, focused PRs — one concern per PR, easy to review and revert

---

## Sequenced PR Plan

### Phase 1: Clean Baseline (quality gate + tests)

These PRs establish a clean quality baseline. No functional changes, just removing noise so that subsequent PRs are easier to review and verify.

#### PR-01: Fix E501 and enforce full ruff compliance

**What:** Fix 27 E501 violations (all in 3 UI files: mode_factory_v2.py, chat.py, sidebar.py). Most are inline JS console.log statements and long HTML strings. Shorten comments, break strings, or move debug logs to a separate block.

**Why:** After this, `make quality` passes without `--ignore E501`. Removes the need for the workaround.

**Files:** `ui/mode_factory_v2.py`, `ui/pages/chat.py`, `ui/components/sidebar.py`

**Verify:** `uv run ruff check src/ tests/` passes clean. `make pre-commit` passes.

---

#### PR-02: Rationalize test suite — delete dead and stub tests

**What:** Delete 11 test files (~137 tests) that cover dead code or are pure stubs. Fix or delete the 12 failing tests (sidebar + auth). Result: 0 failures, ~320 real tests, all passing.

**Why:** Stop testing code that doesn't run. Get to a green baseline where every test that passes actually validates something.

**Delete:**
- `tests/ui/test_mode_factory.py` (tests dead mode_factory.py)
- `tests/ui/test_seo_coach_interface.py` (tests dead seo_coach_app.py)
- `tests/ui/test_ui_integration.py` (18 stubs)
- `tests/ui/test_sidebar.py` (6 failing, outdated)
- `tests/ui/test_sidebar_phase3.py` (5 failing, duplicate)
- `tests/integration/test_langgraph_workflows.py` (13 stubs)
- `tests/integration/test_auth_flow.py` (1 failing, dead auth)
- `tests/integration/test_user_isolation.py` (tests dead auth)
- `tests/integration/test_conversation_loading.py` (tests dead context)
- `tests/unit/test_service_integration.py` (12 stubs)
- `tests/unit/api/routes/test_chat.py` (4 skipped, deprecated)

**Verify:** `make test` — 0 failures, ~320 passing. `make pre-commit` passes.

---

#### PR-03: Add smoke tests and restructure Makefile test targets

**What:** Add 4-6 regression/smoke tests that verify the app starts and core endpoints work. Add `make test-smoke` target. Update `make pre-commit` to run `quality-check + test-smoke + test-unit-only` (fast).

**Smoke tests:**
- App creates without error
- GET /health returns 200
- POST /chat/workflow accepts request
- Gradio interface mounts correctly

**Why:** Fast, reliable quality gate. Catches actual breakage before anything else runs.

**Verify:** `make test-smoke` passes in <5s. `make pre-commit` passes.

---

### Phase 2: Dead Code Removal (delete before refactoring)

Each PR deletes one category of dead code. Order matters — tests deleted first (PR-02), then the code they tested.

#### PR-04: Delete dead UI files

**What:** Delete dead UI factories and orphaned components.

**Delete:**
- `src/agent_workbench/ui/app.py` (368 lines, dead)
- `src/agent_workbench/ui/seo_coach_app.py` (455 lines, dead)
- `src/agent_workbench/ui/mode_factory.py` (225 lines, replaced by v2)
- `src/agent_workbench/ui/components/chat.py` (20 lines, never called)
- `src/agent_workbench/ui/components/settings.py` (unused)
- `src/agent_workbench/ui/components/error_handling.py` (unused)
- `src/agent_workbench/ui/components/simple_client.py` (unused)

**Verify:** `make start-app` works. `make pre-commit` passes.

---

#### PR-05: Delete dead routes and their tests

**What:** Delete API routes that are never called from the UI.

**Delete:**
- `src/agent_workbench/api/routes/context.py` (not even registered in main.py)
- `src/agent_workbench/api/routes/conversations.py` (unused CRUD)
- `src/agent_workbench/api/routes/messages.py` (conflicts with workflow)
- `src/agent_workbench/api/routes/files.py` (security issue + HF incompatible)
- Remove router registrations from main.py
- Delete remaining tests for these routes

**Also:** Remove duplicate `/consolidated/state/` endpoint from chat_workflow.py.

**Verify:** `make start-app` works. Health and chat endpoints still respond. `make pre-commit` passes.

---

#### PR-06: Delete dead services and main.py bloat

**What:** Remove dead service files and ~565 lines of dead code from main.py.

**Delete:**
- `src/agent_workbench/services/langgraph_service.py` (15KB, never instantiated)
- `src/agent_workbench/services/workflow_nodes.py` (7KB, only ref'd by dead service)
- `src/agent_workbench/services/auth_service.py` (Phase 2, not wired)
- `src/agent_workbench/services/user_settings_service.py` (Phase 2, not wired)
- main.py: dead fallback interfaces (lines 598-978)
- main.py: dead message handler (lines 981-1103)
- main.py: dead dependency injection (lines 538-589)

**Verify:** `make start-app` works. `make pre-commit` passes.

---

#### PR-07: Delete dead Pydantic models and aliases

**What:** Remove model shadowing and backward-compat aliases.

**Delete from consolidated_state.py:**
- `ConversationResponse` (line 359, shadows api_models)
- `CreateConversationRequest` (line 350, shadows api_models)
- `ContextUpdateRequest` (line 342, duplicate)

**Delete from schemas.py:**
- All 15 backward-compat aliases (ConversationBase, MessageCreate, etc.)
- Duplicate `ConversationSummary`

**Delete from providers.py:**
- Provider ABC classes (lines 296-454, ~160 lines)

**Verify:** `make pre-commit` passes. No import errors.

---

### Phase 3: Structural Improvements (refactor what remains)

After dead code is gone, the codebase is lean enough to make targeted improvements.

#### PR-08: Fix known bugs

**What:** Fix all bugs identified across assessments.

**Fixes:**
- `response.reply` -> `response.message` in simple_chat.py:204 and main.py:579
- Remove `await` from `session.delete()` in MessageModel
- Replace debug `print()` with `logging.debug()` in mode_factory_v2.py
- Remove `type="messages"` from Chatbot calls (Gradio 6 prep)

**Verify:** `make pre-commit` passes. `/chat/test-model` endpoint doesn't crash.

---

#### PR-09: Externalize inline JavaScript

**What:** Move 246-line JavaScript from mode_factory_v2.py Python string to `static/js/ui-init.js`. Replace hard-coded component IDs with `elem_id=` selectors. Move mobile layout fixes to CSS `@media` queries.

**Why:** Testable JS, IDE support, stable selectors, most E501 violations disappear permanently.

**Verify:** App starts, sidebar toggle works, mobile layout works. `make pre-commit` passes.

---

#### PR-10: Strip custom CSS to Gradio-native styling

**What:** Delete `agent-workbench-design.css` (duplicates tokens.css). Reduce `styles.css` from ~400 lines to ~100 by using `gr.themes.Base()` for colors/fonts/spacing. Keep only layout CSS that Gradio's theme system can't control.

**Why:** Makes Gradio updates safe. Removes `!important` overrides. Simpler maintenance.

**Verify:** App looks correct. Dark mode works. `make pre-commit` passes.

---

#### PR-11: Add critical missing tests

**What:** Add tests for untested production path components.

**New test files:**
- `tests/unit/services/test_bridge.py` — LangGraphStateBridge state round-trip
- `tests/unit/services/test_workflow_orchestrator.py` — main workflow
- `tests/unit/services/test_mode_handlers.py` — workbench vs seo_coach
- `tests/unit/services/test_state_manager.py` — state persistence

**Update conftest.py:**
- Add `workflow_state_factory` fixture
- Add `mock_llm_provider` fixture
- Configure coverage threshold (`--cov-fail-under=60`)

**Verify:** `make test` — all pass with ≥60% coverage on production path.

---

### Phase 4: Design Decisions (address when ready)

These are not PRs yet — they need discussion first.

| # | Decision | Options | Depends On |
|---|----------|---------|-----------|
| D1 | Messages table | Normalize messages into it, or delete it? | PR-05 |
| D2 | AdaptiveDatabase | Add real adapter logic, or replace with factory? | PR-06 |
| D3 | Hub backend stubs | Implement properly, or mark HF Spaces read-only? | D1 |
| D4 | ContextService | Implement properly, or remove entirely? | PR-06 |
| D5 | Pydantic-LangChain symbiosis | ModelConfig.to_chat_model(), LangChain messages as storage format | PR-07 |
| D6 | WorkbenchState | Switch from TypedDict to Pydantic model? | D5 |
| D7 | PWA | Wire service worker registration, or defer/remove? | PR-09 |
| D8 | Streaming | Implement stream_workflow(), or document as future? | D4 |
| D9 | State pipeline | One format instead of three? | D5, D6 |
| D10 | Field naming | Standardize conversation_id vs id across all models? | PR-07 |
| D11 | DB schema naming | Rename ConversationSchema -> ConversationDB? | PR-07 |
| D12 | SEO Coach components | Keep dutch_messages.py + business_profile_form.py? | PR-04 |

---

## Sequencing Rationale

```
PR-01 (E501)          ──┐
PR-02 (dead tests)    ──┤── Phase 1: Clean baseline
PR-03 (smoke tests)   ──┘
                         │
PR-04 (dead UI)       ──┐
PR-05 (dead routes)   ──┤── Phase 2: Delete dead code
PR-06 (dead services) ──┤   (each PR removes one category)
PR-07 (dead models)   ──┘
                         │
PR-08 (bug fixes)     ──┐
PR-09 (externalize JS)──┤── Phase 3: Improve what remains
PR-10 (strip CSS)     ──┤
PR-11 (add tests)     ──┘
                         │
D1-D12                ──── Phase 4: Design decisions (discuss first)
```

**Why this order:**
1. **E501 first** — your request, quick win, makes ruff fully enforced
2. **Tests second** — stop testing dead code before deleting it
3. **Smoke tests third** — safety net before structural changes
4. **Dead code deletion** — UI first (biggest volume), then routes, then services, then models
5. **Bug fixes after deletion** — some bugs are in dead code (no point fixing then deleting)
6. **JS/CSS after deletion** — cleaner files to work with
7. **New tests last** — test what survived the cleanup, not what was deleted

---

## Estimated Effort

| Phase | PRs | Estimated Time |
|-------|-----|---------------|
| Phase 1 (baseline) | 3 | 2-3 hours |
| Phase 2 (delete) | 4 | 2-3 hours |
| Phase 3 (improve) | 4 | 6-8 hours |
| Phase 4 (decisions) | TBD | Discussion first |
| **Total** | **11 PRs** | **10-14 hours** |
