# AGENT-001: Basic Agent Service + Comprehensive Debug Logging

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: AGENT-001-v1-langchain-agent-logging
**Phase**: 2.3
**Dependencies**: UI-002 (user authentication and session management)

## Context

Create a minimal LangChain v1.0 agent service **without tools** but with **comprehensive debug logging from day 1**. This task establishes the foundation for agentic workflows while implementing production-ready observability infrastructure immediately.

**Critical Design Decision**: Debug logging is implemented in Phase 2.3 (not Phase 2.8) because we'll encounter numerous obstacles during development and need detailed execution logs to troubleshoot issues. Waiting until Phase 2.8 would make debugging Phase 2.3-2.7 extremely difficult.

**Agent Characteristics (Phase 2.3)**:
- Uses LangChain v1.0 `create_agent()` API
- NO tools yet (tools added in Phase 2.4 with MCP integration)
- Supports structured outputs via `AgentResponse` Pydantic model
- Uses `MemorySaver` checkpointer for agent working memory
- Wraps existing LLM calls in agent structure
- Streams responses to UI

**Debug Logging Characteristics**:
- Comprehensive 48-field `AgentExecutionLogModel` capturing all execution details
- Separate `ToolCallLogModel` for individual tool invocations (ready for Phase 2.4)
- 10 database indexes optimizing production queries
- `DebugLoggingMiddleware` with before/after/error hooks
- Captures full stack traces on errors
- Ready for analytics and monitoring from day 1

## Architecture Scope

### What's Included:

- **LangChain v1.0 Agent Service**:
  - `AgentService` class with `create_agent()` initialization
  - Empty tools list (no tool calling yet)
  - Structured output support with `AgentResponse` model
  - `MemorySaver` checkpointer for conversation memory
  - Streaming response support
  - Integration with existing `WorkbenchState` and `ConversationState`

- **Comprehensive Debug Logging**:
  - `AgentExecutionLogModel` (48 fields) - Complete execution metadata
  - `ToolCallLogModel` - Individual tool call details (ready for Phase 2.4)
  - 10 database indexes for production query optimization
  - `DebugLoggingMiddleware` - Before/after/error hooks
  - Full stack trace capture on errors
  - `AnalyticsService` - Optimized query methods using indexes

- **Database Integration**:
  - Execution log storage methods in `SQLiteBackend` and `HubBackend`
  - Migration for new tables and indexes
  - Cascade delete on conversation deletion
  - Foreign key relationships to `conversations`, `users`, `user_sessions`

- **Workflow Integration**:
  - Update `ConsolidatedWorkbenchService` to use `AgentService`
  - Maintain existing workflow endpoints (`POST /api/v1/chat/workflow`)
  - Preserve backward compatibility with Phase 1 behavior

- **LangChain v1.0 API Contract Testing**:
  - Contract tests ensuring `create_agent()` API stability
  - Version pinning for production reliability
  - Deprecation warnings monitoring

### What's Explicitly Excluded:

- Tool integration (Phase 2.4 - MCP adapters and tool registry)
- Multi-agent coordination (Phase 2.6)
- Agent memory and learning beyond checkpointer (Phase 2.7)
- PII redaction middleware (Phase 2.5)
- Conversation summarization (Phase 2.5)
- Production error handling and retries (Phase 2.8)
- Rate limiting (Phase 2.8)
- Health checks (Phase 2.8)
- Cost estimation and token counting beyond basic tracking (Phase 2.8)
- UI components for debug log viewing (future phase)

## Architectural Decisions

### 1. LangChain v1.0 Agent with NO Tools

**Core Approach**: Create minimal agent structure to establish workflow patterns before adding tool complexity.

```python
# services/agent_service.py

from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from typing import Dict, Any, List
from models.agent_models import AgentResponse
from middleware.debug_logging_middleware import DebugLoggingMiddleware

class AgentService:
    """Minimal agent service with comprehensive debug logging."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.checkpointer = MemorySaver()  # Agent's working memory

    async def initialize(self, model_config: ModelConfig):
        """Initialize agent WITHOUT tools but WITH debug logging."""

        # Get LangChain model (reuse existing ChatService logic)
        llm = self._create_langchain_model(model_config)

        # Create agent with NO tools but WITH debug logging middleware
        self.agent = create_agent(
            model=llm,
            tools=[],  # ← NO TOOLS YET (Phase 2.4)
            middleware=[
                DebugLoggingMiddleware(db=self.db)  # ← DEBUG LOGGING FROM START
            ],
            structured_output=AgentResponse,  # Type-safe responses
            checkpointer=self.checkpointer     # Conversation memory
        )

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        conversation_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Execute agent with debug logging."""

        config = {
            "configurable": {
                "thread_id": task_id,  # Agent's working memory identifier
                "conversation_id": conversation_id,
                "user_id": user_id
            }
        }

        try:
            # Agent execution with automatic debug logging via middleware
            result = await self.agent.ainvoke(
                {"messages": messages, "config": user_settings},
                config=config
            )
            return result

        except Exception as e:
            # Debug logging middleware captures stack trace automatically
            raise

    async def stream(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        conversation_id: UUID,
        user_id: UUID
    ) -> AsyncGenerator[str, None]:
        """Stream agent responses with debug logging."""

        config = {
            "configurable": {
                "thread_id": task_id,
                "conversation_id": conversation_id,
                "user_id": user_id
            }
        }

        try:
            async for chunk in self.agent.astream(
                {"messages": messages, "config": user_settings},
                config=config
            ):
                yield chunk

        except Exception as e:
            # Debug logging middleware captures error details
            raise
```

