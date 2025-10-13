# UI-002: Enhanced Gradio UI with File Support (STUBBED)

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: UI-002-file-handling-in-interface
**Phase**: 2.2
**Dependencies**: Phase 2.1 (PWA App with User Settings)

## Context

Add file upload/download capabilities to the Gradio interface using an **MVP-first strategy**: build complete UI components with stubbed backend processing. The goal is to create a visible, functional interface that accepts files, displays metadata, and provides download options - but defers actual document processing to Phase 2.4 (ContentRetriever Tool).

This approach allows rapid UI iteration and user testing without blocking on complex document processing implementation. All backend calls return placeholder data, making the interface look complete while keeping implementation minimal.

**CRITICAL: This is a STUBBED implementation**. The UI will appear fully functional, but:
- File uploads only store metadata, not content
- Document processing returns placeholder text
- Downloads generate stub files with "coming soon" messages
- Approval dialogs auto-approve without validation

Real document processing, content extraction, and retrieval comes in **Phase 2.4 ContentRetriever Tool**.

## Architecture Scope

### What's Included:

- File upload UI component in Gradio interface
- File metadata display (filename, size, type, upload timestamp)
- Upload status indicators (uploading → uploaded → "processing pending")
- Download UI components for conversation export
- Multi-format export options (JSON, CSV, TXT, PDF)
- Human-in-the-loop approval dialog UI (approve/edit/reject buttons)
- Stubbed `DocumentProcessor` service (returns placeholder data)
- Stubbed `DownloadManager` service (generates simple placeholder files)
- Stubbed `ApprovalDialog` component (auto-approves all operations)
- Basic file validation (size limits, file type restrictions)
- Error handling for upload failures

### What's Explicitly Excluded:

- Actual document processing (PDF parsing, text extraction, chunking)
- Vector embeddings or semantic search integration
- File storage service or persistent file management
- Content retrieval from uploaded documents
- RAG (Retrieval Augmented Generation) implementation
- Document versioning or history tracking
- File sharing or collaboration features
- Advanced file preview or rendering
- Multi-file batch processing
- Authentication or access control for files
- Backend implementation (Phase 2.4)
- Agent tool integration (Phase 2.5+)

## Architectural Decisions

### 1. MVP-First Strategy: UI Before Backend

**Core Approach**: Build visible results first, defer complex processing

```python
# STUB PATTERN: Services return placeholder data immediately

class DocumentProcessor:
    """Phase 2.2: STUB - Returns metadata without processing"""

    async def process_file(self, file_path: str, conversation_id: UUID) -> Dict[str, Any]:
        """Stub: Return placeholder metadata without processing."""
        return {
            "document_id": str(uuid4()),
            "filename": Path(file_path).name,
            "file_type": Path(file_path).suffix or "unknown",
            "size_bytes": os.path.getsize(file_path),
            "content_preview": "📄 Document uploaded. Processing coming in Phase 2.4...",
            "status": "uploaded",
            "note": "⚠️ STUB: Actual processing not implemented yet"
        }
```

**Why Stub First:**
- Get user feedback on UI/UX without backend complexity
- Validate file upload patterns before implementing storage
- Iterate rapidly on interface design
- Unblock Phase 2.3 (Agent workflows can reference stub structure)
- Reduce risk by separating UI and backend concerns

### 2. File Upload UI Components

**Gradio Integration Strategy**:

```python
# ui/components/file_handler_ui.py

def create_file_upload_interface() -> gr.Column:
    """
    File upload UI with drag-and-drop support.

    Displays:
    - Upload button/drag-drop area
    - File metadata table (uploaded files)
    - Upload status (uploading → uploaded)
    """

    with gr.Column() as file_section:
        gr.Markdown("### 📎 Attach Documents")

        # File upload component
        file_upload = gr.File(
            label="Upload Files",
            file_count="multiple",
            file_types=[".txt", ".md", ".pdf", ".docx", ".csv", ".json"],
            type="filepath"  # Returns file path, not binary
        )

        # Status display
        upload_status = gr.Markdown("No files uploaded")

        # Uploaded files table
        files_table = gr.DataFrame(
            headers=["Filename", "Size", "Type", "Status"],
            datatype=["str", "str", "str", "str"],
            interactive=False,
            label="Uploaded Files"
        )

        # Event handler
        file_upload.change(
            fn=handle_file_upload,
            inputs=[file_upload, gr.State()],  # conversation_id from state
            outputs=[upload_status, files_table]
        )

    return file_section
```

