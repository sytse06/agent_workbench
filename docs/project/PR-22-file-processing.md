# PR-2.2: File Processing

**Branch:** `feature/file-processing`
**Status:** Planning

---

## Problem

PR-2.1 uploads files and stores them in `pending_files` state, but their content is never read.
The LLM receives no document context — attaching a file has no effect on the conversation.

This PR wires the full processing pipeline: file → Docling conversion → hierarchical chunks →
DB storage → token-aware context block → injected as system message into the LLM turn.

---

## Scope

**IN:**
- `DoclingService`: wraps `DocumentConverter` + `HierarchicalChunker`; returns typed `DocumentChunk` list
- `FileProcessingService`: orchestrates DoclingService → DB → context block
- Two new DB tables: `documents` + `document_chunks` (Alembic migration)
- Token-aware context assembly: chunk selection fits within a configurable token budget (default 24k)
- Context injected as a system message via `document_context` field on `ConsolidatedWorkflowRequest`
- Mode handlers prepend the system message when `document_context` is present
- UI handlers call `FileProcessingService` on submit; pass `document_context` in API payload
- `pending_files` cleared after processing (already on submit from PR-2.1)
- Accepted types: `.pdf`, `.docx`, `.txt`, `.md` (same as PR-2.1)
- `docling` added as required dependency

**OUT (subsequent PRs):**
- SentenceTransformer embeddings + semantic chunk retrieval — PR-2.3 `ContentRetrieverTool`
- Multi-file upload — PR-2.3 decision
- Embedding column on `document_chunks` — migration added in PR-2.3
- Image, audio, video processing — Docling supports these; deferred to explicit PR
- File retention beyond processing (chunks are the durable artifact; temp file discarded)

---

## Current State

`pending_files` is populated by PR-2.1 approval flow. On submit:

```python
# handle_submit / handle_chat_interface_message (current)
text, _ = _extract_message(message)
payload = {"user_message": text, "conversation_id": ..., ...}
# pending_files never touched — files die with the Gradio session
```

`ConsolidatedWorkflowRequest.user_message` carries only the text. No document field exists.

---

## Architecture Decisions

### Decision 1: DoclingService is the only conversion layer

`DocumentConverter` + `HierarchicalChunker` from Docling. No fallback basic processor —
Docling handles `.pdf`, `.docx`, `.txt`, `.md` natively. If Docling raises, the error
surfaces to the user rather than silently stripping context (silent failure is worse than
an error message).

### Decision 2: Token-aware chunk selection, 24k token budget

32k context window, 24k reserved for document, 8k for conversation + system prompt +
user message. Token estimate: `len(chunk.content) // 4` (characters-to-tokens approximation).
This estimate is intentionally coarse — PR-2.5 middleware will replace it with provider-aware
token counting. The constant is named `_DOCUMENT_TOKEN_BUDGET` so it is findable and
replaceable in one place.

Chunks are selected in document order until the budget is exhausted. No semantic reordering
in this PR — that is PR-2.3.

### Decision 3: Context as system message via `document_context` field

`document_context: Optional[str]` added to `ConsolidatedWorkflowRequest` (and `WorkbenchState`).
Mode handlers check for it and prepend a synthetic system message to the messages list:

```python
{"role": "system", "content": f"[Attached document: {filename}]\n\n{context_block}"}
```

This keeps the user message clean, is semantically correct (background context = system),
and is the right hook for PR-2.5 middleware to intercept and summarize.

### Decision 4: Process and discard — no file bytes stored

Docling reads the Gradio temp file path immediately on submit (before any `yield`, so the
path is still valid). Chunks are stored as text in `document_chunks`. The temp file is left
for Gradio to clean up. No uploads directory, no file bytes in DB.

### Decision 5: Hub backend — stub

`hub.py` implements the document protocol methods as no-ops (log warning, return empty).
HuggingFace Hub DB has no SQL table for documents. For production Hub deployments, file
content will still be processed and injected into the current turn — it just won't be
persisted for retrieval across sessions. Acceptable for PR-2.2.

---

## Data Model

### New DB tables (`models/database.py`)

```python
class DocumentModel(Base, TimestampMixin):
    __tablename__ = "documents"

    id              = UUID primary key
    conversation_id = FK → conversations.id (CASCADE)
    filename        = String(255)      # original filename from Gradio
    mime_type       = String(100)      # "application/pdf", "text/plain", etc.
    status          = String(20)       # "processed" | "failed"
    page_count      = Integer nullable # from Docling document metadata
    total_tokens    = Integer nullable # sum of all chunk token estimates

class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id          = UUID primary key
    document_id = FK → documents.id (CASCADE)
    chunk_index = Integer        # position in document order
    content     = Text           # chunk text from HierarchicalChunker
    heading     = Text nullable  # contextualize() heading prefix
    page        = Integer nullable
    token_count = Integer        # len(content) // 4
    # embedding column deliberately absent — PR-2.3 Alembic migration adds it
```