**Why No Tools Yet**:
- Simplifies initial agent integration
- Establishes middleware patterns before tool complexity
- Allows testing structured output and checkpointer in isolation
- Debug logging infrastructure ready when tools added in Phase 2.4

### 2. Comprehensive Debug Logging from Day 1

**Database Schema**: 48-field execution log capturing everything

```python
# models/database.py

from sqlalchemy import ForeignKey, JSON, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class AgentExecutionLogModel(Base):
    """
    Comprehensive debug log for agent executions.

    Stores technical details for troubleshooting, analytics, and error tracking.
    Designed for production debugging and observability.
    """
    __tablename__ = "agent_execution_logs"

    # ==================== PRIMARY IDENTIFICATION ====================

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"),
        index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    session_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("user_sessions.id", ondelete="SET NULL")
    )

    # ==================== TIMING ====================

    started_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        index=True
    )
    completed_at: Mapped[Optional[datetime]]
    duration_ms: Mapped[Optional[int]]  # Milliseconds

    # ==================== EXECUTION DETAILS ====================

    task_id: Mapped[str] = mapped_column(index=True)  # Agent's thread_id
    workflow_mode: Mapped[str]  # "workbench" or "seo_coach"
    execution_status: Mapped[str]  # "success", "error", "timeout", "cancelled"

    # ==================== AGENT CONFIGURATION ====================

    model_provider: Mapped[str]  # "openrouter", "anthropic", etc.
    model_name: Mapped[str]  # "claude-sonnet-4-5", etc.
    temperature: Mapped[Optional[float]]
    max_tokens: Mapped[Optional[int]]

    # ==================== INPUT/OUTPUT ====================

    user_message: Mapped[Text]
    agent_response: Mapped[Optional[Text]]
    structured_response: Mapped[Optional[JSON]]  # AgentResponse as JSON

    # ==================== TOOL USAGE ====================

    tools_available: Mapped[JSON]  # List of tool names
    tools_called: Mapped[JSON]  # List of {tool_name, arguments, result, duration_ms}
    tool_call_count: Mapped[int] = mapped_column(default=0)

    # ==================== MIDDLEWARE TRACKING ====================

    middleware_chain: Mapped[JSON]  # List of middleware names executed
    middleware_timings: Mapped[JSON]  # {middleware_name: duration_ms}
    pii_redacted: Mapped[bool] = mapped_column(default=False)
    summarization_triggered: Mapped[bool] = mapped_column(default=False)

    # ==================== PERFORMANCE METRICS ====================

    step_count: Mapped[int] = mapped_column(default=0)
    token_count_input: Mapped[Optional[int]]
    token_count_output: Mapped[Optional[int]]
    token_count_total: Mapped[Optional[int]]
    cost_usd: Mapped[Optional[float]]  # Estimated cost

    # ==================== ERROR TRACKING ====================

    error_type: Mapped[Optional[str]]  # Exception class name
    error_message: Mapped[Optional[Text]]
    error_stack_trace: Mapped[Optional[Text]]  # FULL STACK TRACE
    retry_count: Mapped[int] = mapped_column(default=0)

    # ==================== CONTEXT AND STATE ====================

    context_sources: Mapped[JSON]  # List of context sources used
    context_size_bytes: Mapped[Optional[int]]
    state_snapshot: Mapped[Optional[JSON]]  # WorkbenchState at completion

    # ==================== RELATIONSHIPS ====================

    conversation: Mapped["ConversationModel"] = relationship(
        back_populates="execution_logs"
    )
    user: Mapped["UserModel"] = relationship()
    session: Mapped[Optional["UserSessionModel"]] = relationship()
    tool_calls: Mapped[List["ToolCallLogModel"]] = relationship(
        back_populates="execution_log",
        cascade="all, delete-orphan"
    )


class ToolCallLogModel(Base):
    """
    Detailed log for individual tool calls within an agent execution.

    Ready for Phase 2.4 when tools are added.
    """
    __tablename__ = "tool_call_logs"

    # ==================== PRIMARY IDENTIFICATION ====================

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    execution_log_id: Mapped[UUID] = mapped_column(
        ForeignKey("agent_execution_logs.id", ondelete="CASCADE"),
        index=True
    )

    # ==================== TOOL IDENTIFICATION ====================

    tool_name: Mapped[str] = mapped_column(index=True)
    tool_type: Mapped[str]  # "langchain" or "mcp"
    call_index: Mapped[int]  # Order within execution (0, 1, 2, ...)

    # ==================== TIMING ====================

    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]]
    duration_ms: Mapped[Optional[int]]

    # ==================== CALL DETAILS ====================

    arguments: Mapped[JSON]  # Tool input arguments
    result: Mapped[Optional[JSON]]  # Tool output
    status: Mapped[str]  # "success", "error", "timeout"

    # ==================== ERROR TRACKING ====================

    error_type: Mapped[Optional[str]]
    error_message: Mapped[Optional[Text]]

    # ==================== RELATIONSHIPS ====================

    execution_log: Mapped["AgentExecutionLogModel"] = relationship(
        back_populates="tool_calls"
    )
```

