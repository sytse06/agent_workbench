## Summary

- Deleted 7 dead UI files (~1,327 lines): app.py, seo_coach_app.py, mode_factory.py (v1), and 4 orphaned components
- Deleted 3 dead endpoints in main.py that imported mode_factory v1: /api/mode, /api/health/detailed, create_hf_spaces_app (~177 lines)
- Deleted 10 test files (~2,185 lines) that imported the dead UI code
- Removed unused `Optional` import from main.py
- Total: 3,689 lines deleted, 18 files removed

## Why

These files were replaced by mode_factory_v2 and the new page-based UI. Nobody imports them except dead endpoints and dead tests.

## Scope

Deleted source files:
- `src/agent_workbench/ui/app.py` (368 lines, dead workbench UI)
- `src/agent_workbench/ui/seo_coach_app.py` (454 lines, dead SEO UI)
- `src/agent_workbench/ui/mode_factory.py` (224 lines, replaced by v2)
- `src/agent_workbench/ui/components/chat.py` (20 lines, never called)
- `src/agent_workbench/ui/components/settings.py` (62 lines, unused)
- `src/agent_workbench/ui/components/error_handling.py` (46 lines, unused)
- `src/agent_workbench/ui/components/simple_client.py` (154 lines, unused)

Deleted from main.py:
- `get_mode_info()` endpoint (/api/mode)
- `detailed_health_check()` endpoint (/api/health/detailed)
- `create_hf_spaces_app()` function (unused, HF deploy uses app directly)

Deleted test files (10 files, all imported dead code):
- test_dual_mode_integration.py, test_chat_flows.py, test_consolidated_integration.py
- test_error_scenarios.py, test_extension_pathways.py, test_gradio_integration.py
- test_langgraph_client.py, test_model_switching.py, test_seo_coach_integration.py
- test_state_consistency.py

## Test plan

- [x] `make pre-commit` passes (quality + smoke + unit)
- [x] `uv run pytest tests/ -q` -- 249 passed, 0 failures

Generated with [Claude Code](https://claude.com/claude-code)
