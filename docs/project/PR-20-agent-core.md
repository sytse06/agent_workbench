# PR-2.0: Agent Core

**Branch:** `feature/agent-core`
**Status:** Planning

---

## Problem

The workbench currently calls the LLM directly from `WorkbenchModeHandler.handle()` via
`ChatService.chat()` — a one-shot call with no tool capability, no working memory, no structured
output. Every conversation turn is stateless and the `_get_conversation_history()` method in
`llm_service.py` returns an empty list `[]` (stubbed since Phase 1).

`langgraph_service.py` and `workflow_nodes.py` exist as pre-built Phase 2 infrastructure but are
entirely unwired — never instantiated, never called. The 5-node workflow they define has never
executed in production.

This PR wires the agent stack: `create_agent` becomes the execution engine inside a LangGraph
node, multi-turn history is loaded from the database, and thinking tokens surface in the UI via
`gr.ChatMessage`.

---

## Scope

**IN:**
- New `AgentService` wrapping `create_agent` — no tools yet, structured output from day one
- Rename `WorkbenchLangGraphService` → `LangGraphService` in `langgraph_service.py` — mode-independent execution layer
- Wire `LangGraphService` as the active workflow for all modes — replaces the direct LLM path through mode handlers
- Wire `workflow_nodes.py` — specifically `generate_response_node` delegates to `AgentService`
- Wire `_get_conversation_history()` stub to actually query DB via `StateManager`
- Task-scoped working memory: agent receives unique `task_id` (not `conversation_id`) as checkpointer thread
- Streaming thinking tokens: Claude extended thinking `content_blocks` → `gr.ChatMessage(metadata={"status": "thinking"})`
- SEO Coach: same agent path — mode handlers are UI/language concerns only, execution layer is shared

**OUT (subsequent PRs):**
- Tools (Phase 2.3: `ContentRetriever`, Phase 2.4: Firecrawl)
- Middleware (Phase 2.5: PII, summarization, human-in-the-loop)
- File upload and Docling pipeline (Phase 2.1, 2.2)
- Multi-agent coordination (Phase 3)
- Auth, PWA, user management (Phase 3)

---

## Current State

**Active chat path (Workbench mode):**
```
POST /api/v1/chat/workflow
  → ConsolidatedChatService.execute_workflow()
  → WorkflowOrchestrator (5-node LangGraph graph)
  → WorkbenchModeHandler.handle()
  → ChatService.chat()          ← direct LLM call, no agent, no history
  → assistant_response (str)
```

**Pre-built but unwired:**
- `WorkbenchLangGraphService` (`langgraph_service.py`) — 5-node workflow, never instantiated; renamed to `LangGraphService` in this PR
- `WorkflowNodes` (`workflow_nodes.py`) — `generate_response_node` calls `self.llm_service.chat()` directly
- `_get_conversation_history()` (`llm_service.py:~185`) — returns `[]`

**To be retired in this PR:**
- `workflow_orchestrator.py` — replaced by `LangGraphService`
- `simple_chat_workflow.py` — chatting is agent execution; no separate "simple" path
- `ChatService.chat()` — direct LLM call replaced by `AgentService.run()`; `ChatService` shrinks to model instantiation only (`get_model()`)

---

## Architecture Decisions

### Decision 1: AgentService as a dedicated service class

`AgentService` wraps `create_agent` and is instantiated once at startup (singleton, injected via
DI). It holds:
- The configured `create_agent` instance (toolless in this PR)
- A `MemorySaver` checkpointer for task-scoped working memory
- An `AgentResponse` Pydantic model for structured output

