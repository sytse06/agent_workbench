# Phase 2 Architecture Plan: Agent Implementation

**Status:** Planning Phase
**Date Created:** 2025-10-12
**Last Updated:** 2025-10-13 (Session management fix)
**Based On:** LangChain v1.0 official patterns
**Release Version:** v0.2.0 (completion of Phase 2)

**Recent Changes:**
- **2025-10-13:** Fixed session management to prevent database pollution
  - Added `get_active_session()` method with 30-minute timeout
  - Added `update_session_activity()` method for session reuse
  - Updated `on_load()` to check for existing sessions before creating new ones
  - Added database backend methods: `get_active_user_session()`, `update_session_activity()`
- **2025-10-13:** Enhanced PWA manifest.json with comprehensive metadata
  - Added `scope` field for URL handling
  - Added `categories` for app store classification (productivity, developer-tools, utilities)
  - Added 8 icon sizes (72px to 512px) for all platforms
  - Added `screenshots` array with desktop/mobile examples (required for app stores)
  - Added `shortcuts` for quick actions (New Chat, Settings, History)
  - Added `share_target` for file sharing integration
  - Added documentation for icon sizes, screenshot requirements, and shortcuts best practices
- **2025-10-13:** Optimized execution logs with comprehensive database indexing
  - Added 10 composite indexes for common production queries
  - Added `idx_execution_logs_conv_id` for conversation history queries
  - Added `idx_execution_logs_user_status` for user-specific error tracking
  - Added `idx_tool_calls_execution` for debugging tool sequences
  - Added `idx_tool_calls_performance` for tool optimization analytics
  - Added `idx_execution_logs_model` for model performance comparison
  - Added `idx_execution_logs_cost` and `idx_execution_logs_duration` for monitoring
  - Created `AnalyticsService` with 9 optimized query methods
  - Added comprehensive query examples using indexes
  - Added performance notes about composite index usage

---

## Executive Summary

Phase 2 implements **SINGLE AGENT** capabilities using **LangChain v1's standardized patterns**:
- `create_agent()` as the standard method (NOT `create_react_agent`)
- **ONE agent only** - No multi-agent, no coordinator, no specialists (Phase 3+)
- **Structured outputs** with Pydantic models for type-safe responses (REQUIRED)
- Built-in middleware for PII redaction, summarization, human-in-the-loop
- MCP tools via `langchain-mcp-adapters`
- LangGraph StateGraph for workflow orchestration (state owner)

**Release Target:** Version 0.2.0
**Milestone:** Complete agent implementation with tools, middleware, and production hardening

**Key Changes:**
1. LangChain v1 replaces legacy `AgentExecutor` and `create_react_agent` with a simpler, more powerful `create_agent()` API
2. **All agent communications use structured outputs** - `result["structured_response"]` returns validated Pydantic models for type safety and debugging (`repr()`)
3. **Agent can have internal working state** - LangGraph owns conversation state, agent uses ephemeral task-scoped working memory

### Critical Transition Challenges

**1. LangChain v1.0 is Alpha/Beta**
- Not yet GA (generally available)
- API may change before stable release
- Requires `pip install --pre` flag
- Strategy: Build on v1.0 but maintain Phase 1 fallback

**2. Simplified Namespace**
LangChain v1.0 consolidates packages:
```
langchain (v1.0) - core + agents + middleware
├── langchain-core (bundled)
├── langchain-anthropic ✅
├── langchain-openai ✅
├── langchain-google-genai ⚠️
├── langchain-aws
├── langchain-ollama
└── langchain-mcp-adapters
```

Legacy features → `langchain-classic`

**3. Content Blocks: Provider Support in v1**
- **Full support:** Anthropic (Claude), OpenAI, Ollama ✅
- **Partial:** Google GenAI ⚠️
- **Limited:** AWS Bedrock (depends on model)

**Our strategy:** Start with Anthropic (our primary), Ollama for local testing.

**4. Dependency Conflicts**
- `langchain` v0.3 (current) vs v1.0 (target) cannot coexist
- Solution: Feature flag + parallel implementation
- Keep Phase 1 working while Phase 2 develops

### Implementation Strategy

```
Phase 2.0: Preparation (CURRENT)
├─ Document v1.0 architecture
├─ Test v1.0 in isolated environment
└─ Identify compatibility issues

Phase 2.1: Parallel Implementation
├─ Add v1.0 agent behind feature flag
├─ Both Phase 1 (stable) and Phase 2 (experimental) run
├─ Use ENABLE_LANGCHAIN_V1=true/false to switch
└─ Phase 1 remains default

Phase 2.2: Gradual Migration
├─ Test v1.0 agent in workbench mode
├─ Enable for SEO coach mode after validation
├─ Collect metrics: performance, stability, errors
└─ Fix issues as v1.0 stabilizes

Phase 2.3: Full Transition
├─ Make v1.0 agent default (after GA release)
├─ Deprecate Phase 1 StateGraph workflow
└─ Remove legacy code after validation period
```

### Risk Mitigation

**If v1.0 causes issues:**
1. Fall back to Phase 1 (feature flag)
2. Continue using stable LangGraph patterns
3. Wait for v1.0 GA release
4. Revisit when ecosystem stabilizes

**Monitoring:**
- Track v1.0 alpha/beta releases
- Test each release for breaking changes
- Monitor LangChain GitHub for API stability
- Watch content blocks provider support expansion

---

## What LangChain v1 Provides

### 1. Standardized Agent Creation

```python
from langchain.agents import create_agent

# LangChain v1 CAN accept a checkpointer...
agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",
    tools=[tool1, tool2, tool3],
    middleware=[...],  # Optional middleware
    checkpointer=checkpointer,  # Built-in persistence
)

# Native streaming and async support
result = await agent.ainvoke({"messages": [user_message]})
```

**What this gives us:**
- Simpler API than `create_react_agent`
- Native persistence support (checkpointer parameter available)
- Built-in streaming
- Human-in-the-loop by default
- Time-travel debugging
- Middleware composition

**⚠️ IMPORTANT FOR AGENT WORKBENCH:**
In our implementation, we do NOT give the agent a checkpointer. Instead:
- LangGraph StateGraph owns the checkpointer (single source of truth)
- Agent is stateless and executes within LangGraph node
- See "Key Patterns" section 3 below for the correct pattern

### 2. Middleware System (Phase 2: Get It Right)

**Phase 2 includes BOTH built-in AND custom middleware:**

```python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIRedactionMiddleware,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware
)

agent = create_agent(
    model=get_model(),
    tools=tools,
    middleware=[
        # Built-in LangChain v1 middleware
        PIIRedactionMiddleware(
            patterns=["email", "phone", "ssn", "credit_card"]
        ),
        SummarizationMiddleware(
            model=get_model(),
            max_tokens_before_summary=8000
        ),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "send_email": ["approve", "edit", "reject"],
                "delete_file": ["approve", "reject"],
            }
        ),

        # Custom middleware
        ContextMiddleware(db),   # Load conversation history from DB
        MemoryMiddleware(db),    # Save agent responses to DB
    ]
)
```

**Goal: Implement LangChain v1 middleware patterns correctly.**
No multi-agent. Single agent with proper middleware.

### 3. Custom Middleware Pattern

**Five hook points for custom behavior:**

```python
from langchain.agents.middleware import BaseMiddleware

class CustomContextMiddleware(BaseMiddleware):
    """Load relevant context before agent runs."""

    async def before_agent(self, state):
        """Called before agent starts - load memory, validate input."""
        context = await self.context_service.retrieve(state["conversation_id"])
        state["context"] = context
        return state

    async def before_model(self, state):
        """Called before model invocation - update prompts."""
        # Inject context into prompt
        return state

    async def wrap_model_call(self, state, model_func):
        """Wrap model calls - intercept/modify requests."""
        # Add caching, logging, etc.
        result = await model_func(state)
        return result

    async def after_model(self, state):
        """Called after model responds - apply guardrails."""
        # Check for policy violations
        return state

    async def after_agent(self, state):
        """Called after agent completes - save results, cleanup."""
        await self.memory_service.store(state)
        return state
```

### 4. Content Blocks (Provider-Agnostic)

**Unified access to LLM features:**
- Reasoning traces
- Citations/sources
- Tool calls
- Streaming chunks
- Type-safe with full hints

### 5. Structured Outputs (REQUIRED for All Communications)

**Critical Requirement:** All agent communications MUST support structured outputs using Pydantic models. This ensures type-safe, validated responses throughout the system.

**Implementation Pattern:**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from langchain.agents import create_agent

# Define response schema
class AgentResponse(BaseModel):
    """Structured response from agent."""
    status: Literal["success", "error", "pending"]
    message: str = Field(description="Human-readable response message")
    reasoning: Optional[str] = Field(None, description="Chain-of-thought reasoning")
    tool_calls: List[str] = Field(default_factory=list, description="Tools used")
    data: Optional[dict] = Field(None, description="Structured data payload")
    metadata: Optional[dict] = Field(None, description="Additional metadata")

# Create agent with structured output
agent = create_agent(
    model=get_model(),  # OpenRouter
    tools=mcp_tools,
    middleware=[...],
    structured_output=AgentResponse,  # Enforce structured output
)

# Execute and get structured response
result = await agent.ainvoke({"messages": [user_message]})

# Access structured response - guaranteed type-safe
print(repr(result["structured_response"]))
# AgentResponse(status='success', message='Task completed', ...)
```

**Benefits:**
- **Type Safety**: Pydantic validation ensures correct data types
- **Consistency**: All responses follow same schema
- **Debugging**: `repr()` shows full structured object
- **API Compatibility**: Easy serialization to JSON
- **Middleware Integration**: Structured data flows through middleware

**Integration with WorkflowState:**

```python
class WorkflowState(TypedDict):
    """LangGraph state with structured response."""
    # ... existing fields ...
    agent_response: Optional[str]  # Human-readable message
    structured_response: Optional[AgentResponse]  # Full structured data

async def execute_agent_node(state: WorkflowState) -> dict:
    """Execute agent and capture structured response."""
    result = await agent.ainvoke({"messages": state["conversation_history"]})

    # Extract structured response
    structured = result["structured_response"]

    return {
        "agent_response": structured.message,  # For display
        "structured_response": structured,  # For processing
        "workflow_steps": state["workflow_steps"] + ["execute_agent"],
        "execution_successful": structured.status == "success"
    }
```

**Response Schema Variants:**

```python
# SEO Coach Mode
class SEOCoachResponse(BaseModel):
    status: Literal["analysis", "recommendations", "complete"]
    message: str
    seo_score: Optional[int] = Field(None, ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)

# Workbench Mode
class WorkbenchResponse(BaseModel):
    status: Literal["success", "error", "tool_required"]
    message: str
    debug_info: Optional[dict] = None
    tool_results: Optional[List[dict]] = None

# File Processing Response
class FileProcessingResponse(BaseModel):
    status: Literal["processed", "error", "partial"]
    message: str
    files_processed: List[str] = Field(default_factory=list)
    extracted_text: Optional[str] = None
    metadata: Optional[dict] = None
```

**Error Handling with Structured Outputs:**

```python
try:
    result = await agent.ainvoke({"messages": [user_message]})
    structured = result["structured_response"]

    if structured.status == "error":
        logger.error(f"Agent error: {structured.message}")
        # Structured error - safe to display
        return structured

except ValidationError as e:
    # Pydantic validation failed - response doesn't match schema
    logger.error(f"Invalid response structure: {e}")
    return AgentResponse(
        status="error",
        message="Internal error: Invalid response format"
    )
```

**Testing Structured Outputs:**

```python
# tests/test_structured_outputs.py

async def test_agent_returns_structured_output():
    """Agent must return structured response."""
    agent = create_agent(
        model=get_model(),
        tools=[],
        structured_output=AgentResponse
    )

    result = await agent.ainvoke({"messages": ["Hello"]})

    # Verify structured response exists
    assert "structured_response" in result

    # Verify it's correct type
    assert isinstance(result["structured_response"], AgentResponse)

    # Verify required fields
    assert result["structured_response"].status in ["success", "error", "pending"]
    assert result["structured_response"].message

    # repr() should work for debugging
    repr_str = repr(result["structured_response"])
    assert "AgentResponse" in repr_str
```

**Why This Matters:**

1. **Type Safety**: Eliminates string parsing errors
2. **Validation**: Pydantic catches malformed responses early
3. **Debugging**: `repr()` provides clear object inspection
4. **Consistency**: Same structure across all modes (workbench, seo_coach)
5. **API Contracts**: Clear response schemas for frontend/backend
6. **Middleware Compatibility**: Structured data flows cleanly through hooks

---

## Phase 2 Architecture: Keep It Simple

### Core Pattern: Single Agent with Middleware

**ONE agent. No multi-agent. No swarm. Get the basics right first.**

Phase 2 is about:
1. Replacing current LLM calls with LangChain v1's `create_agent()`
2. Adding MCP tools via `langchain-mcp-adapters`
3. Using middleware for PII redaction, summarization, context
4. That's it.

Multi-agent complexity is Phase 3+. Not now.

```python
# services/agent_service.py

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

class AgentService:
    """Manages the primary agent with MCP tools and middleware."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.mcp_client = None
        self.tools = []
        self.agent = None

    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        """Initialize MCP servers and create STATELESS agent."""

        # 1. Connect to MCP servers
        self.mcp_client = MultiServerMCPClient(mcp_server_configs)
        self.tools = await self.mcp_client.get_tools()

        # 2. Create STATELESS agent with full middleware stack
        # NOTE: Agent does NOT have a checkpointer - it's stateless
        # State is managed by LangGraph StateGraph (see WorkflowOrchestrator)
        self.agent = create_agent(
            model=get_model(),  # OpenRouter
            tools=self.tools,
            middleware=[
                # Built-in LangChain v1 middleware
                PIIRedactionMiddleware(patterns=["email", "phone"]),
                SummarizationMiddleware(
                    model=get_model(),
                    max_tokens_before_summary=8000
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "send_email": ["approve", "edit", "reject"],
                        "delete_file": ["approve", "reject"],
                    }
                ),

                # Custom middleware
                ContextMiddleware(db=self.db),   # Load conversation history
                MemoryMiddleware(db=self.db),    # Save responses
            ],
            structured_output=AgentResponse,  # Type-safe responses
            # NO checkpointer - agent is stateless
        )

    async def execute(
        self,
        conversation_history: List[StandardMessage],
        user_message: str
    ) -> AgentResponse:
        """
        Execute STATELESS agent with conversation context.

        NOTE: This method is called FROM a LangGraph node.
        The node extracts conversation_history from LangGraph state.
        """
        # Convert history to agent message format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ] + [{"role": "user", "content": user_message}]

        # Execute stateless agent
        result = await self.agent.ainvoke({"messages": messages})

        # Return structured response
        return result["structured_response"]

    async def stream(
        self,
        conversation_history: List[StandardMessage],
        user_message: str
    ):
        """
        Stream STATELESS agent responses.

        NOTE: This method is called FROM a LangGraph node for streaming.
        The node extracts conversation_history from LangGraph state.
        """
        # Convert history to agent message format
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in conversation_history
        ] + [{"role": "user", "content": user_message}]

        # Stream stateless agent execution
        async for chunk in self.agent.astream({"messages": messages}):
            yield chunk
```

---

## Implementation Components

### 1. MCP Tool Integration

**Use `langchain-mcp-adapters` exactly as documented:**

```python
# services/mcp_service.py

from langchain_mcp_adapters.client import MultiServerMCPClient

class MCPService:
    """Manages MCP server connections."""

    def __init__(self):
        self.client = None

    async def initialize(self, configs: Dict[str, Dict]):
        """
        Initialize MCP servers.

        Config format:
        {
            "filesystem": {
                "command": "python",
                "args": ["mcp_servers/filesystem.py"],
                "transport": "stdio"
            },
            "web": {
                "url": "http://localhost:8001/mcp",
                "transport": "streamable_http",
                "headers": {"Authorization": "Bearer TOKEN"}
            }
        }
        """
        self.client = MultiServerMCPClient(configs)

    async def get_tools(self, server_name: Optional[str] = None):
        """Get tools from all servers or specific server."""
        if server_name:
            async with self.client.session(server_name) as session:
                return await load_mcp_tools(session)
        return await self.client.get_tools()

    async def reload_tools(self):
        """Reload tools from all servers."""
        return await self.get_tools()
```

### 2. Custom Middleware

**Context Injection:**

```python
# middleware/context_middleware.py

from langchain.agents.middleware import BaseMiddleware

class ContextMiddleware(BaseMiddleware):
    """Inject relevant context before agent runs."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def before_agent(self, state):
        """Load context before agent starts."""

        # Get conversation history
        messages = self.db.get_messages(state["conversation_id"])

        # Get business profile if SEO mode
        if state.get("mode") == "seo_coach":
            profile = self.db.get_business_profile(state["conversation_id"])
            state["business_profile"] = profile

        # Add to state
        state["conversation_history"] = messages

        return state
```

**Memory/Learning:**

```python
# middleware/memory_middleware.py

class MemoryMiddleware(BaseMiddleware):
    """Store agent interactions for learning."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def after_agent(self, state):
        """Save interaction after agent completes."""

        # Store tool usage
        if "tool_calls" in state:
            for tool_call in state["tool_calls"]:
                await self._store_tool_usage(
                    conversation_id=state["conversation_id"],
                    tool_name=tool_call["name"],
                    success=tool_call.get("success", True)
                )

        # Store response
        await self.db.save_message({
            "conversation_id": state["conversation_id"],
            "role": "assistant",
            "content": state["messages"][-1]["content"]
        })

        return state
```

**Guardrails Middleware (Optional):**

```python
# middleware/guardrails_middleware.py

class GuardrailsMiddleware(BaseMiddleware):
    """Apply guardrails after model responds."""

    async def after_model(self, state):
        """Check response before tool execution."""

        response = state["messages"][-1]

        # Check for policy violations
        if self._contains_prohibited_content(response["content"]):
            raise ValueError("Response violates content policy")

        # Validate tool calls
        if "tool_calls" in response:
            for tool_call in response["tool_calls"]:
                if not self._is_tool_allowed(tool_call["name"]):
                    raise ValueError(f"Tool {tool_call['name']} not allowed")

        return state
```

**Phase 2 Middleware Stack:**
1. Built-in: PIIRedactionMiddleware
2. Built-in: SummarizationMiddleware
3. Built-in: HumanInTheLoopMiddleware
4. Custom: ContextMiddleware
5. Custom: MemoryMiddleware
6. Custom: GuardrailsMiddleware (optional)

Get the middleware implementation RIGHT in Phase 2.

### 3. State Management (Simplified)

**Let LangChain handle most state:**

```python
# models/agent_state.py

from typing import TypedDict, List, Dict, Any, Optional
from uuid import UUID

class AgentState(TypedDict):
    """
    Minimal state - LangChain manages most of this via checkpointer.

    Only add what LangChain doesn't handle automatically.
    """

    # LangChain manages automatically:
    # - messages: conversation history
    # - tool_calls: tool invocations
    # - tool_results: tool outputs

    # We add:
    conversation_id: UUID              # Our conversation tracking
    mode: str                          # "workbench" or "seo_coach"
    business_profile: Optional[Dict]   # SEO mode only
    context: Optional[List[Dict]]      # Retrieved context
```

### 4. Integration with Existing Architecture

**Update `ConsolidatedWorkbenchService`:**

```python
# services/consolidated_service.py

class ConsolidatedWorkbenchService:
    """Main workflow service - now uses LangChain agent."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent_service = AgentService(db)
        self.mcp_service = MCPService()

    async def initialize(self):
        """Initialize services."""

        # Load MCP server configs from env/DB
        mcp_configs = await self._load_mcp_configs()
        await self.mcp_service.initialize(mcp_configs)

        # Initialize agent with loaded tools
        tools = await self.mcp_service.get_tools()
        await self.agent_service.initialize_with_tools(tools)

    async def process_message(
        self,
        conversation_id: UUID,
        user_message: str,
        mode: str = "workbench"
    ) -> str:
        """Process user message through agent."""

        # Simple - let agent handle everything
        result = await self.agent_service.run(
            conversation_id=conversation_id,
            user_message=user_message,
            mode=mode
        )

        return result

    async def stream_message(
        self,
        conversation_id: UUID,
        user_message: str,
        mode: str = "workbench"
    ):
        """Stream agent responses."""

        async for chunk in self.agent_service.stream(
            conversation_id=conversation_id,
            user_message=user_message,
            mode=mode
        ):
            yield chunk
```

---

## Database Changes

### Extend Existing Models

```python
# models/database.py

# Add to AgentConfigModel
class AgentConfigModel(Base):
    __tablename__ = "agent_configs"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]

    # MCP server assignments
    mcp_servers: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    # Example: ["filesystem", "web", "database"]

    # Tool preferences
    enabled_tools: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    # Example: ["read_file", "web_search", "send_email"]

    # Middleware config
    middleware_config: Mapped[Optional[JSON]] = mapped_column(JSON, nullable=True)
    # Example: {
    #   "pii_redaction": {"patterns": ["email", "phone"]},
    #   "summarization": {"max_tokens": 8000}
    # }

# Add new table for tool usage tracking
class ToolUsageModel(Base):
    __tablename__ = "tool_usage"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"))
    tool_name: Mapped[str]
    success: Mapped[bool]
    execution_time_ms: Mapped[Optional[int]]
    error_message: Mapped[Optional[str]]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

---

## Phase 2.0: User Authentication & Settings (FIRST STEP)

**⚠️ PREREQUISITE: Must be completed before any other Phase 2 work ⚠️**

### Why First?

User authentication enables:
1. **Per-user conversation storage** - Isolate conversations by user
2. **User-specific settings** - Active (user-configured) and passive (system-learned)
3. **Usage tracking** - Monitor agent usage per user
4. **Personalization** - Adapt agent behavior per user
5. **Security** - Control access to sensitive operations

### HuggingFace Spaces Authentication

**Current State:** Public access without user tracking
**Phase 2.0:** Mandatory HF account login for both modes (workbench + SEO coach)

### Database Schema Extensions

