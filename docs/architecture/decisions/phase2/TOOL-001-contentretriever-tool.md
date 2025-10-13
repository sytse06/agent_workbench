# TOOL-001: ContentRetriever Tool Implementation

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: TOOL-001-contentretriever-tool
**Phase**: 2.4
**Dependencies**: Phase 2.3 (AGENT-001: Basic Agent Service + Debug Logging)

## Context

Phase 2.4 implements the **first tool** for the agent: a LangChain BaseTool for local file processing. This replaces the stubbed `DocumentProcessor` from Phase 2.2 with a real implementation that provides actual content retrieval capabilities.

**Critical Context:**
- This is a **LangChain tool**, NOT an MCP tool
- User priority: "Langchain tool first then mcp"
- Firecrawl MCP tool for web scraping comes later in Phase 2.7
- ContentRetriever handles ONLY local files (no URLs, no web scraping)
- Proven pattern from showcase implementation (`docs/showcases/content_retriever_tool.py`)

**Phase 2.2 → Phase 2.4 Transition:**
Phase 2.2 created UI components with stubbed backend processing. Phase 2.4 makes those stubs real:
- Phase 2.2: File upload UI shows, but processing returns placeholder data
- Phase 2.4: File upload UI actually processes files, agent can read content
- Agent from Phase 2.3 gets its first tool

## Architecture Scope

### What's Included:

- `ContentRetrieverTool` as LangChain BaseTool (NOT MCP)
- File format detection for extensionless files
- Docling integration for advanced document processing
- Fallback to basic processing when Docling fails
- Real `DocumentProcessor` implementation replacing Phase 2.2 stub
- File content storage and retrieval
- Query-based semantic filtering of content
- Multi-format support: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON
- ContentRetriever added to agent's tools list
- Integration with Phase 2.3 debug logging (tool calls logged)

### What's Explicitly Excluded:

- Web scraping or URL fetching (Phase 2.7: Firecrawl MCP tool)
- MCP tool implementation patterns (Phase 2.7)
- Vector database integration (Phase 3+)
- Document chunking strategies (Phase 3+)
- Advanced RAG capabilities (Phase 3+)
- Document version control or history
- Collaborative document editing
- Authentication or authorization for file access
- Cloud storage integration (S3, GCS, etc.)

## Architectural Decisions

### 1. LangChain BaseTool Pattern (NOT MCP)

**Core Approach**: Implement as LangChain BaseTool for local file processing

**Rationale:**
- Local file operations are stateless and synchronous
- No external API keys or services required
- Perfect fit for LangChain's tool abstraction
- MCP overhead unnecessary for simple file I/O
- User explicitly prioritized: "Langchain tool first then mcp"

**Tool Separation Strategy:**

| Tool | Type | Purpose | Phase |
|------|------|---------|-------|
| ContentRetrieverTool | LangChain | Local file processing | 2.4 |
| Firecrawl | MCP | Web scraping | 2.7 |

```python
# tools/content_retriever_tool.py

from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field

class ContentRetrieverInput(BaseModel):
    """Input schema for content retriever tool."""
    file_path: str = Field(description="Path to local file or document")
    query: Optional[str] = Field(None, description="Optional query to filter content")

class ContentRetrieverTool(BaseTool):
    """
    LangChain tool for retrieving content from local files.

    Based on showcase ContentRetrieverTool pattern.
    Does NOT handle web scraping - use Firecrawl MCP tool for that.
    """
    name: str = "content_retriever"
    description: str = """
    Retrieve and process content from local files and documents.
    Supports: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON.
    Use this for LOCAL file processing only.
    For web scraping, use the separate scraping tool.
    """
    args_schema: Type[BaseModel] = ContentRetrieverInput

    def _run(self, file_path: str, query: Optional[str] = None) -> str:
        """Synchronous implementation."""
        # Implementation details below

    async def _arun(self, file_path: str, query: Optional[str] = None) -> str:
        """Async implementation for agent execution."""
        # Implementation details below
```

### 2. Docling Integration with Intelligent Fallback

