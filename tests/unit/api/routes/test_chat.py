"""Tests for chat API routes."""

from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from agent_workbench.main import app
from agent_workbench.models.state_requests import ChatResponse
from agent_workbench.services.chat_models import ModelConfig

client = TestClient(app)


class TestChatRoutes:
    """Tests for chat API routes."""

    def setup_method(self):
        """Setup method for tests."""
        self.model_config = ModelConfig(
            provider="ollama", model_name="llama3", temperature=0.7, max_tokens=1000
        )

    @patch("agent_workbench.api.routes.chat.create_chat_service")
    def test_chat_completion(self, mock_create_chat_service):
        """Test POST /api/v1/chat endpoint."""
        # Setup mock
        mock_service_instance = AsyncMock()
        mock_response = ChatResponse(
            content="Hello! How can I help you?",
            conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
            model_used="ollama:llama3",
            llm_config=self.model_config,
        )
        mock_service_instance.chat_completion.return_value = mock_response
        mock_create_chat_service.return_value = mock_service_instance

        # Test data
        chat_request = {
            "message": "Hello!",
            "llm_config": {
                "provider": "ollama",
                "model_name": "llama3",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        # Make request
        response = client.post("/api/v1/chat", json=chat_request)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello! How can I help you?"
        assert data["conversation_id"] == "12345678-1234-5678-1234-567812345678"
        mock_service_instance.chat_completion.assert_called_once()

    @patch("agent_workbench.api.routes.chat.create_chat_service")
    def test_chat_completion_with_conversation(self, mock_create_chat_service):
        """Test POST /api/v1/chat endpoint with conversation ID."""
        # Setup mock
        mock_service_instance = AsyncMock()
        mock_response = ChatResponse(
            content="Hello! How can I help you?",
            conversation_id=UUID("12345678-1234-5678-1234-567812345678"),
            model_used="ollama:llama3",
            llm_config=self.model_config,
        )
        mock_service_instance.chat_completion.return_value = mock_response
        mock_create_chat_service.return_value = mock_service_instance

        # Test data
        chat_request = {
            "message": "Hello!",
            "conversation_id": "12345678-1234-5678-1234-567812345678",
            "llm_config": {
                "provider": "ollama",
                "model_name": "llama3",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        # Make request
        response = client.post("/api/v1/chat", json=chat_request)

        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello! How can I help you?"
        assert data["conversation_id"] == "12345678-1234-5678-1234-567812345678"
        mock_service_instance.chat_completion.assert_called_once()

    @patch("agent_workbench.api.routes.chat.create_chat_service")
    def test_chat_completion_invalid_request(self, mock_create_chat_service):
        """Test POST /api/v1/chat endpoint with minimal request (uses defaults)."""
        # Setup mock
        mock_service_instance = AsyncMock()
        mock_response = ChatResponse(
            content="Hello! How can I help you?",
            conversation_id=None,
            model_used="ollama:llama3.1",
            llm_config=ModelConfig(
                provider="ollama",
                model_name="llama3.1",
                temperature=0.7,
                max_tokens=1000,
            ),
        )
        mock_service_instance.chat_completion.return_value = mock_response
        mock_create_chat_service.return_value = mock_service_instance

        # Test data with minimal fields (llm_config will use defaults)
        chat_request = {
            "message": "Hello!"
            # Missing llm_config - should use defaults
        }

        # Make request
        response = client.post("/api/v1/chat", json=chat_request)

        # Assertions - should succeed with defaults
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Hello! How can I help you?"
        assert data["model_used"] == "ollama:llama3.1"

    def test_stream_chat(self):
        """Test POST /api/v1/chat/stream endpoint."""
        # This test would require more complex setup for streaming
        # For now, we'll test that the endpoint exists
        response = client.post("/api/v1/chat/stream", json={})

        # Should fail due to validation, not because endpoint doesn't exist
        assert response.status_code == 422