```python
# models/database.py

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class UserModel(Base):
    """
    User account from HuggingFace authentication.

    Links to all user-specific data.
    """
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # HuggingFace OAuth data
    hf_username: Mapped[str] = mapped_column(unique=True, index=True)
    hf_user_id: Mapped[str] = mapped_column(unique=True)  # HF OAuth ID
    hf_email: Mapped[Optional[str]]
    hf_avatar_url: Mapped[Optional[str]]

    # Account metadata
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_login: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(default=True)

    # Relationships
    conversations: Mapped[list["ConversationModel"]] = relationship(back_populates="user")
    settings: Mapped[list["UserSettingModel"]] = relationship(back_populates="user")


class UserSettingModel(Base):
    """
    User settings - both active (user-configured) and passive (system-learned).

    Key-value store for flexible settings without schema changes.
    """
    __tablename__ = "user_settings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Setting identification
    setting_key: Mapped[str] = mapped_column(index=True)  # e.g., "preferred_model", "ui_theme"
    setting_value: Mapped[JSON]  # Flexible JSON value
    setting_type: Mapped[str]  # "active" or "passive"

    # Metadata
    category: Mapped[Optional[str]]  # e.g., "ui", "agent", "workflow"
    description: Mapped[Optional[str]]
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="settings")


class ConversationModel(Base):
    """
    Updated: Link conversations to users.
    """
    __tablename__ = "conversations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # NEW: User link
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Existing fields...
    title: Mapped[Optional[str]]
    mode: Mapped[str]  # "workbench" or "seo_coach"
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="conversations")
    messages: Mapped[list["MessageModel"]] = relationship(back_populates="conversation")


class UserSessionModel(Base):
    """
    Track user sessions for analytics and security.

    Automatically logs when users access the application.
    """
    __tablename__ = "user_sessions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Session tracking
    session_start: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    session_end: Mapped[Optional[datetime]]
    last_activity: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    # Request metadata (from gradio.Request)
    ip_address: Mapped[Optional[str]]  # request.client.host
    user_agent: Mapped[Optional[str]]  # request.headers.get("user-agent")
    referrer: Mapped[Optional[str]]    # request.headers.get("referer")

    # Activity tracking
    total_messages: Mapped[int] = mapped_column(default=0)
    total_tool_calls: Mapped[int] = mapped_column(default=0)

    # Relationships
    user: Mapped["UserModel"] = relationship(back_populates="sessions")
    activities: Mapped[list["SessionActivityModel"]] = relationship(back_populates="session")


class SessionActivityModel(Base):
    """
    Detailed activity log within a session.

    Tracks every significant action for analytics.
    """
    __tablename__ = "session_activities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(ForeignKey("user_sessions.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Activity details
    timestamp: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    action: Mapped[str]  # "message_sent", "tool_called", "file_uploaded", etc.
    metadata: Mapped[Optional[JSON]]  # Flexible JSON for action-specific data

    # Relationships
    session: Mapped["UserSessionModel"] = relationship(back_populates="activities")
    user: Mapped["UserModel"] = relationship()


class UsageMetricsModel(Base):
    """
    Track usage per user for analytics and rate limiting.

    Aggregated daily metrics for reporting.
    """
    __tablename__ = "usage_metrics"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)

    # Metrics
    total_messages: Mapped[int] = mapped_column(default=0)
    total_tokens: Mapped[int] = mapped_column(default=0)
    total_tool_calls: Mapped[int] = mapped_column(default=0)
    total_files_processed: Mapped[int] = mapped_column(default=0)

    # Time-based tracking
    date: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)

    # Cost tracking (optional)
    estimated_cost_usd: Mapped[Optional[float]]


# Update UserModel relationships
class UserModel(Base):
    # ... existing fields ...

    # Relationships
    conversations: Mapped[list["ConversationModel"]] = relationship(back_populates="user")
    settings: Mapped[list["UserSettingModel"]] = relationship(back_populates="user")
    sessions: Mapped[list["UserSessionModel"]] = relationship(back_populates="user")  # NEW
```

### HuggingFace OAuth Integration with Session Logging

```python
# services/auth_service.py

from huggingface_hub import OAuth
from gradio import Request
import os
from typing import Optional
from datetime import datetime
from uuid import UUID

class AuthService:
    """
    Handle HuggingFace OAuth authentication and session management.

    Integrates with Gradio's built-in HF OAuth via Request object.
    Automatically logs user sessions to database.

    SESSION MANAGEMENT PATTERN:
    - Sessions are reused within 30-minute timeout window
    - Prevents database pollution from page refreshes
    - Only creates new session if no active session exists
    - Updates last_activity on session reuse
    - Critical methods:
      * get_active_session() - Check for existing session
      * update_session_activity() - Refresh session timestamp
      * create_session() - Create new session (only when needed)
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.oauth = OAuth(
            client_id=os.getenv("HF_OAUTH_CLIENT_ID"),
            client_secret=os.getenv("HF_OAUTH_CLIENT_SECRET"),
            scopes=["profile", "email"]
        )

    async def get_or_create_user_from_request(self, request: Request) -> UserModel:
        """
        Get or create user from Gradio request object.

        PATTERN: Use request.username for authenticated user in HF Spaces.

        Args:
            request: Gradio Request object (automatically injected)

        Returns:
            UserModel instance
        """

        username = request.username

        if not username:
            raise ValueError("No authenticated user in request")

        # Check if user exists
        user = self.db.get_user_by_hf_username(username)

        if not user:
            # First login - create user
            # Note: In HF Spaces with auth="huggingface", we only get username
            # Full OAuth data would require additional HF API calls
            user = self.db.create_user(
                hf_username=username,
                hf_user_id=username,  # Use username as ID for simplicity
                hf_email=None,  # Would need separate HF API call
                hf_avatar_url=None  # Would need separate HF API call
            )

            # Initialize default settings
            await self._initialize_default_settings(user.id)
        else:
            # Update last login
            self.db.update_user_last_login(user.id)

        return user

    async def get_active_session(
        self,
        user_id: UUID,
        max_age_minutes: int = 30
    ) -> Optional[UserSessionModel]:
        """
        Get active session for user if one exists within timeout window.

        PATTERN: Prevents session pollution by reusing recent sessions.

        Args:
            user_id: User UUID
            max_age_minutes: Maximum age of session to consider active (default: 30)

        Returns:
            Active UserSessionModel if found, None otherwise
        """
        from datetime import timedelta

        cutoff_time = datetime.utcnow() - timedelta(minutes=max_age_minutes)

        # Query for most recent session within timeout window
        session = self.db.get_active_user_session(
            user_id=user_id,
            since=cutoff_time
        )

        return session

    async def update_session_activity(self, session_id: UUID):
        """
        Update session's last_activity timestamp.

        Called when reusing an existing session on page refresh.

        Args:
            session_id: Session UUID
        """
        self.db.update_session_activity(session_id)

    async def create_session(
        self,
        user_id: UUID,
        request: Request
    ) -> UserSessionModel:
        """
        Create new user session and log to database.

        Automatically extracts metadata from Gradio Request object.

        IMPORTANT: Use get_active_session() first to check for existing sessions.
        Only create new session if no active session exists.

        Args:
            user_id: User UUID
            request: Gradio Request object with client info

        Returns:
            UserSessionModel instance
        """

        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent") if request.headers else None
        referrer = request.headers.get("referer") if request.headers else None

        # Create session
        session = self.db.create_user_session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer
        )

        return session

    async def log_session_activity(
        self,
        session_id: UUID,
        user_id: UUID,
        action: str,
        metadata: Optional[dict] = None
    ):
        """
        Log activity within a session.

        Args:
            session_id: Session UUID
            user_id: User UUID
            action: Action name (e.g., "message_sent", "tool_called")
            metadata: Optional action-specific data
        """

        self.db.create_session_activity(
            session_id=session_id,
            user_id=user_id,
            action=action,
            metadata=metadata
        )

        # Update session last_activity
        self.db.update_session_activity(session_id)

        # Increment session counters
        if action == "message_sent":
            self.db.increment_session_messages(session_id)
        elif action == "tool_called":
            self.db.increment_session_tool_calls(session_id)

    async def end_session(self, session_id: UUID):
        """
        Mark session as ended.

        Note: In practice, sessions may not have explicit end.
        Can be triggered by inactivity timeout or explicit logout.
        """

        self.db.update_user_session(
            session_id=session_id,
            session_end=datetime.utcnow()
        )

    async def handle_login(self, oauth_token: str) -> UserModel:
        """
        Handle user login via HF OAuth.

        Creates user if first login, updates last_login if existing.
        """

        # Get user info from HF
        user_info = await self.oauth.get_user_info(oauth_token)

        # Check if user exists
        user = self.db.get_user_by_hf_id(user_info["id"])

        if not user:
            # First login - create user
            user = self.db.create_user(
                hf_username=user_info["username"],
                hf_user_id=user_info["id"],
                hf_email=user_info.get("email"),
                hf_avatar_url=user_info.get("avatar_url")
            )

            # Initialize default settings
            await self._initialize_default_settings(user.id)
        else:
            # Update last login
            self.db.update_user_last_login(user.id)

        return user

    async def _initialize_default_settings(self, user_id: UUID):
        """Initialize default settings for new user."""

        default_settings = [
            # Active settings (user can change)
            {
                "setting_key": "preferred_model",
                "setting_value": {"provider": "openrouter", "model": "anthropic/claude-sonnet-4-5"},
                "setting_type": "active",
                "category": "agent",
                "description": "User's preferred LLM model"
            },
            {
                "setting_key": "ui_theme",
                "setting_value": {"theme": "light"},
                "setting_type": "active",
                "category": "ui",
                "description": "UI theme preference"
            },
            {
                "setting_key": "default_mode",
                "setting_value": {"mode": "workbench"},
                "setting_type": "active",
                "category": "workflow",
                "description": "Default mode on startup"
            },

            # Passive settings (system learns)
            {
                "setting_key": "most_used_tools",
                "setting_value": {"tools": []},
                "setting_type": "passive",
                "category": "agent",
                "description": "Tools user uses most frequently"
            },
            {
                "setting_key": "conversation_patterns",
                "setting_value": {"patterns": {}},
                "setting_type": "passive",
                "category": "workflow",
                "description": "Learned conversation patterns"
            },
            {
                "setting_key": "file_upload_history",
                "setting_value": {"file_types": {}},
                "setting_type": "passive",
                "category": "documents",
                "description": "File types user typically uploads"
            }
        ]

        for setting in default_settings:
            self.db.create_user_setting(user_id=user_id, **setting)
```

### Gradio UI with HF OAuth

**Authentication Pattern:** Use `gradio.Request` to access authenticated user

```python
# ui/app.py (updated for authentication)

import gradio as gr
from gradio import Request
import os
from typing import Optional
from datetime import datetime

def create_workbench_app() -> gr.Blocks:
    """
    Create workbench interface with mandatory HF authentication.

    Uses gradio.Request pattern for user authentication.
    """

    with gr.Blocks(title="Agent Workbench") as app:
        # User state persists across interactions
        user_state = gr.State(value=None)
        session_id = gr.State(value=None)

        # Welcome message with user info
        with gr.Row():
            gr.Markdown("# Agent Workbench")
            user_info = gr.Markdown("Loading user info...")

        # Chat interface
        chatbot = gr.Chatbot(label="Conversation")
        msg_input = gr.Textbox(label="Message", placeholder="Send a message...")
        send_btn = gr.Button("Send")

        # On load: Initialize user session
        async def on_load(request: Request):
            """
            Initialize user session on app load.

            IMPORTANT: Use Request parameter to access authenticated user.
            Gradio provides authenticated HF user via request.username

            PATTERN: Reuses existing sessions to prevent database pollution.
            Only creates new session if no active session exists (30min timeout).
            """

            # Access authenticated user from request
            username = request.username if request else None

            if not username:
                return "⚠️ Please log in with your HuggingFace account", None, None

            # Get or create user in DB
            auth_service = AuthService(db)
            user = await auth_service.get_or_create_user_from_request(request)

            # Check for active session (within last 30 min)
            active_session = await auth_service.get_active_session(
                user_id=user.id,
                max_age_minutes=30
            )

            if active_session:
                # Reuse existing session and update activity timestamp
                session = active_session
                await auth_service.update_session_activity(session.id)
            else:
                # No active session - create new one
                session = await auth_service.create_session(
                    user_id=user.id,
                    request=request  # Includes IP, user agent, etc.
                )

            # Load user settings
            settings = db.get_user_settings(user.id)

            # Welcome message
            welcome = f"Welcome back, **{user.hf_username}**! 👋\n\n_Last login: {user.last_login.strftime('%Y-%m-%d %H:%M')}_"

            return welcome, user, session.id

        app.load(on_load, outputs=[user_info, user_state, session_id])

        # On message: Extract user from request
        async def handle_message(message: str, history: list, request: Request):
            """
            Handle chat message with user context from request.

            PATTERN: Always use Request parameter to get user context.
            """

            # Extract authenticated user from request
            username = request.username if request else None

            if not username:
                return history + [("Error", "Session expired. Please reload.")], ""

            # Get user from DB
            user = db.get_user_by_hf_username(username)

            if not user:
                return history + [("Error", "User not found. Please reload.")], ""

            # Get session_id from state (set during on_load)
            session = db.get_active_session(user.id)

            # Log message to session
            auth_service = AuthService(db)
            await auth_service.log_session_activity(
                session_id=session.id,
                user_id=user.id,
                action="message_sent",
                metadata={"message_length": len(message)}
            )

            # Process message through workflow
            response = await orchestrator.process_message(
                user_id=user.id,
                user_message=message,
                mode="workbench"
            )

            # Update history
            history.append((message, response))

            return history, ""

        send_btn.click(
            handle_message,
            inputs=[msg_input, chatbot],
            outputs=[chatbot, msg_input]
        )

    return app


# Launch with HF OAuth (only works in HF Spaces)
if __name__ == "__main__":
    app = create_workbench_app()

    app.queue()

    # IMPORTANT: auth parameter enables HF OAuth
    # This makes request.username available in all functions with Request parameter
    app.launch(
        auth="huggingface",  # Requires HF account login
        share=False,
        server_name="0.0.0.0",
        server_port=7860
    )
```

**Key Pattern:**
1. Add `request: Request` parameter to any function that needs user context
2. Access authenticated user via `request.username`
3. Gradio automatically injects the Request object when auth="huggingface" is enabled
4. Request also provides: `request.client.host` (IP), `request.headers` (user agent, etc.)

### Passive Settings Collection

```python
# middleware/settings_learning_middleware.py

from langchain.agents.middleware import BaseMiddleware
from typing import Dict, Any

class SettingsLearningMiddleware(BaseMiddleware):
    """
    Passive settings collection without user awareness.

    Learns user preferences from behavior.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def after_agent(self, state):
        """Collect passive settings after agent execution."""

        user_id = state.get("user_id")
        if not user_id:
            return state

        # 1. Track tool usage
        if "tool_calls" in state:
            tools_used = [tc["name"] for tc in state["tool_calls"]]
            await self._update_tool_frequency(user_id, tools_used)

        # 2. Track conversation patterns
        if "execution_successful" in state and state["execution_successful"]:
            await self._update_conversation_patterns(
                user_id=user_id,
                message_type=state.get("message_type"),
                complexity=state.get("complexity")
            )

        # 3. Track file processing
        if state.get("processed_documents"):
            file_types = [doc["file_type"] for doc in state["processed_documents"]]
            await self._update_file_preferences(user_id, file_types)

        return state

    async def _update_tool_frequency(self, user_id: UUID, tools: list[str]):
        """Update most_used_tools passive setting."""

        setting = self.db.get_user_setting(user_id, "most_used_tools")

        # Update frequency count
        tools_data = setting.setting_value.get("tools", {})
        for tool in tools:
            tools_data[tool] = tools_data.get(tool, 0) + 1

        # Keep top 10 most used
        sorted_tools = sorted(tools_data.items(), key=lambda x: x[1], reverse=True)[:10]

        self.db.update_user_setting(
            user_id=user_id,
            setting_key="most_used_tools",
            setting_value={"tools": dict(sorted_tools)}
        )

    async def _update_conversation_patterns(
        self,
        user_id: UUID,
        message_type: str,
        complexity: str
    ):
        """Learn conversation patterns."""

        setting = self.db.get_user_setting(user_id, "conversation_patterns")
        patterns = setting.setting_value.get("patterns", {})

        # Track complexity distribution
        key = f"{message_type}_{complexity}"
        patterns[key] = patterns.get(key, 0) + 1

        self.db.update_user_setting(
            user_id=user_id,
            setting_key="conversation_patterns",
            setting_value={"patterns": patterns}
        )

    async def _update_file_preferences(self, user_id: UUID, file_types: list[str]):
        """Learn file type preferences."""

        setting = self.db.get_user_setting(user_id, "file_upload_history")
        file_data = setting.setting_value.get("file_types", {})

        for file_type in file_types:
            file_data[file_type] = file_data.get(file_type, 0) + 1

        self.db.update_user_setting(
            user_id=user_id,
            setting_key="file_upload_history",
            setting_value={"file_types": file_data}
        )
```

### LangGraph State Updates with User Context

```python
# services/workflow_service.py (updated)

class WorkflowState(TypedDict):
    """
    State for user-system-agent workflow.

    IMPORTANT: State updates flow through nodes.
    Each node returns a dict that MERGES with existing state.
    """

    # User context (NEW)
    user_id: UUID
    user_settings: Dict[str, Any]

    # Existing fields...
    conversation_id: UUID
    user_message: str
    mode: str

    # ... rest of state


class WorkflowOrchestrator:
    """Updated to include user context."""

    async def _process_input_node(self, state: WorkflowState) -> Dict:
        """
        Node 1: Load user settings and process input.

        State updates: Each return dict MERGES with state.
        """

        steps = state.get("steps", [])
        steps.append("Loading user settings")

        # Load user settings (active + passive)
        user_settings = self.db.get_user_settings_dict(state["user_id"])

        # Get preferred model from settings
        preferred_model = user_settings.get("preferred_model", {})

        # Get most used tools for optimization
        most_used_tools = user_settings.get("most_used_tools", {})

        steps.append("Processing user input with personalized settings")

        # ... rest of processing

        # Return dict MERGES with state
        return {
            "user_settings": user_settings,
            "preferred_model": preferred_model,
            "steps": steps,
            # ... other updates
        }
```

### Database Backend Updates

```python
# database/backends/sqlite.py (add user methods)

class SQLiteBackend(DatabaseBackend):
    """Extended with user management."""

    def get_user_by_hf_id(self, hf_user_id: str) -> Optional[UserModel]:
        """Get user by HuggingFace ID."""
        with self.session() as session:
            return session.query(UserModel).filter_by(hf_user_id=hf_user_id).first()

    def create_user(self, **kwargs) -> UserModel:
        """Create new user."""
        with self.session() as session:
            user = UserModel(**kwargs)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_user_settings(self, user_id: UUID) -> list[UserSettingModel]:
        """Get all settings for user."""
        with self.session() as session:
            return session.query(UserSettingModel).filter_by(user_id=user_id).all()

    def get_user_setting(self, user_id: UUID, setting_key: str) -> Optional[UserSettingModel]:
        """Get specific setting."""
        with self.session() as session:
            return session.query(UserSettingModel).filter_by(
                user_id=user_id,
                setting_key=setting_key
            ).first()

    def create_user_setting(self, user_id: UUID, **kwargs) -> UserSettingModel:
        """Create user setting."""
        with self.session() as session:
            setting = UserSettingModel(user_id=user_id, **kwargs)
            session.add(setting)
            session.commit()
            session.refresh(setting)
            return setting

    def update_user_setting(
        self,
        user_id: UUID,
        setting_key: str,
        setting_value: Dict[str, Any]
    ):
        """Update existing setting."""
        with self.session() as session:
            setting = session.query(UserSettingModel).filter_by(
                user_id=user_id,
                setting_key=setting_key
            ).first()

            if setting:
                setting.setting_value = setting_value
                setting.updated_at = datetime.utcnow()
                session.commit()

    def create_user_session(
        self,
        user_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None
    ) -> UserSessionModel:
        """Create new user session."""
        with self.session() as session:
            user_session = UserSessionModel(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer
            )
            session.add(user_session)
            session.commit()
            session.refresh(user_session)
            return user_session

    def get_active_user_session(
        self,
        user_id: UUID,
        since: datetime
    ) -> Optional[UserSessionModel]:
        """
        Get most recent active session for user within time window.

        Args:
            user_id: User UUID
            since: Cutoff datetime (e.g., now - 30 minutes)

        Returns:
            Most recent UserSessionModel if found, None otherwise
        """
        with self.session() as session:
            return (
                session.query(UserSessionModel)
                .filter(
                    UserSessionModel.user_id == user_id,
                    UserSessionModel.last_activity >= since,
                    UserSessionModel.session_end.is_(None)  # Exclude explicitly ended sessions
                )
                .order_by(UserSessionModel.last_activity.desc())
                .first()
            )

    def update_session_activity(self, session_id: UUID):
        """Update session's last_activity timestamp."""
        with self.session() as session:
            user_session = session.query(UserSessionModel).filter_by(id=session_id).first()
            if user_session:
                user_session.last_activity = datetime.utcnow()
                session.commit()

    def update_user_session(self, session_id: UUID, **kwargs):
        """Update user session fields (e.g., session_end)."""
        with self.session() as session:
            user_session = session.query(UserSessionModel).filter_by(id=session_id).first()
            if user_session:
                for key, value in kwargs.items():
                    setattr(user_session, key, value)
                session.commit()

    def increment_session_messages(self, session_id: UUID):
        """Increment message counter for session."""
        with self.session() as session:
            user_session = session.query(UserSessionModel).filter_by(id=session_id).first()
            if user_session:
                user_session.total_messages += 1
                session.commit()

    def increment_session_tool_calls(self, session_id: UUID):
        """Increment tool call counter for session."""
        with self.session() as session:
            user_session = session.query(UserSessionModel).filter_by(id=session_id).first()
            if user_session:
                user_session.total_tool_calls += 1
                session.commit()

    def create_session_activity(
        self,
        session_id: UUID,
        user_id: UUID,
        action: str,
        metadata: Optional[dict] = None
    ):
        """Log session activity."""
        with self.session() as session:
            activity = SessionActivityModel(
                session_id=session_id,
                user_id=user_id,
                action=action,
                metadata=metadata
            )
            session.add(activity)
            session.commit()

    def get_user_by_hf_username(self, hf_username: str) -> Optional[UserModel]:
        """Get user by HuggingFace username."""
        with self.session() as session:
            return session.query(UserModel).filter_by(hf_username=hf_username).first()

    def update_user_last_login(self, user_id: UUID):
        """Update user's last_login timestamp."""
        with self.session() as session:
            user = session.query(UserModel).filter_by(id=user_id).first()
            if user:
                user.last_login = datetime.utcnow()
                session.commit()


# database/backends/hub.py (add user methods)

class HubBackend(DatabaseBackend):
    """Extended with user management for HF Spaces."""

    def __init__(self, mode: str = "workbench"):
        super().__init__()

        # Users dataset
        self.users_dataset = load_dataset(
            f"{HF_USERNAME}/{mode}_users",
            split="train",
            use_auth_token=True
        )

        # Settings dataset
        self.settings_dataset = load_dataset(
            f"{HF_USERNAME}/{mode}_settings",
            split="train",
            use_auth_token=True
        )

    # Implement same methods as SQLiteBackend...
```

