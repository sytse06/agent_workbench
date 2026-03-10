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
- Adding a new tool in PR-2.4+ requires only passing it via context — no
  changes to the graph structure

**Key observation:** Mode handlers (`_build_workbench_messages()`,
`_build_coaching_messages()`) already return `list[BaseMessage]` — LangChain
native types. `AgentGraph` takes these directly as its initial `messages`.
No format conversion needed.

**Note on state type:** `WorkbenchState` (outer) and `MessagesState` (inner)
are both TypedDict-based — not Pydantic BaseModel. LangGraph docs explicitly
warn that Pydantic state is less performant and incompatible with
`create_agent`. TypedDict is the correct choice throughout.

---

## Scope

**IN:**
- `services/agent_graph.py` (NEW): `AgentGraph` class — inner sub-graph with
  `input_schema` / `output_schema` boundary, `context_schema` for runtime
  tool injection, `MessagesState`, `llm_node`, `ToolNode`, conditional
  back-edge
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

### State — three schemas

`AgentGraph` uses three schema layers:

```python
# 1. Input schema — what the outer graph passes in
class AgentInput(TypedDict):
    messages: list[BaseMessage]

# 2. Output schema — what the outer graph receives back
#    ToolMessage objects from the loop are NOT exposed — private to inner graph
class AgentOutput(TypedDict):
    messages: list[BaseMessage]   # contains only the final AIMessage

# 3. Internal state — full MessagesState with add_messages reducer
#    Accumulates all messages across the ReAct loop iterations
from langgraph.graph import MessagesState
# MessagesState provides:
#   messages: Annotated[list[BaseMessage], add_messages]

StateGraph(
    MessagesState,          # internal state with add_messages reducer
    input_schema=AgentInput,
    output_schema=AgentOutput,
)
```

The `input_schema` / `output_schema` boundary makes the sub-graph a clean
black box: the outer `WorkbenchState` pipeline only sees messages in and
messages out. All intermediate `ToolMessage` objects, partial `AIMessage`
tool-call responses, and loop state remain private inside the inner graph.

### Context schema — compile once, inject tools at call time

Rather than rebuilding the compiled graph on every turn (the naive approach),
`context_schema` injects tools and model config at invocation time into a
**single compiled graph singleton**:

```python
from dataclasses import dataclass, field
from langgraph.types import Runtime

@dataclass
class AgentContext:
    model_config: ModelConfig
    tools: list = field(default_factory=list)

StateGraph(MessagesState, context_schema=AgentContext, ...)
```

Inside `llm_node`, runtime context provides the model and tools:

```python
async def llm_node(
    state: MessagesState, runtime: Runtime[AgentContext]
) -> dict:
    model = provider_registry.create_model(runtime.context.model_config)
    if runtime.context.tools:
        model = model.bind_tools(runtime.context.tools)
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}
```

At call time:

```python
# Same compiled graph — different context per turn
await graph.ainvoke(
    {"messages": messages},
    context={"model_config": model_config, "tools": [content_retriever_tool]},
)
```

The graph is compiled once in `AgentGraph.__init__()` and reused for every
turn. Adding a tool in PR-2.4 requires no graph recompilation — only a
different `context.tools` list at call time.

### Nodes

```python
# llm_node: call the model using tools and model_config from context
async def llm_node(
    state: MessagesState, runtime: Runtime[AgentContext]
) -> dict:
    model = provider_registry.create_model(runtime.context.model_config)
    if runtime.context.tools:
        model = model.bind_tools(runtime.context.tools)
    response = await model.ainvoke(state["messages"])
    return {"messages": [response]}   # add_messages reducer appends

# tool_node: LangGraph's built-in ToolNode
# Built dynamically from context.tools — reads tool_calls from last AIMessage,
# executes each tool, returns ToolMessage objects via add_messages.
# When tools=[], this node is never reached (should_continue returns END).
```

`ToolNode` is LangGraph's built-in tool execution node. It handles tool lookup
by name, sync/async execution, and `ToolMessage` construction automatically.
No manual tool dispatch needed.

