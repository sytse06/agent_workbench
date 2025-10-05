# Testing Strategy Recommendations

## Overview

Following the Pydantic Implementation Audit (Priority 2.3 and 3.2 completed), we can significantly simplify our testing strategy by leveraging Pydantic's built-in validation capabilities.

## Key Improvements from Pydantic Audit

1. **ValidatedWorkbenchState wrapper** - Provides runtime validation for LangGraph state
2. **Comprehensive field examples** - All 36+ models have field examples for test data generation
3. **Field validators** - Custom validation logic in models (provider_name, retry_count, website_url, etc.)
4. **Model-level validators** - Cross-field validation (e.g., temperature vs top_p conflicts)

## 4 Major Testing Simplifications

### 1. Eliminate Manual Validation Tests

**Before (manual validation):**
```python
def test_invalid_temperature():
    """Test that invalid temperature raises error."""
    with pytest.raises(ValueError):
        config = ModelConfig(provider="anthropic", model_name="claude-3.5-sonnet")
        config.temperature = 5.0  # Need to manually check
        validate_temperature(config.temperature)
```

**After (Pydantic validates automatically):**
```python
def test_invalid_temperature():
    """Pydantic validates automatically on construction."""
    with pytest.raises(ValidationError):
        ModelConfig(
            provider="anthropic",
            model_name="claude-3.5-sonnet",
            temperature=5.0  # Fails immediately
        )
```

**Impact:** ~30-40% fewer validation test cases needed

### 2. Test Data Generation from Field Examples

**Before:**
```python
# Need to manually create valid test data for every test
def test_chat_request():
    request = ChatRequest(
        message="test",
        conversation_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        llm_config=ModelConfig(
            provider="anthropic",
            model_name="claude-3.5-sonnet",
            temperature=0.7
        )
    )
```

**After (using field examples):**
```python
# Generate valid test data from schema examples
from agent_workbench.testing.factories import create_from_schema

def test_chat_request():
    request = create_from_schema(ChatRequest)  # Uses field examples
    assert request.message  # Guaranteed valid
```

**Implementation:**

Create `src/agent_workbench/testing/factories.py`:
```python
"""Test data factories using Pydantic schema examples."""
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

def create_from_schema(model_class: Type[T], **overrides) -> T:
    """Create instance from schema's json_schema_extra example.

    Args:
        model_class: Pydantic model class with json_schema_extra example
        **overrides: Field overrides for the example data

    Returns:
        Valid instance of model_class

    Examples:
        >>> config = create_from_schema(ModelConfig)
        >>> config = create_from_schema(ModelConfig, temperature=0.3)
    """
    example = model_class.model_config.get("json_schema_extra", {}).get("example", {})
    return model_class(**{**example, **overrides})
```

**Impact:** Reduces test setup code by ~50%

### 3. Property-Based Testing with ValidatedWorkbenchState

**Before (TypedDict had no validation):**
```python
def test_workbench_state():
    # TypedDict allows invalid data through
    state = WorkbenchState(
        conversation_id=UUID(...),
        user_message="test",
        provider_name="INVALID SPACES",  # No validation!
        retry_count=999,  # No bounds checking!
        model_config=ModelConfig(...),
        provider_name="anthropic",
        context_data={},
        active_contexts=[],
        conversation_history=[],
        workflow_mode="workbench",
        workflow_steps=[],
        execution_successful=True,
        retry_count=0
    )
    # Need manual validation in every test
```

**After (ValidatedWorkbenchState wrapper):**
```python
def test_workbench_state_validation():
    """ValidatedWorkbenchState catches issues early."""
    with pytest.raises(ValidationError) as exc_info:
        ValidatedWorkbenchState(
            conversation_id=UUID(...),
            user_message="test",
            provider_name="INVALID SPACES",  # Fails: spaces not allowed
            retry_count=999,  # Fails: max is 5
            model_config=ModelConfig(...),
            workflow_mode="workbench"
        )

    # Validate specific errors
    errors = exc_info.value.errors()
    assert any("lowercase" in str(e) for e in errors)
    assert any("exceed 5" in str(e) for e in errors)
```

