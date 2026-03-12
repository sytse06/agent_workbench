# PR-2.4: ContentRetriever Tool

**Branch:** `feature/content-retriever`
**Status:** In Progress (phase 1 landed — see Current State)

---

## Problem

PR-2.2 injects document content as a system message with a hard token budget (24k). For
short documents this works well. For large documents the budget truncates content and the
agent has no way to query what was cut. The agent is passive — it gets what fits, nothing
more.

This PR makes the agent active: it receives a `document_retrieval` tool it can call at
any point in the conversation to retrieve semantically relevant chunks from documents
attached to the session.

---

## Current State (after phase 1)

Phase 1 landed the structural wiring without semantic quality:

- `AgentGraph` now accepts `tools: list` at compile time; `ToolNode` added when non-empty
- `ContentRetrieverTool` exists (`services/content_retriever_tool.py`) with:
  - `DocumentRetrievalContext` — isolated Pydantic context (never enters `MessagesState`)
  - TF-IDF keyword ranking ← **to be replaced by semantic search in phase 2**
  - LLM synthesis step — secondary model call returns a focused, cited answer
  - `_fetch_chunks()` — fetches raw text chunks from DB via `session_factory`
- `consolidated_service.py` wires the tool as singleton into `AgentGraph` at startup
- `conversation_id` read from `config["configurable"]["thread_id"]` at runtime

What phase 1 does **not** have:
- Semantic retrieval (TF-IDF misses paraphrases, synonyms, cross-language queries)
- Multi-turn efficiency (chunks re-fetched and re-ranked on every tool call)

---

## Phase 2 Design

### Core decisions

**Decision 1: Semantic retrieval via `EmbeddingService`, not TF-IDF.**

`all-MiniLM-L6-v2` — 384-dim, ~80MB, CPU-friendly, multilingual. Cosine similarity against
batch-embedded chunk vectors. This enables Dutch-language queries in SEO Coach mode to
match English document content and vice versa. TF-IDF cannot do this.

**Decision 2: Vectorization happens inside a `DocumentContextGraph` subgraph — not in the DB.**

The original project doc proposed storing embeddings in a `document_chunks.embedding` column
(requiring an Alembic migration). This was rejected because:
- It couples a compute artifact to the storage schema
- Embeddings are a pure function of text — they can always be recomputed
- It adds ~300KB of float data to the DB per document

Instead: a `DocumentContextGraph` (inner `StateGraph`) computes and caches embeddings in
its own LangGraph state. The DB stays clean.

**Decision 3: Embedding vectors live in `DocumentContextGraph` state with a `MemorySaver` checkpointer.**

The outer `AgentGraph` uses `AsyncSqliteSaver` (PR-2.3d) for durable conversation history.
The inner `DocumentContextGraph` uses a separate `MemorySaver` — embeddings persist
in-process across multiple tool calls within the same conversation, without being written
to SQLite.

```
Turn 1: "What does section 3 say?"
  → load_chunks_node: fetch from DB (chunks empty in state)
  → embed_chunks_node: embed_batch(all chunks) — stored in MemorySaver state
  → retrieve_node: embed query, cosine similarity → top-K
  → synthesize_node: LLM call → answer

Turn 2: "What about section 5?"
  → load_chunks_node: SKIP (chunks already in state)
  → embed_chunks_node: SKIP (embeddings already in state)
  → retrieve_node: embed query only — 50ms vs. full batch
  → synthesize_node: LLM call → answer
```

On restart the MemorySaver is empty; the subgraph re-embeds on first call. Whether to
persist embeddings to disk is a PR-2.6a checkpoint policy decision.

**Decision 4: `ContentRetrieverTool` becomes a thin wrapper over `DocumentContextGraph`.**

The tool's responsibility shrinks to: extract `conversation_id` from `config`, invoke
the subgraph with `thread_id = conversation_id`, return the answer string. All retrieval
logic lives in the subgraph.

**Decision 5: Context isolation pattern is kept.**

The `DocumentRetrievalContext` Pydantic model survives as the retrieval context within
`retrieve_node`. It is never passed to the outer `AgentGraph`'s `MessagesState` — the
agent sees only the synthesized answer string as a `ToolMessage`.

**Decision 6: No DB migration.**

No changes to `document_chunks`, `DocumentChunkModel`, or `DatabaseBackend` protocol.
Chunks are fetched as raw text; embeddings are ephemeral.

---

## Architecture

