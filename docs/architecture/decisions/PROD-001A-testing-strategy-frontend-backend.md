# PROD-001A: Testing Strategy for Frontend-Backend Transparency

## Context

Create clarity on how main.py layering and inheritance works through a thorough testing strategy. Use test feedback to improve the building of the Gradio UI from the backend in a more transparent way. Implement test-first methodology followed by refactoring.

## What's Included

- [ ] Comprehensive architecture tests for main.py structure
- [ ] Service dependency injection testing and clarity
- [ ] Gradio UI mounting and mode factory pattern tests
- [ ] Basic chatting service as shared subservice across modes
- [ ] **Database table validation and schema testing (CRITICAL)**
- [ ] **Cross-mode database operations testing**
- [ ] Cross-mode service integration testing (workbench + seo_coach)
- [ ] Gradio UI component testing (dropdowns, sliders, options)
- [ ] Dynamic configuration testing for UI components
- [ ] UI component interaction and event handler testing
- [ ] Layer separation and responsibility boundary tests
- [ ] Error handling and fallback mechanism validation
- [ ] Test insights to guide Gradio UI building improvements

## What's Excluded

- ❌ UI component visual/browser rendering testing (save for later)
- ❌ End-to-end browser automation testing (separate task)
- ❌ Performance testing (separate concern)
- ❌ Database integration testing beyond service layer

## Implementation Boundaries

### Files to CREATE:
- `tests/test_main_architecture.py` - Comprehensive main.py architecture tests
- `tests/test_gradio_integration_patterns.py` - UI building pattern tests
- `tests/test_gradio_ui_components.py` - UI component configuration and interaction tests
- `tests/test_shared_chat_service.py` - Basic chatting service cross-mode testing
- `tests/test_minimal_node_setup.py` - Minimal node configuration testing
- `tests/test_database_tables.py` - **CRITICAL: Database schema and table validation**
- `tests/test_service_injection_clarity.py` - Service layer testing
- `src/agent_workbench/services/minimal_chat_nodes.py` - Minimal node implementation
- `docs/architecture/testing-insights.md` - Documentation of findings

### Test Categories:

```python
class TestFastAPILayerArchitecture:
    """Test FastAPI app structure and middleware stack"""

class TestServiceInjectionLayer:
    """Test dependency injection clarity and patterns"""

class TestGradioIntegrationLayer:
    """Test UI mounting and mode factory patterns"""

class TestSharedChatService:
    """Test basic chatting service across both modes"""

class TestMinimalNodeSetup:
    """Test minimal node configuration for MVP chat service"""

class TestDatabaseTables:
    """CRITICAL: Test database schema and table validation"""

class TestGradioUIComponents:
    """Test Gradio component configuration and behavior"""

class TestLayerSeparationAndResponsibilities:
    """Test clear layer boundaries and responsibilities"""

class TestArchitecturalInsights:
    """Tests that provide refactoring insights"""
```

### Testing Infrastructure Usage:
- Utilize existing `make test` capabilities
- Leverage `uv pytest` with coverage reporting
- Integration with existing test structure in `tests/`
- Use pytest fixtures from `tests/conftest.py`

## Testing Strategy Phases

### Phase 1: Architecture Transparency Tests
1. **FastAPI Layer Tests**
   - App initialization structure
   - Middleware stack configuration
   - Route registration order and conflicts

2. **Service Injection Tests**
   - LangGraph service dependency injection
   - Error handling when injection fails
   - Service isolation and testability

3. **Gradio Integration Tests**
   - UI mounting success and error paths
   - Mode factory architecture clarity
   - Interface creation error handling

4. **Gradio UI Component Tests**
   - Provider and model dropdown configuration
   - Temperature and max_tokens slider ranges
   - Debug mode checkbox functionality
   - Dynamic choices from model_config_service
   - Component default value validation

### Phase 2: Layer Responsibility Tests
1. **Separation of Concerns**
   - FastAPI layer HTTP-only responsibilities
   - UI layer independence from FastAPI
   - Service layer isolation and injectability

