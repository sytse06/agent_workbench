"""Service for managing conversations and their persistence."""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConversationError
from ..models.database import ConversationModel, MessageModel
from ..models.schemas import ConversationResponse, ConversationSummary
from .chat_models import ModelConfig


class ConversationService:
    """Enhanced service for managing conversation lifecycle.

    Provides database persistence for conversations.
    """

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """Initialize conversation service with optional database session."""
        self.db_session = db_session

    async def get_or_create(self, conversation_id: str) -> ConversationModel:
        """
        Get existing conversation or create new one with database persistence.

        Args:
            conversation_id: Conversation ID

        Returns:
            ConversationModel instance

        Raises:
            ConversationError: If database operation fails
        """
        try:
            if not self.db_session:
                raise ConversationError("No database session available")

            # Try to get existing conversation
            conversation = await ConversationModel.get_by_id(
                self.db_session, UUID(conversation_id)
            )

            if not conversation:
                # Create new conversation
                conversation = await ConversationModel.create(
                    self.db_session,
                    id=UUID(conversation_id),
                    title=f"Conversation {conversation_id[:8]}",
                )

            return conversation
        except Exception as e:
            error_msg = f"Failed to get or create conversation: {str(e)}"
            raise ConversationError(error_msg) from e

    async def add_message(self, conv_id: str, role: str, content: str) -> MessageModel:
        """
        Add message to conversation with database persistence.

        Args:
            conv_id: Conversation ID
            role: Message role (user, assistant, system, tool)
            content: Message content

        Returns:
            MessageModel instance

        Raises:
            ConversationError: If database operation fails
        """
        try:
            if not self.db_session:
                raise ConversationError("No database session available")

            # Create message in database
            message = await MessageModel.create(
                self.db_session,
                conversation_id=UUID(conv_id),
                role=role,
                content=content,
            )

            return message
        except Exception as e:
            error_msg = f"Failed to add message: {str(e)}"
            raise ConversationError(error_msg) from e

    async def get_history(self, conversation_id: str) -> List[Dict]:
        """
        Get conversation history from database.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of message dictionaries

        Raises:
            ConversationError: If database operation fails
        """
        try:
            if not self.db_session:
                raise ConversationError("No database session available")

            # Get messages from database
            messages = await MessageModel.get_by_conversation(
                self.db_session, UUID(conversation_id)
            )

            # Convert to dictionary format
            history = []
            for message in messages:
                history.append(
                    {
                        "role": message.role,
                        "content": message.content,
                        "created_at": message.created_at.isoformat(),
                    }
                )

            return history
        except Exception as e:
            error_msg = f"Failed to get conversation history: {str(e)}"
            raise ConversationError(error_msg) from e

    async def update_context(self, conv_id: str, context: Dict) -> None:
        """
        Update conversation context in database.

        Args:
            conv_id: Conversation ID
            context: Context data to store

        Raises:
            ConversationError: If database operation fails
        """
        try:
            if not self.db_session:
                raise ConversationError("No database session available")

            # Get conversation
            conversation = await ConversationModel.get_by_id(
                self.db_session, UUID(conv_id)
            )

            if conversation:
                # Update conversation with context metadata
                await conversation.update(
                    self.db_session, title=context.get("title", conversation.title)
                )
        except Exception as e:
            error_msg = f"Failed to update conversation context: {str(e)}"
            raise ConversationError(error_msg) from e

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation from database.

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if successful

        Raises:
            ConversationError: If deletion fails
        """
        try:
            if not self.db_session:
                raise ConversationError("No database session available")

            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )

            if conversation:
                await conversation.delete(self.db_session)
                return True

            return False
        except Exception as e:
            error_msg = f"Failed to delete conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e

    # Legacy methods for backward compatibility
    async def create_conversation(
        self,
        title: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        is_temporary: bool = False,
    ) -> UUID:
        """Create a new conversation (legacy method)."""
        try:
            conversation_id = uuid4()
            if self.db_session:
                await ConversationModel.create(
                    self.db_session,
                    id=conversation_id,
                    title=title or f"Conversation {str(conversation_id)[:8]}",
                )
            return conversation_id
        except Exception as e:
            error_msg = f"Failed to create conversation: {str(e)}"
            raise ConversationError(error_msg) from e

    async def get_conversations(self, limit: int = 50) -> List[ConversationSummary]:
        """Get list of conversations (legacy method)."""
        try:
            if not self.db_session:
                return []

            # This would need proper implementation with database query
            # For now, return empty list
            return []
        except Exception as e:
            error_msg = f"Failed to fetch conversations: {str(e)}"
            raise ConversationError(error_msg) from e

    async def get_conversation(self, conversation_id: UUID) -> ConversationResponse:
        """Get conversation details (legacy method)."""
        try:
            if not self.db_session:
                from datetime import datetime

                return ConversationResponse(
                    id=conversation_id,
                    title="Mock Conversation",
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    messages=[],
                    llm_config=None,
                )

            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )

            if conversation:
                return ConversationResponse(
                    id=conversation.id,
                    title=conversation.title or "Untitled",
                    created_at=conversation.created_at,
                    updated_at=conversation.updated_at,
                    messages=[],
                    llm_config=None,
                )
            else:
                raise ConversationError(f"Conversation {conversation_id} not found")
        except Exception as e:
            error_msg = f"Failed to fetch conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e
