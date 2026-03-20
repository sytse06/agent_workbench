# Patterns: Agent Workflow + SKILLS.md

Reference for recreating the two core patterns built in PR-2.4 and PR-2.5.
Copy-paste starting points for any LangGraph project that needs tools with context isolation.

---

## Pattern 1 — Tool with Context Isolation (Subgraph)

### The problem it solves

A tool needs to fetch a large amount of data (documents, web content) and answer a focused
question about it. Dumping the raw data into `MessagesState` inflates the context window and
leaks retrieval internals into the conversation history.

### The solution

The tool runs an inner `StateGraph` (no checkpointer) that does all the heavy work. Only the
synthesized answer crosses back into `MessagesState` as a `ToolMessage`.

```
AgentGraph (outer)                              MessagesState
  ToolNode → MyTool._arun(query, config)
               │
               └── MySubGraph.ainvoke(query, conv_id)
                     │
                     ├── fetch_node       ← DB / API call, large raw data
                     ├── embed_chunks_node ← embeddings (never leave subgraph)
                     ├── retrieve_node    ← cosine select + LLM synthesis
                     │
                     └── returns: "The answer is X because Y."  ──→  ToolMessage
```

### Minimal implementation

**State (TypedDict, total=False so nodes return partial updates):**

```python
class MySubgraphState(TypedDict, total=False):
    query: str
    conversation_id: str
    chunks: list          # list[RetrievedChunk] — stays inside subgraph
    chunk_embeddings: list
    answer: str
```

**Graph (compiled without checkpointer):**

```python
class MySubGraph:
    def __init__(self, semantic_retriever: SemanticRetriever, model_config: ModelConfig):
        self._retriever = semantic_retriever
        self._model_config = model_config
        self._graph = self._build()

    def _build(self) -> CompiledStateGraph:
        retriever = self._retriever

        async def fetch_node(state): ...         # returns {"chunks": [...]}
        async def embed_chunks_node(state): ...  # returns {"chunk_embeddings": [...]}
        async def retrieve_node(state): ...      # returns {"answer": "..."}

        builder = StateGraph(MySubgraphState)
        builder.add_node("fetch", fetch_node)
        builder.add_node("embed_chunks", embed_chunks_node)
        builder.add_node("retrieve", retrieve_node)
        builder.set_entry_point("fetch")
        builder.add_edge("fetch", "embed_chunks")
        builder.add_edge("embed_chunks", "retrieve")
        builder.add_edge("retrieve", END)
        return builder.compile()          # no checkpointer

    async def ainvoke(self, query: str, conversation_id: str) -> str:
        result = await self._graph.ainvoke(
            {"query": query, "conversation_id": conversation_id}
        )
        return result.get("answer", "No answer produced.")
```

**Tool wrapper:**

```python
class MyTool(BaseTool):
    name: str = "my_tool"
    description: str = "..."          # what the agent sees
    args_schema: Type[BaseModel] = MyToolInput

    _graph: Any = None

    def __init__(self, graph: Any, description: str, **data):
        super().__init__(description=description, **data)
        object.__setattr__(self, "_graph", graph)   # Pydantic v2 private attr

    def _run(self, query: str, **kwargs) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(self, query: str, config: Optional[RunnableConfig] = None, **kwargs) -> str:
        conversation_id = (config or {}).get("configurable", {}).get("thread_id", "")
        if not conversation_id:
            return "No active conversation."
        return await self._graph.ainvoke(query, conversation_id)
```

**Wire into AgentGraph at compile time:**

```python
graph = MySubGraph(semantic_retriever, model_config)
tool = MyTool(graph=graph, description="...")
agent = AgentGraph(model_config, tools=[tool], checkpointer=checkpointer)
```

### Multi-turn caching

Avoid re-fetching or re-embedding on follow-up questions about the same source:

```python
# Module-level — survives across requests within one process
_chunk_cache:     dict[str, dict[str, list]] = {}   # conv_id → key → chunks
_embedding_cache: dict[str, dict[str, list]] = {}   # conv_id → key → embeddings

# In fetch_node:
if conv_id in _chunk_cache and key in _chunk_cache[conv_id]:
    return {"chunks": _chunk_cache[conv_id][key]}   # cache hit
# ... fetch, chunk, then:
_chunk_cache.setdefault(conv_id, {})[key] = chunks

# In embed_chunks_node:
if conv_id in _embedding_cache and key in _embedding_cache[conv_id]:
    return {"chunk_embeddings": _embedding_cache[conv_id][key]}
# ... embed, then:
_embedding_cache.setdefault(conv_id, {})[key] = embeddings
```

Cache key = URL for scrape/crawl/extract; query string for search.

---

## Pattern 2 — Hierarchical Skill Routing via SKILLS.md

### The problem it solves

A single domain (e.g. "web research") has multiple execution methods (scrape, search, crawl,
extract). Exposing all four as separate tools floods the agent's tool list with similar-looking
options, making routing unreliable. But putting them all in one tool's description string mixes
tool-selection metadata with execution instructions.

### The solution

One tool per domain. The tool's description (what the agent sees) comes from YAML frontmatter
in a `SKILLS.md` file. The catalog of sub-skills (what the inner LLM uses to route) is the
file body — it never leaves the subgraph state.

### SKILLS.md format

```markdown
---
name: my_domain
description: "One sentence. What the agent should call this tool for. Include NOT-fors."
---

# My Domain Skills

## skill_one
When to use this specific method. Positive signal.
NOT for X (use skill_two). NOT for Y.

## skill_two
When to use this one instead.
NOT when a URL is known (use skill_one).

## skill_three
...
```

Rules:
- `name` must match a handler in `_build_domain_tool()`
- `description` is the exact string the agent reads as `tool.description`
- Each `## heading` is one routable skill
- Keep the catalog tight — the match_skill LLM call should be cheap and deterministic
- NOT-fors are important: they prevent routing collisions between similar skills

### Directory layout

```
skills/
├── shared/           ← loaded for all APP_MODE values
│   └── web_research/
│       └── SKILLS.md
└── workbench/        ← loaded only when APP_MODE=workbench (overrides shared)
    └── code_execution/
        └── SKILLS.md
```

Mode-specific directories override shared on name clash. Adding a new domain = adding a
directory + SKILLS.md + one handler in `_build_domain_tool()`. No other code changes.

### SkillLoader

```python
@dataclass
class SkillDefinition:
    name: str            # from frontmatter
    description: str     # from frontmatter → tool.description
    skills_catalog: str  # file body → subgraph state only

class SkillLoader:
    def __init__(self, skills_root: Path): ...

    def build_tools(
        self,
        mode: str,                          # "workbench" | "seo_coach"
        model_config: ModelConfig,
        semantic_retriever: SemanticRetriever,
        external_client: Optional[Any] = None,
    ) -> list[BaseTool]:
        # 1. load shared/ + skills/{mode}/, last-wins on name clash
        # 2. for each SkillDefinition, call _build_domain_tool()
        # 3. return list of BaseTool instances
```

### Subgraph that uses the catalog

The `skills_catalog` (SKILLS.md body) is loaded as the first node so it's available in state
for the `match_skill` LLM call:

```
load_skills_node    ← {"skills_catalog": body}  (pure, no I/O)
      ↓
match_skill_node    ← LLM prompt: catalog + query → one skill name
      ↓
execute_node        ← dispatch to external API based on matched_skill
      ↓
embed_chunks_node   ← SemanticRetriever.embed_chunks()
      ↓
retrieve_node       ← cosine select → LLM synthesis → answer
```

**match_skill_node prompt pattern:**

