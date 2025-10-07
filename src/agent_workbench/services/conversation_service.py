"""Service for managing conversations and their persistence."""

from typing import Dict, List, Optional
from uuid import UUID, uuid4

from ..core.exceptions import ConversationError
from ..database import AdaptiveDatabase
from ..models.api_models import ConversationResponse, ConversationSummary
from ..models.schemas import ModelConfig


class ConversationService:
    """Enhanced service for managing conversation lifecycle.

    Provides database persistence for conversations using AdaptiveDatabase
    which automatically selects SQLite or Hub DB backend based on environment.

    Examples:
        >>> service = ConversationService()
        >>> conv_id = await service.create_conversation(title="Debug Session")
        >>> await service.add_message(str(conv_id), "user", "Help me debug this")
    """

    def __init__(self, db: Optional[AdaptiveDatabase] = None):
        """Initialize conversation service with optional database instance.

        Args:
            db: AdaptiveDatabase instance (creates new if not provided)
        """
        self.db = db or AdaptiveDatabase()

    def get_or_create(self, conversation_id: str) -> Dict:
        """Get existing conversation or create new one with database persistence.

        Args:
            conversation_id: Conversation ID

        Returns:
            Dictionary with conversation data

        Raises:
            ConversationError: If database operation fails
        """
        try:
            # Try to get existing conversation
            conversation = self.db.get_conversation(conversation_id)

            if not conversation:
                # Create new conversation
                self.db.save_conversation(
                    {
                        "id": conversation_id,
                        "title": f"Conversation {conversation_id[:8]}",
                        "mode": "workbench",
                    }
                )
                conversation = self.db.get_conversation(conversation_id)

                if not conversation:
                    raise ConversationError("Failed to create conversation")

            return conversation
        except Exception as e:
            error_msg = f"Failed to get or create conversation: {str(e)}"
            raise ConversationError(error_msg) from e

    def add_message(self, conv_id: str, role: str, content: str) -> str:
        """Add message to conversation with database persistence.

        Args:
            conv_id: Conversation ID
            role: Message role (user, assistant, system, tool)
            content: Message content

        Returns:
            Message ID as string

        Raises:
            ConversationError: If database operation fails
        """
        try:
            # Create message in database
            message_id = self.db.save_message(
                {
                    "conversation_id": conv_id,
                    "role": role,
                    "content": content,
                }
            )

            return message_id
        except Exception as e:
            error_msg = f"Failed to add message: {str(e)}"
            raise ConversationError(error_msg) from e

    def get_history(self, conversation_id: str) -> List[Dict]:
        """Get conversation history from database.

        Args:
            conversation_id: Conversation ID

        Returns:
            List of message dictionaries with role, content, created_at

        Raises:
            ConversationError: If database operation fails
        """
        try:
            # Get messages from database
            messages = self.db.get_messages(conversation_id)

            # Already in dictionary format from backend
            return messages
        except Exception as e:
            error_msg = f"Failed to get conversation history: {str(e)}"
            raise ConversationError(error_msg) from e

    def update_context(self, conv_id: str, context: Dict) -> None:
        """Update conversation context in database.

        Args:
            conv_id: Conversation ID
            context: Context data to store

        Raises:
            ConversationError: If database operation fails
        """
        try:
            # Update conversation title if provided in context
            if "title" in context:
                self.db.update_conversation(conv_id, {"title": context["title"]})

            # Save full context data
            self.db.save_context(conv_id, context)
        except Exception as e:
            error_msg = f"Failed to update conversation context: {str(e)}"
            raise ConversationError(error_msg) from e

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from database.

        Args:
            conversation_id: ID of conversation to delete (UUID string)

        Returns:
            True if successful, False if conversation not found

        Raises:
            ConversationError: If deletion fails
        """
        try:
            success = self.db.delete_conversation(conversation_id)
            return success
        except Exception as e:
            error_msg = f"Failed to delete conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e

    # Legacy methods for backward compatibility
    def create_conversation(
        self,
        title: Optional[str] = None,
        model_config: Optional[ModelConfig] = None,
        is_temporary: bool = False,
    ) -> str:
        """Create a new conversation (legacy method).

        Returns:
            Conversation ID as string
        """
        try:
            conversation_id = str(uuid4())
            self.db.save_conversation(
                {
                    "id": conversation_id,
                    "title": title or f"Conversation {conversation_id[:8]}",
                    "mode": "workbench",
                }
            )
            return conversation_id
        except Exception as e:
            error_msg = f"Failed to create conversation: {str(e)}"
            raise ConversationError(error_msg) from e

    def get_conversations(
        self, limit: int = 50, mode: Optional[str] = None
    ) -> List[ConversationSummary]:
        """Get list of conversations (legacy method).

        Args:
            limit: Maximum number of conversations to return
            mode: Optional mode filter (workbench/seo_coach)

        Returns:
            List of ConversationSummary objects
        """
        try:
            conversations = self.db.list_conversations(mode=mode, limit=limit)

            # Convert to ConversationSummary objects
            from datetime import datetime

            summaries = []
            for conv in conversations:
                summaries.append(
                    ConversationSummary(
                        id=UUID(conv["id"]),
                        title=conv.get("title", "Untitled"),
                        created_at=(
                            datetime.fromisoformat(conv["created_at"])
                            if isinstance(conv["created_at"], str)
                            else conv["created_at"]
                        ),
                        last_activity=(
                            datetime.fromisoformat(conv["updated_at"])
                            if isinstance(conv["updated_at"], str)
                            else conv["updated_at"]
                        ),
                        message_count=0,  # Would need to query separately
                        llm_config=None,
                    )
                )

            return summaries
        except Exception as e:
            error_msg = f"Failed to fetch conversations: {str(e)}"
            raise ConversationError(error_msg) from e

    def get_conversation(self, conversation_id: str) -> ConversationResponse:
        """Get conversation details (legacy method).

        Args:
            conversation_id: Conversation ID as string

        Returns:
            ConversationResponse object

        Raises:
            ConversationError: If conversation not found
        """
        try:
            conversation = self.db.get_conversation(conversation_id)

            if not conversation:
                raise ConversationError(f"Conversation {conversation_id} not found")

            from datetime import datetime

            # Get messages for this conversation
            messages = self.db.get_messages(conversation_id)

            return ConversationResponse(
                id=UUID(conversation["id"]),
                title=conversation.get("title", "Untitled"),
                created_at=(
                    datetime.fromisoformat(conversation["created_at"])
                    if isinstance(conversation["created_at"], str)
                    else conversation["created_at"]
                ),
                updated_at=(
                    datetime.fromisoformat(conversation["updated_at"])
                    if isinstance(conversation["updated_at"], str)
                    else conversation["updated_at"]
                ),
                messages=messages,
                llm_config=None,
            )
        except Exception as e:
            error_msg = f"Failed to fetch conversation {conversation_id}: {str(e)}"
            raise ConversationError(error_msg) from e
