# Phase 2 Testing Strategy

**Date:** 2025-10-13
**Status:** Planning
**Based On:** Phase 2 Architecture Plan + Phase 1 Test Coverage

---

## Testing Philosophy

**Key Principles:**
1. **Leverage Pydantic validation** - No low-level validation tests needed
2. **Reuse Phase 1 test patterns** - Messages and conversations already tested
3. **Focus on NEW functionality** - Authentication, agents, tools, middleware
4. **Integration over unit** - Test real workflows, not internal details
5. **Contract tests for LangChain v1** - API may change in alpha/beta

---

## What NOT to Test (Already Covered)

### Phase 1 Coverage (Reusable)
✅ **StandardMessage validation** - Pydantic handles it
✅ **ConversationState CRUD** - Tested in Phase 1
✅ **WorkbenchState schema** - TypedDict validated
✅ **Database backends** - SQLite + Hub tested
✅ **LangGraph Bridge** - State conversion tested
✅ **Gradio mounting** - 6/6 tests pass (test_gradio_unified.py)
✅ **Message/Conversation CRUD** - Full coverage in Phase 1

### Pydantic Auto-Validation (No Tests Needed)
✅ **AgentResponse structured outputs** - Pydantic enforces schema
✅ **UserModel fields** - SQLAlchemy + Pydantic validation
✅ **UserSettingModel JSON** - Pydantic handles JSON schema
✅ **Tool arguments** - LangChain validates via Pydantic

---

## Phase 2 Test Coverage by Component

### Phase 2.0: User Authentication & Settings

**NEW Components:**
- UserModel, UserSettingModel, UserSessionModel
- AuthService with HF OAuth
- Session management (reuse logic)
- Database indexes

**Tests Required:**

#### Integration Tests (Priority: HIGH)
```python
# tests/integration/test_auth_flow.py

async def test_user_authentication_flow():
    """Test complete HF OAuth flow."""
    # Mock Gradio Request with username
    # Call get_or_create_user_from_request
    # Verify user created in DB
    # Verify last_login updated on second call

async def test_session_reuse_prevents_pollution():
    """Test session reuse logic (30min timeout)."""
    # Create user
    # Create session
    # Simulate page refresh within 30min
    # Verify same session returned
    # Verify last_activity updated
    # Simulate page refresh after 30min
    # Verify new session created

async def test_user_settings_persistence():
    """Test settings CRUD operations."""
    # Create user
    # Save setting (active)
    # Load setting
    # Update setting
    # Verify persistence across sessions
```

#### Database Tests (Priority: MEDIUM)
```python
# tests/unit/database/test_user_models.py

def test_get_active_user_session_uses_index():
    """Verify idx_execution_logs_user_status used."""
    # Use SQLAlchemy EXPLAIN to verify index usage
    # Assert query plan uses composite index

def test_session_activity_update():
    """Test update_session_activity method."""
    # Create session
    # Update activity
    # Verify timestamp changed
```

**Test Count: ~8 tests**

---

### Phase 2.1: PWA App with User Settings

**NEW Components:**
- PWA manifest.json
- Service worker
- Settings page UI
- Share target handler

**Tests Required:**

#### E2E Tests (Priority: HIGH)
```python
# tests/e2e/test_pwa_installation.py

def test_pwa_manifest_valid():
    """Validate manifest.json structure."""
    # Load manifest.json
    # Verify all required fields present
    # Verify icon paths exist
    # Verify screenshot dimensions correct

async def test_share_target_handler():
    """Test sharing content to app."""
    # POST to /share with title, text, url
    # Verify redirect to chat with pre-filled message
    # Test file upload via share target
```

#### UI Integration Tests (Priority: MEDIUM)
```python
# tests/ui/test_settings_page.py

def test_settings_page_renders():
    """Test settings page UI."""
    # Launch settings page
    # Verify all 4 tabs present
    # Verify model/provider dropdowns work
    # Verify save button updates database

def test_minimal_chat_interface():
    """Test Ollama-style chat UI."""
    # Verify model selector in bottom-right
    # Verify no config controls in chat
    # Verify navigation to settings works
```

**Test Count: ~6 tests**

---

### Phase 2.2: Enhanced Gradio UI (Stubbed)

**NEW Components:**
- File upload UI (stubbed)
- Approval dialog (stubbed)
- Document processor stubs

**Tests Required:**

#### UI Tests (Priority: LOW - Stubs Only)
```python
# tests/ui/test_file_ui_stubs.py

def test_file_upload_ui_renders():
    """Test file upload component visible."""
    # Verify file upload button exists
    # Verify stub message displayed

def test_approval_dialog_stub():
    """Test approval dialog auto-approves."""
    # Trigger approval flow
    # Verify auto-approval
    # Verify stub warning logged
```