```python
SystemMessage(
    "You are a skill router. Given a user query and a skills catalog, "
    "respond with ONLY the skill name that best matches. "
    f"Valid values: {', '.join(sorted(VALID_SKILLS))}"
)
HumanMessage(
    f"Skills catalog:\n{state['skills_catalog']}\n\n"
    f"Query: {state['query']}\n"
    f"URL provided: {state.get('url') or 'none'}"
)
# Parse: strip + lower + validate against VALID_SKILLS set, fallback to "search"
skill = str(response.content).strip().lower()
matched = skill if skill in VALID_SKILLS else "search"
```

### Context isolation summary

| Layer | What it contains | Enters MessagesState? |
|---|---|---|
| `tool.description` | One-sentence domain description | Yes (agent reads it) |
| `skills_catalog` | Sub-skill instructions | No — subgraph state only |
| `matched_skill` | e.g. `"scrape"` | No — subgraph state only |
| Raw API response | Full page/search markdown | No — subgraph state only |
| Chunk embeddings | N × 384 floats | No — module-level cache only |
| Synthesized answer | Focused prose with citations | Yes — ToolMessage only |

### Graceful degradation

```python
api_key = os.getenv("MY_DOMAIN_API_KEY")
if api_key:
    client = MyDomainClient(api_key)
    tools = skill_loader.build_tools(..., external_client=client)
else:
    logger.warning("MY_DOMAIN_API_KEY not set — my_domain skill disabled")
    tools = []

agent = AgentGraph(model_config, tools=[*other_tools, *tools], checkpointer=...)
```

When `external_client=None`, the execute_node returns a clear message string instead of
raising — the synthesis LLM tells the user the capability is unavailable.

---

## SemanticRetriever — shared retrieval pipeline

Both patterns above use the same retrieval pipeline. Extract it once, share it everywhere.

```python
class SemanticRetriever:
    def __init__(self, embedding_service: EmbeddingService): ...

    def chunk_text(self, text: str, filename: str, chunk_size: int = 512) -> list[RetrievedChunk]:
        """Split raw text into RetrievedChunk objects."""

    async def embed_chunks(self, chunks: list[RetrievedChunk]) -> list[list[float]]:
        """embed_batch in asyncio.to_thread (CPU-bound)."""

    async def embed_query(self, query: str) -> list[float]:
        """Single embed call in asyncio.to_thread."""

    def select(
        self,
        query_vec: list[float],
        chunks: list[RetrievedChunk],
        embeddings: list[list[float]],
        budget: int = 16_000,           # token budget before synthesis LLM
    ) -> list[RetrievedChunk]:
        """Cosine similarity → top-K within token budget → restore document order."""
```

Create one singleton at service startup, pass it into every subgraph constructor:

```python
_embedding_service = EmbeddingService()          # lazy-loads model on first call
_semantic_retriever = SemanticRetriever(_embedding_service)
```

---

---

## Pattern 3 — Ephemeral Per-Request Data via AgentContext

### The problem it solves

Some data needs to reach every LLM call inside the agent graph but must NOT be stored in
the checkpointer — it changes between turns (e.g. long-term memory snapshots), is
re-derived fresh each invocation, or is caller-side context that doesn't belong in
conversation history.

Injecting it as a real message (HumanMessage / SystemMessage) would store it in
`MessagesState` and corrupt the conversation record. Passing it via global state is fragile.

### The solution

Use LangGraph's `context_schema` to define a per-invocation dataclass. Fields are injected
at call time via `runtime.context` inside any node — they never enter `MessagesState` and are
never checkpointed.

```python
from dataclasses import dataclass, field
from langgraph.runtime import Runtime

@dataclass
class AgentContext:
    model_config: ModelConfig
    memory_context: str = ""   # ephemeral — fresh every turn, never stored

# In llm_node (inside _build()):
async def llm_node(state: MessagesState, runtime: Runtime) -> dict:
    messages = list(state["messages"])
    if runtime.context.memory_context:
        messages = [SystemMessage(content=runtime.context.memory_context)] + messages
    model = provider_registry.create_model(runtime.context.model_config)
    response = await model.ainvoke(messages)
    return {"messages": [response]}   # only the AIMessage enters MessagesState

# In _build():
builder = StateGraph(MessagesState, context_schema=AgentContext, ...)
```

