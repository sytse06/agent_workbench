"""Tests for LLM service."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from agent_workbench.models.state_requests import ChatResponse
from agent_workbench.services.chat_models import ModelConfig
from agent_workbench.services.llm_service import (
    ChatService,
    create_chat_service,
    get_default_chat_service,
)


class TestChatService:
    """Tests for ChatService class."""

    def setup_method(self):
        """Setup method for tests."""
        self.model_config = ModelConfig(
            provider="ollama", model_name="llama3", temperature=0.7, max_tokens=1000
        )

    def test_chat_service_initialization(self):
        """Test ChatService initialization."""
        service = ChatService(self.model_config)

        assert service.model_config == self.model_config
        assert service._chat_model is None

    def test_chat_model_property(self):
        """Test chat_model property."""
        with patch(
            "agent_workbench.services.llm_service.provider_registry"
        ) as mock_registry:
            mock_model = MagicMock()
            mock_registry.create_model.return_value = mock_model

            service = ChatService(self.model_config)
            chat_model = service.chat_model

            assert chat_model == mock_model
            mock_registry.create_model.assert_called_once_with(self.model_config)

    @pytest.mark.asyncio
    async def test_chat_completion_with_conversation(self):
        """Test chat_completion with conversation ID."""
        # Mock the retry decorator to avoid actual retries
        with patch("agent_workbench.services.llm_service.retry_llm_call") as mock_retry:
            mock_retry.side_effect = lambda func: func

            # Create service and mock the chat_model property
            service = ChatService(self.model_config)
            mock_model = AsyncMock()
            mock_response = MagicMock()
            mock_response.content = "Hello! How can I help you?"
            mock_model.ainvoke.return_value = mock_response

            # Use property setter to mock the chat_model
            service._chat_model = mock_model

            # Test
            conversation_id = UUID("12345678-1234-5678-1234-567812345678")
            result = await service.chat_completion("Hello!", conversation_id)

            # Assertions
            assert isinstance(result, ChatResponse)
            assert result.reply == "Hello! How can I help you?"
            assert result.conversation_id == conversation_id
            assert result.llm_config == self.model_config
            mock_model.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_stream_completion(self):
        """Test stream_completion method."""
        # Mock the retry decorator to avoid actual retries
        with patch("agent_workbench.services.llm_service.retry_llm_call") as mock_retry:
            mock_retry.side_effect = lambda func: func

            # Create service and mock the chat_model property
            service = ChatService(self.model_config)

            # Create async iterable mock
            async def mock_astream(*args, **kwargs):
                chunks = [
                    MagicMock(content="Hello"),
                    MagicMock(content="!"),
                    MagicMock(content=" How"),
                    MagicMock(content=" are"),
                    MagicMock(content=" you"),
                    MagicMock(content="?"),
                ]
                for chunk in chunks:
                    yield chunk

            mock_model = AsyncMock()
            mock_model.astream = mock_astream

            # Use property setter to mock the chat_model
            service._chat_model = mock_model

            # Test
            chunks = []
            async for chunk in service.stream_completion("Hello!"):
                chunks.append(chunk)

            # Assertions
            expected_chunks = ["Hello", "!", " How", " are", " you", "?"]
            assert chunks == expected_chunks
            # Note: We can't easily assert the mock was called since it's an
            # async generator

    @pytest.mark.asyncio
    async def test_stream_completion_with_conversation(self):
        """Test stream_completion with conversation ID."""
        # Mock the retry decorator to avoid actual retries
        with patch("agent_workbench.services.llm_service.retry_llm_call") as mock_retry:
            mock_retry.side_effect = lambda func: func

            # Create service and mock the chat_model property
            service = ChatService(self.model_config)

            # Create async iterable mock
            async def mock_astream(*args, **kwargs):
                chunks = [
                    MagicMock(content="Hello"),
                    MagicMock(content="!"),
                    MagicMock(content=" How"),
                    MagicMock(content=" are"),
                    MagicMock(content=" you"),
                    MagicMock(content="?"),
                ]
                for chunk in chunks:
                    yield chunk

            mock_model = AsyncMock()
            mock_model.astream = mock_astream

            # Use property setter to mock the chat_model
            service._chat_model = mock_model

            # Test
            conversation_id = UUID("12345678-1234-5678-1234-567812345678")
            chunks = []
            async for chunk in service.stream_completion("Hello!", conversation_id):
                chunks.append(chunk)

            # Assertions
            expected_chunks = ["Hello", "!", " How", " are", " you", "?"]
            assert chunks == expected_chunks
            # Note: We can't easily assert the mock was called since it's
            # an async generator

    @pytest.mark.asyncio
    async def test_get_available_models(self):
        """Test get_available_models method."""
        service = ChatService(self.model_config)

        # Should return empty list for now
        models = await service.get_available_models("ollama")
        assert isinstance(models, list)
        assert models == []


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    @pytest.mark.asyncio
    async def test_create_chat_service(self):
        """Test create_chat_service function."""
        model_config = ModelConfig(
            provider="ollama", model_name="llama3", temperature=0.7, max_tokens=1000
        )

        service = await create_chat_service(model_config)

        assert isinstance(service, ChatService)
        assert service.model_config == model_config

    @pytest.mark.asyncio
    async def test_get_default_chat_service(self):
        """Test get_default_chat_service function."""
        service = await get_default_chat_service()

        assert isinstance(service, ChatService)
        assert service.model_config.provider == "ollama"
        assert service.model_config.model_name == "llama3.1"
        assert service.model_config.temperature == 0.7
        assert service.model_config.max_tokens == 1000
