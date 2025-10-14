# AGENT-003: Custom Middleware

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: AGENT-003-custom-middleware
**Phase**: 2.6
**Dependencies**: AGENT-002 (built-in middleware), AGENT-001 (agent service), UI-002 (user authentication)

## Context

Implement custom middleware for context loading, memory persistence, execution tracking, and guardrails. These middleware components integrate with Phase 1's existing `ContextService` and database infrastructure to provide comprehensive agent orchestration capabilities.

**Critical Design Decision**: Custom middleware completes Phase 1's placeholder `ContextService` implementation, transforming it from a stub into a fully functional context management system. This middleware layer sits between built-in LangChain middleware (from Phase 2.5) and the agent execution core.

**Middleware Characteristics**:
- **ContextMiddleware**: Loads conversation history and business profiles from database before agent execution
- **MemoryMiddleware**: Saves agent responses and tool calls to database after execution
- **ExecutionTrackingMiddleware**: Tracks execution metrics using Phase 1 `ContextService` for context-aware performance monitoring
- **GuardrailsMiddleware**: Validates tool calls and responses against configurable policies (optional)

**Integration with Phase 1**:
- Uses existing `AdaptiveDatabase` for persistence
- Completes `ContextService` placeholder implementation
- Integrates with `WorkbenchState` for context injection
- Maintains Phase 1 conversation/message models

## Architecture Scope

### What's Included:

- **ContextMiddleware**:
  - Load conversation history from database
  - Load business profile for SEO Coach mode
  - Inject context into agent state before execution
  - Integration with Phase 1 `ConversationService`

- **MemoryMiddleware**:
  - Save assistant responses to database
  - Store tool call results
  - Track tool usage patterns
  - Update conversation metadata

- **ExecutionTrackingMiddleware**:
  - Complete Phase 1 `ContextService` implementation
  - Track execution metrics (duration, steps, tokens)
  - Store context sources and sizes
  - Link metrics to conversation context

- **GuardrailsMiddleware (Optional)**:
  - Validate tool call permissions
  - Check response content policies
  - Block prohibited operations
  - Log policy violations

- **ContextService Enhancement**:
  - Complete placeholder methods from Phase 1
  - Database integration for context persistence
  - Context prompt building with formatting
  - Active context source tracking

- **Middleware Orchestration**:
  - Middleware chain configuration
  - Execution order management
  - Error propagation handling
  - State passing between middleware

### What's Explicitly Excluded:

- Built-in middleware (Phase 2.5 - PII redaction, summarization, human-in-the-loop)
- Multi-agent coordination (Phase 2.7)
- Agent learning and preference adaptation (Phase 2.7)
- Advanced context retrieval (RAG, vector search) - Phase 3
- Production error handling and retries (Phase 2.8)
- Rate limiting (Phase 2.8)
- Cost optimization (Phase 2.8)
- UI components for middleware configuration

## Architectural Decisions

### 1. ContextMiddleware: Database-Backed Context Loading

**Core Approach**: Load conversation state from database before agent execution

