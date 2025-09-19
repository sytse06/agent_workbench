# Tests for LangGraph client integration

from unittest.mock import AsyncMock, patch

import pytest

from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_client_send_message():
    """Test sending message through LangGraph client"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.json.return_value = {
            "reply": "Test response",
            "conversation_id": "test-id",
        }
        mock_post.return_value.raise_for_status = AsyncMock()

        result = await client.send_message(
            message="Hello",
            conversation_id="test-id",
            model_config={
                "provider": "openrouter",
                "model": "claude-3-5-sonnet-20241022",
            },
        )

        assert result["reply"] == "Test response"
        assert result["conversation_id"] == "test-id"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_client_get_chat_history():
    """Test getting chat history from LangGraph client"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "get") as mock_get:
        mock_get.return_value.json.return_value = {
            "messages": [
                {"content": "Hello", "role": "user"},
                {"content": "Hi there!", "role": "assistant"},
            ]
        }
        mock_get.return_value.raise_for_status = AsyncMock()

        history = await client.get_chat_history("test-id")

        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "assistant", "content": "Hi there!"}
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_client_error_handling():
    """Test error handling in LangGraph client"""
    client = LangGraphClient()

    # Mock the HTTP client to raise an exception
    with patch.object(client.client, "post") as mock_post:
        mock_post.side_effect = Exception("Network error")

        with pytest.raises(Exception) as exc_info:
            await client.send_message(
                message="Hello",
                conversation_id="test-id",
                model_config={
                    "provider": "openrouter",
                    "model": "claude-3-5-sonnet-20241022",
                },
            )

        assert "Network error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