**Call site** — pass context at invocation time, not at compile time:

```python
await graph.astream(
    {"messages": messages},
    config={"configurable": {"thread_id": thread_id}},
    context={"model_config": model_config, "memory_context": memory_content},
    ...
)
```

### When to use this pattern

| Data | Put in MessagesState? | Put in AgentContext? |
|---|---|---|
| User / assistant messages | Yes | No |
| Tool call results | Yes (ToolMessage) | No |
| LLM model config (changes per request) | No | Yes |
| Long-term memory snapshot | No — changes every turn | Yes |
| PII-redacted version of a message | No — use separately | Yes |
| Feature flags for this invocation | No | Yes |

---

## Pattern 4 — Store Tool via InjectedStore + RunnableConfig

### The problem it solves

A tool needs to write to the LangGraph `Store` using a per-request namespace key
(e.g. `session_id` or `user_id`). The key is not known at graph compile time and
must not be hardcoded into the tool. The tool also needs the `Store` instance injected
without coupling to module-level globals.

### The solution

LangGraph's `InjectedStore` injects the compiled graph's store into the tool at call
time. `RunnableConfig` carries per-invocation context (like `session_id`) via the
`configurable` dict. Both are available as function parameters and are invisible to the
LLM (the agent never sees them in the tool signature).

```python
from typing import Annotated
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

@tool
async def update_memory(
    key: Annotated[str, "Memory key: 'agents' or 'domain_context'"],
    content: Annotated[str, "Full new file content (replaces existing)."],
    config: RunnableConfig,                         # injected — LLM never sees this
    store: Annotated[BaseStore, InjectedStore()],   # injected — LLM never sees this
) -> str:
    """Update a long-term memory file about this user."""
    session_id = (config.get("configurable") or {}).get("session_id", "anonymous")
    await store.aput((session_id, "memories"), key, {"content": content})
    return f"Memory '{key}' updated."
```

**Wire it** — compile the graph with the store; pass `session_id` in the config:

```python
# At startup (once):
agent = AgentGraph(model_config, tools=[update_memory], checkpointer=checkpointer, store=store)

# Per request:
await agent.astream(messages, thread_id=thread_id, session_id=session_id)
# _config() sets: {"configurable": {"thread_id": ..., "session_id": ...}}
```

**Read side** — read before the graph runs and pass via `AgentContext`, not via the Store inside the graph:

```python
# In consolidated_service.stream_workflow():
agents_mem = await read_memory(store, session_id, "agents")
domain_mem = await read_memory(store, session_id, "domain_context")
memory_context = build_memory_prefix(agents_mem, domain_mem)  # string or ""

await agent_graph.astream(..., session_id=session_id, memory_context=memory_context)
```

This keeps read and write paths decoupled: reads are explicit and happen before the graph
runs (Pattern 3 delivers the result); writes are agent-initiated tool calls during the run.

### Key rules

- `InjectedStore` and `RunnableConfig` parameters must come AFTER the parameters the LLM fills
- The tool's docstring + annotated `key`/`content` params are what the LLM sees — keep them tight
- The graph must be compiled with `store=store`; otherwise `InjectedStore` injects `None`
- `session_id` travels in `config["configurable"]`, same dict as `thread_id`

---

## Pattern 5 — Minimal Session Identity (BrowserState UUID)

### The problem it solves

A feature needs a stable per-user namespace key (e.g. for LangGraph Store) but full
OAuth is not yet available. Building a full auth system just for a namespace key is
over-engineering — the session only needs to be stable within one browser.

