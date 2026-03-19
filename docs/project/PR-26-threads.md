# PR-2.6 — Thread Management

**Branch:** `feature/thread-management`
**Prerequisites:** PR-2.5 merged
**Design reference:** `docs/project/THREAD-MANAGEMENT.md`

Split into two sequential PRs. 2.6a is a prerequisite for 2.6b.

---

## PR-2.6a — Dual Persistence Removal + Thread Metadata + Listing API

### What this PR does

- Removes the Phase 1 dual-write holdover (`state_bridge` in `stream_workflow`)
- Makes the LangGraph checkpointer the single source of truth for conversation state
- Introduces a thin `thread_metadata` table for the conversation browser
- Cleans up the `conversations` table and migrates FK references to `thread_id`
- Exposes a `GET /threads` listing endpoint

### What this PR does NOT do

Thread switching, deletion, and the sidebar UI are in 2.6b. This PR is purely backend.

---

### Files to change

#### `src/agent_workbench/services/consolidated_service.py`

Remove from `stream_workflow()`:
- The `state_bridge.load_into_langgraph_state()` call (~lines 382–393) and its surrounding try/except
- The `state_bridge.save_turn()` call after streaming completes (~lines 492+)

The `get_state()` deduplication check (~lines 421–426) stays — it is now the sole guard against message duplication on the first turn after a server restart.

After the `done` event is yielded, write thread metadata:
- First turn (no existing metadata row): `INSERT INTO thread_metadata` with `thread_id`, `title` (first 15 chars of user message), `preview` (first 100 chars), `created_at = now()`
- Subsequent turns: `UPDATE thread_metadata SET last_updated_at = now() WHERE thread_id = X`

#### `src/agent_workbench/models/database.py`

Add `ThreadMetadata` SQLAlchemy model:

```python
class ThreadMetadata(Base):
    __tablename__ = "thread_metadata"

    thread_id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    preview: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime]
    last_updated_at: Mapped[datetime]
```

Remove `Conversation` model after migration confirms clean.

#### Alembic migration (single migration file)

Order of operations:
1. Create `thread_metadata(thread_id UUID PK, title TEXT, preview TEXT, created_at TIMESTAMP, last_updated_at TIMESTAMP)`
2. Migrate data from `conversations`: for each row insert into `thread_metadata` with `thread_id = id`, `title = first 15 chars of first message if available else "Untitled"`, `created_at = created_at`
3. Drop FK constraint on `documents.conversation_id`
4. Rename column `documents.conversation_id` → `documents.thread_id`
5. Add FK `documents.thread_id → thread_metadata.thread_id`
6. Repeat steps 3–5 for `document_chunks.conversation_id`
7. Drop `conversations` table

#### `src/agent_workbench/api/routes/threads.py` (new file)

```python
GET /threads
# Returns list of ThreadSummary ordered by last_updated_at DESC
# No pagination for now
```

Register in `main.py`.

#### `src/agent_workbench/models/schemas.py`

Add:

```python
class ThreadSummary(BaseModel):
    thread_id: UUID
    title: str
    preview: str
    created_at: datetime
    last_updated_at: datetime
```

#### `src/agent_workbench/services/langgraph_bridge.py`

**Do not delete.** `LangGraphStateBridge` has three distinct callers:

1. `consolidated_service.stream_workflow()` — the dual-write being removed. ✓ Handled above.
2. `consolidated_service.get_conversation_state()` — calls `load_into_langgraph_state(user_message="")` purely for state retrieval via API. Replace with a direct `agent_graph.get_state(thread_id)` call. Not dual persistence — just the wrong tool.
3. `langgraph_service.py` (lines 92, 219, 292) — Phase 2 5-node workflow orchestrator. Pre-built, currently unwired. Uses both `load_into_langgraph_state()` and `save_from_langgraph_state()`. **Do not touch** — protected Phase 2 infrastructure.

The bridge has 10 methods (`prepare_for_workflow`, `extract_from_workflow`, `merge_workflow_context`, `save_from_langgraph_state`, etc.) still used by `langgraph_service.py`.

**Net result for this PR:** two call sites removed from `stream_workflow()`, one replaced in `get_conversation_state()` with a direct checkpointer call. File stays.

---

### Tests

**Unit tests to add/update:**