### 3. 10 Database Indexes for Production Query Optimization

**Critical Indexes**: Optimize common debugging and analytics queries

```python
# models/database.py (continued)

# ==================== INDEX 1: Conversation execution history ====================
# Query: Get all executions for a conversation (sorted by time)
# Use case: View complete execution history for debugging conversation issues
Index(
    'idx_execution_logs_conv_id',
    AgentExecutionLogModel.conversation_id,
    AgentExecutionLogModel.started_at
)

# ==================== INDEX 2: User-specific error tracking ====================
# Query: Get all errors for a specific user
# Use case: User-specific error tracking, support tickets, troubleshooting
Index(
    'idx_execution_logs_user_status',
    AgentExecutionLogModel.user_id,
    AgentExecutionLogModel.execution_status
)

# ==================== INDEX 3: User activity analytics ====================
# Query: Find executions by user and date range
# Use case: User activity reports, usage analytics, billing
Index(
    'idx_execution_logs_user_date',
    AgentExecutionLogModel.user_id,
    AgentExecutionLogModel.started_at
)

# ==================== INDEX 4: System-wide error monitoring ====================
# Query: Find all failed executions across system
# Use case: System-wide error monitoring, SLA tracking, alerts
Index(
    'idx_execution_logs_status',
    AgentExecutionLogModel.execution_status,
    AgentExecutionLogModel.started_at
)

# ==================== INDEX 5: Task tracking ====================
# Query: Find executions by task_id (working memory thread)
# Use case: Track agent's internal task state across executions
# Note: Single-column index already defined at field level (line task_id)

# ==================== INDEX 6: Tool execution sequence ====================
# Query: Get all tool calls for an execution (in order)
# Use case: Debug tool execution sequence, replay tool calls
Index(
    'idx_tool_calls_execution',
    ToolCallLogModel.execution_log_id,
    ToolCallLogModel.call_index
)

# ==================== INDEX 7: Tool performance analysis ====================
# Query: Analyze tool performance across all executions
# Use case: Identify slow tools, optimize tool implementations
Index(
    'idx_tool_calls_performance',
    ToolCallLogModel.tool_name,
    ToolCallLogModel.duration_ms
)

# ==================== INDEX 8: Tool usage analytics ====================
# Query: Find tool calls by name and date
# Use case: Tool usage analytics, adoption tracking, feature usage
Index(
    'idx_tool_calls_tool_date',
    ToolCallLogModel.tool_name,
    ToolCallLogModel.started_at
)

# ==================== INDEX 9: Model performance comparison ====================
# Query: Find executions by model provider/name
# Use case: Compare performance across models, cost analysis, A/B testing
Index(
    'idx_execution_logs_model',
    AgentExecutionLogModel.model_provider,
    AgentExecutionLogModel.model_name,
    AgentExecutionLogModel.started_at
)

# ==================== INDEX 10: Cost monitoring ====================
# Query: Find high-cost executions
# Use case: Cost monitoring, identify expensive queries, budget tracking
Index(
    'idx_execution_logs_cost',
    AgentExecutionLogModel.cost_usd.desc(),
    AgentExecutionLogModel.started_at
)

# ==================== INDEX 11: Performance monitoring ====================
# Query: Find long-running executions
# Use case: Performance monitoring, timeout analysis, optimization
Index(
    'idx_execution_logs_duration',
    AgentExecutionLogModel.duration_ms.desc(),
    AgentExecutionLogModel.started_at
)
```

**Index Rationale**:
- **Indexes 1-4**: Core operational queries (conversation, user, status)
- **Indexes 6-8**: Tool-specific queries (ready for Phase 2.4)
- **Indexes 9-11**: Performance and cost analytics
- All indexes include `started_at` for time-based filtering
- Composite indexes support multiple query patterns efficiently

### 4. Debug Logging Middleware

**Middleware Hooks**: Before agent execution, after execution, on error

