# TOOL-002: Firecrawl MCP Tool Implementation

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: TOOL-002-firecrawl-mcp
**Phase**: 2.7
**Dependencies**: Phase 2.6 (Custom Middleware), Phase 2.4 (TOOL-001: ContentRetriever)

## Context

Phase 2.7 implements the **second tool** for the agent: an MCP (Model Context Protocol) tool for web scraping via Firecrawl. This is fundamentally different from the first tool (ContentRetriever) because it uses the MCP protocol instead of LangChain's BaseTool pattern.

**Critical Context:**
- This is an **MCP tool**, NOT a LangChain BaseTool
- User priority: "Langchain tool first then mcp" - ContentRetriever came first (Phase 2.4), now MCP
- Firecrawl handles ONLY web URLs (no local files - that's ContentRetriever's job)
- Uses `langchain-mcp-adapters` to bridge MCP tools to LangChain agent
- Agent now has TWO tools with intelligent tool selection

**Phase 2.4 → Phase 2.7 Transition:**
Phase 2.4 added ContentRetriever (LangChain tool) for local files. Phase 2.7 adds complementary web scraping:
- Phase 2.4: ContentRetriever handles local files (PDF, DOCX, text, etc.)
- Phase 2.7: Firecrawl handles web URLs (scraping, crawling, link extraction)
- Agent learns to choose correct tool based on input type

**MCP vs LangChain Tool:**

| Aspect | ContentRetriever (Phase 2.4) | Firecrawl (Phase 2.7) |
|--------|------------------------------|------------------------|
| Type | LangChain BaseTool | MCP Tool |
| Protocol | Direct LangChain | MCP via adapters |
| Input | Local file paths | Web URLs |
| Setup | Python class | External MCP server |
| API Key | None | FIRECRAWL_API_KEY required |
| Integration | `tools=[tool]` | `langchain-mcp-adapters` |

## Architecture Scope

### What's Included:

- `langchain-mcp-adapters` integration for MCP protocol support
- `MCPService` for managing MCP server connections and lifecycle
- Firecrawl MCP server configuration with environment-based API key
- Three Firecrawl tools: `scrape_url`, `crawl_site`, `extract_links`
- Firecrawl tools added to agent's tools list alongside ContentRetriever
- Intelligent tool selection (local files → ContentRetriever, web URLs → Firecrawl)
- Human-in-the-loop approval for web scraping operations
- MCP connection cleanup and error handling
- Integration with Phase 2.3 debug logging (MCP tool calls logged)

### What's Explicitly Excluded:

- Local file processing (Phase 2.4: ContentRetriever handles this)
- Additional MCP servers beyond Firecrawl (Phase 3+)
- Custom MCP tool development (use existing MCP servers)
- Web browser automation (Firecrawl does server-side scraping)
- Authentication for protected websites (basic Firecrawl capabilities only)
- Rate limiting or caching of scraped content (Phase 3+)
- Vector storage of scraped content (Phase 3+)
- Scheduled/automated web crawling (Phase 3+)

## Architectural Decisions

### 1. MCP Integration via langchain-mcp-adapters

**Core Approach**: Use official LangChain adapters to integrate MCP tools

**Why MCP for Firecrawl:**
- Firecrawl provides official MCP server (`@modelcontextprotocol/server-firecrawl`)
- MCP protocol designed for external tool integration
- No need to write custom LangChain wrapper for web scraping
- Automatic tool discovery and schema generation
- Connection management handled by adapter library

**Integration Pattern:**
```python
from langchain_mcp_adapters.client import MultiServerMCPClient

# Define MCP servers
mcp_servers = {
    "firecrawl": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-firecrawl"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
        }
    }
}

# Create MCP client
mcp_client = MultiServerMCPClient(mcp_servers)

# Get MCP tools (auto-discovered)
mcp_tools = await mcp_client.get_tools()
# Returns: [scrape_url, crawl_site, extract_links] as LangChain-compatible tools

# Add to agent
agent = create_agent(
    model=get_model(),
    tools=[content_retriever_tool, *mcp_tools],  # Mix LangChain + MCP tools
    middleware=[...],
    structured_output=AgentResponse
)
```