**Accepted File Types** (Phase 2.2):
- Text: `.txt`, `.md`
- Documents: `.pdf`, `.docx`
- Data: `.csv`, `.json`

**File Size Limits**:
- Individual file: 10MB max
- Total upload per conversation: 50MB max

### 3. File Download UI Components

**Export Strategy**: Generate simple placeholder files for each format

```python
# ui/components/file_handler_ui.py

def create_download_interface() -> gr.Column:
    """
    Download buttons for conversation export.

    Formats:
    - JSON: Structured conversation data
    - CSV: Message list in tabular format
    - TXT: Plain text transcript
    - PDF: Formatted conversation (stub for Phase 2.4)
    """

    with gr.Column() as download_section:
        gr.Markdown("### 💾 Export Conversation")

        with gr.Row():
            json_btn = gr.Button("📄 Export JSON")
            csv_btn = gr.Button("📊 Export CSV")
            txt_btn = gr.Button("📝 Export TXT")
            pdf_btn = gr.Button("📕 Export PDF (Coming Soon)")

        # Download file path (hidden, triggers download)
        download_file = gr.File(visible=False)

        # Status message
        download_status = gr.Markdown("")

        # Event handlers
        json_btn.click(
            fn=export_conversation,
            inputs=[gr.State(), gr.State("json")],  # conv_id, format
            outputs=[download_file, download_status]
        )

        csv_btn.click(
            fn=export_conversation,
            inputs=[gr.State(), gr.State("csv")],
            outputs=[download_file, download_status]
        )

        txt_btn.click(
            fn=export_conversation,
            inputs=[gr.State(), gr.State("txt")],
            outputs=[download_file, download_status]
        )

        pdf_btn.click(
            fn=show_coming_soon_message,
            outputs=[download_status]
        )

    return download_section
```

### 4. Human-in-the-Loop Approval Dialog (Stubbed)

**Approval UI**: Modal-style dialog for operation approval (Phase 2.5+ for real implementation)

```python
# ui/components/approval_dialog.py

def create_approval_dialog() -> gr.Column:
    """
    Stubbed approval dialog component.

    Phase 2.2: Always auto-approves
    Phase 2.5: Implements real approval workflow
    """

    with gr.Column(visible=False) as approval_dialog:
        gr.Markdown("### ⚠️ Agent Approval Required")

        # Operation description
        operation_desc = gr.Markdown("")

        # Parameters display
        parameters_display = gr.JSON(label="Operation Parameters")

        # Action buttons
        with gr.Row():
            approve_btn = gr.Button("✅ Approve", variant="primary")
            edit_btn = gr.Button("✏️ Edit", variant="secondary")
            reject_btn = gr.Button("❌ Reject", variant="stop")

        # Status message
        approval_status = gr.Markdown("")

        # Event handlers (Phase 2.2: Auto-approve)
        approve_btn.click(
            fn=auto_approve_stub,
            inputs=[parameters_display],
            outputs=[approval_status, approval_dialog]  # Hide dialog
        )

        edit_btn.click(
            fn=show_edit_coming_soon,
            outputs=[approval_status]
        )

        reject_btn.click(
            fn=reject_operation_stub,
            outputs=[approval_status, approval_dialog]
        )

    return approval_dialog


async def auto_approve_stub(parameters: Dict[str, Any]) -> Tuple[str, gr.update]:
    """Phase 2.2 STUB: Auto-approve all operations."""
    print(f"⚠️ STUB: Auto-approving operation")
    return (
        "✅ Operation approved (auto-approved in Phase 2.2)",
        gr.update(visible=False)  # Hide dialog
    )
```

