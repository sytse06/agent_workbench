"""Service for managing conversations and their persistence."""

from typing import List, Optional
from uuid import UUID, uuid4

from ..core.exceptions import ConversationError
from ..models.schemas import ConversationResponse, ConversationSummary
from .chat_models import ModelConfig


class ConversationService:
    """Service for managing conversation lifecycle and persistence."""

    async def create_conversation(
        self,
        title: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        is_temporary: bool = False,
    ) -> UUID:
        """
        Create a new conversation.

        Args:
            title: Optional conversation title
            model_config: Optional model configuration
            is_temporary: Whether this is a temporary conversation

        Returns:
            Conversation ID

        Raises:
            ConversationError: If conversation creation fails
        """
        try:
            # This would typically interact with database
            # For now, generate a real UUID
            conversation_id = uuid4()
            return conversation_id
        except Exception as e:
            error_msg = f"Failed to create conversation: {str(e)}"
            raise ConversationError(error_msg) from e

    async def get_conversations(self, limit: int = 50) -> List[ConversationSummary]:
        """
        Get list of conversations.

        Args:
            limit: Maximum number of conversations to return

        Returns:
            List of conversation summaries

        Raises:
            ConversationError: If fetching conversations fails
        """
        try:
            # This would typically fetch from database
            # For now, return empty list
            return []
        except Exception as e:
            error_msg = f"Failed to fetch conversations: {str(e)}"
            raise ConversationError(error_msg) from e

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if successful

        Raises:
            ConversationError: If deletion fails
        """
        try:
            # This would typically delete from database
            # For now, return True
            return True
        except Exception as e:
            error_msg = f"Failed to delete conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e

    async def get_conversation(self, conversation_id: UUID) -> ConversationResponse:
        """
        Get conversation details.

        Args:
            conversation_id: ID of conversation to retrieve

        Returns:
            Conversation response

        Raises:
            ConversationError: If fetching conversation fails
        """
        try:
            # This would typically fetch from database
            # For now, return mock response with proper data types
            from datetime import datetime

            return ConversationResponse(
                id=conversation_id,
                title="Mock Conversation",
                created_at=datetime.now(),
                updated_at=datetime.now(),
                messages=[],
                llm_config=None,
            )
        except Exception as e:
            error_msg = f"Failed to fetch conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e
