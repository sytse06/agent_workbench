"""Tests for simple chat endpoint (Phase 1)."""

from unittest.mock import AsyncMock, patch

import pytest

from src.agent_workbench.api.routes.simple_chat import (
    ModelTestRequest,
    ModelTestResponse,
    SimpleChatRequest,
    SimpleChatResponse,
    simple_chat,
)
from src.agent_workbench.api.routes.simple_chat import (
    test_model_connectivity as model_connectivity_endpoint,
)


@pytest.mark.asyncio
async def test_direct_chat_success():
    """Test successful direct chat response."""
    # Mock the SimpleChatWorkflow execution
    mock_workflow = AsyncMock()
    mock_workflow.execute = AsyncMock(
        return_value={
            "execution_successful": True,
            "assistant_response": "Hello! This is a test response.",
        }
    )

    with patch(
        "src.agent_workbench.api.routes.simple_chat.SimpleChatWorkflow"
    ) as mock_workflow_class:
        mock_workflow_class.return_value = mock_workflow

        request = SimpleChatRequest(
            message="Hello, test message",
            provider="openrouter",
            model_name="qwen/qwq-32b-preview",
        )

        response = await simple_chat(request)

        assert isinstance(response, SimpleChatResponse)
        assert response.content == "Hello! This is a test response."
        assert response.model_used == "qwen/qwq-32b-preview"
        assert response.provider_used == "openrouter"
        assert response.status == "success"
        assert response.latency_ms is not None


@pytest.mark.asyncio
async def test_direct_chat_failure():
    """Test direct chat error handling."""
    # Mock the SimpleChatWorkflow to raise an exception
    mock_workflow = AsyncMock()
    mock_workflow.execute = AsyncMock(side_effect=Exception("API connection failed"))

    with patch(
        "src.agent_workbench.api.routes.simple_chat.SimpleChatWorkflow"
    ) as mock_workflow_class:
        mock_workflow_class.return_value = mock_workflow

        request = SimpleChatRequest(
            message="Hello, test message",
            provider="openrouter",
            model_name="qwen/qwq-32b-preview",
        )

        # Should raise HTTPException
        with pytest.raises(Exception):  # HTTPException from FastAPI
            await simple_chat(request)


@pytest.mark.asyncio
async def test_model_connectivity_success():
    """Test successful model connectivity test."""
    mock_response = AsyncMock()
    mock_response.message = "Test response"

    with patch(
        "src.agent_workbench.api.routes.simple_chat.ChatService"
    ) as mock_service:
        mock_service.return_value.chat_completion = AsyncMock(
            return_value=mock_response
        )

        request = ModelTestRequest(
            provider="openrouter", model_name="qwen/qwq-32b-preview"
        )

        response = await model_connectivity_endpoint(request)

        assert isinstance(response, ModelTestResponse)
        assert response.status == "success"
        assert response.provider == "openrouter"
        assert response.model == "qwen/qwq-32b-preview"
        assert response.response_length == len("Test response")
        assert response.api_key_source == "environment_variable"
        assert response.latency_ms is not None


@pytest.mark.asyncio
async def test_model_connectivity_with_api_key():
    """Test model connectivity with custom API key."""
    mock_response = AsyncMock()
    mock_response.reply = "Test response"

    with patch(
        "src.agent_workbench.api.routes.simple_chat.ChatService"
    ) as mock_service:
        mock_service.return_value.chat_completion = AsyncMock(
            return_value=mock_response
        )

        request = ModelTestRequest(
            provider="openrouter",
            model_name="qwen/qwq-32b-preview",
            api_key="test-api-key",
        )

        response = await model_connectivity_endpoint(request)

        assert response.status == "success"
        assert response.api_key_source == "request_override"


@pytest.mark.asyncio
async def test_model_connectivity_failure():
    """Test model connectivity test failure."""
    with patch(
        "src.agent_workbench.api.routes.simple_chat.ChatService"
    ) as mock_service:
        mock_service.return_value.chat_completion = AsyncMock(
            side_effect=Exception("API connection failed")
        )

        request = ModelTestRequest(
            provider="openrouter", model_name="qwen/qwq-32b-preview"
        )

        response = await model_connectivity_endpoint(request)

        assert response.status == "failed"
        assert response.error == "API connection failed"
        assert response.provider == "openrouter"
        assert response.model == "qwen/qwq-32b-preview"


def test_direct_chat_request_validation():
    """Test simple chat request validation."""
    # Valid request
    request = SimpleChatRequest(message="Test message")
    assert request.message == "Test message"
    assert request.provider == "openrouter"  # default
    assert request.model_name == "anthropic/claude-3.5-sonnet"  # default

    # Custom parameters
    request = SimpleChatRequest(
        message="Test message",
        provider="anthropic",
        model_name="claude-3-sonnet",
        temperature=0.5,
        max_tokens=1000,
    )
    assert request.provider == "anthropic"
    assert request.model_name == "claude-3-sonnet"
    assert request.temperature == 0.5
    assert request.max_tokens == 1000


def test_model_test_request_validation():
    """Test model test request validation."""
    request = ModelTestRequest(provider="openrouter", model_name="qwen/qwq-32b-preview")
    assert request.provider == "openrouter"
    assert request.model_name == "qwen/qwq-32b-preview"
    assert request.test_message == "Test connection"  # default
    assert request.api_key is None  # default