Note: `ToolNode` needs the tool list at graph build time, not via context.
The graph is therefore built with `ToolNode(tools)` where `tools` is passed
at construction. Since the context schema approach makes `AgentGraph` a
singleton compiled with no tools initially, PR-2.4 will evaluate whether
to keep the singleton pattern or compile per tool-set. For this PR,
`tools=[]` means `ToolNode` is never added to the graph.

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

    Self-contained LLM ↔ tool loop using MessagesState. Compiled once at
    init; tools and model config injected at invocation time via context_schema.

    Schema layers:
        input_schema=AgentInput   — messages in from outer graph
        output_schema=AgentOutput — final AIMessage out to outer graph
        context_schema=AgentContext — model_config + tools at call time
        internal: MessagesState  — add_messages reducer for loop accumulation

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
        self._graph = self._build()   # compiled once

    def _build(self) -> CompiledStateGraph:
        async def llm_node(
            state: MessagesState, runtime: Runtime[AgentContext]
        ) -> dict:
            model = provider_registry.create_model(runtime.context.model_config)
            if runtime.context.tools:
                model = model.bind_tools(runtime.context.tools)
            response = await model.ainvoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: MessagesState) -> str:
            last = state["messages"][-1]
            if hasattr(last, "tool_calls") and last.tool_calls:
                return "tool_node"
            return END

        builder = StateGraph(
            MessagesState,
            input_schema=AgentInput,
            output_schema=AgentOutput,
            context_schema=AgentContext,
        )
        builder.add_node("llm_node", llm_node)
        builder.add_conditional_edges("llm_node", should_continue)
        builder.set_entry_point("llm_node")
        return builder.compile()

    def _context(self, tools: list) -> dict:
        return {"model_config": self._model_config, "tools": tools}

    async def ainvoke(
        self, messages: list[BaseMessage], tools: list = []
    ) -> BaseMessage:
        """Batch invocation. Returns final AIMessage."""
        result = await self._graph.ainvoke(
            {"messages": messages},
            context=self._context(tools),
        )
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
        async for event in self._graph.astream_events(
            {"messages": messages},
            context=self._context(tools),
            version="v2",
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
messages = await handler._build_messages(state)   # already list[BaseMessage]
async for event in self.agent_graph.astream_events(messages, tools=tools):
    if event["event"] == "on_chat_model_stream":
        chunk = event["data"]["chunk"]
        # same content_blocks + _split_think_tags logic as before
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
from dataclasses import dataclass, field
from typing import AsyncIterator, List

from langgraph.graph import END, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Runtime
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict

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

- `AgentGraph._build()` compiles without error
- `AgentGraph._graph` is a singleton — same object on repeated access
- `ainvoke()` returns final `AIMessage`
- `ainvoke()` with `tools=[]` terminates after one LLM call
- `ainvoke()` passes model_config and tools via context to `llm_node`
- `astream_events()` yields `on_chat_model_stream` events
- `should_continue()` returns `END` when no tool_calls on last message
- `should_continue()` returns `"tool_node"` when tool_calls present
- Input/output schema: graph accepts `{"messages": [...]}` and returns same shape

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

PR-2.4 adds `ContentRetrieverTool` as the first real tool. With this PR in
place, wiring it requires passing the tool at call time — no graph recompilation:

```python
# In consolidated_service.stream_workflow() / langgraph_service nodes:
tools = [ContentRetrieverTool(conversation_id=..., ...)]
await agent_graph.ainvoke(messages, tools=tools)
# context={"model_config": ..., "tools": [tool]} — same compiled graph
```

PR-2.4 also evaluates whether `ToolNode` can be wired with tools from context
(currently it requires tools at build time). If not, the compile-once singleton
pattern gives way to a lightweight compile-per-tool-set approach for that PR.

And two additions to `message_converter.py`:

```python
"tool_call":   ("🔍", "Retrieving", "Ophalen"),
"tool_result": ("📋", "Result",     "Resultaat"),
```