**Test Count: ~3 tests (minimal for stubs)**

---

### Phase 2.3: Basic Agent Service + Debug Logging

**NEW Components:**
- AgentService with create_agent()
- AgentExecutionLogModel, ToolCallLogModel
- DebugLoggingMiddleware
- AnalyticsService

**Tests Required:**

#### Integration Tests (Priority: CRITICAL)
```python
# tests/integration/test_agent_service.py

async def test_agent_responds_without_tools():
    """Test minimal agent with NO tools."""
    # Initialize AgentService
    # Send basic question
    # Verify response received
    # Verify NO tool calls
    # Verify debug log created

async def test_agent_structured_output():
    """Test structured response validation."""
    # Send message to agent
    # Verify result["structured_response"] is AgentResponse
    # Verify Pydantic model validated
    # Access via repr() for debugging

async def test_debug_logging_captures_execution():
    """Test execution logged to database."""
    # Execute agent query
    # Query AgentExecutionLogModel
    # Verify all fields populated
    # Verify timing recorded
    # Verify model config captured

async def test_debug_logging_captures_errors():
    """Test error stack traces logged."""
    # Trigger agent error (mock LLM failure)
    # Query execution log
    # Verify error_type, error_message, error_stack_trace populated
    # Verify execution_status = "error"
```

#### Analytics Tests (Priority: HIGH)
```python
# tests/unit/services/test_analytics_service.py

async def test_get_conversation_executions():
    """Test conversation history query."""
    # Create multiple executions for conversation
    # Query via AnalyticsService.get_conversation_executions()
    # Verify correct executions returned
    # Verify sorted by started_at desc

async def test_get_user_errors():
    """Test user error tracking."""
    # Create successful and failed executions
    # Query via get_user_errors()
    # Verify only errors returned
    # Verify idx_execution_logs_user_status used

async def test_get_slowest_tools():
    """Test tool performance analytics."""
    # Create tool call logs with varying durations
    # Query via get_slowest_tools()
    # Verify aggregation correct
    # Verify sorted by avg_duration desc
```

#### Contract Tests (Priority: CRITICAL)
```python
# tests/integration/test_langchain_v1_contract.py

async def test_create_agent_api_stable():
    """Test LangChain v1 create_agent() still works."""
    # Call create_agent() with current signature
    # If fails, LangChain v1 API changed
    # Update agent service accordingly

async def test_structured_output_format():
    """Test structured output still returns dict."""
    # Execute agent
    # Verify result is dict
    # Verify "structured_response" key exists
```

**Test Count: ~12 tests**

---

### Phase 2.4: ContentRetriever Tool

**NEW Components:**
- ContentRetrieverTool (LangChain BaseTool)
- Real DocumentProcessor implementation
- File format detection

**Tests Required:**

#### Integration Tests (Priority: HIGH)
```python
# tests/integration/test_content_retriever_tool.py

async def test_agent_uses_content_retriever():
    """Test agent calls ContentRetriever tool."""
    # Initialize agent with ContentRetriever
    # Upload test document
    # Ask question about document
    # Verify tool called
    # Verify correct answer from document

async def test_docling_processing():
    """Test advanced document processing."""
    # Upload PDF with complex layout
    # Process with Docling
    # Verify structure extracted
    # Verify tables/images handled

async def test_fallback_processing():
    """Test fallback when Docling fails."""
    # Upload unsupported format
    # Verify Docling fails gracefully
    # Verify fallback to basic processing
    # Verify content still extracted
```

#### Tool Tests (Priority: MEDIUM)
```python
# tests/unit/tools/test_content_retriever_tool.py

def test_tool_schema_valid():
    """Verify ContentRetrieverTool schema."""
    # Check tool name, description
    # Verify args_schema is Pydantic model
    # Verify _run() method exists
```

**Test Count: ~6 tests**

---

### Phase 2.5: Built-in Middleware

**NEW Components:**
- PIIRedactionMiddleware
- SummarizationMiddleware
- HumanInTheLoopMiddleware

**Tests Required:**

#### Integration Tests (Priority: HIGH)
```python
# tests/integration/test_middleware_chain.py

async def test_pii_redaction():
    """Test PII automatically redacted."""
    # Send message with email, phone, SSN
    # Verify PII redacted in logs
    # Verify PII redacted in API response
    # Verify pii_redacted flag set in execution log

async def test_summarization_triggered():
    """Test conversation summarized at token limit."""
    # Send messages approaching token limit
    # Verify summarization triggered
    # Verify summarization_triggered flag set
    # Verify context compressed

async def test_human_approval_required():
    """Test sensitive operations pause."""
    # Trigger sensitive operation (e.g., file delete)
    # Verify execution pauses
    # Verify approval dialog shown
    # Approve operation
    # Verify operation completes
```

**Test Count: ~5 tests**

