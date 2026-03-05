# Backend Assessment 1/3: FastAPI + Database

**Branch:** feature/backend-assessment-fastapi-db
**Date:** 2026-03-05

---

## Executive Summary

**43 API endpoints defined. Only 4 are actually used.** The database layer has a critical design flaw where the `messages` table exists but is never written to — messages are stored as JSON blobs inside `conversation_states`. The Hub backend (HF Spaces) is ~70% stubbed. User/session tables and 20+ protocol methods are premature Phase 2 code that's never called.

---

## Routes Audit

### Endpoint Usage Map

| File | Total | Used | Unused | Stubs |
|------|-------|------|--------|-------|
| chat_workflow.py | 9 | 2 | 3 | 4 |
| simple_chat.py | 4 | 0 | 4 | 0 |
| conversations.py | 7 | 0 | 2 | 5 |
| messages.py | 5 | 0 | 5 | 0 |
| agent_configs.py | 5 | 0 | 3 | 2 |
| health.py | 2 | 2 | 0 | 0 |
| context.py | 3 | 0 | 3 | 0 |
| files.py | 5 | 0 | 5 | 0 |
| models.py | 2 | 0 | 2 | 0 |
| share.py | 1 | 0 | 0 | 1 |
| **TOTAL** | **43** | **4** | **27** | **12** |

### What's Actually Used

Only these endpoints are called from the Gradio UI:

1. `POST /api/v1/chat/workflow` — primary chat endpoint (chat_workflow.py)
2. `GET /api/v1/chat/conversations/{id}/state` — load conversation state for UI (chat_workflow.py)
3. `GET /api/v1/health` — health check (health.py)
4. `GET /api/v1/health/ping` — ping (health.py)

Everything else is dead code, stubs, or Phase 2 placeholders.

### Critical Route Issues

#### SECURITY: Path traversal in files.py

`files.py:41-43` — File ID includes user-supplied filename without sanitization. No file size limits, no type validation. Also incompatible with HF Spaces (`/tmp` is ephemeral).

**Action:** Delete files.py entirely for Phase 1, or fix with proper path validation.

#### BUG: Uninitialized variable in simple_chat.py

`simple_chat.py:210-220` — `api_key_source` referenced in except block before assignment. Uses fragile `if "api_key_source" in locals()` check.

**Action:** Initialize `api_key_source = "environment_variable"` before try block.

#### BUG: Stub endpoints return 200 OK

`conversations.py:138-195` — History endpoints return empty lists with 200 status, masking that they're unimplemented. Clients get silent no-data responses.

**Action:** Return 501 Not Implemented, or delete stubs.

#### DESIGN: Duplicate state endpoints

`chat_workflow.py` has two state endpoints:
- `/chat/consolidated/state/{id}` — never called, returns full state
- `/chat/conversations/{id}/state` — used by UI, returns subset

**Action:** Delete the unused `/consolidated/state/` endpoint.

#### DESIGN: context.py not registered

`context.py` defines 3 endpoints but is never imported in `main.py`. The same endpoints exist (differently pathed) in `chat_workflow.py`. Pure dead code.

**Action:** Delete context.py.

#### DESIGN: messages.py conflicts with architecture

Standalone message CRUD bypasses the LangGraph workflow pipeline. Creating messages outside the workflow breaks state management.

**Action:** Delete messages.py — messages should only flow through workflows.

### Route Recommendations

**Delete entirely (dead code):**
- `context.py` — not registered, duplicates chat_workflow.py
- `conversations.py` — unused CRUD suite, stubs return misleading 200s
- `messages.py` — conflicts with workflow-based message creation

**Delete or defer (Phase 2):**
- `files.py` — security issues, HF Spaces incompatible
- `share.py` — PWA share target stub, not wired

**Keep but document as dev-only:**
- `simple_chat.py` — useful for curl/API testing (fix the bug first)
- `models.py` — provider discovery, wire to settings UI later
- `agent_configs.py` — Phase 2 infrastructure

**Keep as-is:**
- `chat_workflow.py` — primary endpoint (remove duplicate state endpoint)
- `health.py` — clean, functional

---

## Database Audit

### Table Usage

| Table | Rows | Status |
|-------|------|--------|
| conversations | 24 | Used |
| conversation_states | 21 | Used (stores messages as JSON) |
| messages | 0 | DEAD — never written to |
| agent_configs | 0 | Phase 2 placeholder |
| business_profiles | 0 | SEO Coach — not implemented in SQLite backend |
| workflow_executions | 0 | Dead |
| alembic_version | 1 | Migration tracking |
| users | 0 | Phase 2 — never called |
| user_sessions | 0 | Phase 2 — never called |
| user_settings | 0 | Phase 2 — never called |
| session_activities | 0 | Phase 2 — never called |

### Critical Database Issues

#### CRITICAL: Messages table is dead code

`models/database.py:102-172` — MessageModel is fully defined with relationships and indexes but **never written to**. Messages are stored as JSON inside `conversation_states.state_data`.