### Environment Configuration

```bash
# .env (add OAuth credentials)

# HuggingFace OAuth (for HF Spaces only)
HF_OAUTH_CLIENT_ID=your_client_id
HF_OAUTH_CLIENT_SECRET=your_client_secret

# Space configuration
SPACE_ID=username/agent-workbench  # Auto-detected in HF Spaces
HF_TOKEN=hf_xxxxx  # For dataset access
```

### Migration Script

```python
# migrations/add_user_auth.py

"""
Add user authentication and settings tables.

Run before Phase 2 deployment.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('hf_username', sa.String(), unique=True, nullable=False),
        sa.Column('hf_user_id', sa.String(), unique=True, nullable=False),
        sa.Column('hf_email', sa.String()),
        sa.Column('hf_avatar_url', sa.String()),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow),
        sa.Column('last_login', sa.DateTime(), default=datetime.utcnow),
        sa.Column('is_active', sa.Boolean(), default=True),
    )

    # Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('user_id', UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('setting_key', sa.String(), nullable=False),
        sa.Column('setting_value', sa.JSON(), nullable=False),
        sa.Column('setting_type', sa.String(), nullable=False),
        sa.Column('category', sa.String()),
        sa.Column('description', sa.String()),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow),
    )

    # Create usage_metrics table
    op.create_table(
        'usage_metrics',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('user_id', UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('total_messages', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('total_tool_calls', sa.Integer(), default=0),
        sa.Column('total_files_processed', sa.Integer(), default=0),
        sa.Column('date', sa.DateTime(), default=datetime.utcnow),
        sa.Column('estimated_cost_usd', sa.Float()),
    )

    # Add user_id to conversations table
    op.add_column('conversations', sa.Column('user_id', UUID(), sa.ForeignKey('users.id')))
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])

    # Create indexes
    op.create_index('ix_users_hf_username', 'users', ['hf_username'])
    op.create_index('ix_user_settings_user_id', 'user_settings', ['user_id'])
    op.create_index('ix_user_settings_key', 'user_settings', ['setting_key'])
    op.create_index('ix_usage_metrics_user_id', 'usage_metrics', ['user_id'])
    op.create_index('ix_usage_metrics_date', 'usage_metrics', ['date'])


def downgrade():
    op.drop_table('usage_metrics')
    op.drop_table('user_settings')
    op.drop_table('users')
    op.drop_column('conversations', 'user_id')
```

### Testing

```python
# tests/test_auth_service.py

async def test_user_creation_on_first_login():
    """Test user is created on first HF login."""

    auth_service = AuthService(db)

    # Simulate HF OAuth response
    oauth_token = "mock_token"

    user = await auth_service.handle_login(oauth_token)

    assert user.hf_username == "test_user"
    assert user.hf_user_id == "hf_123"

    # Check default settings created
    settings = db.get_user_settings(user.id)
    assert len(settings) > 0
    assert any(s.setting_key == "preferred_model" for s in settings)


async def test_passive_settings_learning():
    """Test passive settings are learned from usage."""

    middleware = SettingsLearningMiddleware(db)

    state = {
        "user_id": user_id,
        "tool_calls": [
            {"name": "web_search"},
            {"name": "web_search"},
            {"name": "read_file"}
        ]
    }

    await middleware.after_agent(state)

    # Check tool frequency updated
    setting = db.get_user_setting(user_id, "most_used_tools")
    tools = setting.setting_value["tools"]

    assert tools["web_search"] == 2
    assert tools["read_file"] == 1
```

### Deployment Checklist

**Phase 2.0 Completion Criteria:**
- [ ] Database tables created (users, user_settings, usage_metrics)
- [ ] Migration script tested
- [ ] HF OAuth configured in Spaces
- [ ] AuthService implemented and tested
- [ ] Gradio UI requires HF login
- [ ] User settings load on app start
- [ ] Passive settings collection active
- [ ] Both workbench and SEO coach modes require auth
- [ ] User data isolated per account
- [ ] Settings persist across sessions

---

## Implementation Phases

**Release Target:** v0.2.0 (completion of all 9 phases)

**Phase Order (MVP-First Strategy):**
1. **Phase 2.0**: User Authentication (PREREQUISITE - completed first) ✅
2. **Phase 2.1**: PWA App with User Settings (UI MVP - visible results) ⭐
3. **Phase 2.2**: Enhanced Gradio UI with File Support (stubbed document processing)
4. **Phase 2.3**: Basic Agent Service + **Debug Logging** (minimal agent, comprehensive logging) 🔍
5. **Phase 2.4**: ContentRetriever Tool (LangChain tool for local files)
6. **Phase 2.5**: Built-in Middleware
7. **Phase 2.6**: Custom Middleware
8. **Phase 2.7**: Firecrawl MCP Tool (web scraping)
9. **Phase 2.8**: Production Hardening

**Strategy:**
- **UI First** (2.1-2.2): Get visible MVP quickly, stub backend calls
- **Agent Core + Debug Logging** (2.3): Create minimal agent WITHOUT tools BUT WITH comprehensive debug logging from day 1 🔍
- **Tool Priority** (2.4): ContentRetriever first (local files, LangChain tool)
- **Middleware** (2.5-2.6): Add safety and context layers
- **Web Scraping** (2.7): Firecrawl MCP tool (later stage)
- **Polish** (2.8): Production hardening

**⚠️ CRITICAL: Debug Logging in Phase 2.3**
- Originally planned for Phase 2.8, moved to Phase 2.3
- We'll hit obstacles during development - need logs from the start
- Database captures: execution details, stack traces, tool calls, performance metrics
- Can troubleshoot issues immediately instead of waiting until Phase 2.8

**Release:** When Phase 2.8 is complete → Release v0.2.0 (see Release Checklist below)

---

### Phase 2.0 Summary: Authentication & Session Logging Pattern

**✅ COMPLETED PATTERN DEFINITION**

**Key Components Implemented:**

1. **Database Models**
   - `UserModel`: HF OAuth user account
   - `UserSettingModel`: Active + passive settings (key-value store)
   - `UserSessionModel`: Session tracking with request metadata
   - `SessionActivityModel`: Detailed activity log per session
   - `UsageMetricsModel`: Daily aggregated metrics

2. **Gradio Request Pattern (CRITICAL)**
   ```python
   # Add Request parameter to access authenticated user
   async def handle_message(message: str, request: Request):
       username = request.username  # HF authenticated user
       ip = request.client.host     # IP address
       user_agent = request.headers.get("user-agent")  # Browser info
   ```

3. **AuthService Operations**
   - `get_or_create_user_from_request()`: Extract user from Request object
   - `create_session()`: Create session with request metadata
   - `log_session_activity()`: Log actions (message_sent, tool_called, etc.)
   - `end_session()`: Mark session as ended (optional)

4. **Automatic Session Logging Flow**
   ```
   User loads app (app.load event)
     → Extract user from request.username
     → Get or create user in DB
     → Create new session with IP, user agent, referrer
     → Return session_id in state

   User sends message
     → Extract user from request.username
     → Log activity to session (message_sent)
     → Increment session counters
     → Update last_activity timestamp
   ```

5. **Request Metadata Captured**
   - IP address: `request.client.host`
   - User agent: `request.headers.get("user-agent")`
   - Referrer: `request.headers.get("referer")`
   - Timestamp: `datetime.utcnow()`

**Implementation Notes:**
- All Gradio handlers that need user context MUST include `request: Request` parameter
- `auth="huggingface"` in `app.launch()` makes `request.username` available
- Session logging is automatic and transparent to user
- Works in HuggingFace Spaces with zero external auth setup

---

### Phase 2.1: PWA App with User Settings (SECOND MILESTONE)

**Goal:** Transform HF Spaces into Progressive Web App with dedicated user settings page

**Design Standard:** Ollama app interface pattern
- Clean, minimal centered chat interface
- Model selector in bottom-right of chat input
- Separate settings page (not in main chat UI)
- Native app-like experience

**Tasks:**

#### 2.1a: PWA Configuration
1. Create `manifest.json` for PWA metadata
2. Add service worker for offline capability
3. Configure app icons and splash screens
4. Add PWA meta tags to Gradio interface
5. Test "Add to Home Screen" on mobile/desktop

#### 2.1b: User Settings Page (Separate from Chat)
1. Create dedicated settings interface using Gradio Tabs
2. Move provider/model selection from chat UI to settings
3. Create tabbed settings layout:
   - **Account** tab: HF profile, preferences
   - **Models** tab: Provider selection, model configuration
   - **Company** tab (SEO Coach only): Business profile, brand settings
   - **Advanced** tab: Debug mode, API keys, experimental features

#### 2.1c: Minimal Chat Interface (Ollama Pattern)
1. Simplify main chat interface to Ollama-style design:
   - Center-aligned chat with logo/icon
   - Single message input at bottom
   - Model selector dropdown (bottom-right, minimal)
   - Settings icon/button (links to settings page)
   - Remove all configuration controls from chat view

#### 2.1d: Settings Persistence
1. Link settings to user_id (from Phase 2.0 auth)
2. Load user settings on app start
3. Apply settings to agent configuration
4. Save settings changes to database

**Success Criteria:**
- App installs as PWA on mobile and desktop
- Settings page accessible via navigation
- Chat interface minimal (no config controls)
- Model selection in bottom-right of input (Ollama style)
- Provider/model settings persist per user
- SEO Coach business settings on dedicated tab

**Files to Create:**
- `static/manifest.json` - Comprehensive PWA manifest with all metadata
- `static/service-worker.js` - Offline support
- `ui/settings_page.py` - Dedicated settings interface
- `ui/minimal_chat.py` - Ollama-style chat interface
- `static/icons/` - PWA icons (8 sizes: 72, 96, 128, 144, 152, 192, 384, 512)
  - `icon-72.png`, `icon-96.png`, `icon-128.png`, `icon-144.png`
  - `icon-152.png`, `icon-192.png` (REQUIRED), `icon-384.png`
  - `icon-512.png` (REQUIRED)
  - `shortcut-chat.png`, `shortcut-settings.png`, `shortcut-history.png` (96x96)
- `static/screenshots/` - App store screenshots
  - `desktop-home.png` (1280x720, wide)
  - `desktop-settings.png` (1280x720, wide)
  - `mobile-chat.png` (750x1334, narrow)
  - `mobile-settings.png` (750x1334, narrow)
- `api/routes/share.py` - Share target handler endpoint

**Files to Modify:**
- `ui/app.py` - Use minimal chat interface
- `ui/seo_coach_app.py` - Use minimal chat + company settings tab
- `main.py` - Add PWA routes and static file serving
- `services/user_settings_service.py` - Settings CRUD operations

**PWA Manifest Example:**

```json
{
  "name": "Agent Workbench",
  "short_name": "Workbench",
  "description": "AI Agent Development Platform with LangGraph and MCP Tools",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#000000",
  "orientation": "portrait-primary",
  "categories": [
    "productivity",
    "developer-tools",
    "utilities"
  ],
  "lang": "en-US",
  "dir": "ltr",
  "icons": [
    {
      "src": "/static/icons/icon-72.png",
      "sizes": "72x72",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-96.png",
      "sizes": "96x96",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-128.png",
      "sizes": "128x128",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-144.png",
      "sizes": "144x144",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-152.png",
      "sizes": "152x152",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/static/icons/icon-384.png",
      "sizes": "384x384",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/static/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ],
  "screenshots": [
    {
      "src": "/static/screenshots/desktop-home.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Agent Workbench main chat interface"
    },
    {
      "src": "/static/screenshots/desktop-settings.png",
      "sizes": "1280x720",
      "type": "image/png",
      "form_factor": "wide",
      "label": "Settings page with model configuration"
    },
    {
      "src": "/static/screenshots/mobile-chat.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Mobile chat interface"
    },
    {
      "src": "/static/screenshots/mobile-settings.png",
      "sizes": "750x1334",
      "type": "image/png",
      "form_factor": "narrow",
      "label": "Mobile settings view"
    }
  ],
  "shortcuts": [
    {
      "name": "New Chat",
      "short_name": "Chat",
      "description": "Start a new conversation",
      "url": "/?new=true",
      "icons": [
        {
          "src": "/static/icons/shortcut-chat.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    },
    {
      "name": "Settings",
      "short_name": "Settings",
      "description": "Open settings page",
      "url": "/settings",
      "icons": [
        {
          "src": "/static/icons/shortcut-settings.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    },
    {
      "name": "Recent Conversations",
      "short_name": "History",
      "description": "View conversation history",
      "url": "/history",
      "icons": [
        {
          "src": "/static/icons/shortcut-history.png",
          "sizes": "96x96",
          "type": "image/png"
        }
      ]
    }
  ],
  "related_applications": [],
  "prefer_related_applications": false,
  "iarc_rating_id": "",
  "share_target": {
    "action": "/share",
    "method": "POST",
    "enctype": "multipart/form-data",
    "params": {
      "title": "title",
      "text": "text",
      "url": "url",
      "files": [
        {
          "name": "documents",
          "accept": [
            "text/*",
            "application/pdf",
            ".md",
            ".txt"
          ]
        }
      ]
    }
  }
}
```

**Icon Sizes Required:**

PWA apps need multiple icon sizes for different contexts:
- **72x72**: Android old devices
- **96x96**: Android notification icons
- **128x128**: Chrome Web Store
- **144x144**: Windows tiles
- **152x152**: iOS devices
- **192x192**: Android home screen (minimum required)
- **384x384**: High-resolution displays
- **512x512**: Splash screens and app stores (minimum required)

**Screenshot Requirements:**

App store listings require screenshots:
- **Desktop (wide)**: 1280x720 or higher (16:9 aspect ratio)
- **Mobile (narrow)**: 750x1334 or higher (typical phone aspect)
- **Minimum**: 2 screenshots (1 desktop, 1 mobile recommended)
- **Maximum**: 8 screenshots
- **Format**: PNG or JPEG

**Shortcuts Best Practices:**

Quick actions from home screen:
- **Maximum**: 4 shortcuts
- **Icons**: 96x96 recommended
- **Use cases**: New chat, settings, history, common workflows

**Gradio Settings Page Layout:**

```python
# ui/settings_page.py

import gradio as gr
from typing import Optional
from services.user_settings_service import UserSettingsService

def create_settings_page(user_id: str) -> gr.Blocks:
    """
    Dedicated settings page with tabs.

    Follows Ollama pattern: settings separate from chat.
    """

    with gr.Blocks(title="Settings") as settings_page:
        gr.Markdown("# Settings")

        with gr.Tabs():
            # Tab 1: Account
            with gr.Tab("Account"):
                with gr.Column():
                    gr.Markdown("### HuggingFace Account")
                    hf_username = gr.Textbox(label="Username", interactive=False)
                    hf_email = gr.Textbox(label="Email", interactive=False)

                    gr.Markdown("### Preferences")
                    theme = gr.Radio(
                        ["Light", "Dark", "Auto"],
                        label="Theme",
                        value="Auto"
                    )
                    language = gr.Dropdown(
                        ["English", "Nederlands"],
                        label="Language",
                        value="English"
                    )

            # Tab 2: Models (moved from chat UI)
            with gr.Tab("Models"):
                with gr.Column():
                    gr.Markdown("### Provider Configuration")

                    provider = gr.Dropdown(
                        ["OpenRouter", "Anthropic", "OpenAI", "Ollama"],
                        label="Default Provider",
                        value="OpenRouter",
                        info="Primary API provider"
                    )

                    # OpenRouter settings
                    with gr.Group(visible=True) as openrouter_settings:
                        gr.Markdown("#### OpenRouter Settings")
                        openrouter_model = gr.Dropdown(
                            [
                                "anthropic/claude-sonnet-4-5",
                                "openai/gpt-4-turbo",
                                "google/gemini-pro",
                                "meta-llama/llama-3-70b"
                            ],
                            label="Model",
                            value="anthropic/claude-sonnet-4-5"
                        )
                        openrouter_api_key = gr.Textbox(
                            label="API Key",
                            type="password",
                            placeholder="sk-or-v1-..."
                        )

                    # Model parameters
                    gr.Markdown("#### Model Parameters")
                    temperature = gr.Slider(0, 2, value=0.7, label="Temperature")
                    max_tokens = gr.Slider(100, 8000, value=2000, label="Max Tokens")

                    save_model_btn = gr.Button("Save Model Settings", variant="primary")

            # Tab 3: Company (SEO Coach only)
            with gr.Tab("Company", visible=False) as company_tab:
                with gr.Column():
                    gr.Markdown("### Business Profile")

                    company_name = gr.Textbox(label="Company Name")
                    company_website = gr.Textbox(label="Website URL")
                    company_industry = gr.Dropdown(
                        ["Technology", "Retail", "Services", "Healthcare", "Other"],
                        label="Industry"
                    )

                    gr.Markdown("### Brand Settings")
                    brand_voice = gr.Radio(
                        ["Professional", "Friendly", "Technical", "Creative"],
                        label="Brand Voice"
                    )
                    target_audience = gr.Textbox(
                        label="Target Audience",
                        placeholder="e.g., B2B enterprises, local consumers"
                    )

                    save_company_btn = gr.Button("Save Company Settings", variant="primary")

            # Tab 4: Advanced
            with gr.Tab("Advanced"):
                with gr.Column():
                    gr.Markdown("### Developer Settings")

                    debug_mode = gr.Checkbox(label="Enable Debug Mode")
                    verbose_logs = gr.Checkbox(label="Verbose Logging")

                    gr.Markdown("### Experimental Features")
                    enable_mcp_tools = gr.Checkbox(
                        label="Enable MCP Tools",
                        value=True
                    )
                    enable_firecrawl = gr.Checkbox(
                        label="Enable Firecrawl Web Scraping"
                    )

                    save_advanced_btn = gr.Button("Save Advanced Settings", variant="primary")

        # Load settings on page load
        settings_page.load(
            fn=load_user_settings,
            inputs=[gr.State(user_id)],
            outputs=[
                hf_username, hf_email, theme, language,
                provider, openrouter_model, temperature, max_tokens,
                company_name, company_website, brand_voice,
                debug_mode, enable_mcp_tools
            ]
        )

        # Save handlers
        save_model_btn.click(
            fn=save_model_settings,
            inputs=[gr.State(user_id), provider, openrouter_model, temperature, max_tokens],
            outputs=[gr.Textbox(label="Status")]
        )

    return settings_page
```

**Minimal Chat Interface (Ollama Pattern):**

```python
# ui/minimal_chat.py

import gradio as gr

def create_minimal_chat_interface() -> gr.Blocks:
    """
    Ollama-style minimal chat interface.

    - Centered chat with logo
    - Model selector in bottom-right (minimal)
    - No configuration controls in chat view
    """

    with gr.Blocks(
        title="Agent Workbench",
        css="""
        /* Ollama-style centered layout */
        .chat-container {
            max-width: 800px;
            margin: 0 auto;
            padding-top: 10vh;
        }
        .logo-center {
            text-align: center;
            margin-bottom: 2rem;
            font-size: 3rem;
        }
        .message-input {
            position: relative;
        }
        .model-selector {
            position: absolute;
            bottom: 12px;
            right: 60px;
            font-size: 0.9rem;
        }
        .settings-icon {
            position: fixed;
            top: 20px;
            right: 20px;
        }
        """
    ) as app:

        with gr.Column(elem_classes=["chat-container"]):
            # Centered logo (like Ollama llama icon)
            gr.HTML('<div class="logo-center">🤖</div>')

            # Chat interface
            chatbot = gr.Chatbot(
                height=500,
                show_label=False,
                container=True
            )

            # Message input with inline model selector
            with gr.Row(elem_classes=["message-input"]):
                msg = gr.Textbox(
                    placeholder="Send a message",
                    show_label=False,
                    scale=10,
                    container=False
                )

                # Model selector (bottom-right, minimal like Ollama)
                model_selector = gr.Dropdown(
                    choices=["claude-sonnet-4-5", "gpt-4-turbo", "gemini-pro"],
                    value="claude-sonnet-4-5",
                    show_label=False,
                    scale=2,
                    container=False,
                    elem_classes=["model-selector"]
                )

                submit_btn = gr.Button("↑", scale=1)

        # Settings icon/link (top-right)
        with gr.Row(elem_classes=["settings-icon"]):
            settings_link = gr.Button("⚙️", size="sm")
            settings_link.click(fn=lambda: None, js="window.location.href = '/settings'")

    return app
```

**Service Worker for Offline Support:**

```javascript
// static/service-worker.js

const CACHE_NAME = 'agent-workbench-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png'
];

// Install service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

// Fetch from cache, fallback to network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => response || fetch(event.request))
  );
});
```

**Settings Service:**

