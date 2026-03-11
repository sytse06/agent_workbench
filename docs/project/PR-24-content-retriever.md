# PR-2.3: ContentRetriever Tool

**Branch:** `feature/content-retriever`
**Status:** Planning

---

## Problem

PR-2.2 injects document content as a system message with a hard token budget (24k). For
short documents this works well. For large documents the budget truncates content and the
agent has no way to query what was cut. The agent is passive — it gets what fits and nothing
more.

This PR makes the agent active: it receives a `ContentRetrieverTool` it can call at any
point in a conversation to retrieve semantically relevant chunks from documents that were
previously processed in this session. The tool uses cosine similarity on stored embeddings —
the same semantic search pattern as `docs/showcases/content_retriever_tool.py`, rewritten
as a LangChain `BaseTool` and wired into `AgentService`.

---

## Scope

**IN:**
- Alembic migration: add `embedding` column (JSON float array) to `document_chunks`
- `EmbeddingService`: wraps `SentenceTransformer("all-MiniLM-L6-v2")`; lazy init
- `FileProcessingService` updated: embed chunks at processing time; store in `embedding` column
- `ContentRetrieverTool` (`BaseTool`): takes `query` + `conversation_id`; returns top-k chunks via cosine similarity
- `AgentService` updated: `tools=[content_retriever_tool]` (replaces `tools=[]` from PR-2.0)
- Truncation suffix in PR-2.2 context block updated: "Use the document retrieval tool to query specific sections"
- `sentence-transformers` added as required dependency

**OUT (subsequent PRs):**
- Multi-document retrieval across conversations — Phase 3
- Re-ranking, hybrid BM25+vector search — Phase 3
- URL/web content retrieval (Firecrawl) — PR-2.4
- Custom embedding models / provider-based embeddings — Phase 3

---

## Current State (post PR-2.2)

```
document_chunks:
  id, document_id, chunk_index, content, heading, page, token_count
  # embedding column absent — placeholder noted in PR-2.2 migration comments

AgentService:
  self.agent = create_agent(model, tools=[], ...)
  # no tools wired — Phase 2.3 was called out explicitly in PR-2.0 scope

FileProcessingService.process():
  chunks = docling.convert(path)
  db.save_document_chunks(chunks)     # text only
  context_block = docling.build_context_block(chunks)
  # no embeddings generated
```

---

## Architecture Decisions

### Decision 1: Embed at processing time, retrieve at query time

Embeddings are generated once when the file is processed (in `FileProcessingService.process()`),
stored in `document_chunks.embedding` as a JSON float array. At query time, `ContentRetrieverTool`
embeds only the query string and computes cosine similarity against stored chunk embeddings.

This is the correct split: processing is a one-time cost; retrieval should be fast and
independent of Docling.

### Decision 2: `all-MiniLM-L6-v2` as the embedding model

384-dimensional, ~80MB, CPU-friendly, no GPU required. This is the same model used in
`docs/showcases/content_retriever_tool.py`. Fast enough for real-time query embedding
(< 50ms per query on CPU). Can be swapped by changing one constant.

### Decision 3: `ContentRetrieverTool` is a LangChain `BaseTool`, not smolagents `Tool`

`AgentService` wraps a LangChain agent (PR-2.0). The tool must be a `BaseTool` subclass.
The retrieval logic is adapted directly from `_process_with_docling()` in
`docs/showcases/content_retriever_tool.py`:
- Embed query
- Cosine similarity against all chunk embeddings for the conversation
- Softmax-weighted cumulative threshold selection (threshold: 0.2)
- Return top-k chunks with heading context

The smolagents interface (`forward()`, `inputs`, `output_type`) is replaced with
LangChain's `_run()` and `args_schema`.

### Decision 4: Tool receives `conversation_id` as a bound parameter

`ContentRetrieverTool` is instantiated per-conversation-turn (or per-agent-invocation)
with `conversation_id` bound at construction time. The agent does not need to pass
`conversation_id` — it only passes `query`. This avoids leaking internal IDs into the
agent's tool interface.

