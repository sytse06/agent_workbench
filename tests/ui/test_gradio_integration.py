# Unit tests for Gradio UI integration

from unittest.mock import patch

import pytest

from agent_workbench.ui.app import create_workbench_app
from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_gradio_app_creation():
    """Test Gradio app can be created without errors"""
    app = create_workbench_app()
    assert app is not None
    # Verify key components exist
    assert len(app.blocks) > 0


@pytest.mark.asyncio
async def test_message_handling():
    """Test message flow through simplified interface"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "post") as mock_post:
        mock_post.return_value.json.return_value = {
            "reply": "Test response",
            "conversation_id": "test-id",
        }

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


@pytest.mark.asyncio
async def test_client_initialization():
    """Test LangGraph client initialization"""
    client = LangGraphClient()
    assert client.base_url == "http://localhost:8000"
    assert hasattr(client, "client")


if __name__ == "__main__":
    pytest.main([__file__])