### New `DatabaseBackend` protocol methods

```python
def save_document(self, data: Dict[str, Any]) -> str: ...          # returns document_id
def get_documents(self, conversation_id: str) -> List[Dict]: ...
def save_document_chunks(self, chunks: List[Dict[str, Any]]) -> None: ...
def get_document_chunks(self, document_id: str) -> List[Dict]: ...
```

---

## Step-by-Step Implementation

### Step 1: Add Docling dependency
**File:** `pyproject.toml`

```toml
dependencies = [
    ...
    "docling>=2.0.0",
]
```

Run `uv sync`. Verify: `uv run python -c "from docling.document_converter import DocumentConverter; print('ok')"`.

### Step 2: New `DocumentChunk` dataclass + `DoclingService`
**New file:** `src/agent_workbench/services/docling_service.py`

```python
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)

_DOCUMENT_TOKEN_BUDGET = 24_000  # tokens reserved for document context per turn


@dataclass
class DocumentChunk:
    index: int
    content: str
    heading: str        # contextualize() prefix, empty string if none
    page: Optional[int]
    token_count: int    # len(content) // 4


class DoclingService:
    def __init__(self) -> None:
        self._converter = None   # lazy init — Docling loads ML models on first use
        self._chunker = None

    def _ensure_init(self) -> None:
        if self._converter is None:
            from docling.document_converter import DocumentConverter
            from docling.chunking import HierarchicalChunker
            self._converter = DocumentConverter()
            self._chunker = HierarchicalChunker()
            logger.info("DoclingService initialised")

    def convert(self, file_path: str) -> list[DocumentChunk]:
        self._ensure_init()
        document = self._converter.convert(file_path).document
        raw_chunks = list(self._chunker.chunk(dl_doc=document))
        chunks = []
        for i, chunk in enumerate(raw_chunks):
            contextualized = self._chunker.contextualize(chunk)
            heading = contextualized.replace(chunk.text, "").strip()
            page = getattr(chunk.meta, "page_no", None) if hasattr(chunk, "meta") else None
            chunks.append(DocumentChunk(
                index=i,
                content=chunk.text,
                heading=heading,
                page=page,
                token_count=len(chunk.text) // 4,
            ))
        return chunks

    def build_context_block(
        self,
        chunks: list[DocumentChunk],
        token_budget: int = _DOCUMENT_TOKEN_BUDGET,
    ) -> str:
        selected = []
        used = 0
        for chunk in chunks:
            if used + chunk.token_count > token_budget:
                break
            selected.append(chunk)
            used += chunk.token_count
        parts = []
        for chunk in selected:
            if chunk.heading:
                parts.append(f"{chunk.heading}\n{chunk.content}")
            else:
                parts.append(chunk.content)
        suffix = (
            f"\n\n[Document truncated — {used:,} of {sum(c.token_count for c in chunks):,}"
            f" estimated tokens shown. Full retrieval available in PR-2.3.]"
            if len(selected) < len(chunks)
            else ""
        )
        return "\n\n".join(parts) + suffix
```

Run `uv run pytest tests/ -q` — no regressions before wiring.

### Step 3: New DB tables + protocol methods
**File:** `src/agent_workbench/models/database.py`

Add `DocumentModel` and `DocumentChunkModel` as described in the Data Model section above.

**File:** `src/agent_workbench/database/protocol.py`

Add the four document methods to `DatabaseBackend`.

**File:** `src/agent_workbench/database/backends/sqlite.py`

Implement all four methods using `session.execute` / `session.add` patterns matching existing
model methods.

**File:** `src/agent_workbench/database/backends/hub.py`

Stub all four:
```python
def save_document(self, data: Dict[str, Any]) -> str:
    logger.warning("Document storage not supported in Hub backend")
    return str(uuid4())

def get_documents(self, conversation_id: str) -> List[Dict]:
    return []

def save_document_chunks(self, chunks: List[Dict[str, Any]]) -> None:
    logger.warning("Document chunk storage not supported in Hub backend")

def get_document_chunks(self, document_id: str) -> List[Dict]:
    return []
```

**New file:** `alembic/versions/xxxx_add_documents_tables.py`

```python
def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("conversation_id", UUID, sa.ForeignKey("conversations.id", ondelete="CASCADE")),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("page_count", sa.Integer, nullable=True),
        sa.Column("total_tokens", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("document_id", UUID, sa.ForeignKey("documents.id", ondelete="CASCADE")),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("heading", sa.Text, nullable=True),
        sa.Column("page", sa.Integer, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=False),
    )
    op.create_index("idx_documents_conversation_id", "documents", ["conversation_id"])
    op.create_index("idx_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index("idx_document_chunks_index", "document_chunks", ["document_id", "chunk_index"])
```