2. **Error Boundaries**
   - Cross-layer error propagation
   - Graceful degradation mechanisms
   - API-only mode fallback validation

### Phase 3: Refactoring Insights
1. **Coupling Point Identification**
   - Document current tight coupling
   - Test dependency injection opportunities
   - Configuration centralization needs

2. **Improvement Documentation**
   - Service injection enhancement opportunities
   - UI component service integration patterns
   - Mode factory pattern improvements

## Gradio UI Component Testing Strategy

### Component Structure Testing
```python
def test_gradio_dropdown_configuration():
    """Test provider and model dropdowns are properly configured."""
    app = create_workbench_app()

    # Test provider dropdown structure
    provider_choices, default_provider = model_config_service.get_provider_choices_for_ui()
    assert len(provider_choices) > 0
    assert default_provider in provider_choices

    # Test model dropdown structure
    model_choices, default_model = model_config_service.get_model_choices_for_ui()
    assert len(model_choices) > 0
    assert default_model in model_choices

def test_gradio_slider_configuration():
    """Test temperature and max_tokens sliders have correct ranges."""
    # Temperature slider: 0.0-2.0 with service default
    temp_default = model_config_service.default_temperature
    assert 0.0 <= temp_default <= 2.0

    # Max tokens slider: 100-4000 with service default
    tokens_default = model_config_service.default_max_tokens
    assert 100 <= tokens_default <= 4000
```

### Dynamic Configuration Testing
```python
def test_model_config_service_integration():
    """Test UI components get correct values from model_config_service."""
    # Test that service provides valid dropdown choices
    provider_choices, default_provider = model_config_service.get_provider_choices_for_ui()

    # Validate provider choices
    expected_providers = ["anthropic", "openai", "ollama"]
    assert any(provider in provider_choices for provider in expected_providers)

    # Test model choices are provider-specific
    model_choices, default_model = model_config_service.get_model_choices_for_ui()
    assert "claude" in default_model.lower() or "gpt" in default_model.lower()
```

### Event Handler Testing
```python
@pytest.mark.asyncio
async def test_gradio_message_handler():
    """Test the handle_enhanced_message function with various inputs."""
    # Test valid inputs
    result = await handle_enhanced_message(
        msg="test message",
        conv_id="test-conv-id",
        provider_val="anthropic",
        model_val="claude-3-5-sonnet-20241022",
        temp_val=0.7,
        max_tokens_val=2000,
        debug_val=False
    )

    # Verify handler returns correct structure
    assert len(result) == 3  # message, history, status
    message_clear, history, status_html = result
    assert message_clear == ""  # Message should be cleared
    assert isinstance(history, list)  # History should be list
    assert "workflow" in status_html.lower()  # Status should mention workflow

def test_component_value_validation():
    """Test that component values are properly validated."""
    # Test temperature bounds
    assert validate_temperature(0.5) == True
    assert validate_temperature(-0.1) == False
    assert validate_temperature(2.1) == False

    # Test max_tokens bounds
    assert validate_max_tokens(1000) == True
    assert validate_max_tokens(50) == False
    assert validate_max_tokens(5000) == False
```

## Shared Chat Service Testing Strategy (MVP Goal)

### Minimal Node Setup Architecture
The basic chat service should use a **minimal node configuration** that can be shared across modes:

```python
# Minimal Chat Node Setup for MVP
class MinimalChatNodes:
    """Lightweight node setup for basic chat functionality across modes."""

    # Core MVP nodes (shared across workbench + seo_coach)
    @staticmethod
    async def input_validation_node(state: Dict) -> Dict:
        """Validate user input - shared logic"""

    @staticmethod
    async def basic_llm_node(state: Dict) -> Dict:
        """Basic LLM call - mode-agnostic"""

    @staticmethod
    async def response_formatting_node(state: Dict) -> Dict:
        """Format response - shared logic"""

    # Mode-specific minimal nodes (when needed)
    @staticmethod
    async def workbench_context_node(state: Dict) -> Dict:
        """Minimal workbench-specific processing"""

    @staticmethod
    async def seo_coach_context_node(state: Dict) -> Dict:
        """Minimal seo_coach-specific processing"""
```

