# AGENT-002: LangChain v1 Built-in Middleware Configuration

## Status

**Status**: Ready for Implementation
**Date**: October 13, 2025
**Decision Makers**: Human Architect
**Task ID**: AGENT-002-v1-langchain-middleware
**Phase**: 2.5
**Dependencies**: Phase 2.4 (TOOL-001: ContentRetriever Tool)

## Context

Phase 2.5 configures **LangChain v1's built-in middleware** for the agent created in Phase 2.3. This adds production-ready capabilities for PII protection, conversation summarization, and human oversight of sensitive operations.

**Critical Context:**
- This phase implements ONLY **built-in LangChain v1 middleware** (NOT custom middleware)
- Custom middleware (ContextMiddleware, MemoryMiddleware, etc.) comes in **Phase 2.6**
- Agent from Phase 2.3 already has structure; this phase adds middleware to it
- ContentRetriever tool from Phase 2.4 remains; middleware wraps it
- Focus is on **correct configuration**, not implementation

**Phase 2.4 → Phase 2.5 Transition:**
Phase 2.4 gave the agent its first tool (ContentRetriever). Phase 2.5 adds middleware to protect and enhance that tool:
- Phase 2.4: Agent has ContentRetriever tool, no middleware protection
- Phase 2.5: Agent has ContentRetriever + built-in middleware for PII, summarization, human approval
- Phase 2.6: Agent gets custom middleware for context and memory

**Why This Matters:**
Production agents need safeguards. Built-in middleware provides:
- **PII Redaction**: Automatic redaction of sensitive data (emails, SSNs, credit cards)
- **Summarization**: Automatic conversation compression when approaching token limits
- **Human-in-the-Loop**: Required approval for sensitive operations

## Architecture Scope

### What's Included:

- Configuration of `PIIRedactionMiddleware` from LangChain v1
- Configuration of `SummarizationMiddleware` from LangChain v1
- Configuration of `HumanInTheLoopMiddleware` from LangChain v1
- Middleware configuration file (`config/middleware.py`)
- Middleware execution order (PII → Summarization → Human-in-Loop → Custom)
- Integration with Phase 2.3 debug logging
- Testing each middleware independently
- Testing middleware chain execution

### What's Explicitly Excluded:

- Custom middleware implementation (Phase 2.6)
- ContextMiddleware (Phase 2.6)
- MemoryMiddleware (Phase 2.6)
- ExecutionTrackingMiddleware (Phase 2.6)
- GuardrailsMiddleware (Phase 2.6)
- Multi-agent coordination (out of scope)
- Advanced RAG capabilities (Phase 3+)
- Vector database integration (Phase 3+)
- Authentication or authorization (Phase 2.1)

## Architectural Decisions

### 1. Built-in Middleware: Three Core Types

**Core Approach**: Configure LangChain v1's production-ready middleware correctly

**Three Built-in Middleware:**

| Middleware | Purpose | Configuration |
|------------|---------|---------------|
| PIIRedactionMiddleware | Redact sensitive data | Patterns for email, phone, SSN, credit cards |
| SummarizationMiddleware | Compress long conversations | Token threshold, model selection |
| HumanInTheLoopMiddleware | Pause for human approval | List of sensitive operations |

**Implementation Pattern:**
```python
# services/agent_service.py (MODIFY)

from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIRedactionMiddleware,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware
)
from config.middleware import MIDDLEWARE_CONFIG

class AgentService:
    """Agent service with built-in middleware."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.content_retriever = None

    async def initialize(self):
        """Initialize agent with built-in middleware."""

        # Create ContentRetriever tool (from Phase 2.4)
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

        # Configure built-in middleware
        middleware = self._create_middleware_chain()

        # Create agent with tools AND middleware
        self.agent = create_agent(
            model=get_model(),
            tools=[self.content_retriever],
            middleware=middleware,  # ← NEW: Add middleware
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

    def _create_middleware_chain(self) -> List[Any]:
        """Create ordered middleware chain."""

        middleware = []

        # 1. PII Redaction (first - protect data throughout)
        if MIDDLEWARE_CONFIG["pii_redaction"]["enabled"]:
            middleware.append(
                PIIRedactionMiddleware(
                    patterns=MIDDLEWARE_CONFIG["pii_redaction"]["patterns"]
                )
            )

        # 2. Summarization (second - reduce tokens before processing)
        if MIDDLEWARE_CONFIG["summarization"]["enabled"]:
            middleware.append(
                SummarizationMiddleware(
                    model=get_model(MIDDLEWARE_CONFIG["summarization"]["model"]),
                    max_tokens_before_summary=MIDDLEWARE_CONFIG["summarization"]["max_tokens"]
                )
            )

        # 3. Human-in-the-Loop (third - final approval gate)
        if MIDDLEWARE_CONFIG["human_in_loop"]["enabled"]:
            middleware.append(
                HumanInTheLoopMiddleware(
                    interrupt_on=MIDDLEWARE_CONFIG["human_in_loop"]["interrupt_on"]
                )
            )

        # 4. Debug Logging (last - from Phase 2.3, log everything)
        middleware.append(DebugLoggingMiddleware(db=self.db))

        return middleware
```

