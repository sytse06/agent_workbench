# PR-11: Critical Missing Tests

**Branch:** `feature/critical-missing-tests`
**Status:** Planned

## Problem

The four components that Phase 2 directly builds on have zero test coverage.
API routes, models, and service wrappers are well-tested — but the LangGraph
pipeline that Phase 2 will rewire is completely uncovered. Any regression in
bridge, orchestrator, or handler logic will be invisible until it breaks in
production.

| Component | Lines | Tested | Phase 2 dependency |
|---|---|---|---|
| `langgraph_bridge.py` | 415 | ✗ | Agent state in/out conversion |
| `workflow_orchestrator.py` | 403 | ✗ | Will be extended by `create_agent` |
| `mode_handlers.py` | 457 | ✗ | Workbench/SEO routing logic |
| `message_converter.py` | 25 | ✗ | UI boundary — every agent response |
| `ValidatedWorkbenchState` | ~100 | ✗ | State validation before LangGraph |

## Scope

~40 new tests across 5 files. All unit tests — no LLM calls, no DB. Phase 2
services (`langgraph_service.py`, `workflow_nodes.py`) are tested when wired
in Phase 2.0, not here.

## New test files

### `tests/unit/services/test_langgraph_bridge.py`

Pure and near-pure methods only:

- `_convert_messages_to_standard()` — dict with metadata, dict without,
  StandardMessage passthrough
- `_convert_context_data()` — serializable values pass through,
  non-serializable → string fallback
- `merge_workflow_context()` — workflow keys override base keys
- `extract_from_workflow()` — assistant_response appended as StandardMessage,
  safe field-scoped reconstruction
- `_create_new_langgraph_state()` — seo_coach gets gpt-4o-mini config,
  workbench gets claude config

### `tests/unit/services/test_workflow_orchestrator.py`

Node logic and routing — state bridge and mode handlers mocked:

- `_route_by_mode()` — workbench → workbench, seo_coach → seo_coach,
  current_error set → error
- `_validate_input_node()` — empty message fails, invalid mode fails,
  valid state passes through
- `_detect_intent_node()` — mode appended to workflow_steps
- `_handle_error_node()` — Dutch fallback for seo_coach mode, English for
  workbench mode
- `_build_consolidated_workflow()` — graph compiles without error (structure
  smoke)

### `tests/unit/services/test_mode_handlers.py`

Pure methods — no LLM calls:

- `WorkbenchModeHandler._apply_parameter_overrides()` — override values
  applied, non-overridden fields preserved
- `WorkbenchModeHandler._build_technical_context()` — correct keys present,
  debug_mode propagated, parameter_overrides included when present
- `SEOCoachModeHandler._update_coaching_phase()` — Dutch keyword → phase
  transitions:
  - "analyse" / "check" → analysis
  - "aanbeveling" / "wat moet ik" → recommendations
  - "hoe" / "implementeren" → implementation
  - "resultaat" / "monitoring" → monitoring
  - unknown input → current phase preserved
- `SEOCoachModeHandler._build_coaching_context()` — business profile fields
  extracted, Dutch defaults applied when profile absent

### `tests/unit/ui/test_message_converter.py`

Pure — zero mocks needed:

- `to_chat_message(dict)` — role and content extracted correctly
- `to_chat_message(StandardMessage)` — role and content extracted correctly
- Only `_GRADIO_META_KEYS` (title, log, status, duration) pass through
- Unknown metadata keys are stripped
- Missing or None metadata → empty dict on output

### `tests/unit/models/test_consolidated_state.py`

Pydantic validation logic:

- `ValidatedWorkbenchState` rejects `retry_count > 5`
- Rejects empty strings in `workflow_steps`
- Rejects `provider_name` with spaces or uppercase
- `to_typeddict()` / `from_typeddict()` roundtrip preserves all fields
- `model_config` alias handled correctly across both directions

## Additions to existing files

### `tests/smoke/test_smoke.py` — 3 new smoke tests

- `WorkflowOrchestrator` graph compiles (mocked bridge and handlers)
- `SimpleChatWorkflow` builds without error (mocked model config)
- `LangGraphStateBridge` instantiates (mocked state manager and context
  service)

## What is NOT in scope

- Real LLM calls — all LLM interactions mocked at `ChatService` level
- DB operations — covered by `tests/integration/`
- `langgraph_service.py` / `workflow_nodes.py` — tested when wired in
  Phase 2.0
- New test infrastructure or fixtures beyond what `conftest.py` already
  provides

## Verification

```bash
make pre-commit && uv run pytest tests/ -q
# Target: ~270 tests passing (230 existing + ~40 new)
# No new warnings
```

## Why this before Phase 2

Phase 2.0 rewires `langgraph_bridge`, `workflow_orchestrator`, and
`mode_handlers` to use `create_agent`. Having baseline tests in place means
regressions are caught immediately rather than discovered through broken chat
responses in staging.
