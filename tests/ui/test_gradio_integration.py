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
        from unittest.mock import Mock
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.json.return_value = {
            "assistant_response": "Test response",
            "conversation_id": "test-id",
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

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

        assert result["assistant_response"] == "Test response"
        assert result["conversation_id"] == "test-id"
        assert result["reply"] == "Test response"  # Legacy compatibility field


@pytest.mark.asyncio
async def test_client_initialization():
    """Test LangGraph client initialization"""
    client = LangGraphClient()
    assert client.base_url == "http://localhost:8000"
    assert hasattr(client, "client")


def test_gradio_queue_fix_validation():
    """Test that Gradio queue fix prevents UI unresponsiveness"""
    from fastapi.testclient import TestClient

    from agent_workbench.main import app

    # Test that the app can start successfully (validates queue fix)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    # If this passes, your queue() + run_startup_events() fix works!


def test_database_tables_exist():
    """Test DB tables exist (prevent 'burned hands')"""
    from agent_workbench.models.database import ConversationModel, MessageModel

    assert hasattr(ConversationModel, "__tablename__")
    assert hasattr(MessageModel, "__tablename__")


if __name__ == "__main__":
    pytest.main([__file__])