```python
# middleware/context_middleware.py

from typing import Dict, Any
from uuid import UUID
from database.adapter import AdaptiveDatabase
from services.context_service import ContextService

class ContextMiddleware:
    """
    Load conversation context before agent execution.

    Integrates with Phase 1 database infrastructure to inject
    conversation history, business profiles, and context data
    into agent state.
    """

    def __init__(self, db: AdaptiveDatabase, context_service: ContextService):
        self.db = db
        self.context_service = context_service

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Load context before agent starts.

        Args:
            state: Agent state with conversation_id

        Returns:
            Enhanced state with conversation history and context
        """
        conversation_id = state.get("conversation_id")
        if not conversation_id:
            return state

        # Load conversation history using Phase 1 database
        messages = self.db.get_messages(conversation_id)
        state["conversation_history"] = [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            for msg in messages
        ]

        # Load business profile for SEO Coach mode
        workflow_mode = state.get("workflow_mode", "workbench")
        if workflow_mode == "seo_coach":
            profile = self.db.get_business_profile(conversation_id)
            if profile:
                state["business_profile"] = {
                    "name": profile.business_name,
                    "industry": profile.industry,
                    "target_audience": profile.target_audience,
                    "goals": profile.goals
                }

        # Load active context data using Phase 1 ContextService
        context_sources = await self.context_service.get_active_contexts(
            conversation_id
        )

        if context_sources:
            # Build context data from stored sources
            context_data = {}
            for source in context_sources:
                source_data = await self._load_context_source(
                    conversation_id,
                    source
                )
                if source_data:
                    context_data[source] = source_data

            if context_data:
                # Format context as prompt
                context_prompt = await self.context_service.build_context_prompt(
                    context_data
                )
                state["context_prompt"] = context_prompt
                state["context_sources"] = context_sources

        return state

    async def _load_context_source(
        self,
        conversation_id: UUID,
        source: str
    ) -> Dict[str, Any]:
        """
        Load specific context source data.

        Args:
            conversation_id: Conversation ID
            source: Context source identifier

        Returns:
            Context data for source
        """
        # Load from database (implementation depends on context storage schema)
        # For now, use Phase 1 ContextService pattern
        return {}
```

**Why Database-Backed**:
- Reuses Phase 1 conversation infrastructure
- No additional state management needed
- Supports multi-mode workflows (workbench/seo_coach)
- Context persists across sessions

### 2. MemoryMiddleware: Persistent Conversation Memory

**Core Approach**: Save agent outputs to database after execution

```python
# middleware/memory_middleware.py

from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from database.adapter import AdaptiveDatabase
from models.standard_messages import StandardMessage

class MemoryMiddleware:
    """
    Save agent interactions to database for persistent memory.

    Stores responses, tool calls, and metadata using Phase 1
    message and conversation models.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db

    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save agent interaction after execution.

        Args:
            state: Agent state with response and metadata

        Returns:
            Unchanged state (persistence side effect)
        """
        conversation_id = state.get("conversation_id")
        if not conversation_id:
            return state

        # Extract assistant response from state
        messages = state.get("messages", [])
        if not messages:
            return state

        # Get the last assistant message
        last_message = messages[-1]
        if last_message.get("role") != "assistant":
            return state

        # Save assistant message using Phase 1 database
        message_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": last_message.get("content", ""),
            "timestamp": datetime.utcnow()
        }

        # Add tool calls if present
        tool_calls = last_message.get("tool_calls", [])
        if tool_calls:
            message_data["tool_calls"] = tool_calls

            # Store individual tool usage for analytics
            for tool_call in tool_calls:
                await self._store_tool_usage(
                    conversation_id=conversation_id,
                    tool_name=tool_call.get("name"),
                    tool_args=tool_call.get("arguments", {}),
                    tool_result=tool_call.get("result"),
                    success=tool_call.get("success", True),
                    duration_ms=tool_call.get("duration_ms")
                )

        # Save message to database
        await self.db.save_message(message_data)

        # Update conversation metadata
        await self._update_conversation_metadata(
            conversation_id=conversation_id,
            message_count=len(messages),
            last_activity=datetime.utcnow()
        )

        return state

    async def _store_tool_usage(
        self,
        conversation_id: UUID,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Any,
        success: bool,
        duration_ms: int = None
    ) -> None:
        """
        Store tool usage for analytics.

        Links to Phase 2.3 ToolCallLogModel if available,
        otherwise stores in conversation metadata.
        """
        # Use Phase 2.3 execution logs if available
        # Falls back to metadata storage for Phase 2.6 standalone usage
        tool_usage_data = {
            "conversation_id": conversation_id,
            "tool_name": tool_name,
            "arguments": tool_args,
            "result": tool_result,
            "success": success,
            "duration_ms": duration_ms,
            "timestamp": datetime.utcnow()
        }

        # Store via database backend
        await self.db.store_tool_usage(tool_usage_data)

    async def _update_conversation_metadata(
        self,
        conversation_id: UUID,
        message_count: int,
        last_activity: datetime
    ) -> None:
        """Update conversation-level metadata."""
        metadata = {
            "message_count": message_count,
            "last_activity": last_activity,
            "updated_at": datetime.utcnow()
        }
        await self.db.update_conversation_metadata(conversation_id, metadata)
```