- `tests/unit/services/test_consolidated_service.py`
  - `test_stream_workflow_does_not_call_state_bridge_save_turn` — assert `state_bridge.save_turn` is never called
  - `test_stream_workflow_writes_thread_metadata_on_first_turn`
  - `test_stream_workflow_updates_thread_metadata_on_subsequent_turn`

- `tests/unit/api/test_threads.py` (new)
  - `test_get_threads_returns_ordered_list`
  - `test_get_threads_empty_returns_empty_list`

**Integration check (manual before merging):**
- Start server, have a conversation, restart server, continue same conversation — confirm no duplicate messages in the response

---

### Acceptance criteria

- [ ] No calls to `state_bridge.load_into_langgraph_state()` or `save_turn()` in `stream_workflow()`
- [ ] `conversations` table dropped, `thread_metadata` table live with correct schema
- [ ] `documents.thread_id` and `document_chunks.thread_id` FK pointing to `thread_metadata`
- [ ] `GET /threads` returns threads ordered by `last_updated_at DESC`
- [ ] Thread metadata written on first turn, `last_updated_at` updated on each subsequent turn
- [ ] Server restart: existing thread continues correctly from checkpointer without duplicate messages
- [ ] All unit tests pass, migration runs cleanly on dev DB (`uv run alembic upgrade head`)

---

## PR-2.6b — Thread Switching + Deletion + Sidebar UI

**Branch:** `feature/thread-management-ui`
**Prerequisite:** PR-2.6a merged

### What this PR does

- `DELETE /threads/{thread_id}` endpoint (LangGraph SDK + metadata row)
- `GET /threads/{thread_id}/messages` endpoint for reconstructing display history
- Collapsible sidebar UI that slides in from the left
- Thread switching wired in Gradio: click thread → update `conv_id_state_wb`, reload chat display
- Thread deletion in UI
- "New conversation" button

---

### Files to change

#### `src/agent_workbench/api/routes/threads.py`

Add two endpoints:

```python
DELETE /threads/{thread_id}
# 1. Delete checkpointer state via LangGraph SDK API (no direct SQL)
# 2. DELETE FROM thread_metadata WHERE thread_id = X
# 3. DELETE FROM documents WHERE thread_id = X (cascades to document_chunks)

GET /threads/{thread_id}/messages
# Reconstruct message list for display from aget_state_history()
# Returns list of {role, content} dicts in chronological order
# Used by sidebar to populate chat display on thread switch
```

#### `src/agent_workbench/ui/pages/chat.py`

Thread sidebar additions:
- Sidebar `gr.Column` component, visible based on `show_conv_browser` state
- Toggle button that sets `show_conv_browser`
- Thread list populated from `GET /threads` on page load and after each conversation turn
- Click handler: call `GET /threads/{id}/messages`, update chatbot display, set `conv_id_state_wb`
- Delete handler: call `DELETE /threads/{id}`, refresh thread list, reset `conv_id_state_wb` if deleted thread was active
- "New conversation" button: reset `conv_id_state_wb` to `None`, clear chatbot display

The `show_conv_browser` feature flag already exists as `False` — flip it to `True` for workbench mode in this PR.

---

### Tests

**Unit tests to add:**

- `tests/unit/api/test_threads.py`
  - `test_delete_thread_calls_langgraph_sdk`
  - `test_delete_thread_removes_metadata_row`
  - `test_get_thread_messages_returns_chronological_list`
  - `test_delete_nonexistent_thread_returns_404`

**Integration check (manual before merging):**
- Switch to an older thread, confirm chat display reloads with correct history
- Switch to a thread with uploaded documents, ask a question, confirm `document_retrieval` finds the chunks
- Delete a thread, confirm it disappears from sidebar and checkpointer

---

### Acceptance criteria

- [ ] Sidebar slides in from the left, toggle button works
- [ ] Thread list populates from `GET /threads`, sorted by recency
- [ ] Clicking a thread switches the active conversation: chat display reloads, `conv_id_state_wb` updated
- [ ] Deleting a thread removes it from both the checkpointer (via LangGraph SDK) and `thread_metadata`
- [ ] "New conversation" resets state and clears display
- [ ] Switching to a thread with uploaded documents: `document_retrieval` tool finds the chunks via `thread_id`
- [ ] SEO Coach mode: sidebar not shown (feature-flagged, follow-up PR)
- [ ] All unit tests pass

