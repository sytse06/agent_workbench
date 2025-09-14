"""Tests for conversation service."""

from unittest.mock import patch
from uuid import UUID

import pytest

from agent_workbench.models.schemas import ConversationResponse
from agent_workbench.services.chat_models import ModelConfig
from agent_workbench.services.conversation_service import ConversationService


class TestConversationService:
    """Tests for ConversationService class."""

    def setup_method(self):
        """Setup method for tests."""
        self.service = ConversationService()

    @pytest.mark.asyncio
    async def test_create_conversation_without_title(self):
        """Test create_conversation without title."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = await self.service.create_conversation()

            assert isinstance(result, UUID)
            assert result == conversation_id

    @pytest.mark.asyncio
    async def test_create_conversation_with_title(self):
        """Test create_conversation with title."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = await self.service.create_conversation(title="Test Conversation")

            assert isinstance(result, UUID)
            assert result == conversation_id

    @pytest.mark.asyncio
    async def test_create_conversation_with_model_config(self):
        """Test create_conversation with model config."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")
        model_config = ModelConfig(
            provider="ollama", model_name="llama3", temperature=0.7, max_tokens=1000
        )

        with patch(
            "agent_workbench.services.conversation_service.uuid4",
            return_value=conversation_id,
        ):
            result = await self.service.create_conversation(
                title="Test Conversation", model_config=model_config
            )

            assert isinstance(result, UUID)
            assert result == conversation_id

    @pytest.mark.asyncio
    async def test_get_conversations(self):
        """Test get_conversations method."""
        # Should return empty list for now
        result = await self.service.get_conversations()

        assert isinstance(result, list)
        assert result == []

    @pytest.mark.asyncio
    async def test_get_conversations_with_limit(self):
        """Test get_conversations with limit."""
        # Should return empty list for now
        result = await self.service.get_conversations(limit=10)

        assert isinstance(result, list)
        assert result == []
        # In practice, this would test limiting, but we return empty list

    @pytest.mark.asyncio
    async def test_delete_conversation(self):
        """Test delete_conversation method."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        # Should return True for now (placeholder)
        result = await self.service.delete_conversation(conversation_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_get_conversation(self):
        """Test get_conversation method."""
        conversation_id = UUID("12345678-1234-5678-1234-567812345678")

        # Should return ConversationResponse
        result = await self.service.get_conversation(conversation_id)

        assert result is not None
        assert isinstance(result, ConversationResponse)
        assert result.id == conversation_id
        assert result.title == "Mock Conversation"