**Advanced Processing Strategy**: Use Docling for sophisticated document parsing, fall back gracefully

**Docling Capabilities:**
- Advanced PDF parsing with layout detection
- Table extraction from documents
- Image extraction and OCR
- Structured output for complex documents
- Format-specific optimizations

**Fallback Strategy:**
```python
class ContentRetrieverTool(BaseTool):
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        self.model_name = model_name
        self._has_docling = self._check_docling_availability()

        if self._has_docling:
            self._init_docling_components()

    def _check_docling_availability(self) -> bool:
        """Check if Docling is installed and working."""
        try:
            from docling.document_converter import DocumentConverter
            return True
        except ImportError:
            return False

    async def _arun(self, file_path: str, query: Optional[str] = None) -> str:
        """Process file with fallback strategy."""
        # Validate local file
        if file_path.startswith('http'):
            return "Error: This tool only handles local files. Use the scraping tool for web URLs."

        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        # Prepare file (detect format if extensionless)
        processed_path = self._prepare_file_access(file_path)

        # Try Docling first
        if self._has_docling:
            try:
                return await self._process_with_docling(processed_path, query)
            except Exception as e:
                # Check if it's a format error or Docling limitation
                if self._is_format_error(e):
                    # Fall back to basic processing
                    return await self._process_basic(file_path, query)
                raise  # Re-raise if it's a real error

        # Use basic processing if Docling not available
        return await self._process_basic(file_path, query)
```

**When to Use Each:**
- **Docling**: PDFs with tables, complex layouts, images requiring OCR
- **Basic**: Simple text files, CSVs, JSON, plain documents, Docling failures

### 3. File Format Detection for Extensionless Files

**Problem**: Many files lack extensions (e.g., downloaded files, system files)

**Solution**: Magic number detection + content analysis

```python
# utils/file_handler.py

import magic
from pathlib import Path
from typing import Optional

class FileHandler:
    """Handle file operations with format detection."""

    MIME_TO_EXTENSION = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'text/html': '.html',
        'text/plain': '.txt',
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'application/json': '.json',
        'text/csv': '.csv',
    }

    @staticmethod
    def detect_file_format(file_path: str) -> str:
        """
        Detect file format using magic numbers.

        Returns:
            Detected MIME type
        """
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        return mime_type

    @staticmethod
    def prepare_file_access(file_path: str) -> str:
        """
        Prepare file for processing, adding extension if needed.

        For extensionless files:
        1. Detect format via magic numbers
        2. Create temp copy with correct extension
        3. Return temp path for processing

        Returns:
            Path to file with correct extension
        """
        path = Path(file_path)

        # Already has extension
        if path.suffix:
            return file_path

        # Detect format
        mime_type = FileHandler.detect_file_format(file_path)
        extension = FileHandler.MIME_TO_EXTENSION.get(mime_type, '.bin')

        # Create temp copy with extension
        import tempfile
        import shutil

        temp_dir = Path(tempfile.gettempdir()) / "agent_workbench_files"
        temp_dir.mkdir(exist_ok=True)

        temp_path = temp_dir / f"{path.stem}{extension}"
        shutil.copy2(file_path, temp_path)

        return str(temp_path)

    @staticmethod
    def analyze_file_metadata(file_path: str) -> dict:
        """Extract file metadata for display."""
        path = Path(file_path)
        stat = path.stat()

        return {
            "filename": path.name,
            "size_bytes": stat.st_size,
            "size_human": FileHandler._format_size(stat.st_size),
            "mime_type": FileHandler.detect_file_format(file_path),
            "extension": path.suffix or "unknown",
            "modified": stat.st_mtime,
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes as human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
```

### 4. DocumentProcessor: Real Implementation Replaces Stub

**Phase 2.2 Stub → Phase 2.4 Real:**

Phase 2.2 created a stub that returned placeholder data:
```python
# Phase 2.2 STUB
class DocumentProcessor:
    async def process_file(self, file_path: str, conversation_id: UUID) -> Dict[str, Any]:
        """Stub: Return placeholder metadata without processing."""
        return {
            "document_id": uuid4(),
            "status": "processed",
            "content": "Placeholder content - real processing in Phase 2.4"
        }
```