---

## Scope boundaries

Items explicitly out of scope for 2.6a and 2.6b — tracked in later PRs below:

| Item | Where it belongs |
|---|---|
| LLM-generated thread titles | PR-2.6g — later enhancement, no schema change needed |
| Context compaction (summarization) | PR-2.6c — independent |
| Long-term memory Store (`agents.md`, `domain_context.md`) | PR-2.6d — blocked on Phase 3 auth for namespace key |
| SEO Coach sidebar | PR-2.6f — follow-up after 2.6b |
| Postgres checkpointer migration | Phase 3.3 — separate infrastructure PR before multi-worker deployment |

---

## PR-2.6c — Context Compaction (Summarization Node)

**Branch:** `feature/context-compaction`
**Prerequisite:** None — independent of 2.6a/b

### What this PR does

Adds a summarization node to the agent graph that fires when context window pressure is detected. Replaces the oldest messages in `MessagesState` with a compact summary, keeping the checkpointer as the store of record.

### Acceptance criteria

- [ ] Summarization node detects token count threshold and fires automatically
- [ ] Summary replaces oldest messages in checkpointer state, not appended
- [ ] Conversation continues coherently after summarization
- [ ] Unit tests for summarization trigger logic

---

## PR-2.6d — Long-Term Memory Store

**Branch:** `feature/long-term-memory`
**Prerequisite:** PR-2.6a (stable `thread_id` semantics) + Phase 3 auth (namespace key)

### What this PR does

Wires LangGraph `Store` as the semantic memory layer. Introduces two operational memory files per user, stored in the user-scoped `/memories/` namespace:

```
/memories/agents.md         — how to work with this user: behavior, tone, tool/agent preferences
                              (community standard filename for agent behavioral memory)
/memories/domain_context.md — what the agent knows about the user's domain:
                              project context + tech stack (Workbench)
                              business profile + SEO goals (SEO Coach — replaces static BusinessProfile)
```

**Build mechanism:** agent writes proactively via tool calls — system prompt instructs it to update these files when it learns something new about the user (self-improving instructions pattern).

**Curate mechanism:** memory panel UI where the user can read and edit both files directly; explicit commands ("remember this", "update your notes").

### Key constraints

- Namespace key must be tied to the authenticated user — blocked until Phase 3 auth lands
- In Phase 2, Store namespace is scoped to device session only (no cross-device memory)
- `InMemoryStore` (dev): resets on server restart — for local testing only
- `AsyncSqliteStore` (staging): persists but has the same single-process SQLite limitation as the checkpointer
- `PostgresStore` is the production-grade target — see Phase 3.3

### Acceptance criteria

- [ ] `agents.md` and `domain_context.md` read at conversation start via system prompt injection
- [ ] Agent updates files via tool calls on trigger (user correction, new preference stated)
- [ ] Memory panel UI: both files visible and editable
- [ ] Explicit user commands ("remember this") trigger an update
- [ ] Works in both Workbench and SEO Coach modes with mode-appropriate content

---

## PR-2.6e — Middleware

**Branch:** `feature/middleware`
**Prerequisite:** None — independent

### What this PR does

- `interrupt_before=["tool_node"]` — compile-time graph config, human-in-the-loop tool approval
- PII redaction wrapper around `llm_node`
- Custom context injection and execution tracking hooks

---

## PR-2.6f — SEO Coach Sidebar

**Branch:** `feature/seo-coach-sidebar`
**Prerequisite:** PR-2.6b merged, `show_conv_browser` feature flag in place

### What this PR does

Enables the conversation browser sidebar for SEO Coach mode. The flag `show_conv_browser` already exists and defaults to `False` — this PR flips it for SEO Coach and handles any mode-specific display differences.

---

## PR-2.6g — LLM-Generated Thread Titles

**Branch:** `feature/llm-thread-titles`
**Prerequisite:** PR-2.6a merged

### What this PR does

Post-turn async task: after the first turn completes, send the first user message to the LLM and write a short descriptive title back to `thread_metadata.title`. No schema change needed — `title` column already exists from 2.6a, currently populated with the first 15 chars of the user message.

### Acceptance criteria

- [ ] LLM title generation runs async after `done` event, does not block streaming
- [ ] Falls back to the 15-char truncation if generation fails
- [ ] Title visible and correct in thread list
