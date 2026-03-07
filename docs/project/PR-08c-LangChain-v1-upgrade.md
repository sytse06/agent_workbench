# PR-08C: LangChain v1 + LangGraph v1 Upgrade

**Branch:** `feature/langchain-v1-upgrade`
**Status:** Done

## Problem

The codebase is pinned to `langchain>=0.3.0` and `langgraph>=0.2.0`. LangChain v1 and
LangGraph v1 shipped late 2025 with a stable, production-ready foundation for agents.
Staying on 0.3.x means Phase 2 would have to introduce `create_agent` and middleware
on an outdated base, or migrate mid-way through.

Additionally, `langchain-community` (0.3.29) is listed as a dependency but has zero
imports anywhere in the codebase. It is dead weight pulling in a large transitive
dependency tree for nothing.

## Scope

Pure dependency upgrade. No `create_agent` adoption, no middleware wiring, no Phase 2
features. `uv sync` + the test suite define the remaining scope after the version bumps.

## Changes

### `pyproject.toml`

| Dependency | Before | After | Reason |
|---|---|---|---|
| `langchain` | `>=0.3.0` | `>=1.0.0` | Phase 2 `create_agent` requires v1 |
| `langchain-core` | `>=0.3.0` | `>=1.0.0` | Align with langchain v1 |
| `langgraph` | `>=0.2.0` | `>=1.0.0` | Stability release; core graph APIs unchanged |
| `langchain-community` | `>=0.3.0` | **REMOVE** | Zero imports — confirmed by grep |
| `langchain-openai` | `>=0.2.0` | resolver-determined | Bump minimum post-sync |
| `langchain-anthropic` | `>=0.1.0` | resolver-determined | Bump minimum post-sync |
| `langchain-ollama` | `>=0.1.0` | resolver-determined | Bump minimum post-sync |
| `langchain-mistralai` | `>=0.1.0` | resolver-determined | Bump minimum post-sync |
| `langchain-google-genai` | `>=2.1.12` | resolver-determined | Bump minimum post-sync |

Integration package minimums are updated to whatever `uv sync` resolves — no pinning
before running the resolver.

### Code changes

Expected to be zero. The active import surface is:
- `langchain-core` message types and `BaseChatModel` — unchanged in v1
- Provider packages (`langchain-openai`, etc.) — unchanged
- `langgraph.graph.StateGraph` — core graph APIs are stable in LangGraph v1

Any breakage discovered by `make pre-commit` or `pytest` is fixed as part of this PR.

## Known breaking changes to verify

| Change | Action |
|---|---|
| `response.text()` → `response.text` property | Grep `src/` for `.text()` on message objects |
| `AIMessage.example` parameter removed | Grep — almost certainly unused |
| `max_tokens` default in `langchain-anthropic` now model-dependent (was 1024) | No code fix needed; note the behavior change |
| `langchain-community` re-exports moved to `langchain-classic` | N/A — we never imported from it |

## What is NOT in scope

- `create_agent` adoption (Phase 2.3)
- Middleware wiring (Phase 2.5/2.6)
- `langchain-classic` — not needed; we use zero chains, retrievers, or hub functionality
- ContentRetriever / vector store (Phase 2.4)

## Execution

```bash
# Step 1 — update pyproject.toml (bumps + remove langchain-community)
# Step 2 — resolve
uv sync

# Step 3 — check known breaking changes
grep -r "\.text()" src/

# Step 4 — quality + tests
make pre-commit
uv run pytest tests/ -q

# Step 5 — fix anything surfaced, then update integration package minimums
#          in pyproject.toml to match resolved versions
```

## Strategic context

Phase 2 (`docs/phase2/phase2_architecture_plan.md`) is written for LangChain v1
throughout — `langchain.agents.create_agent`, `langchain.agents.middleware`, etc.
This bump ensures Phase 2 starts on the correct foundation rather than carrying
0.3.x debt into agent implementation.

## Verification

```bash
make pre-commit && uv run pytest tests/ -q
# All tests pass, quality checks clean
# langchain-community absent from installed packages (uv pip list | grep community)
```