```python
tool = ContentRetrieverTool(
    conversation_id=conversation_id,
    embedding_service=embedding_service,
    db=db,
)
agent = create_agent(model=..., tools=[tool], ...)
```

This means `AgentService` receives the tool instance (or factory) at call time, not at
init time — a small change to the `run()` / `astream()` signatures.

### Decision 5: PR-2.2 context block retained for immediate context

The full-text injection from PR-2.2 is kept as-is. For documents that fit within the 24k
budget, the agent gets the full text upfront and likely won't need to call the tool.
For truncated documents, the suffix now reads:

```
[Document truncated — 24,000 of 51,200 estimated tokens shown.
 Use the document_retrieval tool to query specific sections by topic.]
```

The agent learns from the system message that the tool exists for deep retrieval.

---

## Data Model Change

### Alembic migration: `embedding` column

```python
# alembic/versions/xxxx_add_embedding_to_chunks.py
def upgrade() -> None:
    op.add_column(
        "document_chunks",
        sa.Column("embedding", sa.JSON, nullable=True),
        # nullable=True: existing rows from PR-2.2 have no embedding;
        # they are skipped during retrieval (embedding IS NOT NULL filter)
    )
```

### Updated `DocumentChunkModel`

```python
embedding = mapped_column(JSON, nullable=True)  # list[float], 384 dims
```

### Updated `DatabaseBackend` protocol

```python
def get_document_chunks_with_embeddings(self, conversation_id: str) -> List[Dict]: ...
# Returns all chunks across all documents in the conversation where embedding IS NOT NULL
# Used by ContentRetrieverTool for cross-document retrieval within a session
```

---

## Step-by-Step Implementation

### Step 1: Add `sentence-transformers` dependency
**File:** `pyproject.toml`

```toml
dependencies = [
    ...
    "sentence-transformers>=3.0.0",
]
```

Run `uv sync`. Verify: `uv run python -c "from sentence_transformers import SentenceTransformer; print('ok')"`.

### Step 2: `EmbeddingService`
**New file:** `src/agent_workbench/services/embedding_service.py`

```python
import logging
from typing import Optional
import numpy as np

logger = logging.getLogger(__name__)

_MODEL_NAME = "all-MiniLM-L6-v2"


class EmbeddingService:
    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        self._model_name = model_name
        self._model = None   # lazy init — model download on first use

    def _ensure_init(self) -> None:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            logger.info("EmbeddingService initialised with model: %s", self._model_name)

    def embed(self, text: str) -> list[float]:
        self._ensure_init()
        vector = self._model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self._ensure_init()
        vectors = self._model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()

    def cosine_similarity(
        self, query_vec: list[float], chunk_vecs: list[list[float]]
    ) -> list[float]:
        q = np.array(query_vec)
        c = np.array(chunk_vecs)
        q_norm = q / (np.linalg.norm(q) + 1e-10)
        c_norm = c / (np.linalg.norm(c, axis=1, keepdims=True) + 1e-10)
        return (c_norm @ q_norm).tolist()
```

### Step 3: Alembic migration
**New file:** `alembic/versions/xxxx_add_embedding_to_chunks.py`

Add `embedding` column (nullable JSON) to `document_chunks`. See Data Model section.

Run `uv run alembic upgrade head`.

### Step 4: Update `DocumentChunkModel` and `DatabaseBackend`

**File:** `src/agent_workbench/models/database.py`

Add `embedding = mapped_column(JSON, nullable=True)` to `DocumentChunkModel`.

**File:** `src/agent_workbench/database/protocol.py`

Add `get_document_chunks_with_embeddings(conversation_id: str) -> List[Dict]`.

**File:** `src/agent_workbench/database/backends/sqlite.py`

Implement: join `document_chunks` → `documents` on `conversation_id`, filter
`embedding IS NOT NULL`, return all matching chunks.

