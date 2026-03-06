# PR-06: main.py Bloat Removal + Test Quality Fixes

Branch: `feature/cleanup-06-dead-services`
Merged to: `main`

---

## What changed

### main.py — trimmed ~1,047 → ~563 lines

Removed dead fallback interfaces that were unreachable in production:
- `create_simple_chat_interface()` — standalone Gradio interface, bypassed by mounting pattern
- `create_seo_coach_interface()` — orphaned SEO Coach fallback
- `create_workbench_interface()` — orphaned Workbench fallback
- `get_langgraph_service()` dependency injection function — Phase 2 placeholder wired to nothing

The live mounting pattern (`mode_factory_v2.py` + `app.mount()`) was left untouched.
See `.claude/docs/gradio-fastapi-pattern.md` for the critical mounting pattern details.

### database.py — SQLAlchemy deprecation warning fixed

Replaced deprecated `declarative_base()` call with the current `DeclarativeBase` class pattern.
This eliminated the third-party warning that was polluting test output.

### Test quality fixes

**`tests/unit/services/test_consolidated_service.py`**
- Fixed `AsyncMock` leaking across test cases due to missing teardown
- Tests now isolate properly; no shared mock state between cases

**`tests/unit/services/test_conversation_service.py`**
- Fixed real DB engine being created during unit tests (violated unit test isolation)
- Patched at the correct import boundary so no I/O occurs in unit scope

### Phase 2 services restored

Four services were incorrectly deleted as "dead code" in an earlier pass and restored:
- `auth_service.py` — Phase 2.0: HF OAuth + session management (unwired by design)
- `user_settings_service.py` — Phase 2.1: User settings CRUD (unwired by design)
- `langgraph_service.py` — Phase 2.3: 5-node workflow orchestration (unwired by design)
- `workflow_nodes.py` — Phase 2.3: LangGraph node implementations (unwired by design)

See `docs/phase2/phase2_architecture_plan.md` for the wiring plan.

### settings.py + test_settings_phase2.py

- `settings.py`: removed two unwired auth paths that referenced deleted route modules
- `tests/unit/test_settings_phase2.py`: removed 3 stale mock-based tests that asserted
  behaviour of the deleted paths; remaining tests pass

### Docs created

- `docs/project/ARCHITECTURE.md` — project architecture overview (created)
- `docs/project/BACKLOG.md` — Phase 2 roadmap added, cleanup PRs tracked

---

## Result

- main.py: ~1,047 → ~563 lines
- Test suite: 230 tests passing, 1 warning (third-party websockets, not ours)
- No regressions
