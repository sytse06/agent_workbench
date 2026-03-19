# Thread Management — Design Notes

**Date:** 2026-03-18
**Status:** Brainstorm capture — not a final design. Use as a head start for the design session.
**Related:** `docs/project/BACKLOG.md` Phase 2.6a
**Reference:** [LangGraph — How to add memory to your graph](https://docs.langchain.com/oss/python/langgraph/add-memory)

---

## Context

PR-2.6a in the backlog currently bundles thread management, summarization, long-term memory, and middleware under one ticket. These don't belong together. The suggested PR split at the bottom of this document separates them.

Thread management is the prerequisite that the others depend on — or are at least cleaner after. It should be isolated and shipped first.

---

## The Core Problem: Dual Persistence

Every conversation turn currently writes to two places:

1. **LangGraph checkpointer (`AsyncSqliteSaver`)** — full agent state: messages, tool calls, reasoning traces, tool results. Keyed by `thread_id` (= `conversation_id` UUID). Lives in `data/langgraph_checkpoints.db`.

2. **`state_bridge.save_turn()`** — simplified user/assistant message pairs in the `conversations` DB table. Written via `LangGraphStateBridge`. Lives in `data/agent_workbench_dev.db`.

This works today because there is only one active thread and no thread switching. The relevant code is in `src/agent_workbench/services/consolidated_service.py`:

- Lines ~382–393: loads history from `state_bridge.load_into_langgraph_state()` at the start of `stream_workflow()` — non-fatal catch
- Lines ~419–433: `get_state()` check to detect if the checkpointer already has history; if so, passes only the new user message to avoid duplicating context in `MessagesState`

The `get_state()` check prevents message duplication **within one process lifetime**. It does not protect against:

- Server restarts (checkpointer persists, but `state_bridge` will also try to reload from DB and inject into what the checkpointer already holds)
- Thread switching (switching `conversation_id` causes `load_into_langgraph_state` to load a different thread's DB history, while the checkpointer independently holds the correct state for that thread)

The existing code comments call this a "Phase 1 holdover". That's accurate. The dual-write made sense before the checkpointer existed. It doesn't make sense now.

---

## The Core Decision: Which System Owns the Truth?

Before any UI or thread features can be built, one system must own the truth.

| Question | Option A: Checkpointer owns truth | Option B: DB owns truth |
|---|---|---|
| Thread list query | Query `AsyncSqliteSaver` checkpoint records | Query `conversations` table |
| Resume conversation | Checkpointer state — agent picks up exactly where it left off | Replay messages from DB into a fresh checkpointer thread |
| Delete thread | Delete checkpoint records + DB metadata row | Delete DB record + orphan checkpoint (or chase both) |
| Server restart | `AsyncSqliteSaver` persists across restarts natively | DB persists; checkpointer rehydrates from DB on first turn |
| What gets stored | Full agent state: tool calls, reasoning traces, token counts | Only user/assistant message text |

**Decision: Option A — checkpointer owns the truth.**

LangGraph was designed for this. `AsyncSqliteSaver` is not a cache; it is the durable conversation store. Making it the authority means `state_bridge.load_into_langgraph_state()` and `save_turn()` calls in `stream_workflow()` become dead code and get removed in this PR. The `LangGraphStateBridge` simplification already flagged as deferred in PR-2.3c and PR-2.3d belongs here.

---

## The Metadata Gap

The checkpointer stores raw LangGraph state. It has no conversation title, preview, or human-readable timestamp metadata that a conversation browser needs. Three options:

**Option 1 (preferred): Thin `conversation_metadata` table**
- Schema: `id UUID PK, title TEXT, preview TEXT, created_at TIMESTAMP, last_updated_at TIMESTAMP`
- Written on the `done` event of the first turn (title + preview derived from first user message)
- Updated `last_updated_at` on every subsequent `done` event
- `GET /threads` queries this table — no checkpointer involvement at query time

**Option 2: Extract from checkpointer at query time**
- Call `aget_state_history()` per thread to get timestamps and reconstruct previews
- Expensive at list-view scale; no title unless you parse message content
- Not recommended

**Option 3: LLM-generated title**
- Post-turn async task: send first user message to LLM, get a short title back
- Better UX but adds latency and token cost to every conversation start
- Can be layered on top of Option 1 later without redesigning the table

---

## What Thread Management Actually Requires (in order)

These are prerequisites — each step must be done before the next is safe to implement.

**1. Remove dual persistence**

Remove `state_bridge.load_into_langgraph_state()` and `state_bridge.save_turn()` from `stream_workflow()`. The checkpointer is now the only writer. The `get_state()` check becomes the sole guard against message duplication — verify it holds across restarts before closing this step. This is a prerequisite for everything else; thread switching is unsafe until this is resolved.

**2. Thread metadata table**

Alembic migration: `conversation_metadata(id UUID PK, title TEXT, preview TEXT, created_at TIMESTAMP, last_updated_at TIMESTAMP)`. Written on first-turn `done` event. Title defaults to first N characters of the first user message (LLM title can be added later as an enhancement without schema changes).

**3. Thread listing API**

`GET /threads` — returns metadata table rows ordered by `last_updated_at DESC`. No checkpointer involvement. Pagination optional for now.

**4. Thread switching in Gradio**

Update `conv_id_state_wb` to the selected thread's UUID. Clear the chat display. Reconstruct the visible message list from `aget_state_history()` on the checkpointer — this gives the full message sequence for display, without re-running any inference.

**5. Thread deletion**

`DELETE /threads/{id}` — deletes checkpoint records for `thread_id` (via LangGraph API or direct SQL — see open question below) and deletes the metadata row. If the deleted thread is the active thread in Gradio, reset `conv_id_state_wb` to `None`.

**6. Conversation browser sidebar UI**

List of threads with title, preview, and timestamp. Click to switch. Delete button per thread. "New conversation" button resets `conv_id_state_wb` to `None`. The workbench UI already has a `show_conv_browser` flag defaulted to `False` — this is where it gets wired up.

---

## Decisions

All open questions resolved.

**Title generation** ✓
Static — first 15 characters of the first user message. Zero cost, ships fast. LLM-generated title is a later enhancement, not a blocker.

**`conversations` table** ✓
Option B: create a new `thread_metadata` table, migrate existing rows, drop `conversations`. Cleaner than renaming — no Alembic rename awkwardness, FK targets are explicit in the migration. `conversations` is phased out entirely.

**FK key: `thread_id`** ✓
`documents` and `document_chunks` should key to `thread_id`, not `conversation_id`. The naming inconsistency is cleaned up here — the FK target in the new `thread_metadata` table uses `thread_id` as the column name throughout. The retrieval tool already receives `thread_id` from LangGraph config; no logic change needed, only the FK target and column name in the migration.

**Thread switching and document context** ✓
Not a design decision — a verification task. Mark as integration test coverage in 2.6b: switch to a thread that had uploaded documents, confirm retrieval tool finds them via `thread_id`.

**Checkpointer thread deletion** ✓
Use LangGraph SDK API exclusively — no direct SQL against `checkpoints`, `checkpoint_writes`, or `checkpoint_migrations` tables. If the SDK API proves reliable, establish it as the standard pattern for all checkpointer interactions going forward.

**Conversation browser placement** ✓
Collapsible sidebar that slides in from the left. Standard pattern, familiar to users. Workbench-first; the `show_conv_browser=False` feature flag is already in place. SEO Coach follows later.

---

## Relationship to Other PR-2.6 Items

The other items currently grouped under PR-2.6a are largely independent. Splitting them out avoids blocking unrelated work on thread management decisions.

| Item | Dependency on thread management |
|---|---|
| Context compaction (summarization) | None — summarization node just reduces message count in the checkpointer; can be developed and tested independently |
| Long-term memory (LangGraph Store) | Loosely dependent — `Store` is separate from checkpointer, but namespace design (keyed by what?) is cleaner once `conversation_id` semantics are stable post-2.6a |
| Middleware (`interrupt_before`, PII redaction) | None — `interrupt_before=["tool_node"]` is compile-time graph config; PII redaction is a wrapper around `llm_node`; neither touches thread state |

---

## Memory Is the Real Topic

Thread management and the checkpointer are not primarily about conversation UI — they are the working memory system of the agent. Framing it as "thread management" undersells the design challenge. Before going further, think through the full memory stack and what webapp deployment actually means for each layer.

### The four memory layers

| Layer | What it holds | LangGraph mechanism | Resets on... |
|---|---|---|---|
| **In-context (working)** | Current conversation messages + tool calls | `MessagesState` in checkpointer | Every new thread |
| **Episodic (short-term)** | Summaries of past turns in this thread | Summarization node writes back into checkpointer | Thread deletion |
| **Semantic (long-term)** | Facts, user preferences, cross-session knowledge | LangGraph `Store` | Never (explicit delete) |
| **Procedural** | Tools and skills available | `SKILLS.md` + `SkillLoader` | Deployment / code change |

### Webapp deployment consequences

A single-user desktop app and a multi-user webapp have fundamentally different memory constraints. This app is headed toward webapp deployment (HuggingFace Spaces, multi-user).

**Working memory (checkpointer):**
- `AsyncSqliteSaver` uses a local SQLite file — fine for single-process local dev, breaks under multi-worker deployments (multiple Uvicorn workers will each have their own SQLite connection)
- HF Spaces runs a single process today, but this is a latent bomb if the deployment model changes
- A Postgres-backed checkpointer (`langgraph-checkpoint-postgres`) is the production-grade answer; the switch should be planned before the memory architecture is locked in

**Long-term memory (Store):**
- `InMemoryStore` resets on every server restart — useless for a webapp
- `AsyncSqliteStore` persists but has the same single-process SQLite limitation as above
- Without user authentication (Phase 3), the Store namespace can only be keyed by `conversation_id` or device session — cross-device and cross-session memory isn't possible until Phase 3 auth lands
- This means long-term memory in Phase 2 is scoped to the device/browser session, not the user

**Key open question before any of this is implemented:** what is the target deployment model at the point where memory goes live? If HF Spaces (single process, SQLite OK), the current stack is fine. If a proper multi-user webapp (multiple workers, shared DB), it needs Postgres-backed checkpointer and Store.

### deepagents library — findings

deepagents (`langchain-ai/deepagents`) did not replace LangGraph `Store` — it built a filesystem metaphor on top of it. The reason: LangGraph Store's raw KV interface (`put/get/search`) doesn't map naturally to how LLMs navigate information. deepagents adds `ls`, `read_file`, `write_file`, `edit_file`, `grep` as tools, and the LLM navigates memory as a virtual filesystem. The underlying storage is still LangGraph `BaseStore`.

**Key findings relevant to agent_workbench:**

- `StoreBackend` namespaces by `(assistant_id, "filesystem")` by default — designed for single-agent deployments, not multi-user webapps. In a multi-user context all users would share the same namespace. **Namespace key must be tied to the authenticated user** — this blocks long-term memory until Phase 3 auth lands.
- `PostgresStore` is the only production-grade store mentioned. `InMemoryStore` resets on restart. SQLite not mentioned as a production option — consistent with the checkpointer migration need above.
- No retention mechanisms: no TTL, no scoring, no decay, no forgetting. "Prune old data" is listed as a best practice with no tooling. This is an unsolved problem in the ecosystem.
- The **self-improving instructions pattern** is directly adoptable: the agent maintains its own operational memory files, updates them based on user feedback via tool calls, and reads them at the start of each conversation via system prompt instruction.

### Operational memory file design

Two files, same names across both modes, stored in the user-scoped `/memories/` namespace:

```
/memories/agents.md         — how to work with this user: behavior, tone, tool/agent preferences
                              (community standard filename for agent behavioral memory)
/memories/domain_context.md — what the agent knows about the user's domain:
                              business profile + SEO goals (SEO Coach),
                              project context + preferences (Workbench)
```

**Workbench** `agents.md`: preferred tools, response style, things to always/never do, agent usage patterns.
**Workbench** `domain_context.md`: project context, tech stack, ongoing work, past decisions.

**SEO Coach** `agents.md`: coaching style, language preferences, communication tone, how the user likes to receive feedback.
**SEO Coach** `domain_context.md`: replaces the static `BusinessProfile` Pydantic model — accumulated business context, SEO goals, what's been tried, what's working.

**Build vs. curate:**
- *Build*: agent writes proactively using the self-improving instructions pattern — system prompt instructs the agent to update these files when it learns something new about the user
- *Curate*: user-facing memory panel in the UI where both files can be read and edited directly; also explicit commands ("remember this", "update your notes")

The memory panel is arguably more valuable than the conversation browser as a UI investment — thread history is ephemeral value, curated operational files are compounding value.

---

## Suggested PR Split

| PR | Scope | Prerequisite |
|---|---|---|
| **2.6a** | Remove dual persistence + thread metadata table + thread listing API | None |
| **2.6b** | Thread switching + deletion + conversation browser sidebar UI | 2.6a |
| **2.6c** | Context compaction (summarization node) | None — independent |
| **2.6d** | Long-term memory Store | 2.6a (stable `conversation_id` semantics) |
| **2.6e** | Middleware (`interrupt_before`, PII redaction, context injection) | None — independent |