**File:** `src/agent_workbench/database/backends/hub.py`

Stub: return `[]` (consistent with PR-2.2 no-op pattern).

### Step 5: Update `FileProcessingService` to embed chunks
**File:** `src/agent_workbench/services/file_processing_service.py`

Add `embedding_service: EmbeddingService` to `__init__`. In `process()`, after
converting chunks, generate embeddings in batch before saving:

```python
texts = [c.content for c in chunks]
embeddings = self.embedding_service.embed_batch(texts)

self.db.save_document_chunks([
    {
        ...existing fields...,
        "embedding": embeddings[i],
    }
    for i, c in enumerate(chunks)
])
```

Also update the truncation suffix in `DoclingService.build_context_block()`:

```python
suffix = (
    f"\n\n[Document truncated — {used:,} of {sum(c.token_count for c in chunks):,}"
    f" estimated tokens shown."
    f" Use the document_retrieval tool to query specific sections by topic.]"
    if len(selected) < len(chunks)
    else ""
)
```

### Step 6: `ContentRetrieverTool`
**New file:** `src/agent_workbench/services/content_retriever_tool.py`

```python
import logging
from typing import Type
import numpy as np
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .embedding_service import EmbeddingService
from ..database.protocol import DatabaseBackend

logger = logging.getLogger(__name__)

_THRESHOLD = 0.2   # cumulative softmax probability threshold (from ContentRetrieverTool)
_MAX_CHUNKS = 10   # hard cap on returned chunks


class RetrievalInput(BaseModel):
    query: str = Field(description="Search query to find relevant sections in attached documents")


class ContentRetrieverTool(BaseTool):
    name: str = "document_retrieval"
    description: str = (
        "Retrieve relevant sections from documents attached in this conversation. "
        "Use this when the user asks about specific content in an uploaded file, "
        "or when you need more detail than was provided in the initial document context."
    )
    args_schema: Type[BaseModel] = RetrievalInput

    # Bound at construction time — not passed by the agent
    conversation_id: str
    embedding_service: EmbeddingService
    db: DatabaseBackend

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        chunks = self.db.get_document_chunks_with_embeddings(self.conversation_id)
        if not chunks:
            return "No documents with stored embeddings found for this conversation."

        query_vec = self.embedding_service.embed(query)
        chunk_vecs = [c["embedding"] for c in chunks]
        similarities = self.embedding_service.cosine_similarity(query_vec, chunk_vecs)

        # Softmax-weighted cumulative threshold selection (from ContentRetrieverTool)
        exp_scores = np.exp(similarities)
        probs = exp_scores / exp_scores.sum()
        sorted_indices = np.argsort(probs)[::-1]

        selected = []
        cumulative = 0.0
        for idx in sorted_indices:
            cumulative += probs[idx]
            selected.append(int(idx))
            if cumulative >= _THRESHOLD or len(selected) >= _MAX_CHUNKS:
                break

        selected.sort()   # restore document order
        parts = []
        for idx in selected:
            chunk = chunks[idx]
            heading = chunk.get("heading") or ""
            content = chunk.get("content", "")
            parts.append(f"{heading}\n{content}".strip() if heading else content)

        logger.info(
            "ContentRetrieverTool: query=%r → %d/%d chunks selected",
            query[:60],
            len(selected),
            len(chunks),
        )
        return "\n\n".join(parts) if parts else "No relevant sections found for this query."

    async def _arun(self, query: str) -> str:
        return self._run(query)   # embedding is CPU-bound; no async benefit
```

### Step 7: Update `AgentService` to accept tools
**File:** `src/agent_workbench/services/agent_service.py`

`AgentService.__init__` currently calls `create_agent(model, tools=[], ...)`. The tool
instance is conversation-scoped (it needs `conversation_id`), so tools cannot be bound
at service init time.

Change `run()` and `astream()` to accept an optional `tools` parameter:

```python
async def run(
    self,
    messages: list[dict],
    task_id: str,
    tools: Optional[list] = None,
) -> AgentResponse:
    agent = create_agent(
        model=self._model,
        tools=tools or [],
        structured_output=AgentResponse,
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": task_id}}
    result = await agent.ainvoke({"messages": messages}, config=config)
    return result["structured_response"]
```

Same pattern for `astream()`. If `tools=[]`, behaviour is identical to PR-2.0.

### Step 8: Wire tool in UI handler
**File:** `src/agent_workbench/ui/pages/chat.py`

After `FileProcessingService.process()` is called and `conversation_id` is known,
construct the tool and pass it through the API payload — or, more practically, pass it
via a thread-local / request-scoped mechanism.

The cleanest approach: add `tools` to the `ConsolidatedWorkflowRequest` as a list of
tool names (strings), and instantiate the actual tool objects in `ConsolidatedWorkbenchService`
before calling `agent_service.run()`. `"document_retrieval"` is the only registered tool
name in PR-2.3; the service resolves it to a `ContentRetrieverTool` instance with the
correct `conversation_id`.

```python
# In ConsolidatedWorkflowRequest
active_tools: List[str] = Field(default_factory=list)
# e.g. ["document_retrieval"] when a file was processed this turn
```

```python
# In ConsolidatedWorkbenchService.execute_workflow() / stream_workflow()
tools = []
if "document_retrieval" in request.active_tools:
    tools.append(ContentRetrieverTool(
        conversation_id=str(request.conversation_id),
        embedding_service=self.embedding_service,
        db=self.db,
    ))
response = await self.agent_service.run(messages, task_id, tools=tools)
```

### Step 9: Wire `EmbeddingService` and `ContentRetrieverTool` in `main.py`
**File:** `src/agent_workbench/main.py`

```python
from .services.embedding_service import EmbeddingService
from .services.content_retriever_tool import ContentRetrieverTool

embedding_service = EmbeddingService()   # lazy — model loads on first embed()

file_processing_service = FileProcessingService(
    docling=docling_service,
    embedding_service=embedding_service,   # added
    db=state_manager.db,
)
```

Inject `embedding_service` and `db` into `ConsolidatedWorkbenchService` so it can
construct `ContentRetrieverTool` on demand.

### Step 10: Tests
**New file:** `tests/unit/services/test_embedding_service.py`

- `EmbeddingService` instantiates without loading model (lazy init)
- `embed()` returns a list of floats with length 384 (mocked model)
- `embed_batch()` returns N lists for N inputs
- `cosine_similarity()` returns 1.0 for identical vectors
- `cosine_similarity()` returns 0.0 for orthogonal vectors

**New file:** `tests/unit/services/test_content_retriever_tool.py`

- `_run()` returns "No documents" message when DB returns empty list
- `_run()` calls `embedding_service.embed()` with the query string
- `_run()` returns chunks sorted by document order (not similarity rank)
- `_run()` selects only chunks within cumulative threshold
- `_run()` does not exceed `_MAX_CHUNKS` limit
- `arun()` returns same result as `_run()`

**Update:** `tests/unit/services/test_agent_service.py`

- `run()` accepts `tools=[]` without error (no regression)
- `run()` passes tools to `create_agent` (mocked)
- `astream()` accepts `tools=[mock_tool]` and yields events as before

**Update:** `tests/unit/services/test_consolidated_service.py`

- `ConsolidatedWorkflowRequest` accepts `active_tools=["document_retrieval"]`
- `active_tools=[]` behaves identically to current (no regression)

---

## Files Touched