Run `uv run alembic upgrade head` — verify tables exist with `make db-analyze`.

### Step 4: `FileProcessingService`
**New file:** `src/agent_workbench/services/file_processing_service.py`

```python
import logging
from typing import Optional
from uuid import uuid4

from .docling_service import DoclingService
from ..database.protocol import DatabaseBackend

logger = logging.getLogger(__name__)

_MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class FileProcessingService:
    def __init__(self, docling: DoclingService, db: DatabaseBackend) -> None:
        self.docling = docling
        self.db = db

    def process(
        self,
        file_path: str,
        filename: str,
        conversation_id: str,
    ) -> Optional[str]:
        """
        Convert file → chunks → DB → context block.

        Returns the context block string, or None if processing fails.
        Failure is logged; the caller proceeds without document context.
        """
        from pathlib import Path
        suffix = Path(filename).suffix.lower()
        mime_type = _MIME_MAP.get(suffix, "application/octet-stream")

        try:
            chunks = self.docling.convert(file_path)
        except Exception as exc:
            logger.error("DoclingService.convert failed for %s: %s", filename, exc)
            return None

        document_id = str(uuid4())
        total_tokens = sum(c.token_count for c in chunks)

        self.db.save_document({
            "id": document_id,
            "conversation_id": conversation_id,
            "filename": filename,
            "mime_type": mime_type,
            "status": "processed",
            "page_count": chunks[-1].page if chunks and chunks[-1].page else None,
            "total_tokens": total_tokens,
        })

        self.db.save_document_chunks([
            {
                "id": str(uuid4()),
                "document_id": document_id,
                "chunk_index": c.index,
                "content": c.content,
                "heading": c.heading or None,
                "page": c.page,
                "token_count": c.token_count,
            }
            for c in chunks
        ])

        context_block = self.docling.build_context_block(chunks)
        logger.info(
            "Processed %s: %d chunks, %d estimated tokens, %d in context block",
            filename,
            len(chunks),
            total_tokens,
            len(context_block) // 4,
        )
        return context_block
```

### Step 5: Wire `FileProcessingService` into `main.py`
**File:** `src/agent_workbench/main.py`

```python
from .services.docling_service import DoclingService
from .services.file_processing_service import FileProcessingService

docling_service = DoclingService()   # lazy — no ML models loaded yet
file_processing_service = FileProcessingService(
    docling=docling_service,
    db=state_manager.db,             # reuse existing DatabaseBackend
)
```

Inject into the consolidated service or pass directly to the UI handlers (see Step 6).

### Step 6: Add `document_context` to the request model
**File:** `src/agent_workbench/models/consolidated_state.py`

```python
class ConsolidatedWorkflowRequest(BaseModel):
    ...
    document_context: Optional[str] = None   # assembled by FileProcessingService; injected as system message
```

**File:** `src/agent_workbench/models/consolidated_state.py` — `WorkbenchState` TypedDict:

```python
document_context: Optional[str]  # present when a file was processed in this turn
```

### Step 7: Mode handlers inject system message
**File:** `src/agent_workbench/services/workflow_nodes.py` (or wherever mode handlers
prepare the messages list for `AgentService`)

At the point where `messages` is assembled for `agent_service.run()` / `agent_service.astream()`:

```python
if state.get("document_context"):
    filename = state.get("document_filename", "document")
    messages = [
        {"role": "system", "content": f"[Attached document: {filename}]\n\n{state['document_context']}"},
        *messages,
    ]
```

`document_filename` is a convenience field (the original filename) carried through state,
set by the UI handler alongside `document_context`.

### Step 8: UI handler changes
**File:** `src/agent_workbench/ui/pages/chat.py`

Both `handle_chat_interface_message` (Workbench) and `handle_submit` (SEO Coach):

```python
# After extracting text, before building payload:
document_context = None
document_filename = None

if pending:                                   # pending = pending_files state value
    file_info = pending[0]                    # single file per PR-2.1 constraint
    file_path = file_info.get("path") or file_info.get("name", "")
    document_filename = file_info.get("orig_name") or file_info.get("name", "file")

    # yield processing indicator before blocking Docling call
    yield current_history + [gr.ChatMessage(
        role="assistant",
        content="",
        metadata={"title": f"Processing {document_filename}...", "status": "thinking"},
    )]

    document_context = file_processing_service.process(
        file_path=file_path,
        filename=document_filename,
        conversation_id=str(conversation_id),
    )

# Build payload
payload = {
    "user_message": text,
    "conversation_id": str(conversation_id),
    "document_context": document_context,
    "document_filename": document_filename,
    ...
}
```

`ConsolidatedWorkflowRequest` now carries `document_context` through to the mode handler.
`document_filename` is passed via `context_data` or an additional optional field.