### 5. Stubbed Backend Services

**DocumentProcessor Stub**:

```python
# services/document_processor.py (STUB VERSION)

from typing import Dict, Any
from uuid import UUID, uuid4
from pathlib import Path
import os


class DocumentProcessor:
    """
    Phase 2.2 STUB: Document processor returning placeholder data.

    Real implementation in Phase 2.4 (ContentRetriever Tool).
    """

    def __init__(self):
        """Initialize stub processor (no dependencies needed)."""
        pass

    async def process_file(
        self,
        file_path: str,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Stub: Return placeholder metadata without processing.

        Phase 2.4 will implement:
        - Text extraction (PDF, DOCX)
        - Document chunking
        - Vector embedding
        - Storage in retrieval system
        """
        file_info = Path(file_path)

        # Basic file validation
        if not file_info.exists():
            raise ValueError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            raise ValueError("File exceeds 10MB limit")

        return {
            "document_id": str(uuid4()),
            "filename": file_info.name,
            "file_type": file_info.suffix or "unknown",
            "size_bytes": file_size,
            "size_formatted": self._format_size(file_size),
            "content_preview": "📄 Document uploaded. Processing coming in Phase 2.4...",
            "status": "uploaded",
            "note": "⚠️ STUB: Actual processing not implemented yet",
            "conversation_id": str(conversation_id)
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size for display."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
```

**DownloadManager Stub**:

```python
# services/download_manager.py (STUB VERSION)

from typing import Literal
from uuid import UUID
import tempfile
import json
import os


class DownloadManager:
    """
    Phase 2.2 STUB: Download manager generating placeholder export files.

    Real implementation in Phase 2.4+ will:
    - Export actual conversation history
    - Generate formatted PDFs
    - Include file attachments in exports
    """

    @staticmethod
    async def export_conversation_history(
        conversation_id: UUID,
        format: Literal["json", "csv", "txt", "pdf"]
    ) -> str:
        """
        Stub: Generate simple export file with placeholder content.

        Returns:
            File path to generated export file
        """
        output_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{conversation_id}_{timestamp}.{format}"
        filepath = os.path.join(output_dir, filename)

        if format == "json":
            stub_data = {
                "conversation_id": str(conversation_id),
                "exported_at": datetime.now().isoformat(),
                "format": "json",
                "messages": [],
                "note": "⚠️ STUB: Actual conversation export coming in Phase 2.4+",
                "phase": "2.2 - UI only"
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(stub_data, f, indent=2)

        elif format == "csv":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("timestamp,role,content\n")
                f.write(f"{datetime.now().isoformat()},system,\"⚠️ STUB: CSV export coming in Phase 2.4+\"\n")
                f.write(f"{datetime.now().isoformat()},system,\"Conversation ID: {conversation_id}\"\n")

        elif format == "txt":
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("AGENT WORKBENCH - CONVERSATION EXPORT\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Conversation ID: {conversation_id}\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write("⚠️ STUB: Text export coming in Phase 2.4+\n")
                f.write("This is a placeholder export file.\n")

        elif format == "pdf":
            # PDF stub not implemented in Phase 2.2
            raise NotImplementedError("PDF export coming in Phase 2.4+")

        return filepath
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/ui/components/
├── file_handler_ui.py       # File upload/download UI components
└── approval_dialog.py        # Human-in-the-loop approval UI (stubbed)

src/agent_workbench/services/
├── document_processor.py     # STUB: Returns placeholder metadata
└── download_manager.py       # STUB: Generates placeholder export files

tests/ui/components/
├── test_file_handler_ui.py   # UI component tests (3 tests)
└── test_approval_dialog.py   # Approval dialog tests (2 tests)

tests/services/
├── test_document_processor.py   # Stub service tests (2 tests)
└── test_download_manager.py     # Stub service tests (3 tests)
```

### Files to MODIFY:

```
src/agent_workbench/ui/
├── app.py                    # Add file upload/download components
└── seo_coach_app.py          # Add file upload UI (Dutch labels)

src/agent_workbench/main.py  # Add temp file cleanup on shutdown (optional)
```

