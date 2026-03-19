# Technical Debt

Items that work today but carry known risk, fragility, or hidden assumptions.
Each entry has a severity, a description of the actual hazard, and where it belongs.

---

## Active Debt

### 1. `DatabaseConfig` ignores `DATABASE_URL` environment variable

**Severity:** Medium — silent misconfiguration risk

`DatabaseConfig` is a plain Pydantic `BaseModel`, not `BaseSettings`. It never reads
`DATABASE_URL` from the environment. The `.env` file sets
`DATABASE_URL=sqlite+aiosqlite:///./data/agent_workbench_dev.db`, but the app always
uses the hardcoded default `agent_workbench.db` via the module-level `_db_manager`
singleton in `api/database.py`.

Today this works because all code paths hit the same singleton — but anyone reading
`.env` has no idea their setting is ignored. Changing the default URL will also be
invisible unless `DatabaseConfig` is converted to `BaseSettings` with `env_prefix=""`.

**Where it belongs:** Convert `DatabaseConfig` to `pydantic_settings.BaseSettings` and
add `model_config = SettingsConfigDict(env_prefix="")` — small change, correct behaviour.
Can be done standalone before PR-2.6a.

---

### 2. `config: RunnableConfig = None  # type: ignore` is a type lie

**Severity:** Low — functional, but confusing to future maintainers

`ContentRetrieverTool._arun` and `WebResearchTool._arun` use bare `RunnableConfig`
with a `None` default and a `# type: ignore[assignment]` comment. This is a workaround
for LangChain's `_get_runnable_config_param` using `type_ is RunnableConfig` (identity
check, not `isinstance`), which means `Optional[RunnableConfig]` is silently skipped
for config injection.

The comment documents the reason, which reduces the risk. But if LangChain ever fixes
or changes this check, the workaround may break silently in the opposite direction.

**Where it belongs:** Watch for a LangChain fix. If `Optional[RunnableConfig]` starts
working correctly, remove the `type: ignore` and restore the proper annotation.

---

### 3. Module-level embedding and chunk caches have no TTL or eviction

**Severity:** Medium — memory leak risk in long-running processes

`_chunk_cache` and `_embedding_cache` in `document_context_graph.py` are plain
module-level dicts keyed by `conversation_id`. They grow unbounded for the lifetime
of the process. In a long-running server with many conversations, this leaks memory.
They also do not survive a server restart, so they are warm only within a single
process run.

**Where it belongs:** PR-2.6a is the right moment — once `thread_metadata` is live and
the dual-persistence cleanup is done, revisit these caches. Options: LRU with a max
size, TTL-based expiry, or drop the in-process cache entirely and rely on the DB (query
cost is low for document chunks within a session).

---

### 4. `AgentService` instantiates the LLM model at `__init__` time

**Severity:** Low — test reliability issue, caught and patched

`AgentService.__init__` calls `provider_registry.create_model(model_config)` immediately,
which constructs a real `ChatOpenAI` client. In environments without `OPENROUTER_API_KEY`
(CI, clean dev setups), this raises `OpenAIError` before any test logic runs.

Patched in `tests/unit/services/test_consolidated_service.py` with an `autouse` fixture
that mocks `provider_registry.create_model`. The patch is correct but means those tests
verify wiring only — they never exercise whether the model config is actually valid.

**Where it belongs:** `AgentService` should lazy-init the model on first use, not at
construction. Small refactor, unblocks reliable test runs anywhere without API keys.

---

### 5. Dual persistence holdover — state_bridge still called in `stream_workflow`

**Severity:** Medium — correctness risk on thread switching and server restart

`consolidated_service.stream_workflow()` still calls
`state_bridge.load_into_langgraph_state()` (~lines 382–393) and
`state_bridge.save_turn()` (~lines 492+). This is the Phase 1 dual-write that was
correct before the checkpointer existed. Now it causes message duplication risk on
server restart and makes thread switching unsafe.

The `get_state()` deduplication check (~lines 421–426) guards against duplication
within one process run but does not protect across restarts.

**Where it belongs:** PR-2.6a — this is the primary motivation for that PR. See
`docs/project/PR-26-threads.md`.

---

### 6. `PG_UUID` type used on a SQLite database

**Severity:** Low — works, semantically wrong

`DocumentModel`, `DocumentChunkModel`, and other models use `PG_UUID(as_uuid=True)` —
a PostgreSQL-specific SQLAlchemy dialect type — on a SQLite database. SQLAlchemy falls
back to storing UUIDs as 32-char hex strings, which works but is not the intended use
of this type. It also means UUID values are stored without hyphens (32 chars), which
trips up raw SQL queries but is transparent through the ORM.

**Where it belongs:** Phase 3.3 Postgres migration — when the engine switches to
Postgres, `PG_UUID` will work as intended. No action needed before then.

---

### 7. `AsyncSqliteSaver` is a latent bomb for multi-worker deployment

**Severity:** High for production, Low for current single-worker setup

The LangGraph checkpointer uses `AsyncSqliteSaver` backed by a local SQLite file
(`data/langgraph_checkpoints.db`). SQLite does not support concurrent writes from
multiple processes. If the deployment ever moves to multiple Uvicorn workers
(HF Spaces can have multiple workers, Docker setups often do), each worker gets its
own SQLite connection and checkpointer state diverges silently.

**Where it belongs:** Phase 3.3 — swap to `langgraph-checkpoint-postgres`. Needs
planning before long-term memory Store is implemented (Store has the same problem).
See `docs/project/BACKLOG.md` Phase 3.3.

---

## Resolved

| Item | Resolved in |
|---|---|
| `Optional[RunnableConfig]` skipped by LangChain config injection (`WebResearchTool`) | `c4318be` |
| Agent routing to `web_research` instead of `document_retrieval` for uploaded docs | `c4318be` |
| `test_stream_workflow` patching wrong method (`astream_events` vs `astream`) | `c4318be` |
| `test_initialize_service` failing without API key in environment | This session |
| Document retrieval end-to-end — confirmed working after routing fix | Manual test confirmed |
| Multi-turn conversation_id loss — Gradio not round-tripping `conv_id_state_wb` | `326b0fd` area |
