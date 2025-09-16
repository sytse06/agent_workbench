"""Temporary conversation lifecycle management."""

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.exceptions import ConversationError
from ..models.conversation_state import ConversationStateDB
from ..models.database import ConversationModel


class TemporaryManager:
    """Manager for temporary conversation lifecycle."""

    def __init__(self, db_session: AsyncSession):
        """
        Initialize temporary manager.

        Args:
            db_session: Database session
        """
        self.db_session = db_session

    async def cleanup_expired_temporary_conversations(
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
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(minutes=older_than_minutes)

            # Find temporary conversations older than cutoff
            result = await self.db_session.execute(
                select(ConversationStateDB)
                .join(ConversationModel)
                .where(
                    ConversationStateDB.context_data.contains({"is_temporary": True}),
                    ConversationModel.updated_at < cutoff_time,
                )
            )
            expired_states = result.scalars().all()

            cleanup_count: int = 0
            for state_db in expired_states:
                try:
                    # Delete conversation and its state
                    conversation = await ConversationModel.get_by_id(
                        self.db_session, state_db.conversation_id
                    )
                    if conversation:
                        await conversation.delete(self.db_session)
                        cleanup_count += 1
                except Exception:
                    # Continue with other cleanups even if one fails
                    continue

            await self.db_session.commit()
            return cleanup_count

        except Exception as e:
            await self.db_session.rollback()
            raise ConversationError(
                f"Failed to cleanup temporary conversations: {str(e)}"
            ) from e

    async def is_temporary_conversation(self, conversation_id: UUID) -> bool:
        """
        Check if a conversation is temporary.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if conversation is temporary
        """
        try:
            result = await self.db_session.execute(
                select(ConversationStateDB).where(
                    ConversationStateDB.conversation_id == conversation_id
                )
            )
            state_db = result.scalar_one_or_none()

            if state_db and state_db.context_data:
                is_temp = state_db.context_data.get("is_temporary", False)
                return bool(is_temp)

            return False

        except Exception:
            # If we can't determine, assume it's not temporary
            return False

    async def extend_temporary_conversation_lifetime(
        self, conversation_id: UUID
    ) -> bool:
        """
        Extend the lifetime of a temporary conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if successful
        """
        try:
            conversation = await ConversationModel.get_by_id(
                self.db_session, conversation_id
            )
            if conversation:
                _ = await conversation.update(self.db_session)
                await self.db_session.commit()
                return True

            return False

        except Exception:
            await self.db_session.rollback()
            return False