```python
# middleware/debug_logging_middleware.py

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID, uuid4
import traceback
import json
from database.adapter import AdaptiveDatabase
from models.database import AgentExecutionLogModel

class DebugLoggingMiddleware:
    """
    Comprehensive debug logging middleware for agent executions.

    Captures all execution details including errors with full stack traces.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.execution_log_id: Optional[UUID] = None
        self.started_at: Optional[datetime] = None

    async def before_agent(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any]
    ) -> None:
        """
        Called before agent execution starts.

        Creates execution log record with initial metadata.
        """
        self.started_at = datetime.utcnow()
        self.execution_log_id = uuid4()

        # Extract configuration
        conversation_id = config["configurable"]["conversation_id"]
        user_id = config["configurable"]["user_id"]
        task_id = config["configurable"]["thread_id"]
        session_id = config["configurable"].get("session_id")

        # Extract user message (last message in list)
        user_message = messages[-1].get("content", "") if messages else ""

        # Get model config from user_settings
        user_settings = config.get("config", {})
        model_provider = user_settings.get("provider", "unknown")
        model_name = user_settings.get("model", "unknown")
        temperature = user_settings.get("temperature")
        max_tokens = user_settings.get("max_tokens")

        # Get workflow mode
        workflow_mode = config.get("workflow_mode", "workbench")

        # Create initial log record
        log_data = {
            "id": self.execution_log_id,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "session_id": session_id,
            "started_at": self.started_at,
            "task_id": task_id,
            "workflow_mode": workflow_mode,
            "execution_status": "running",
            "model_provider": model_provider,
            "model_name": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "user_message": user_message,
            "tools_available": [],  # Empty in Phase 2.3
            "tools_called": [],
            "tool_call_count": 0,
            "middleware_chain": ["DebugLoggingMiddleware"],
            "middleware_timings": {},
            "pii_redacted": False,
            "summarization_triggered": False,
            "step_count": 0,
            "retry_count": 0,
            "context_sources": config.get("context_sources", []),
        }

        await self.db.create_execution_log(log_data)

    async def after_agent(
        self,
        result: Dict[str, Any],
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Called after successful agent execution.

        Updates execution log with results and performance metrics.
        """
        if not self.execution_log_id or not self.started_at:
            return

        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        # Extract response
        agent_response = result.get("content", "")
        structured_response = result.get("structured_output")

        # Extract token counts (if available from model)
        usage = result.get("usage", {})
        token_count_input = usage.get("input_tokens")
        token_count_output = usage.get("output_tokens")
        token_count_total = usage.get("total_tokens")

        # Estimate cost (basic calculation, can be enhanced)
        cost_usd = self._estimate_cost(
            token_count_input,
            token_count_output,
            result.get("model_provider"),
            result.get("model_name")
        )

        # Update log record
        update_data = {
            "completed_at": completed_at,
            "duration_ms": duration_ms,
            "execution_status": "success",
            "agent_response": agent_response,
            "structured_response": structured_response,
            "token_count_input": token_count_input,
            "token_count_output": token_count_output,
            "token_count_total": token_count_total,
            "cost_usd": cost_usd,
            "state_snapshot": state_snapshot,
        }

        await self.db.update_execution_log(self.execution_log_id, update_data)

    async def on_error(
        self,
        error: Exception,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Called when agent execution fails.

        Captures full stack trace and error details for debugging.
        """
        if not self.execution_log_id or not self.started_at:
            return

        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        # Capture full stack trace
        stack_trace = traceback.format_exc()

        # Update log record with error details
        update_data = {
            "completed_at": completed_at,
            "duration_ms": duration_ms,
            "execution_status": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_stack_trace": stack_trace,
            "state_snapshot": state_snapshot,
        }

        await self.db.update_execution_log(self.execution_log_id, update_data)

    def _estimate_cost(
        self,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        provider: Optional[str],
        model: Optional[str]
    ) -> Optional[float]:
        """
        Estimate execution cost in USD.

        Basic implementation - can be enhanced with actual pricing tables.
        """
        if not input_tokens or not output_tokens:
            return None

        # Simple cost estimation (placeholder rates)
        # TODO: Add actual pricing table in Phase 2.8
        cost_per_1k_input = 0.003  # $3/million
        cost_per_1k_output = 0.015  # $15/million

        cost = (
            (input_tokens / 1000) * cost_per_1k_input +
            (output_tokens / 1000) * cost_per_1k_output
        )

        return round(cost, 6)
```

### 5. Analytics Service for Optimized Log Queries

**Service Layer**: High-level query methods using indexes