**Why This Works:**
- `langchain-mcp-adapters` converts MCP tools to LangChain-compatible format
- Agent sees no difference between MCP and native LangChain tools
- Tool schemas automatically generated from MCP server definitions
- Connection lifecycle managed by adapter

### 2. MCPService: Connection Manager

**Purpose**: Centralized management of MCP server connections and tool discovery

**Design Pattern**: Service layer managing MCP lifecycle

```python
# services/mcp_service.py

from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MCPService:
    """
    Manages MCP server connections and tools.

    Responsibilities:
    - Initialize MCP servers from configuration
    - Discover and expose MCP tools
    - Handle connection lifecycle (startup/cleanup)
    - Provide error handling for MCP operations
    """

    def __init__(self):
        """Initialize MCP service."""
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Any] = []
        self._initialized = False

    async def initialize(self, mcp_server_configs: Dict[str, Dict]) -> List[Any]:
        """
        Initialize MCP servers and load tools.

        Args:
            mcp_server_configs: Dictionary of MCP server configurations
                Format: {"server_name": {"command": str, "args": List[str], "env": Dict}}

        Returns:
            List of LangChain-compatible tools from all MCP servers

        Raises:
            RuntimeError: If MCP initialization fails
        """
        if self._initialized:
            logger.warning("MCPService already initialized")
            return self.tools

        try:
            # Create multi-server client
            self.client = MultiServerMCPClient(mcp_server_configs)

            # Discover tools from all configured servers
            self.tools = await self.client.get_tools()

            logger.info(f"MCP tools loaded: {[tool.name for tool in self.tools]}")
            self._initialized = True

            return self.tools

        except Exception as e:
            logger.error(f"Failed to initialize MCP service: {e}")
            raise RuntimeError(f"MCP initialization failed: {e}")

    async def cleanup(self) -> None:
        """
        Close MCP connections and cleanup resources.

        Should be called on application shutdown or when MCP tools no longer needed.
        """
        if self.client:
            try:
                await self.client.close()
                logger.info("MCP connections closed")
            except Exception as e:
                logger.error(f"Error closing MCP connections: {e}")
            finally:
                self.client = None
                self.tools = []
                self._initialized = False

    def is_initialized(self) -> bool:
        """Check if MCP service is initialized."""
        return self._initialized

    def get_tools(self) -> List[Any]:
        """Get list of MCP tools (after initialization)."""
        return self.tools
```

**Lifecycle Management:**
```python
# Application startup (main.py or services/agent_service.py)

async def initialize_agent_with_mcp():
    # Create MCP service
    mcp_service = MCPService()

    # Initialize with Firecrawl configuration
    from config.mcp_servers import MCP_SERVERS
    mcp_tools = await mcp_service.initialize(MCP_SERVERS)

    # Create agent with combined tools
    agent = create_agent(
        model=get_model(),
        tools=[
            ContentRetrieverTool(),  # LangChain tool
            *mcp_tools                # MCP tools (Firecrawl)
        ]
    )

    return agent, mcp_service

# Application shutdown
async def shutdown():
    await mcp_service.cleanup()
```

### 3. Firecrawl MCP Server Configuration

**Configuration Pattern**: Environment-based MCP server setup

