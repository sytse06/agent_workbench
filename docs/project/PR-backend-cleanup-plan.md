## Summary

- Consolidated all 4 assessments into a sequenced 11-PR cleanup plan across 4 phases
- Phase 1: Clean baseline (E501, dead tests, smoke tests)
- Phase 2: Delete ~4,350 lines of dead code across 19 files
- Phase 3: Fix 8 bugs, externalize JS, strip CSS, add critical tests
- Phase 4: 12 design decisions to discuss before implementing
- Every PR results in working software (`make pre-commit` passes, app starts)

## Why

Move forward by cutting slack and delivering working software step by step. The 4 assessments identified 57 backlog items — this plan sequences them into concrete PRs with clear dependencies.

## Scope

Inputs:
- assessment-fastapi-db.md (17 items)
- assessment-pydantic-langchain.md (14 items)
- assessment-gradio.md (18 items)
- assessment-test-infrastructure.md (8 items)

Deliverable:
- `docs/project/assessment-cleanup-plan.md` — sequenced PR plan with rationale

Excluded:
- No code changes

## Test plan

- Not applicable (plan only)

Generated with [Claude Code](https://claude.com/claude-code)