### Exact Function Signatures:

```python
# CREATE: ui/components/file_handler_ui.py

def create_file_upload_interface() -> gr.Column:
    """Create file upload UI with drag-and-drop support."""
    pass

def create_download_interface() -> gr.Column:
    """Create download buttons for conversation export."""
    pass

async def handle_file_upload(
    files: List[str],
    conversation_id: UUID
) -> Tuple[str, pd.DataFrame]:
    """
    Process uploaded files (stub implementation).

    Returns:
        (status_message, files_dataframe)
    """
    pass

async def export_conversation(
    conversation_id: UUID,
    format: Literal["json", "csv", "txt", "pdf"]
) -> Tuple[str, str]:
    """
    Export conversation to specified format (stub implementation).

    Returns:
        (file_path, status_message)
    """
    pass

def show_coming_soon_message() -> str:
    """Return 'coming soon' message for unimplemented features."""
    return "⚠️ Coming in Phase 2.4+"


# CREATE: ui/components/approval_dialog.py

def create_approval_dialog() -> gr.Column:
    """Create human-in-the-loop approval dialog (stubbed)."""
    pass

async def show_approval_request(
    operation: str,
    parameters: Dict[str, Any]
) -> gr.update:
    """
    Show approval dialog for operation (Phase 2.5+).
    Phase 2.2: Immediately auto-approve.
    """
    pass

async def auto_approve_stub(parameters: Dict[str, Any]) -> Tuple[str, gr.update]:
    """Phase 2.2 STUB: Auto-approve all operations."""
    pass

async def show_edit_coming_soon() -> str:
    """Show 'edit coming soon' message."""
    return "✏️ Edit functionality coming in Phase 2.5+"

async def reject_operation_stub(parameters: Dict[str, Any]) -> Tuple[str, gr.update]:
    """Phase 2.2 STUB: Reject operation (close dialog)."""
    pass


# CREATE: services/document_processor.py (STUB VERSION)

class DocumentProcessor:
    """Phase 2.2 STUB: Returns placeholder metadata without processing."""

    def __init__(self):
        """Initialize stub processor."""
        pass

    async def process_file(
        self,
        file_path: str,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """
        Stub: Return placeholder metadata without processing.

        Returns:
            {
                "document_id": str,
                "filename": str,
                "file_type": str,
                "size_bytes": int,
                "size_formatted": str,
                "content_preview": str,
                "status": "uploaded",
                "note": "⚠️ STUB: ..."
            }
        """
        pass

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size for display."""
        pass


# CREATE: services/download_manager.py (STUB VERSION)

class DownloadManager:
    """Phase 2.2 STUB: Generates placeholder export files."""

    @staticmethod
    async def export_conversation_history(
        conversation_id: UUID,
        format: Literal["json", "csv", "txt", "pdf"]
    ) -> str:
        """
        Stub: Generate simple export file with placeholder content.

        Returns:
            File path to generated export file
        """
        pass


# MODIFY: ui/app.py

def create_workbench_app() -> gr.Blocks:
    """
    Enhanced with file upload/download components.

    Additions:
    - File upload section below chat
    - Download section in sidebar
    - Approval dialog (hidden by default)
    """
    # Existing code...

    # ADD: File components
    with gr.Tab("Files"):
        file_upload_ui = create_file_upload_interface()

    # ADD: Download section
    with gr.Accordion("📥 Export", open=False):
        download_ui = create_download_interface()

    # ADD: Approval dialog (hidden)
    approval_dialog = create_approval_dialog()

    # Existing code...


# MODIFY: ui/seo_coach_app.py

def create_seo_coach_app() -> gr.Blocks:
    """
    Enhanced with file upload (Dutch labels).

    Additions:
    - File upload section: "Documenten uploaden"
    - Download section: "Conversatie exporteren"
    """
    # Similar to app.py but with Dutch labels
    pass
```

### Additional Dependencies:

```toml
# No new dependencies required!
# All functionality uses existing packages:

gradio = "^4.0.0"           # File upload/download components
pandas = "^2.0.0"           # DataFrame for file metadata table
pathlib = "^3.11"           # File path handling (stdlib)
tempfile = "^3.11"          # Temporary file generation (stdlib)
json = "^3.11"              # JSON export (stdlib)
```

### FORBIDDEN Actions:

- Implementing actual document processing (text extraction, parsing)
- Adding vector embeddings or semantic search
- Creating persistent file storage service
- Implementing content retrieval from uploaded documents
- Adding RAG capabilities
- Building document versioning system
- Implementing multi-file batch processing
- Adding authentication or access control for files
- Creating file sharing or collaboration features
- Implementing advanced file preview or rendering
- **Backend implementation (deferred to Phase 2.4)**

## Testing Strategy

**Test Coverage Goal**: ~80% (reduced from standard 90% due to stubbed functionality)

### 1. UI Component Tests (Minimal)

```python
# tests/ui/components/test_file_handler_ui.py (3 tests)

def test_file_upload_interface_renders():
    """Test file upload UI component renders without errors."""
    interface = create_file_upload_interface()
    assert interface is not None
    assert isinstance(interface, gr.Column)

def test_download_interface_renders():
    """Test download UI component renders without errors."""
    interface = create_download_interface()
    assert interface is not None
    assert isinstance(interface, gr.Column)

async def test_handle_file_upload_returns_placeholder():
    """Test file upload handler returns stub data."""
    status, df = await handle_file_upload(
        files=["test.txt"],
        conversation_id=uuid4()
    )
    assert "uploaded" in status.lower()
    assert df is not None
```

### 2. Approval Dialog Tests (Minimal)

```python
# tests/ui/components/test_approval_dialog.py (2 tests)

def test_approval_dialog_renders():
    """Test approval dialog component renders."""
    dialog = create_approval_dialog()
    assert dialog is not None

async def test_auto_approve_stub_always_approves():
    """Test stub auto-approves all operations."""
    status, update = await auto_approve_stub({"operation": "test"})
    assert "approved" in status.lower()
    assert update["visible"] is False  # Dialog hides
```

### 3. Stub Service Tests (Minimal)

```python
# tests/services/test_document_processor.py (2 tests)

async def test_document_processor_returns_metadata():
    """Test stub processor returns placeholder metadata."""
    processor = DocumentProcessor()
    result = await processor.process_file(
        file_path="test_file.txt",
        conversation_id=uuid4()
    )

    assert result["status"] == "uploaded"
    assert "STUB" in result["note"]
    assert result["filename"] == "test_file.txt"

async def test_document_processor_validates_file_exists():
    """Test stub processor raises error for missing file."""
    processor = DocumentProcessor()

    with pytest.raises(ValueError, match="File not found"):
        await processor.process_file(
            file_path="nonexistent.txt",
            conversation_id=uuid4()
        )


# tests/services/test_download_manager.py (3 tests)

async def test_export_json_creates_file():
    """Test JSON export creates placeholder file."""
    filepath = await DownloadManager.export_conversation_history(
        conversation_id=uuid4(),
        format="json"
    )

    assert os.path.exists(filepath)
    assert filepath.endswith(".json")

    with open(filepath) as f:
        data = json.load(f)
        assert "STUB" in data["note"]

async def test_export_csv_creates_file():
    """Test CSV export creates placeholder file."""
    filepath = await DownloadManager.export_conversation_history(
        conversation_id=uuid4(),
        format="csv"
    )

    assert os.path.exists(filepath)
    assert filepath.endswith(".csv")

async def test_export_pdf_raises_not_implemented():
    """Test PDF export raises NotImplementedError in Phase 2.2."""
    with pytest.raises(NotImplementedError):
        await DownloadManager.export_conversation_history(
            conversation_id=uuid4(),
            format="pdf"
        )
```

### 4. Integration Tests (Deferred to Phase 2.4)

**Phase 2.2 has NO integration tests** - all backend is stubbed.

Integration tests will be added in Phase 2.4 when:
- Real document processing is implemented
- Vector embeddings are functional
- Content retrieval works end-to-end