### 2. PIIRedactionMiddleware Configuration

**Purpose**: Automatically redact sensitive data in logs and API calls

**Configuration Strategy:**
```python
# config/middleware.py (CREATE)

MIDDLEWARE_CONFIG = {
    "pii_redaction": {
        "enabled": True,
        "patterns": [
            "email",           # user@example.com → [EMAIL_REDACTED]
            "phone",           # (555) 123-4567 → [PHONE_REDACTED]
            "ssn",             # 123-45-6789 → [SSN_REDACTED]
            "credit_card",     # 4532-1234-5678-9010 → [CC_REDACTED]
        ]
    }
}
```

**What Gets Redacted:**
- User input: Before agent sees it
- Agent responses: Before logging
- Tool calls: Before execution
- Debug logs: Before database storage

**Pattern Details:**
- **Email**: Matches RFC 5322 email format
- **Phone**: Matches international formats (+1-555-123-4567, (555) 123-4567, etc.)
- **SSN**: Matches US Social Security Number (123-45-6789, 123456789)
- **Credit Card**: Matches major card formats (Visa, Mastercard, Amex)

**Testing:**
```python
# Test: PII redacted in logs
messages = [{"role": "user", "content": "My email is john@example.com"}]
result = await agent_service.run(messages, {}, "test-task")

# Check logs: email should be redacted
logs = await db.get_execution_logs(task_id="test-task")
assert "[EMAIL_REDACTED]" in logs[0]["user_message"]
assert "john@example.com" not in logs[0]["user_message"]
```

### 3. SummarizationMiddleware Configuration

**Purpose**: Automatically compress conversations when approaching token limits

**Configuration Strategy:**
```python
# config/middleware.py (in MIDDLEWARE_CONFIG)

"summarization": {
    "enabled": True,
    "max_tokens": 8000,  # Trigger summarization at 8K tokens
    "model": "anthropic:claude-sonnet-4-5-20250929"  # Model for summarization
}
```

**How It Works:**
1. Middleware tracks token count in conversation history
2. When history exceeds `max_tokens`, triggers summarization
3. Summarization model creates concise summary of old messages
4. Summary replaces old messages, preserving recent context
5. Agent continues with compressed history

**Token Counting:**
- Counts tokens in conversation history (not single message)
- Uses model-specific tokenizer for accuracy
- Monitors across multiple turns

**Testing:**
```python
# Test: Long conversation triggers summarization
messages = []
for i in range(100):  # Create long conversation
    messages.append({"role": "user", "content": f"Question {i}: Tell me about topic {i}"})
    messages.append({"role": "assistant", "content": f"Answer {i}: Here's info about topic {i}"})

# When run, should trigger summarization
result = await agent_service.run(messages, {}, "long-task")

# Verify summarization occurred
logs = await db.get_execution_logs(task_id="long-task")
assert "summarization_triggered" in logs[0]["metadata"]
```

### 4. HumanInTheLoopMiddleware Configuration

**Purpose**: Pause agent execution for human approval of sensitive operations

**Configuration Strategy:**
```python
# config/middleware.py (in MIDDLEWARE_CONFIG)

"human_in_loop": {
    "enabled": True,
    "interrupt_on": {
        "send_email": ["approve", "edit", "reject"],      # Email requires approval
        "delete_file": ["approve", "reject"],              # File deletion requires approval
        "execute_code": ["approve", "edit", "reject"],     # Code execution requires approval
    }
}
```