### Step 9: Tests
**New file:** `tests/unit/services/test_docling_service.py`

- `DoclingService` instantiates without error (no ML models loaded on `__init__`)
- `convert()` calls `DocumentConverter` and `HierarchicalChunker` (mocked); returns `list[DocumentChunk]`
- `build_context_block()` selects chunks within token budget
- `build_context_block()` appends truncation suffix when budget exceeded
- `build_context_block()` includes heading prefix when heading is non-empty
- Empty chunk list returns empty string

**New file:** `tests/unit/services/test_file_processing_service.py`

- `process()` calls `docling.convert()` with the given file path
- `process()` saves document and chunks to DB
- `process()` returns context block string on success
- `process()` returns `None` and logs error when `docling.convert()` raises
- `process()` sets `status="processed"` on successful conversion

**Update:** `tests/unit/services/test_consolidated_service.py`

- `ConsolidatedWorkflowRequest` accepts `document_context` field
- `document_context=None` behaves identically to current (no regression)

---

## Files Touched

| File | Change |
|---|---|
| `pyproject.toml` | Add `docling>=2.0.0` |
| `src/agent_workbench/services/docling_service.py` | **NEW** — `DocumentChunk`, `DoclingService` |
| `src/agent_workbench/services/file_processing_service.py` | **NEW** — `FileProcessingService` |
| `src/agent_workbench/models/database.py` | Add `DocumentModel`, `DocumentChunkModel` |
| `src/agent_workbench/database/protocol.py` | Add 4 document methods |
| `src/agent_workbench/database/backends/sqlite.py` | Implement 4 document methods |
| `src/agent_workbench/database/backends/hub.py` | Stub 4 document methods |
| `alembic/versions/xxxx_add_documents_tables.py` | **NEW** migration — `documents` + `document_chunks` |
| `src/agent_workbench/models/consolidated_state.py` | Add `document_context` to request + state |
| `src/agent_workbench/services/workflow_nodes.py` | Inject system message when `document_context` present |
| `src/agent_workbench/main.py` | Instantiate `DoclingService`, `FileProcessingService` |
| `src/agent_workbench/ui/pages/chat.py` | Call `file_processing_service.process()` on submit; yield processing indicator; pass `document_context` in payload |
| `tests/unit/services/test_docling_service.py` | **NEW** |
| `tests/unit/services/test_file_processing_service.py` | **NEW** |

---

## Verification

### Pre-merge checklist

- [ ] `make pre-commit` passes (mypy, ruff, black, pytest)
- [ ] `uv run alembic upgrade head` — both tables present in `make db-analyze`
- [ ] Docling import works: `uv run python -c "from docling.document_converter import DocumentConverter"`
- [ ] Existing chat tests still pass (no regressions — `document_context=None` path unchanged)

### Workbench mode

- [ ] `make start-app` — attach a `.pdf` → approve → submit with message
- [ ] "Processing filename..." thinking indicator appears before LLM response
- [ ] LLM response references content from the PDF (proves context injection works)
- [ ] Submit without file → no change in behaviour (no `document_context` field sent)
- [ ] Attach `.docx` → submit → LLM references content
- [ ] Attach `.txt` → submit → LLM references content
- [ ] Attach `.md` → submit → LLM references content
- [ ] Large PDF (> 24k token estimate) → truncation suffix in context block; LLM still responds
- [ ] Multi-turn after file submit: follow-up question still gets correct response
- [ ] `make db-analyze` → `documents` and `document_chunks` rows present after file submit

### SEO Coach mode

- [ ] `APP_MODE=seo_coach make start-app` — attach a PDF product page → approve → submit
- [ ] Processing indicator appears (Dutch UX: same Gradio `status="thinking"` metadata)
- [ ] LLM response is in Dutch and references content from the PDF
- [ ] Submit button state still works correctly (no regression from PR-2.1)

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Docling ML model download on first `convert()` call blocks for 30–60s | Lazy init is correct; consider startup warmup call in `main.py` after services are wired if startup time is acceptable |
| Gradio temp path already cleaned up before `process()` is called | `process()` called before any `yield` in the handler — path is still valid at that point |
| `HierarchicalChunker.contextualize()` API differs from `docs/showcases/content_retriever_tool.py` (written against earlier Docling) | Pin `docling>=2.0.0` and verify `contextualize()` signature against installed version in Step 2 |
| `total_tokens` estimate via `len // 4` is inaccurate for non-ASCII content (Dutch, special chars) | Acceptable for PR-2.2; PR-2.5 middleware replaces with provider-aware tokenizer |
| Hub backend no-op silently loses document context across sessions | Expected and documented; file is still processed + injected for the current turn |
| `document_context` field too large for API JSON serialization | 24k tokens × 4 chars ≈ 96k chars; well within HTTP body limits for local deployments |