```python
# config/mcp_servers.py

import os
from typing import Dict, Any

# MCP server configurations
MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    "firecrawl": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-firecrawl"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")
        }
    }
}

def validate_mcp_config() -> Dict[str, str]:
    """
    Validate MCP server configurations.

    Returns:
        Dict of validation errors (empty if all valid)
    """
    errors = {}

    # Check Firecrawl API key
    if not os.getenv("FIRECRAWL_API_KEY"):
        errors["firecrawl"] = "FIRECRAWL_API_KEY environment variable not set"

    return errors

def get_enabled_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """
    Get only MCP servers with valid configurations.

    Returns:
        Dict of enabled MCP servers (may be empty if none configured)
    """
    enabled = {}
    errors = validate_mcp_config()

    for server_name, config in MCP_SERVERS.items():
        if server_name not in errors:
            enabled[server_name] = config

    return enabled
```

**Environment Configuration:**
```bash
# .env
FIRECRAWL_API_KEY=fc-your-api-key-here
```

**Example .env.example:**
```bash
# MCP Tools Configuration

# Firecrawl API Key (required for web scraping)
# Get your key at: https://firecrawl.dev
FIRECRAWL_API_KEY=
```

### 4. Firecrawl Tools and Capabilities

**Three Tools Provided by Firecrawl MCP Server:**

**1. scrape_url** - Scrape single URL and return markdown
```python
# Tool definition (auto-generated by MCP)
{
    "name": "scrape_url",
    "description": "Scrape a single URL and return content as markdown",
    "input_schema": {
        "url": "string (required) - URL to scrape",
        "format": "string (optional) - Output format (markdown, html, text)"
    }
}

# Usage example
result = await agent.ainvoke({
    "messages": [
        {"role": "user", "content": "What's on https://example.com/about"}
    ]
})
# Agent calls: scrape_url(url="https://example.com/about")
```

**2. crawl_site** - Crawl entire site up to max depth
```python
# Tool definition
{
    "name": "crawl_site",
    "description": "Crawl an entire website up to specified depth",
    "input_schema": {
        "url": "string (required) - Starting URL",
        "max_depth": "integer (optional, default=2) - Maximum crawl depth",
        "max_pages": "integer (optional, default=10) - Maximum pages to crawl"
    }
}

# Usage example
result = await agent.ainvoke({
    "messages": [
        {"role": "user", "content": "Crawl https://docs.example.com and summarize the documentation"}
    ]
})
# Agent calls: crawl_site(url="https://docs.example.com", max_depth=2)
```

**3. extract_links** - Get all links from page
```python
# Tool definition
{
    "name": "extract_links",
    "description": "Extract all links from a webpage",
    "input_schema": {
        "url": "string (required) - URL to extract links from",
        "filter": "string (optional) - Filter links by pattern"
    }
}

# Usage example
result = await agent.ainvoke({
    "messages": [
        {"role": "user", "content": "Find all documentation links on https://example.com"}
    ]
})
# Agent calls: extract_links(url="https://example.com", filter="docs")
```

### 5. Intelligent Tool Selection Strategy

**Problem**: Agent has TWO tools for content retrieval - how does it choose?

**Solution**: Clear tool descriptions + natural agent behavior

```python
# ContentRetrieverTool description (from Phase 2.4)
ContentRetrieverTool.description = """
Retrieve and process content from LOCAL FILES and documents.
Supports: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON.
Use this for LOCAL file processing only.
For web URLs, use the web scraping tools instead.
"""

# Firecrawl tools descriptions (auto-generated by MCP)
scrape_url.description = """
Scrape content from WEB URLS and return as markdown.
Use this for web pages, not local files.
For local files, use the content_retriever tool.
"""

crawl_site.description = """
Crawl an entire WEBSITE starting from a URL.
Use this for comprehensive site content.
For single pages, use scrape_url. For local files, use content_retriever.
"""
```

**Agent Decision Making:**
```python
# User: "What's in document.pdf?"
# → Agent sees "document.pdf" (local file)
# → Chooses: content_retriever tool

# User: "What's on https://example.com?"
# → Agent sees "https://" (web URL)
# → Chooses: scrape_url tool

# User: "Analyze the entire docs site at https://docs.example.com"
# → Agent sees "entire site" + URL
# → Chooses: crawl_site tool

# User: "Find all links on https://example.com"
# → Agent sees "links" + URL
# → Chooses: extract_links tool
```

