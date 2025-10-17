"""Tests for conversation service."""

from unittest.mock import patch
from uuid import UUID

from agent_workbench.models.api_models import ConversationResponse
from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.conversation_service import ConversationService


class TestConversationService:
    """Tests for ConversationService class."""

    def setup_method(self):
        """Setup method for tests."""
        self.service = ConversationService()

    # @pytest.mark.asyncio
    def test_create_conversation_without_title(self):
        """Test create_conversation without title."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = self.service.create_conversation()

            assert isinstance(result, str)
            assert result == str(conversation_id)

    # @pytest.mark.asyncio
    def test_create_conversation_with_title(self):
        """Test create_conversation with title."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = self.service.create_conversation(title="Test Conversation")

            assert isinstance(result, str)
            assert result == str(conversation_id)

    # @pytest.mark.asyncio
    def test_create_conversation_with_model_config(self):
        """Test create_conversation with model config."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")
        model_config = ModelConfig(
            provider="ollama",
            model_name="llama3",
            temperature=0.7,
            max_tokens=1000,
        )

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = self.service.create_conversation(
                title="Test Conversation", model_config=model_config
            )

            assert isinstance(result, str)
            assert result == str(conversation_id)

    def test_get_conversations(self):
        """Test get_conversations method."""
        with patch.object(self.service.db, "list_conversations", return_value=[]):
            result = self.service.get_conversations()

            assert isinstance(result, list)
            assert result == []

    def test_get_conversations_with_limit(self):
        """Test get_conversations with limit."""
        with patch.object(self.service.db, "list_conversations", return_value=[]):
            result = self.service.get_conversations(limit=10)

            assert isinstance(result, list)
            assert result == []

    def test_delete_conversation(self):
        """Test delete_conversation method."""
        conversation_id = str(UUID("12345678-1234-5678-1234-567812345678"))

        # Mock database session with regular Mock (not AsyncMock)
        from unittest.mock import MagicMock

        mock_session = MagicMock()

        # Create service with mock session
        service_with_session = ConversationService(db=mock_session)

        # Mock database delete_conversation method to return boolean directly
        mock_session.delete_conversation.return_value = False
        result = service_with_session.delete_conversation(conversation_id)
        assert result is False

        # Mock successful deletion
        mock_session.delete_conversation.return_value = True
        result = service_with_session.delete_conversation(conversation_id)
        assert result is True

    def test_get_conversation(self):
        """Test get_conversation method."""
        conversation_id = "12345678-1234-5678-1234-567812345678"

        # Mock the database to return a conversation
        mock_conversation = {
            "id": conversation_id,
            "title": "Test Conversation",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }

        with patch.object(
            self.service.db, "get_conversation", return_value=mock_conversation
        ):
            with patch.object(self.service.db, "get_messages", return_value=[]):
                result = self.service.get_conversation(conversation_id)

                assert result is not None
                assert isinstance(result, ConversationResponse)
                assert result.id == UUID(conversation_id)
