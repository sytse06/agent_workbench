# PR-2.5: WebResearch Skills

**Branch:** `feature/webresearch-skills`
**Sub-PRs:** 2.5a → 2.5b → 2.5c (sequential — each builds on the last)

---

## Problem

The agent has no way to access live web content. Firecrawl MCP exists in the developer
environment but is unavailable to the web app at runtime. This PR brings Firecrawl
capabilities into the agent as a first-class skill domain.

Two constraints drive the design:
1. Web content (especially crawl results) is too large for the synthesis LLM — it needs
   semantic retrieval, not raw dumping
2. Users ask multiple questions about a single web source — re-fetching on every question
   wastes API credits and latency

---

## Core Insight: Shared Retrieval Infrastructure

DocumentContextGraph (PR-2.4) and WebResearchGraph face the identical retrieval problem.
The data source differs; the pipeline is the same:

```
DocumentContextGraph          WebResearchGraph
  source: DB (uploaded docs)    source: Firecrawl response
       ↓                              ↓
  chunks (from upload)          chunk_text(raw_content)
       ↓                              ↓
  EmbeddingService ←── shared ──→ EmbeddingService
       ↓                              ↓
  embed_batch()                 embed_batch()
       ↓                              ↓
  _embedding_cache[conv_id]     _embedding_cache[conv_id][url]
       ↓                              ↓
  cosine_similarity(query_vec)  cosine_similarity(query_vec)
       ↓                              ↓
  top-K within token budget     top-K within token budget
       ↓                              ↓
  synthesize_node               synthesize_node
```

PR-2.5a extracts this shared pipeline into `SemanticRetriever`. Both subgraphs use it.
Keyword-based retrieval is not an option — semantic search handles paraphrases, synonyms,
and cross-language queries that TF-IDF cannot.

---

## Hierarchical Skill Routing

One tool per domain. The agent makes one coarse decision (which domain). The subgraph
handles fine-grained skill selection internally — more deterministic than exposing 4+
similarly-described tools directly to the LLM.

```
Tier 1 — Agent selects domain     (few options, non-overlapping, reliable)
Tier 2 — Subgraph selects skill   (focused LLM call against small catalog, isolated)
```

`SKILLS.md` is a routing artifact, not a behavior file. All synthesis prompts and
execution parameters live in Python.

---

## Full Runtime Flow

```
AgentGraph (outer)
  MessagesState, AsyncSqliteSaver
  │
  └── ToolNode → WebResearchTool._arun(query, url?, config)
                    │
                    └── WebResearchGraph (inner subgraph, no checkpointer)
                          │
                          ├── load_skills_node
                          │     read SKILLS.md catalog into state (static)
                          │
                          ├── match_skill_node
                          │     LLM picks: scrape | search | crawl | extract
                          │     (query + catalog only — small, focused call)
                          │
                          ├── execute_node
                          │     cache hit?  → return _web_cache[conv_id][url]
                          │     cache miss? → FirecrawlClient API call
                          │                   chunk_text() → SemanticRetriever
                          │                   embed_batch() → store embeddings
                          │
                          ├── retrieve_node
                          │     embed query → cosine_similarity
                          │     top-K chunks within token budget
                          │
                          └── synthesize_node
                                LLM call → answer str → ToolMessage
```

### Context isolation

| Layer | Content | Enters MessagesState? |
|---|---|---|
| `WebResearchTool.description` | "Search and retrieve web content..." | Yes — tool description only |
| `SKILLS.md` catalog | Sub-skill descriptions | No — subgraph state only |
| Matched skill | e.g. `"search"` | No — subgraph state only |
| Firecrawl raw response | Full page markdown | No — subgraph state only |
| Chunk embeddings | N × 384 floats | No — module-level cache only |
| Synthesized answer | Focused prose with citations | Yes — ToolMessage only |

### Multi-turn caching

```python
# Module-level — same pattern as DocumentContextGraph
_web_chunk_cache: dict[str, dict[str, list[RetrievedChunk]]] = {}
_web_embedding_cache: dict[str, dict[str, list[list[float]]]] = {}
# outer key: conversation_id
# inner key: url (scrape/crawl/extract) or normalized query (search)
```