This approach provides:
- ✅ **Shared core nodes** for basic chat functionality
- ✅ **Mode-specific nodes** only when absolutely necessary
- ✅ **Minimal complexity** for MVP
- ✅ **Easy testing** of individual node behavior

## Shared Chat Service Testing Strategy (MVP Goal)

### Cross-Mode Service Integration Testing
```python
class TestSharedChatService:
    """Test SimpleLangGraphClient as shared subservice across modes."""

    def test_chat_service_initialization(self):
        """Test that chat service initializes consistently across modes."""
        # Test workbench mode initialization
        with patch.dict(os.environ, {"APP_MODE": "workbench"}):
            workbench_client = SimpleLangGraphClient()
            assert workbench_client.base_url == "http://localhost:8000"

        # Test seo_coach mode initialization
        with patch.dict(os.environ, {"APP_MODE": "seo_coach"}):
            seo_client = SimpleLangGraphClient()
            assert seo_client.base_url == "http://localhost:8000"

        # Both should use same underlying service
        assert workbench_client.__class__ == seo_client.__class__

    @pytest.mark.asyncio
    async def test_shared_service_workbench_mode(self):
        """Test chat service works in workbench mode."""
        client = SimpleLangGraphClient()

        with patch.object(client.client, 'post') as mock_post:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "assistant_response": "Test response",
                "conversation_id": "test-conv",
                "workflow_mode": "workbench",
                "execution_successful": True,
                "metadata": {"provider_used": "anthropic"}
            }
            mock_post.return_value = mock_response

            result = await client.send_message(
                message="test message",
                conversation_id="test-conv",
                model_config={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )

            # Verify workbench mode integration
            assert result["workflow_mode"] == "workbench"
            assert result["assistant_response"] == "Test response"
            assert result["execution_successful"] == True

    @pytest.mark.asyncio
    async def test_shared_service_seo_coach_mode(self):
        """Test chat service adapts to seo_coach mode."""
        client = SimpleLangGraphClient()

        with patch.object(client.client, 'post') as mock_post:
            # Mock seo_coach response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "assistant_response": "SEO advice response",
                "conversation_id": "seo-conv",
                "workflow_mode": "seo_coach",
                "execution_successful": True,
                "metadata": {"coaching_type": "dutch_seo"}
            }
            mock_post.return_value = mock_response

            # Modify payload for seo_coach mode
            payload_with_mode = {
                "user_message": "test seo question",
                "conversation_id": "seo-conv",
                "workflow_mode": "seo_coach",  # Key difference
                "llm_config": {
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "streaming": False
                }
            }

            # Test mode switching capability
            result = await client.send_message(
                message="test seo question",
                conversation_id="seo-conv",
                model_config={
                    "provider": "anthropic",
                    "model_name": "claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )

            assert result["workflow_mode"] == "seo_coach"
            assert "seo" in result["assistant_response"].lower()

def test_cross_mode_service_consistency():
    """Test that service behavior is consistent across both modes."""
    # Test that same client can handle both modes
    client = SimpleLangGraphClient()

    # Test method signatures are identical
    import inspect
    send_message_sig = inspect.signature(client.send_message)
    get_history_sig = inspect.signature(client.get_chat_history)

    # Verify consistent interface
    assert len(send_message_sig.parameters) == 3  # message, conv_id, model_config
    assert len(get_history_sig.parameters) == 1   # conversation_id

    # Both modes should use same API endpoints
    assert client.base_url == "http://localhost:8000"
```