**Why After-Agent Hook**:
- Ensures response is complete before saving
- Captures final state including tool results
- Separates execution from persistence
- Allows error recovery without partial saves

### 3. ExecutionTrackingMiddleware: Complete Phase 1 ContextService

**Core Approach**: Use Phase 1 ContextService for metrics storage

```python
# middleware/execution_tracking_middleware.py

from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID
from services.context_service import ContextService

class ExecutionTrackingMiddleware:
    """
    Track execution metrics using Phase 1 ContextService.

    Completes the placeholder ContextService implementation by
    storing execution metrics as context data for performance
    monitoring and optimization.
    """

    def __init__(self, context_service: ContextService):
        self.context_service = context_service
        self.started_at: Optional[datetime] = None
        self.step_count: int = 0

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Record execution start time."""
        self.started_at = datetime.utcnow()
        self.step_count = 0
        return state

    async def before_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Count agent steps."""
        self.step_count += 1
        return state

    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store execution metrics in ContextService.

        Uses Phase 1 ContextService to persist metrics as
        conversation context for performance tracking.
        """
        if not self.started_at:
            return state

        conversation_id = state.get("conversation_id")
        if not conversation_id:
            return state

        # Calculate metrics
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - self.started_at).total_seconds() * 1000)

        # Extract token counts if available
        usage = state.get("usage", {})
        token_count = usage.get("total_tokens", 0)

        # Build metrics context data
        metrics_context = {
            "execution_metrics": {
                "started_at": self.started_at.isoformat(),
                "completed_at": completed_at.isoformat(),
                "duration_ms": duration_ms,
                "step_count": self.step_count,
                "token_count": token_count,
                "workflow_mode": state.get("workflow_mode", "workbench")
            }
        }

        # Store metrics using Phase 1 ContextService
        await self.context_service.update_conversation_context(
            conversation_id=conversation_id,
            context_data=metrics_context,
            sources=["execution_metrics"]
        )

        # Add metrics to state for downstream middleware
        state["execution_duration_ms"] = duration_ms
        state["execution_steps"] = self.step_count

        return state

    async def on_error(
        self,
        error: Exception,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track error metrics.

        Stores error information as context for debugging
        and error pattern analysis.
        """
        if not self.started_at:
            return state

        conversation_id = state.get("conversation_id")
        if not conversation_id:
            return state

        # Calculate partial execution time
        error_at = datetime.utcnow()
        duration_ms = int((error_at - self.started_at).total_seconds() * 1000)

        # Build error context
        error_context = {
            "execution_error": {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_at": error_at.isoformat(),
                "duration_before_error_ms": duration_ms,
                "step_count": self.step_count
            }
        }

        # Store error context
        await self.context_service.update_conversation_context(
            conversation_id=conversation_id,
            context_data=error_context,
            sources=["execution_error"]
        )

        return state
```

**Why ContextService Integration**:
- Completes Phase 1 placeholder implementation
- Metrics stored as conversation context
- Enables context-aware performance optimization
- Reuses existing persistence infrastructure

### 4. GuardrailsMiddleware: Optional Policy Enforcement

**Core Approach**: Validate responses and tool calls against policies