Turn 1: Firecrawl fetch → chunk → embed → cache. execute_node + embed_chunks_node run.
Turn 2+: Cache hit. Skip Firecrawl call and embedding. retrieve_node + synthesize_node only.

---

## Sub-PRs

---

### PR-2.5a — Extract `SemanticRetriever`

**Scope:** Pure refactor of existing PR-2.4 code. No new features. Proves the extraction
is clean before building WebResearchGraph on top of it.

**New file:** `src/agent_workbench/services/semantic_retriever.py`

```python
"""SemanticRetriever — shared retrieval pipeline for document and web content."""

_RETRIEVAL_TOKEN_BUDGET = 16_000  # moved here from content_retriever_tool.py


class SemanticRetriever:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    def chunk_text(
        self,
        text: str,
        filename: str,
        chunk_size: int = 512,
    ) -> list[RetrievedChunk]:
        """Split raw text into RetrievedChunk objects. Used by WebResearchGraph."""
        ...

    async def embed_chunks(
        self, chunks: list[RetrievedChunk]
    ) -> list[list[float]]:
        """Embed chunk contents. CPU-bound — wrapped in asyncio.to_thread."""
        return await asyncio.to_thread(
            self._embedding_service.embed_batch,
            [c.content for c in chunks],
        )

    async def embed_query(self, query: str) -> list[float]:
        return await asyncio.to_thread(self._embedding_service.embed, query)

    def select(
        self,
        query_vec: list[float],
        chunks: list[RetrievedChunk],
        embeddings: list[list[float]],
        budget: int = _RETRIEVAL_TOKEN_BUDGET,
    ) -> list[RetrievedChunk]:
        """Cosine similarity → top-K within token budget → document order."""
        scores = self._embedding_service.cosine_similarity(query_vec, embeddings)
        for chunk, score in zip(chunks, scores):
            chunk.score = score
        ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
        selected, used = [], 0
        for chunk in ranked:
            if used + chunk.token_count > budget:
                continue
            selected.append(chunk)
            used += chunk.token_count
        selected = selected or chunks[:5]
        selected.sort(key=lambda c: c.chunk_index)
        return selected
```

**Refactor `document_context_graph.py`:** replace inline embedding/selection logic with
`SemanticRetriever` calls. Behavior identical — this is a refactor, not a feature change.

**Files:**

| File | Change |
|---|---|
| `src/agent_workbench/services/semantic_retriever.py` | **NEW** |
| `src/agent_workbench/services/document_context_graph.py` | Use `SemanticRetriever` |
| `src/agent_workbench/services/content_retriever_tool.py` | Remove `_RETRIEVAL_TOKEN_BUDGET` (moved) |
| `src/agent_workbench/services/consolidated_service.py` | Pass `SemanticRetriever` to `DocumentContextGraph` |
| `tests/unit/services/test_semantic_retriever.py` | **NEW** |
| `tests/unit/services/test_document_context_graph.py` | Update for new constructor |

**Tests for 2.5a:**
- `chunk_text()` produces correct chunk count and token estimates
- `embed_chunks()` calls `embed_batch()` once, returns N lists
- `embed_query()` calls `embed()` once
- `select()` respects token budget
- `select()` restores document order after ranking
- `select()` falls back to `chunks[:5]` when all chunks exceed budget
- DocumentContextGraph tests: all existing tests still pass after refactor

**Verification:** `make test-unit-only` — all existing tests green, no behavior change.

---

### PR-2.5b — Skills Infrastructure + WebResearchGraph

**Scope:** SkillLoader, SKILLS.md, WebResearchGraph using SemanticRetriever.
`execute_node` stubbed — no real Firecrawl calls yet. Proves architecture end-to-end.

**Directory:**

```
src/agent_workbench/skills/
└── web_research/
    └── SKILLS.md
```

**`SKILLS.md` format:**