Phase 2.4 real implementation:
```python
# services/document_processor.py (REAL IMPLEMENTATION)

from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from pathlib import Path
from database.adapter import AdaptiveDatabase
from tools.content_retriever_tool import ContentRetrieverTool
from utils.file_handler import FileHandler

class DocumentProcessor:
    """
    Real document processor integrating ContentRetrieverTool.

    Replaces Phase 2.2 stub with actual file processing.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

    async def process_file(
        self,
        file_path: str,
        conversation_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded file and store content.

        Args:
            file_path: Path to uploaded file
            conversation_id: Conversation this file belongs to
            user_id: User who uploaded the file

        Returns:
            Document metadata including content
        """
        # Validate file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract metadata
        metadata = FileHandler.analyze_file_metadata(file_path)

        # Process content using ContentRetrieverTool
        try:
            content = await self.content_retriever._arun(file_path=file_path)
        except Exception as e:
            # Log error but don't fail completely
            content = f"Error processing file: {str(e)}"
            metadata["processing_error"] = str(e)

        # Store in database
        document_id = uuid4()
        await self.db.save_document(
            document_id=document_id,
            conversation_id=conversation_id,
            user_id=user_id,
            file_path=file_path,
            content=content,
            metadata=metadata
        )

        return {
            "document_id": str(document_id),
            "status": "processed" if "processing_error" not in metadata else "error",
            "content": content,
            "metadata": metadata
        }

    async def get_document_content(
        self,
        document_id: UUID,
        query: Optional[str] = None
    ) -> str:
        """
        Retrieve document content with optional query filtering.

        Args:
            document_id: Document to retrieve
            query: Optional query for semantic filtering

        Returns:
            Document content (filtered if query provided)
        """
        # Get document from database
        document = await self.db.get_document(document_id)

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # If query provided, re-process with filtering
        if query:
            content = await self.content_retriever._arun(
                file_path=document["file_path"],
                query=query
            )
            return content

        return document["content"]

    async def get_conversation_documents(
        self,
        conversation_id: UUID
    ) -> list[Dict[str, Any]]:
        """Get all documents for a conversation."""
        return await self.db.get_conversation_documents(conversation_id)
```

### 5. Agent Integration: Adding First Tool

**Phase 2.3 → Phase 2.4 Transition:**

Phase 2.3 created agent with empty tools list:
```python
# Phase 2.3: NO TOOLS
self.agent = create_agent(
    model=get_model(),
    tools=[],  # ← Empty
    middleware=[DebugLoggingMiddleware(db=self.db)],
    structured_output=AgentResponse
)
```

Phase 2.4 adds ContentRetriever:
```python
# services/agent_service.py (UPDATED)

from tools.content_retriever_tool import ContentRetrieverTool

class AgentService:
    """Agent service with ContentRetriever tool."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.content_retriever = None

    async def initialize(self):
        """Initialize agent WITH ContentRetriever tool."""

        # Create ContentRetriever tool
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

        # Create agent with tools
        self.agent = create_agent(
            model=get_model(),
            tools=[self.content_retriever],  # ← FIRST TOOL
            middleware=[DebugLoggingMiddleware(db=self.db)],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        uploaded_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute agent with file context if provided."""

        # Build file context if files uploaded
        file_context = ""
        if uploaded_files:
            file_context = await self._build_file_context(uploaded_files)
            # Inject as system message
            messages.insert(0, {
                "role": "system",
                "content": f"Available files:\n{file_context}"
            })

        config = {
            "configurable": {
                "thread_id": task_id
            }
        }

        result = await self.agent.ainvoke(
            {"messages": messages, "config": user_settings},
            config=config
        )

        return result

    async def _build_file_context(self, file_paths: List[str]) -> str:
        """Build context string from uploaded files."""
        from services.document_processor import DocumentProcessor
        processor = DocumentProcessor(self.db)

        context_parts = []
        for file_path in file_paths:
            metadata = FileHandler.analyze_file_metadata(file_path)
            context_parts.append(
                f"- {metadata['filename']} ({metadata['size_human']}, {metadata['mime_type']})"
            )

        return "\n".join(context_parts)
```

