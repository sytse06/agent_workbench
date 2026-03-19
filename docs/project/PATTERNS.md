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