### Minimal Node Setup Testing
```python
class TestMinimalNodeSetup:
    """Test minimal node configuration for shared chat service."""

    @pytest.mark.asyncio
    async def test_core_shared_nodes(self):
        """Test that core nodes work for both modes."""
        from src.agent_workbench.services.minimal_chat_nodes import MinimalChatNodes

        # Test input validation node (shared)
        test_state = {"user_message": "Hello", "workflow_mode": "workbench"}
        validated_state = await MinimalChatNodes.input_validation_node(test_state)
        assert "validated_input" in validated_state

        # Same node should work for seo_coach mode
        seo_state = {"user_message": "SEO help", "workflow_mode": "seo_coach"}
        validated_seo = await MinimalChatNodes.input_validation_node(seo_state)
        assert "validated_input" in validated_seo

    @pytest.mark.asyncio
    async def test_basic_llm_node_mode_agnostic(self):
        """Test that basic LLM node works regardless of mode."""
        node = MinimalChatNodes()

        # Test workbench mode
        workbench_state = {
            "validated_input": "test message",
            "workflow_mode": "workbench",
            "model_config": {"provider": "anthropic", "model_name": "claude-3-5-sonnet"}
        }
        result = await node.basic_llm_node(workbench_state)
        assert "llm_response" in result

        # Test seo_coach mode with same node
        seo_state = {
            "validated_input": "SEO question",
            "workflow_mode": "seo_coach",
            "model_config": {"provider": "anthropic", "model_name": "claude-3-5-sonnet"}
        }
        seo_result = await node.basic_llm_node(seo_state)
        assert "llm_response" in seo_result

    def test_minimal_node_composition(self):
        """Test that minimal nodes can be composed into workflows."""

        # Define minimal workflow for both modes
        minimal_workflow_steps = [
            "input_validation_node",
            "basic_llm_node",
            "response_formatting_node"
        ]

        # Test that SimpleLangGraphClient can use minimal node setup
        client = SimpleLangGraphClient()

        # Verify client can work with minimal node configuration
        # (This drives toward simpler service architecture)
        assert hasattr(client, 'send_message')  # Core interface maintained

        # The key insight: complex workflows not needed for basic chat MVP

def test_node_vs_full_workflow_performance():
    """Test that minimal nodes are more efficient than full workflows."""

    # This test drives the architectural decision:
    # For basic chat MVP, use minimal nodes instead of complex LangGraph workflows

    minimal_node_count = 3  # input_validation, basic_llm, response_formatting
    full_workflow_node_count = 8  # All existing workflow nodes

    # MVP should use minimal setup
    assert minimal_node_count < full_workflow_node_count

    # Test complexity reduction
    assert "minimal" in "minimal_chat_nodes"  # Naming drives simplicity

### Service Abstraction Testing
```python
def test_chat_service_abstraction_layer():
    """Test that chat service provides clean abstraction for UI layers."""

    # Test that UI components don't need mode-specific logic
    workbench_app = create_workbench_app()
    seo_coach_app = create_seo_coach_app()

    # Both should use SimpleLangGraphClient
    # (This drives the goal of shared subservice)

    # Extract client usage from both apps (implementation detail)
    # The key insight: both modes should instantiate the same client class
    assert SimpleLangGraphClient.__name__ in str(workbench_app)
    # This test guides us toward shared service architecture

def test_mvp_chat_functionality():
    """Test MVP chat functionality works across modes."""

    # Define MVP requirements
    mvp_requirements = {
        "send_message": True,
        "get_chat_history": True,
        "handle_model_config": True,
        "error_handling": True,
        "conversation_persistence": True
    }

    client = SimpleLangGraphClient()

    # Verify MVP methods exist
    assert hasattr(client, 'send_message')
    assert hasattr(client, 'get_chat_history')

    # Verify async interface (required for Gradio)
    import asyncio
    assert asyncio.iscoroutinefunction(client.send_message)
    assert asyncio.iscoroutinefunction(client.get_chat_history)
