## Summary

- Added 6 smoke tests in `tests/smoke/test_smoke.py`
- Added `make test-smoke` Makefile target (~3s)
- Updated `make pre-commit` to run `quality-check + test-smoke + test-unit-only` (fast)
- `make test` still runs the full suite for CI

## Why

Fast, reliable quality gate. Catches actual breakage before anything else runs.

## Scope

New files:
- `tests/smoke/__init__.py`
- `tests/smoke/test_smoke.py` (6 tests)

Modified:
- `Makefile` (added test-smoke target, updated pre-commit and help)

Smoke tests:
1. App creates without error
2. GET /health returns 200
3. GET /api/v1/health/ping returns pong
4. POST /api/v1/chat/workflow accepts requests
5. Gradio interface factory creates successfully
6. Static CSS files are served

## Test plan

- [x] `make test-smoke` passes in <5s (6 passed, 2.96s)
- [x] `make pre-commit` passes (quality + smoke + unit)

Generated with [Claude Code](https://claude.com/claude-code)
