# End-to-end chat flow tests

from unittest.mock import AsyncMock, patch

import pytest

from agent_workbench.ui.app import create_workbench_app
from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_end_to_end_chat_flow():
    """Test complete chat flow from UI to LangGraph"""
    # Create app
    app = create_workbench_app()
    assert app is not None

    # Test client interaction
    client = LangGraphClient()

    # Mock the HTTP client
    with (
        patch.object(client.client, "post") as mock_post,
        patch.object(client.client, "get") as mock_get,
    ):

        # Setup mock responses
        mock_post.return_value.json.return_value = {
            "reply": "Hello! How can I assist you today?",
            "conversation_id": "test-flow-id",
        }
        mock_post.return_value.raise_for_status = AsyncMock()

        mock_get.return_value.json.return_value = {
            "messages": [
                {"content": "Hello", "role": "user"},
                {"content": "Hello! How can I assist you today?", "role": "assistant"},
            ]
        }
        mock_get.return_value.raise_for_status = AsyncMock()

        # Test sending message
        result = await client.send_message(
            message="Hello",
            conversation_id="test-flow-id",
            model_config={
                "provider": "openrouter",
                "model": "claude-3-5-sonnet-20241022",
            },
        )

        assert result["reply"] == "Hello! How can I assist you today?"
        assert result["conversation_id"] == "test-flow-id"

        # Test getting history
        history = await client.get_chat_history("test-flow-id")
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {
            "role": "assistant",
            "content": "Hello! How can I assist you today?",
        }


@pytest.mark.asyncio
async def test_empty_message_handling():
    """Test handling of empty messages"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.json.return_value = {
            "reply": "",
            "conversation_id": "test-empty-id",
        }
        mock_post.return_value.raise_for_status = AsyncMock()

        result = await client.send_message(
            message="",
            conversation_id="test-empty-id",
            model_config={
                "provider": "openrouter",
                "model": "claude-3-5-sonnet-20241022",
            },
        )

        assert result["reply"] == ""
        assert result["conversation_id"] == "test-empty-id"


if __name__ == "__main__":
    pytest.main([__file__])