```python
# middleware/guardrails_middleware.py

from typing import Dict, Any, List, Optional
import re

class GuardrailsMiddleware:
    """
    Optional middleware for policy enforcement and validation.

    Validates tool calls and responses against configurable
    policies before execution proceeds.
    """

    def __init__(
        self,
        allowed_tools: Optional[List[str]] = None,
        blocked_patterns: Optional[List[str]] = None,
        max_tool_calls_per_execution: int = 10
    ):
        self.allowed_tools = allowed_tools
        self.blocked_patterns = blocked_patterns or []
        self.max_tool_calls = max_tool_calls_per_execution
        self.tool_call_count = 0

    async def after_model(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate model response before tool execution.

        Called after model generates response but before
        tools are executed.
        """
        messages = state.get("messages", [])
        if not messages:
            return state

        last_message = messages[-1]

        # Check response content
        content = last_message.get("content", "")
        if self._contains_prohibited_content(content):
            raise ValueError(
                "Response violates content policy: prohibited pattern detected"
            )

        # Validate tool calls
        tool_calls = last_message.get("tool_calls", [])
        if tool_calls:
            # Check tool call limit
            self.tool_call_count += len(tool_calls)
            if self.tool_call_count > self.max_tool_calls:
                raise ValueError(
                    f"Tool call limit exceeded: {self.tool_call_count} > {self.max_tool_calls}"
                )

            # Validate each tool call
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")

                # Check tool permissions
                if self.allowed_tools and tool_name not in self.allowed_tools:
                    raise ValueError(
                        f"Tool '{tool_name}' not in allowed tools list"
                    )

                # Validate tool arguments (basic validation)
                args = tool_call.get("arguments", {})
                if not isinstance(args, dict):
                    raise ValueError(
                        f"Tool '{tool_name}' arguments must be a dictionary"
                    )

        return state

    def _contains_prohibited_content(self, content: str) -> bool:
        """
        Check if content matches prohibited patterns.

        Args:
            content: Response content to check

        Returns:
            True if prohibited content detected
        """
        for pattern in self.blocked_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reset tool call counter at start of execution."""
        self.tool_call_count = 0
        return state
```

**Why Optional**:
- Not all use cases require guardrails
- Can be added selectively per workflow mode
- Minimal overhead when not used
- Extensible for custom policies

### 5. Enhanced Phase 1 ContextService Implementation

**Complete Placeholder Methods**: Transform stub into full implementation

```python
# services/context_service.py (MODIFY existing Phase 1 file)

from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime
from database.adapter import AdaptiveDatabase

class ContextService:
    """
    Service for managing conversation context integration.

    Enhanced from Phase 1 placeholder to full implementation
    with database persistence.
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
        Update conversation context data.

        Args:
            conversation_id: Conversation ID
            context_data: Context data to inject
            sources: Context source tracking
        """
        # Store context in database
        context_record = {
            "conversation_id": conversation_id,
            "context_data": context_data,
            "sources": sources,
            "updated_at": datetime.utcnow()
        }

        await self.db.save_conversation_context(context_record)

    async def clear_conversation_context(
        self,
        conversation_id: UUID,
        source: Optional[str] = None
    ) -> None:
        """
        Clear conversation context.

        Args:
            conversation_id: Conversation ID
            source: Specific source to clear (None = clear all)
        """
        if source:
            # Clear specific source
            await self.db.clear_context_source(conversation_id, source)
        else:
            # Clear all context
            await self.db.clear_all_context(conversation_id)

    async def get_active_contexts(self, conversation_id: UUID) -> List[str]:
        """
        Get active context sources for conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of active context sources
        """
        context_record = await self.db.get_conversation_context(conversation_id)
        if not context_record:
            return []

        return context_record.get("sources", [])

    async def build_context_prompt(self, context_data: Dict[str, Any]) -> str:
        """
        Build context prompt from context data.

        Args:
            context_data: Context data

        Returns:
            Formatted context prompt
        """
        if not context_data:
            return ""

        # Enhanced formatting with sections
        sections = []

        # Execution metrics section
        if "execution_metrics" in context_data:
            metrics = context_data["execution_metrics"]
            sections.append(
                "Execution Context:\n"
                f"- Duration: {metrics.get('duration_ms')}ms\n"
                f"- Steps: {metrics.get('step_count')}\n"
                f"- Tokens: {metrics.get('token_count')}"
            )

        # Business profile section (SEO Coach)
        if "business_profile" in context_data:
            profile = context_data["business_profile"]
            sections.append(
                "Business Profile:\n"
                f"- Name: {profile.get('name')}\n"
                f"- Industry: {profile.get('industry')}\n"
                f"- Target Audience: {profile.get('target_audience')}"
            )

        # Generic sections
        for key, value in context_data.items():
            if key not in ["execution_metrics", "business_profile"]:
                if isinstance(value, dict):
                    formatted_value = "\n".join(
                        f"  - {k}: {v}" for k, v in value.items()
                    )
                    sections.append(f"{key}:\n{formatted_value}")
                else:
                    sections.append(f"{key}: {value}")

        return "Context Information:\n\n" + "\n\n".join(sections)
```