**Impact:** State validation tests are now **declarative** instead of imperative

### 4. Integration Test Simplification

**Before:**
```python
async def test_workflow_execution():
    # Need to manually validate state at each step
    state = create_initial_state()
    assert validate_state(state), "Initial state invalid"

    state = await execute_step_1(state)
    assert validate_state(state), "Step 1 state invalid"

    state = await execute_step_2(state)
    assert validate_state(state), "Step 2 state invalid"
```

**After (validation in model layer):**
```python
async def test_workflow_execution():
    # Validation happens automatically in model layer
    validated_state = ValidatedWorkbenchState(
        conversation_id=UUID(...),
        user_message="test message",
        model_config=ModelConfig(provider="anthropic", model_name="claude-3.5-sonnet"),
        provider_name="anthropic",
        workflow_mode="workbench"
    )
    state = validated_state.to_typeddict()

    # Workflow fails fast if state becomes invalid
    result = await execute_workflow(state)  # Any invalid state raises ValidationError

    # Just test business logic, not validation
    assert result.execution_successful
    assert len(result.workflow_steps) == 3
```

**Impact:** Focus tests on **business logic** instead of **data validation**

## Concrete Recommendations

### A. Create Test Data Factories

**File:** `src/agent_workbench/testing/factories.py`

```python
"""Test data factories using Pydantic schema examples."""
from typing import Type, TypeVar
from uuid import UUID, uuid4
from datetime import datetime
from pydantic import BaseModel

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.models.api_models import (
    ChatRequest,
    ChatResponse,
    CreateConversationRequest,
    ConversationResponse,
)
from agent_workbench.models.consolidated_state import ValidatedWorkbenchState

T = TypeVar("T", bound=BaseModel)

def create_from_schema(model_class: Type[T], **overrides) -> T:
    """Create instance from schema's json_schema_extra example."""
    example = model_class.model_config.get("json_schema_extra", {}).get("example", {})
    return model_class(**{**example, **overrides})

# Specific factories for common models
def create_model_config(**overrides) -> ModelConfig:
    """Create valid ModelConfig for testing."""
    return create_from_schema(ModelConfig, **overrides)

def create_chat_request(**overrides) -> ChatRequest:
    """Create valid ChatRequest for testing."""
    return create_from_schema(ChatRequest, **overrides)

def create_validated_workbench_state(**overrides) -> ValidatedWorkbenchState:
    """Create valid ValidatedWorkbenchState for testing."""
    defaults = {
        "conversation_id": uuid4(),
        "user_message": "test message",
        "model_config": create_model_config(),
        "provider_name": "anthropic",
        "workflow_mode": "workbench",
        "context_data": {},
        "active_contexts": [],
        "conversation_history": [],
        "workflow_steps": [],
        "execution_successful": True,
        "retry_count": 0,
        "mcp_tools_active": [],
    }
    return ValidatedWorkbenchState(**{**defaults, **overrides})
```

### B. Centralized Validation Tests

**File:** `tests/unit/models/test_pydantic_validation.py`