```python
# services/agent_service.py (new)
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from typing import Optional

class AgentResponse(BaseModel):
    message: str
    status: str = "success"
    reasoning: Optional[str] = None  # populated when extended thinking is on

class AgentService:
    def __init__(self, llm_service: ChatService):
        self.agent = create_agent(
            model=llm_service.get_model(),
            tools=[],                          # Phase 2.3 adds tools here
            structured_output=AgentResponse,
            checkpointer=MemorySaver(),        # task-scoped working memory
        )

    async def run(
        self,
        messages: list[dict],
        task_id: str,
    ) -> AgentResponse:
        config = {"configurable": {"thread_id": task_id}}
        result = await self.agent.ainvoke({"messages": messages}, config=config)
        return result["structured_response"]
```

### Decision 2: task_id — not conversation_id — for agent checkpointer

Per `docs/phase2/state_management_critical_pattern.md`:
- LangGraph StateGraph checkpointer uses `conversation_id` (persistent conversation state)
- Agent checkpointer uses a fresh `task_id = str(uuid4())` per invocation (ephemeral working memory)
- The two never share a thread ID — no state conflict

### Decision 3: `LangGraphService` replaces `WorkflowOrchestrator` for both modes

`LangGraphService` becomes the single execution path. Both Workbench and SEO Coach route
through it — `WorkbenchModeHandler` and `SEOCoachModeHandler` remain as the mode-specific logic
(prompt building, Dutch vs English, coaching phase) called from within the workflow nodes.

`WorkflowOrchestrator` is retired. `AgentService` is the new execution engine inside
`generate_response_node`.

### Decision 4: Thinking tokens via extended thinking (Anthropic only)

Extended thinking requires:
- `ChatAnthropic(model=..., thinking={"type": "enabled", "budget_tokens": 5000})`
- Response `content_blocks` contain `{"type": "thinking", "thinking": "..."}` entries
- These map to `gr.ChatMessage(role="assistant", content=thinking_text, metadata={"title": "Reasoning", "status": "done"})`

This is Anthropic-specific. For OpenAI/Ollama providers, thinking tokens are omitted gracefully.
The `AgentService.run()` method detects thinking blocks in the response and returns them in
`AgentResponse.reasoning`.

---

## Step-by-Step Implementation

### Step 1: Create `AgentService`
**New file:** `src/agent_workbench/services/agent_service.py`

- Define `AgentResponse(BaseModel)` with `message`, `status`, `reasoning`
- `AgentService.__init__`: call `create_agent(model, tools=[], structured_output=AgentResponse, checkpointer=MemorySaver())`
- `AgentService.run(messages, task_id) -> AgentResponse`: `ainvoke` — used inside workflow nodes for state management
- `AgentService.astream(messages, task_id) -> AsyncIterator[dict]`: `astream_events` — used by UI handler for token streaming; yields typed event dicts:
  ```python
  # event shapes yielded by astream():
  {"type": "thinking_chunk", "content": str}   # Anthropic extended thinking only
  {"type": "answer_chunk", "content": str}      # all providers
  {"type": "done", "response": AgentResponse}   # final structured response
  ```
- Handle thinking blocks: detect `content_blocks` of type `"thinking"` in stream events → emit `thinking_chunk` events
- Graceful fallback when `create_agent` is unavailable: fall back to direct `model.ainvoke()` / `model.astream()`
- Run `make pre-commit && uv run pytest tests/ -q` — no regressions before wiring

### Step 2: Wire `_get_conversation_history()` to DB
**File:** `src/agent_workbench/services/llm_service.py`

- Replace the `return []` stub with `await self.state_manager.get_messages(conversation_id)`
- Convert DB message dicts → `StandardMessage` using the safe field-scoped pattern from PR-08b
- `StandardMessage` → LangChain message types using `standard_to_lc()` mapping (Issue C from PR-08b plan, now actually used):
  ```python
  _ROLE_TO_LC = {"user": HumanMessage, "assistant": AIMessage, "system": SystemMessage}
  ```
- This makes multi-turn context available to both the legacy path and the new agent path

### Step 3: Update `WorkflowNodes.generate_response_node`
**File:** `src/agent_workbench/services/workflow_nodes.py`

