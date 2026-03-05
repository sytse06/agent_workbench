# Assessment: Test Infrastructure & Quality

**Branch:** feature/backend-assessment-test
**Date:** 2026-03-05

---

## Big Picture

The test infrastructure is a mirror of the codebase problem: over-built, under-delivering. 457 test functions across 45 files, but only ~48 test real production code. 65 are stubs (`pass`), 121 test dead code. The suite reports 450 passed / 12 failed / 4 skipped — impressive numbers that mask the reality that critical paths like the LangGraph bridge, workflow orchestrator, and state persistence have zero test coverage.

The quality tooling (black, ruff, mypy, pytest) is correctly configured. The Makefile commands work. The problem isn't the tools — it's that the tests don't test what matters.

---

## Test Run Results

```
450 passed, 12 failed, 4 skipped, 53 warnings (40.91s)
```

### 12 Failures

| Test | File | Root Cause |
|------|------|-----------|
| 6x sidebar tests | test_sidebar.py | Outdated after sidebar refactor |
| 5x sidebar tests | test_sidebar_phase3.py | Duplicate of above |
| 1x concurrent sessions | test_auth_flow.py | SQLAlchemy connection leak (dead auth code) |

### 53 Warnings

All are SQLAlchemy `SAWarning` about garbage-collected connections and `RuntimeWarning` about unawaited coroutines from `AsyncMockMixin`. These indicate sloppy async mocking — connections opened but never properly closed.

---

## Test Inventory

### By Category

| Category | Files | Functions | Real | Stubs | Dead Code | Status |
|----------|-------|-----------|------|-------|-----------|--------|
| Unit tests | 22 | ~180 | ~60 | ~30 | ~90 | Mostly tests dead code |
| Integration tests | 5 | ~34 | ~5 | ~25 | ~4 | 95% placeholder stubs |
| UI tests | 18 | ~243 | ~48 | ~10 | ~27 | test_mode_factory_v2 is the only real one |
| **Total** | **45** | **~457** | **~48** | **~65** | **~121** | **10.5% real coverage** |

### Production Path Coverage

The actual production path: `mode_factory_v2 -> consolidated_service -> workflow_orchestrator -> providers -> database`

| Component | Test File | Real Tests | Assessment |
|-----------|-----------|------------|------------|
| mode_factory_v2 | test_mode_factory_v2.py | 14 | Only production UI tests |
| consolidated_service | test_consolidated_service.py | 12 | Heavily mocked, some real |
| workflow_orchestrator | - | 0 | UNTESTED |
| langgraph_bridge | - | 0 | UNTESTED |
| providers | test_providers.py | 14 | Proper LangChain mocking |
| state_manager | - | 0 | UNTESTED |
| mode_handlers | - | 0 | UNTESTED |
| database models | test_database.py | 13 | Only ConversationModel |

### Tests Covering Dead Code

| Dead Code | Test File | Tests | Should Delete |
|-----------|-----------|-------|---------------|
| app.py (dead UI) | test_mode_factory.py | 21 | Yes |
| seo_coach_app.py (dead UI) | test_seo_coach_interface.py | 24 | Yes |
| auth_service (Phase 2) | test_auth_flow.py | 8 | Yes |
| auth_service (Phase 2) | test_user_isolation.py | 10 | Yes |
| context loading (stubbed) | test_conversation_loading.py | 10 | Yes |
| conversations route (dead) | test_conversations.py | 7 | Yes |
| messages route (dead) | test_messages.py | 10 | Yes |
| chat route (deprecated) | test_chat.py | 4 (skipped) | Yes |
| various stubs | test_ui_integration.py | 18 (all pass) | Yes |
| various stubs | test_langgraph_workflows.py | 13 (all pass) | Yes |
| various stubs | test_service_integration.py | 12 (all pass) | Yes |

**Total removable: ~137 test functions across 11 files**

### Stub Tests (body = `pass`)

65 tests with no implementation. Example:

```python
def test_retry_decorator_success(self):
    """Test retry decorator with successful execution."""
    pass  # roadmap placeholder, not a test
```

Found in: `test_core_functionality.py` (9), `test_langgraph_workflows.py` (13), `test_service_integration.py` (12), `test_ui_integration.py` (18), and others.

These inflate the "passed" count without testing anything.

---