This means:
- 0 rows in messages despite 24 conversations with messages
- To query messages, you must deserialize the entire state JSON blob
- No per-message indexing, search, or deletion possible
- The messages CRUD route (`messages.py`) targets a table that's always empty

**Action:** Decide: normalize messages into the table OR remove the table. The current hybrid is broken.

#### CRITICAL: Hub backend ~70% stubbed

`database/backends/hub.py` — These operations print warnings and return empty/placeholder values:
- `save_message()` — returns fake ID, never persists
- `get_messages()` — returns empty list
- `delete_message()` — returns False
- `delete_conversation()` — returns False
- All business profile operations — empty/False
- User session operations — simplified stubs

**Impact:** HF Spaces deployment silently loses data for any operation beyond basic conversation create/read.

#### BUG: MessageModel.delete() incorrect

`models/database.py:168-171` — Uses `await session.delete(self)` but `session.delete()` is not async. Should be `session.delete(self)` without await.

#### BUG: Schema drift in conversation_states

Migration `ca1c1d0b76c0` creates `conversation_id` as `String(36)`, but the Python model uses `PG_UUID(as_uuid=True)`. Works on SQLite, breaks on PostgreSQL.

#### DESIGN: User/session operations are premature

`protocol.py` defines 16 user/session/settings methods. `adapter.py` delegates all 35 methods including these. **None are called anywhere in the codebase.** These are Phase 2 auth features built into Phase 1.

Tables: `users`, `user_sessions`, `user_settings`, `session_activities` — all 0 rows, no callers.

**Action:** Remove from protocol and adapter. Add back when auth is actually implemented.

#### DESIGN: AdaptiveDatabase is pure pass-through

`adapter.py` — 35 methods, every one is:
```python
def method(self, args):
    return self.backend.method(args)
```

No caching, no validation, no logging, no retries. The only real logic is backend selection in `_create_backend()`.

**Action:** Replace with a factory function that returns the backend directly, or add actual adapter logic.

#### DESIGN: SQLiteBackend missing business profile and context operations

`backends/sqlite.py` — Protocol defines `save_business_profile()`, `get_business_profile()`, `save_context()`, `get_context()` but SQLiteBackend doesn't implement them. SEO Coach mode has no persistence for business profiles.

#### DESIGN: ThreadPoolExecutor never cleaned up

`backends/sqlite.py:45-74` — Creates `ThreadPoolExecutor(max_workers=1)` with new event loop per call. No `__del__` or context manager for cleanup.

### Pydantic Model Confusion

Three state representations with overlapping names:

| Model | Type | Location | Purpose |
|-------|------|----------|---------|
| ConversationState | Pydantic | standard_messages.py | Storage format |
| WorkbenchState | TypedDict | consolidated_state.py | LangGraph execution |
| ConversationStateDB | SQLAlchemy | conversation_state.py | DB persistence |

The naming makes the flow opaque:
```
ConversationStateDB -> ConversationState -> WorkbenchState -> (execute) -> WorkbenchState -> ConversationState -> ConversationStateDB
```

Additional issues:
- `ConversationState` uses forward reference string `"ModelConfig"` without `__future__` import
- `ValidatedWorkbenchState` has confusing `model_config_field` with alias to `model_config`
- `api_models.py`, `schemas.py`, and `business_models.py` have overlapping request/response models

---

## Actionable Backlog Items

Priority order. Each can be a separate commit or small PR.

### Immediate fixes (bugs)

1. [ ] Fix `await session.delete()` bug in MessageModel
2. [ ] Fix uninitialized `api_key_source` in simple_chat.py
3. [ ] Fix path traversal vulnerability in files.py (or delete the file)

### Dead code removal

4. [ ] Delete `context.py` — not registered, duplicated
5. [ ] Delete `conversations.py` — unused CRUD, misleading stubs
6. [ ] Delete `messages.py` — conflicts with workflow approach
7. [ ] Remove duplicate `/consolidated/state/` endpoint from chat_workflow.py
8. [ ] Remove user/session tables, protocol methods, and adapter methods (or move to Phase 2 branch)

### Design decisions needed

9. [ ] **Messages table**: normalize messages into it, or delete it?
10. [ ] **AdaptiveDatabase**: add real adapter logic, or replace with factory function?
11. [ ] **Hub backend stubs**: implement properly, or mark HF Spaces as read-only demo?
12. [ ] **Business profile persistence**: implement in SQLiteBackend, or defer?

### Technical debt

13. [ ] Align migration schema with Python models (String(36) vs UUID)
14. [ ] Fix ConversationState forward reference (`__future__` import)
15. [ ] Rename state models for clarity
16. [ ] Add ThreadPoolExecutor cleanup to SQLiteBackend
17. [ ] Document which endpoints are dev-only vs production

---

## Stats

- **Routes:** 43 defined, 4 used (9% utilization)
- **DB tables:** 11 defined, 2 actively used (18% utilization)
- **Protocol methods:** 35 in adapter, ~12 actually called
- **Security issues:** 1 (path traversal in files.py)
- **Bugs:** 3 (await delete, uninitialized var, schema drift)
- **Dead code files:** 3 route files can be deleted entirely