**Why Complete Implementation**:
- Phase 1 intentionally left ContextService as placeholder
- Phase 2.6 is the natural place to complete it
- Middleware requires functional context persistence
- Maintains Phase 1 service interface

### 6. Middleware Chain Configuration

**Core Approach**: Ordered middleware execution with state passing

```python
# services/agent_service.py (MODIFY from Phase 2.3)

from typing import List, Dict, Any
from middleware.context_middleware import ContextMiddleware
from middleware.memory_middleware import MemoryMiddleware
from middleware.execution_tracking_middleware import ExecutionTrackingMiddleware
from middleware.guardrails_middleware import GuardrailsMiddleware

class AgentService:
    """
    Agent service with custom middleware chain.

    Extends Phase 2.3 implementation with custom middleware.
    """

    def __init__(
        self,
        db: AdaptiveDatabase,
        context_service: ContextService,
        enable_guardrails: bool = False
    ):
        self.db = db
        self.context_service = context_service
        self.agent = None
        self.checkpointer = MemorySaver()

        # Build middleware chain
        self.middleware_chain = self._build_middleware_chain(enable_guardrails)

    def _build_middleware_chain(
        self,
        enable_guardrails: bool
    ) -> List[Any]:
        """
        Build middleware chain in execution order.

        Order matters:
        1. Context loading (before agent needs data)
        2. Execution tracking (before agent runs)
        3. Guardrails (optional - after model, before tools)
        4. Memory persistence (after agent completes)

        Args:
            enable_guardrails: Whether to include guardrails

        Returns:
            Ordered list of middleware instances
        """
        middleware = []

        # Phase 2.5 built-in middleware (if available)
        # These would be added by AgentService initialization
        # middleware.append(PIIRedactionMiddleware())
        # middleware.append(SummarizationMiddleware())

        # Phase 2.6 custom middleware (this task)
        middleware.append(
            ContextMiddleware(
                db=self.db,
                context_service=self.context_service
            )
        )

        middleware.append(
            ExecutionTrackingMiddleware(
                context_service=self.context_service
            )
        )

        if enable_guardrails:
            middleware.append(
                GuardrailsMiddleware(
                    allowed_tools=None,  # None = all tools allowed
                    blocked_patterns=[],
                    max_tool_calls_per_execution=10
                )
            )

        middleware.append(
            MemoryMiddleware(db=self.db)
        )

        return middleware

    async def initialize(
        self,
        model_config: ModelConfig,
        tools: List[Any] = None
    ) -> None:
        """
        Initialize agent with middleware chain.

        Args:
            model_config: Model configuration
            tools: Tool list (from Phase 2.4/2.5)
        """
        llm = self._create_langchain_model(model_config)

        # Create agent with custom middleware chain
        self.agent = create_agent(
            model=llm,
            tools=tools or [],
            middleware=self.middleware_chain,  # ← Custom middleware
            structured_output=AgentResponse,
            checkpointer=self.checkpointer
        )
```

**Why Ordered Chain**:
- Context must load before agent needs it
- Tracking starts before execution
- Guardrails validate after model, before tools
- Memory saves after everything completes
- Clear dependency ordering

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/middleware/
├── context_middleware.py              # Load conversation context
├── memory_middleware.py               # Save responses and tool calls
├── execution_tracking_middleware.py   # Track metrics via ContextService
└── guardrails_middleware.py          # Optional policy enforcement

tests/middleware/
├── test_context_middleware.py        # Context loading tests
├── test_memory_middleware.py         # Memory persistence tests
├── test_execution_tracking_middleware.py  # Metrics tracking tests
└── test_guardrails_middleware.py     # Guardrails validation tests
```

### Files to MODIFY:

```
src/agent_workbench/services/context_service.py
# COMPLETE placeholder implementation from Phase 1
# ADD: Database integration for context persistence
# ADD: Enhanced context prompt formatting
# ADD: Active context source tracking with database