### 6. Debug Logging Integration

**Tool Calls Logged Automatically:**

Phase 2.3's DebugLoggingMiddleware already captures tool calls. Phase 2.4 benefits immediately:

```python
# middleware/debug_logging_middleware.py (from Phase 2.3)

class DebugLoggingMiddleware:
    """Captures tool calls automatically."""

    async def after_agent(self, result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Log tool usage after agent execution."""

        # Extract tool calls from result
        tool_calls = []
        if "messages" in result:
            for msg in result["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tc in msg.tool_calls:
                        tool_calls.append({
                            "tool_name": tc["name"],
                            "tool_input": tc["args"],
                            "tool_call_id": tc["id"]
                        })

        # Store tool calls in database
        for tc in tool_calls:
            await self.db.create_tool_call_log(
                execution_log_id=context["execution_log_id"],
                tool_name=tc["tool_name"],
                tool_input=tc["tool_input"],
                tool_call_id=tc["tool_call_id"]
            )
```

**Querying Tool Usage:**
```python
# After Phase 2.4, can query ContentRetriever usage
logs = await db.get_execution_logs(limit=100)

for log in logs:
    tool_calls = await db.get_tool_calls_for_execution(log["execution_log_id"])
    content_retriever_calls = [tc for tc in tool_calls if tc["tool_name"] == "content_retriever"]
    print(f"ContentRetriever used {len(content_retriever_calls)} times in execution {log['task_id']}")
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/tools/
├── __init__.py                         # Package initialization
└── content_retriever_tool.py           # ContentRetrieverTool (LangChain BaseTool)

src/agent_workbench/services/
└── document_processor.py               # Real implementation (replaces stub)

src/agent_workbench/utils/
└── file_handler.py                     # File format detection and metadata
```

### Files to MODIFY:

```
src/agent_workbench/services/
└── agent_service.py                    # Add ContentRetriever to tools list

pyproject.toml                          # Add docling, python-magic dependencies
```

### Exact Function Signatures:

```python
# CREATE: tools/content_retriever_tool.py
from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import os
from pathlib import Path

class ContentRetrieverInput(BaseModel):
    """Input schema for content retriever tool."""
    file_path: str = Field(description="Path to local file or document")
    query: Optional[str] = Field(None, description="Optional query to filter content")

class ContentRetrieverTool(BaseTool):
    """
    LangChain tool for retrieving content from local files.

    Supports: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON.
    Uses Docling for advanced processing with fallback to basic.
    """
    name: str = "content_retriever"
    description: str = """
    Retrieve and process content from local files and documents.
    Supports: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON.
    Use this for LOCAL file processing only.
    For web scraping, use the separate scraping tool.
    """
    args_schema: Type[BaseModel] = ContentRetrieverInput

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize tool with optional embedding model."""
        super().__init__()
        self.model_name = model_name
        self._has_docling = self._check_docling_availability()

        if self._has_docling:
            self._init_docling_components()

    def _check_docling_availability(self) -> bool:
        """Check if Docling is installed and working."""
        # Implementation

    def _init_docling_components(self) -> None:
        """Initialize Docling converter if available."""
        # Implementation

    def _run(self, file_path: str, query: Optional[str] = None) -> str:
        """Synchronous implementation."""
        import asyncio
        return asyncio.run(self._arun(file_path, query))

    async def _arun(self, file_path: str, query: Optional[str] = None) -> str:
        """
        Async implementation for agent execution.

        Args:
            file_path: Path to local file
            query: Optional query for semantic filtering

        Returns:
            Processed file content
        """
        # Implementation

    def _prepare_file_access(self, file_path: str) -> str:
        """Prepare file for processing, adding extension if needed."""
        from utils.file_handler import FileHandler
        return FileHandler.prepare_file_access(file_path)

    async def _process_with_docling(self, file_path: str, query: Optional[str] = None) -> str:
        """Process file using Docling for advanced parsing."""
        # Implementation

    async def _process_basic(self, file_path: str, query: Optional[str] = None) -> str:
        """Process file using basic parsing methods."""
        # Implementation

    def _is_format_error(self, exception: Exception) -> bool:
        """Check if exception is a format limitation (should fallback)."""
        # Implementation

    def _apply_query_filter(self, content: str, query: str) -> str:
        """Apply semantic filtering if query provided."""
        # Implementation (simple for now, can enhance later)


# CREATE: services/document_processor.py (REAL IMPLEMENTATION)
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
from pathlib import Path
from database.adapter import AdaptiveDatabase
from tools.content_retriever_tool import ContentRetrieverTool
from utils.file_handler import FileHandler

class DocumentProcessor:
    """Real document processor using ContentRetrieverTool."""

    def __init__(self, db: AdaptiveDatabase):
        """Initialize with database connection."""
        self.db = db
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

    async def process_file(
        self,
        file_path: str,
        conversation_id: UUID,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process uploaded file and store content.

        Args:
            file_path: Path to uploaded file
            conversation_id: Conversation this file belongs to
            user_id: User who uploaded the file

        Returns:
            Document metadata including content
        """
        # Implementation

    async def get_document_content(
        self,
        document_id: UUID,
        query: Optional[str] = None
    ) -> str:
        """
        Retrieve document content with optional query filtering.

        Args:
            document_id: Document to retrieve
            query: Optional query for semantic filtering

        Returns:
            Document content (filtered if query provided)
        """
        # Implementation

    async def get_conversation_documents(
        self,
        conversation_id: UUID
    ) -> list[Dict[str, Any]]:
        """Get all documents for a conversation."""
        return await self.db.get_conversation_documents(conversation_id)


# CREATE: utils/file_handler.py
import magic
from pathlib import Path
from typing import Optional

class FileHandler:
    """Handle file operations with format detection."""

    MIME_TO_EXTENSION = {
        'application/pdf': '.pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'text/html': '.html',
        'text/plain': '.txt',
        'image/png': '.png',
        'image/jpeg': '.jpg',
        'application/json': '.json',
        'text/csv': '.csv',
    }

    @staticmethod
    def detect_file_format(file_path: str) -> str:
        """
        Detect file format using magic numbers.

        Returns:
            Detected MIME type
        """
        # Implementation

    @staticmethod
    def prepare_file_access(file_path: str) -> str:
        """
        Prepare file for processing, adding extension if needed.

        Returns:
            Path to file with correct extension
        """
        # Implementation

    @staticmethod
    def analyze_file_metadata(file_path: str) -> dict:
        """Extract file metadata for display."""
        # Implementation

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes as human-readable string."""
        # Implementation


# MODIFY: services/agent_service.py
from tools.content_retriever_tool import ContentRetrieverTool
from utils.file_handler import FileHandler
from typing import Optional, List

class AgentService:
    """Agent service with ContentRetriever tool."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.content_retriever = None

    async def initialize(self):
        """Initialize agent WITH ContentRetriever tool."""
        # Create ContentRetriever tool
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

        # Create agent with tools (ADD ContentRetriever to tools list)
        self.agent = create_agent(
            model=get_model(),
            tools=[self.content_retriever],  # ← CHANGE: Add ContentRetriever
            middleware=[DebugLoggingMiddleware(db=self.db)],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        uploaded_files: Optional[List[str]] = None  # ← ADD: File support
    ) -> Dict[str, Any]:
        """Execute agent with file context if provided."""
        # ADD: Build file context if files uploaded
        if uploaded_files:
            file_context = await self._build_file_context(uploaded_files)
            messages.insert(0, {
                "role": "system",
                "content": f"Available files:\n{file_context}"
            })

        config = {
            "configurable": {
                "thread_id": task_id
            }
        }

        result = await self.agent.ainvoke(
            {"messages": messages, "config": user_settings},
            config=config
        )

        return result

    # ADD: New helper method
    async def _build_file_context(self, file_paths: List[str]) -> str:
        """Build context string from uploaded files."""
        # Implementation
```