```python
"""Centralized Pydantic validation tests."""
import pytest
from pydantic import ValidationError
from uuid import uuid4

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.models.consolidated_state import ValidatedWorkbenchState
from agent_workbench.models.business_models import BusinessProfile

class TestModelConfigValidation:
    """Test ModelConfig field and model validators."""

    @pytest.mark.parametrize("invalid_provider", [
        "invalid",
        "unknown",
        "bad_provider",
        "ANTHROPIC",  # Should be lowercase
    ])
    def test_invalid_provider(self, invalid_provider):
        """Test that invalid providers are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(provider=invalid_provider, model_name="test-model")
        assert "not supported" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_temp", [2.1, 5.0, -0.1, 100])
    def test_invalid_temperature(self, invalid_temp):
        """Test temperature bounds validation."""
        with pytest.raises(ValidationError):
            ModelConfig(
                provider="anthropic",
                model_name="claude-3.5-sonnet",
                temperature=invalid_temp
            )

    def test_contradictory_sampling_params(self):
        """Test model validator catches contradictory sampling."""
        with pytest.raises(ValidationError) as exc_info:
            ModelConfig(
                provider="anthropic",
                model_name="claude-3.5-sonnet",
                temperature=0.0,  # Deterministic
                top_p=0.9  # Random
            )
        assert "Contradictory sampling" in str(exc_info.value)


class TestValidatedWorkbenchStateValidation:
    """Test ValidatedWorkbenchState field validators."""

    @pytest.mark.parametrize("invalid_retry", [6, 10, 100, -1])
    def test_invalid_retry_count(self, invalid_retry):
        """Test retry_count bounds validation."""
        with pytest.raises(ValidationError) as exc_info:
            ValidatedWorkbenchState(
                conversation_id=uuid4(),
                user_message="test",
                model_config=ModelConfig(provider="anthropic", model_name="claude-3.5-sonnet"),
                provider_name="anthropic",
                workflow_mode="workbench",
                retry_count=invalid_retry
            )
        if invalid_retry > 5:
            assert "exceed 5" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_provider_name", [
        "ANTHROPIC",  # Must be lowercase
        "open ai",  # No spaces
        "OpenRouter",  # Must be lowercase
    ])
    def test_invalid_provider_name(self, invalid_provider_name):
        """Test provider_name format validation."""
        with pytest.raises(ValidationError) as exc_info:
            ValidatedWorkbenchState(
                conversation_id=uuid4(),
                user_message="test",
                model_config=ModelConfig(provider="anthropic", model_name="claude-3.5-sonnet"),
                provider_name=invalid_provider_name,
                workflow_mode="workbench"
            )
        errors = str(exc_info.value)
        assert "lowercase" in errors or "spaces" in errors


class TestBusinessProfileValidation:
    """Test BusinessProfile field validators."""

    @pytest.mark.parametrize("invalid_url", [
        "not-a-url",
        "ftp://example.com",
        "example.com",  # Missing protocol
    ])
    def test_invalid_website_url(self, invalid_url):
        """Test website URL validation."""
        with pytest.raises(ValidationError) as exc_info:
            BusinessProfile(
                conversation_id=uuid4(),
                business_name="Test Business",
                website_url=invalid_url,
                business_type="E-commerce"
            )
        assert "http" in str(exc_info.value).lower()
```

### C. Remove Redundant Tests

You can now **safely delete** tests that only check field validation:

**Tests to Remove:**
- ❌ `test_temperature_too_high` - Pydantic Field(ge=0.0, le=2.0) handles this
- ❌ `test_temperature_too_low` - Pydantic Field(ge=0.0, le=2.0) handles this
- ❌ `test_empty_message` - Pydantic Field(min_length=1) handles this
- ❌ `test_invalid_uuid_format` - UUID type annotation handles this
- ❌ `test_max_tokens_negative` - Pydantic Field(gt=0) handles this
- ❌ `test_retry_count_negative` - Pydantic Field(ge=0) handles this

**Tests to Keep:**
- ✅ Business logic tests (e.g., `test_workflow_execution_order`)
- ✅ Integration tests (e.g., `test_database_conversation_lifecycle`)
- ✅ API endpoint tests (e.g., `test_chat_completion`)
- ✅ Service layer tests (e.g., `test_llm_service_streaming`)

**Estimated Test Reduction:** 20-30% fewer unit tests while **maintaining same coverage**

## Migration Plan

