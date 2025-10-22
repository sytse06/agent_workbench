# Tests for state consistency in UI

from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_no_state_drift():
    """Verify UI doesn't maintain parallel state that can drift"""
    client = LangGraphClient()

    # Mock the HTTP client
    with (
        patch.object(client.client, "post") as mock_post,
        patch.object(client.client, "get") as mock_get,
    ):

        # Setup mock responses
        from unittest.mock import Mock

        mock_post_response = Mock()
        mock_post_response.json.return_value = {
            "assistant_response": "Test response",
            "conversation_id": "test-consistency",
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {},
        }
        mock_post_response.raise_for_status = MagicMock(return_value=None)
        mock_post_response.status_code = 200
        mock_post_response.headers = {}
        mock_post.return_value = mock_post_response

        # Setup mock response for GET requests (chat history)
        mock_get_response = Mock()
        mock_get_response.json.return_value = {
            "messages": [
                {
                    "content": "Hello",
                    "response": "Hi there!",
                    "role": "user",
                },
                {
                    "content": "Hi there!",
                    "response": "How can I help?",
                    "role": "assistant",
                },
            ]
        }
        mock_get_response.raise_for_status = MagicMock(return_value=None)
        mock_get_response.status_code = 200
        mock_get_response.headers = {}
        mock_get.return_value = mock_get_response

        # Send message
        await client.send_message(
            message="Hello",
            conversation_id="test-consistency",
            model_config={
                "provider": "openrouter",
                "model_name": "claude-3-5-sonnet-20241022",
            },
        )

        # Get history twice - should be identical (no caching/drift)
        history1 = await client.get_chat_history("test-consistency")
        history2 = await client.get_chat_history("test-consistency")

        assert history1 == history2
        assert len(history1) > 0


@pytest.mark.asyncio
async def test_error_recovery():
    """Test that UI gracefully handles LangGraph errors"""
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
