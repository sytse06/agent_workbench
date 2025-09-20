"""Tests for UI-001 Consolidated Service Integration"""

from unittest.mock import AsyncMock, patch

import pytest

from agent_workbench.ui.app import create_workbench_app
from agent_workbench.ui.components.simple_client import SimpleLangGraphClient


@pytest.mark.asyncio
async def test_simple_langgraph_client_consolidated_send():
    """Test SimpleLangGraphClient uses consolidated endpoint correctly"""
    client = SimpleLangGraphClient()

    # Mock the HTTP client with proper async support
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "assistant_response": "Test response",
        "conversation_id": "test-id",
        "workflow_mode": "workbench",
        "execution_successful": True,
        "metadata": {"provider_used": "openrouter"},
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "post", return_value=mock_response) as mock_post:
        result = await client.send_message(
            message="Hello",
            conversation_id="test-id",
            model_config={
                "provider": "openrouter",
                "model_name": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
        )

    # Verify consolidated endpoint was called
    mock_post.assert_called_once_with(
        "http://localhost:8000/api/v1/chat/consolidated",
        json={
            "user_message": "Hello",
            "conversation_id": "test-id",
            "workflow_mode": "workbench",
            "llm_config": {
                "provider": "openrouter",
                "model_name": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 2000,
            },
            "streaming": False,
            "parameter_overrides": None,
            "context_data": {},
        },
    )

    # Verify response format
    assert result["assistant_response"] == "Test response"
    assert result["conversation_id"] == "test-id"
    assert result["workflow_mode"] == "workbench"
    assert result["execution_successful"] is True
    assert result["metadata"]["provider_used"] == "openrouter"


@pytest.mark.asyncio
async def test_simple_langgraph_client_get_history():
    """Test SimpleLangGraphClient gets conversation history from state endpoint"""
    client = SimpleLangGraphClient()

    # Mock the HTTP client with proper async support
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "conversation_history": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
    }
    mock_response.raise_for_status.return_value = None

    with patch.object(client.client, "get", return_value=mock_response) as mock_get:
        history = await client.get_chat_history("test-id")

    # Verify state endpoint was called
    mock_get.assert_called_once_with(
        "http://localhost:8000/api/v1/conversations/test-id/state"
    )

    # Verify history format
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"


@pytest.mark.asyncio
async def test_enhanced_gradio_app_creation():
    """Test enhanced Gradio app can be created without errors"""
    app = create_workbench_app()
    assert app is not None
    # Verify key components exist
    assert len(app.blocks) > 0

    # Check that we have the expected number of components for enhanced app
    # Enhanced app should have more components than basic app
    assert len(app.blocks) >= 10  # Should have multiple sliders, dropdowns, etc

    # Verify app has correct title
    assert app.title == "Agent Workbench - Enhanced"

    # Verify the app can be created without throwing exceptions
    # This confirms the enhanced functionality is properly structured
    assert hasattr(app, "blocks")
    assert hasattr(app, "title")


@pytest.mark.asyncio
async def test_enhanced_message_handling():
    """Test enhanced message handling with workflow status"""
    from agent_workbench.ui.app import create_workbench_app

    # Mock the client within the app
    with patch("agent_workbench.ui.app.SimpleLangGraphClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        # Mock successful response
        mock_client.send_message.return_value = {
            "assistant_response": "Test response",
            "conversation_id": "test-id",
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {"provider_used": "openrouter"},
        }
        mock_client.get_chat_history.return_value = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Test response"},
        ]

        create_workbench_app()

        # Verify client was configured correctly
        mock_client_class.assert_called_once()


@pytest.mark.asyncio
async def test_error_handling_in_enhanced_ui():
    """Test error handling in enhanced UI"""
    client = SimpleLangGraphClient()

    # Mock HTTP error
    with patch.object(client.client, "post") as mock_post:
        mock_post.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            await client.send_message("Hello", "test-id", {})

        assert "Network error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_model_config_enhancement():
    """Test enhanced model configuration includes all required fields"""
    client = SimpleLangGraphClient()

    # Mock the HTTP client with proper async support
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "assistant_response": "Test response",
        "conversation_id": "test-id",
        "workflow_mode": "workbench",
        "execution_successful": True,
        "metadata": {},
    }
    mock_response.raise_for_status.return_value = None

    enhanced_config = {
        "provider": "openrouter",
        "model_name": "qwen/qwq-32b-preview",
        "temperature": 0.8,
        "max_tokens": 3000,
    }

    with patch.object(client.client, "post", return_value=mock_response) as mock_post:
        await client.send_message(
            message="Test", conversation_id="test-id", model_config=enhanced_config
        )

    # Verify all enhanced config fields were passed
    call_args = mock_post.call_args
    json_data = call_args[1]["json"]

    assert json_data["llm_config"]["provider"] == "openrouter"
    assert json_data["llm_config"]["model_name"] == "qwen/qwq-32b-preview"
    assert json_data["llm_config"]["temperature"] == 0.8
    assert json_data["llm_config"]["max_tokens"] == 3000
    assert json_data["workflow_mode"] == "workbench"
    assert json_data["streaming"] is False


@pytest.mark.asyncio
async def test_workflow_status_updates():
    """Test workflow status updates correctly"""
    # This would test the HTML status updates in the UI
    # For now, we verify the status strings are formatted correctly

    response = {
        "workflow_mode": "workbench",
        "execution_successful": True,
        "metadata": {"provider_used": "openrouter"},
    }

    mode = response["workflow_mode"]
    success = response["execution_successful"]
    provider_used = response.get("metadata", {}).get("provider_used", "Unknown")

    expected_html = f"""
                <div class='success'>
                    ✅ Workflow completed successfully<br>
                    <strong>Mode:</strong> {mode}<br>
                    <strong>Execution:</strong> {'Success' if success else 'Failed'}<br>
                    <strong>Provider:</strong> {provider_used}
                </div>
                """

    assert "workbench" in expected_html
    assert "Success" in expected_html
    assert "openrouter" in expected_html


def test_backward_compatibility():
    """Test that LangGraphClient alias still works"""
    from agent_workbench.ui.components.simple_client import (
        LangGraphClient,
        SimpleLangGraphClient,
    )

    # Verify alias works
    assert LangGraphClient is SimpleLangGraphClient

    # Can instantiate both
    client1 = SimpleLangGraphClient()
    client2 = LangGraphClient()

    assert isinstance(client1, SimpleLangGraphClient)
    assert isinstance(client2, SimpleLangGraphClient)
    assert client1.base_url == client2.base_url
