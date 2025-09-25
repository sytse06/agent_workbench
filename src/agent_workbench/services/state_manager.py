"""State manager for conversation state persistence and lifecycle."""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConversationError
from ..models.conversation_state import ConversationStateDB
from ..models.database import ConversationModel, MessageModel
from ..models.schemas import ModelConfig
from ..models.standard_messages import ConversationState, StandardMessage


class StateManager:
    """Manager for conversation state persistence and lifecycle."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize state manager.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    async def load_conversation_state(self, conversation_id: UUID) -> ConversationState:
        """
        Load conversation state from database.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation state

        Raises:
            ConversationError: If state loading fails
        """
        try:
            # First check if conversation exists
            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )
            if not conversation:
                raise ConversationError(f"Conversation {conversation_id} not found")

            # Load state from database
            result = await self.db_session.execute(
                select(ConversationStateDB).where(
                    ConversationStateDB.conversation_id == conversation_id
                )
            )
            state_db = result.scalar_one_or_none()

            if state_db:
                # Convert from database format
                state = ConversationState(
                    conversation_id=conversation_id,
                    messages=state_db.state_data.get("messages", []),
                    llm_config=state_db.state_data.get("model_config"),
                    context_data=state_db.context_data or {},
                    active_contexts=state_db.active_contexts or [],
                    metadata=state_db.state_data.get("metadata", {}),
                    updated_at=state_db.updated_at or datetime.utcnow(),
                )
            else:
                # Create new state for conversation
                state = ConversationState(
                    conversation_id=conversation_id,
                    messages=[],
                    llm_config=ModelConfig(
                        provider="ollama",
                        model_name="llama3.1",
                        temperature=0.7,
                        max_tokens=1000,
                    ),
                    context_data={},
                    active_contexts=[],
                    metadata={},
                    updated_at=datetime.utcnow(),
                )

            return state

        except Exception as e:
            raise ConversationError(
                f"Failed to load conversation state: {str(e)}"
            ) from e

    async def save_conversation_state(self, state: ConversationState) -> None:
        """
        Save conversation state to database.

        Args:
            state: Conversation state to save

        Raises:
            ConversationError: If state saving fails
        """
        try:
            # Prepare state data for storage with datetime serialization
            state_data = {
                "messages": [self._serialize_message(msg) for msg in state.messages],
                "model_config": state.llm_config.model_dump(),
                "metadata": self._serialize_metadata(state.metadata),
            }

            # Check if state already exists
            result = await self.db_session.execute(
                select(ConversationStateDB).where(
                    ConversationStateDB.conversation_id == state.conversation_id
                )
            )
            state_db = result.scalar_one_or_none()

            if state_db:
                # Update existing state
                state_db.state_data = state_data
                state_db.context_data = state.context_data
                state_db.active_contexts = state.active_contexts
                state_db.updated_at = datetime.utcnow()
            else:
                # Create new state record
                state_db = ConversationStateDB(
                    conversation_id=state.conversation_id,
                    state_data=state_data,
                    context_data=state.context_data,
                    active_contexts=state.active_contexts,
                    updated_at=datetime.utcnow(),
                )
                self.db_session.add(state_db)

            await self.db_session.commit()

        except Exception as e:
            await self.db_session.rollback()
            raise ConversationError(
                f"Failed to save conversation state: {str(e)}"
            ) from e

    async def create_conversation(
        self,
        model_config: ModelConfig,
        title: Optional[str] = None,
        is_temporary: bool = False,
    ) -> UUID:
        """
        Create a new conversation with initial state.

        Args:
            model_config: Model configuration
            title: Optional conversation title
            is_temporary: Whether this is a temporary conversation

        Returns:
            Conversation ID

        Raises:
            ConversationError: If conversation creation fails
        """
        try:
            # Create conversation record
            conversation = await ConversationModel.create(self.db_session, title=title)
            conversation_id: UUID = conversation.id

            # Create initial state
            initial_state = ConversationState(
                conversation_id=conversation_id,
                messages=[],
                llm_config=model_config,
                context_data={},
                active_contexts=[],
                metadata={
                    "is_temporary": is_temporary,
                    "created_at": datetime.utcnow().isoformat(),
                },
                updated_at=datetime.utcnow(),
            )

            # Save initial state
            await self.save_conversation_state(initial_state)

            return conversation_id

        except Exception as e:
            await self.db_session.rollback()
            raise ConversationError(f"Failed to create conversation: {str(e)}") from e

    async def delete_conversation(self, conversation_id: UUID) -> bool:
        """
        Delete conversation and its state.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful

        Raises:
            ConversationError: If deletion fails
        """
        try:
            # Delete state first
            result = await self.db_session.execute(
                select(ConversationStateDB).where(
                    ConversationStateDB.conversation_id == conversation_id
                )
            )
            state_db = result.scalar_one_or_none()
            if state_db:
                await self.db_session.delete(state_db)

            # Delete conversation
            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )
            if conversation:
                await conversation.delete(self.db_session)

            await self.db_session.commit()
            return True

        except Exception as e:
            await self.db_session.rollback()
            raise ConversationError(f"Failed to delete conversation: {str(e)}") from e

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
            from sqlalchemy import func

            # Get conversations with message counts
            result = await self.db_session.execute(
                select(ConversationModel)
                .order_by(ConversationModel.updated_at.desc())
                .limit(limit)
            )
            conversations = result.scalars().all()

            summaries = []
            for conv in conversations:
                # Get message count
                msg_count_result = await self.db_session.execute(
                    select(func.count()).where(MessageModel.conversation_id == conv.id)
                )
                count = msg_count_result.scalar_one()

                summaries.append(
                    {
                        "id": conv.id,
                        "title": conv.title or f"Conversation {conv.id}",
                        "created_at": conv.created_at,
                        "last_activity": conv.updated_at,
                        "message_count": count,
                        "is_temporary": False,
                    }
                )

            return summaries

        except Exception as e:
            raise ConversationError(f"Failed to list conversations: {str(e)}") from e

    async def migrate_conversation_to_stateful(
        self, conversation_id: UUID
    ) -> ConversationState:
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
            # Get existing conversation
            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )
            if not conversation:
                raise ConversationError(f"Conversation {conversation_id} not found")

            # Get existing messages
            messages = await MessageModel.get_by_conversation(
                self.db_session,
                conversation_id,
            )

            # Convert to standard messages
            standard_messages = []
            for msg in messages:
                standard_messages.append(
                    StandardMessage(
                        role=msg.role,
                        content=msg.content,
                        timestamp=msg.created_at,
                    )
                )

            # Create state with default model config
            state = ConversationState(
                conversation_id=conversation_id,
                messages=standard_messages,
                llm_config=ModelConfig(
                    provider="ollama",
                    model_name="llama3.1",
                    temperature=0.7,
                    max_tokens=1000,
                ),
                context_data={},
                active_contexts=[],
                metadata={
                    "migrated": True,
                    "migrated_at": datetime.utcnow().isoformat(),
                },
                updated_at=datetime.utcnow(),
            )

            # Save migrated state
            await self.save_conversation_state(state)

            return state

        except Exception as e:
            raise ConversationError(f"Failed to migrate conversation: {str(e)}") from e

    async def cleanup_temporary_conversations(
        self, older_than_minutes: int = 60
    ) -> int:
        """
        Clean up temporary conversations older than specified time.

        Args:
            older_than_minutes: Age threshold in minutes

        Returns:
            Number of conversations cleaned up

        Raises:
            ConversationError: If cleanup fails
        """
        try:
            # This would implement cleanup logic
            # For now, return 0
            return 0

        except Exception as e:
            raise ConversationError(
                f"Failed to cleanup temporary conversations: {str(e)}"
            ) from e

    def _serialize_message(self, msg: StandardMessage) -> Dict:
        """
        Serialize a message with proper datetime handling.

        Args:
            msg: StandardMessage to serialize

        Returns:
            Serialized message dict
        """
        msg_dict = msg.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if isinstance(msg_dict.get("timestamp"), datetime):
            msg_dict["timestamp"] = msg_dict["timestamp"].isoformat()
        return msg_dict

    def _serialize_metadata(self, metadata: Dict) -> Dict:
        """
        Serialize metadata with proper datetime handling.

        Args:
            metadata: Metadata dict to serialize

        Returns:
            Serialized metadata dict
        """
        serialized = {}
        for key, value in metadata.items():
            if isinstance(value, datetime):
                serialized[key] = value.isoformat()
            elif isinstance(value, dict):
                # Recursively serialize nested dicts
                serialized[key] = self._serialize_metadata(value)
            else:
                serialized[key] = value
        return serialized