**Approval Flow:**
1. Agent decides to call sensitive tool (e.g., `send_email`)
2. Middleware intercepts tool call
3. Execution pauses, returns approval request to user
4. User approves/edits/rejects
5. If approved, tool executes; if rejected, agent informed

**Response Format:**
```python
# When approval needed, agent returns:
{
    "status": "pending_approval",
    "tool_call": {
        "name": "send_email",
        "args": {
            "to": "user@example.com",
            "subject": "Report",
            "body": "Here's the report you requested."
        }
    },
    "approval_options": ["approve", "edit", "reject"]
}

# After user approves:
# Agent continues with tool execution
```

**Testing:**
```python
# Test: Sensitive operation pauses for approval
messages = [{"role": "user", "content": "Send an email to john@example.com"}]
result = await agent_service.run(messages, {}, "approval-task")

# Should pause for approval
assert result["status"] == "pending_approval"
assert result["tool_call"]["name"] == "send_email"

# Simulate approval
result = await agent_service.continue_with_approval(
    task_id="approval-task",
    approval="approve"
)

# Now should complete
assert result["status"] == "completed"
```

**Note on Phase 2.5 Scope:**
- In Phase 2.5, ContentRetriever is NOT a sensitive operation (no approval required)
- Approval configuration prepared for future tools (Phase 2.7+)
- Testing approval flow with mock sensitive tools

### 5. Middleware Execution Order

**Critical Pattern**: Order matters for middleware execution

**Correct Order:**
1. **PIIRedactionMiddleware** (FIRST)
   - Redacts PII before any other middleware sees data
   - Protects sensitive data throughout entire chain

2. **SummarizationMiddleware** (SECOND)
   - Compresses conversation before expensive processing
   - Reduces tokens for model calls

3. **HumanInTheLoopMiddleware** (THIRD)
   - Final approval gate before tool execution
   - Operates on already-redacted, summarized data

4. **DebugLoggingMiddleware** (LAST - from Phase 2.3)
   - Logs everything after all processing
   - Captures final state for debugging

**Why This Order:**
```python
# Example flow:
# User input: "My SSN is 123-45-6789, send it to john@example.com"

# 1. PIIRedactionMiddleware
# → "My SSN is [SSN_REDACTED], send it to [EMAIL_REDACTED]"

# 2. SummarizationMiddleware
# → (If needed) Compresses old messages, keeps recent

# 3. HumanInTheLoopMiddleware
# → (If send_email tool called) Pauses for approval

# 4. DebugLoggingMiddleware
# → Logs final state with redacted PII
```

**Implementation:**
```python
def _create_middleware_chain(self) -> List[Any]:
    """Create ordered middleware chain."""
    return [
        PIIRedactionMiddleware(...),        # 1st: Protect data
        SummarizationMiddleware(...),       # 2nd: Reduce tokens
        HumanInTheLoopMiddleware(...),      # 3rd: Approval gate
        DebugLoggingMiddleware(db=self.db)  # 4th: Log everything
    ]
```

### 6. Integration with Phase 2.3 Debug Logging

**Seamless Integration**: Built-in middleware works with existing debug logging

**DebugLoggingMiddleware Enhancement:**
```python
# middleware/debug_logging_middleware.py (MODIFY from Phase 2.3)

class DebugLoggingMiddleware:
    """Enhanced to track middleware chain execution."""

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Track middleware chain start."""
        self._middleware_start_time = time.time()
        self._middleware_chain = []
        return state

    async def after_agent(self, result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Log middleware chain execution."""

        # Existing logging (from Phase 2.3)
        await self._log_execution(result, context)

        # NEW: Log middleware chain
        await self._log_middleware_execution(
            execution_log_id=context["execution_log_id"],
            middleware_chain=self._middleware_chain,
            total_duration=time.time() - self._middleware_start_time
        )

    async def _log_middleware_execution(
        self,
        execution_log_id: UUID,
        middleware_chain: List[str],
        total_duration: float
    ) -> None:
        """Log which middleware executed and timing."""

        # Add to execution log metadata
        await self.db.update_execution_log(
            execution_log_id=execution_log_id,
            metadata={
                "middleware_chain": middleware_chain,
                "middleware_duration_ms": total_duration * 1000
            }
        )
```