```python
# services/analytics_service.py

from sqlalchemy import select, and_, desc, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from database.adapter import AdaptiveDatabase
from models.database import AgentExecutionLogModel, ToolCallLogModel

class AnalyticsService:
    """
    Query execution logs efficiently using database indexes.

    All methods use the 10 production indexes for optimal performance.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    # ==================== INDEX 1: idx_execution_logs_conv_id ====================

    async def get_conversation_executions(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Get all executions for a conversation (chronological order).

        Uses composite index on (conversation_id, started_at).
        """
        return await self.db.get_execution_logs(
            conversation_id=conversation_id,
            limit=limit
        )

    # ==================== INDEX 2: idx_execution_logs_user_status ====================

    async def get_user_errors(
        self,
        user_id: UUID,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """
        Get all errors for a specific user.

        Uses composite index on (user_id, execution_status).
        Useful for support tickets and troubleshooting.
        """
        return await self.db.get_execution_logs(
            user_id=user_id,
            status="error",
            since=since,
            limit=limit
        )

    # ==================== INDEX 4: idx_execution_logs_status ====================

    async def get_system_errors(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """
        Get all errors across the system.

        Uses composite index on (execution_status, started_at).
        Useful for system-wide monitoring and SLA tracking.
        """
        return await self.db.get_execution_logs(
            status="error",
            since=since,
            limit=limit
        )

    # ==================== INDEX 6: idx_tool_calls_execution ====================

    async def get_execution_tool_calls(
        self,
        execution_log_id: UUID
    ) -> List[ToolCallLogModel]:
        """
        Get all tool calls for an execution (in order).

        Uses composite index on (execution_log_id, call_index).
        Useful for debugging tool execution sequences.
        """
        return await self.db.get_tool_calls(execution_log_id=execution_log_id)

    # ==================== INDEX 7: idx_tool_calls_performance ====================

    async def get_slowest_tools(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find slowest tool calls across all executions.

        Uses composite index on (tool_name, duration_ms).
        Useful for identifying performance bottlenecks.
        """
        # Implemented in database backend with aggregation
        return await self.db.get_tool_performance_stats(limit=limit)

    # ==================== INDEX 9: idx_execution_logs_model ====================

    async def get_model_performance(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Compare performance across models.

        Uses composite index on (model_provider, model_name, started_at).
        Useful for A/B testing and cost analysis.
        """
        return await self.db.get_model_performance_stats(
            provider=provider,
            since=since
        )

    # ==================== INDEX 10: idx_execution_logs_cost ====================

    async def get_expensive_executions(
        self,
        threshold_usd: float = 0.10,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Find high-cost executions.

        Uses index on (cost_usd DESC, started_at).
        Useful for budget monitoring.
        """
        return await self.db.get_execution_logs(
            min_cost=threshold_usd,
            limit=limit,
            order_by="cost_desc"
        )

    # ==================== INDEX 11: idx_execution_logs_duration ====================

    async def get_slow_executions(
        self,
        threshold_ms: int = 10000,  # 10 seconds
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """
        Find long-running executions.

        Uses index on (duration_ms DESC, started_at).
        Useful for performance optimization.
        """
        return await self.db.get_execution_logs(
            min_duration_ms=threshold_ms,
            limit=limit,
            order_by="duration_desc"
        )

    # ==================== COMPOSITE QUERIES ====================

    async def get_user_tool_usage(
        self,
        user_id: UUID,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tool usage statistics for a user.

        Uses idx_execution_logs_user_date + idx_tool_calls_execution.
        Useful for user analytics and feature adoption tracking.
        """
        # First get user's execution IDs
        executions = await self.db.get_execution_logs(
            user_id=user_id,
            since=since
        )

        execution_ids = [e.id for e in executions]
        if not execution_ids:
            return []

        # Then get tool call statistics
        return await self.db.get_tool_usage_by_executions(execution_ids)
```

### 6. Structured Output Model

**Type-Safe Response**: Pydantic model for agent responses

```python
# models/agent_models.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class AgentResponse(BaseModel):
    """
    Structured response from agent execution.

    Ensures type safety and consistent response format.
    """

    content: str = Field(
        ...,
        description="Agent's response message to the user"
    )

    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in the response (0-1)"
    )

    needs_clarification: bool = Field(
        default=False,
        description="Whether agent needs clarification from user"
    )

    clarification_questions: Optional[List[str]] = Field(
        default=None,
        description="Questions for user if clarification needed"
    )

    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata (tool calls, reasoning, etc.)"
    )

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response generation timestamp"
    )
```

### 7. LangChain v1.0 Contract Testing

**API Stability**: Ensure `create_agent()` API remains stable across updates

```python
# tests/contracts/test_langchain_v1_agent.py

import pytest
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from models.agent_models import AgentResponse

class TestLangChainV1AgentContract:
    """
    Contract tests for LangChain v1.0 create_agent() API.

    These tests ensure the API we depend on remains stable.
    If these fail after a LangChain update, we need to adapt our code.
    """

    def test_create_agent_signature(self):
        """Verify create_agent() accepts expected parameters."""
        from inspect import signature

        sig = signature(create_agent)
        params = list(sig.parameters.keys())

        # Required parameters we use
        assert "model" in params
        assert "tools" in params
        assert "middleware" in params
        assert "structured_output" in params
        assert "checkpointer" in params

    def test_create_agent_with_empty_tools(self, mock_llm):
        """Verify agent creation with empty tools list."""
        agent = create_agent(
            model=mock_llm,
            tools=[],  # Phase 2.3: No tools
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

        assert agent is not None

    def test_create_agent_with_middleware(self, mock_llm, mock_middleware):
        """Verify middleware parameter accepts list of middleware."""
        agent = create_agent(
            model=mock_llm,
            tools=[],
            middleware=[mock_middleware],
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

        assert agent is not None

    def test_agent_ainvoke_signature(self, mock_agent):
        """Verify agent.ainvoke() accepts our config structure."""
        from inspect import signature

        sig = signature(mock_agent.ainvoke)
        params = list(sig.parameters.keys())

        assert "input" in params  # Or first positional
        assert "config" in params

    def test_agent_astream_signature(self, mock_agent):
        """Verify agent.astream() supports streaming responses."""
        from inspect import signature

        sig = signature(mock_agent.astream)
        params = list(sig.parameters.keys())

        assert "input" in params
        assert "config" in params

    def test_structured_output_format(self, mock_agent):
        """Verify structured_output returns AgentResponse format."""
        # This would be an integration test with real model
        # Contract test just verifies the type is accepted
        pass

    def test_checkpointer_interface(self):
        """Verify MemorySaver implements expected interface."""
        checkpointer = MemorySaver()

        # Verify required methods exist
        assert hasattr(checkpointer, "aget")
        assert hasattr(checkpointer, "aput")
        assert hasattr(checkpointer, "alist")
```

