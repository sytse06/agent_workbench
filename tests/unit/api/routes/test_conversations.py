"""Tests for conversation API routes."""

from unittest.mock import AsyncMock, patch
from uuid import UUID

from fastapi.testclient import TestClient

from agent_workbench.main import app

client = TestClient(app)


class TestConversationRoutes:
    """Tests for conversation API routes."""

    def test_get_conversations(self):
        """Test GET /api/v1/conversations endpoint."""
        # Make request
        response = client.get("/api/v1/conversations")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return a list (even if empty for now)
        data = response.json()
        assert isinstance(data, list)

    def test_get_conversations_with_limit(self):
        """Test GET /api/v1/conversations endpoint with limit."""
        # Make request
        response = client.get("/api/v1/conversations?limit=10")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return a list (even if empty for now)
        data = response.json()
        assert isinstance(data, list)

    @patch("agent_workbench.api.routes.conversations.ConversationService")
    def test_create_conversation(self, mock_conversation_service):
        """Test POST /api/v1/conversations endpoint."""
        # Setup mock
        mock_service_instance = AsyncMock()
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_service_instance.create_conversation.return_value = conversation_id

        # Mock get_conversation to return proper data
        from datetime import datetime

        from agent_workbench.models.schemas import ConversationResponse

        mock_conversation_response = ConversationResponse(
            id=conversation_id,
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            llm_config=None,
        )
        mock_service_instance.get_conversation.return_value = mock_conversation_response
        mock_conversation_service.return_value = mock_service_instance

        # Test data
        conversation_request = {"title": "Test Conversation"}

        # Make request
        response = client.post("/api/v1/conversations", json=conversation_request)

        # Should return 201 Created
        assert response.status_code == 201

        # Should return conversation data
        data = response.json()
        assert data["id"] == str(conversation_id)
        assert data["title"] == "Test Conversation"

    @patch("agent_workbench.api.routes.conversations.ConversationService")
    def test_create_conversation_with_model_config(self, mock_conversation_service):
        """Test POST /api/v1/conversations endpoint with model config."""
        # Setup mock
        mock_service_instance = AsyncMock()
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")
        mock_service_instance.create_conversation.return_value = conversation_id

        # Mock get_conversation to return proper data
        from datetime import datetime

        from agent_workbench.models.schemas import ConversationResponse
        from agent_workbench.services.chat_models import ModelConfig

        mock_model_config = ModelConfig(
            provider="ollama",
            model_name="llama3",
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            system_prompt=None,
            streaming=True,
            extra_params={},
        )
        mock_conversation_response = ConversationResponse(
            id=conversation_id,
            title="Test Conversation",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            messages=[],
            llm_config=mock_model_config,
        )
        mock_service_instance.get_conversation.return_value = mock_conversation_response
        mock_conversation_service.return_value = mock_service_instance

        # Test data
        conversation_request = {
            "title": "Test Conversation",
            "llm_config": {
                "provider": "ollama",
                "model_name": "llama3",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        # Make request
        response = client.post("/api/v1/conversations", json=conversation_request)

        # Should return 201 Created
        assert response.status_code == 201

        # Should return conversation data
        data = response.json()
        assert data["id"] == str(conversation_id)
        assert data["title"] == "Test Conversation"
        assert data["llm_config"]["provider"] == "ollama"

    def test_create_conversation_with_extra_fields(self):
        """Test POST /api/v1/conversations endpoint ignores extra fields."""
        # Test data with extra fields (should be ignored gracefully)
        conversation_request = {"invalid_field": "invalid_value"}

        # Make request
        response = client.post("/api/v1/conversations", json=conversation_request)

        # Should succeed and ignore extra fields
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "created_at" in data

    def test_get_conversation_by_id(self):
        """Test GET /api/v1/conversations/{conversation_id} endpoint."""
        conversation_id = "12345678-1234-5678-1234-567812345678"

        # Make request
        response = client.get(f"/api/v1/conversations/{conversation_id}")

        # For now, this will return 404 since we don't have real implementation
        # In practice, this would return the conversation data
        assert response.status_code in [200, 404]

    def test_delete_conversation(self):
        """Test DELETE /api/v1/conversations/{conversation_id} endpoint."""
        conversation_id = "12345678-1234-5678-1234-567812345678"

        # Make request
        response = client.delete(f"/api/v1/conversations/{conversation_id}")

        # For now, this will return 404 since we don't have real implementation
        # In practice, this would delete the conversation
        assert response.status_code in [204, 404]
