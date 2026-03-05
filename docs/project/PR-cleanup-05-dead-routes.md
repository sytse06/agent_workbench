## Summary

- Deleted 4 dead route files + 1 deprecated file: context.py, conversations.py, messages.py, files.py, chat.py.deprecated
- Removed router registrations from main.py (conversations, messages, files)
- Deleted 2 test files that tested the dead routes
- Total: 7 files removed

## Why

These routes are never called from the UI. conversations.py and messages.py duplicate functionality in chat_workflow.py. files.py has a path traversal security issue. context.py was never even registered.

## Scope

Deleted route files:
- `src/agent_workbench/api/routes/context.py` (not registered in main.py)
- `src/agent_workbench/api/routes/conversations.py` (unused CRUD)
- `src/agent_workbench/api/routes/messages.py` (conflicts with workflow)
- `src/agent_workbench/api/routes/files.py` (security issue + HF incompatible)
- `src/agent_workbench/api/routes/chat.py.deprecated` (already deprecated)

Modified:
- `src/agent_workbench/main.py` (removed imports and router registrations)

Deleted test files:
- `tests/unit/api/routes/test_conversations.py`
- `tests/unit/api/test_messages.py`

## Test plan

- [x] `make pre-commit` passes
- [x] `uv run pytest tests/ -q` -- 232 passed, 0 failures
- [x] Health and chat endpoints still respond (verified via smoke tests)

Generated with [Claude Code](https://claude.com/claude-code)