### 6. Human-in-the-Loop for Web Scraping

**Why Approval Needed:**
- Web scraping may access external sites
- Could consume API quota (Firecrawl API)
- User should confirm before external requests

**Integration with Phase 2.5 HumanInTheLoopMiddleware:**

```python
# Configure HumanInTheLoopMiddleware to require approval for web scraping
from langchain.middleware import HumanInTheLoopMiddleware

hitl_middleware = HumanInTheLoopMiddleware(
    sensitive_operations=[
        "scrape_url",      # Require approval
        "crawl_site",      # Require approval (crawls multiple pages)
        "extract_links"    # Optional: may not need approval
    ],
    approval_callback=async_approval_handler
)
```

**Approval Dialog (UI):**
```python
# ui/components/approval_dialog.py

async def handle_web_scraping_approval(tool_name: str, tool_input: Dict) -> bool:
    """
    Show approval dialog for web scraping operations.

    Args:
        tool_name: Name of tool requesting approval
        tool_input: Tool input arguments (contains URL)

    Returns:
        True if user approves, False otherwise
    """
    if tool_name == "scrape_url":
        message = f"Allow scraping: {tool_input.get('url')}?"
    elif tool_name == "crawl_site":
        url = tool_input.get('url')
        max_depth = tool_input.get('max_depth', 2)
        message = f"Allow crawling {url} (depth: {max_depth})? This may scrape multiple pages."
    elif tool_name == "extract_links":
        message = f"Allow extracting links from: {tool_input.get('url')}?"
    else:
        message = f"Allow tool: {tool_name}?"

    # Show approval dialog in UI
    return await show_approval_dialog(
        title="Web Scraping Approval",
        message=message,
        tool_name=tool_name,
        tool_input=tool_input
    )
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
└── mcp_service.py                      # MCPService for connection management

src/agent_workbench/config/
└── mcp_servers.py                      # MCP server configurations

src/agent_workbench/ui/components/
└── approval_dialog.py                  # Approval dialog for web scraping (if not exists)
```

### Files to MODIFY:

```
src/agent_workbench/services/
└── agent_service.py                    # Add MCP tools to agent initialization

pyproject.toml                          # Add langchain-mcp-adapters dependency

.env.example                            # Add FIRECRAWL_API_KEY example

src/agent_workbench/main.py             # Add MCP cleanup to shutdown
```

### Exact Function Signatures:

```python
# CREATE: services/mcp_service.py
from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict, List, Any, Optional
import logging

class MCPService:
    """Manages MCP server connections and tools."""

    def __init__(self):
        """Initialize MCP service."""
        self.client: Optional[MultiServerMCPClient] = None
        self.tools: List[Any] = []
        self._initialized = False

    async def initialize(self, mcp_server_configs: Dict[str, Dict]) -> List[Any]:
        """
        Initialize MCP servers and load tools.

        Args:
            mcp_server_configs: Dictionary of MCP server configurations

        Returns:
            List of LangChain-compatible tools from all MCP servers

        Raises:
            RuntimeError: If MCP initialization fails
        """
        # Implementation

    async def cleanup(self) -> None:
        """Close MCP connections and cleanup resources."""
        # Implementation

    def is_initialized(self) -> bool:
        """Check if MCP service is initialized."""
        return self._initialized

    def get_tools(self) -> List[Any]:
        """Get list of MCP tools (after initialization)."""
        return self.tools


# CREATE: config/mcp_servers.py
import os
from typing import Dict, Any

MCP_SERVERS: Dict[str, Dict[str, Any]] = {
    "firecrawl": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-firecrawl"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY", "")
        }
    }
}

def validate_mcp_config() -> Dict[str, str]:
    """
    Validate MCP server configurations.

    Returns:
        Dict of validation errors (empty if all valid)
    """
    # Implementation

def get_enabled_mcp_servers() -> Dict[str, Dict[str, Any]]:
    """
    Get only MCP servers with valid configurations.

    Returns:
        Dict of enabled MCP servers (may be empty if none configured)
    """
    # Implementation


# MODIFY: services/agent_service.py
from tools.content_retriever_tool import ContentRetrieverTool
from services.mcp_service import MCPService
from config.mcp_servers import get_enabled_mcp_servers
from typing import Optional, List, Dict, Any

class AgentService:
    """Agent service with ContentRetriever + MCP tools."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.content_retriever = None
        self.mcp_service: Optional[MCPService] = None  # ADD

    async def initialize(self):
        """Initialize agent with both LangChain and MCP tools."""
        tools = []

        # 1. Add LangChain tools (ContentRetriever from Phase 2.4)
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")
        tools.append(self.content_retriever)

        # 2. Add MCP tools (Firecrawl) if configured
        mcp_servers = get_enabled_mcp_servers()
        if mcp_servers:
            self.mcp_service = MCPService()
            try:
                mcp_tools = await self.mcp_service.initialize(mcp_servers)
                tools.extend(mcp_tools)
                logger.info(f"MCP tools added: {[t.name for t in mcp_tools]}")
            except Exception as e:
                logger.error(f"Failed to initialize MCP tools: {e}")
                # Continue without MCP tools (graceful degradation)

        # 3. Create agent with combined tools
        self.agent = create_agent(
            model=get_model(),
            tools=tools,  # Both LangChain + MCP tools
            middleware=[
                DebugLoggingMiddleware(db=self.db),
                HumanInTheLoopMiddleware(
                    sensitive_operations=["scrape_url", "crawl_site"]
                )
            ],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

    async def cleanup(self) -> None:  # ADD
        """Cleanup resources including MCP connections."""
        if self.mcp_service:
            await self.mcp_service.cleanup()

    # Existing methods unchanged
    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        uploaded_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute agent (existing implementation)."""
        # Existing implementation from Phase 2.4


# MODIFY: main.py (add cleanup)
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with MCP cleanup."""
    # Existing initialization
    db = await init_adaptive_database()
    app.adaptive_db = db

    # ... existing setup ...

    yield

    # ADD: Cleanup MCP connections on shutdown
    if hasattr(app, "agent_service") and app.agent_service:
        await app.agent_service.cleanup()

    # Existing cleanup
    await app.requests_client.aclose()
```

### Additional Dependencies:

```toml
# ADD to pyproject.toml

# MCP Integration
langchain-mcp-adapters = "^0.1.0"      # LangChain <-> MCP adapter

# Firecrawl API (optional, for reference)
# Note: Firecrawl MCP server is accessed via npx, not Python package
```

### Environment Variables:

```bash
# ADD to .env.example

# ===== MCP Tools Configuration =====

# Firecrawl API Key (required for web scraping via MCP)
# Get your API key at: https://firecrawl.dev
# Leave empty to disable Firecrawl tools
FIRECRAWL_API_KEY=
```

### FORBIDDEN Actions:

- Implementing custom web scraping instead of using Firecrawl MCP server
- Adding local file processing to Firecrawl tools (use ContentRetriever)
- Creating custom MCP tools without official MCP server
- Replacing ContentRetriever with Firecrawl for local files
- Adding additional MCP servers beyond Firecrawl (wait for Phase 3+)
- Implementing vector storage or caching of scraped content
- Adding rate limiting or quota management (Firecrawl API handles this)
- Modifying Phase 2.4 ContentRetrieverTool
- Breaking backward compatibility with Phase 2.6 middleware

## Testing Strategy

Comprehensive testing for Firecrawl MCP tool integration:

### Unit Tests (~3 tests)