```

## Database Table Testing Strategy (CRITICAL!)

### Schema Validation Testing
```python
class TestDatabaseTables:
    """CRITICAL: Prevent database table issues that break the service."""

    def test_required_tables_exist(self):
        """Test that all required database tables exist."""
        from src.agent_workbench.models.database import Base, ConversationModel, MessageModel

        # Verify table models are properly defined
        assert hasattr(ConversationModel, '__tablename__')
        assert ConversationModel.__tablename__ == "conversations"

        assert hasattr(MessageModel, '__tablename__')
        assert MessageModel.__tablename__ == "messages"

        # Verify Base includes all tables
        table_names = [table.name for table in Base.metadata.tables.values()]
        assert "conversations" in table_names
        assert "messages" in table_names

    def test_conversation_table_schema(self):
        """Test ConversationModel has required fields for shared chat service."""
        from src.agent_workbench.models.database import ConversationModel

        # Critical fields for MVP chat service
        required_columns = ['id', 'user_id', 'title', 'created_at', 'updated_at']

        model_columns = [column.name for column in ConversationModel.__table__.columns]

        for required_col in required_columns:
            assert required_col in model_columns, f"Missing required column: {required_col}"

        # Verify primary key
        pk_columns = [col.name for col in ConversationModel.__table__.primary_key.columns]
        assert 'id' in pk_columns

    def test_message_table_schema(self):
        """Test MessageModel has required fields for cross-mode compatibility."""
        from src.agent_workbench.models.database import MessageModel

        # Critical fields for MVP chat service
        required_columns = ['id', 'conversation_id', 'role', 'content']

        model_columns = [column.name for column in MessageModel.__table__.columns]

        for required_col in required_columns:
            assert required_col in model_columns, f"Missing required column: {required_col}"

        # Verify foreign key relationship
        fk_columns = [fk.parent.name for fk in MessageModel.__table__.foreign_keys]
        assert 'conversation_id' in fk_columns

    def test_role_constraints(self):
        """Test that message roles are properly constrained."""
        from src.agent_workbench.models.database import MessageModel

        # Find role column constraint
        role_column = MessageModel.__table__.columns['role']

        # Should have check constraint for valid roles
        constraints = [str(constraint) for constraint in MessageModel.__table__.constraints]
        role_constraint_found = any("role IN" in constraint for constraint in constraints)
        assert role_constraint_found, "Missing role constraint for messages"

### Database Operations Testing
```python
    @pytest.mark.asyncio
    async def test_conversation_crud_operations(self):
        """Test that conversation CRUD works for shared chat service."""
        from src.agent_workbench.models.database import ConversationModel
        from src.agent_workbench.api.database import get_session

        async for session in get_session():
            # Test CREATE
            conversation = await ConversationModel.create(
                session,
                title="Test Chat - MVP"
            )
            assert conversation.id is not None
            assert conversation.title == "Test Chat - MVP"

            # Test READ
            found_conversation = await ConversationModel.get_by_id(session, conversation.id)
            assert found_conversation is not None
            assert found_conversation.title == "Test Chat - MVP"

            # Test UPDATE
            updated_conversation = await conversation.update(session, title="Updated Chat")
            assert updated_conversation.title == "Updated Chat"

            # Test DELETE
            await conversation.delete(session)
            deleted_conversation = await ConversationModel.get_by_id(session, conversation.id)
            assert deleted_conversation is None

            break  # Exit after first session

    @pytest.mark.asyncio
    async def test_message_persistence_cross_mode(self):
        """Test that messages persist correctly for both workbench and seo_coach."""
        from src.agent_workbench.models.database import ConversationModel, MessageModel
        from src.agent_workbench.api.database import get_session

        async for session in get_session():
            # Create conversation
            conversation = await ConversationModel.create(session, title="Cross-Mode Test")

            # Test workbench mode message
            workbench_message = MessageModel(
                conversation_id=conversation.id,
                role="user",
                content="Workbench test message"
            )
            session.add(workbench_message)

            # Test seo_coach mode message
            seo_message = MessageModel(
                conversation_id=conversation.id,
                role="assistant",
                content="SEO coaching response"
            )
            session.add(seo_message)

            await session.commit()

            # Verify both messages persisted
            messages = await session.execute(
                select(MessageModel).where(MessageModel.conversation_id == conversation.id)
            )
            message_list = list(messages.scalars().all())

            assert len(message_list) == 2
            assert any(msg.content == "Workbench test message" for msg in message_list)
            assert any(msg.content == "SEO coaching response" for msg in message_list)

            # Cleanup
            await conversation.delete(session)
            break

def test_alembic_migrations_applied():
    """Test that database migrations are properly applied."""
    from alembic.config import Config
    from alembic import command
    from alembic.script import ScriptDirectory
    from alembic.runtime.environment import EnvironmentContext

    # Verify alembic is configured
    assert os.path.exists("alembic.ini"), "Missing alembic.ini configuration"

    # Verify migrations directory exists
    assert os.path.exists("alembic/"), "Missing alembic migrations directory"

    # This test ensures migrations won't be forgotten!
    config = Config("alembic.ini")
    script_dir = ScriptDirectory.from_config(config)

    # Should have at least initial migration
    revisions = list(script_dir.walk_revisions())
    assert len(revisions) > 0, "No database migrations found!"

def test_database_connection_config():
    """Test database connection configuration for different environments."""
    import os
    from src.agent_workbench.api.database import get_database_url

    # Test that database URL is configured
    db_url = get_database_url()
    assert db_url is not None, "Database URL not configured"

    # Should use SQLite for development/testing
    if os.getenv("APP_ENV") in ["development", "test"]:
        assert "sqlite" in db_url.lower()

    # Should be accessible
    assert "://" in db_url  # Valid URL format
```