```
AgentGraph (outer)
  MessagesState, thread_id = conversation_id, AsyncSqliteSaver
  │
  └── ToolNode → ContentRetrieverTool._arun(query, config)
                    │
                    └── DocumentContextGraph (inner subgraph)
                          DocumentContextState, thread_id = conversation_id, MemorySaver
                          │
                          ├── load_chunks_node   (skip if chunks already in state)
                          ├── embed_chunks_node  (skip if embeddings already in state)
                          ├── retrieve_node      (embed query, cosine sim, DocumentRetrievalContext)
                          └── synthesize_node    (LLM call → answer str)
```

### `DocumentContextState`

```python
class DocumentContextState(TypedDict):
    conversation_id: str
    query: str
    chunks: list[RetrievedChunk]         # loaded once from DB
    chunk_embeddings: list[list[float]]  # computed once, cached in MemorySaver
    answer: str
```

`chunk_embeddings` is large (N_chunks × 384 floats) but is never serialized to disk —
it lives only in the `MemorySaver` dict. At PR-2.6a, decide whether to promote it to
`AsyncSqliteSaver` with a TTL policy.

---

## Step-by-Step Implementation

### Step 1: Add `sentence-transformers` dependency

```toml
# pyproject.toml
dependencies = [
    ...
    "sentence-transformers>=3.0.0",
]
```

Run `uv sync`.

### Step 2: `EmbeddingService`

**New file:** `src/agent_workbench/services/embedding_service.py`

```python
"""EmbeddingService — lazy-loaded SentenceTransformer wrapper."""
import logging
import numpy as np

logger = logging.getLogger(__name__)
_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None  # lazy — downloads ~80MB on first use

    def _ensure_init(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("EmbeddingService loaded: %s", self._model_name)

    def embed(self, text: str) -> list[float]:
        self._ensure_init()
        return self._model.encode(text, convert_to_numpy=True).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._ensure_init()
        return self._model.encode(texts, convert_to_numpy=True).tolist()

    def cosine_similarity(
        self, query_vec: list[float], chunk_vecs: list[list[float]]
    ) -> list[float]:
        q = np.array(query_vec)
        c = np.array(chunk_vecs)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        c_norm = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-10)
        return (c_norm @ q_norm).tolist()
```

### Step 3: `DocumentContextGraph`

**New file:** `src/agent_workbench/services/document_context_graph.py`