| File | Change |
|---|---|
| `pyproject.toml` | Add `sentence-transformers>=3.0.0` |
| `alembic/versions/xxxx_add_embedding_to_chunks.py` | **NEW** — `embedding` column on `document_chunks` |
| `src/agent_workbench/models/database.py` | Add `embedding` to `DocumentChunkModel` |
| `src/agent_workbench/database/protocol.py` | Add `get_document_chunks_with_embeddings()` |
| `src/agent_workbench/database/backends/sqlite.py` | Implement `get_document_chunks_with_embeddings()` |
| `src/agent_workbench/database/backends/hub.py` | Stub `get_document_chunks_with_embeddings()` |
| `src/agent_workbench/services/embedding_service.py` | **NEW** — `EmbeddingService` |
| `src/agent_workbench/services/file_processing_service.py` | Add embedding generation; update truncation suffix |
| `src/agent_workbench/services/docling_service.py` | Update truncation suffix text |
| `src/agent_workbench/services/content_retriever_tool.py` | **NEW** — `ContentRetrieverTool` |
| `src/agent_workbench/services/agent_service.py` | `run()` / `astream()` accept `tools` parameter |
| `src/agent_workbench/models/consolidated_state.py` | Add `active_tools: List[str]` to request |
| `src/agent_workbench/services/consolidated_service.py` | Instantiate + pass tool when `"document_retrieval"` in `active_tools` |
| `src/agent_workbench/main.py` | Instantiate `EmbeddingService`; inject into services |
| `src/agent_workbench/ui/pages/chat.py` | Set `active_tools=["document_retrieval"]` when file was processed |
| `tests/unit/services/test_embedding_service.py` | **NEW** |
| `tests/unit/services/test_content_retriever_tool.py` | **NEW** |

---

## Verification

### Pre-merge checklist

- [ ] `make pre-commit` passes
- [ ] `uv run alembic upgrade head` — `embedding` column present in `document_chunks`
- [ ] `uv run python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"` — model downloads cleanly
- [ ] Existing file upload tests still pass (PR-2.2 path: `active_tools=[]`)

### Workbench mode

- [ ] `make start-app` — attach a large PDF (> 24k token estimate) → approve → submit
- [ ] Truncation suffix visible in LLM context (check logs or ask LLM "were you given the full document?")
- [ ] LLM references the tool to answer a follow-up question about a section not in the initial context
- [ ] Tool call visible in streaming events (thinking block or log line)
- [ ] Short PDF (< 24k tokens) → no tool call needed; LLM answers from system message context
- [ ] Submit without file → `active_tools=[]` → tool not registered → no regression

### SEO Coach mode

- [ ] `APP_MODE=seo_coach make start-app` — attach a product page PDF → submit
- [ ] Ask "wat staat er op pagina 3?" (what's on page 3?) → LLM calls tool → Dutch response with page 3 content
- [ ] Tool works correctly in Dutch context (query embedding is language-agnostic; `all-MiniLM-L6-v2` is multilingual-capable for common Western languages)

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| `create_agent` reconstructed on every `run()` / `astream()` call (one per turn) — performance | `MemorySaver` is lightweight; `create_agent` is fast to construct. Monitor in prod; cache compiled graph if needed |
| `all-MiniLM-L6-v2` downloads ~80MB on first use — blocks first request | Warmup in `main.py` startup: call `embedding_service.embed("warmup")` after server starts |
| Existing `document_chunks` rows from PR-2.2 have `embedding=NULL` — skipped during retrieval | Correct and expected; migration is nullable. Add a one-off backfill script if needed |
| LangChain `BaseTool` with Pydantic `model_fields` conflicts with instance attributes (`conversation_id`, `embedding_service`, `db`) | Use `model_config = ConfigDict(arbitrary_types_allowed=True)` — already shown in Step 6 |
| `_THRESHOLD = 0.2` may select too few or too many chunks depending on document structure | Tunable constant; expose as config param if retrieval quality is poor in practice |
| `all-MiniLM-L6-v2` quality on Dutch text | Model is multilingual (trained on 50+ languages). Acceptable for PR-2.3; swap to `paraphrase-multilingual-MiniLM-L12-v2` if Dutch retrieval quality is poor |