```python
# services/user_settings_service.py

from typing import Dict, Any, Optional
from uuid import UUID
from database.adapter import AdaptiveDatabase

class UserSettingsService:
    """Manage user settings persistence."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def get_all_settings(self, user_id: UUID) -> Dict[str, Any]:
        """Load all user settings grouped by category."""

        settings = self.db.get_user_settings_dict(user_id)

        return {
            "account": {
                "theme": settings.get("theme", "Auto"),
                "language": settings.get("language", "English")
            },
            "models": {
                "provider": settings.get("provider", "OpenRouter"),
                "model": settings.get("model", "anthropic/claude-sonnet-4-5"),
                "temperature": settings.get("temperature", 0.7),
                "max_tokens": settings.get("max_tokens", 2000)
            },
            "company": {
                "name": settings.get("company_name"),
                "website": settings.get("company_website"),
                "industry": settings.get("company_industry"),
                "brand_voice": settings.get("brand_voice")
            },
            "advanced": {
                "debug_mode": settings.get("debug_mode", False),
                "enable_mcp_tools": settings.get("enable_mcp_tools", True)
            }
        }

    async def save_model_settings(
        self,
        user_id: UUID,
        provider: str,
        model: str,
        temperature: float,
        max_tokens: int
    ):
        """Save model configuration settings."""

        self.db.update_user_setting(user_id, "provider", provider, "active", "models")
        self.db.update_user_setting(user_id, "model", model, "active", "models")
        self.db.update_user_setting(user_id, "temperature", temperature, "active", "models")
        self.db.update_user_setting(user_id, "max_tokens", max_tokens, "active", "models")

    async def get_active_model_config(self, user_id: UUID) -> Dict[str, Any]:
        """Get user's active model configuration for agent initialization."""

        settings = self.db.get_user_settings_dict(user_id)

        return {
            "provider": settings.get("provider", "OpenRouter"),
            "model": settings.get("model", "anthropic/claude-sonnet-4-5"),
            "temperature": settings.get("temperature", 0.7),
            "max_tokens": settings.get("max_tokens", 2000)
        }
```

**Main.py Integration:**

```python
# main.py additions

from fastapi import FastAPI, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from typing import List
from uuid import uuid4
from urllib.parse import quote_plus

app = FastAPI()

# Serve PWA static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/manifest.json")
async def manifest():
    """Serve PWA manifest."""
    return FileResponse("static/manifest.json")

@app.get("/service-worker.js")
async def service_worker():
    """Serve service worker."""
    return FileResponse("static/service-worker.js")

# Settings page route
@app.get("/settings")
async def settings_page():
    """Render settings page."""
    # Use Gradio Blocks for settings interface
    from ui.settings_page import create_settings_page
    settings_ui = create_settings_page(user_id=get_current_user_id())
    return settings_ui

# Share target handler
@app.post("/share")
async def share_handler(
    title: str = Form(None),
    text: str = Form(None),
    url: str = Form(None),
    documents: List[UploadFile] = File(None)
):
    """
    Handle shared content from other apps (PWA share target).

    Allows users to share text, URLs, and files to the app
    from other applications via the system share menu.
    """
    # Create new conversation with shared content
    conversation_id = str(uuid4())

    # Build initial message from shared content
    shared_content = []
    if title:
        shared_content.append(f"**Title:** {title}")
    if text:
        shared_content.append(f"**Text:** {text}")
    if url:
        shared_content.append(f"**URL:** {url}")

    initial_message = "\n\n".join(shared_content)

    # Handle shared files
    if documents:
        file_descriptions = []
        for file in documents:
            # Save file temporarily or process it
            content = await file.read()
            filename = file.filename

            # Store file for conversation
            # TODO: Implement file storage service
            file_descriptions.append(f"- {filename} ({len(content)} bytes)")

        if file_descriptions:
            initial_message += "\n\n**Attached Files:**\n" + "\n".join(file_descriptions)

    # Redirect to chat with pre-filled message
    return RedirectResponse(
        url=f"/?conversation_id={conversation_id}&message={quote_plus(initial_message)}",
        status_code=303
    )
```

**Share Target Usage:**

Users can share content to Agent Workbench from:
- Browser pages (share URL to analyze)
- Text selection (share selected text for analysis)
- Files from file manager (share documents for processing)
- Other apps (share notes, emails, etc.)

Example use cases:
- Share a website URL to extract SEO insights
- Share a document for analysis
- Share selected text for summarization
- Share notes for AI processing

**Phase 2.1 Checklist:**

**PWA Manifest & Assets:**
- [ ] PWA manifest.json created with comprehensive metadata
  - [ ] Basic fields: name, short_name, description, start_url
  - [ ] `scope` field for URL handling
  - [ ] `categories` array (productivity, developer-tools, utilities)
  - [ ] `lang`, `dir`, `orientation` fields
- [ ] Service worker implemented for offline support
- [ ] App icons created and added to static/icons/:
  - [ ] icon-72.png (Android old devices)
  - [ ] icon-96.png (Android notifications, shortcut icons)
  - [ ] icon-128.png (Chrome Web Store)
  - [ ] icon-144.png (Windows tiles)
  - [ ] icon-152.png (iOS devices)
  - [ ] icon-192.png (Android home screen - REQUIRED)
  - [ ] icon-384.png (High-res displays)
  - [ ] icon-512.png (Splash screens - REQUIRED)
- [ ] Screenshots captured and added to static/screenshots/:
  - [ ] desktop-home.png (1280x720, form_factor: wide)
  - [ ] desktop-settings.png (1280x720, form_factor: wide)
  - [ ] mobile-chat.png (750x1334, form_factor: narrow)
  - [ ] mobile-settings.png (750x1334, form_factor: narrow)
- [ ] Shortcut icons created (96x96):
  - [ ] shortcut-chat.png (New Chat)
  - [ ] shortcut-settings.png (Settings)
  - [ ] shortcut-history.png (Recent Conversations)
- [ ] Share target handler implemented at /share endpoint

**UI Components:**
- [ ] Settings page with 4 tabs created
- [ ] Model/provider selection moved from chat to settings
- [ ] SEO Coach company settings on dedicated tab
- [ ] Minimal chat interface (Ollama pattern) implemented
- [ ] Model selector in bottom-right of input
- [ ] Navigation between chat and settings works

**Backend Integration:**
- [ ] Settings persistence via UserSettingsService
- [ ] Settings load on app start and apply to agent
- [ ] PWA static file routes configured in main.py
- [ ] /manifest.json endpoint serving manifest
- [ ] /service-worker.js endpoint configured

**Testing:**
- [ ] "Add to Home Screen" works on mobile (Android/iOS)
- [ ] "Add to Home Screen" works on desktop (Chrome/Edge)
- [ ] Shortcuts appear in app context menu
- [ ] Share target works (share files to app)
- [ ] App installs offline-capable
- [ ] Both HF Spaces (workbench + seo_coach) support PWA
- [ ] Lighthouse PWA audit score > 90

---

### Phase 2.2: Enhanced Gradio UI with File Support (STUBBED)

**Goal:** Build visible MVP with file upload UI - backend stubbed for now

**⚠️ MVP STRATEGY: UI First, Working Backend Later**
- Build complete UI with file upload, downloads, approval dialogs
- Stub all backend calls with placeholder responses
- Get to visible results ASAP
- Backend implementation comes in later phases

**Tasks:**

#### 2.2a: File Upload UI Components (Stubbed Backend)
1. Add file upload component to Gradio interface
2. Display uploaded file metadata
3. Show "processing" status
4. **Stub:** `DocumentProcessor` returns placeholder data
5. **Stub:** File content not actually processed yet

#### 2.2b: File Download UI Components (Stubbed Backend)
1. Add download buttons for conversation export
2. Support multiple export formats (JSON, CSV, TXT, PDF)
3. **Stub:** Generate simple placeholder files
4. **Stub:** Agent-generated files show "Coming soon" message

#### 2.2c: Human-in-the-Loop UI (Stubbed Backend)
1. Create approval dialog component
2. Add approve/edit/reject buttons
3. **Stub:** Approval always auto-approves for now
4. **Stub:** Edit functionality shows but doesn't work yet

**Success Criteria:**
- ✅ File upload UI appears and accepts files
- ✅ Upload shows metadata (filename, size, type)
- ✅ Download buttons appear and work (with stub content)
- ✅ Approval dialog appears and dismisses
- ⚠️ Backend processing stubbed (placeholder responses)

**Stub Implementations:**

```python
# services/document_processor.py (STUB VERSION)

class DocumentProcessor:
    """Stubbed document processor - returns placeholder data."""

    async def process_file(
        self,
        file_path: str,
        conversation_id: UUID
    ) -> Dict[str, Any]:
        """Stub: Return placeholder metadata without processing."""
        from pathlib import Path
        import os

        file_info = Path(file_path)

        return {
            "document_id": str(uuid4()),
            "filename": file_info.name,
            "file_type": file_info.suffix or "unknown",
            "size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            "content_preview": "📄 Document uploaded. Processing coming in Phase 2.4...",
            "status": "uploaded",
            "note": "⚠️ STUB: Actual processing not implemented yet"
        }
```

```python
# services/download_manager.py (STUB VERSION)

class DownloadManager:
    """Stubbed download manager - generates placeholder files."""

    @staticmethod
    async def export_conversation_history(
        conversation_id: UUID,
        format: str
    ) -> str:
        """Stub: Generate simple export file."""
        import tempfile
        import json

        output_dir = tempfile.gettempdir()
        filename = f"conversation_{conversation_id}.{format}"
        filepath = os.path.join(output_dir, filename)

        if format == "json":
            stub_data = {
                "conversation_id": str(conversation_id),
                "messages": [],
                "note": "⚠️ STUB: Actual conversation export coming later"
            }
            with open(filepath, 'w') as f:
                json.dump(stub_data, f, indent=2)

        elif format in ["txt", "csv"]:
            with open(filepath, 'w') as f:
                f.write(f"⚠️ STUB: {format.upper()} export coming in later phase\n")
                f.write(f"Conversation ID: {conversation_id}\n")

        return filepath
```

```python
# ui/components/approval_dialog.py (STUB VERSION)

class ApprovalDialog:
    """Stubbed approval dialog - always auto-approves."""

    @staticmethod
    async def show_approval_request(
        operation: str,
        parameters: Dict[str, Any]
    ) -> Literal["approve", "edit", "reject"]:
        """Stub: Always auto-approve for now."""
        print(f"⚠️ STUB: Auto-approving operation: {operation}")
        return "approve"
```

**Files to Create:**
- `ui/components/file_handler_ui.py` (file upload/download UI)
- `ui/components/approval_dialog.py` (human approval UI - stubbed)
- `services/document_processor.py` (STUB VERSION)
- `services/download_manager.py` (STUB VERSION)

**Files to Modify:**
- `ui/app.py` (add file components)
- `ui/seo_coach_app.py` (add file upload UI)

**Phase 2.2 Checklist:**
- [ ] File upload component added to UI
- [ ] File metadata display working
- [ ] Download buttons render and create stub files
- [ ] Approval dialog appears and dismisses
- [ ] Stub implementations in place
- [ ] UI looks complete (even though backend stubbed)
- [ ] No errors when using UI components

**Note:** Actual file processing implemented in **Phase 2.4** (ContentRetriever Tool)

---

### Phase 2.3: Basic Agent Service + Debug Logging

**Goal:** Create minimal agent service AND comprehensive debug logging for troubleshooting

**⚠️ CRITICAL: Debug logging implemented EARLY**
- We'll hit many obstacles during development
- Need debug logs from the start to troubleshoot issues
- Agent starts minimal (no tools), but logging is comprehensive

**Tasks:**
1. Install `langchain` v1.0 (no MCP adapters yet)
2. Create minimal `AgentService` with NO tools
3. **Create debug logging database schema (AgentExecutionLogModel, ToolCallLogModel)**
4. **Create DebugLoggingMiddleware**
5. **Add debug logging to agent (even though no tools yet)**
6. Wrap existing LLM calls in `create_agent()` structure
7. Update workflow endpoint to use agent service
8. Test basic agent responses with debug logs capturing everything

**Success Criteria:**
- ✅ Agent responds to basic questions
- ✅ No tool calls (tools not added yet)
- ✅ Conversation history maintained
- ✅ Responses streamed to UI
- ✅ **Debug logs capturing all execution details in database**
- ✅ **Error stack traces stored when issues occur**
- ✅ **Can query logs to troubleshoot problems**
- ⚠️ Agent has no tools yet (coming in Phase 2.4)

**Minimal Agent with Debug Logging:**

```python
# services/agent_service.py (MINIMAL VERSION WITH DEBUG LOGGING)

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, List
from middleware.debug_logging_middleware import DebugLoggingMiddleware

class AgentService:
    """Minimal agent service with comprehensive debug logging."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None

    async def initialize(self):
        """Initialize agent WITHOUT tools but WITH debug logging."""

        # Create agent with NO tools but WITH debug logging middleware
        self.agent = create_agent(
            model=get_model(),
            tools=[],  # ← NO TOOLS YET
            middleware=[
                DebugLoggingMiddleware(db=self.db)  # ← DEBUG LOGGING FROM START
            ],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()  # Agent's working memory
        )

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """Execute agent with debug logging."""

        config = {
            "configurable": {
                "thread_id": task_id
            }
        }

        try:
            result = await self.agent.ainvoke(
                {"messages": messages, "config": user_settings},
                config=config
            )
            return result

        except Exception as e:
            # Debug logging middleware captures stack trace automatically
            raise
```

**Database Schema (see full implementation below):**
- `AgentExecutionLogModel` - Comprehensive execution log
- `ToolCallLogModel` - Individual tool call details

**Why Debug Logging Early:**
1. **Troubleshooting** - When agent fails, we have stack traces
2. **Performance** - Track execution time from day 1
3. **Analytics** - Understand usage patterns early
4. **Development** - See exactly what agent is doing during testing
5. **Production** - Ready for production monitoring from start

**Files to Create:**
- `services/agent_service.py` (minimal version with debug logging)
- `models/database.py` (add AgentExecutionLogModel, ToolCallLogModel with comprehensive indexes)
- `middleware/debug_logging_middleware.py` (comprehensive logging)
- `services/analytics_service.py` (optimized query methods using indexes)

**Files to Modify:**
- `services/consolidated_service.py` (use AgentService)
- `database/backends/sqlite.py` (add execution log methods)
- `database/backends/hub.py` (add execution log methods)
- `pyproject.toml` (add `langchain` v1.0)
- `.env.example` (add agent config vars)

**Phase 2.3 Checklist:**
- [ ] LangChain v1.0 installed
- [ ] AgentExecutionLogModel and ToolCallLogModel created
- [ ] DebugLoggingMiddleware implemented
- [ ] Database methods for execution logs added
- [ ] Minimal AgentService created with debug logging
- [ ] Agent initialized with empty tools list but logging middleware
- [ ] Workflow uses AgentService
- [ ] Agent responds to basic questions
- [ ] Streaming works
- [ ] **Debug logs captured for every execution**
- [ ] **Stack traces stored on errors**
- [ ] **Can query logs via database**
- [ ] No tool calls (expected - tools not added)

---

#### Debug Logging Schema (Phase 2.3)

**Full implementation moved from Phase 2.8 to Phase 2.3**

See comprehensive debug logging documentation below with:
- AgentExecutionLogModel (48 fields capturing everything)
- ToolCallLogModel (detailed tool call logs)
- DebugLoggingMiddleware (before_agent, after_agent, on_error hooks)
- Database service methods (create_execution_log, update_execution_log, etc.)

**What Gets Logged from Phase 2.3 onward:**
1. Execution metadata (task_id, timestamps, duration, status)
2. Agent configuration (model, provider, temperature, max_tokens)
3. Input/Output (user message, agent response, structured response)
4. Tool usage (none in Phase 2.3, but ready for Phase 2.4)
5. Middleware tracking (debug logging itself)
6. Performance metrics (step count, timing)
7. **Error information (exception type, message, FULL STACK TRACE)** ⭐
8. State snapshot (conversation history length, context keys)

**Query logs to troubleshoot:**
```python
# Get all errors during development
error_logs = await db.get_execution_logs(status="error", limit=100)

# Get specific user's agent executions
user_logs = await db.get_execution_logs(user_id=user_id)

# Get conversation execution history
conv_logs = await db.get_execution_logs(conversation_id=conv_id)
```

---

### Phase 2.4: ContentRetriever Tool (LangChain Tool)

**Goal:** Add ContentRetriever tool to agent for local file processing

**⚠️ FIRST TOOL: LangChain BaseTool for local files**
- ContentRetriever is a LangChain tool (NOT MCP)
- Handles local file processing only
- Replaces stubbed DocumentProcessor
- User priority: "Langchain tool first then mcp"

**Tasks:**
1. Create `ContentRetrieverTool` class (LangChain BaseTool)
2. Implement file format detection (extensionless files)
3. Add Docling integration with fallback to basic processing
4. Replace stubbed `DocumentProcessor` with real implementation
5. Add ContentRetriever to agent's tools list
6. Test file upload → processing → agent can access content

**Success Criteria:**
- ✅ ContentRetriever tool created
- ✅ Agent has ContentRetriever in tools list
- ✅ File uploads actually processed (not stubbed anymore)
- ✅ Agent can answer questions about uploaded files
- ✅ Docling advanced processing works
- ✅ Fallback to basic processing when Docling fails
- ✅ Tool shows up in agent's tool calls

**Files to Create:**
- `tools/content_retriever_tool.py` (LangChain BaseTool)
- `services/document_processor.py` (real implementation, replaces stub)
- `utils/file_handler.py` (file format detection)

**Files to Modify:**
- `services/agent_service.py` (add ContentRetriever to tools list)
- `pyproject.toml` (add docling, sentence-transformers dependencies)

**Phase 2.4 Checklist:**
- [ ] ContentRetrieverTool implemented as LangChain BaseTool
- [ ] File format detection working
- [ ] Docling integration complete
- [ ] Fallback to basic processing working
- [ ] DocumentProcessor real implementation replaces stub
- [ ] Agent initialized with ContentRetriever tool
- [ ] File uploads actually processed
- [ ] Agent can answer questions about files
- [ ] Tool calls visible in logs

**Note:** Firecrawl MCP tool (web scraping) added in **Phase 2.7**

---

### Phase 2.5: Built-in Middleware

**Goal:** Configure LangChain v1's built-in middleware correctly

**Tasks:**
1. Configure `PIIRedactionMiddleware` (patterns for email, phone, SSN, etc.)
2. Configure `SummarizationMiddleware` (token limits, model selection)
3. Configure `HumanInTheLoopMiddleware` (define sensitive operations)
4. Test each middleware independently
5. Test middleware chain execution

**Success Criteria:**
- PII automatically redacted in logs and API calls
- Conversations summarized when approaching token limits
- Sensitive operations (send_email, delete_file) pause for approval
- Middleware executes in correct order

**Files to Modify:**
- `services/agent_service.py`
- `config/middleware.py` (middleware configuration)

---

### Phase 2.6: Custom Middleware

**Goal:** Implement custom middleware for context and memory

**Tasks:**
1. Create `ContextMiddleware` (load conversation history from DB)
2. Create `MemoryMiddleware` (save responses to DB)
3. Create `ExecutionTrackingMiddleware` (track metrics using Phase 1 ContextService)
4. Create `GuardrailsMiddleware` (optional: tool validation)
5. Add custom middleware to agent
6. Test custom middleware with built-in middleware

**Success Criteria:**
- Context loaded from DB before agent runs
- Responses saved to DB after agent completes
- Execution metrics tracked in Phase 1 ContextService
- Custom middleware integrates with built-in middleware
- No middleware conflicts

**Files to Create:**
- `middleware/context_middleware.py`
- `middleware/memory_middleware.py`
- `middleware/execution_tracking_middleware.py` (uses Phase 1 ContextService)
- `middleware/guardrails_middleware.py` (optional)

**Files to Modify:**
- `services/agent_service.py`
- `services/context_service.py` (complete Phase 1 placeholder implementation)

**Phase 2.6 Checklist:**
- [ ] ContextMiddleware created and tested
- [ ] MemoryMiddleware created and tested
- [ ] ExecutionTrackingMiddleware maps to Phase 1 ContextService
- [ ] GuardrailsMiddleware created (optional)
- [ ] All middleware added to agent
- [ ] Middleware chain executes in correct order
- [ ] No conflicts between built-in and custom middleware

---

### Phase 2.7: Firecrawl MCP Tool (Web Scraping)

**Goal:** Add Firecrawl MCP tool for web scraping capabilities

**⚠️ SECOND TOOL: MCP Tool for web scraping**
- Firecrawl is an MCP tool (NOT LangChain)
- Accessed via `langchain-mcp-adapters`
- Comes after ContentRetriever (user priority: "Langchain tool first then mcp")
- Handles web URLs, not local files

**Tasks:**
1. Install `langchain-mcp-adapters` package
2. Create MCP server configuration for Firecrawl
3. Add `MCPService` for managing MCP connections
4. Configure Firecrawl API key in environment
5. Add Firecrawl tools to agent's tools list
6. Test web scraping with various sites
7. Update approval dialog to handle web scraping operations

**Success Criteria:**
- ✅ MCP adapters installed and working
- ✅ Firecrawl MCP server configured
- ✅ MCPService manages MCP connections
- ✅ Agent has both ContentRetriever (LangChain) + Firecrawl (MCP) tools
- ✅ Web scraping works for complex sites
- ✅ Agent can answer questions about scraped content
- ✅ Tool selection is intelligent (local files → ContentRetriever, web URLs → Firecrawl)

**MCP Server Configuration:**

```python
# config/mcp_servers.py

import os

MCP_SERVERS = {
    "firecrawl": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-firecrawl"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
        }
    }
}
```

**MCPService Implementation:**

```python
# services/mcp_service.py

from langchain_mcp_adapters.client import MultiServerMCPClient
from typing import Dict, List, Any

class MCPService:
    """Manages MCP server connections and tools."""

    def __init__(self):
        self.client = None
        self.tools = []

    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        """Initialize MCP servers and load tools."""

        self.client = MultiServerMCPClient(mcp_server_configs)

        # Get all MCP tools
        self.tools = await self.client.get_tools()

        return self.tools

    async def cleanup(self):
        """Close MCP connections."""
        if self.client:
            await self.client.close()
```

**Agent Service Integration:**

```python
# services/agent_service.py (UPDATE)

class AgentService:
    async def initialize(self, mcp_server_configs: Dict[str, Dict] = None):
        """Initialize agent with both LangChain and MCP tools."""

        tools = []

        # 1. Add LangChain tools (ContentRetriever)
        from tools.content_retriever_tool import ContentRetrieverTool
        content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")
        tools.append(content_retriever)

        # 2. Add MCP tools (Firecrawl) if configured
        if mcp_server_configs:
            from services.mcp_service import MCPService
            self.mcp_service = MCPService()
            mcp_tools = await self.mcp_service.initialize(mcp_server_configs)
            tools.extend(mcp_tools)

        # 3. Create agent with combined tools
        self.agent = create_agent(
            model=get_model(),
            tools=tools,  # Both LangChain + MCP tools
            middleware=[...],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )
```

**Firecrawl Tools Available:**
- `scrape_url(url: str)` - Scrape single URL and return markdown
- `crawl_site(url: str, max_depth: int)` - Crawl entire site
- `extract_links(url: str)` - Get all links from page