### The solution

`gr.BrowserState` persists a value in `localStorage`. Generate a UUID on first page
load; return it unchanged on subsequent loads. The UUID becomes the namespace key.

```python
# In chat.render() — workbench block:
session_id_state = gr.BrowserState("", storage_key="aw_session_id")

# In mode_factory_v2.py — after chat.render():
@demo.load(inputs=[session_id_state], outputs=[session_id_state])
def _init_session_id(current_id: str) -> str:
    from uuid import uuid4
    return current_id if current_id else str(uuid4())
```

Pass it through the API as a request field:

```python
# handle_chat_interface_message → payload:
if session_id:
    payload["session_id"] = session_id   # → ConsolidatedWorkflowRequest.session_id
```

### Phase 3 migration path

When HF OAuth lands, replace the BrowserState source with the authenticated user ID.
Nothing downstream changes — the Store namespace key is still just a string.

### Limitations

| Property | BrowserState UUID |
|---|---|
| Survives page refresh | Yes (localStorage) |
| Survives browser cache clear | No — new UUID generated |
| Cross-device | No |
| Tied to identity | No |
| Cost | ~10 lines, zero infrastructure |

---

---

## Pattern 6 — HITL via interrupt() (not interrupt_before=)

### The problem it solves

The spec for PR-2.6e originally listed `interrupt_before=["tool_node"]` as the HITL
mechanism. This is a compile-time graph config that stops before **every** tool call,
unconditionally, with no ability to pass context to the UI or apply conditions.

### The correct pattern

Call `interrupt()` **inside a node**. It pauses the graph, passes a payload to the
caller (e.g. the Gradio UI), and resumes cleanly when the caller reinvokes with a
response. It's conditional — fire it only when human review is needed.

```python
from langgraph.types import interrupt

def review_node(state):
    last_tool_call = state["messages"][-1].tool_calls[0]

    # Only interrupt for high-risk tools, not every call
    if last_tool_call["name"] in HIGH_RISK_TOOLS:
        response = interrupt({
            "tool": last_tool_call["name"],
            "args": last_tool_call["args"],
            "action": "approve_or_reject",
        })
        if response.get("approved"):
            return {"approved": True}
        return {"approved": False, "reason": response.get("reason")}

    return {"approved": True}   # auto-approve low-risk tools
```

**Wire it** — add the node between `llm_node` and `tool_node`:

```python
builder.add_node("review_node", review_node)
builder.add_conditional_edges(
    "llm_node", should_continue,
    {"review_node": "review_node", END: END}
)
builder.add_conditional_edges(
    "review_node",
    lambda s: "tool_node" if s.get("approved") else END,
    {"tool_node": "tool_node", END: END},
)
```

**Resume** — the caller reinvokes the graph with the human response:

```python
# Initial call — pauses at interrupt
result = await graph.ainvoke(input, config=config)
# result contains the interrupt payload

# Human reviews, then resume:
final = await graph.ainvoke({"approved": True}, config=config)
```

### interrupt_before= vs interrupt() comparison

| | `interrupt_before=["tool_node"]` | `interrupt()` inside a node |
|---|---|---|
| When it fires | Every tool call, always | Conditionally — you decide |
| Payload to UI | None | Any dict you want |
| Resume input | None (just reinvoke) | Dict returned from `interrupt()` |
| Compile-time | Yes — baked in at build | No — runtime logic |
| Use case | Blanket approval gate | Selective, context-aware review |

**Rule:** always use `interrupt()`. `interrupt_before=` is a blunt instrument.

**Requirement:** graph must be compiled with a checkpointer — `interrupt()` saves state
before pausing so the graph can resume from exactly that point.

---

## Pattern 7 — Multi-Agent via langgraph-supervisor / langgraph-swarm

### The problem it solves

Phase 4 requires orchestrating multiple specialist agents. Building a custom supervisor
or swarm routing mechanism from scratch is hundreds of lines of boilerplate.