```python
"""DocumentContextGraph — inner subgraph for multi-turn document retrieval."""
import logging
from typing import Callable, Optional
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from .embedding_service import EmbeddingService
from .content_retriever_tool import (
    DocumentRetrievalContext,
    RetrievedChunk,
    _RETRIEVAL_TOKEN_BUDGET,
    _SYNTHESIS_SYSTEM,
)
from ..models.schemas import ModelConfig
from .providers import provider_registry

logger = logging.getLogger(__name__)

# Module-level MemorySaver — separate from the outer AsyncSqliteSaver.
# Keeps chunk embeddings in-process without writing float vectors to SQLite.
# Checkpoint policy (persist vs. evict) deferred to PR-2.6a.
_doc_checkpointer = MemorySaver()


class DocumentContextState(TypedDict):
    conversation_id: str
    query: str
    chunks: list[RetrievedChunk]
    chunk_embeddings: list[list[float]]  # cached after first embed; not serialized to disk
    answer: str


class DocumentContextGraph:
    """Inner subgraph: load chunks → embed (cached) → retrieve → synthesize."""

    def __init__(
        self,
        session_factory: Callable,
        embedding_service: EmbeddingService,
        model_config: ModelConfig,
    ) -> None:
        self._session_factory = session_factory
        self._embedding_service = embedding_service
        self._model_config = model_config
        self._graph: CompiledStateGraph = self._build()

    def _build(self) -> CompiledStateGraph:
        session_factory = self._session_factory
        embedding_service = self._embedding_service
        model_config = self._model_config

        async def load_chunks_node(state: DocumentContextState) -> dict:
            if state.get("chunks"):
                return {}  # already loaded — skip
            chunks = await _fetch_chunks(session_factory, state["conversation_id"])
            return {"chunks": chunks}

        async def embed_chunks_node(state: DocumentContextState) -> dict:
            if state.get("chunk_embeddings"):
                return {}  # already embedded — skip (multi-turn reuse)
            chunks = state.get("chunks", [])
            if not chunks:
                return {"chunk_embeddings": []}
            texts = [c.content for c in chunks]
            embeddings = await asyncio.to_thread(embedding_service.embed_batch, texts)
            logger.info(
                "DocumentContextGraph: embedded %d chunks for conversation %s",
                len(embeddings), state["conversation_id"],
            )
            return {"chunk_embeddings": embeddings}

        async def retrieve_node(state: DocumentContextState) -> dict:
            chunks = state.get("chunks", [])
            embeddings = state.get("chunk_embeddings", [])
            if not chunks or not embeddings:
                return {"answer": "No documents have been attached to this conversation."}
            query_vec = await asyncio.to_thread(
                embedding_service.embed, state["query"]
            )
            scores = embedding_service.cosine_similarity(query_vec, embeddings)
            # Attach scores to chunks; select within token budget
            for chunk, score in zip(chunks, scores):
                chunk.score = score
            ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
            selected, used = [], 0
            for chunk in ranked:
                if used + chunk.token_count > _RETRIEVAL_TOKEN_BUDGET:
                    continue
                selected.append(chunk)
                used += chunk.token_count
            selected = selected or chunks[:5]
            # Restore document order
            selected.sort(key=lambda c: c.chunk_index)
            ctx = DocumentRetrievalContext(
                query=state["query"],
                conversation_id=state["conversation_id"],
                chunks=selected,
                total_tokens=used,
            )
            answer = await _synthesize(ctx, model_config)
            return {"answer": answer}

        builder = StateGraph(DocumentContextState)
        builder.add_node("load_chunks", load_chunks_node)
        builder.add_node("embed_chunks", embed_chunks_node)
        builder.add_node("retrieve", retrieve_node)
        builder.set_entry_point("load_chunks")
        builder.add_edge("load_chunks", "embed_chunks")
        builder.add_edge("embed_chunks", "retrieve")
        builder.add_edge("retrieve", END)
        return builder.compile(checkpointer=_doc_checkpointer)

    async def ainvoke(self, query: str, conversation_id: str) -> str:
        config = {"configurable": {"thread_id": conversation_id}}
        result = await self._graph.ainvoke(
            {"query": query, "conversation_id": conversation_id},
            config=config,
        )
        return result.get("answer", "No answer produced.")


async def _fetch_chunks(session_factory: Callable, conversation_id: str) -> list[RetrievedChunk]:
    from uuid import UUID
    from sqlalchemy import select
    from ..models.database import DocumentChunkModel, DocumentModel

    chunks: list[RetrievedChunk] = []
    async for session in session_factory():
        result = await session.execute(
            select(DocumentChunkModel, DocumentModel.filename)
            .join(DocumentModel)
            .where(DocumentModel.conversation_id == UUID(conversation_id))
            .order_by(DocumentChunkModel.chunk_index)
        )
        for chunk_row, filename in result:
            chunks.append(RetrievedChunk(
                chunk_index=chunk_row.chunk_index,
                content=chunk_row.content,
                filename=filename,
                heading=chunk_row.heading,
                page=chunk_row.page,
                token_count=chunk_row.token_count,
            ))
    return chunks


async def _synthesize(ctx: DocumentRetrievalContext, model_config: ModelConfig) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    parts = []
    for c in ctx.chunks:
        ref = c.filename
        if c.page:
            ref += f", p.{c.page}"
        if c.heading:
            ref += f", Section: {c.heading}"
        parts.append(f"[{ref}]\n{c.content}")

    model = provider_registry.create_model(model_config)
    response = await model.ainvoke([
        SystemMessage(content=_SYNTHESIS_SYSTEM),
        HumanMessage(content=(
            f"Document excerpts:\n\n{chr(10).join(parts)}\n\nQuery: {ctx.query}"
        )),
    ])
    return str(response.content)
```

### Step 4: Rewrite `ContentRetrieverTool` as thin wrapper

**File:** `src/agent_workbench/services/content_retriever_tool.py`

Remove `_tfidf_select`. Keep `RetrievedChunk`, `DocumentRetrievalContext`,
`_RETRIEVAL_TOKEN_BUDGET`, and `_SYNTHESIS_SYSTEM` (imported by `DocumentContextGraph`).
Rewrite `_arun`:

```python
async def _arun(
    self,
    query: str,
    config: Optional[RunnableConfig] = None,
    **kwargs: Any,
) -> str:
    conversation_id = (config or {}).get("configurable", {}).get("thread_id", "")
    if not conversation_id:
        return "No active conversation — cannot retrieve documents."
    return await self._doc_graph.ainvoke(query, conversation_id)
```

Construction:

```python
def __init__(
    self,
    session_factory: Callable,
    model_config: ModelConfig,
    embedding_service: EmbeddingService,
    **data: Any,
) -> None:
    super().__init__(**data)
    from .document_context_graph import DocumentContextGraph
    doc_graph = DocumentContextGraph(
        session_factory=session_factory,
        embedding_service=embedding_service,
        model_config=model_config,
    )
    object.__setattr__(self, "_doc_graph", doc_graph)
```

### Step 5: Wire `EmbeddingService` in `consolidated_service.py`