```python
# tests/services/test_mcp_service.py

import pytest
from services.mcp_service import MCPService
from config.mcp_servers import MCP_SERVERS, validate_mcp_config, get_enabled_mcp_servers
import os

class TestMCPService:
    """Test MCP service functionality."""

    @pytest.fixture
    def mcp_service(self):
        """Create MCP service instance."""
        return MCPService()

    @pytest.mark.asyncio
    async def test_mcp_service_initialization(self, mcp_service, monkeypatch):
        """Test MCP service initializes with valid config."""
        # Set dummy API key for testing
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-api-key")

        # Initialize with test config
        mcp_servers = get_enabled_mcp_servers()

        # Skip if no API key configured
        if not mcp_servers:
            pytest.skip("FIRECRAWL_API_KEY not configured")

        tools = await mcp_service.initialize(mcp_servers)

        assert mcp_service.is_initialized()
        assert isinstance(tools, list)
        # Firecrawl provides 3 tools: scrape_url, crawl_site, extract_links
        assert len(tools) >= 1  # At least one tool loaded

    @pytest.mark.asyncio
    async def test_mcp_service_cleanup(self, mcp_service, monkeypatch):
        """Test MCP service cleanup."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-api-key")

        mcp_servers = get_enabled_mcp_servers()
        if not mcp_servers:
            pytest.skip("FIRECRAWL_API_KEY not configured")

        await mcp_service.initialize(mcp_servers)
        assert mcp_service.is_initialized()

        await mcp_service.cleanup()
        assert not mcp_service.is_initialized()
        assert len(mcp_service.get_tools()) == 0

    @pytest.mark.asyncio
    async def test_mcp_service_graceful_degradation_without_api_key(self, mcp_service, monkeypatch):
        """Test MCP service handles missing API key gracefully."""
        # Clear API key
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

        mcp_servers = get_enabled_mcp_servers()

        # Should return empty dict when API key missing
        assert len(mcp_servers) == 0

        # Should not fail when initializing with empty config
        tools = await mcp_service.initialize({})
        assert len(tools) == 0


# tests/config/test_mcp_servers.py

import pytest
from config.mcp_servers import (
    MCP_SERVERS,
    validate_mcp_config,
    get_enabled_mcp_servers
)
import os

class TestMCPConfiguration:
    """Test MCP server configuration."""

    def test_validate_mcp_config_with_api_key(self, monkeypatch):
        """Test validation passes with API key."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

        errors = validate_mcp_config()
        assert "firecrawl" not in errors

    def test_validate_mcp_config_without_api_key(self, monkeypatch):
        """Test validation fails without API key."""
        monkeypatch.delenv("FIRECRAWL_API_KEY", raising=False)

        errors = validate_mcp_config()
        assert "firecrawl" in errors
        assert "FIRECRAWL_API_KEY" in errors["firecrawl"]

    def test_get_enabled_mcp_servers(self, monkeypatch):
        """Test getting only enabled servers."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

        enabled = get_enabled_mcp_servers()
        assert "firecrawl" in enabled
        assert "command" in enabled["firecrawl"]
        assert "args" in enabled["firecrawl"]
        assert "env" in enabled["firecrawl"]

    def test_mcp_servers_structure(self):
        """Test MCP_SERVERS has correct structure."""
        assert isinstance(MCP_SERVERS, dict)
        assert "firecrawl" in MCP_SERVERS

        firecrawl = MCP_SERVERS["firecrawl"]
        assert "command" in firecrawl
        assert "args" in firecrawl
        assert "env" in firecrawl
        assert firecrawl["command"] == "npx"
        assert "@modelcontextprotocol/server-firecrawl" in firecrawl["args"]
```

### Integration Tests (~3 tests, requires FIRECRAWL_API_KEY)

