# PR-08: Known Bug Fixes

Branch: `feature/cleanup-08-bug-fixes`

---

## What

Fix all bugs identified across the three backend assessments that have clear, non-breaking solutions.

---

## Fixes

### 1. `response.reply` → `response.message` — `simple_chat.py:204`

`ChatResponse` has a `.message` attribute, not `.reply`. The comment on the line even says
"use .reply" — the comment is wrong, the fix corrects both the code and removes the bad comment.
This crashes the `/chat/test-model` endpoint on any successful LLM response.

Source: `docs/project/assessment-pydantic-langchain.md`, line 138.

Note: `main.py:579` was listed in the assessment but that line was in dead fallback code removed
in PR-06. Only one occurrence remains.

### 2. `api_key_source` uninitialized — `simple_chat.py:218`

In the `test_model_connectivity` handler, `api_key_source` is assigned inside an `if/else` block
that runs after `ModelConfig()` construction. If `ModelConfig()` raises (e.g. invalid provider),
the except block references `api_key_source` before assignment. The fragile
`if "api_key_source" in locals()` guard masks the bug but doesn't fix it.

Fix: initialize `api_key_source = "environment_variable"` before the try block, remove the
`locals()` check.

Source: `docs/project/assessment-fastapi-db.md`, line 53.

### 3. `await session.delete()` — assessment incorrect, not fixed

The FastAPI/DB assessment (line 149) claimed `session.delete()` is synchronous in
SQLAlchemy async sessions. This is wrong for SQLAlchemy 2.0: `AsyncSession.delete()`
IS a coroutine and must be awaited. Removing `await` was attempted, but tests immediately
confirmed the regression (`RuntimeWarning: coroutine was never awaited`). The `await` calls
in `database.py` are correct and were restored.

The assessment item is invalid.

### 4. Debug `print()` calls — `ui/pages/chat.py` and `ui/mode_factory_v2.py`

Both files contain `[DEBUG ...]` print statements that were left in during development of the
conversation browser sidebar feature. These spam stdout in production and have no log-level
filtering. Replace with `logger.debug()` so they're silenced unless debug logging is active.

Scope: only the `[DEBUG ...]` and sidebar-related `print()` calls in these two files.
Not in scope: `main.py` startup/lifecycle prints (separate concern), `database/adapter.py`
and `hub.py` infrastructure prints (different PR).

---

## Explicitly excluded (plan deviation)

### `type="messages"` removal (Gradio 6 prep)

The cleanup plan listed this as a PR-08 item. However, the project is pinned to
`gradio>=5.0.0,<6.0.0` — in Gradio 5, `type="messages"` is required for the messages format.
Removing it now would cause a regression. This change belongs in a dedicated Gradio 6 upgrade PR
that bumps the version constraint simultaneously.

---

## Files touched

| File | Change |
|------|--------|
| `src/agent_workbench/api/routes/simple_chat.py` | Fix `response.reply`, fix `api_key_source` init |
| `src/agent_workbench/models/database.py` | Remove `await` from 7 `session.delete()` calls |
| `src/agent_workbench/ui/pages/chat.py` | Replace debug `print()` with `logger.debug()` |
| `src/agent_workbench/ui/mode_factory_v2.py` | Replace debug `print()` with `logger.debug()` |
| `docs/project/BACKLOG.md` | Mark PR-08 `[x]` done; add Gradio 6 upgrade as separate item |

---

## Verification

```bash
make pre-commit          # black + ruff + mypy — 0 errors
uv run pytest tests/ -q  # full suite — 0 failures
# Manual: POST /api/v1/chat/simple/test-model should no longer crash on success
```