**Querying Middleware Execution:**
```python
# Check which middleware executed
logs = await db.get_execution_logs(limit=100)

for log in logs:
    middleware_chain = log["metadata"].get("middleware_chain", [])
    print(f"Task {log['task_id']} used middleware: {middleware_chain}")

    # Check if PII redaction triggered
    if "PIIRedactionMiddleware" in middleware_chain:
        print("  → PII was redacted")

    # Check if summarization triggered
    if "SummarizationMiddleware" in middleware_chain:
        print("  → Conversation was summarized")

    # Check if approval required
    if "HumanInTheLoopMiddleware" in middleware_chain:
        print("  → Human approval was required")
```

## Implementation Boundaries for AI

### Files to CREATE:

```
src/agent_workbench/config/
└── middleware.py                       # Middleware configuration (MIDDLEWARE_CONFIG)
```

### Files to MODIFY:

```
src/agent_workbench/services/
└── agent_service.py                    # Add middleware to agent initialization

src/agent_workbench/middleware/
└── debug_logging_middleware.py         # Enhance to track middleware chain
```

### Exact Function Signatures:

```python
# CREATE: config/middleware.py

from typing import Dict, Any, List

MIDDLEWARE_CONFIG: Dict[str, Any] = {
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


# MODIFY: services/agent_service.py
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIRedactionMiddleware,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware
)
from config.middleware import MIDDLEWARE_CONFIG
from typing import List, Dict, Any, Optional

class AgentService:
    """Agent service with built-in middleware chain."""

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self.agent = None
        self.content_retriever = None

    async def initialize(self):
        """Initialize agent with built-in middleware."""
        # Existing: Create ContentRetriever tool (from Phase 2.4)
        self.content_retriever = ContentRetrieverTool(model_name="all-MiniLM-L6-v2")

        # NEW: Configure middleware chain
        middleware = self._create_middleware_chain()

        # MODIFY: Add middleware to agent
        self.agent = create_agent(
            model=get_model(),
            tools=[self.content_retriever],
            middleware=middleware,  # ← NEW: Add middleware
            structured_output=AgentResponse,
            checkpointer=MemorySaver()
        )

    # NEW: Create middleware chain
    def _create_middleware_chain(self) -> List[Any]:
        """
        Create ordered middleware chain.

        Order matters:
        1. PII Redaction (protect data first)
        2. Summarization (reduce tokens)
        3. Human-in-Loop (approval gate)
        4. Debug Logging (log everything)

        Returns:
            List of middleware instances in execution order
        """
        middleware = []

        # 1. PII Redaction
        if MIDDLEWARE_CONFIG["pii_redaction"]["enabled"]:
            middleware.append(
                PIIRedactionMiddleware(
                    patterns=MIDDLEWARE_CONFIG["pii_redaction"]["patterns"]
                )
            )

        # 2. Summarization
        if MIDDLEWARE_CONFIG["summarization"]["enabled"]:
            middleware.append(
                SummarizationMiddleware(
                    model=get_model(MIDDLEWARE_CONFIG["summarization"]["model"]),
                    max_tokens_before_summary=MIDDLEWARE_CONFIG["summarization"]["max_tokens"]
                )
            )

        # 3. Human-in-the-Loop
        if MIDDLEWARE_CONFIG["human_in_loop"]["enabled"]:
            middleware.append(
                HumanInTheLoopMiddleware(
                    interrupt_on=MIDDLEWARE_CONFIG["human_in_loop"]["interrupt_on"]
                )
            )

        # 4. Debug Logging (from Phase 2.3)
        middleware.append(DebugLoggingMiddleware(db=self.db))

        return middleware

    # NEW: Handle approval flow
    async def continue_with_approval(
        self,
        task_id: str,
        approval: str,
        edited_args: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Continue agent execution after human approval.

        Args:
            task_id: Task waiting for approval
            approval: "approve", "edit", or "reject"
            edited_args: If approval == "edit", the modified tool args

        Returns:
            Completed agent result
        """
        # Implementation: Resume agent with approval decision
        pass


# MODIFY: middleware/debug_logging_middleware.py
import time
from typing import Dict, Any, List
from uuid import UUID

class DebugLoggingMiddleware:
    """
    Debug logging middleware with middleware chain tracking.

    Enhanced from Phase 2.3 to track middleware execution.
    """

    def __init__(self, db: AdaptiveDatabase):
        self.db = db
        self._middleware_start_time: float = 0.0
        self._middleware_chain: List[str] = []

    async def before_agent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Track middleware chain start."""
        self._middleware_start_time = time.time()
        self._middleware_chain = []

        # Existing Phase 2.3 logic
        # ...

        return state

    async def after_agent(self, result: Dict[str, Any], context: Dict[str, Any]) -> None:
        """Log middleware chain execution."""

        # Existing Phase 2.3 logging
        await self._log_execution(result, context)

        # NEW: Log middleware chain
        await self._log_middleware_execution(
            execution_log_id=context["execution_log_id"],
            middleware_chain=self._middleware_chain,
            total_duration=time.time() - self._middleware_start_time
        )

    # NEW: Log middleware execution
    async def _log_middleware_execution(
        self,
        execution_log_id: UUID,
        middleware_chain: List[str],
        total_duration: float
    ) -> None:
        """
        Log which middleware executed and timing.

        Args:
            execution_log_id: Execution log to update
            middleware_chain: List of middleware names that executed
            total_duration: Total middleware execution time in seconds
        """
        await self.db.update_execution_log(
            execution_log_id=execution_log_id,
            metadata={
                "middleware_chain": middleware_chain,
                "middleware_duration_ms": total_duration * 1000
            }
        )
```

