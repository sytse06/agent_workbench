# PR-07: Dead Pydantic Models + Aliases

Branch: `feature/cleanup-07-dead-models`

---

## Why

The project treats Pydantic and LangChain as separate worlds. They shouldn't be — LangChain
components (`ChatOpenAI`, `HumanMessage`, `AIMessage`, etc.) already inherit from Pydantic
`BaseModel`. The 15 backward-compat aliases in `schemas.py` and shadow model definitions in
`consolidated_state.py` are the clearest symptom: parallel model definitions that fragment the
namespace and obscure where real models live.

Removing them is the first concrete step toward the target pattern:
`ModelConfig.to_chat_model()`, LangChain messages stored directly (they're already Pydantic),
`WorkbenchState` as a Pydantic model instead of TypedDict.

Source: `docs/project/assessment-pydantic-langchain.md` — "Missing: Pydantic-LangChain Symbiosis".

---

## What changed

### `src/agent_workbench/models/schemas.py` — deleted 12 alias lines

Three alias blocks removed (lines were of the form `AliasName = ConcreteSchema`):

**Conversation group (5 aliases deleted):**
- `ConversationBase`, `ConversationCreate`, `ConversationUpdate`, `ConversationInDB`, `ConversationResponse`

**Message group (5 aliases deleted):**
- `MessageBase`, `MessageCreate`, `MessageUpdate`, `MessageInDB`, `MessageResponse`

**AgentConfig group (2 aliases deleted):**
- `AgentConfigBase`, `AgentConfigInDB`

Confirmed zero external imports for all 12 via grep before deletion.

**Not deleted from schemas.py:**
- `AgentConfigCreate`, `AgentConfigUpdate`, `AgentConfigResponse` — actively imported in
  `api/routes/agent_configs.py` and `tests/unit/api/test_agent_configs.py`

### `src/agent_workbench/models/consolidated_state.py` — deleted 2 of 3 shadow models

**Deleted:**
- `CreateConversationRequest` (lines ~350-357) — shadow adding `workflow_mode` field;
  real definition lives in `api_models.py:165`; not imported outside consolidated_state
- `ConversationResponse` (lines ~359-368) — shadow with different field set;
  real definition lives in `api_models.py:215`; not imported outside consolidated_state

**Not deleted (plan deviation):**
- `ContextUpdateRequest` (lines ~342-348) — the plan stated this was unused, but grep
  confirmed it IS imported by `api/routes/chat_workflow.py:25`. Keeping it in place.
  A follow-up PR should redirect that import to `api_models.py` and then delete the shadow.

### `docs/project/BACKLOG.md` — PR-06 and PR-07 marked done

---

## Scope explicitly excluded

**providers.py — Provider ABCs (~160 lines, lines 296-454):**
Assessment item #4 listed these as dead code. However grep confirms `PROVIDER_FACTORIES` dict
is imported and used at runtime in `api/routes/simple_chat.py:226`; concrete subclasses are
tested in `tests/unit/services/test_providers.py`. Assessment was written before simple_chat.py
usage was confirmed. Added to BACKLOG for later review.

**Phase 2 pre-built services:**
`auth_service.py`, `user_settings_service.py`, `langgraph_service.py`, `workflow_nodes.py` —
intentionally unwired Phase 2.0/2.1/2.3 infrastructure. Not touched.

---

## Follow-up items (added to BACKLOG)

- Redirect `chat_workflow.py` import of `ContextUpdateRequest` from `consolidated_state`
  to `api_models`, then delete the shadow from `consolidated_state`
- Provider ABCs in `providers.py` (~160 lines): revisit in a later PR once usage confirmed
- Schema rename: `ConversationSchema` → `ConversationDB` etc. (assessment item #12)

---

## Verification

```bash
make pre-commit          # black + ruff + mypy — 0 errors
uv run pytest tests/ -q  # full suite — 0 failures

# Sanity: should return no results
grep -r "ConversationBase\|MessageBase\|AgentConfigBase\|AgentConfigInDB" src/
```