src/agent_workbench/services/agent_service.py
# MODIFY: Add middleware chain configuration
# ADD: _build_middleware_chain() method
# ADD: enable_guardrails parameter

src/agent_workbench/database/backends/sqlite.py
# ADD: save_conversation_context(record: Dict) -> None
# ADD: get_conversation_context(conversation_id: UUID) -> Dict
# ADD: clear_context_source(conversation_id: UUID, source: str) -> None
# ADD: clear_all_context(conversation_id: UUID) -> None
# ADD: store_tool_usage(data: Dict) -> None
# ADD: update_conversation_metadata(conversation_id: UUID, metadata: Dict) -> None

src/agent_workbench/database/backends/hub.py
# ADD: Same context methods as sqlite.py for HF Spaces compatibility

src/agent_workbench/database/protocol.py
# ADD: Context method signatures to DatabaseBackend protocol
```

### Exact Function Signatures:

```python
# ==================== middleware/context_middleware.py ====================

class ContextMiddleware:
    def __init__(self, db: AdaptiveDatabase, context_service: ContextService):
        ...

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Load conversation history, business profile, and context."""
        ...

    async def _load_context_source(
        self,
        conversation_id: UUID,
        source: str
    ) -> Dict[str, Any]:
        """Load specific context source data."""
        ...


# ==================== middleware/memory_middleware.py ====================

class MemoryMiddleware:
    def __init__(self, db: AdaptiveDatabase):
        ...

    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Save assistant response and tool calls."""
        ...

    async def _store_tool_usage(
        self,
        conversation_id: UUID,
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Any,
        success: bool,
        duration_ms: Optional[int]
    ) -> None:
        """Store tool usage for analytics."""
        ...

    async def _update_conversation_metadata(
        self,
        conversation_id: UUID,
        message_count: int,
        last_activity: datetime
    ) -> None:
        """Update conversation-level metadata."""
        ...


# ==================== middleware/execution_tracking_middleware.py ====================

class ExecutionTrackingMiddleware:
    def __init__(self, context_service: ContextService):
        ...

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Record execution start time."""
        ...

    async def before_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Count agent steps."""
        ...

    async def after_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Store execution metrics in ContextService."""
        ...

    async def on_error(
        self,
        error: Exception,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Track error metrics."""
        ...


# ==================== middleware/guardrails_middleware.py ====================