---

### Phase 2.6: Custom Middleware

**NEW Components:**
- ContextMiddleware
- MemoryMiddleware
- ExecutionTrackingMiddleware

**Tests Required:**

#### Integration Tests (Priority: MEDIUM)
```python
# tests/integration/test_custom_middleware.py

async def test_context_loaded_before_agent():
    """Test context injected into agent."""
    # Create context in DB
    # Execute agent
    # Verify context loaded in ContextMiddleware
    # Verify context available to agent

async def test_memory_persisted_after_agent():
    """Test memory saved to DB."""
    # Execute agent with memory
    # Verify MemoryMiddleware saves to DB
    # Load conversation in new session
    # Verify memory restored
```

**Test Count: ~4 tests**

---

### Phase 2.7: Firecrawl MCP Tool

**NEW Components:**
- MCPService (connection manager)
- Firecrawl MCP adapter
- MCP server configuration

**Tests Required:**

#### Integration Tests (Priority: HIGH)
```python
# tests/integration/test_firecrawl_mcp.py

@pytest.mark.skipif(not os.getenv("FIRECRAWL_API_KEY"), reason="Firecrawl API key required")
async def test_firecrawl_scrape():
    """Test Firecrawl scrapes URL."""
    # Initialize agent with Firecrawl tool
    # Ask to scrape test URL
    # Verify Firecrawl tool called
    # Verify markdown content returned

async def test_mcp_connection_management():
    """Test MCP connections don't leak."""
    # Execute multiple scrapes
    # Verify connections closed
    # Verify no resource leaks
```

**Test Count: ~3 tests (API key required)**

---

### Phase 2.8: Production Hardening

**NEW Components:**
- Error boundaries
- Rate limiting
- Monitoring endpoints

**Tests Required:**

#### System Tests (Priority: HIGH)
```python
# tests/system/test_production_readiness.py

async def test_concurrent_users():
    """Test 10+ concurrent users."""
    # Simulate 10 concurrent requests
    # Verify all complete successfully
    # Verify no race conditions
    # Verify database handles concurrency

async def test_error_recovery():
    """Test system recovers from errors."""
    # Trigger various errors
    # Verify error logged
    # Verify system continues
    # Verify no cascading failures

def test_health_endpoint():
    """Test /health endpoint."""
    # Call /health
    # Verify database connected
    # Verify LLM providers available
    # Verify MCP servers connected
```

#### Performance Tests (Priority: MEDIUM)
```python
# tests/performance/test_response_times.py

@pytest.mark.slow
async def test_agent_response_time():
    """Test agent responds within 5s (p95)."""
    # Execute 100 agent queries
    # Measure response times
    # Verify p95 < 5000ms

@pytest.mark.slow
async def test_file_processing_time():
    """Test file upload processes within 10s."""
    # Upload 1MB test files
    # Measure processing times
    # Verify p95 < 10000ms
```

**Test Count: ~8 tests**

---

## Test Organization

```
tests/
├── unit/                          # Fast, isolated tests
│   ├── database/
│   │   ├── test_user_models.py   # User, settings, sessions
│   │   └── test_indexes.py        # Index verification
│   ├── services/
│   │   └── test_analytics_service.py
│   └── tools/
│       └── test_content_retriever_tool.py
│
├── integration/                   # Cross-component tests
│   ├── test_auth_flow.py         # Phase 2.0
│   ├── test_agent_service.py     # Phase 2.3
│   ├── test_content_retriever_tool.py  # Phase 2.4
│   ├── test_middleware_chain.py  # Phase 2.5-2.6
│   ├── test_firecrawl_mcp.py     # Phase 2.7
│   └── test_langchain_v1_contract.py  # API stability
│
├── ui/                            # Gradio UI tests
│   ├── test_settings_page.py     # Phase 2.1
│   ├── test_file_ui_stubs.py     # Phase 2.2
│   └── test_pwa_features.py      # PWA manifest, etc.
│
├── e2e/                          # End-to-end workflows
│   └── test_pwa_installation.py
│
├── system/                       # Production readiness
│   └── test_production_readiness.py  # Phase 2.8
│
└── performance/                  # Performance benchmarks
    └── test_response_times.py    # Phase 2.8

conftest.py                       # Shared fixtures
```

---

## Test Fixtures (Reusable)