**Files to Create:**
- `services/mcp_service.py` (MCP connection manager)
- `config/mcp_servers.py` (MCP server configurations)

**Files to Modify:**
- `services/agent_service.py` (add MCP tools to agent)
- `pyproject.toml` (add `langchain-mcp-adapters`)
- `.env.example` (add `FIRECRAWL_API_KEY`)

**Phase 2.7 Checklist:**
- [ ] `langchain-mcp-adapters` installed
- [ ] Firecrawl MCP server configured
- [ ] MCPService created and tested
- [ ] Firecrawl API key configured
- [ ] Agent has both ContentRetriever + Firecrawl tools
- [ ] Web scraping works
- [ ] Agent intelligently selects correct tool (local vs web)
- [ ] Tool calls visible in logs

---

### Phase 2.8: Production Hardening

**Goal:** Error handling, observability, production readiness, and comprehensive debug logging

**Tasks:**
1. Add comprehensive error handling and retries
2. Add middleware performance logging
3. Add tool usage tracking and metrics
4. **Add debug logs to database with technical information**
5. Test all failure scenarios (network errors, API failures, timeout)
6. Add health checks for all services (agent, MCP, database)
7. Implement rate limiting for agent calls
8. Add request/response validation
9. Implement proper cleanup (temp files, MCP connections)
10. Add monitoring and alerting hooks
11. Load testing and performance optimization

**Success Criteria:**
- ✅ Graceful error handling for all failure modes
- ✅ Middleware performance metrics logged
- ✅ Tool usage tracked in database
- ✅ **Debug logs with technical details stored in database**
- ✅ Failed requests don't crash application
- ✅ Health endpoint shows all service statuses
- ✅ Rate limiting prevents abuse
- ✅ Temp files cleaned up automatically
- ✅ MCP connections properly closed on shutdown
- ✅ Application handles concurrent requests
- ✅ Performance metrics within acceptable ranges

---

### Debug Logging to Database

**⚠️ NOTE: Debug logging MOVED to Phase 2.3**

Debug logging was originally planned for Phase 2.8 but moved to **Phase 2.3** because:
- We'll hit many obstacles during development
- Need debug logs from the start to troubleshoot issues
- Can't wait until Phase 2.8 to debug problems in Phase 2.3-2.7

See **Phase 2.3** for implementation details.

**Original documentation kept below for reference:**

---

**Goal:** Store comprehensive technical debug information in database for troubleshooting, analytics, and error tracking.

**Database Schema for Debug Logs:**

```python
# models/database.py

from sqlalchemy import ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class AgentExecutionLogModel(Base):
    """
    Comprehensive debug log for agent executions.

    Stores technical details for troubleshooting and analytics.
    """
    __tablename__ = "agent_execution_logs"

    # Primary identification
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), index=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("user_sessions.id"))

    # Timing
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, index=True)
    completed_at: Mapped[Optional[datetime]]
    duration_ms: Mapped[Optional[int]]  # Milliseconds

    # Execution details
    task_id: Mapped[str] = mapped_column(index=True)  # Agent's working memory thread_id
    workflow_mode: Mapped[str]  # "workbench" or "seo_coach"
    execution_status: Mapped[str]  # "success", "error", "timeout", "cancelled"

    # Agent configuration
    model_provider: Mapped[str]  # "openrouter", "anthropic", etc.
    model_name: Mapped[str]  # "claude-sonnet-4-5", etc.
    temperature: Mapped[Optional[float]]
    max_tokens: Mapped[Optional[int]]

    # Input/Output
    user_message: Mapped[Text]
    agent_response: Mapped[Optional[Text]]
    structured_response: Mapped[Optional[JSON]]  # AgentResponse Pydantic model as JSON

    # Tool usage
    tools_available: Mapped[JSON]  # List of tool names
    tools_called: Mapped[JSON]  # List of {tool_name, arguments, result, duration_ms}
    tool_call_count: Mapped[int] = mapped_column(default=0)

    # Middleware tracking
    middleware_chain: Mapped[JSON]  # List of middleware names executed
    middleware_timings: Mapped[JSON]  # {middleware_name: duration_ms}
    pii_redacted: Mapped[bool] = mapped_column(default=False)
    summarization_triggered: Mapped[bool] = mapped_column(default=False)

    # Performance metrics
    step_count: Mapped[int] = mapped_column(default=0)
    token_count_input: Mapped[Optional[int]]
    token_count_output: Mapped[Optional[int]]
    token_count_total: Mapped[Optional[int]]
    cost_usd: Mapped[Optional[float]]  # Estimated cost

    # Error tracking
    error_type: Mapped[Optional[str]]  # Exception class name
    error_message: Mapped[Optional[Text]]
    error_stack_trace: Mapped[Optional[Text]]
    retry_count: Mapped[int] = mapped_column(default=0)

    # Context and state
    context_sources: Mapped[JSON]  # List of context sources used
    context_size_bytes: Mapped[Optional[int]]
    state_snapshot: Mapped[Optional[JSON]]  # Snapshot of WorkbenchState at completion

    # Relationships
    conversation: Mapped["ConversationModel"] = relationship(back_populates="execution_logs")
    user: Mapped["UserModel"] = relationship()
    session: Mapped[Optional["UserSessionModel"]] = relationship()


class ToolCallLogModel(Base):
    """
    Detailed log for individual tool calls within an agent execution.

    Stores arguments, results, and timing for each tool invocation.
    """
    __tablename__ = "tool_call_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    execution_log_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_execution_logs.id"),
        index=True
    )

    # Tool identification
    tool_name: Mapped[str] = mapped_column(index=True)
    tool_type: Mapped[str]  # "langchain" or "mcp"
    call_index: Mapped[int]  # Order within execution (0, 1, 2, ...)

    # Timing
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]]
    duration_ms: Mapped[Optional[int]]

    # Call details
    arguments: Mapped[JSON]  # Tool input arguments
    result: Mapped[Optional[JSON]]  # Tool output
    status: Mapped[str]  # "success", "error", "timeout"

    # Error tracking
    error_type: Mapped[Optional[str]]
    error_message: Mapped[Optional[Text]]

    # Relationships
    execution_log: Mapped["AgentExecutionLogModel"] = relationship()


# Add indexes for common queries
# CRITICAL: These indexes optimize production debugging and analytics queries

# Query: Get all executions for a conversation (sorted by time)
# Use case: View complete execution history for a conversation
Index('idx_execution_logs_conv_id',
      AgentExecutionLogModel.conversation_id,
      AgentExecutionLogModel.started_at)

# Query: Get all errors for a specific user
# Use case: User-specific error tracking and troubleshooting
Index('idx_execution_logs_user_status',
      AgentExecutionLogModel.user_id,
      AgentExecutionLogModel.execution_status)

# Query: Find executions by user and date range
# Use case: User activity reports, usage analytics
Index('idx_execution_logs_user_date',
      AgentExecutionLogModel.user_id,
      AgentExecutionLogModel.started_at)

# Query: Find all failed executions across system
# Use case: System-wide error monitoring, SLA tracking
Index('idx_execution_logs_status',
      AgentExecutionLogModel.execution_status,
      AgentExecutionLogModel.started_at)

# Query: Find executions by task_id (working memory thread)
# Use case: Track agent's internal task state across multiple executions
# Note: task_id already has single-column index at line 3415

# Query: Get all tool calls for an execution (in order)
# Use case: Debug tool execution sequence, replay tool calls
Index('idx_tool_calls_execution',
      ToolCallLogModel.execution_log_id,
      ToolCallLogModel.call_index)

# Query: Analyze tool performance across all executions
# Use case: Identify slow tools, optimize tool implementations
Index('idx_tool_calls_performance',
      ToolCallLogModel.tool_name,
      ToolCallLogModel.duration_ms)

# Query: Find tool calls by name and date
# Use case: Tool usage analytics, adoption tracking
Index('idx_tool_calls_tool_date',
      ToolCallLogModel.tool_name,
      ToolCallLogModel.started_at)

# Query: Find executions by model provider/name
# Use case: Compare performance across models, cost analysis
Index('idx_execution_logs_model',
      AgentExecutionLogModel.model_provider,
      AgentExecutionLogModel.model_name,
      AgentExecutionLogModel.started_at)

# Query: Find high-cost executions
# Use case: Cost monitoring, identify expensive queries
Index('idx_execution_logs_cost',
      AgentExecutionLogModel.cost_usd.desc(),
      AgentExecutionLogModel.started_at)

# Query: Find long-running executions
# Use case: Performance monitoring, timeout analysis
Index('idx_execution_logs_duration',
      AgentExecutionLogModel.duration_ms.desc(),
      AgentExecutionLogModel.started_at)
```

**Example Queries Using Indexes:**

```python
# services/analytics_service.py

from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

class AnalyticsService:
    """Query execution logs efficiently using indexes."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    # USE INDEX: idx_execution_logs_conv_id
    def get_conversation_executions(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Get all executions for a conversation (chronological order).
        Uses composite index on (conversation_id, started_at).
        """
        with self.db.session() as session:
            return session.scalars(
                select(AgentExecutionLogModel)
                .where(AgentExecutionLogModel.conversation_id == conversation_id)
                .order_by(AgentExecutionLogModel.started_at.desc())
                .limit(limit)
            ).all()

    # USE INDEX: idx_execution_logs_user_status
    def get_user_errors(
        self,
        user_id: UUID,
        since: datetime = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """
        Get all errors for a user.
        Uses composite index on (user_id, execution_status).
        """
        with self.db.session() as session:
            query = (
                select(AgentExecutionLogModel)
                .where(
                    and_(
                        AgentExecutionLogModel.user_id == user_id,
                        AgentExecutionLogModel.execution_status == "error"
                    )
                )
            )

            if since:
                query = query.where(AgentExecutionLogModel.started_at >= since)

            return session.scalars(
                query.order_by(AgentExecutionLogModel.started_at.desc()).limit(limit)
            ).all()

    # USE INDEX: idx_execution_logs_status
    def get_system_errors(
        self,
        since: datetime = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """
        Get all errors across the system.
        Uses composite index on (execution_status, started_at).
        """
        with self.db.session() as session:
            query = select(AgentExecutionLogModel).where(
                AgentExecutionLogModel.execution_status == "error"
            )

            if since:
                query = query.where(AgentExecutionLogModel.started_at >= since)

            return session.scalars(
                query.order_by(AgentExecutionLogModel.started_at.desc()).limit(limit)
            ).all()

    # USE INDEX: idx_tool_calls_execution
    def get_execution_tool_calls(
        self,
        execution_log_id: UUID
    ) -> List[ToolCallLogModel]:
        """
        Get all tool calls for an execution (in order).
        Uses composite index on (execution_log_id, call_index).
        """
        with self.db.session() as session:
            return session.scalars(
                select(ToolCallLogModel)
                .where(ToolCallLogModel.execution_log_id == execution_log_id)
                .order_by(ToolCallLogModel.call_index)
            ).all()

    # USE INDEX: idx_tool_calls_performance
    def get_slowest_tools(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find slowest tool calls across all executions.
        Uses composite index on (tool_name, duration_ms).
        """
        with self.db.session() as session:
            return session.execute(
                select(
                    ToolCallLogModel.tool_name,
                    func.avg(ToolCallLogModel.duration_ms).label('avg_duration'),
                    func.max(ToolCallLogModel.duration_ms).label('max_duration'),
                    func.count().label('call_count')
                )
                .group_by(ToolCallLogModel.tool_name)
                .order_by(desc('avg_duration'))
                .limit(limit)
            ).all()

    # USE INDEX: idx_execution_logs_model
    def get_model_performance(
        self,
        provider: str = None,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Compare performance across models.
        Uses composite index on (model_provider, model_name, started_at).
        """
        with self.db.session() as session:
            query = select(
                AgentExecutionLogModel.model_provider,
                AgentExecutionLogModel.model_name,
                func.avg(AgentExecutionLogModel.duration_ms).label('avg_duration'),
                func.avg(AgentExecutionLogModel.token_count_total).label('avg_tokens'),
                func.avg(AgentExecutionLogModel.cost_usd).label('avg_cost'),
                func.count().label('execution_count')
            )

            if provider:
                query = query.where(AgentExecutionLogModel.model_provider == provider)

            if since:
                query = query.where(AgentExecutionLogModel.started_at >= since)

            return session.execute(
                query
                .group_by(
                    AgentExecutionLogModel.model_provider,
                    AgentExecutionLogModel.model_name
                )
                .order_by(desc('execution_count'))
            ).all()

    # USE INDEX: idx_execution_logs_cost
    def get_expensive_executions(
        self,
        threshold_usd: float = 0.10,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Find high-cost executions.
        Uses index on (cost_usd DESC, started_at).
        """
        with self.db.session() as session:
            return session.scalars(
                select(AgentExecutionLogModel)
                .where(AgentExecutionLogModel.cost_usd >= threshold_usd)
                .order_by(
                    AgentExecutionLogModel.cost_usd.desc(),
                    AgentExecutionLogModel.started_at.desc()
                )
                .limit(limit)
            ).all()

    # USE INDEX: idx_execution_logs_duration
    def get_slow_executions(
        self,
        threshold_ms: int = 10000,  # 10 seconds
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Find long-running executions.
        Uses index on (duration_ms DESC, started_at).
        """
        with self.db.session() as session:
            return session.scalars(
                select(AgentExecutionLogModel)
                .where(AgentExecutionLogModel.duration_ms >= threshold_ms)
                .order_by(
                    AgentExecutionLogModel.duration_ms.desc(),
                    AgentExecutionLogModel.started_at.desc()
                )
                .limit(limit)
            ).all()

    # COMPOSITE: Multiple indexes for complex query
    def get_user_tool_usage(
        self,
        user_id: UUID,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Get tool usage statistics for a user.
        Uses idx_execution_logs_user_date + idx_tool_calls_execution.
        """
        with self.db.session() as session:
            # First get user's executions (uses idx_execution_logs_user_date)
            exec_query = select(AgentExecutionLogModel.id).where(
                AgentExecutionLogModel.user_id == user_id
            )

            if since:
                exec_query = exec_query.where(AgentExecutionLogModel.started_at >= since)

            execution_ids = session.scalars(exec_query).all()

            if not execution_ids:
                return []

            # Then get tool calls for those executions (uses idx_tool_calls_execution)
            return session.execute(
                select(
                    ToolCallLogModel.tool_name,
                    func.count().label('usage_count'),
                    func.avg(ToolCallLogModel.duration_ms).label('avg_duration'),
                    func.sum(
                        func.case((ToolCallLogModel.status == 'error', 1), else_=0)
                    ).label('error_count')
                )
                .where(ToolCallLogModel.execution_log_id.in_(execution_ids))
                .group_by(ToolCallLogModel.tool_name)
                .order_by(desc('usage_count'))
            ).all()
```

**Index Performance Notes:**

- **Composite indexes**: Order matters! Leading column must be in WHERE clause
- **idx_execution_logs_conv_id**: Fast conversation history queries (common)
- **idx_execution_logs_user_status**: Instant error lookups per user (critical for support)
- **idx_tool_calls_execution**: Ordered tool call retrieval (debugging)
- **idx_tool_calls_performance**: Tool performance analytics (optimization)
- **Descending indexes**: Optimized for "top N" queries (cost, duration)

**Debug Logging Middleware:**

```python
# middleware/debug_logging_middleware.py

from langchain.agents.middleware import BaseMiddleware
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import time
import traceback

class DebugLoggingMiddleware(BaseMiddleware):
    """
    Comprehensive debug logging middleware.

    Captures all technical details of agent execution and stores in database.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self._execution_log_id: Optional[UUID] = None
        self._start_time: Optional[float] = None
        self._tool_calls: list = []
        self._middleware_timings: Dict[str, float] = {}

    async def before_agent(self, state) -> dict:
        """Create execution log entry at start."""
        from uuid import uuid4

        self._execution_log_id = uuid4()
        self._start_time = time.time()
        self._tool_calls = []

        # Extract configuration from state
        user_settings = state.get("user_settings", {})

        # Create initial log entry
        log_entry = {
            "id": self._execution_log_id,
            "conversation_id": state.get("conversation_id"),
            "user_id": state.get("user_id"),
            "session_id": state.get("session_id"),
            "started_at": datetime.utcnow(),
            "task_id": state.get("task_id"),
            "workflow_mode": state.get("workflow_mode", "workbench"),
            "execution_status": "running",
            "model_provider": user_settings.get("provider", "unknown"),
            "model_name": user_settings.get("model", "unknown"),
            "temperature": user_settings.get("temperature"),
            "max_tokens": user_settings.get("max_tokens"),
            "user_message": state.get("user_message", ""),
            "tools_available": [tool.name for tool in state.get("tools", [])],
            "tools_called": [],
            "tool_call_count": 0,
            "middleware_chain": [],
            "step_count": 0,
        }

        await self.db.create_execution_log(log_entry)

        return state

    async def before_tool(self, tool_name: str, arguments: dict) -> dict:
        """Log tool call start."""
        tool_call = {
            "execution_log_id": self._execution_log_id,
            "tool_name": tool_name,
            "tool_type": "langchain",  # Detect from tool instance
            "call_index": len(self._tool_calls),
            "started_at": datetime.utcnow(),
            "arguments": arguments,
            "status": "running"
        }

        self._tool_calls.append(tool_call)

        return {"tool_name": tool_name, "arguments": arguments}

    async def after_tool(
        self,
        tool_name: str,
        result: Any,
        error: Optional[Exception] = None
    ) -> dict:
        """Log tool call completion."""
        if not self._tool_calls:
            return {}

        # Find the most recent call for this tool
        tool_call = self._tool_calls[-1]

        tool_call.update({
            "completed_at": datetime.utcnow(),
            "duration_ms": int((time.time() - tool_call["started_at"].timestamp()) * 1000),
            "result": result if not error else None,
            "status": "error" if error else "success",
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None
        })

        # Save tool call log
        await self.db.create_tool_call_log(tool_call)

        return {"result": result}

    async def after_agent(self, state) -> dict:
        """Complete execution log with final details."""
        if not self._execution_log_id:
            return state

        duration = time.time() - self._start_time if self._start_time else 0

        # Extract final state details
        structured_response = state.get("structured_response")
        execution_successful = state.get("execution_successful", False)
        error_message = state.get("error_message")

        # Calculate token counts (if available from structured_response)
        token_count_input = None
        token_count_output = None
        token_count_total = None

        if structured_response and hasattr(structured_response, "metadata"):
            metadata = structured_response.metadata or {}
            token_count_input = metadata.get("input_tokens")
            token_count_output = metadata.get("output_tokens")
            token_count_total = metadata.get("total_tokens")

        # Update execution log
        log_update = {
            "completed_at": datetime.utcnow(),
            "duration_ms": int(duration * 1000),
            "execution_status": "success" if execution_successful else "error",
            "agent_response": state.get("agent_response"),
            "structured_response": structured_response.dict() if structured_response else None,
            "tools_called": [
                {
                    "tool_name": tc["tool_name"],
                    "duration_ms": tc.get("duration_ms"),
                    "status": tc.get("status")
                }
                for tc in self._tool_calls
            ],
            "tool_call_count": len(self._tool_calls),
            "middleware_timings": self._middleware_timings,
            "step_count": state.get("steps_executed", 0),
            "token_count_input": token_count_input,
            "token_count_output": token_count_output,
            "token_count_total": token_count_total,
            "error_message": error_message,
            "context_sources": state.get("active_contexts", []),
            "state_snapshot": {
                "conversation_history_length": len(state.get("conversation_history", [])),
                "context_data_keys": list(state.get("context_data", {}).keys())
            }
        }

        await self.db.update_execution_log(self._execution_log_id, log_update)

        return state

    async def on_error(self, error: Exception, state) -> dict:
        """Log error details."""
        if not self._execution_log_id:
            return state

        error_update = {
            "execution_status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_stack_trace": traceback.format_exc(),
            "completed_at": datetime.utcnow(),
            "duration_ms": int((time.time() - self._start_time) * 1000) if self._start_time else None
        }

        await self.db.update_execution_log(self._execution_log_id, error_update)

        return state
```

**Database Service Methods:**

```python
# database/backends/sqlite.py (add these methods)

class SQLiteBackend(DatabaseBackend):

    async def create_execution_log(self, log_data: Dict[str, Any]) -> UUID:
        """Create agent execution log entry."""
        async with self.async_session() as session:
            log = AgentExecutionLogModel(**log_data)
            session.add(log)
            await session.commit()
            return log.id

    async def update_execution_log(
        self,
        log_id: UUID,
        updates: Dict[str, Any]
    ) -> None:
        """Update execution log with completion details."""
        async with self.async_session() as session:
            result = await session.execute(
                select(AgentExecutionLogModel).where(
                    AgentExecutionLogModel.id == log_id
                )
            )
            log = result.scalar_one_or_none()

            if log:
                for key, value in updates.items():
                    setattr(log, key, value)
                await session.commit()

    async def create_tool_call_log(self, tool_call_data: Dict[str, Any]) -> UUID:
        """Create tool call log entry."""
        async with self.async_session() as session:
            tool_log = ToolCallLogModel(**tool_call_data)
            session.add(tool_log)
            await session.commit()
            return tool_log.id

    async def get_execution_logs(
        self,
        user_id: Optional[UUID] = None,
        conversation_id: Optional[UUID] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query execution logs with filters."""
        async with self.async_session() as session:
            query = select(AgentExecutionLogModel)

            if user_id:
                query = query.where(AgentExecutionLogModel.user_id == user_id)
            if conversation_id:
                query = query.where(AgentExecutionLogModel.conversation_id == conversation_id)
            if status:
                query = query.where(AgentExecutionLogModel.execution_status == status)

            query = query.order_by(AgentExecutionLogModel.started_at.desc()).limit(limit)

            result = await session.execute(query)
            logs = result.scalars().all()

            return [self._serialize_log(log) for log in logs]
```

**What Gets Logged:**

