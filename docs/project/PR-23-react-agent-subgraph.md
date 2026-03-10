# PR-2.3: LangGraph ReAct Agent Sub-Graph

**Branch:** `feature/react-agent-subgraph`
**Status:** Planning
**Depends on:** PR-2.2b (merged)
**Precedes:** PR-2.4 (ContentRetriever — first tool wired through this graph)

---

## Problem

The current workflow is a linear pipeline with the LLM call buried four levels deep:

```
consolidated_service.stream_workflow()
  → agent_service.astream()
      → model.astream()           ← bare model call, no tool loop
```

```
langgraph_service.execute_workflow()
  → process_workbench node
      → mode_handler.process_message()
          → agent_service.run()
              → model.ainvoke()   ← bare model call, no tool loop
```

Three structural gaps prevent tool use:

**1. State — no reducer on `conversation_history`**
`WorkbenchState` uses a plain `List[StandardMessage]` field. In a ReAct loop,
each node that writes to the message list **overwrites** the previous value.
`ToolMessage` objects (tool results) would erase the prior conversation.
LangGraph's `add_messages` reducer accumulates instead of overwrites.

**2. Nodes — no tool execution node**
No node exists to execute `tool_calls` from an `AIMessage` and inject
`ToolMessage` results back into the message list. Even if the model signals
a tool call, nothing runs it.

**3. Edges — no cycle**
The graph has no back-edge. A ReAct loop requires:
```
llm_node → (tool_calls?) → tool_node → llm_node  (repeat until done)
```
The current graph flows linearly to `END` with no feedback path.

---

## Solution: Option C — Inner Agent Sub-Graph

Keep the outer `WorkbenchState` pipeline for orchestration (load conversation,
detect mode, save state, handle errors) unchanged. Add a self-contained inner
`AgentGraph` that handles the LLM ↔ tool loop using LangGraph's `MessagesState`.

```
Outer graph (WorkbenchState — orchestration):
  load → validate → detect_mode → [inner AgentGraph] → save → END

Inner graph (MessagesState — ReAct loop):
  llm_node → (tool_calls?) → tool_node → llm_node → ... → END
```

The outer graph does not need to know about tools. `WorkbenchState` does not
change. The inner graph owns `MessagesState` with `add_messages` reducer and
handles `AIMessage.tool_calls` + `ToolMessage` natively.

**Why this is the right split:**
- Orchestration concerns (mode detection, persistence, error handling) stay in
  `LangGraphService` and `WorkbenchState`
- Agent concerns (LLM calls, tool execution, looping) stay in `AgentGraph`
  and `MessagesState`
- Adding a new tool in PR-2.4+ requires only passing it to `AgentGraph` — no
  changes to the outer pipeline

**Key observation:** Mode handlers (`_build_workbench_messages()`,
`_build_coaching_messages()`) already return `list[BaseMessage]` — LangChain
native types. `AgentGraph` takes these directly as its initial `messages`.
No format conversion needed.

---

## Scope

**IN:**
- `services/agent_graph.py` (NEW): `AgentGraph` class — inner sub-graph with
  `MessagesState`, `llm_node`, `ToolNode`, conditional edge + back-edge
- `services/consolidated_service.py`: streaming path uses
  `AgentGraph.astream_events()` instead of `AgentService.astream()`
- `services/langgraph_service.py`: batch path calls `AgentGraph.ainvoke()`
  instead of `AgentService.run()` inside mode handler nodes
- `models/consolidated_state.py`: add `active_tools: List[str]` to
  `ConsolidatedWorkflowRequest` (tool names resolved to instances in service)

**OUT:**
- No tools wired yet — `AgentGraph` runs with `tools=[]` in this PR,
  identical in behaviour to the current `AgentService` path
- `WorkbenchState` is NOT changed (this is the point of Option C)
- `AgentService.run()` / `astream()` are NOT deleted — keep for compatibility
  and as fallback; deprecate in a later PR

---

## Architecture

### State

`AgentGraph` uses LangGraph's `MessagesState` internally:

```python
from langgraph.graph import MessagesState

# MessagesState provides:
# messages: Annotated[list[BaseMessage], add_messages]
# add_messages reducer: accumulates across loop iterations,
#   handles ID deduplication, deserialises message dicts
```

`WorkbenchState` in the outer graph is unchanged. The inner graph receives
`list[BaseMessage]` (prepared by mode handlers) as its initial state and
returns the final `AIMessage` to the outer graph as `assistant_response`.

### Nodes

```python
# llm_node: call the model with current messages
async def llm_node(state: MessagesState) -> dict:
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}   # add_messages reducer appends

# tool_node: LangGraph's built-in ToolNode
# - reads tool_calls from last AIMessage
# - executes each tool (sync or async)
# - returns ToolMessage objects via add_messages
from langgraph.prebuilt import ToolNode
tool_node = ToolNode(tools)
```

`ToolNode` is LangGraph's built-in tool execution node. It handles tool lookup
by name, sync/async execution, and `ToolMessage` construction automatically.
No manual tool dispatch needed.

### Edges

```python
from langgraph.graph import END

def should_continue(state: MessagesState) -> str:
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tool_node"
    return END

builder.add_conditional_edges("llm_node", should_continue)
builder.add_edge("tool_node", "llm_node")   # loop back
```

When `tools=[]`, `should_continue` always returns `END` — the graph terminates
after one LLM call. No performance cost, identical behaviour to current code.

### `AgentGraph` class

```python
class AgentGraph:
    """Inner ReAct agent sub-graph.

    Self-contained LLM ↔ tool loop using MessagesState. Stateless by design
    — compiled graph is built per call with the tool set for that turn.

    Usage:
        graph = AgentGraph(model_config)
        # Batch
        result = await graph.ainvoke(messages, tools=[])
        # Streaming
        async for event in graph.astream_events(messages, tools=[]):
            ...
    """

    def __init__(self, model_config: ModelConfig) -> None:
        self._model_config = model_config

    def _build(self, tools: list) -> CompiledStateGraph:
        model = provider_registry.create_model(self._model_config)
        if tools:
            model = model.bind_tools(tools)

        async def llm_node(state: MessagesState) -> dict:
            response = await model.ainvoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: MessagesState) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tool_node"
            return END

        builder = StateGraph(MessagesState)
        builder.add_node("llm_node", llm_node)
        builder.add_conditional_edges("llm_node", should_continue)

        if tools:
            builder.add_node("tool_node", ToolNode(tools))
            builder.add_edge("tool_node", "llm_node")

        builder.set_entry_point("llm_node")
        return builder.compile()

    async def ainvoke(
        self, messages: list[BaseMessage], tools: list = []
    ) -> BaseMessage:
        """Batch invocation. Returns final AIMessage."""
        graph = self._build(tools)
        result = await graph.ainvoke({"messages": messages})
        return result["messages"][-1]

    async def astream_events(
        self, messages: list[BaseMessage], tools: list = []
    ) -> AsyncIterator[dict]:
        """Stream events from the agent loop.

        Yields LangGraph v2 events. Callers filter by event name:
          on_chat_model_stream → token chunks (answer_chunk / thinking_chunk)
          on_tool_start        → tool call starting (PR-2.4)
          on_tool_end          → tool call completed (PR-2.4)
        """
        graph = self._build(tools)
        async for event in graph.astream_events(
            {"messages": messages}, version="v2"
        ):
            yield event
```

### `consolidated_service.py` — streaming path

Replace `agent_service.astream()` with `agent_graph.astream_events()`:

```python
# Before
async for event in self.agent_service.astream(messages_dicts, ...):
    yield event

# After
messages = handler.build_messages(state)   # already list[BaseMessage]
async for event in self.agent_graph.astream_events(messages, tools=tools):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        # same content_blocks logic as before
        for block in chunk.content_blocks:
            ...
```

The SSE event types emitted to the UI are unchanged: `thinking_chunk`,
`answer_chunk`, `done`, `processing_file`. The source of the chunks changes
from `model.astream()` to LangGraph's `on_chat_model_stream` events, but the
content is identical.

### `langgraph_service.py` — batch path

Replace `agent_service.run()` inside mode handler nodes:

```python
# process_workbench node (and seo_coach equivalent)
async def _process_workbench_node(self, state: WorkbenchState) -> WorkbenchState:
    messages = await self.workbench_handler._build_workbench_messages(state)
    result = await self.agent_graph.ainvoke(messages, tools=[])
    return {**state, "assistant_response": result.content}
```

---

## Step-by-Step Implementation

### Step 1: Create `services/agent_graph.py`

Implement `AgentGraph` as shown above. Imports:

```python
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage
from .providers import provider_registry
from ..models.schemas import ModelConfig
```

### Step 2: Update `consolidated_service.py`

- Add `self.agent_graph: Optional[AgentGraph] = None` to `__init__`
- In `initialize()`: `self.agent_graph = AgentGraph(self.default_model_config)`
- In `stream_workflow()`: replace `agent_service.astream()` loop with
  `agent_graph.astream_events()` — filter `on_chat_model_stream` events and
  apply the same `content_blocks` + `_split_think_tags` logic
- Resolve `active_tools` strings to tool instances here (empty list for now)

### Step 3: Update `langgraph_service.py`

- Accept `agent_graph: AgentGraph` in `__init__`
- In `_process_workbench_node` and `_process_seo_coach_node`: call
  `agent_graph.ainvoke(messages, tools=[])` instead of going through mode
  handler's `agent_service.run()`

### Step 4: Update `main.py`

```python
from .services.agent_graph import AgentGraph
agent_graph = AgentGraph(default_model_config)
# Pass to consolidated_service.initialize() and LangGraphService
```

### Step 5: Tests

**`tests/unit/services/test_agent_graph.py`** (NEW):

- `AgentGraph._build(tools=[])` compiles without error
- `AgentGraph._build(tools=[mock_tool])` binds tools to model
- `ainvoke()` returns final `AIMessage`
- `ainvoke()` with no tools terminates after one LLM call (no loop)
- `ainvoke()` with mock tool: model returns tool_call → tool executes →
  `ToolMessage` injected → second LLM call → final `AIMessage`
- `astream_events()` yields `on_chat_model_stream` events
- `should_continue()` returns `END` when no tool_calls on last message
- `should_continue()` returns `"tool_node"` when tool_calls present

**Update `tests/unit/services/test_consolidated_service.py`:**
- Streaming path emits same SSE events (`answer_chunk`, `done`) as before

---

## Files Touched

| File | Change |
|---|---|
| `src/agent_workbench/services/agent_graph.py` | **NEW** — `AgentGraph` inner sub-graph |
| `src/agent_workbench/services/consolidated_service.py` | Streaming uses `agent_graph.astream_events()` |
| `src/agent_workbench/services/langgraph_service.py` | Batch nodes call `agent_graph.ainvoke()` |
| `src/agent_workbench/main.py` | Instantiate `AgentGraph`, inject into services |
| `tests/unit/services/test_agent_graph.py` | **NEW** |
| `tests/unit/services/test_consolidated_service.py` | Update streaming path tests |

No DB changes. No API changes. No UI changes. `WorkbenchState` unchanged.

---

## Verification

```bash
make pre-commit   # all checks must pass

# Behaviour must be identical to pre-PR:
make start-app
# Submit a message → response streams correctly
# Thinking bubble appears for Anthropic/Qwen models as before
# File upload → document processed → context injected → response correct
```

The graph runs with `tools=[]` — behaviour is identical to the current
`AgentService` path. The only observable change is internal routing.

---

## Relation to PR-2.4 (ContentRetriever)

PR-2.4 (formerly PR-2.3) adds `ContentRetrieverTool` as the first real tool.
With this PR in place, wiring it requires one change:

```python
# In consolidated_service.stream_workflow() / langgraph_service nodes:
tools = [ContentRetrieverTool(conversation_id=..., ...)]
await agent_graph.ainvoke(messages, tools=tools)
```

And two additions to `message_converter.py`:

```python
"tool_call":   ("🔍", "Retrieving", "Ophalen"),
"tool_result": ("📋", "Result",     "Resultaat"),
```

No changes to `AgentGraph` itself.