```python
# tests/conftest.py additions for Phase 2

import pytest
from unittest.mock import Mock
from gradio import Request

@pytest.fixture
def mock_hf_request():
    """Mock Gradio Request with HF authentication."""
    request = Mock(spec=Request)
    request.username = "test_user"
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "pytest"}
    return request

@pytest.fixture
async def authenticated_user(db, mock_hf_request):
    """Create authenticated user."""
    auth_service = AuthService(db)
    user = await auth_service.get_or_create_user_from_request(mock_hf_request)
    return user

@pytest.fixture
async def agent_service(db, authenticated_user):
    """Initialize minimal agent service."""
    service = AgentService(db)
    await service.initialize()
    return service

@pytest.fixture
def mock_langchain_agent():
    """Mock LangChain v1 agent for testing."""
    agent = Mock()
    agent.ainvoke = AsyncMock(return_value={
        "structured_response": AgentResponse(
            response="Test response",
            confidence=0.9,
            tool_calls=[]
        )
    })
    return agent
```

---

## Test Execution Strategy

### Development Workflow
```bash
# Fast unit tests only (during development)
make test-unit-only         # ~20 tests, <5 seconds

# Integration tests (before commit)
make test-with-backend      # ~50 tests, <30 seconds

# Full suite (before PR)
make test                   # ~60 tests, <60 seconds
```

### CI/CD Pipeline
```yaml
# .github/workflows/test.yml

test-phase2:
  strategy:
    matrix:
      test-suite:
        - unit
        - integration
        - ui
        - system
  steps:
    - run: pytest tests/${{ matrix.test-suite }}

test-performance:
  # Only on main branch
  if: github.ref == 'refs/heads/main'
  steps:
    - run: pytest tests/performance -m slow
```

---

## Coverage Goals

**Minimum Coverage by Phase:**
- Phase 2.0 (Auth): 80% (critical path)
- Phase 2.1 (PWA): 60% (mostly UI)
- Phase 2.2 (Stubs): 40% (stubs only)
- Phase 2.3 (Agent): 85% (core functionality)
- Phase 2.4 (Tools): 75% (file processing)
- Phase 2.5-2.6 (Middleware): 70% (middleware chains)
- Phase 2.7 (MCP): 60% (external dependency)
- Phase 2.8 (Production): 90% (production critical)

**Overall Phase 2 Target: 75% coverage**

---

## What We DON'T Test

**External Dependencies:**
- ❌ LangChain v1 internal logic (trust the library)
- ❌ HuggingFace OAuth flow (trust HF)
- ❌ Firecrawl API behavior (test our adapter only)
- ❌ MCP server implementations (test connection only)

**Pydantic Validation:**
- ❌ Field type validation (Pydantic does this)
- ❌ Required vs optional fields (Pydantic does this)
- ❌ JSON schema generation (Pydantic does this)

**Phase 1 Coverage:**
- ❌ StandardMessage CRUD (already tested)
- ❌ ConversationState persistence (already tested)
- ❌ WorkbenchState schema (already tested)
- ❌ Gradio mounting (test_gradio_unified.py passes)

---

## Test Summary by Phase

| Phase | Component | Test Count | Priority | Notes |
|-------|-----------|------------|----------|-------|
| 2.0 | Auth & Settings | 8 | HIGH | Critical for all features |
| 2.1 | PWA App | 6 | MEDIUM | UI-focused |
| 2.2 | File UI (Stubs) | 3 | LOW | Stubs only |
| 2.3 | Agent Service | 12 | CRITICAL | Core agent logic |
| 2.4 | ContentRetriever | 6 | HIGH | Tool integration |
| 2.5 | Built-in Middleware | 5 | HIGH | Security/compliance |
| 2.6 | Custom Middleware | 4 | MEDIUM | Context/memory |
| 2.7 | Firecrawl MCP | 3 | HIGH | External tool |
| 2.8 | Production | 8 | HIGH | System stability |
| **TOTAL** | **All Phases** | **~60 tests** | - | Focused, high-value |

---

## Key Testing Principles

1. **Integration over Unit**: Test real workflows, not internal methods
2. **Contract Tests for Alpha APIs**: Verify LangChain v1 API stability
3. **Reuse Phase 1 Fixtures**: Build on existing test infrastructure
4. **Trust Pydantic**: No validation tests needed
5. **Focus on NEW Behavior**: Don't re-test Phase 1 functionality
6. **Mock External APIs**: Use real APIs only in integration tests
7. **Fast Feedback Loop**: Unit tests <5s, integration <30s, full <60s

---

## Success Criteria

**Phase 2 Testing Complete When:**
- ✅ All 60 core tests passing
- ✅ 75%+ code coverage
- ✅ LangChain v1 contract tests passing (API stable)
- ✅ Agent responds correctly without tools (Phase 2.3)
- ✅ Agent responds correctly with ContentRetriever (Phase 2.4)
- ✅ Agent responds correctly with Firecrawl (Phase 2.7)
- ✅ Middleware chain executes correctly (Phase 2.5-2.6)
- ✅ Session management prevents DB pollution (Phase 2.0)
- ✅ PWA installs on mobile/desktop (Phase 2.1)
- ✅ Performance tests pass (Phase 2.8)

**Ready for v0.2.0 Release!**