### Database Schema Extensions:

```python
# ADD to models/database.py (if not already present)

class DocumentModel(Base):
    """Document storage for uploaded files."""
    __tablename__ = "documents"

    id = Column(UUID, primary_key=True, default=uuid4)
    conversation_id = Column(UUID, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    conversation = relationship("ConversationModel", back_populates="documents")


# ADD to AdaptiveDatabase protocol (database/protocol.py)
@runtime_checkable
class DatabaseBackend(Protocol):
    """Protocol for database backends."""

    async def save_document(
        self,
        document_id: UUID,
        conversation_id: UUID,
        user_id: Optional[str],
        file_path: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Save processed document."""
        ...

    async def get_document(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID."""
        ...

    async def get_conversation_documents(self, conversation_id: UUID) -> List[Dict[str, Any]]:
        """Get all documents for a conversation."""
        ...
```

### Additional Dependencies:

```toml
# ADD to pyproject.toml

# Document processing
docling = "^1.0.0"                    # Advanced document parsing
python-magic = "^0.4.27"              # File format detection
sentence-transformers = "^2.2.0"      # Semantic similarity (for query filtering)

# Optional dependencies for format support
pypdf = "^3.17.0"                     # PDF processing fallback
python-docx = "^0.8.11"               # DOCX processing fallback
openpyxl = "^3.1.2"                   # XLSX processing fallback
pillow = "^10.1.0"                    # Image processing
```

### FORBIDDEN Actions:

- Implementing MCP tool patterns (wait for Phase 2.7)
- Adding web scraping or URL fetching capabilities
- Implementing vector database integration
- Creating advanced RAG capabilities
- Adding document version control
- Implementing authentication for file access
- Adding cloud storage integration
- Replacing existing Phase 2.3 agent structure
- Modifying Phase 2.3 debug logging middleware
- Breaking backward compatibility with Phase 2.2 UI

## Testing Strategy

Comprehensive testing for ContentRetriever tool and document processing:

### Unit Tests (~6 tests)