- Inject `AgentService` into `WorkflowNodes.__init__`
- In `generate_response_node`: replace direct `self.llm_service.chat()` call with:
  ```python
  task_id = str(uuid4())
  response = await self.agent_service.run(messages=history_as_dicts, task_id=task_id)
  ```
- Store `task_id` in message metadata for traceability
- Update state: `assistant_response`, `conversation_history`, `execution_successful`

### Step 4: Wire `LangGraphService` as the active workflow (both modes)
**File:** `src/agent_workbench/main.py`

- Instantiate `LangGraphService(state_bridge, llm_service, context_service)` with `AgentService` injected into `WorkflowNodes`
- Remove `WorkflowOrchestrator` instantiation — it is retired

**File:** `src/agent_workbench/api/routes/chat_workflow.py`

- Route all `workflow_mode` values to `LangGraphService.process_message()`
- Mode handlers (`WorkbenchModeHandler`, `SEOCoachModeHandler`) are called from within the workflow nodes as before — no change to their interfaces

### Step 5: Streaming UI handler + thinking tokens
**File:** `src/agent_workbench/ui/pages/chat.py`

Convert both mode handlers from `return` to `async def` generators using `yield`. The UI now streams tokens directly from `AgentService.astream()`.

**Workbench** (`handle_chat_interface_message`):
```python
async def handle_chat_interface_message(message, history):
    task_id = str(uuid4())
    messages = build_messages(history, message)

    thinking_content = ""
    answer_content = ""

    async for event in agent_service.astream(messages, task_id):
        if event["type"] == "thinking_chunk":
            thinking_content += event["content"]
            yield [
                gr.ChatMessage(
                    role="assistant",
                    content=thinking_content,
                    metadata={"title": "Reasoning", "status": "thinking"},
                )
            ]
        elif event["type"] == "answer_chunk":
            answer_content += event["content"]
            # yield thinking (done) + answer (streaming) as a pair
            msgs = []
            if thinking_content:
                msgs.append(gr.ChatMessage(
                    role="assistant",
                    content=thinking_content,
                    metadata={"title": "Reasoning", "status": "done"},
                ))
            msgs.append(gr.ChatMessage(role="assistant", content=answer_content))
            yield msgs
        elif event["type"] == "done":
            # state save: persist final AgentResponse to DB via LangGraphService
            await lang_graph_service.save_turn(message, event["response"])
```

**SEO Coach** (`handle_submit`): same pattern — `yield` the updated history list with `gr.ChatMessage` objects on each chunk.

**Key architectural note:** The UI streams directly from `AgentService` for responsiveness. State is persisted via `LangGraphService.save_turn()` on the `"done"` event — after the stream completes. This is a deliberate split: stream path for UX, workflow path for persistence.

`to_chat_message()` in `message_converter.py` is unchanged — `metadata` passthrough already handles `status` and `title`.

### Step 6: `response_metadata` passthrough
**File:** `src/agent_workbench/models/consolidated_state.py` / workflow response builder

- `AgentResponse.status` → `response_metadata["status"]` → `ConsolidatedWorkflowResponse.response_metadata`
- Already wired in PR-08b; ensure the new agent path populates it on `save_turn()`

### Step 7: Tests
**New file:** `tests/unit/services/test_agent_service.py`

- `AgentService` instantiates without error (mocked `create_agent`)
- `run()` calls `ainvoke` with task-scoped `thread_id`; never uses `conversation_id` as `thread_id`
- `astream()` yields typed event dicts in order: `thinking_chunk*`, `answer_chunk+`, `done`
- `astream()` omits `thinking_chunk` events for non-Anthropic providers
- Thinking block extraction: `content_blocks` with `type="thinking"` → `thinking_chunk` events
- `"done"` event carries a valid `AgentResponse`
- Fallback: provider without `create_agent` support → falls back to direct `model.astream()`