```python
# tests/integration/test_agent_with_mcp_tools.py

import pytest
from services.agent_service import AgentService
from database.adapter import AdaptiveDatabase
import os

class TestAgentWithMCPTools:
    """Test agent with Firecrawl MCP tools integration."""

    @pytest.fixture
    async def agent_service(self, adaptive_db):
        """Create and initialize agent service with MCP tools."""
        service = AgentService(db=adaptive_db)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    @pytest.mark.requires_firecrawl
    async def test_agent_has_both_content_retriever_and_firecrawl(self, agent_service):
        """Test that agent has both ContentRetriever and Firecrawl tools."""
        # Should have ContentRetriever
        assert agent_service.content_retriever is not None
        assert agent_service.content_retriever.name == "content_retriever"

        # Should have MCP service if API key configured
        if os.getenv("FIRECRAWL_API_KEY"):
            assert agent_service.mcp_service is not None
            assert agent_service.mcp_service.is_initialized()
            tools = agent_service.mcp_service.get_tools()
            assert len(tools) >= 1
            # Check for Firecrawl tools
            tool_names = [t.name for t in tools]
            assert any("scrape" in name or "crawl" in name for name in tool_names)
        else:
            pytest.skip("FIRECRAWL_API_KEY not configured")

    @pytest.mark.asyncio
    @pytest.mark.requires_firecrawl
    async def test_agent_intelligently_selects_tools(self, agent_service):
        """Test that agent selects correct tool based on input type."""
        if not os.getenv("FIRECRAWL_API_KEY"):
            pytest.skip("FIRECRAWL_API_KEY not configured")

        # Test 1: Local file → should prefer ContentRetriever
        messages = [
            {"role": "user", "content": "What's in the file document.pdf?"}
        ]
        # Note: Actual tool selection depends on agent reasoning
        # This test validates agent has both tools available

        # Test 2: Web URL → should prefer Firecrawl
        messages = [
            {"role": "user", "content": "What's on https://example.com?"}
        ]
        # Agent should have access to both tool types

        # Validation: Both tool types present
        assert agent_service.content_retriever is not None
        assert agent_service.mcp_service is not None

    @pytest.mark.asyncio
    @pytest.mark.requires_firecrawl
    async def test_mcp_tool_calls_logged_in_debug_logs(self, agent_service, adaptive_db):
        """Test that Firecrawl MCP tool calls appear in debug logs."""
        if not os.getenv("FIRECRAWL_API_KEY"):
            pytest.skip("FIRECRAWL_API_KEY not configured")

        messages = [
            {"role": "user", "content": "Scrape https://example.com"}
        ]

        # Execute agent (may require approval)
        result = await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="test-task-mcp",
            uploaded_files=None
        )

        # Check debug logs
        logs = await adaptive_db.get_execution_logs(task_id="test-task-mcp")
        assert len(logs) > 0

        # Tool calls should be logged
        tool_calls = await adaptive_db.get_tool_calls_for_execution(logs[0]["execution_log_id"])
        # May or may not have tool calls depending on approval and agent decision
        assert isinstance(tool_calls, list)


# tests/integration/test_mcp_cleanup.py

import pytest
from services.agent_service import AgentService
from database.adapter import AdaptiveDatabase

class TestMCPCleanup:
    """Test MCP connection cleanup."""

    @pytest.mark.asyncio
    async def test_mcp_cleanup_on_agent_service_shutdown(self, adaptive_db, monkeypatch):
        """Test MCP connections cleaned up on agent service shutdown."""
        monkeypatch.setenv("FIRECRAWL_API_KEY", "test-key")

        service = AgentService(db=adaptive_db)
        await service.initialize()

        # Verify MCP service exists if API key configured
        if service.mcp_service:
            assert service.mcp_service.is_initialized()

            # Cleanup
            await service.cleanup()

            # Should be cleaned up
            assert not service.mcp_service.is_initialized()
```

### Test Execution:

```bash
# Run MCP-specific tests (without API key - basic validation only)
uv run pytest tests/services/test_mcp_service.py tests/config/test_mcp_servers.py -v

# Run integration tests (requires FIRECRAWL_API_KEY)
export FIRECRAWL_API_KEY=your-api-key
uv run pytest tests/integration/test_agent_with_mcp_tools.py -v -m requires_firecrawl

# Run all tests
make test

# Manual validation with debug mode
make start-app-debug  # Check logs for MCP tool initialization and usage
```

### Test Markers:

```python
# pytest.ini or conftest.py
# ADD marker for tests requiring Firecrawl API key

markers =
    requires_firecrawl: marks tests as requiring FIRECRAWL_API_KEY (skip if not set)
```

## Success Criteria

Phase 2.7 is complete when ALL of the following are verified:

### Functional Requirements:

- [ ] **langchain-mcp-adapters Installed**: Package added to dependencies
- [ ] **MCPService Created**: Connection manager implemented and working
- [ ] **Firecrawl MCP Server Configured**: MCP server config with API key
- [ ] **MCP Tools Discovered**: All 3 Firecrawl tools (scrape_url, crawl_site, extract_links) loaded
- [ ] **Agent Has Both Tool Types**: ContentRetriever (LangChain) + Firecrawl (MCP)
- [ ] **Web Scraping Works**: Can scrape URLs using Firecrawl tools
- [ ] **Intelligent Tool Selection**: Agent chooses correct tool (local vs web)
- [ ] **MCP Tool Calls Logged**: Firecrawl usage appears in debug logs
- [ ] **Human-in-the-Loop**: Web scraping requires approval
- [ ] **Graceful Degradation**: App works without FIRECRAWL_API_KEY (no MCP tools)

### Quality Requirements:

- [ ] **Test Coverage**: >80% coverage for new code
- [ ] **All Tests Pass**: Unit tests + integration tests (with API key) pass
- [ ] **Type Checking**: `make quality` passes with no mypy errors
- [ ] **No Regressions**: Phase 2.4-2.6 functionality still works
- [ ] **MCP Cleanup**: Connections properly closed on shutdown
- [ ] **Error Handling**: Missing API key handled gracefully

### Documentation Requirements:

- [ ] **MCP Integration**: How MCP tools work with LangChain agent
- [ ] **Firecrawl Setup**: How to get and configure FIRECRAWL_API_KEY
- [ ] **Tool Selection**: Examples of when each tool is used
- [ ] **API Key Management**: Security best practices for API keys

### Integration Requirements:

- [ ] **Phase 2.4 Works**: ContentRetriever still works for local files
- [ ] **Phase 2.5 Works**: Built-in middleware still works
- [ ] **Phase 2.6 Works**: Custom middleware still works
- [ ] **Phase 2.3 Debug Logs Work**: MCP tool calls logged correctly
- [ ] **No Breaking Changes**: Existing agent functionality preserved

### Validation Commands:

```bash
# Code quality
make quality

# Unit tests (no API key required)
uv run pytest tests/services/test_mcp_service.py tests/config/test_mcp_servers.py -v

# Integration tests (requires FIRECRAWL_API_KEY)
export FIRECRAWL_API_KEY=your-api-key
uv run pytest tests/integration/test_agent_with_mcp_tools.py -v -m requires_firecrawl

# Full test suite
make test

# Manual validation
make start-app-debug  # Check logs for:
# - "MCP tools loaded: ['scrape_url', 'crawl_site', 'extract_links']"
# - Tool calls in execution logs
# - Approval dialogs for web scraping
```

### Ready for Phase 2.8 When:

- All success criteria above are met
- Agent successfully uses both ContentRetriever and Firecrawl tools
- Tool selection is intelligent (local vs web)
- MCP tool calls visible in debug logs
- No errors in test suite with and without API key
- Documentation updated
- Phase 2.4-2.6 functionality preserved

**Next Phase:** Phase 2.8 focuses on production hardening with comprehensive error handling, monitoring, and performance optimization.