## Quality Tooling Assessment

### Configuration (pyproject.toml)

| Tool | Config | Status |
|------|--------|--------|
| pytest | `testpaths = ["tests"]`, `asyncio_mode = "auto"` | Works, but `auto` is risky |
| black | `line-length = 88` | Correct |
| ruff | `select = ["E", "W", "F", "I"]` | Correct, missing E501 enforcement |
| mypy | `disallow_untyped_defs = true`, strict options | Good — enforces type hints |

### Makefile Commands

| Command | What It Does | Assessment |
|---------|-------------|------------|
| `make test` | `pytest tests/ -v --cov` | Runs everything including stubs and dead code tests |
| `make test-unit-only` | `pytest tests/unit/ -v --tb=short` | Runs unit tests only, no backend needed |
| `make test-with-backend` | Starts backend + runs integration + unit | Good concept, but integration tests are stubs |
| `make quality` | `ruff check + black --check + mypy` | Works correctly |
| `make quality-fix` | `black + ruff --fix` | Works correctly |
| `make pre-commit` | `quality-check + test` | Runs all checks before PR |

**Issue:** `make test` runs 457 tests including 137 that test dead code and 65 stubs. This gives false confidence. A focused test run on production code would be more honest.

### CI/CD (.github/workflows/)

CI runs only unit tests (`tests/unit/`), which is the right call given integration tests are stubs.

### conftest.py

Minimal fixtures:
- `event_loop` — async event loop (correct)
- `async_engine` — in-memory SQLite (correct)
- `mock_session` — MagicMock of AsyncSession (basic)

**Missing:**
- No WorkbenchState factory fixture
- No LLM provider mock fixture
- No database transaction rollback fixture
- No Gradio test utilities

---

## Test Quality Issues

### 1. Implementation Detail Testing (Brittle)

```python
@patch("...consolidated_service.StateManager")
@patch("...consolidated_service.ConversationService")
@patch("...consolidated_service.ContextService")
@patch("...consolidated_service.ChatService")
async def test_execute_workflow_seo_coach(self, mock_chat, mock_ctx, ...):
```

Tests internal wiring, not behavior. Refactoring internals breaks tests even when behavior is preserved.

### 2. No Negative Test Cases

Test fixtures hardcode success scenarios:
```python
"execution_successful": True,
"workflow_steps": ["Workflow completed"],
"assistant_response": "Test response",
```

Zero tests for: provider failure, timeout, malformed input, state conversion error.

### 3. Async Mocking Issues

53 warnings about unawaited coroutines and garbage-collected connections. The async mocking strategy (`AsyncMockMixin`) doesn't properly handle SQLAlchemy session lifecycle.

### 4. No Coverage Reporting

pyproject.toml doesn't configure `--cov-fail-under`. No minimum coverage threshold enforced.

---

## Principled Test Strategy

Here's how to restructure around three layers: regression, unit, and integration.

### Layer 1: Regression Tests (smoke tests, always run)

Purpose: catch breakage fast. Run on every commit.

```
tests/regression/
  test_app_starts.py        — app creates without error
  test_health_endpoint.py   — GET /health returns 200
  test_chat_endpoint.py     — POST /chat/workflow returns response
  test_gradio_mounts.py     — Gradio interface mounts correctly
```

Characteristics:
- 4-8 tests, runs in <5 seconds
- No mocking — tests the real thing with a test database
- If any fail, nothing else matters
- Maps to `make test-smoke` (new Makefile target)

### Layer 2: Unit Tests (focused, mocked at boundaries)

Purpose: verify individual components work correctly in isolation.

```
tests/unit/
  services/
    test_providers.py       — ModelRegistry creates correct LangChain models
    test_consolidated.py    — ConsolidatedService orchestrates workflow
    test_bridge.py          — State conversion round-trips correctly (NEW)
    test_mode_handlers.py   — Workbench/SEO handlers produce correct output (NEW)
    test_state_manager.py   — State saves/loads correctly (NEW)
  models/
    test_schemas.py         — Pydantic validation catches bad input (NEW)
    test_database.py        — SQLAlchemy models CRUD works
  api/
    test_chat_workflow.py   — POST /chat/workflow validates + returns
    test_health.py          — Health endpoint works
```