1. **Execution Metadata:**
   - Task ID (agent's working memory thread)
   - Start/end timestamps
   - Duration in milliseconds
   - Execution status (success/error/timeout)

2. **Agent Configuration:**
   - Model provider and name
   - Temperature, max_tokens
   - Workflow mode

3. **Input/Output:**
   - User message (full text)
   - Agent response (full text)
   - Structured response (Pydantic model as JSON)

4. **Tool Usage:**
   - Tools available
   - Tools called with arguments and results
   - Tool call timing and status
   - Error details for failed tools

5. **Middleware Tracking:**
   - Middleware chain executed
   - Timing for each middleware
   - PII redaction flag
   - Summarization trigger flag

6. **Performance Metrics:**
   - Step count
   - Token counts (input/output/total)
   - Estimated cost
   - Context size

7. **Error Information:**
   - Exception type
   - Error message
   - Full stack trace
   - Retry count

8. **State Snapshot:**
   - Context sources used
   - Conversation history length
   - Context data keys

**Usage Queries:**

```python
# Get all errors for debugging
error_logs = await db.get_execution_logs(status="error", limit=100)

# Get specific user's execution history
user_logs = await db.get_execution_logs(user_id=user_id, limit=50)

# Get logs for specific conversation
conv_logs = await db.get_execution_logs(conversation_id=conv_id)

# Analyze tool performance
tool_stats = await db.get_tool_call_statistics(tool_name="content_retriever")
```

**Files to Create:**
- `models/database.py` (add AgentExecutionLogModel, ToolCallLogModel)
- `middleware/debug_logging_middleware.py`

**Files to Modify:**
- `database/backends/sqlite.py` (add execution log methods)
- `database/backends/hub.py` (add execution log methods)
- `services/agent_service.py` (add DebugLoggingMiddleware to chain)

**Phase 2.8 Checklist Addition:**
- [ ] AgentExecutionLogModel and ToolCallLogModel created
- [ ] DebugLoggingMiddleware implemented
- [ ] Database methods for execution logs added
- [ ] All technical details captured (tools, errors, performance)
- [ ] Stack traces stored for error debugging
- [ ] Query methods for analytics working
- [ ] Logs viewable in debug UI (optional)

---

**Error Handling:**

```python
# ui/components/file_handler_ui.py

import gradio as gr
import os
from pathlib import Path
from typing import List, Optional, Tuple
from uuid import UUID

class FileHandlerUI:
    """
    Gradio file upload/download components.

    Based on showcase patterns + Gradio best practices.
    """

    @staticmethod
    def create_upload_component() -> gr.File:
        """Create file upload component with multi-file support."""

        return gr.File(
            label="Upload Files",
            file_count="multiple",
            file_types=[
                ".pdf", ".docx", ".doc", ".txt", ".md",  # Documents
                ".csv", ".xlsx", ".xls",                  # Data
                ".png", ".jpg", ".jpeg", ".gif",          # Images
                ".mp3", ".mp4", ".wav", ".m4a",          # Media
                ".json", ".xml", ".yaml", ".yml",         # Structured
                ".py", ".js", ".sql", ".html"            # Code
            ],
            type="filepath"  # Returns file path instead of binary
        )

    @staticmethod
    def create_download_button(
        file_path: str,
        filename: str,
        visible: bool = True
    ) -> gr.DownloadButton:
        """Create download button for generated files."""

        return gr.DownloadButton(
            label=f"Download {filename}",
            value=file_path,
            visible=visible,
            variant="primary"
        )

    @staticmethod
    async def handle_file_upload(
        files: List[str],
        conversation_id: UUID,
        agent_service
    ) -> Tuple[str, List[dict]]:
        """
        Process uploaded files.

        Returns:
            - Status message
            - File metadata list
        """

        if not files:
            return "No files uploaded", []

        file_metadata = []
        processed_count = 0

        for file_path in files:
            try:
                # Analyze file
                from utils.file_handler import FileHandler
                metadata = FileHandler.analyze_file_metadata(file_path)

                # Store in database
                from services.document_processor import DocumentProcessor
                processor = DocumentProcessor()
                doc_id = await processor.process_file(
                    file_path=file_path,
                    conversation_id=conversation_id
                )

                metadata["document_id"] = str(doc_id)
                metadata["status"] = "processed"
                file_metadata.append(metadata)
                processed_count += 1

            except Exception as e:
                file_metadata.append({
                    "file_path": file_path,
                    "status": "error",
                    "error": str(e)
                })

        status_msg = f"✅ Processed {processed_count}/{len(files)} files"
        return status_msg, file_metadata

    @staticmethod
    def format_file_metadata(metadata_list: List[dict]) -> str:
        """Format file metadata for display."""

        if not metadata_list:
            return "No files uploaded"

        output = "**Uploaded Files:**\n\n"
        for meta in metadata_list:
            status_emoji = "✅" if meta.get("status") == "processed" else "❌"
            filename = os.path.basename(meta.get("file_path", "unknown"))
            category = meta.get("category", "unknown")
            size = meta.get("file_size", 0)
            size_mb = size / 1_000_000 if size > 0 else 0

            output += f"{status_emoji} **{filename}**\n"
            output += f"   - Type: {category}\n"
            output += f"   - Size: {size_mb:.2f} MB\n"

            if meta.get("recommended_tools"):
                tools = ", ".join(meta["recommended_tools"])
                output += f"   - Recommended tools: {tools}\n"

            if meta.get("error"):
                output += f"   - Error: {meta['error']}\n"

            output += "\n"

        return output


class DownloadManager:
    """Manage file downloads and exports."""

    @staticmethod
    async def export_conversation_history(
        conversation_id: UUID,
        format: str = "json"
    ) -> str:
        """
        Export conversation history to file.

        Formats: json, csv, txt, pdf
        """

        from services.conversation_service import ConversationService
        service = ConversationService()

        messages = service.get_messages(conversation_id)

        import tempfile
        temp_dir = tempfile.gettempdir()
        filename = f"conversation_{conversation_id}_{format}"
        file_path = os.path.join(temp_dir, filename)

        if format == "json":
            import json
            with open(file_path, 'w') as f:
                json.dump([msg.dict() for msg in messages], f, indent=2)

        elif format == "csv":
            import csv
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["role", "content", "timestamp"])
                writer.writeheader()
                for msg in messages:
                    writer.writerow({
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.created_at
                    })

        elif format == "txt":
            with open(file_path, 'w') as f:
                for msg in messages:
                    f.write(f"{msg.role.upper()}: {msg.content}\n\n")

        elif format == "pdf":
            # Use reportlab for PDF generation
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            c = canvas.Canvas(file_path, pagesize=letter)
            y = 750

            for msg in messages:
                c.drawString(50, y, f"{msg.role.upper()}:")
                y -= 20
                # Wrap text
                text = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                c.drawString(70, y, text)
                y -= 40

                if y < 100:  # New page
                    c.showPage()
                    y = 750

            c.save()

        return file_path

    @staticmethod
    async def export_analysis_results(
        data: dict,
        filename: str,
        format: str = "json"
    ) -> str:
        """Export analysis results to file."""

        import tempfile
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, f"{filename}.{format}")

        if format == "json":
            import json
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)

        elif format == "csv":
            import csv
            import pandas as pd

            # Convert dict to DataFrame
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)

        return file_path
```

**Updated Gradio Interface:**

```python
# ui/app.py (workbench mode updates)

import gradio as gr
from ui.components.file_handler_ui import FileHandlerUI, DownloadManager
from services.agent_service import AgentService
from uuid import UUID

def create_workbench_app() -> gr.Blocks:
    """Create workbench interface with file upload/download support."""

    with gr.Blocks(title="Agent Workbench") as app:
        gr.Markdown("# Agent Workbench")

        # State
        conversation_id_state = gr.State(value=None)

        with gr.Row():
            # Left column: Chat
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    height=500,
                    show_copy_button=True
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        label="Message",
                        placeholder="Ask a question or upload files...",
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

                # File upload
                file_upload = FileHandlerUI.create_upload_component()
                file_status = gr.Markdown("No files uploaded")

            # Right column: Downloads & Tools
            with gr.Column(scale=1):
                gr.Markdown("### Downloads")

                # Export conversation
                with gr.Group():
                    gr.Markdown("**Export Conversation**")
                    export_format = gr.Radio(
                        choices=["json", "csv", "txt", "pdf"],
                        value="json",
                        label="Format"
                    )
                    export_btn = gr.Button("Export Conversation")
                    download_conversation = gr.File(
                        label="Download",
                        visible=False
                    )

                # Agent-generated files
                gr.Markdown("**Generated Files**")
                generated_files_list = gr.Markdown("No files generated yet")
                generated_file_download = gr.File(
                    label="Download Generated File",
                    visible=False
                )

        # Event handlers

        async def handle_message(message, history, conv_id, files):
            """Handle user message with optional file context."""

            # Process files first if uploaded
            file_context = ""
            if files:
                status, metadata = await FileHandlerUI.handle_file_upload(
                    files, conv_id, agent_service
                )
                file_context = FileHandlerUI.format_file_metadata(metadata)

            # Send to agent
            agent_service = AgentService()

            # Include file context in message
            full_message = message
            if file_context:
                full_message = f"{message}\n\n{file_context}"

            response = await agent_service.run(
                conversation_id=conv_id,
                user_message=full_message
            )

            # Update history
            history.append((message, response))

            return history, "", None  # Clear input and files

        async def handle_export(conv_id, format):
            """Export conversation history."""

            file_path = await DownloadManager.export_conversation_history(
                conversation_id=conv_id,
                format=format
            )

            return gr.File(value=file_path, visible=True)

        # Wire events
        send_btn.click(
            fn=handle_message,
            inputs=[msg_input, chatbot, conversation_id_state, file_upload],
            outputs=[chatbot, msg_input, file_upload]
        )

        export_btn.click(
            fn=handle_export,
            inputs=[conversation_id_state, export_format],
            outputs=[download_conversation]
        )

        # File upload triggers processing
        file_upload.change(
            fn=lambda files: FileHandlerUI.format_file_metadata(
                [{"file_path": f, "status": "uploaded"} for f in (files or [])]
            ),
            inputs=[file_upload],
            outputs=[file_status]
        )

    return app
```

**Human-in-the-Loop Approval Dialog:**

```python
# ui/components/approval_dialog.py

import gradio as gr
from typing import Dict, Any, Literal

class ApprovalDialog:
    """
    Human approval dialog for sensitive operations.

    Integrates with HumanInTheLoopMiddleware.
    """

    @staticmethod
    def create_approval_interface() -> gr.Blocks:
        """Create approval dialog component."""

        with gr.Blocks() as approval_ui:
            gr.Markdown("## ⚠️ Approval Required")

            operation_details = gr.Markdown("Waiting for operation...")

            with gr.Row():
                approve_btn = gr.Button("✅ Approve", variant="primary")
                edit_btn = gr.Button("✏️ Edit")
                reject_btn = gr.Button("❌ Reject", variant="stop")

            # Edit interface (hidden by default)
            with gr.Group(visible=False) as edit_group:
                edit_input = gr.Textbox(
                    label="Edit Operation Parameters",
                    lines=3
                )
                submit_edit_btn = gr.Button("Submit Edit")

            approval_result = gr.State(value=None)

        return approval_ui, (approve_btn, edit_btn, reject_btn, edit_input, submit_edit_btn)

    @staticmethod
    async def show_approval_request(
        operation: str,
        parameters: Dict[str, Any]
    ) -> Literal["approve", "edit", "reject"]:
        """
        Show approval request and wait for user response.

        This is called by HumanInTheLoopMiddleware.
        """

        # Format operation details
        details = f"**Operation:** {operation}\n\n"
        details += "**Parameters:**\n"
        for key, value in parameters.items():
            details += f"- {key}: {value}\n"

        # Show dialog and wait for response
        # Implementation depends on Gradio queue system
        # Return user choice

        return "approve"  # Placeholder
```

**Files to Create:**
- `ui/components/file_handler_ui.py` (file upload/download)
- `ui/components/approval_dialog.py` (human approval)
- `api/routes/approvals.py` (approval API)
- `api/routes/downloads.py` (download API)
- `services/document_processor.py` (file processing)

**Files to Modify:**
- `ui/app.py` (add file components)
- `ui/seo_coach_app.py` (add file upload for documents)
- `services/agent_service.py` (integrate approval flow)

**Dependencies:**

```toml
# Add to pyproject.toml
reportlab = "^4.0.0"  # PDF generation for exports
pandas = "^2.0.0"     # CSV export
```

---

**Note:** Old Phase 2.6 and 2.7 sections removed - content redistributed across new phases

## Critical: LangGraph Workflow for User-System Interaction

**⚠️ CRUCIAL ARCHITECTURAL DECISION ⚠️**

Phase 2 requires a **standard LangGraph workflow** that orchestrates interactions between:
- User (via Gradio UI)
- System (file processing, context loading)
- Agent (single LangChain v1 `create_agent()`)

**Pattern Source:** `docs/showcases/agent_logic.py` - GAIAAgent's LangGraph workflow

**Key Insight:** The showcase uses LangGraph StateGraph to coordinate:
1. Question reading + file handling
2. Complexity assessment (route to simple vs complex)
3. Agent execution
4. Answer formatting

**Phase 2 Adaptation:** Same workflow pattern BUT with **single agent** (no coordinator, no specialists).

### LangGraph Workflow Architecture

```python
# services/workflow_service.py

from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Optional, List, Dict, Any
from uuid import UUID

class WorkflowState(TypedDict):
    """
    State for user-system-agent workflow.

    Based on showcase GAIAState but adapted for Phase 2.
    """

    # User context
    conversation_id: UUID
    user_message: str
    mode: str  # "workbench" or "seo_coach"

    # File handling
    uploaded_files: Optional[List[str]]
    processed_documents: Optional[List[Dict]]
    file_context: Optional[str]

    # System processing
    steps: List[str]
    context_loaded: bool
    similar_examples: Optional[List[Dict]]

    # Agent execution
    agent_response: Optional[str]  # Human-readable message for display
    structured_response: Optional[AgentResponse]  # Full structured data (NEW)
    tool_calls: Optional[List[Dict]]
    execution_successful: bool

    # Output
    final_response: str
    error_message: Optional[str]


class WorkflowOrchestrator:
    """
    LangGraph workflow for Phase 2.

    Orchestrates: User → System → Agent → User

    Based on showcase pattern but simplified for single agent.
    """

    def __init__(
        self,
        db: AdaptiveDatabase,
        agent_service: AgentService,
        vector_store: VectorStoreService
    ):
        self.db = db
        self.agent_service = agent_service
        self.vector_store = vector_store
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow.

        Nodes:
        1. process_input - Handle files, load context
        2. prepare_agent_input - Format for agent
        3. execute_agent - Run LangChain v1 agent
        4. format_output - Format response for user

        Pattern from showcase: _build_workflow() → StateGraph with nodes
        """

        builder = StateGraph(WorkflowState)

        # Add nodes (showcase pattern: add_node for each step)
        builder.add_node("process_input", self._process_input_node)
        builder.add_node("prepare_agent_input", self._prepare_agent_input_node)
        builder.add_node("execute_agent", self._execute_agent_node)
        builder.add_node("format_output", self._format_output_node)

        # Add edges (showcase pattern: linear flow with conditional routing)
        builder.add_edge(START, "process_input")
        builder.add_edge("process_input", "prepare_agent_input")
        builder.add_edge("prepare_agent_input", "execute_agent")
        builder.add_edge("execute_agent", "format_output")
        builder.add_edge("format_output", END)

        return builder.compile()

    async def _process_input_node(self, state: WorkflowState) -> Dict:
        """
        Node 1: Process user input and files.

        Based on showcase: _read_question_node

        Responsibilities:
        1. Process uploaded files (if any)
        2. Load conversation context from DB
        3. Search similar examples (vector store)
        4. Prepare file context for agent
        """

        steps = state.get("steps", [])
        steps.append("Processing user input and files")

        # 1. Process uploaded files (showcase pattern: file handling)
        processed_documents = []
        file_context = ""

        if state.get("uploaded_files"):
            from services.document_processor import DocumentProcessor
            processor = DocumentProcessor()

            for file_path in state["uploaded_files"]:
                try:
                    doc_data = await processor.process_file(
                        file_path=file_path,
                        conversation_id=state["conversation_id"]
                    )
                    processed_documents.append(doc_data)

                    # Build context string
                    file_context += f"\nFile: {doc_data['filename']}\n"
                    file_context += f"Type: {doc_data['file_type']}\n"
                    file_context += f"Content preview: {doc_data['content_preview']}\n"

                except Exception as e:
                    steps.append(f"File processing error: {str(e)}")

        # 2. Load conversation history (showcase pattern: context loading)
        conversation_history = self.db.get_messages(state["conversation_id"])

        # 3. Search similar examples (showcase pattern: RAG retrieval)
        similar_examples = []
        try:
            similar_examples = await self.vector_store.search_similar(
                query=state["user_message"],
                conversation_id=str(state["conversation_id"]),
                limit=3
            )
        except Exception as e:
            steps.append(f"Vector search error: {str(e)}")

        return {
            "processed_documents": processed_documents,
            "file_context": file_context,
            "similar_examples": similar_examples,
            "context_loaded": True,
            "steps": steps
        }

    async def _prepare_agent_input_node(self, state: WorkflowState) -> Dict:
        """
        Node 2: Prepare input for agent.

        Formats context for single agent with:
        - User message
        - File context
        - Conversation history
        - Similar examples
        """

        steps = state.get("steps", [])
        steps.append("Preparing agent input")

        # Build context string (showcase pattern: structured context)
        context_parts = []

        # File context
        if state.get("file_context"):
            context_parts.append("FILES AVAILABLE:")
            context_parts.append(state["file_context"])

        # Similar examples
        if state.get("similar_examples"):
            context_parts.append("\nSIMILAR PAST INTERACTIONS:")
            for ex in state["similar_examples"][:3]:
                context_parts.append(f"- {ex.get('content', '')[:100]}...")

        # Mode-specific instructions
        if state["mode"] == "seo_coach":
            context_parts.append("\nMODE: SEO Coach (Dutch, business-friendly)")
        else:
            context_parts.append("\nMODE: Technical workbench")

        agent_context = "\n".join(context_parts)

        return {
            "agent_context": agent_context,
            "steps": steps
        }

    async def _execute_agent_node(self, state: WorkflowState) -> Dict:
        """
        Node 3: Execute single LangChain v1 agent.

        This is where the agent runs with:
        - Full middleware stack
        - MCP tools (including Firecrawl)
        - Document context
        - Structured output
        """

        steps = state.get("steps", [])
        steps.append("Executing agent")

        try:
            # Build full message with context
            full_message = state["user_message"]
            if state.get("agent_context"):
                full_message = f"{state['agent_context']}\n\nUSER QUESTION: {state['user_message']}"

            # Execute agent (single LangChain v1 create_agent with structured output)
            result = await self.agent_service.run(
                conversation_id=state["conversation_id"],
                user_message=full_message,
                mode=state["mode"]
            )

            # Extract structured response
            structured = result["structured_response"]

            return {
                "agent_response": structured.message,  # Human-readable for display
                "structured_response": structured,  # Full structured data
                "execution_successful": structured.status == "success",
                "steps": steps + ["Agent execution completed"]
            }

        except Exception as e:
            return {
                "agent_response": None,
                "execution_successful": False,
                "error_message": str(e),
                "steps": steps + [f"Agent execution failed: {str(e)}"]
            }

    async def _format_output_node(self, state: WorkflowState) -> Dict:
        """
        Node 4: Format output for user.

        Based on showcase: _format_answer_node

        Ensures response is properly formatted for UI.
        """

        steps = state.get("steps", [])
        steps.append("Formatting output")

        if state.get("execution_successful"):
            final_response = state["agent_response"]
        else:
            final_response = f"Error: {state.get('error_message', 'Unknown error')}"

        return {
            "final_response": final_response,
            "steps": steps + ["Output formatted"]
        }

    async def process_message(
        self,
        conversation_id: UUID,
        user_message: str,
        mode: str = "workbench",
        uploaded_files: Optional[List[str]] = None
    ) -> str:
        """
        Main entry point for workflow execution.

        Based on showcase: GAIAAgent.workflow.ainvoke()
        """

        # Create initial state
        initial_state: WorkflowState = {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "mode": mode,
            "uploaded_files": uploaded_files,
            "processed_documents": None,
            "file_context": None,
            "steps": [],
            "context_loaded": False,
            "similar_examples": None,
            "agent_response": None,
            "tool_calls": None,
            "execution_successful": False,
            "final_response": "",
            "error_message": None
        }

        # Execute workflow (showcase pattern: workflow.ainvoke)
        final_state = await self.workflow.ainvoke(initial_state)

        return final_state["final_response"]
```

### Integration with Agent Service

```python
# services/agent_service.py (updated)

from langchain.agents import create_agent

class AgentService:
    """
    Single LangChain v1 agent with full middleware.

    Called by WorkflowOrchestrator._execute_agent_node
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None

    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        """Initialize agent with MCP tools."""

        # Load MCP tools (including Firecrawl)
        mcp_client = MultiServerMCPClient(mcp_server_configs)
        tools = await mcp_client.get_tools()

        # Create STATELESS agent with full middleware stack
        # NOTE: Agent does NOT have checkpointer - state owned by LangGraph
        self.agent = create_agent(
            model=get_model(),  # OpenRouter
            tools=tools,  # MCP tools including Firecrawl
            middleware=[
                # Built-in LangChain v1 middleware
                PIIRedactionMiddleware(patterns=["email", "phone"]),
                SummarizationMiddleware(
                    model=get_model(),
                    max_tokens_before_summary=8000
                ),
                HumanInTheLoopMiddleware(
                    interrupt_on={
                        "send_email": ["approve", "edit", "reject"],
                        "delete_file": ["approve", "reject"],
                    }
                ),

                # Custom middleware (all use Phase 1 services)
                ContextMiddleware(db=self.db),
                MemoryMiddleware(db=self.db),
                ExecutionTrackingMiddleware(
                    context_service=ContextService(db=self.db)  # Phase 1 CONTEXT domain
                )
            ],
            structured_output=AgentResponse,  # Type-safe responses
            # NO checkpointer - agent is stateless
        )

    async def run(
        self,
        conversation_id: UUID,
        user_message: str,
        mode: str = "workbench"
    ) -> str:
        """
        Run agent (called by workflow).
        """

        config = {
            "configurable": {
                "thread_id": str(conversation_id),
                "mode": mode
            }
        }

        result = await self.agent.ainvoke(
            {"messages": [{"role": "user", "content": user_message}]},
            config=config
        )

        return result["messages"][-1]["content"]
```

### Workflow Integration Points

**1. API Endpoint:**
```python
# api/routes/chat_workflow.py

@router.post("/api/v1/chat/workflow")
async def chat_workflow(request: WorkflowRequest):
    """
    Main chat endpoint.

    User → LangGraph Workflow → Agent → User
    """

    orchestrator = WorkflowOrchestrator(
        db=app.adaptive_db,
        agent_service=app.agent_service,
        vector_store=app.vector_store
    )

    response = await orchestrator.process_message(
        conversation_id=request.conversation_id,
        user_message=request.message,
        mode=request.mode,
        uploaded_files=request.files
    )

    return {"response": response}
```

**2. Gradio UI Integration:**
```python
# ui/app.py

async def handle_message(message, files, history, conv_id):
    """Handle message from Gradio UI."""

    # Call workflow endpoint
    response = await orchestrator.process_message(
        conversation_id=conv_id,
        user_message=message,
        mode="workbench",
        uploaded_files=files
    )

    history.append((message, response))
    return history, "", None
```

### Key Differences from Showcase

| Showcase (Multi-Agent) | Phase 2 (Single Agent) |
|------------------------|------------------------|
| Multiple specialist agents (data_analyst, web_researcher, content_processor) | One agent with MCP tools |
| Coordinator delegates to specialists | Agent uses tools directly |
| SmolagAgents CodeAgent/ToolCallingAgent | LangChain v1 `create_agent()` |
| Manual state management via Bridge | **LangGraph StateGraph owns state, agent is stateless** |
| Custom tool wrapping | MCP adapters provide tools |

### What We Keep from Showcase

✅ **LangGraph StateGraph pattern** - Nodes for workflow steps
✅ **File handling pattern** - Process files before agent
✅ **Context building pattern** - Structure context for agent
✅ **Execution tracking** - ContextBridge → ExecutionTrackingMiddleware (uses Phase 1 ContextService)
✅ **Error handling** - Graceful fallbacks
✅ **Logging pattern** - Step-by-step logging

**Integration Note:** All Phase 2 features use Phase 1 domain objects (CONTEXT, MESSAGE, CONVERSATION, etc.) - no parallel structures.

### Implementation Priority

**Phase 2.1: Basic Workflow**
1. Create `WorkflowState` TypedDict
2. Implement `WorkflowOrchestrator` with 4 nodes
3. Connect to `AgentService`
4. Test end-to-end flow

**Phase 2.2: File Processing**
1. Add document processor integration
2. Build file context string
3. Pass to agent via message context

**Phase 2.3: Vector Store Integration**
1. Add similar example search
2. Include in agent context
3. Test relevance improvement

**Phase 2.4: Production Hardening**
1. Add error handling at each node
2. Implement retry logic
3. Add execution metrics
4. Test failure scenarios

### Files to Create

```
services/
├── workflow_service.py          # NEW: WorkflowOrchestrator
├── agent_service.py             # Updated: Single agent
├── document_processor.py        # NEW: File processing
└── vector_store_service.py      # NEW: Weaviate integration

middleware/
├── context_middleware.py        # Custom middleware
├── memory_middleware.py         # Custom middleware
└── execution_tracking_middleware.py  # NEW: From ContextBridge
```

---

## Key Patterns to Follow

### 1. One Agent Only

```python
# DO THIS - single agent
agent = create_agent(
    model=get_model(),  # OpenRouter
    tools=mcp_tools,
    middleware=[ContextMiddleware(), MemoryMiddleware()]
)

# NOT THIS - multi-agent, swarm, coordination, etc.
# Save that for Phase 3+
```

### 2. Use create_agent (LangChain v1) - NO Checkpointer

```python
# DO THIS - create STATELESS agent
from langchain.agents import create_agent

agent = create_agent(
    model=get_model(),
    tools=tools,
    middleware=[...],
    structured_output=AgentResponse,
    # NO checkpointer - agent is stateless
)

# NOT THIS - legacy patterns
from langgraph.prebuilt import create_react_agent  # Deprecated in v1

# NOT THIS - agent with checkpointer (conflicts with LangGraph)
agent = create_agent(
    model=get_model(),
    tools=tools,
    checkpointer=checkpointer  # ❌ Creates state conflict with LangGraph
)
```

### 3. LangGraph Owns State, Agent is Stateless (CRITICAL)

**⚠️ STATE MANAGEMENT RULE: LangGraph StateGraph is the SINGLE SOURCE OF TRUTH**

```python
# ✅ CORRECT: LangGraph owns state, agent is stateless
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver

# 1. Define LangGraph state
class WorkflowState(TypedDict):
    conversation_id: UUID
    user_message: str
    conversation_history: List[StandardMessage]
    agent_response: Optional[str]
    structured_response: Optional[AgentResponse]
    execution_successful: bool

# 2. Create STATELESS agent (NO checkpointer)
agent = create_agent(
    model=get_model(),
    tools=mcp_tools,
    middleware=[...],
    structured_output=AgentResponse,
    # NO checkpointer parameter - agent is stateless
)

# 3. Agent executes INSIDE LangGraph node
async def execute_agent_node(state: WorkflowState) -> dict:
    """LangGraph node that executes stateless agent."""
    # Extract FROM state
    history = state["conversation_history"]
    user_msg = state["user_message"]

    # Execute stateless agent
    result = await agent.ainvoke({
        "messages": [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ] + [{"role": "user", "content": user_msg}]
    })

    # Return TO state (LangGraph merges)
    return {
        "agent_response": result["structured_response"].message,
        "structured_response": result["structured_response"],
        "conversation_history": history + [
            StandardMessage(
                role="assistant",
                content=result["structured_response"].message
            )
        ],
        "execution_successful": True
    }

# 4. LangGraph owns checkpointer
builder = StateGraph(WorkflowState)
builder.add_node("execute_agent", execute_agent_node)
# ... add other nodes ...
workflow = builder.compile(
    checkpointer=MemorySaver()  # ← ONLY LangGraph has checkpointer
)

# ❌ WRONG: Don't give agent its own checkpointer
agent = create_agent(
    model=get_model(),
    tools=tools,
    checkpointer=MemorySaver()  # ❌ CONFLICT! Creates two state systems
)

# ❌ WRONG: Don't let agent manage conversation history
# Agent should receive history via parameters, not load from DB
```

**Why This Pattern:**
- **Single Source of Truth:** Only LangGraph manages state persistence
- **No Conflicts:** Agent doesn't compete with LangGraph for state ownership
- **Phase 1 Continuity:** Preserves Bridge pattern and state conversion
- **Testing:** Can test agent independently (stateless = easier to test)

**See:** `docs/phase2/state_management_critical_pattern.md` for complete pattern

### 4. Use Full Middleware Stack

```python
# DO THIS - complete middleware stack
middleware = [
    # Built-in LangChain v1 middleware
    PIIRedactionMiddleware(patterns=["email", "phone"]),
    SummarizationMiddleware(model=get_model(), max_tokens_before_summary=8000),
    HumanInTheLoopMiddleware(interrupt_on={"send_email": [...]}),

    # Custom middleware
    ContextMiddleware(db),    # Load history
    MemoryMiddleware(db),     # Save responses
    GuardrailsMiddleware(db)  # Optional: tool validation
]

# NOT THIS - incomplete middleware
middleware = [ContextMiddleware(db)]  # Missing PII, summarization, human-in-loop
```

### 5. Always Use Structured Outputs

```python
# DO THIS - structured outputs with Pydantic
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    status: Literal["success", "error", "pending"]
    message: str
    data: Optional[dict] = None

agent = create_agent(
    model=get_model(),
    tools=tools,
    middleware=[...],
    structured_output=AgentResponse  # Enforce type safety
)

result = await agent.ainvoke({"messages": [user_message]})
print(repr(result["structured_response"]))  # Debug with repr()

# NOT THIS - unstructured strings
# result = await agent.ainvoke(...)
# response = result["output"]  # Just a string - no validation
```

**Why:** Type safety, validation, debugging (`repr()`), API consistency

### 6. MCP Tools via Adapters Only

```python
# DO THIS
from langchain_mcp_adapters.client import MultiServerMCPClient
client = MultiServerMCPClient(configs)
tools = await client.get_tools()

# NOT THIS
# Don't reimplement MCP protocol
# Don't create custom tool wrappers
```

---

## Configuration

### Model Provider Configuration

**OpenRouter as Default (Recommended):**

```python
# config/model_config.py

import os
from langchain_openai import ChatOpenAI

def get_model(model_name: str = "anthropic/claude-sonnet-4-5"):
    """
    Get model via OpenRouter (unified API).

    Supports any OpenRouter model:
    - anthropic/claude-sonnet-4-5
    - openai/gpt-4-turbo
    - google/gemini-pro
    - meta-llama/llama-3-70b
    - mistralai/mistral-large
    """

    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        model=model_name,
        temperature=0.7,
    )

# Environment variables
# .env
OPENROUTER_API_KEY=sk-or-v1-...
DEFAULT_MODEL=anthropic/claude-sonnet-4-5
```

**Direct Provider Alternative:**

```python
# For direct Anthropic (with prompt caching)
from langchain_anthropic import ChatAnthropic

def get_anthropic_model(model_name: str = "claude-sonnet-4-5-20250929"):
    return ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=model_name,
        temperature=0.7,
    )
```

**Local Development:**

```python
# For Ollama (local testing, no API costs)
from langchain_ollama import ChatOllama

def get_ollama_model(model_name: str = "llama3.2"):
    return ChatOllama(
        model=model_name,
        base_url="http://localhost:11434",
    )
```

**Agent Service with OpenRouter:**

```python
# services/agent_service.py

from langchain.agents import create_agent
from config.model_config import get_model

class AgentService:
    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.model = get_model()  # OpenRouter by default

    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        """Initialize MCP servers and load tools."""

        # Connect to MCP servers
        self.mcp_client = MultiServerMCPClient(mcp_server_configs)
        self.tools = await self.mcp_client.get_tools()

        # Create STATELESS agent with OpenRouter model
        # NOTE: Agent does NOT have checkpointer - state owned by LangGraph
        self.agent = create_agent(
            model=self.model,  # OpenRouter
            tools=self.tools,
            middleware=[
                PIIRedactionMiddleware(patterns=["email", "phone"]),
                SummarizationMiddleware(
                    model=self.model,  # Same model for summarization
                    max_tokens_before_summary=8000
                ),
                ContextMiddleware(db=self.db),
                MemoryMiddleware(db=self.db),
            ],
            structured_output=AgentResponse,  # Type-safe responses
            # NO checkpointer - agent is stateless
        )
```

### MCP Server Configuration

```python
# config/mcp_servers.py

MCP_SERVERS = {
    "filesystem": {
        "command": "python",
        "args": ["mcp_servers/filesystem.py"],
        "transport": "stdio",
        "enabled": True
    },
    "web_search": {
        "url": "http://localhost:8001/mcp",
        "transport": "streamable_http",
        "headers": {
            "Authorization": f"Bearer {os.getenv('WEB_SEARCH_API_KEY')}"
        },
        "enabled": True
    },
    "code_executor": {
        "command": "python",
        "args": ["mcp_servers/code_executor.py"],
        "transport": "stdio",
        "enabled": False  # Disabled by default for security
    }
}
```

### Middleware Configuration

```python
# config/middleware.py

MIDDLEWARE_CONFIG = {
    "pii_redaction": {
        "enabled": True,
        "patterns": ["email", "phone", "ssn", "credit_card"]
    },
    "summarization": {
        "enabled": True,
        "max_tokens": 8000,
        "model": "anthropic:claude-sonnet-4-5-20250929"
    },
    "human_in_loop": {
        "enabled": True,
        "interrupt_on": {
            "send_email": ["approve", "edit", "reject"],
            "delete_file": ["approve", "reject"],
            "execute_code": ["approve", "edit", "reject"]
        }
    }
}
```

---

## Dependencies & v1.0 Transition Strategy

### Dependency Challenges

**LangChain v1.0 introduces a simplified namespace** - moving away from the sprawling package ecosystem. This creates potential dependency conflicts during transition.

#### New Simplified Structure

```
langchain (v1.0)           # Core package with create_agent, middleware
├── langchain-core         # Fundamental abstractions (included)
├── langchain-anthropic    # Anthropic integration
├── langchain-openai       # OpenAI integration
├── langchain-google-genai # Google integration
├── langchain-aws          # AWS Bedrock integration
├── langchain-ollama       # Ollama integration
└── langchain-mcp-adapters # MCP tool integration
```

**Legacy packages moved to `langchain-classic`** (features not in v1.0 core).

### Content Blocks: Provider Support

**Content Blocks** provide provider-agnostic access to LLM features in LangChain v1:

**Fully Supported:**
- **Anthropic (Claude)** - reasoning traces, citations, tool calls, prompt caching ✅
- **OpenAI** - tool calls, function calling, structured outputs ✅
- **Ollama** - tool calls, local model support (NEW in v1) ✅

**Partial Support:**
- **Google GenAI** - tool calls only ⚠️
- **AWS Bedrock** - depends on underlying model ⚠️

**What this means for Agent Workbench:**
- **Production:** Anthropic (Claude direct) - full content blocks + prompt caching
- **Production (unified API):** OpenRouter via `langchain-openai` - access to all models
- **Development/Testing:** Ollama - local models with content blocks
- **Future:** Google GenAI, AWS Bedrock as support expands

**OpenRouter Integration:**
OpenRouter provides a unified API for multiple providers (Anthropic, OpenAI, Google, Meta, etc.) using OpenAI-compatible endpoints. Use `langchain-openai` SDK:

```python
from langchain_openai import ChatOpenAI

# OpenRouter with any model
model = ChatOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    model="anthropic/claude-sonnet-4-5",  # or any OpenRouter model
)
```

**Benefits:**
- Single API key for multiple providers
- Fallback between models
- Cost optimization
- No vendor lock-in

### Recommended Dependency Strategy

```toml
[project.dependencies]
# Core (existing - keep)
fastapi = "^0.104.1"
gradio = "^4.12.0"
sqlalchemy = "^2.0.23"

# LangChain v1.0 - Use ALPHA/BETA versions initially
langchain = ">=1.0.0a0"  # Alpha: --pre flag required
langchain-core = "*"     # Auto-installed with langchain v1

# Structured outputs (already available via FastAPI)
# pydantic = "^2.0.0"    # Already included as FastAPI dependency - used for structured agent responses

# Provider packages
langchain-openai = "^0.3.0"      # PRIMARY: OpenRouter (unified API) + OpenAI direct
langchain-anthropic = "^0.3.0"   # Optional: Direct Anthropic (for prompt caching)
langchain-ollama = "^0.2.0"      # Dev/testing: Local models (full content blocks ✅)

# Future/optional providers
langchain-google-genai = "^0.2.0"  # Optional (partial support ⚠️)
langchain-aws = "^0.2.0"         # Optional (depends on model ⚠️)

# MCP Integration
langchain-mcp-adapters = "^0.1.0"

# LangGraph - keep for custom workflows if needed
langgraph = "^0.2.0"

# Web scraping & document processing
firecrawl-py = "^0.1.0"              # Firecrawl API client (web scraping)
beautifulsoup4 = "^4.12.0"           # Fallback HTML scraper
requests = "^2.31.0"                 # HTTP client
docling = "^1.0.0"                   # Advanced document parsing
pypdf = "^3.17.0"                    # PDF parsing (fallback)
python-docx = "^1.1.0"               # DOCX parsing
langchain-text-splitters = "^0.3.0"  # Text chunking

# Vector database (in-memory)
weaviate-client = "^4.9.0"           # Weaviate embedded vector DB
sentence-transformers = "^2.2.0"     # Local embeddings (all-MiniLM-L6-v2)

# UI enhancements (file upload/download)
reportlab = "^4.0.0"                 # PDF generation for exports
pandas = "^2.0.0"                    # CSV export and data handling

# Compatibility bridge (if needed during transition)
langchain-community = "^0.3.0"  # Only if legacy integrations required
```

### Environment Configuration

**Required Environment Variables:**

```bash
# .env

# Model Provider - OpenRouter (unified API)
OPENROUTER_API_KEY=sk-or-v1-xxxxx
DEFAULT_MODEL=anthropic/claude-sonnet-4-5

# Alternative: Direct Anthropic (for prompt caching)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# Local Development
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# MCP Servers
MCP_FILESYSTEM_ENABLED=true
MCP_WEB_SEARCH_ENABLED=true
MCP_WEB_SEARCH_API_KEY=xxxxx

# Feature Flags
ENABLE_LANGCHAIN_V1=false  # true to use Phase 2 agent
```

**Model Selection Strategy:**

```python
# config/model_config.py

import os
from typing import Literal

ModelProvider = Literal["openrouter", "anthropic", "ollama"]

def get_model_provider() -> ModelProvider:
    """Determine which provider to use based on environment."""

    # Check feature flags and available API keys
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"  # Default: unified API
    elif os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"  # Direct Anthropic
    elif os.getenv("OLLAMA_BASE_URL"):
        return "ollama"  # Local development
    else:
        raise ValueError("No model provider configured")

def get_model(model_name: str | None = None):
    """Get model based on provider configuration."""

    provider = get_model_provider()

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model=model_name or os.getenv("DEFAULT_MODEL", "anthropic/claude-sonnet-4-5"),
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=model_name or "claude-sonnet-4-5-20250929",
        )

    elif provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=model_name or os.getenv("OLLAMA_MODEL", "llama3.2"),
        )
```

### Installation Strategy

**Phase 1: Isolated Testing Environment**

```bash
# Create isolated test environment
python -m venv venv-langchain-v1
source venv-langchain-v1/bin/activate

# Install alpha release
pip install --pre -U langchain

# Install provider packages
pip install langchain-anthropic langchain-openai
pip install langchain-mcp-adapters

# Test compatibility
python -c "from langchain.agents import create_agent; print('v1.0 ready')"
```

**Phase 2: Gradual Integration**

```bash
# In main project, use feature flag
ENABLE_LANGCHAIN_V1=false make start-app  # Current Phase 1
ENABLE_LANGCHAIN_V1=true make start-app   # New Phase 2 agent
```

**Phase 3: Version Pinning After Stable Release**

```toml
# Once v1.0 reaches stable (GA)
[project.dependencies]
langchain = "~1.0.0"  # Pin to 1.0.x patch versions
langchain-anthropic = "~0.3.0"
```

### Dependency Conflict Resolution

**Potential conflicts:**

1. **`langchain` v0.3 vs v1.0**
   - Cannot coexist in same environment
   - Solution: Feature flag + conditional imports

2. **`langchain-core` version mismatch**
   - Different packages may require different core versions
   - Solution: Let pip/uv resolve, use compatible versions

3. **Legacy `langchain-community` imports**
   - Some packages still import from community
   - Solution: Keep `langchain-community` until all updated

### Migration Approach

```python
# services/agent_factory.py

import os
from typing import Any

def create_agent_service(db: AdaptiveDatabase) -> Any:
    """Create agent service - v1.0 or legacy based on feature flag."""

    use_v1 = os.getenv("ENABLE_LANGCHAIN_V1", "false").lower() == "true"

    if use_v1:
        # Import v1.0 agent
        from langchain.agents import create_agent
        from services.agent_service_v1 import AgentServiceV1
        return AgentServiceV1(db)
    else:
        # Import legacy (Phase 1)
        from services.consolidated_service import ConsolidatedWorkbenchService
        return ConsolidatedWorkbenchService(db)
```

### Testing Strategy for v1.0

```python
# tests/test_langchain_v1_compatibility.py

import pytest
import sys

# Skip if v1.0 not installed
try:
    from langchain.agents import create_agent
    LANGCHAIN_V1_AVAILABLE = True
except ImportError:
    LANGCHAIN_V1_AVAILABLE = False

@pytest.mark.skipif(not LANGCHAIN_V1_AVAILABLE, reason="LangChain v1.0 not installed")
async def test_v1_agent_creation():
    """Test agent creation with v1.0 API."""
    from langchain.agents import create_agent

    agent = create_agent(
        model="anthropic:claude-sonnet-4-5-20250929",
        tools=[],
        middleware=[]
    )

    assert agent is not None

@pytest.mark.skipif(not LANGCHAIN_V1_AVAILABLE, reason="LangChain v1.0 not installed")
async def test_v1_content_blocks():
    """Test content blocks with Anthropic provider."""
    # Test reasoning traces, citations, etc.
    pass
```

### Fallback Strategy

**If v1.0 causes issues:**

```python
# Keep Phase 1 working while developing Phase 2
# Phase 1: Current StateGraph + LangGraph (stable)
# Phase 2: v1.0 create_agent + middleware (experimental)

# Both run in parallel during transition
# Remove Phase 1 only after Phase 2 fully validated
```

### Content Blocks Usage Example

```python
# Only use content blocks with supported providers

from langchain.agents import create_agent

agent = create_agent(
    model="anthropic:claude-sonnet-4-5-20250929",  # Full content blocks support ✅
    tools=tools,
    middleware=[]
)

result = await agent.ainvoke({"messages": [user_message]})

# Access content blocks (Anthropic only)
if hasattr(result, "content_blocks"):
    for block in result.content_blocks:
        if block.type == "reasoning":
            # Claude's chain-of-thought reasoning
            print(f"Reasoning: {block.content}")
        elif block.type == "citation":
            # Source citations
            print(f"Source: {block.source}")
        elif block.type == "tool_call":
            # Tool invocation
            print(f"Tool: {block.tool_name}")
```

### Monitoring v1.0 Stability

**Watch for:**
- Breaking API changes in alpha/beta releases
- Middleware API stability
- Content blocks support expansion
- Performance regressions
- Memory leaks in long-running agents

**Create alerts:**
```python
# services/health_check.py

async def check_langchain_v1_health():
    """Monitor LangChain v1.0 stability."""

    metrics = {
        "version": langchain.__version__,
        "agent_creation_time": await measure_agent_creation(),
        "middleware_loaded": check_middleware_availability(),
        "content_blocks_support": check_content_blocks(),
    }

    return metrics
```

---

## Migration Strategy

### Phase 1 → Phase 2 Compatibility

**Keep existing endpoints working:**

```python
# api/routes/chat_workflow.py

@router.post("/api/v1/chat/workflow")
async def chat_workflow(request: WorkflowRequest):
    """Existing endpoint - route to new agent service."""

    # Use new agent service internally
    result = await agent_service.run(
        conversation_id=request.conversation_id,
        user_message=request.message
    )

    # Return in existing format
    return ConsolidatedWorkflowResponse(
        conversation_id=request.conversation_id,
        assistant_response=result,
        execution_successful=True
    )
```

**Gradual rollout:**
1. Add agent as optional backend (feature flag)
2. Test with workbench mode first
3. Enable for SEO coach mode
4. Make default after validation
5. Deprecate old StateGraph workflow

---

## Testing

### Unit Tests

```python
# tests/test_agent_service.py

async def test_agent_with_tools():
    """Test agent uses MCP tools correctly."""
    agent = await create_test_agent()
    result = await agent.run("Read file test.txt")
    assert "read_file" in result.tool_calls

async def test_pii_redaction():
    """Test PII middleware redacts sensitive data."""
    agent = await create_test_agent(
        middleware=[PIIRedactionMiddleware()]
    )
    result = await agent.run("My email is test@example.com")
    assert "test@example.com" not in result.logs
```

### Integration Tests

```python
# tests/integration/test_mcp_integration.py

async def test_mcp_server_connection():
    """Test connection to MCP servers."""
    mcp_service = MCPService()
    await mcp_service.initialize(test_configs)
    tools = await mcp_service.get_tools()
    assert len(tools) > 0
```

---

## References

### LangChain v1 Documentation
- What's new in v1: https://docs.langchain.com/oss/python/releases/langchain-v1
- Agent Middleware: https://blog.langchain.com/agent-middleware/
- PII Handling: https://blog.langchain.com/handling-pii-data-in-langchain/

### MCP Integration
- langchain-mcp-adapters: https://github.com/langchain-ai/langchain-mcp-adapters
- MCP Protocol: https://modelcontextprotocol.io/

### Internal Documentation
- Phase 1 Implementation: `docs/phase1/PHASE_1_IMPLEMENTATION.md`
- CLAUDE.md: Project instructions

---

## Release 0.2.0: Phase 2 Completion Checklist

**Release Version:** v0.2.0
**Milestone:** Complete Agent Implementation
**Release Date:** TBD (after Phase 2.8 completion)

### Pre-Release Requirements

**All 9 phases must be completed:**
- [x] Phase 2.0: User Authentication & Settings
- [ ] Phase 2.1: PWA App with User Settings
- [ ] Phase 2.2: Enhanced Gradio UI (with stubs)
- [ ] Phase 2.3: Basic Agent Service (minimal)
- [ ] Phase 2.4: ContentRetriever Tool (LangChain)
- [ ] Phase 2.5: Built-in Middleware
- [ ] Phase 2.6: Custom Middleware
- [ ] Phase 2.7: Firecrawl MCP Tool
- [ ] Phase 2.8: Production Hardening

### Release Validation

**Functional Tests:**
- [ ] User authentication works in HF Spaces
- [ ] PWA installs on mobile and desktop
- [ ] File upload UI works (with real processing in Phase 2.4)
- [ ] Agent responds to basic questions
- [ ] ContentRetriever processes local files
- [ ] Firecrawl scrapes web content
- [ ] Both workbench and SEO coach modes work
- [ ] Conversation history persists correctly
- [ ] Settings persist across sessions
- [ ] Tool calls logged and visible

**Quality Gates:**
- [ ] All Phase 2 tests pass (`make test`)
- [ ] Code quality passes (`make quality`)
- [ ] No critical bugs in issue tracker
- [ ] Documentation updated (CHANGELOG, README)
- [ ] Migration guide from v0.1.x to v0.2.0 written

**Performance Tests:**
- [ ] Agent responds within 5 seconds (95th percentile)
- [ ] File upload processes within 10 seconds for 1MB files
- [ ] Concurrent requests handled (10+ users)
- [ ] MCP connections stable (no leaks)
- [ ] Memory usage acceptable (<1GB per instance)

### Release Artifacts

**Version Bump:**
```bash
# Update version in pyproject.toml
version = "0.2.0"

# Create git tag
git tag -a v0.2.0 -m "Release 0.2.0: Agent Implementation Complete"
git push origin v0.2.0
```

**GitHub Release:**
- [ ] Create release on GitHub
- [ ] Include CHANGELOG for 0.2.0
- [ ] List breaking changes from 0.1.x
- [ ] Document new features (agent, tools, middleware)
- [ ] Include upgrade instructions

**HuggingFace Spaces Deployment:**
- [ ] Deploy workbench space (main branch)
- [ ] Deploy SEO coach space (main branch)
- [ ] Verify both spaces work with v0.2.0
- [ ] Update space README with new features

**Documentation Updates:**
- [ ] Update main README.md with Phase 2 features
- [ ] Create MIGRATION_0.1_TO_0.2.md guide
- [ ] Update CLAUDE.md with Phase 2 patterns
- [ ] Document new API endpoints
- [ ] Update architecture diagrams

### Post-Release

**Monitoring (First 24 Hours):**
- [ ] Monitor HF Spaces logs for errors
- [ ] Check user feedback on both spaces
- [ ] Monitor agent response times
- [ ] Check MCP connection stability
- [ ] Monitor database performance

**Communication:**
- [ ] Announce release on project channels
- [ ] Update project documentation site
- [ ] Notify key users of new features
- [ ] Share release notes

### Rollback Plan

**If critical issues found:**
1. Revert HF Spaces to v0.1.x
2. Document issues in GitHub
3. Create hotfix branch from v0.2.0
4. Fix and re-release as v0.2.1

**Known Limitations in v0.2.0:**
- LangChain v1.0 still in alpha/beta (API may change)
- Web scraping requires Firecrawl API key
- Document processing limited to supported formats
- No multi-agent support (Phase 3+)

---

## Next Steps

1. **Start Phase 2.1** - PWA App with User Settings
2. **Create feature branch** `feature/PHASE2-1-pwa-settings`
3. **Implement incrementally** following phase order
4. **Test each phase** before moving to next
5. **Track progress** using phase checklists
6. **Prepare for v0.2.0 release** after Phase 2.8

---

## Proven Patterns from Showcase Implementation

### Overview: GAIA Agent Architecture

The showcase implementation (`docs/showcases/`) demonstrates production-ready patterns that achieved excellent results. These patterns should be integrated into Phase 2.

**Key Success Factors (Adapted for Single Agent):**
1. **ContentRetrieverTool** - Universal content processing with intelligent fallback
2. **Weaviate In-Memory Vector DB** - Fast retrieval without external dependencies
3. **File Format Auto-Detection** - Extensionless file handling
4. **LangGraph Workflow** - Structured orchestration with state management
5. **Context Building** - Rich context preparation for agent

### 1. Content Retriever Tool Pattern (LangChain Tool - NOT MCP)

**Source:** `docs/showcases/content_retriever_tool.py`

**⚠️ IMPLEMENTATION TYPE: LangChain Tool**
- ContentRetrieverTool is a **LangChain tool** (not MCP)
- Firecrawl scraping is an **MCP tool** (separate)
- **Tool Priority: LangChain tools FIRST, then MCP tools**

**What It Does:**
- Universal content retrieval: local documents, files, images
- Intelligent fallback: Docling (advanced) → Basic processing (simple)
- Format auto-detection for extensionless files
- Query-based semantic filtering
- Multi-format support: PDF, DOCX, XLSX, HTML, images, text, CSV, JSON

**Does NOT Include:**
- ❌ Web scraping (use Firecrawl MCP tool instead)
- ❌ URL fetching (use Firecrawl MCP tool instead)

**Key Implementation Patterns:**

```python
# tools/content_retriever_tool.py (LangChain Tool)

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

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        super().__init__()
        self.model_name = model_name
        self._has_docling = self._check_docling_availability()

        if self._has_docling:
            self._init_docling_components()

    def _run(self, file_path: str, query: Optional[str] = None) -> str:
        """Sync execution (required by BaseTool)."""
        import asyncio
        return asyncio.run(self._arun(file_path, query))

    async def _arun(self, file_path: str, query: Optional[str] = None) -> str:
        """Async execution - main implementation."""
        # Validate it's a local file, not URL
        if file_path.startswith('http'):
            return "Error: This tool only handles local files. Use the scraping tool for web URLs."

        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"

        # Step 1: Prepare file access (detect format for extensionless files)
        processed_path = self._prepare_file_access(file_path)

        # Step 2: Try advanced processing with Docling
        if self._has_docling:
            try:
                return await self._process_with_docling(processed_path, query)
            except Exception as e:
                # Check if it's a format error
                if self._is_format_error(e):
                    # Fall back to basic processing
                    return await self._process_basic(file_path, query)
                raise

        # Step 3: Basic processing fallback
        return await self._process_basic(file_path, query)

    def _check_docling_availability(self) -> bool:
        """Check if docling and dependencies are available."""
        try:
            from docling.document_converter import DocumentConverter
            from docling.chunking import HierarchicalChunker
            from sentence_transformers import SentenceTransformer
            return True
        except ImportError:
            return False

    # ... implementation continues with _prepare_file_access,
    # _process_with_docling, _process_basic methods ...
```

**Combining LangChain Tool + MCP Tools in Agent:**

```python
# services/agent_service.py

from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from tools.content_retriever_tool import ContentRetrieverTool  # LangChain tool

class AgentService:
    async def initialize(self, mcp_server_configs: Dict[str, Dict]):
        # 1. Load MCP tools (Firecrawl for web scraping)
        self.mcp_client = MultiServerMCPClient(mcp_server_configs)
        mcp_tools = await self.mcp_client.get_tools()

        # 2. Create LangChain tools (ContentRetriever for local files)
        content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

        # 3. Combine: LangChain tools FIRST, then MCP tools
        all_tools = [
            content_retriever,  # LangChain tool (local files)
            *mcp_tools          # MCP tools (web scraping via Firecrawl)
        ]

        # 4. Create agent with combined tools
        self.agent = create_agent(
            model=get_model(),
            tools=all_tools,  # Both LangChain and MCP tools
            middleware=[...],
            structured_output=AgentResponse
        )
```

**Tool Separation:**

| Tool | Type | Purpose | Implementation |
|------|------|---------|----------------|
| ContentRetrieverTool | LangChain | Local file processing | `tools/content_retriever_tool.py` |
| Firecrawl scraping | MCP | Web scraping | MCP server via `langchain-mcp-adapters` |

**Why This Separation:**
1. **ContentRetriever** is local/stateless → Perfect for LangChain BaseTool
2. **Firecrawl** requires API key/external service → Better as MCP tool
3. **Priority:** LangChain tools load FIRST (faster, no external deps)
4. **Fallback:** If MCP fails, LangChain tools still work

### 2. Firecrawl MCP Tool (Web Scraping)

**⚠️ IMPLEMENTATION TYPE: MCP Tool**
- Firecrawl is implemented as an **MCP tool** (not LangChain)
- Accessed via `langchain-mcp-adapters`
- ContentRetrieverTool (LangChain) handles local files
- Firecrawl (MCP) handles web scraping

**What It Does:**
- Scrapes complex websites (JavaScript-rendered content)
- Extracts structured data from web pages
- Handles authentication and rate limiting
- Returns clean markdown content

**MCP Server Configuration:**

```python
# config/mcp_servers.py

MCP_SERVERS = {
    "firecrawl": {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-firecrawl"],
        "env": {
            "FIRECRAWL_API_KEY": os.getenv("FIRECRAWL_API_KEY")
        }
    }
}
```

**Tools Provided by Firecrawl MCP:**
- `scrape_url(url: str)` - Scrape single URL and return markdown
- `crawl_site(url: str, max_depth: int)` - Crawl entire site
- `extract_links(url: str)` - Get all links from page

**Usage in Agent:**

Agent automatically gets Firecrawl tools via MCP adapter - no manual tool definition needed. The agent description guides when to use each tool:
- Local file? → Use `content_retriever` (LangChain tool)
- Web URL? → Use `scrape_url` (Firecrawl MCP tool)

### 3. Weaviate In-Memory Vector Database

**Source:** Showcase uses embedded Weaviate for retrieval

**Why Weaviate:**
- In-memory mode: No external service required
- Fast semantic search
- Built-in hybrid search (dense + sparse)
- Production-ready Python client

**Phase 2 Integration:**

```python
# services/vector_store_service.py

import weaviate
from weaviate.embedded import EmbeddedOptions
from typing import List, Dict, Any

class VectorStoreService:
    """
    In-memory vector store using Weaviate embedded.

    No external database required - perfect for Phase 2.
    """

    def __init__(self):
        self.client = None
        self.collection = None

    async def initialize(self):
        """Initialize Weaviate in embedded mode."""

        # Start embedded Weaviate (runs in-memory)
        self.client = weaviate.Client(
            embedded_options=EmbeddedOptions(
                persistence_data_path="./data/weaviate",  # Optional persistence
                binary_path="./bin/weaviate",
            )
        )

        # Create collection for conversation context
        self._create_schema()

    def _create_schema(self):
        """Create Weaviate schema for conversation context."""

        schema = {
            "class": "ConversationContext",
            "description": "Conversation history and context for retrieval",
            "vectorizer": "text2vec-transformers",
            "moduleConfig": {
                "text2vec-transformers": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2",
                    "options": {
                        "waitForModel": True,
                        "useGPU": False,
                        "useCache": True
                    }
                }
            },
            "properties": [
                {
                    "name": "conversation_id",
                    "dataType": ["text"],
                    "description": "Conversation UUID"
                },
                {
                    "name": "content",
                    "dataType": ["text"],
                    "description": "Message content"
                },
                {
                    "name": "role",
                    "dataType": ["text"],
                    "description": "Message role: user, assistant, system"
                },
                {
                    "name": "timestamp",
                    "dataType": ["date"],
                    "description": "Message timestamp"
                },
                {
                    "name": "metadata",
                    "dataType": ["text"],
                    "description": "JSON metadata"
                }
            ]
        }

        # Create collection if doesn't exist
        if not self.client.schema.exists("ConversationContext"):
            self.client.schema.create_class(schema)

    async def add_message(
        self,
        conversation_id: str,
        content: str,
        role: str,
        metadata: Dict[str, Any] = None
    ):
        """Add message to vector store for retrieval."""

        import json
        from datetime import datetime

        self.client.data_object.create(
            class_name="ConversationContext",
            data_object={
                "conversation_id": conversation_id,
                "content": content,
                "role": role,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": json.dumps(metadata or {})
            }
        )

    async def search_similar(
        self,
        query: str,
        conversation_id: str = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar messages using hybrid search.

        Combines semantic (vector) + keyword (BM25) search.
        """

        where_filter = None
        if conversation_id:
            where_filter = {
                "path": ["conversation_id"],
                "operator": "Equal",
                "valueText": conversation_id
            }

        result = (
            self.client.query
            .get("ConversationContext", ["conversation_id", "content", "role", "timestamp", "metadata"])
            .with_hybrid(query=query, alpha=0.5)  # 0.5 = balanced vector + keyword
            .with_where(where_filter)
            .with_limit(limit)
            .do()
        )

        return result.get("data", {}).get("Get", {}).get("ConversationContext", [])
```

**Dependencies:**

```toml
# Add to pyproject.toml
weaviate-client = "^4.9.0"
sentence-transformers = "^2.2.0"  # For local embeddings
```

### 3. Context Bridge Pattern → Phase 1 ContextService Integration

**Source:** `docs/showcases/agent_logic.py` - ContextBridge class

**Key Features:**
- Execution tracking across workflow
- Step counter and timing
- Error tracking
- Tool call logging

**Phase 2 Adaptation - Uses Phase 1 CONTEXT Domain Object:**

**⚠️ CRITICAL:** Phase 1 already has `ContextService` (placeholder) and `WorkbenchState.context_data`. ExecutionTrackingMiddleware MUST use these, not create new structures.

```python
# middleware/execution_tracking_middleware.py

from langchain.agents.middleware import BaseMiddleware
from services.context_service import ContextService  # Phase 1 service
import time
from typing import Dict, Any
from uuid import UUID

class ExecutionTrackingMiddleware(BaseMiddleware):
    """
    Track agent execution metrics using Phase 1 ContextService.

    INTEGRATION: Stores metrics in WorkbenchState.context_data under "execution" key.
    """

    def __init__(self, context_service: ContextService):
        """
        Initialize with Phase 1 ContextService.

        Args:
            context_service: Phase 1 ContextService instance
        """
        self.context_service = context_service
        self._start_time = None
        self._step_counter = 0
        self._tool_calls = []

    async def before_agent(self, state):
        """Start execution tracking."""
        self._start_time = time.time()
        self._step_counter = 0
        self._tool_calls = []
        return state

    async def before_model(self, state):
        """Track step before each model call."""
        self._step_counter += 1
        return state

    async def after_agent(self, state):
        """
        Save execution metrics to Phase 1 context_data.

        INTEGRATION POINT: Uses WorkbenchState.context_data
        """
        duration = time.time() - self._start_time if self._start_time else 0

        # Build metrics dict
        execution_metrics = {
            "execution_time": duration,
            "steps_executed": self._step_counter,
            "tool_calls": len(self._tool_calls),
            "timestamp": time.time()
        }

        # Store in Phase 1 context_data structure
        conversation_id = state.get("conversation_id")
        if conversation_id:
            # Update context using Phase 1 ContextService
            await self.context_service.update_conversation_context(
                conversation_id=conversation_id,
                context_data={
                    "execution": execution_metrics  # Stored under "execution" key
                },
                sources=["execution_tracking_middleware"]
            )

        return state
```

**Phase 1 ContextService Implementation (Complete the Placeholder):**

```python
# services/context_service.py (Phase 1 - needs implementation)

from typing import Dict, Any, List, Optional
from uuid import UUID

class ContextService:
    """
    Context management service.

    Phase 1: Placeholder → Phase 2: Full implementation
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def update_conversation_context(
        self,
        conversation_id: UUID,
        context_data: Dict[str, Any],
        sources: List[str]
    ) -> None:
        """
        Update context for a conversation.

        Merges new context_data into existing WorkbenchState.context_data.
        """
        # Get current state
        current_state = await self.db.get_conversation_state(conversation_id)

        if not current_state:
            return

        # Merge context (Phase 1 merge strategy)
        existing_context = current_state.get("context_data", {})
        existing_context.update(context_data)

        # Update active_contexts sources
        active_contexts = current_state.get("active_contexts", [])
        for source in sources:
            if source not in active_contexts:
                active_contexts.append(source)

        # Save back to DB
        await self.db.update_conversation_state(
            conversation_id=conversation_id,
            updates={
                "context_data": existing_context,
                "active_contexts": active_contexts
            }
        )

    async def get_active_contexts(
        self,
        conversation_id: UUID
    ) -> List[str]:
        """Return list of active context sources."""
        state = await self.db.get_conversation_state(conversation_id)
        return state.get("active_contexts", []) if state else []

    async def build_context_prompt(
        self,
        context_data: Dict[str, Any]
    ) -> str:
        """
        Build context string for agent prompt.

        Formats context_data into human-readable string.
        """
        parts = []

        # Execution metrics
        if "execution" in context_data:
            exec_data = context_data["execution"]
            parts.append(f"Previous execution: {exec_data.get('steps_executed', 0)} steps, "
                        f"{exec_data.get('execution_time', 0):.2f}s")

        # User profile
        if "user_profile" in context_data:
            profile = context_data["user_profile"]
            parts.append(f"User timezone: {profile.get('timezone', 'unknown')}")

        # File context
        if "files" in context_data:
            parts.append(f"Files available: {len(context_data['files'])}")

        return "\n".join(parts) if parts else ""
```

### 5. File Handling Patterns

**Source:** Both showcase files demonstrate robust file handling

**Key Patterns:**

```python
# utils/file_handler.py

from pathlib import Path
from typing import Optional, Dict, Any
import os
import mimetypes

class FileHandler:
    """
    Robust file handling based on showcase patterns.
    """

    @staticmethod
    def get_best_file_path(
        file_name: Optional[str],
        file_path: Optional[str]
    ) -> Optional[str]:
        """
        Select best file path from multiple sources.

        Pattern from showcase: Prefer filename with extension.
        """

        # Prefer filename if it exists and has extension
        if file_name and file_name.strip() and os.path.exists(file_name):
            return file_name

        # Fallback to cache path
        if file_path and file_path.strip() and os.path.exists(file_path):
            return file_path

        # Return whatever we have
        return file_name or file_path

    @staticmethod
    def analyze_file_metadata(file_path: str) -> Dict[str, Any]:
        """
        Analyze file and recommend processing strategy.
        """

        if not os.path.exists(file_path):
            return {"error": "File not found"}

        path_obj = Path(file_path)
        extension = path_obj.suffix.lower()
        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'

        # Categorize
        if extension in ['.xlsx', '.csv', '.xls']:
            category = "data"
            recommended_tools = ["analyze_spreadsheet", "calculate_statistics"]
        elif extension in ['.pdf', '.docx', '.txt']:
            category = "document"
            recommended_tools = ["extract_text", "summarize_document"]
        elif extension in ['.png', '.jpg', '.jpeg']:
            category = "image"
            recommended_tools = ["analyze_image", "extract_text_ocr"]
        else:
            category = "unknown"
            recommended_tools = []

        return {
            "file_path": file_path,
            "extension": extension,
            "mime_type": mime_type,
            "category": category,
            "recommended_tools": recommended_tools,
            "file_size": os.path.getsize(file_path),
            "exists": True
        }
```

### Integration Checklist

**Phase 2.1: Content Retrieval**
- [ ] Implement `ContentRetrievalService` with Docling + fallback
- [ ] Add file format auto-detection
- [ ] Create MCP tool wrapper
- [ ] Test with extensionless files

**Phase 2.2: Vector Store**
- [ ] Initialize Weaviate embedded
- [ ] Create schema for conversation context
- [ ] Implement hybrid search
- [ ] Test semantic retrieval

**Phase 2.3: Tool Organization**
- [ ] Categorize MCP tools by domain
- [ ] Add tool recommendations to agent prompts
- [ ] Test tool selection accuracy

**Phase 2.4: Execution Tracking**
- [ ] Implement `ExecutionTrackingMiddleware`
- [ ] Add metrics to state
- [ ] Log execution data
- [ ] Test performance tracking

**Phase 2.5: File Handling**
- [ ] Implement `FileHandler` utility
- [ ] Add file metadata analysis
- [ ] Test with various file types
- [ ] Integrate with content retrieval

---

**Document Version:** 2.0 (Revised for LangChain v1)
**Last Updated:** 2025-10-12
**Author:** Claude Code (based on LangChain v1 release + showcase patterns)
