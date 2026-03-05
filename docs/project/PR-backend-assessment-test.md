## Summary

- Assessed test infrastructure: 457 tests across 45 files, but only ~48 test production code (10.5%)
- 65 stub tests (body = `pass`), 137 tests covering dead code, 12 failing
- Proposed 3-layer principled test strategy: regression (smoke), unit, integration
- Pragmatic cleanup plan: delete 11 test files, fix conftest, add 5 critical missing tests
- Quality tooling (black, ruff, mypy, pytest) correctly configured — tools aren't the problem

## Why

The test infrastructure is bloated and gives false confidence. 450 tests pass but critical production paths (bridge, orchestrator, state manager, mode handlers) have zero coverage. Restructure around principled TDD layers.

## Scope

Included:
- All 45 test files in `tests/`
- conftest.py fixtures and async setup
- pyproject.toml test/quality config
- Makefile test commands (make test, test-unit-only, test-with-backend, pre-commit)
- CI/CD workflow (.github/workflows/)
- Principled 3-layer test strategy proposal
- Pragmatic cleanup plan (what to delete, what to add)

Excluded:
- No test rewrites/deletes/additions — assessment only

## Test plan

- Not applicable (assessment only)

Generated with [Claude Code](https://claude.com/claude-code)