### Additional Dependencies:

```toml
# Already in project from Phase 2.3
langchain = "^1.0.0"  # Includes middleware
```

**No new dependencies required** - built-in middleware comes with LangChain v1.0.

### FORBIDDEN Actions:

- Implementing custom middleware (wait for Phase 2.6)
- Creating ContextMiddleware (Phase 2.6)
- Creating MemoryMiddleware (Phase 2.6)
- Creating ExecutionTrackingMiddleware (Phase 2.6)
- Modifying Phase 2.4 ContentRetriever tool
- Changing agent structure from Phase 2.3
- Breaking backward compatibility with Phase 2.3 debug logging
- Adding new tools (wait for Phase 2.7)

## Testing Strategy

Comprehensive testing for built-in middleware configuration and execution:

### Unit Tests (~5 tests)

```python
# tests/services/test_agent_middleware.py

import pytest
from services.agent_service import AgentService
from database.adapter import AdaptiveDatabase
from config.middleware import MIDDLEWARE_CONFIG

class TestAgentMiddleware:
    """Test built-in middleware configuration."""

    @pytest.fixture
    async def agent_service(self, adaptive_db):
        """Create and initialize agent service."""
        service = AgentService(db=adaptive_db)
        await service.initialize()
        return service

    def test_middleware_chain_created(self, agent_service):
        """Test that middleware chain is created with correct order."""
        middleware = agent_service._create_middleware_chain()

        # Should have 4 middleware (PII, Summarization, HumanInLoop, Debug)
        assert len(middleware) >= 3  # At least built-in middleware

        # Check order (by class name)
        class_names = [m.__class__.__name__ for m in middleware]

        # PII should be first
        assert "PIIRedactionMiddleware" in class_names
        pii_index = class_names.index("PIIRedactionMiddleware")

        # Debug should be last
        assert "DebugLoggingMiddleware" in class_names
        debug_index = class_names.index("DebugLoggingMiddleware")

        # PII before Debug
        assert pii_index < debug_index

    @pytest.mark.asyncio
    async def test_pii_redaction_in_logs(self, agent_service, adaptive_db):
        """Test that PII is redacted in debug logs."""
        messages = [
            {"role": "user", "content": "My email is john@example.com"}
        ]

        result = await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="pii-test"
        )

        # Check logs: email should be redacted
        logs = await adaptive_db.get_execution_logs(task_id="pii-test")
        assert len(logs) > 0

        user_message = logs[0]["user_message"]
        assert "[EMAIL_REDACTED]" in user_message or "john@example.com" not in user_message

    @pytest.mark.asyncio
    async def test_summarization_threshold(self, agent_service):
        """Test that summarization is configured with correct threshold."""
        middleware = agent_service._create_middleware_chain()

        # Find SummarizationMiddleware
        summarization = None
        for m in middleware:
            if m.__class__.__name__ == "SummarizationMiddleware":
                summarization = m
                break

        assert summarization is not None
        assert summarization.max_tokens_before_summary == MIDDLEWARE_CONFIG["summarization"]["max_tokens"]

    @pytest.mark.asyncio
    async def test_human_in_loop_configured(self, agent_service):
        """Test that human-in-loop is configured with sensitive operations."""
        middleware = agent_service._create_middleware_chain()

        # Find HumanInTheLoopMiddleware
        hitl = None
        for m in middleware:
            if m.__class__.__name__ == "HumanInTheLoopMiddleware":
                hitl = m
                break

        assert hitl is not None
        assert "send_email" in hitl.interrupt_on
        assert "delete_file" in hitl.interrupt_on

    @pytest.mark.asyncio
    async def test_middleware_chain_logged(self, agent_service, adaptive_db):
        """Test that middleware chain execution is logged."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="middleware-log-test"
        )

        # Check logs for middleware chain
        logs = await adaptive_db.get_execution_logs(task_id="middleware-log-test")
        assert len(logs) > 0

        metadata = logs[0]["metadata"]
        assert "middleware_chain" in metadata
        assert isinstance(metadata["middleware_chain"], list)
        assert len(metadata["middleware_chain"]) > 0


# tests/config/test_middleware_config.py

import pytest
from config.middleware import MIDDLEWARE_CONFIG

class TestMiddlewareConfig:
    """Test middleware configuration."""

    def test_config_structure(self):
        """Test that config has required structure."""
        assert "pii_redaction" in MIDDLEWARE_CONFIG
        assert "summarization" in MIDDLEWARE_CONFIG
        assert "human_in_loop" in MIDDLEWARE_CONFIG

    def test_pii_redaction_config(self):
        """Test PII redaction configuration."""
        pii_config = MIDDLEWARE_CONFIG["pii_redaction"]

        assert "enabled" in pii_config
        assert "patterns" in pii_config
        assert isinstance(pii_config["patterns"], list)
        assert "email" in pii_config["patterns"]

    def test_summarization_config(self):
        """Test summarization configuration."""
        summary_config = MIDDLEWARE_CONFIG["summarization"]

        assert "enabled" in summary_config
        assert "max_tokens" in summary_config
        assert "model" in summary_config
        assert isinstance(summary_config["max_tokens"], int)
        assert summary_config["max_tokens"] > 0

    def test_human_in_loop_config(self):
        """Test human-in-loop configuration."""
        hitl_config = MIDDLEWARE_CONFIG["human_in_loop"]

        assert "enabled" in hitl_config
        assert "interrupt_on" in hitl_config
        assert isinstance(hitl_config["interrupt_on"], dict)

        # Check sensitive operations configured
        assert "send_email" in hitl_config["interrupt_on"]
        assert "delete_file" in hitl_config["interrupt_on"]
```