```python
# tests/tools/test_content_retriever_tool.py

import pytest
from pathlib import Path
from tools.content_retriever_tool import ContentRetrieverTool, ContentRetrieverInput

class TestContentRetrieverTool:
    """Test ContentRetriever tool functionality."""

    @pytest.fixture
    def tool(self):
        """Create tool instance."""
        return ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create sample files for testing."""
        files = {
            "text": tmp_path / "sample.txt",
            "pdf": tmp_path / "sample.pdf",
            "extensionless": tmp_path / "sample",
        }

        # Create test files
        files["text"].write_text("Sample text content")
        # ... create other test files

        return files

    @pytest.mark.asyncio
    async def test_tool_basic_text_file(self, tool, sample_files):
        """Test processing simple text file."""
        result = await tool._arun(file_path=str(sample_files["text"]))
        assert "Sample text content" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_tool_extensionless_file(self, tool, sample_files):
        """Test processing extensionless file with format detection."""
        result = await tool._arun(file_path=str(sample_files["extensionless"]))
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_tool_with_query_filter(self, tool, sample_files):
        """Test query-based content filtering."""
        result = await tool._arun(
            file_path=str(sample_files["text"]),
            query="specific topic"
        )
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_tool_rejects_urls(self, tool):
        """Test that tool rejects web URLs."""
        result = await tool._arun(file_path="https://example.com/doc.pdf")
        assert "Error" in result
        assert "local files" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_handles_missing_file(self, tool):
        """Test error handling for missing files."""
        result = await tool._arun(file_path="/nonexistent/file.txt")
        assert "Error" in result
        assert "not found" in result.lower()

    @pytest.mark.asyncio
    async def test_tool_fallback_to_basic_processing(self, tool, sample_files):
        """Test fallback to basic processing when Docling fails."""
        # Use file format that might fail in Docling
        result = await tool._arun(file_path=str(sample_files["text"]))
        assert isinstance(result, str)
        assert len(result) > 0  # Should still work via fallback


# tests/services/test_document_processor.py

import pytest
from uuid import uuid4
from services.document_processor import DocumentProcessor
from database.adapter import AdaptiveDatabase

class TestDocumentProcessor:
    """Test DocumentProcessor service."""

    @pytest.fixture
    async def processor(self, adaptive_db):
        """Create processor instance."""
        return DocumentProcessor(db=adaptive_db)

    @pytest.mark.asyncio
    async def test_process_file_success(self, processor, sample_files):
        """Test successful file processing."""
        result = await processor.process_file(
            file_path=str(sample_files["text"]),
            conversation_id=uuid4()
        )

        assert result["status"] == "processed"
        assert "document_id" in result
        assert "content" in result
        assert len(result["content"]) > 0

    @pytest.mark.asyncio
    async def test_get_document_content(self, processor, sample_files):
        """Test retrieving document content."""
        # First process file
        result = await processor.process_file(
            file_path=str(sample_files["text"]),
            conversation_id=uuid4()
        )

        # Then retrieve
        from uuid import UUID
        content = await processor.get_document_content(
            document_id=UUID(result["document_id"])
        )

        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_get_conversation_documents(self, processor, sample_files):
        """Test retrieving all documents for conversation."""
        conv_id = uuid4()

        # Process multiple files
        await processor.process_file(str(sample_files["text"]), conv_id)

        # Retrieve all
        docs = await processor.get_conversation_documents(conv_id)
        assert len(docs) >= 1
        assert all("document_id" in doc for doc in docs)


# tests/utils/test_file_handler.py

import pytest
from pathlib import Path
from utils.file_handler import FileHandler

class TestFileHandler:
    """Test file handling utilities."""

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create sample files."""
        files = {
            "with_ext": tmp_path / "sample.txt",
            "no_ext": tmp_path / "sample",
        }

        for f in files.values():
            f.write_text("Sample content")

        return files

    def test_detect_file_format(self, sample_files):
        """Test MIME type detection."""
        mime_type = FileHandler.detect_file_format(str(sample_files["with_ext"]))
        assert mime_type.startswith("text/")

    def test_prepare_file_access_with_extension(self, sample_files):
        """Test prepare_file_access preserves existing extension."""
        result = FileHandler.prepare_file_access(str(sample_files["with_ext"]))
        assert Path(result).suffix == ".txt"

    def test_prepare_file_access_without_extension(self, sample_files):
        """Test prepare_file_access adds extension to extensionless file."""
        result = FileHandler.prepare_file_access(str(sample_files["no_ext"]))
        assert Path(result).suffix in FileHandler.MIME_TO_EXTENSION.values()

    def test_analyze_file_metadata(self, sample_files):
        """Test file metadata extraction."""
        metadata = FileHandler.analyze_file_metadata(str(sample_files["with_ext"]))

        assert "filename" in metadata
        assert "size_bytes" in metadata
        assert "size_human" in metadata
        assert "mime_type" in metadata
        assert metadata["filename"] == "sample.txt"

    def test_format_size_human_readable(self):
        """Test human-readable size formatting."""
        assert "1.0 KB" in FileHandler._format_size(1024)
        assert "1.0 MB" in FileHandler._format_size(1024 * 1024)
        assert "500 B" in FileHandler._format_size(500)
```

### Integration Tests