**Update:** `tests/unit/services/test_langgraph_bridge.py` — `_get_conversation_history()` now returns messages (previously stubbed empty)

**Update:** `tests/unit/ui/test_message_converter.py` — verify `status="thinking"` and `status="done"` pass through `to_chat_message()` correctly (already covered by existing metadata key tests; confirm no gaps)

---

## Files Touched

| File | Change |
|---|---|
| `src/agent_workbench/services/agent_service.py` | **NEW** — `AgentResponse`, `AgentService` |
| `src/agent_workbench/services/workflow_nodes.py` | Inject `AgentService`; `generate_response_node` delegates to agent |
| `src/agent_workbench/services/langgraph_bridge.py` | `load_conversation_node` populates history from DB via `StateManager` |
| `src/agent_workbench/services/llm_service.py` | `chat()` removed; wire `_get_conversation_history()` to DB; add `standard_to_lc()`; `ChatService` trimmed to model instantiation + `get_model()` |
| `src/agent_workbench/services/langgraph_service.py` | Rename class `WorkbenchLangGraphService` → `LangGraphService`; add `save_turn()` for post-stream state persistence |
| `src/agent_workbench/services/workflow_orchestrator.py` | **RETIRED** — deleted |
| `src/agent_workbench/services/simple_chat_workflow.py` | **RETIRED** — deleted; chatting is agent execution |
| `src/agent_workbench/main.py` | Instantiate `AgentService` + `LangGraphService`; remove retired services |
| `src/agent_workbench/api/routes/chat_workflow.py` | Both modes route to `LangGraphService` |
| `src/agent_workbench/ui/pages/chat.py` | Workbench handler returns `[thinking_msg, answer_msg]` when reasoning present |
| `tests/unit/services/test_agent_service.py` | **NEW** — AgentService unit tests |
| `tests/unit/services/test_langgraph_bridge.py` | Update history tests (no longer empty stub) |
| `docs/project/BACKLOG.md` | Mark Phase 2.0 done |

---

## Verification

```bash
# After Step 1 — agent service alone
uv run pytest tests/unit/services/test_agent_service.py -v

# After all steps
make pre-commit                         # mypy, ruff, black, pytest
make start-app                          # Workbench: tokens stream in as they arrive, not batch

# Verify multi-turn history
# Send message 1: "My name is Sytse"
# Send message 2: "What's my name?"
# Agent should answer "Sytse" — proves history is loaded from DB

# Verify thinking tokens (Anthropic provider)
# Enable extended thinking via model config (if exposed)
# → Should see collapsible "Reasoning" block above the answer in the chatbot

# Verify SEO Coach — same execution path, mode handler still produces Dutch responses
APP_MODE=seo_coach make start-app       # send "kun je mijn website analyseren?" → Dutch response, coaching phase = "analysis"

# Smoke tests
uv run pytest tests/smoke/ -v
```

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `langchain.agents.create_agent` API differs from what's documented in `phase2_architecture_plan.md` (written Oct 2025, plan was anticipating v1 release) | Verify import and signature against installed 1.2.10 in Step 1; adjust if needed |
| Extended thinking only available for specific Anthropic models (claude-3-7-sonnet+) | Guard with `if hasattr(result, "thinking_blocks")`; non-thinking providers skip gracefully |
| `gr.ChatInterface` may not accept a list return — only single `gr.ChatMessage` | Test in Step 5; fallback: prepend thinking as content with a separator |
| History wiring introduces latency (now loading all messages per turn) | Paginate: load last N messages (configurable, default 20) |
| `WorkflowOrchestrator` deletion may have hidden dependents | Grep all imports before deleting; `test_workflow_orchestrator.py` tests must be migrated or removed |

---

## Out of Scope (explicitly deferred)

- `simple_chat_workflow.py` removal — stays as test/debug endpoint
- `auth_service.py`, `user_settings_service.py` — Phase 3