```markdown
---
name: web_research
description: >
  Search and retrieve content from the web. Use when the user asks about
  current information, references a URL, or needs content from an online source.
  NOT for documents already attached to this conversation (use document_retrieval).
---

# Web Research Skills

## scrape
Retrieve the full text content of a single known URL the user has referenced
explicitly. Use when a specific page URL is provided or implied.
NOT for topic searches (use search). NOT for structured data (use extract).

## search
Find and retrieve information about a topic when no specific URL is known.
Searches the web and returns synthesized results from top sources.
NOT when a URL is already known (use scrape).

## crawl
Retrieve content from a site and all its linked pages. Use when the user needs
comprehensive coverage of a domain or documentation site, not a single page.

## extract
Pull specific structured data from a known URL — prices, specs, tables, lists.
Use when the user asks for specific data points rather than prose content.
```

**`WebResearchState`:**

```python
class WebResearchState(TypedDict):
    query: str
    url: Optional[str]
    conversation_id: str
    skills_catalog: str          # SKILLS.md body — loaded once, never leaves subgraph
    matched_skill: str           # scrape | search | crawl | extract
    chunks: list[RetrievedChunk] # from cache or chunked Firecrawl response
    chunk_embeddings: list[list[float]]
    answer: str
```

**`SkillLoader`:**

```python
@dataclass
class SkillDefinition:
    name: str
    description: str      # frontmatter → tool description the agent sees
    skills_catalog: str   # SKILLS.md body → loaded into subgraph state

class SkillLoader:
    def __init__(self, skills_root: Path) -> None: ...

    def build_tools(
        self,
        model_config: ModelConfig,
        semantic_retriever: SemanticRetriever,
        firecrawl_client: "FirecrawlClient",
    ) -> list[BaseTool]: ...
```

**Files:**

| File | Change |
|---|---|
| `src/agent_workbench/skills/web_research/SKILLS.md` | **NEW** |
| `src/agent_workbench/services/skill_loader.py` | **NEW** |
| `src/agent_workbench/services/web_research_graph.py` | **NEW** (execute_node stubbed) |
| `tests/unit/services/test_skill_loader.py` | **NEW** |
| `tests/unit/services/test_web_research_graph.py` | **NEW** (mocked execute_node) |

**Tests for 2.5b:**
- `SkillLoader` reads frontmatter `name` and `description` correctly
- `SkillLoader.build_tools()` returns one tool with description from SKILLS.md frontmatter
- `match_skill_node` returns valid skill (mock LLM)
- `match_skill_node` falls back to `"search"` on unrecognized LLM output
- Cache hit: execute_node skipped when `_web_chunk_cache[conv_id][url]` populated
- Cache miss: stub called, result chunked and embedded, stored in cache
- `retrieve_node` uses `SemanticRetriever.select()` — top-K within budget
- Turn 2 cache hit: embed_chunks skipped, retrieve runs on cached embeddings
- `WebResearchTool._arun()` with no `thread_id` returns error string
- Full `ainvoke()` returns `str`

---

### PR-2.5c — FirecrawlClient + Wire

**Scope:** Real Firecrawl API calls, graceful degradation without API key, smoke-testable.

**`FirecrawlClient`:**

```python
class FirecrawlClient:
    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def scrape(self, url: str) -> str: ...       # GET /scrape
    async def search(self, query: str, limit: int = 5) -> str: ...  # GET /search
    async def crawl(self, url: str, max_depth: int = 2, limit: int = 10) -> str: ...
    async def extract(self, url: str, prompt: str) -> str: ...
    async def aclose(self) -> None: ...
```

All methods return normalized markdown. Token budget (`_WEB_TOKEN_BUDGET = 12_000`) applied
in `execute_node` before chunking — caps raw content before it enters the retrieval pipeline.

**`consolidated_service.py` additions:**

```python
from .skill_loader import SkillLoader
from .firecrawl_client import FirecrawlClient
from .semantic_retriever import SemanticRetriever
from pathlib import Path

_skills_root = Path(__file__).parent.parent / "skills"
_skill_loader = SkillLoader(_skills_root)

_firecrawl_client: Optional[FirecrawlClient] = None

# In initialize():
_semantic_retriever = SemanticRetriever(_embedding_service)  # reuses PR-2.4 singleton

api_key = os.getenv("FIRECRAWL_API_KEY")
if api_key:
    _firecrawl_client = FirecrawlClient(api_key)
    web_tools = _skill_loader.build_tools(
        model_config=self.default_model_config,
        semantic_retriever=_semantic_retriever,
        firecrawl_client=_firecrawl_client,
    )
else:
    logger.warning("FIRECRAWL_API_KEY not set — web_research skill disabled")
    web_tools = []

self.agent_graph = AgentGraph(
    self.default_model_config,
    tools=[retriever, *web_tools],
    checkpointer=_checkpointer,
)
```