```python
# tests/integration/test_agent_with_content_retriever.py

import pytest
from services.agent_service import AgentService
from database.adapter import AdaptiveDatabase

class TestAgentWithContentRetriever:
    """Test agent with ContentRetriever tool integration."""

    @pytest.fixture
    async def agent_service(self, adaptive_db):
        """Create and initialize agent service."""
        service = AgentService(db=adaptive_db)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_agent_has_content_retriever_tool(self, agent_service):
        """Test that agent has ContentRetriever in tools list."""
        assert agent_service.content_retriever is not None
        assert agent_service.content_retriever.name == "content_retriever"

    @pytest.mark.asyncio
    async def test_agent_can_process_files(self, agent_service, sample_files):
        """Test agent can answer questions about uploaded files."""
        messages = [
            {"role": "user", "content": "What's in the uploaded file?"}
        ]

        result = await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="test-task",
            uploaded_files=[str(sample_files["text"])]
        )

        assert "messages" in result
        # Should have system message with file context
        assert any(msg["role"] == "system" for msg in result["messages"])

    @pytest.mark.asyncio
    async def test_tool_calls_logged_in_debug_logs(self, agent_service, adaptive_db, sample_files):
        """Test that ContentRetriever tool calls appear in debug logs."""
        messages = [
            {"role": "user", "content": "Read the file"}
        ]

        await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="test-task-2",
            uploaded_files=[str(sample_files["text"])]
        )

        # Check debug logs for tool usage
        logs = await adaptive_db.get_execution_logs(task_id="test-task-2")
        assert len(logs) > 0

        # Tool calls should be logged
        tool_calls = await adaptive_db.get_tool_calls_for_execution(logs[0]["execution_log_id"])
        # May or may not have tool calls depending on agent decision
        # But structure should be present
        assert isinstance(tool_calls, list)
```

### Test Execution:

```bash
# Run tool-specific tests
uv run pytest tests/tools/test_content_retriever_tool.py -v

# Run document processor tests
uv run pytest tests/services/test_document_processor.py -v

# Run file handler tests
uv run pytest tests/utils/test_file_handler.py -v

# Run integration tests
uv run pytest tests/integration/test_agent_with_content_retriever.py -v

# Full test suite
make test
```

## Success Criteria

Phase 2.4 is complete when ALL of the following are verified:

### Functional Requirements:

- [ ] **ContentRetrieverTool Created**: LangChain BaseTool implemented with correct schema
- [ ] **Agent Has Tool**: ContentRetriever appears in agent's tools list
- [ ] **File Processing Works**: Uploaded files are actually processed (not stubbed)
- [ ] **Agent Can Access Content**: Agent can answer questions about uploaded files
- [ ] **Docling Integration**: Advanced processing works for complex documents
- [ ] **Fallback Processing**: Basic processing works when Docling fails
- [ ] **Format Detection**: Extensionless files handled correctly
- [ ] **Tool Calls Logged**: ContentRetriever usage appears in debug logs
- [ ] **DocumentProcessor Real**: Phase 2.2 stub replaced with real implementation
- [ ] **Multi-Format Support**: PDF, DOCX, XLSX, text, CSV, JSON all work

### Quality Requirements:

- [ ] **Test Coverage**: >85% coverage for new code
- [ ] **All Tests Pass**: Unit tests + integration tests pass
- [ ] **Type Checking**: `make quality` passes with no mypy errors
- [ ] **No Regressions**: Phase 2.3 functionality still works
- [ ] **Debug Logs Clean**: No errors in execution logs during testing
- [ ] **Performance**: File processing completes in <5s for typical documents

### Documentation Requirements:

- [ ] **Tool Usage**: Examples of using ContentRetriever in documentation
- [ ] **Supported Formats**: List of supported file formats documented
- [ ] **Fallback Behavior**: Docling vs basic processing documented
- [ ] **Error Handling**: Common errors and solutions documented

### Integration Requirements:

- [ ] **Phase 2.2 UI Works**: File upload UI from Phase 2.2 works with real processing
- [ ] **Phase 2.3 Debug Logs Work**: Tool calls appear in execution logs
- [ ] **Database Schema**: Document storage schema created and working
- [ ] **No Breaking Changes**: Existing conversations and messages still work

### Validation Commands:

```bash
# Code quality
make quality

# Full test suite
make test

# Specific Phase 2.4 tests
uv run pytest tests/tools/ tests/services/test_document_processor.py -v

# Integration validation
uv run pytest tests/integration/test_agent_with_content_retriever.py -v

# Manual validation
make start-app-debug  # Check logs for tool calls
```

### Ready for Phase 2.5 When:

- All success criteria above are met
- Agent successfully processes files and answers questions
- Tool calls visible in debug logs
- No errors in test suite
- Documentation updated
- Phase 2.3 functionality preserved

**Next Phase:** Phase 2.5 adds built-in middleware (PII redaction, summarization, human-in-the-loop) to the agent.
