"""Main LLM service for chat completions and model management."""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from ..core.exceptions import LLMProviderError, ModelConfigurationError, StreamingError
from ..core.retry import retry_llm_call
from ..models.api_models import ChatResponse
from ..models.schemas import ModelConfig
from ..models.standard_messages import StandardMessage
from .providers import provider_registry

logger = logging.getLogger(__name__)

_ROLE_TO_LC: dict = {
    "user": HumanMessage,
    "assistant": AIMessage,
    "system": SystemMessage,
    "tool": ToolMessage,
}


def standard_to_lc(msg: StandardMessage) -> BaseMessage:
    """Convert StandardMessage to the appropriate LangChain message type."""
    cls = _ROLE_TO_LC.get(msg.role, HumanMessage)
    return cls(content=msg.content)


class ChatService:
    """Service for managing LLM chat completions and conversations."""

    def __init__(self, model_config: ModelConfig):
        """
        Initialize chat service with model configuration.

        Args:
            model_config: Model configuration for the service
        """
        self.model_config = model_config
        self._chat_model: Optional[BaseChatModel] = None

    @property
    def chat_model(self) -> BaseChatModel:
        """
        Get or create the chat model instance.

        Returns:
            Chat model instance

        Raises:
            LLMProviderError: If provider is not supported
            ModelConfigurationError: If model configuration is invalid
        """
        if self._chat_model is None:
            self._chat_model = self._create_chat_model()
        return self._chat_model

    def _create_chat_model(self) -> BaseChatModel:
        """
        Create chat model instance using streamlined provider registry.

        Returns:
            Chat model instance

        Raises:
            LLMProviderError: If provider is not supported
            ModelConfigurationError: If model configuration is invalid
        """
        try:
            # Use streamlined provider registry for model creation
            return provider_registry.create_model(self.model_config)
        except ValueError as e:
            # Provider not found
            raise LLMProviderError(str(e), provider=self.model_config.provider) from e
        except ImportError as e:
            # Missing dependencies
            raise LLMProviderError(
                f"Missing dependencies for provider "
                f"'{self.model_config.provider}': {str(e)}",
                provider=self.model_config.provider,
            ) from e
        except Exception as e:
            # Model configuration or creation error
            raise ModelConfigurationError(
                f"Failed to create model for provider "
                f"'{self.model_config.provider}': {str(e)}",
                model_config=self.model_config.model_dump(),
            ) from e

    @retry_llm_call
    async def chat_completion(
        self,
        message: str,
        conversation_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ChatResponse:
        """
        Generate chat completion response.

        Args:
            message: User message
            conversation_id: Existing conversation ID (optional)
            context: Additional context data (optional)

        Returns:
            Chat response with assistant message

        Raises:
            LLMProviderError: If provider call fails
            ConversationError: If conversation management fails
        """
        try:
            # Get conversation history if provided
            messages = await self._prepare_messages(message, conversation_id, context)

            # Generate response
            response = await self.chat_model.ainvoke(messages)
            assistant_message: str = str(response.content)

            # Save conversation if ID provided
            if conversation_id:
                await self._save_message(
                    conversation_id=conversation_id, role="user", content=message
                )
                await self._save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=assistant_message,
                )

            return ChatResponse(
                message=assistant_message,
                conversation_id=conversation_id or UUID(int=0),
                model_used=f"{self.model_config.provider}:{self.model_config.model_name}",
                llm_config=self.model_config,
            )

        except Exception as e:
            logger.error(f"Chat completion failed: {str(e)}")
            if "LLMProviderError" in str(type(e)):
                raise
            raise LLMProviderError(f"Chat completion failed: {str(e)}") from e

    @retry_llm_call
    async def stream_completion(
        self,
        message: str,
        conversation_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat completion response.

        Args:
            message: User message
            conversation_id: Existing conversation ID (optional)
            context: Additional context data (optional)

        Yields:
            Streamed response chunks

        Raises:
            LLMProviderError: If provider call fails
            StreamingError: If streaming fails
        """
        try:
            # Get conversation history if provided
            messages = await self._prepare_messages(message, conversation_id, context)

            # Stream response
            full_response = ""
            async for chunk in self.chat_model.astream(messages):
                content = chunk.content
                if content:
                    full_response += content
                    yield content

            # Save conversation if ID provided
            if conversation_id:
                await self._save_message(
                    conversation_id=conversation_id, role="user", content=message
                )
                await self._save_message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=full_response,
                )

        except Exception as e:
            logger.error(f"Stream completion failed: {str(e)}")
            if "StreamingError" in str(type(e)):
                raise
            raise StreamingError(f"Stream completion failed: {str(e)}") from e

    async def _prepare_messages(
        self,
        message: str,
        conversation_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[BaseMessage]:
        """
        Prepare messages for chat model including history.

        Args:
            message: Current user message
            conversation_id: Conversation ID for history (optional)
            context: Additional context data (optional)

        Returns:
            List of LangChain messages
        """
        messages = []

        # Add context as system message if provided
        if context:
            context_parts = []
            for key, value in context.items():
                context_parts.append(f"{key}: {value}")
            context_prompt = "Context Information:\n" + "\n".join(context_parts)
            messages.append(SystemMessage(content=context_prompt))

        # Add system prompt if provided
        if self.model_config.system_prompt:
            messages.append(SystemMessage(content=self.model_config.system_prompt))

        # Add conversation history if provided
        if conversation_id:
            history = await self._get_conversation_history(conversation_id)
            messages.extend(history)

        # Add current message
        messages.append(HumanMessage(content=message))

        return messages

    async def _get_conversation_history(
        self, conversation_id: UUID
    ) -> List[BaseMessage]:
        """
        Get conversation history from database.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of LangChain messages
        """
        try:
            # This would typically fetch from database
            # For now, return empty list - implement when needed
            return []
        except Exception as e:
            logger.warning(f"Failed to get conversation history: {str(e)}")
            return []

    async def _save_message(
        self, conversation_id: UUID, role: str, content: str
    ) -> None:
        """
        Save message to conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user/assistant/system)
            content: Message content
        """
        # This would typically save to database
        # Implementation to be added when database integration is ready
        pass

    async def get_available_models(self, provider: str) -> List[str]:
        """
        Get available models for a provider.

        Args:
            provider: Provider name

        Returns:
            List of available model names
        """
        # This would typically fetch from provider API
        # For now, return empty list - models will be validated at runtime
        return []

    # Internal methods for stateful service integration
    async def _chat_with_model(
        self, messages: List[BaseMessage], model_config: ModelConfig
    ) -> str:
        """
        Internal method to chat with model using provided messages.

        Args:
            messages: List of LangChain messages
            model_config: Model configuration

        Returns:
            Response content
        """
        # Temporarily override model config if different
        original_config = self.model_config
        if model_config != original_config:
            self.model_config = model_config
            try:
                chat_model = self._create_chat_model()
                response = await chat_model.ainvoke(messages)
            finally:
                self.model_config = original_config
        else:
            response = await self.chat_model.ainvoke(messages)

        return str(response.content)

    async def _stream_chat_with_model(
        self, messages: List[BaseMessage], model_config: ModelConfig
    ) -> AsyncGenerator[str, None]:
        """
        Internal method to stream chat with model using provided messages.

        Args:
            messages: List of LangChain messages
            model_config: Model configuration

        Yields:
            Response content chunks
        """
        # Temporarily override model config if different
        original_config = self.model_config
        if model_config != original_config:
            self.model_config = model_config
            try:
                chat_model = self._create_chat_model()
                async for chunk in chat_model.astream(messages):
                    content = chunk.content
                    if content:
                        yield content
            finally:
                self.model_config = original_config
        else:
            async for chunk in self.chat_model.astream(messages):
                content = chunk.content
                if content:
                    yield content


# Convenience functions for common use cases


async def create_chat_service(model_config: ModelConfig) -> ChatService:
    """
    Create chat service instance.

    Args:
        model_config: Model configuration

    Returns:
        Chat service instance
    """
    return ChatService(model_config)


async def get_default_chat_service() -> ChatService:
    """
    Get default chat service with common model configuration.

    Returns:
        Chat service instance with default configuration
    """
    default_config = ModelConfig(
        provider="ollama", model_name="llama3.1", temperature=0.7, max_tokens=1000
    )
    return ChatService(default_config)
