# Tests for LangGraph client integration

from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_client_send_message():
    """Test sending message through LangGraph client"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "post") as mock_post:
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.json.return_value = {
            "assistant_response": "Test response",
            "conversation_id": "test-id",
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {},
        }
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_post.return_value = mock_response

        result = await client.send_message(
            message="Hello",
            conversation_id="test-id",
            model_config={
                "provider": "openrouter",
                "model_name": "claude-3-5-sonnet-20241022",
            },
        )

        assert result["assistant_response"] == "Test response"
        assert result["reply"] == "Test response"  # Legacy compatibility
        assert result["conversation_id"] == "test-id"
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_client_get_chat_history():
    """Test getting chat history from LangGraph client"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "get") as mock_get:
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.json.return_value = {
            "messages": [
                {"content": "Hello", "role": "user"},
                {"content": "Hi there!", "role": "assistant"},
            ]
        }
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_get.return_value = mock_response

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
                    "model_name": "claude-3-5-sonnet-20241022",
                },
            )

        assert "Network error" in str(exc_info.value)


if __name__ == "__main__":
    pytest.main([__file__])