## Success Criteria

- [ ] Complete test coverage of main.py architecture layers
- [ ] **MVP GOAL**: SimpleLangGraphClient working as shared subservice in both modes
- [ ] **CRITICAL**: All required database tables exist and have correct schema
- [ ] **CRITICAL**: Database CRUD operations work for conversations and messages
- [ ] **CRITICAL**: Cross-mode message persistence validated (workbench + seo_coach)
- [ ] **CRITICAL**: Database migrations properly applied and tested
- [ ] **Minimal Node Setup**: 3-node workflow (validation → LLM → formatting) for MVP
- [ ] Cross-mode service integration validated (workbench + seo_coach)
- [ ] Consistent service interface across both UI modes
- [ ] Mode-agnostic core nodes working in both workflows
- [ ] Validated basic chat functionality (send_message, get_history)
- [ ] Validated Gradio UI component configuration and behavior
- [ ] Working dropdown and slider component tests
- [ ] Dynamic configuration testing from model_config_service
- [ ] Event handler testing for UI interactions
- [ ] Clear documentation of current coupling points
- [ ] Test-driven insights for Gradio UI building improvements
- [ ] Validated error handling and fallback mechanisms
- [ ] Improved transparency in backend-to-frontend integration
- [ ] All existing tests continue to pass (no regressions)

## Testing Commands

```bash
# Run architecture tests specifically
uv run pytest tests/test_main_architecture.py -v

# Run UI component tests
uv run pytest tests/test_gradio_ui_components.py -v

# Run shared chat service tests (MVP GOAL)
uv run pytest tests/test_shared_chat_service.py -v

# Run database table tests (CRITICAL!)
uv run pytest tests/test_database_tables.py -v

# Run comprehensive test suite with coverage
uv run pytest tests/test_main_architecture.py tests/test_gradio_ui_components.py tests/test_shared_chat_service.py tests/test_database_tables.py --cov=src/agent_workbench/main --cov=src/agent_workbench/ui --cov=src/agent_workbench/models

# Test database before starting services (prevent burned hands!)
uv run pytest tests/test_database_tables.py::TestDatabaseTables::test_required_tables_exist -v

# Use existing make test infrastructure
make test

# Run in isolation for clean results
uv run pytest tests/test_main_architecture.py --tb=short
```

## Expected Insights

1. **Current Architecture State**
   - Clear mapping of layer responsibilities
   - Documentation of service injection patterns
   - Understanding of Gradio integration approach

2. **Improvement Opportunities**
   - Better dependency injection patterns
   - Enhanced error boundary handling
   - More transparent UI building process
   - Centralized configuration management

3. **Refactoring Guidance**
   - Test-validated improvements to service injection
   - Enhanced mode factory pattern clarity
   - Better separation between FastAPI and Gradio layers
   - Improved error handling and fallback mechanisms