Characteristics:
- 40-60 tests, runs in <15 seconds
- Mock only external boundaries (LLM providers, database I/O)
- Test behavior, not implementation details
- Include negative cases (bad input, provider failure, timeout)
- Maps to `make test-unit-only`

### Layer 3: Integration Tests (real services, real database)

Purpose: verify components work together end-to-end.

```
tests/integration/
  test_chat_e2e.py          — send message, get response, verify persisted
  test_conversation_flow.py — create conversation, send messages, load history
  test_dual_mode.py         — workbench and seo_coach produce different outputs
  test_provider_switching.py — switch provider mid-conversation
```

Characteristics:
- 10-15 tests, may take 30-60 seconds
- Use real database (in-memory SQLite), mock only LLM calls
- Test the full pipeline: API -> service -> workflow -> database -> response
- Maps to `make test-integration` (new Makefile target)

### What This Replaces

| Current | Count | Becomes |
|---------|-------|---------|
| 45 test files | 457 functions | ~15 test files, ~80 functions |
| 65 stub tests | pass | Deleted |
| 121 dead code tests | test unused code | Deleted |
| 12 failing tests | broken | Fixed or deleted |
| 0 regression tests | - | 4-8 smoke tests |
| 0 integration tests (real) | stubs | 10-15 real e2e tests |

### Makefile Integration

```makefile
# New test targets
test-smoke:          # Regression: 4-8 tests, <5s, always run
test-unit-only:      # Unit: 40-60 tests, <15s, mocked
test-integration:    # Integration: 10-15 tests, <60s, real DB
test:                # All of the above
pre-commit:          # quality-check + test-smoke + test-unit-only
```

The key change: `make pre-commit` runs smoke + unit only (fast). Full integration runs separately or in CI.

---

## Pragmatic Cleanup Plan

### Step 1: Delete dead test files (11 files, ~137 tests)

```
tests/ui/test_mode_factory.py           — tests dead mode_factory.py
tests/ui/test_seo_coach_interface.py    — tests dead seo_coach_app.py
tests/ui/test_ui_integration.py         — 18 stubs
tests/ui/test_sidebar.py                — 6 failing (outdated)
tests/ui/test_sidebar_phase3.py         — 5 failing (duplicate)
tests/integration/test_langgraph_workflows.py  — 13 stubs
tests/integration/test_auth_flow.py     — tests dead auth (1 failing)
tests/integration/test_user_isolation.py — tests dead auth
tests/integration/test_conversation_loading.py — tests dead context
tests/unit/test_service_integration.py  — 12 stubs
tests/unit/api/routes/test_chat.py      — 4 skipped, deprecated
```

**Result:** 0 failures, ~320 passing tests (all real).

### Step 2: Fix conftest.py

Add proper fixtures:
- `workflow_state_factory` — creates realistic WorkbenchState dicts
- `mock_llm_provider` — mock LLM that returns configurable responses
- `test_db` — in-memory SQLite with transaction rollback per test

### Step 3: Add missing critical tests

Priority order:
1. `test_bridge.py` — LangGraphStateBridge state conversion round-trip
2. `test_workflow_orchestrator.py` — main workflow execution
3. `test_mode_handlers.py` — workbench vs seo_coach routing
4. `test_state_manager.py` — state persistence and retrieval
5. `test_schemas.py` — Pydantic validation catches bad input

### Step 4: Configure coverage threshold

```toml
[tool.pytest.ini_options]
addopts = "--cov=src/agent_workbench --cov-report=term-missing --cov-fail-under=60"
```

Start at 60%, increase as tests are added.

---

## Cross-Cutting Summary (All 4 Assessments)

| Metric | FastAPI+DB | LangChain+Pydantic | Gradio | Tests | Total |
|--------|-----------|-------------------|--------|-------|-------|
| Bugs | 3 | 1 | 4 | 12 failing | 8 bugs + 12 test failures |
| Security | 1 | 0 | 0 | 0 | 1 |
| Dead code files | 3 | 2 | 3 | 11 | 19 files |
| Dead code lines | ~350 | ~400 | ~1,600 | ~2,000 (est) | ~4,350 |
| Stubs/placeholders | - | 21 models | - | 65 tests | 86 |
| Design decisions | 4 | 4 | 4 | 3 | 15 |
| Backlog items | 17 | 14 | 18 | 8 | 57 |