### The solution

Use the official packages. Do not build from scratch.

```bash
pip install langgraph-supervisor langgraph-swarm
```

### Supervisor pattern (central orchestrator)

One LLM decides which specialist to call. Predictable, easier to debug.

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

model = ChatAnthropic(model="claude-sonnet-4-6")

web_agent = create_react_agent(
    model, tools=[web_research_tool],
    name="web_research", prompt="You handle web research tasks."
)
doc_agent = create_react_agent(
    model, tools=[document_retrieval_tool],
    name="document_retrieval", prompt="You handle document retrieval tasks."
)

workflow = create_supervisor(
    agents=[web_agent, doc_agent],
    model=model,
    prompt="Route web research to web_research, document tasks to document_retrieval.",
)
app = workflow.compile(checkpointer=checkpointer)
```

### Swarm pattern (peer-to-peer handoff)

Agents hand off to each other directly. More flexible, agents decide routing.

```python
from langgraph_swarm import create_handoff_tool, create_swarm

triage = create_react_agent(
    model,
    tools=[
        create_handoff_tool(agent_name="web_research"),
        create_handoff_tool(agent_name="document_retrieval"),
    ],
    name="triage",
    prompt="Route to the right specialist.",
)

app = create_swarm(
    [triage, web_agent, doc_agent],
    default_active_agent="triage",
).compile(checkpointer=checkpointer)
```

### When to use which

| Scenario | Use |
|---|---|
| Clear task hierarchy, one decision-maker | Supervisor |
| Agents know when to hand off | Swarm |
| Mix of structured pipeline + flexible routing | Hybrid (swarm within teams, supervisor between) |
| Our Phase 4 architecture | Evaluate at design time — both are viable |

---

## Pattern 8 — @task for Durable Side-Effects

### The problem it solves

A node performs a non-deterministic side-effect (API call, DB write, file write). If the
graph resumes from a checkpoint after a crash, the node runs again — causing double-writes
or duplicate API calls.

### The solution

Wrap the side-effect in `@task`. LangGraph records the result in the checkpoint after the
first execution and returns the cached result on any subsequent replay. The effect runs
exactly once per checkpoint.

```python
from langgraph.func import task

@task
async def write_to_store(store, namespace, key, content):
    """Runs once per checkpoint — safe to replay."""
    await store.aput(namespace, key, {"content": content})
    return True
```

### When it matters

| Scenario | Use @task? |
|---|---|
| Store write in a node (PR-2.6d UpdateMemoryTool) | Yes, if the graph may be interrupted mid-run |
| Sending an email / posting a webhook | Yes — idempotency critical |
| Pure LLM call (already deterministic via checkpointer) | No |
| DB reads | No — idempotent by nature |

### Current state in this codebase

`UpdateMemoryTool` in `memory_tools.py` does NOT currently use `@task`. This is acceptable
for Phase 2 (single-user, low crash risk). Add `@task` before Phase 4 when the graph runs
longer and crash-mid-run becomes a real concern.

---

## Checklist: adding a new skill domain

- [ ] Create `skills/shared/{domain_name}/SKILLS.md` (or `skills/{mode}/` for mode-specific)
- [ ] Write frontmatter: `name`, `description` (one sentence, include NOT-fors)
- [ ] Write skill catalog body: one `## heading` per routable method
- [ ] Add `VALID_SKILLS` set to the subgraph module
- [ ] Implement the subgraph: `load_skills → match_skill → execute → embed_chunks → retrieve`
- [ ] Implement the external client (or reuse existing)
- [ ] Add a handler branch in `SkillLoader._build_domain_tool()`
- [ ] Wire the API key check in `consolidated_service.initialize()`
- [ ] Write unit tests: `_parse_skills_md`, `build_tools`, dispatch routing, cache hit/miss,
      token budget trimming, no-key degradation
