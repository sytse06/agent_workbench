"""Stateful LLM service with conversation state management."""

from typing import Any, AsyncGenerator, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConversationError
from ..models.api_models import ChatRequest, ChatResponse
from ..models.schemas import ModelConfig
from ..models.standard_messages import ConversationState, StandardMessage
from .context_service import ContextService
from .llm_service import ChatService
from .message_converter import MessageConverter
from .state_manager import StateManager
from .temporary_manager import TemporaryManager


class StatefulLLMService:
    """Stateful LLM service with persistent conversation management."""

    def __init__(
        self,
        llm_service: ChatService,
        db_session: AsyncSession,
    ):
        """
        Initialize stateful LLM service.

        Args:
            llm_service: Base LLM service
            db_session: Database session
        """
        self.llm_service = llm_service
        self.db_session = db_session
        self.state_manager = StateManager(db_session)
        self.context_service = ContextService()
        self.temporary_manager = TemporaryManager(db_session)

    async def chat_with_state(
        self,
        request: ChatRequest,
        conversation_id: Optional[UUID] = None,
    ) -> ChatResponse:
        """
        Process chat request with state management.

        Args:
            request: Chat request
            conversation_id: Optional conversation ID

        Returns:
            Chat response with conversation ID

        Raises:
            ConversationError: If chat processing fails
        """
        try:
            # Create or load conversation state
            if conversation_id:
                state = await self.state_manager.load_conversation_state(
                    conversation_id
                )
            else:
                model_config = request.model_config or ModelConfig(
                    provider="ollama",
                    model_name="llama3.1",
                    temperature=0.7,
                    max_tokens=1000,
                )
                conversation_id = await self.state_manager.create_conversation(
                    model_config
                )
                state = await self.state_manager.load_conversation_state(
                    conversation_id
                )

            # Convert incoming message to standard format
            user_message = StandardMessage(
                role="user",
                content=request.message,
            )
            state.messages.append(user_message)

            # Build context if provided
            if request.context:
                context_prompt = await self.context_service.build_context_prompt(
                    request.context
                )
                if context_prompt:
                    context_message = StandardMessage(
                        role="system",
                        content=context_prompt,
                    )
                    # Insert context at the beginning for visibility
                    state.messages.insert(0, context_message)

            # Convert to LangChain format for LLM processing
            langchain_messages = MessageConverter.to_langchain_messages(state.messages)

            # Process with LLM
            response_content = await self.llm_service._chat_with_model(
                langchain_messages,
                state.model_config,
            )

            # Convert response to standard format
            assistant_message = StandardMessage(
                role="assistant",
                content=response_content,
            )
            state.messages.append(assistant_message)

            # Update state
            await self.state_manager.save_conversation_state(state)

            return ChatResponse(
                conversation_id=conversation_id,
                message=response_content,
                model_config=state.model_config,
            )

        except Exception as e:
            raise ConversationError(f"Failed to process chat: {str(e)}") from e

    async def stream_chat_with_state(
        self,
        request: ChatRequest,
        conversation_id: Optional[UUID] = None,
    ) -> AsyncGenerator[ChatResponse, None]:
        """
        Stream chat response with state management.

        Args:
            request: Chat request
            conversation_id: Optional conversation ID

        Yields:
            Chat responses with conversation ID

        Raises:
            ConversationError: If chat streaming fails
        """
        try:
            # Create or load conversation state
            if conversation_id:
                state = await self.state_manager.load_conversation_state(
                    conversation_id
                )
            else:
                model_config = request.model_config or ModelConfig(
                    provider="ollama",
                    model_name="llama3.1",
                    temperature=0.7,
                    max_tokens=1000,
                )
                conversation_id = await self.state_manager.create_conversation(
                    model_config
                )
                state = await self.state_manager.load_conversation_state(
                    conversation_id
                )

            # Convert incoming message to standard format
            user_message = StandardMessage(
                role="user",
                content=request.message,
            )
            state.messages.append(user_message)

            # Build context if provided
            if request.context:
                context_prompt = await self.context_service.build_context_prompt(
                    request.context
                )
                if context_prompt:
                    context_message = StandardMessage(
                        role="system",
                        content=context_prompt,
                    )
                    # Insert context at the beginning for visibility
                    state.messages.insert(0, context_message)

            # Convert to LangChain format for LLM processing
            langchain_messages = MessageConverter.to_langchain_messages(state.messages)

            # Stream response from LLM
            full_response = ""
            async for chunk in self.llm_service._stream_chat_with_model(
                langchain_messages,
                state.model_config,
            ):
                full_response += chunk
                yield ChatResponse(
                    conversation_id=conversation_id,
                    message=chunk,
                    model_config=state.model_config,
                )

            # Convert final response to standard format
            assistant_message = StandardMessage(
                role="assistant",
                content=full_response,
            )
            state.messages.append(assistant_message)

            # Update state
            await self.state_manager.save_conversation_state(state)

        except Exception as e:
            raise ConversationError(f"Failed to stream chat: {str(e)}") from e

    async def get_conversation_history(
        self, conversation_id: UUID
    ) -> List[StandardMessage]:
        """
        Get conversation history.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of messages in standard format

        Raises:
            ConversationError: If history retrieval fails
        """
        try:
            state = await self.state_manager.load_conversation_state(conversation_id)
            return state.messages

        except Exception as e:
            raise ConversationError(
                f"Failed to get conversation history: {str(e)}"
            ) from e

    async def clear_conversation_history(self, conversation_id: UUID) -> bool:
        """
        Clear conversation history.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful

        Raises:
            ConversationError: If clearing fails
        """
        try:
            state = await self.state_manager.load_conversation_state(conversation_id)
            state.messages = []
            await self.state_manager.save_conversation_state(state)
            return True

        except Exception as e:
            raise ConversationError(
                f"Failed to clear conversation history: {str(e)}"
            ) from e

    async def update_conversation_context(
        self, conversation_id: UUID, context_data: Dict[str, Any], sources: List[str]
    ) -> bool:
        """
        Update conversation context.

        Args:
            conversation_id: Conversation ID
            context_data: Context data to inject
            sources: Context source tracking

        Returns:
            True if successful

        Raises:
            ConversationError: If context update fails
        """
        try:
            await self.context_service.update_conversation_context(
                conversation_id, context_data, sources
            )
            return True

        except Exception as e:
            raise ConversationError(
                f"Failed to update conversation context: {str(e)}"
            ) from e

    async def list_conversations(self, limit: int = 50) -> List[Dict]:
        """
        List conversations with summary information.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries

        Raises:
            ConversationError: If listing fails
        """
        try:
            return await self.state_manager.list_conversations(limit)

        except Exception as e:
            raise ConversationError(f"Failed to list conversations: {str(e)}") from e

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete conversation and its history.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful

        Raises:
            ConversationError: If deletion fails
        """
        try:
            return await self.state_manager.delete_conversation(conversation_id)

        except Exception as e:
            raise ConversationError(f"Failed to delete conversation: {str(e)}") from e

    async def migrate_conversation(self, conversation_id: UUID) -> ConversationState:
        """
        Migrate existing conversation to stateful format.

        Args:
            conversation_id: Conversation ID

        Returns:
            Migrated conversation state

        Raises:
            ConversationError: If migration fails
        """
        try:
            return await self.state_manager.migrate_conversation_to_stateful(
                conversation_id
            )

        except Exception as e:
            raise ConversationError(f"Failed to migrate conversation: {str(e)}") from e

    async def cleanup_temporary_conversations(
        self, older_than_minutes: int = 60
    ) -> int:
        """
        Clean up expired temporary conversations.

        Args:
            older_than_minutes: Age threshold in minutes

        Returns:
            Number of conversations cleaned up

        Raises:
            ConversationError: If cleanup fails
        """
        try:
            cleanup_func = (
                self.temporary_manager.cleanup_expired_temporary_conversations
            )
            return await cleanup_func(older_than_minutes)

        except Exception as e:
            raise ConversationError(
                f"Failed to cleanup temporary conversations: {str(e)}"
            ) from e