**Files:**

| File | Change |
|---|---|
| `src/agent_workbench/services/firecrawl_client.py` | **NEW** |
| `src/agent_workbench/services/web_research_graph.py` | Replace stub with real execute_node |
| `src/agent_workbench/services/consolidated_service.py` | Wire `SemanticRetriever` + web tools |
| `pyproject.toml` | Add `httpx>=0.27.0` if not present |
| `tests/unit/services/test_firecrawl_client.py` | **NEW** |
| `tests/unit/services/test_web_research_graph.py` | Update: httpx-mocked execute_node |

**Tests for 2.5c:**
- `FirecrawlClient.scrape()` builds correct URL and auth header (mock httpx)
- `FirecrawlClient.search()` passes query and limit
- `FirecrawlClient.crawl()` passes maxDepth and limit
- `FirecrawlClient.extract()` passes prompt
- With `FIRECRAWL_API_KEY` set: tools include `web_research`
- Without `FIRECRAWL_API_KEY`: tools do not include `web_research`
- Token budget: raw content trimmed before chunking

---

## Files Touched (full)

| File | PR | Change |
|---|---|---|
| `services/semantic_retriever.py` | 2.5a | **NEW** — shared retrieval pipeline |
| `services/document_context_graph.py` | 2.5a | Use `SemanticRetriever` |
| `services/content_retriever_tool.py` | 2.5a | Remove `_RETRIEVAL_TOKEN_BUDGET` |
| `tests/unit/services/test_semantic_retriever.py` | 2.5a | **NEW** |
| `skills/web_research/SKILLS.md` | 2.5b | **NEW** |
| `services/skill_loader.py` | 2.5b | **NEW** |
| `services/web_research_graph.py` | 2.5b+c | **NEW** |
| `tests/unit/services/test_skill_loader.py` | 2.5b | **NEW** |
| `tests/unit/services/test_web_research_graph.py` | 2.5b+c | **NEW** |
| `services/firecrawl_client.py` | 2.5c | **NEW** |
| `services/consolidated_service.py` | 2.5c | Wire retriever + web tools |
| `pyproject.toml` | 2.5c | Add `httpx>=0.27.0` |
| `tests/unit/services/test_firecrawl_client.py` | 2.5c | **NEW** |

No DB migrations. No changes to `AgentGraph`, `database.py`, or DB backends.

---

## Deferred

| Item | Where |
|---|---|
| `map` skill (site structure discovery) | PR-2.5d if needed |
| Result cache eviction (TTL/LRU) | PR-2.6a checkpoint policy |
| SEO Coach: Dutch synthesis prompt | PR-2.6 mode-aware skill config |
| Rate limiting / retry in `FirecrawlClient` | PR-2.6a ops hardening |
| Multiple skill domains beyond `web_research` | Future — pattern already extensible |

---

## Verification

```bash
# After 2.5a — refactor only, all existing tests must stay green
make test-unit-only

# After 2.5b — architecture proof without API key
make test-unit-only

# After 2.5c — full smoke test (requires FIRECRAWL_API_KEY in .env)
make pre-commit
make start-app
# 1. Ask: "What does https://example.com say?"
#    → web_research tool called → scrape skill → semantic retrieval → answer
# 2. Ask follow-up about same page
#    → cache hit, no Firecrawl call, embedding skipped
# 3. Ask: "Find recent info about LangGraph agents"
#    → web_research → search skill → chunked + embedded results → answer
# 4. Ask about an uploaded document
#    → document_retrieval called (not web_research) — routing is correct
# 5. Unset FIRECRAWL_API_KEY, restart
#    → only document_retrieval available, app still works
```