```python
from .embedding_service import EmbeddingService

# Module-level singleton — lazy, loads model on first embed() call.
# Warmup call in FastAPI lifespan recommended to avoid cold-start on first request.
_embedding_service = EmbeddingService()
```

In `initialize()`:

```python
from .content_retriever_tool import ContentRetrieverTool

retriever = ContentRetrieverTool(
    session_factory=get_session,
    model_config=self.default_model_config,
    embedding_service=_embedding_service,
)
self.agent_graph = AgentGraph(
    self.default_model_config,
    tools=[retriever],
    checkpointer=_checkpointer,
)
```

### Step 6: Tests

**New file:** `tests/unit/services/test_embedding_service.py`

- `EmbeddingService` instantiates without loading model (lazy init — `_model is None`)
- `embed()` returns `list[float]` of length 384 (mocked `SentenceTransformer`)
- `embed_batch()` returns N lists for N texts
- `cosine_similarity()` returns `[1.0]` for identical vectors (within float tolerance)
- `cosine_similarity()` returns `[0.0]` for orthogonal vectors

**New file:** `tests/unit/services/test_document_context_graph.py`

- `load_chunks_node` skipped when `chunks` already in state
- `embed_chunks_node` skipped when `chunk_embeddings` already in state (multi-turn cache hit)
- `embed_chunks_node` calls `embed_batch()` on first call (cache miss)
- `retrieve_node` returns "No documents" when chunks empty
- `retrieve_node` respects `_RETRIEVAL_TOKEN_BUDGET`
- `retrieve_node` restores document order after ranking by score
- `ainvoke` returns `str`

**Update:** `tests/unit/services/test_content_retriever_tool.py`

- Replace TF-IDF tests with subgraph delegation tests:
  - `test_arun_delegates_to_doc_graph` — mock `_doc_graph.ainvoke`, assert called with query + conversation_id
  - `test_arun_no_conversation_id_returns_message` — unchanged
  - Remove `test_tfidf_*` tests

---

## Files Touched

| File | Change |
|---|---|
| `pyproject.toml` | Add `sentence-transformers>=3.0.0` |
| `src/agent_workbench/services/embedding_service.py` | **NEW** — `EmbeddingService` |
| `src/agent_workbench/services/document_context_graph.py` | **NEW** — `DocumentContextGraph` subgraph |
| `src/agent_workbench/services/content_retriever_tool.py` | Remove `_tfidf_select`; rewrite `_arun` + `__init__` to use `DocumentContextGraph` |
| `src/agent_workbench/services/consolidated_service.py` | Add `_embedding_service` singleton; pass to `ContentRetrieverTool` |
| `tests/unit/services/test_embedding_service.py` | **NEW** |
| `tests/unit/services/test_document_context_graph.py` | **NEW** |
| `tests/unit/services/test_content_retriever_tool.py` | Replace TF-IDF tests with subgraph delegation tests |

No DB migrations. No changes to `AgentGraph`, `database.py`, or DB backends.

---

## Deferred

| Item | Where |
|---|---|
| Persist `chunk_embeddings` to disk with TTL/LRU | PR-2.6a checkpoint policy |
| Warmup call (`_embedding_service.embed("warmup")`) in FastAPI lifespan | PR-2.6a or ops concern |
| Swap `all-MiniLM-L6-v2` → `paraphrase-multilingual-MiniLM-L12-v2` for Dutch retrieval tuning | Later, if quality gap observed |
| Re-ranking (BM25 + vector hybrid) | Phase 3 |
| Firecrawl / web content retrieval | PR-2.5 |

---

## Verification

```bash
# Unit tests
make test-unit-only

# Full quality check
make pre-commit

# Smoke test
make start-app
# 1. Attach a large PDF, approve, ask a question about a section not in the 24k context
# 2. Agent should call document_retrieval tool (visible in streaming)
# 3. Turn 2: ask a follow-up — embed_chunks_node should be skipped (check logs)
# 4. APP_MODE=seo_coach make start-app — Dutch query against English PDF content
#    should still retrieve the right sections
```

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `all-MiniLM-L6-v2` downloads ~80MB on first use — blocks first tool call | Warmup call in lifespan (deferred to PR-2.6a; acceptable for now) |
| `embed_batch()` is CPU-bound — blocks async event loop | Wrapped in `asyncio.to_thread()` in `embed_chunks_node` |
| `MemorySaver` grows unbounded with conversations | Checkpoint policy (TTL/LRU) deferred to PR-2.6a; acceptable for dev/staging |
| `all-MiniLM-L6-v2` quality on Dutch text | Multilingual-capable; monitor in SEO Coach mode |
| `chunk_embeddings` lost on restart — first post-restart call re-embeds | Expected and acceptable; no data loss, just latency |