class GuardrailsMiddleware:
    def __init__(
        self,
        allowed_tools: Optional[List[str]] = None,
        blocked_patterns: Optional[List[str]] = None,
        max_tool_calls_per_execution: int = 10
    ):
        ...

    async def after_model(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Validate model response before tool execution."""
        ...

    def _contains_prohibited_content(self, content: str) -> bool:
        """Check if content matches prohibited patterns."""
        ...

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Reset tool call counter."""
        ...


# ==================== services/context_service.py (MODIFY) ====================

class ContextService:
    def __init__(self, db: AdaptiveDatabase):
        """Initialize with database backend."""
        ...

    async def update_conversation_context(
        self,
        conversation_id: UUID,
        context_data: Dict[str, Any],
        sources: List[str]
    ) -> None:
        """Update conversation context with database persistence."""
        ...

    async def clear_conversation_context(
        self,
        conversation_id: UUID,
        source: Optional[str] = None
    ) -> None:
        """Clear conversation context (specific source or all)."""
        ...

    async def get_active_contexts(self, conversation_id: UUID) -> List[str]:
        """Get active context sources from database."""
        ...

    async def build_context_prompt(self, context_data: Dict[str, Any]) -> str:
        """Build formatted context prompt with sections."""
        ...


# ==================== services/agent_service.py (MODIFY) ====================

class AgentService:
    def __init__(
        self,
        db: AdaptiveDatabase,
        context_service: ContextService,
        enable_guardrails: bool = False
    ):
        """Initialize with custom middleware chain."""
        ...

    def _build_middleware_chain(self, enable_guardrails: bool) -> List[Any]:
        """Build ordered middleware chain."""
        ...

    async def initialize(
        self,
        model_config: ModelConfig,
        tools: List[Any] = None
    ) -> None:
        """Initialize agent with middleware chain."""
        ...


# ==================== database/backends/sqlite.py (MODIFY) ====================

class SQLiteBackend:
    async def save_conversation_context(self, record: Dict[str, Any]) -> None:
        """Save conversation context data."""
        ...

    async def get_conversation_context(
        self,
        conversation_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get conversation context data."""
        ...

    async def clear_context_source(
        self,
        conversation_id: UUID,
        source: str
    ) -> None:
        """Clear specific context source."""
        ...

    async def clear_all_context(self, conversation_id: UUID) -> None:
        """Clear all context for conversation."""
        ...

    async def store_tool_usage(self, data: Dict[str, Any]) -> None:
        """Store tool usage data."""
        ...

    async def update_conversation_metadata(
        self,
        conversation_id: UUID,
        metadata: Dict[str, Any]
    ) -> None:
        """Update conversation metadata."""
        ...
```

### Additional Dependencies:

```toml
# pyproject.toml - No new dependencies required
# All middleware uses existing dependencies:
# - langchain (from Phase 2.3)
# - langgraph (from Phase 2.3)
# - sqlalchemy (from Phase 1)
# - aiosqlite (from Phase 1)
```

### FORBIDDEN Actions:

- Implementing built-in middleware (Phase 2.5 - PII, summarization, human-in-the-loop)
- Adding multi-agent coordination (Phase 2.7)
- Implementing agent learning/preferences (Phase 2.7)
- Adding RAG or vector search (Phase 3)
- Creating UI components for middleware configuration
- Modifying Phase 2.3 DebugLoggingMiddleware
- Adding rate limiting or retries (Phase 2.8)
- Implementing cost optimization (Phase 2.8)

## Testing Strategy

### Test Coverage (~12 tests):

```python
# ==================== UNIT TESTS ====================

# tests/middleware/test_context_middleware.py
async def test_context_middleware_loads_conversation_history():
    """Verify conversation history loaded from database."""
    ...

async def test_context_middleware_loads_business_profile_seo_mode():
    """Verify business profile loaded in SEO Coach mode."""
    ...

async def test_context_middleware_skips_business_profile_workbench_mode():
    """Verify business profile not loaded in workbench mode."""
    ...

async def test_context_middleware_injects_context_prompt():
    """Verify context prompt formatted and injected."""
    ...


# tests/middleware/test_memory_middleware.py
async def test_memory_middleware_saves_assistant_message():
    """Verify assistant message saved to database."""
    ...

async def test_memory_middleware_stores_tool_calls():
    """Verify tool calls stored separately."""
    ...

async def test_memory_middleware_updates_conversation_metadata():
    """Verify conversation metadata updated after save."""
    ...


# tests/middleware/test_execution_tracking_middleware.py
async def test_execution_tracking_records_metrics():
    """Verify execution metrics stored in ContextService."""
    ...

async def test_execution_tracking_counts_steps():
    """Verify step counting during execution."""
    ...

async def test_execution_tracking_stores_error_context():
    """Verify error metrics stored on failure."""
    ...


# tests/middleware/test_guardrails_middleware.py
def test_guardrails_blocks_disallowed_tool():
    """Verify guardrails block tools not in allowed list."""
    ...

def test_guardrails_blocks_prohibited_content():
    """Verify prohibited content patterns blocked."""
    ...

def test_guardrails_enforces_tool_call_limit():
    """Verify tool call limit enforced."""
    ...


# ==================== INTEGRATION TESTS ====================

# tests/integration/test_middleware_chain.py
@pytest.mark.integration
async def test_middleware_chain_execution_order():
    """Test middleware executes in correct order."""
    ...

@pytest.mark.integration
async def test_middleware_chain_with_agent():
    """Test complete middleware chain with agent execution."""
    ...

@pytest.mark.integration
async def test_context_service_persistence():
    """Test ContextService stores and retrieves context."""
    ...


# ==================== SERVICE TESTS ====================

# tests/services/test_context_service.py
async def test_context_service_update_conversation_context():
    """Verify context update with database persistence."""
    ...

async def test_context_service_clear_specific_source():
    """Verify clearing specific context source."""
    ...

async def test_context_service_clear_all_context():
    """Verify clearing all context sources."""
    ...

async def test_context_service_build_context_prompt_formatting():
    """Verify context prompt formatting with sections."""
    ...
```

### Test Execution:

```bash
# Run all tests
make test

# Run middleware tests only
uv run pytest tests/middleware/ -v

# Run integration tests with backend
make test-with-backend

# Check test coverage
uv run pytest --cov=src/agent_workbench/middleware/
uv run pytest --cov=src/agent_workbench/services/context_service.py
```

## Success Criteria

### Functional Requirements:

- [ ] **Context Loading**: Conversation history loaded before agent execution
- [ ] **Business Profile**: SEO Coach mode loads business profile correctly
- [ ] **Context Prompt**: Context formatted and injected into agent state
- [ ] **Response Persistence**: Assistant responses saved to database after execution
- [ ] **Tool Usage Tracking**: Tool calls stored separately for analytics
- [ ] **Execution Metrics**: Metrics tracked and stored via ContextService
- [ ] **Error Context**: Error metrics stored on execution failures
- [ ] **Guardrails Optional**: Guardrails can be enabled/disabled per workflow

### ContextService Requirements:

- [ ] **Placeholder Complete**: All Phase 1 placeholder methods implemented
- [ ] **Database Integration**: Context persisted to database
- [ ] **Source Tracking**: Active context sources tracked correctly
- [ ] **Prompt Formatting**: Context prompts formatted with sections
- [ ] **Multi-Source**: Supports multiple context sources per conversation

### Middleware Chain Requirements:

- [ ] **Correct Order**: Middleware executes in dependency order
- [ ] **State Passing**: State correctly passed between middleware
- [ ] **Error Propagation**: Errors propagate correctly through chain
- [ ] **Built-in Integration**: Compatible with Phase 2.5 built-in middleware

### Technical Requirements:

- [ ] **Type Safety**: All code passes mypy strict checks
- [ ] **Test Coverage**: >90% coverage for all middleware classes
- [ ] **Database Compatibility**: Works with both SQLite and Hub backends
- [ ] **Backward Compatibility**: Phase 1 workflows still work
- [ ] **No Breaking Changes**: Agent service API unchanged

### Performance Requirements:

- [ ] **Context Load Time**: Context loading adds <200ms overhead
- [ ] **Memory Save Time**: Response saving adds <100ms overhead
- [ ] **Metrics Tracking**: Tracking adds <50ms overhead
- [ ] **Total Overhead**: Combined middleware adds <500ms overhead

### Integration Requirements:

- [ ] **Phase 1 Integration**: Uses Phase 1 database and models
- [ ] **Phase 2.3 Integration**: Works with Phase 2.3 agent service
- [ ] **Phase 2.4/2.5 Integration**: Compatible with tools and built-in middleware
- [ ] **No Conflicts**: No conflicts between custom and built-in middleware

---

## Phase 2.6 Checklist

Before marking this task complete, verify:

- [ ] `ContextMiddleware` created and tested
- [ ] `MemoryMiddleware` created and tested
- [ ] `ExecutionTrackingMiddleware` created and tested
- [ ] `GuardrailsMiddleware` created (optional)
- [ ] Phase 1 `ContextService` placeholder implementation completed
- [ ] Database backends support context persistence methods
- [ ] `AgentService` builds middleware chain
- [ ] Middleware chain executes in correct order
- [ ] Context loaded before agent execution
- [ ] Responses saved after agent execution
- [ ] Execution metrics stored in ContextService
- [ ] No middleware conflicts
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Type checking passes (mypy)
- [ ] Documentation updated

**Expected Behavior After Phase 2.6**:
- Context automatically loaded from database before each agent execution
- Conversation history and business profiles injected into agent state
- Agent responses automatically saved to database after execution
- Execution metrics tracked and stored for performance monitoring
- Optional guardrails validate tool calls and responses
- Phase 1 ContextService fully functional with database persistence

**Next Phase (2.7)**: Multi-agent coordination and agent learning