### Integration Tests (~3 tests)

```python
# tests/integration/test_middleware_chain.py

import pytest
from services.agent_service import AgentService
from database.adapter import AdaptiveDatabase

class TestMiddlewareChain:
    """Test middleware chain integration."""

    @pytest.fixture
    async def agent_service(self, adaptive_db):
        """Create and initialize agent service."""
        service = AgentService(db=adaptive_db)
        await service.initialize()
        return service

    @pytest.mark.asyncio
    async def test_full_middleware_chain_execution(self, agent_service, adaptive_db):
        """Test that all middleware execute in correct order."""
        messages = [
            {"role": "user", "content": "Test message"}
        ]

        result = await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="chain-test"
        )

        # Verify execution
        assert "messages" in result

        # Check logs: middleware chain should be logged
        logs = await adaptive_db.get_execution_logs(task_id="chain-test")
        assert len(logs) > 0

        metadata = logs[0]["metadata"]
        assert "middleware_chain" in metadata

        # Verify order
        chain = metadata["middleware_chain"]
        pii_index = chain.index("PIIRedactionMiddleware") if "PIIRedactionMiddleware" in chain else -1
        debug_index = chain.index("DebugLoggingMiddleware") if "DebugLoggingMiddleware" in chain else -1

        if pii_index >= 0 and debug_index >= 0:
            assert pii_index < debug_index

    @pytest.mark.asyncio
    async def test_middleware_with_content_retriever_tool(self, agent_service, sample_files):
        """Test that middleware works with ContentRetriever tool."""
        messages = [
            {"role": "user", "content": "Read the file"}
        ]

        result = await agent_service.run(
            messages=messages,
            user_settings={},
            task_id="middleware-tool-test",
            uploaded_files=[str(sample_files["text"])]
        )

        # Should work normally with middleware
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_middleware_does_not_break_phase_2_4(self, agent_service, adaptive_db):
        """Test that middleware doesn't break Phase 2.4 ContentRetriever."""
        # Verify ContentRetriever still works
        assert agent_service.content_retriever is not None

        # Verify tool is in agent
        assert len(agent_service.agent.tools) > 0
        assert any(tool.name == "content_retriever" for tool in agent_service.agent.tools)
```