## Success Criteria

### Phase 2.2 (STUBBED Implementation):

- [ ] **File Upload UI**:
  - [ ] Upload component renders in both workbench and SEO coach modes
  - [ ] Accepts multiple file types (txt, md, pdf, docx, csv, json)
  - [ ] Displays uploaded file metadata (filename, size, type)
  - [ ] Shows upload status (uploading → uploaded)
  - [ ] Validates file size limits (10MB per file, 50MB total)
  - [ ] Shows error messages for invalid files

- [ ] **File Download UI**:
  - [ ] Download buttons render in both modes
  - [ ] JSON export creates placeholder file
  - [ ] CSV export creates placeholder file
  - [ ] TXT export creates placeholder file
  - [ ] PDF button shows "coming soon" message
  - [ ] Download triggers browser file save dialog

- [ ] **Approval Dialog UI**:
  - [ ] Dialog component renders (hidden by default)
  - [ ] Shows operation description and parameters
  - [ ] Approve/Edit/Reject buttons render
  - [ ] Approve button auto-approves and closes dialog
  - [ ] Edit button shows "coming soon" message
  - [ ] Reject button closes dialog

- [ ] **Stub Services**:
  - [ ] `DocumentProcessor` returns placeholder metadata
  - [ ] `DocumentProcessor` validates file exists and size limits
  - [ ] `DownloadManager` generates JSON export files
  - [ ] `DownloadManager` generates CSV export files
  - [ ] `DownloadManager` generates TXT export files
  - [ ] All stubs clearly marked with "⚠️ STUB" messages

- [ ] **Testing**:
  - [ ] ~10 total tests (minimal coverage for stubs)
  - [ ] 3 UI component tests pass
  - [ ] 2 approval dialog tests pass
  - [ ] 5 stub service tests pass
  - [ ] No integration tests (deferred to Phase 2.4)

- [ ] **Code Quality**:
  - [ ] All code passes `black` formatting
  - [ ] All code passes `ruff` linting
  - [ ] All functions have type hints
  - [ ] Stub implementations clearly documented

- [ ] **Documentation**:
  - [ ] All stub methods have docstrings noting "Phase 2.2 STUB"
  - [ ] README updated with Phase 2.2 status
  - [ ] Architecture decision document merged
  - [ ] Clear notes in code pointing to Phase 2.4 for real implementation

### Phase 2.4+ (Real Implementation - NOT in Phase 2.2):

- [ ] Actual document processing (text extraction, chunking)
- [ ] Vector embeddings and storage
- [ ] Content retrieval from uploaded documents
- [ ] RAG integration with agent workflows
- [ ] Persistent file storage service
- [ ] Real approval workflow with edit capabilities
- [ ] PDF export with formatted conversation
- [ ] Integration tests for full workflow

**IMPORTANT**: Do NOT implement Phase 2.4 features in Phase 2.2. Keep all backend functionality stubbed.

## Phase 2.4 Handoff Notes

When implementing real document processing in Phase 2.4:

1. **Replace DocumentProcessor stub**:
   - Add text extraction (PDF, DOCX, TXT)
   - Implement document chunking strategy
   - Integrate vector embedding service
   - Add persistent storage for chunks

2. **Replace DownloadManager stub**:
   - Export actual conversation messages
   - Include file attachments in exports
   - Generate formatted PDFs
   - Add export customization options

3. **Implement real approval workflow**:
   - Add approval state tracking
   - Implement edit functionality
   - Add timeout and escalation logic
   - Integrate with agent workflow (LangGraph)

4. **Add comprehensive integration tests**:
   - Upload → Process → Retrieve end-to-end
   - Export with actual conversation data
   - Approval workflow with state transitions
   - File storage persistence

5. **Update UI to show real processing status**:
   - Replace placeholder messages with real progress
   - Show document chunks and embeddings
   - Display retrieval relevance scores
   - Add real error handling

See `docs/phase2/phase2_architecture_plan.md` lines 2935+ for Phase 2.4 ContentRetriever Tool specification.