**Why Contract Tests**:
- LangChain v1.0 is new (released 2024)
- API may change in minor versions
- Contract tests alert us to breaking changes
- Can pin version safely with confidence

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/services/
├── agent_service.py                    # Minimal AgentService with debug logging
├── analytics_service.py                # Optimized log query methods

src/agent_workbench/middleware/
└── debug_logging_middleware.py         # Before/after/error hooks

src/agent_workbench/models/
├── agent_models.py                     # AgentResponse structured output
└── agent_config.py                     # Agent configuration models

tests/services/
├── test_agent_service.py               # Unit tests for AgentService
└── test_analytics_service.py           # Tests for analytics queries

tests/middleware/
└── test_debug_logging_middleware.py    # Middleware tests

tests/contracts/
└── test_langchain_v1_agent.py          # LangChain API contract tests

tests/integration/
└── test_agent_workflow_integration.py  # End-to-end agent tests

alembic/versions/
└── XXXX_add_agent_execution_logs.py    # Migration for new tables + indexes
```

### Files to MODIFY:

```
src/agent_workbench/models/database.py
# ADD: AgentExecutionLogModel, ToolCallLogModel
# ADD: 10 database indexes
# ADD: Relationships to ConversationModel, UserModel

src/agent_workbench/database/backends/sqlite.py
# ADD: create_execution_log(data: Dict) -> UUID
# ADD: update_execution_log(id: UUID, data: Dict) -> None
# ADD: get_execution_logs(filters: Dict) -> List[AgentExecutionLogModel]
# ADD: get_tool_calls(execution_log_id: UUID) -> List[ToolCallLogModel]
# ADD: get_tool_performance_stats(limit: int) -> List[Dict]
# ADD: get_model_performance_stats(provider: str, since: datetime) -> List[Dict]

src/agent_workbench/database/backends/hub.py
# ADD: Same methods as sqlite.py for HuggingFace Spaces

src/agent_workbench/database/protocol.py
# ADD: Execution log method signatures to DatabaseBackend protocol

src/agent_workbench/services/consolidated_service.py
# MODIFY: Use AgentService instead of direct LLM calls
# MODIFY: Pass conversation_id and user_id to agent

src/agent_workbench/api/routes/chat_workflow.py
# MODIFY: Extract user_id from authentication (depends on UI-002)
# MODIFY: Pass user_id to workflow service

pyproject.toml
# ADD: langchain = "^1.0.0"
# ADD: langgraph = "^0.3.0"

.env.example
# ADD: AGENT_DEFAULT_PROVIDER=openrouter
# ADD: AGENT_DEFAULT_MODEL=claude-sonnet-4-5
# ADD: AGENT_DEFAULT_TEMPERATURE=0.7
# ADD: AGENT_MAX_TOKENS=4096
# ADD: AGENT_TIMEOUT_SECONDS=60
```

### Exact Function Signatures:

```python
# ==================== services/agent_service.py ====================