### Test Execution:

```bash
# Run middleware configuration tests
uv run pytest tests/config/test_middleware_config.py -v

# Run middleware service tests
uv run pytest tests/services/test_agent_middleware.py -v

# Run middleware integration tests
uv run pytest tests/integration/test_middleware_chain.py -v

# Full test suite (ensure no regressions)
make test
```

## Success Criteria

Phase 2.5 is complete when ALL of the following are verified:

### Functional Requirements:

- [ ] **PIIRedactionMiddleware Configured**: Email, phone, SSN, credit card patterns configured
- [ ] **SummarizationMiddleware Configured**: Token threshold and model configured
- [ ] **HumanInTheLoopMiddleware Configured**: Sensitive operations defined
- [ ] **Middleware Chain Created**: All three built-in middleware in correct order
- [ ] **PII Automatically Redacted**: Sensitive data redacted in logs and API calls
- [ ] **Middleware Execution Logged**: Middleware chain tracked in debug logs
- [ ] **No Phase 2.4 Regressions**: ContentRetriever tool still works
- [ ] **Middleware Order Correct**: PII → Summarization → HumanInLoop → Debug

### Quality Requirements:

- [ ] **Test Coverage**: >85% coverage for new code
- [ ] **All Tests Pass**: Unit tests + integration tests pass
- [ ] **Type Checking**: `make quality` passes with no mypy errors
- [ ] **No Regressions**: Phase 2.3 and 2.4 functionality still works
- [ ] **Config Validation**: Middleware config loads without errors
- [ ] **Performance**: No significant performance degradation (<10% slower)

### Documentation Requirements:

- [ ] **Middleware Configuration**: MIDDLEWARE_CONFIG documented
- [ ] **PII Patterns**: List of redacted patterns documented
- [ ] **Approval Flow**: Human-in-loop approval flow documented
- [ ] **Middleware Order**: Execution order and rationale documented

### Integration Requirements:

- [ ] **Phase 2.3 Debug Logs Work**: Middleware chain appears in execution logs
- [ ] **Phase 2.4 ContentRetriever Works**: Tool still functions with middleware
- [ ] **No Breaking Changes**: Existing agent functionality preserved
- [ ] **Config File Created**: `config/middleware.py` exists and loads

### Validation Commands:

```bash
# Code quality
make quality

# Full test suite
make test

# Specific Phase 2.5 tests
uv run pytest tests/config/ tests/services/test_agent_middleware.py -v

# Integration validation
uv run pytest tests/integration/test_middleware_chain.py -v

# Manual validation
make start-app-debug  # Check logs for middleware execution
```

### Ready for Phase 2.6 When:

- All success criteria above are met
- Built-in middleware configured and executing correctly
- PII redaction working in logs
- Middleware chain logged in execution logs
- No errors in test suite
- Documentation updated
- Phase 2.3 and 2.4 functionality preserved

**Next Phase:** Phase 2.6 implements custom middleware (ContextMiddleware, MemoryMiddleware, ExecutionTrackingMiddleware, GuardrailsMiddleware) that integrates with Phase 1 services.