### Phase 1: Create Test Infrastructure (Week 1)
1. Create `src/agent_workbench/testing/factories.py` with factory functions
2. Create `tests/unit/models/test_pydantic_validation.py` with centralized validation tests
3. Add pytest fixtures for common test data in `tests/conftest.py`

### Phase 2: Refactor Existing Tests (Week 2-3)
1. Identify and remove redundant validation tests
2. Migrate test data creation to use factories
3. Update integration tests to use ValidatedWorkbenchState

### Phase 3: Establish Best Practices (Week 4)
1. Document testing patterns in this file
2. Create test templates for new features
3. Update CI/CD to enforce validation test coverage

## Expected Benefits

1. **30-40% reduction** in validation test code
2. **50% reduction** in test setup boilerplate
3. **Faster test execution** (fewer redundant checks)
4. **Better test maintainability** (centralized validation logic)
5. **Faster development** (test data factories speed up test writing)
6. **Earlier error detection** (ValidatedWorkbenchState catches state errors before LangGraph)

## Testing Patterns by Layer

### Model Layer
- Use Pydantic ValidationError assertions
- Test custom field validators (provider_name, retry_count, website_url)
- Test model validators (contradictory sampling params)
- **Don't test:** Built-in Field constraints (min_length, ge, le, pattern)

### Service Layer
- Use test data factories for model creation
- Test business logic, not validation
- Assume models are valid (Pydantic guarantees this)
- **Don't test:** Field validation (handled by models)

### API Layer
- Test endpoint behavior with valid/invalid requests
- Use factories to create request bodies
- Test 422 validation error responses (FastAPI + Pydantic)
- **Don't test:** Individual field validation (FastAPI does this automatically)

### Integration Layer
- Use ValidatedWorkbenchState for LangGraph state testing
- Test workflow execution with valid state
- Test error handling with validation failures
- **Don't test:** State field validation (ValidatedWorkbenchState handles this)

## Example Test File Using New Strategy

**File:** `tests/unit/services/test_consolidated_service_refactored.py`

```python
"""Refactored consolidated service tests using new Pydantic strategy."""
import pytest
from uuid import uuid4

from agent_workbench.services.consolidated_service import ConsolidatedWorkbenchService
from agent_workbench.testing.factories import (
    create_validated_workbench_state,
    create_model_config,
)

class TestConsolidatedWorkbenchService:
    """Test consolidated service using factory-based approach."""

    @pytest.fixture
    def service(self):
        """Create service instance."""
        return ConsolidatedWorkbenchService()

    @pytest.mark.asyncio
    async def test_execute_workflow_workbench_mode(self, service):
        """Test workbench workflow execution."""
        # Create valid state using factory
        validated_state = create_validated_workbench_state(
            workflow_mode="workbench",
            user_message="Debug this Python code"
        )
        state = validated_state.to_typeddict()

        # Execute workflow
        result = await service.execute_workflow(state)

        # Test business logic only
        assert result.execution_successful
        assert result.workflow_mode == "workbench"
        assert len(result.workflow_steps) > 0

    @pytest.mark.asyncio
    async def test_execute_workflow_seo_coach_mode(self, service):
        """Test SEO coach workflow execution."""
        # Create valid state with business profile
        validated_state = create_validated_workbench_state(
            workflow_mode="seo_coach",
            user_message="Analyze my website",
            business_profile={
                "business_name": "Test Business",
                "website_url": "https://example.com",
                "business_type": "E-commerce"
            }
        )
        state = validated_state.to_typeddict()

        result = await service.execute_workflow(state)

        assert result.execution_successful
        assert result.workflow_mode == "seo_coach"
        assert result.business_profile is not None
```

## References

- Pydantic Implementation Audit: `docs/PYDANTIC_IMPLEMENTATION_AUDIT.md`
- ValidatedWorkbenchState: `src/agent_workbench/models/consolidated_state.py:66-292`
- ModelConfig validators: `src/agent_workbench/models/schemas.py:82-130`
- Field examples: All models in `src/agent_workbench/models/`