class AgentService:
    def __init__(self, db: AdaptiveDatabase):
        ...

    async def initialize(self, model_config: ModelConfig) -> None:
        """Initialize agent with LangChain v1.0 create_agent()."""
        ...

    async def run(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        conversation_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Execute agent with debug logging."""
        ...

    async def stream(
        self,
        messages: List[Dict[str, str]],
        user_settings: Dict[str, Any],
        task_id: str,
        conversation_id: UUID,
        user_id: UUID
    ) -> AsyncGenerator[str, None]:
        """Stream agent responses with debug logging."""
        ...

    def _create_langchain_model(self, model_config: ModelConfig) -> BaseChatModel:
        """Create LangChain model (reuse existing ChatService logic)."""
        ...


# ==================== middleware/debug_logging_middleware.py ====================

class DebugLoggingMiddleware:
    def __init__(self, db: AdaptiveDatabase):
        ...

    async def before_agent(
        self,
        messages: List[Dict[str, str]],
        config: Dict[str, Any]
    ) -> None:
        """Called before agent execution - create log record."""
        ...

    async def after_agent(
        self,
        result: Dict[str, Any],
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """Called after successful execution - update log with results."""
        ...

    async def on_error(
        self,
        error: Exception,
        state_snapshot: Optional[Dict[str, Any]] = None
    ) -> None:
        """Called on error - capture stack trace."""
        ...

    def _estimate_cost(
        self,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        provider: Optional[str],
        model: Optional[str]
    ) -> Optional[float]:
        """Estimate execution cost in USD."""
        ...


# ==================== services/analytics_service.py ====================

class AnalyticsService:
    def __init__(self, db: AdaptiveDatabase):
        ...

    async def get_conversation_executions(
        self,
        conversation_id: UUID,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """Get all executions for a conversation."""
        ...

    async def get_user_errors(
        self,
        user_id: UUID,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """Get all errors for a specific user."""
        ...

    async def get_system_errors(
        self,
        since: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AgentExecutionLogModel]:
        """Get all errors across system."""
        ...

    async def get_execution_tool_calls(
        self,
        execution_log_id: UUID
    ) -> List[ToolCallLogModel]:
        """Get all tool calls for an execution."""
        ...

    async def get_slowest_tools(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find slowest tool calls."""
        ...

    async def get_model_performance(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Compare performance across models."""
        ...

    async def get_expensive_executions(
        self,
        threshold_usd: float = 0.10,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """Find high-cost executions."""
        ...

    async def get_slow_executions(
        self,
        threshold_ms: int = 10000,
        limit: int = 50
    ) -> List[AgentExecutionLogModel]:
        """Find long-running executions."""
        ...

    async def get_user_tool_usage(
        self,
        user_id: UUID,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get tool usage statistics for a user."""
        ...


# ==================== database/backends/sqlite.py ====================

class SQLiteBackend:
    # ADD these methods:

    async def create_execution_log(self, data: Dict[str, Any]) -> UUID:
        """Create new execution log record."""
        ...

    async def update_execution_log(
        self,
        log_id: UUID,
        data: Dict[str, Any]
    ) -> None:
        """Update existing execution log."""
        ...

    async def get_execution_logs(
        self,
        conversation_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
        order_by: str = "started_at_desc"
    ) -> List[AgentExecutionLogModel]:
        """Query execution logs with filters."""
        ...

    async def get_tool_calls(
        self,
        execution_log_id: UUID
    ) -> List[ToolCallLogModel]:
        """Get tool calls for an execution."""
        ...

    async def get_tool_performance_stats(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get tool performance statistics."""
        ...

    async def get_model_performance_stats(
        self,
        provider: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get model performance statistics."""
        ...
```

### Additional Dependencies:

```toml
# pyproject.toml

[tool.uv.dependencies]
# LangChain v1.0 for agent creation
langchain = "^1.0.0"
langgraph = "^0.3.0"

# Existing dependencies (unchanged)
fastapi = "^0.115.0"
gradio = "^5.0.0"
sqlalchemy = "^2.0.0"
# ... other existing dependencies
```

### Environment Variables:

```bash
# .env.example

# ==================== AGENT CONFIGURATION ====================
AGENT_DEFAULT_PROVIDER=openrouter
AGENT_DEFAULT_MODEL=claude-sonnet-4-5
AGENT_DEFAULT_TEMPERATURE=0.7
AGENT_MAX_TOKENS=4096
AGENT_TIMEOUT_SECONDS=60

# ==================== DEBUG LOGGING ====================
AGENT_LOGGING_ENABLED=true
AGENT_LOG_STATE_SNAPSHOTS=true  # Log full state on completion
AGENT_LOG_PII=false              # Redact PII in logs (Phase 2.5)
```

### FORBIDDEN Actions:

- Adding tools to agent (Phase 2.4 - MCP integration)
- Implementing PII redaction middleware (Phase 2.5)
- Implementing conversation summarization (Phase 2.5)
- Adding multi-agent coordination (Phase 2.6)
- Implementing agent memory beyond checkpointer (Phase 2.7)
- Adding production error handling/retries (Phase 2.8)
- Adding rate limiting (Phase 2.8)
- Adding health checks (Phase 2.8)
- Creating UI components for log viewing
- Modifying authentication/session logic (UI-002 dependency)

## Testing Strategy

### Test Coverage (~12 tests):

```python
# ==================== UNIT TESTS ====================

# tests/services/test_agent_service.py
def test_agent_service_initialization():
    """Verify AgentService initializes with empty tools."""
    ...

def test_agent_service_run():
    """Verify agent execution with mock LLM."""
    ...

def test_agent_service_stream():
    """Verify agent streaming with mock LLM."""
    ...

def test_agent_service_error_handling():
    """Verify agent handles errors gracefully."""
    ...


# tests/middleware/test_debug_logging_middleware.py
def test_middleware_before_agent():
    """Verify middleware creates log record before execution."""
    ...

def test_middleware_after_agent():
    """Verify middleware updates log after successful execution."""
    ...

def test_middleware_on_error():
    """Verify middleware captures stack trace on error."""
    ...

def test_middleware_cost_estimation():
    """Verify cost estimation logic."""
    ...


# tests/services/test_analytics_service.py
def test_get_conversation_executions():
    """Verify conversation execution query uses correct index."""
    ...

def test_get_user_errors():
    """Verify user error query uses correct index."""
    ...

def test_get_system_errors():
    """Verify system error query uses correct index."""
    ...


# ==================== CONTRACT TESTS ====================

# tests/contracts/test_langchain_v1_agent.py
def test_create_agent_signature():
    """Verify create_agent() API signature is stable."""
    ...

def test_create_agent_with_empty_tools():
    """Verify agent creation with no tools."""
    ...

def test_create_agent_with_middleware():
    """Verify middleware parameter works correctly."""
    ...

def test_agent_ainvoke_signature():
    """Verify agent.ainvoke() signature is stable."""
    ...

def test_agent_astream_signature():
    """Verify agent.astream() signature is stable."""
    ...


# ==================== INTEGRATION TESTS ====================

# tests/integration/test_agent_workflow_integration.py
@pytest.mark.integration
async def test_agent_workflow_end_to_end():
    """Test complete workflow from request to response with debug logging."""
    ...

@pytest.mark.integration
async def test_agent_workflow_error_logging():
    """Test error logging captures stack traces correctly."""
    ...

@pytest.mark.integration
async def test_agent_workflow_streaming():
    """Test streaming responses work with debug logging."""
    ...


# ==================== DATABASE TESTS ====================

# tests/database/test_execution_logs.py
async def test_create_execution_log():
    """Verify execution log creation."""
    ...

async def test_update_execution_log():
    """Verify execution log updates."""
    ...

async def test_execution_log_cascade_delete():
    """Verify logs deleted when conversation deleted."""
    ...

async def test_execution_log_indexes():
    """Verify all 10 indexes are created."""
    ...
```

### Test Execution:

```bash
# Run all tests
make test

# Run unit tests only (fast)
make test-unit-only

# Run integration tests (requires backend)
make test-with-backend

# Run contract tests (check LangChain API stability)
uv run pytest tests/contracts/ -v

# Check test coverage
uv run pytest --cov=src/agent_workbench/services/agent_service.py
uv run pytest --cov=src/agent_workbench/middleware/debug_logging_middleware.py
```

## Success Criteria

### Functional Requirements:

- [ ] **Agent Responds**: Agent successfully responds to basic questions
- [ ] **No Tools**: Agent has empty tools list (no tool calling in Phase 2.3)
- [ ] **Structured Output**: Agent returns `AgentResponse` Pydantic model
- [ ] **Conversation Memory**: Agent maintains context via `MemorySaver` checkpointer
- [ ] **Streaming**: Agent responses stream to UI successfully
- [ ] **Workflow Integration**: Existing workflow endpoints use `AgentService`

### Debug Logging Requirements:

- [ ] **Execution Logs Created**: Every agent call creates execution log record
- [ ] **Success Logging**: Successful executions log response, timing, tokens
- [ ] **Error Logging**: Failed executions log exception type, message, **FULL STACK TRACE**
- [ ] **Middleware Tracking**: Logs capture middleware chain and timings
- [ ] **Performance Metrics**: Logs include duration_ms, token counts, estimated cost
- [ ] **Database Indexes**: All 10 indexes created and functional
- [ ] **Analytics Queries**: `AnalyticsService` methods use indexes efficiently

### Technical Requirements:

- [ ] **LangChain v1.0**: Using `create_agent()` from langchain v1.0+
- [ ] **Contract Tests**: LangChain API contract tests pass (5/5)
- [ ] **Type Safety**: All code passes mypy strict checks
- [ ] **Test Coverage**: >90% coverage for agent_service, middleware, analytics
- [ ] **Backward Compatibility**: Existing Phase 1 workflows still work
- [ ] **Migration Success**: Database migration runs without errors

### Performance Requirements:

- [ ] **Response Time**: Agent responses complete in <10 seconds for basic queries
- [ ] **Log Creation**: Execution log creation adds <100ms overhead
- [ ] **Query Performance**: Analytics queries return in <500ms using indexes
- [ ] **Streaming Performance**: Streaming adds <50ms latency

### Debugging Requirements:

- [ ] **Error Troubleshooting**: Can identify root cause from stack trace
- [ ] **Performance Analysis**: Can identify slow executions via duration index
- [ ] **Cost Monitoring**: Can track expensive executions via cost index
- [ ] **User Support**: Can view user's error history for support tickets

### Documentation Requirements:

- [ ] **Agent Setup**: README documents agent configuration
- [ ] **Debug Logging**: Documentation explains log fields and indexes
- [ ] **Analytics Queries**: Examples of common analytics queries
- [ ] **Troubleshooting**: Guide for using logs to debug issues

---

## Phase 2.3 Checklist

Before marking this task complete, verify:

- [ ] LangChain v1.0 installed (`langchain>=1.0.0`)
- [ ] LangGraph installed (`langgraph>=0.3.0`)
- [ ] `AgentExecutionLogModel` created with 48 fields
- [ ] `ToolCallLogModel` created (ready for Phase 2.4)
- [ ] 10 database indexes created and functional
- [ ] Database migration runs successfully
- [ ] `AgentService` created with empty tools list
- [ ] `DebugLoggingMiddleware` implemented with 3 hooks
- [ ] `AnalyticsService` created with optimized query methods
- [ ] Database backends support execution log methods
- [ ] `ConsolidatedWorkbenchService` uses `AgentService`
- [ ] Agent responds to basic questions
- [ ] Agent responses stream to UI
- [ ] **Debug logs captured for every execution**
- [ ] **Stack traces stored on errors**
- [ ] **Can query logs via AnalyticsService**
- [ ] No tool calls (expected - tools not added yet)
- [ ] Contract tests pass (5/5)
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Type checking passes (mypy)
- [ ] Documentation updated

**Expected Behavior After Phase 2.3**:
- User sends message → Agent processes → Response returned
- Every execution logged to database with comprehensive metadata
- Errors include full stack traces for debugging
- Can query logs for analytics and troubleshooting
- Agent has NO tools yet (Phase 2.4 adds MCP tools)

**Next Phase (2.4)**: Add MCP tool integration to agent
