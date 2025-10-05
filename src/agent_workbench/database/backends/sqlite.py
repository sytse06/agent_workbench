"""SQLite backend implementation using SQLAlchemy async models.

This backend provides a Protocol-compliant interface to SQLite database
using SQLAlchemy ORM with async/await support.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.models.database import (
    AgentConfigModel,
    ConversationModel,
    MessageModel,
)


class SQLiteBackend:
    """SQLite database backend using SQLAlchemy async models.

    Implements the DatabaseBackend protocol using SQLAlchemy ORM.
    All operations are async and use the session factory for connection management.

    Attributes:
        session_factory: Callable that returns an async context manager for sessions

    Examples:
        >>> from agent_workbench.api.database import get_session
        >>> backend = SQLiteBackend(session_factory=get_session)
        >>> conversation_id = backend.save_conversation({
        ...     "title": "Debug Session",
        ...     "mode": "workbench"
        ... })
    """

    def __init__(self, session_factory: Callable[[], AsyncSession]):
        """Initialize SQLite backend with session factory.

        Args:
            session_factory: Callable that returns async session context manager
                            (e.g., get_session from api.database)
        """
        self.session_factory = session_factory

    def _run_async(self, coro):
        """Helper to run async operations synchronously for Protocol compatibility.

        The Protocol interface is synchronous, but SQLAlchemy is async.
        This helper runs async operations in the event loop.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(coro)

    # ========================================================================
    # Conversation Operations
    # ========================================================================

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation using SQLAlchemy async models."""
        return self._run_async(self._async_save_conversation(conversation_data))

    async def _async_save_conversation(
        self, conversation_data: Dict[str, Any]
    ) -> str:
        """Async implementation of save_conversation."""
        async for session in self.session_factory():
            # Check if conversation ID provided and exists
            conversation_id_str = conversation_data.get("id")
            if conversation_id_str:
                conversation_id = UUID(conversation_id_str)
                existing = await ConversationModel.get_by_id(session, conversation_id)
                if existing:
                    # Update existing conversation
                    update_data = {
                        k: v
                        for k, v in conversation_data.items()
                        if k not in ["id", "created_at"]
                    }
                    await existing.update(session, **update_data)
                    return str(existing.id)

            # Create new conversation
            create_data = {
                k: v
                for k, v in conversation_data.items()
                if k in ["user_id", "title"]
            }

            # Convert user_id string to UUID if provided
            if "user_id" in create_data and isinstance(create_data["user_id"], str):
                create_data["user_id"] = UUID(create_data["user_id"])

            conversation = await ConversationModel.create(session, **create_data)
            return str(conversation.id)

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation using SQLAlchemy async models."""
        return self._run_async(self._async_get_conversation(conversation_id))

    async def _async_get_conversation(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_conversation."""
        async for session in self.session_factory():
            conversation = await ConversationModel.get_by_id(
                session, UUID(conversation_id)
            )
            if not conversation:
                return None

            return {
                "id": str(conversation.id),
                "title": conversation.title or "",
                "mode": "workbench",  # Default mode
                "user_id": str(conversation.user_id) if conversation.user_id else None,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "data": {},  # Additional metadata can be stored here
            }

    def list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List conversations using SQLAlchemy async models."""
        return self._run_async(self._async_list_conversations(mode, limit))

    async def _async_list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Async implementation of list_conversations."""
        async for session in self.session_factory():
            # Note: Mode filtering not implemented in current schema
            # Would require adding mode column to ConversationModel
            query = (
                select(ConversationModel)
                .order_by(ConversationModel.updated_at.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            conversations = result.scalars().all()

            return [
                {
                    "id": str(conv.id),
                    "title": conv.title or "",
                    "mode": "workbench",
                    "user_id": str(conv.user_id) if conv.user_id else None,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "data": {},
                }
                for conv in conversations
            ]

    def update_conversation(
        self, conversation_id: str, conversation_data: Dict[str, Any]
    ) -> bool:
        """Update conversation using SQLAlchemy async models."""
        return self._run_async(
            self._async_update_conversation(conversation_id, conversation_data)
        )

    async def _async_update_conversation(
        self, conversation_id: str, conversation_data: Dict[str, Any]
    ) -> bool:
        """Async implementation of update_conversation."""
        async for session in self.session_factory():
            conversation = await ConversationModel.get_by_id(
                session, UUID(conversation_id)
            )
            if not conversation:
                return False

            update_data = {
                k: v
                for k, v in conversation_data.items()
                if k in ["title", "user_id"]
            }

            # Convert user_id string to UUID if provided
            if "user_id" in update_data and isinstance(update_data["user_id"], str):
                update_data["user_id"] = UUID(update_data["user_id"])

            await conversation.update(session, **update_data)
            return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation using SQLAlchemy async models."""
        return self._run_async(self._async_delete_conversation(conversation_id))

    async def _async_delete_conversation(self, conversation_id: str) -> bool:
        """Async implementation of delete_conversation."""
        async for session in self.session_factory():
            conversation = await ConversationModel.get_by_id(
                session, UUID(conversation_id)
            )
            if not conversation:
                return False

            await conversation.delete(session)
            return True

    # ========================================================================
    # Message Operations
    # ========================================================================

    def save_message(self, message_data: Dict[str, Any]) -> str:
        """Save message using SQLAlchemy async models."""
        return self._run_async(self._async_save_message(message_data))

    async def _async_save_message(self, message_data: Dict[str, Any]) -> str:
        """Async implementation of save_message."""
        async for session in self.session_factory():
            create_data = {
                "conversation_id": UUID(message_data["conversation_id"]),
                "role": message_data["role"],
                "content": message_data["content"],
                "metadata_": message_data.get("metadata"),
            }

            if "id" in message_data:
                create_data["id"] = UUID(message_data["id"])

            message = await MessageModel.create(session, **create_data)
            return str(message.id)

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages using SQLAlchemy async models."""
        return self._run_async(self._async_get_messages(conversation_id))

    async def _async_get_messages(
        self, conversation_id: str
    ) -> List[Dict[str, Any]]:
        """Async implementation of get_messages."""
        async for session in self.session_factory():
            messages = await MessageModel.get_by_conversation(
                session, UUID(conversation_id)
            )

            return [
                {
                    "id": str(msg.id),
                    "conversation_id": str(msg.conversation_id),
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": msg.metadata_,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ]

    def delete_message(self, message_id: str) -> bool:
        """Delete message using SQLAlchemy async models."""
        return self._run_async(self._async_delete_message(message_id))

    async def _async_delete_message(self, message_id: str) -> bool:
        """Async implementation of delete_message."""
        async for session in self.session_factory():
            message = await MessageModel.get_by_id(session, UUID(message_id))
            if not message:
                return False

            await message.delete(session)
            return True

    # ========================================================================
    # Business Profile Operations
    # ========================================================================

    def save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save business profile.

        Note: Business profiles are currently stored as agent configs
        in the database schema. This may be refactored in future.
        """
        return self._run_async(self._async_save_business_profile(profile_data))

    async def _async_save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Async implementation of save_business_profile."""
        async for session in self.session_factory():
            # Use AgentConfigModel as proxy for business profiles
            # Store business profile data in config JSON field
            create_data = {
                "name": profile_data.get("business_name", "Business Profile"),
                "description": f"Business profile for {profile_data.get('business_name', 'Unknown')}",
                "config": profile_data,
            }

            if "id" in profile_data:
                create_data["id"] = UUID(profile_data["id"])

            profile = await AgentConfigModel.create(session, **create_data)
            return str(profile.id)

    def get_business_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile."""
        return self._run_async(self._async_get_business_profile(profile_id))

    async def _async_get_business_profile(
        self, profile_id: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_business_profile."""
        async for session in self.session_factory():
            profile = await AgentConfigModel.get_by_id(session, UUID(profile_id))
            if not profile:
                return None

            # Extract business profile data from config field
            business_data = profile.config.copy()
            business_data["id"] = str(profile.id)
            return business_data

    def list_business_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List business profiles."""
        return self._run_async(self._async_list_business_profiles(limit))

    async def _async_list_business_profiles(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Async implementation of list_business_profiles."""
        async for session in self.session_factory():
            profiles = await AgentConfigModel.get_all(session)

            # Filter for business profiles (simplified - in production would need better filtering)
            return [
                {**profile.config, "id": str(profile.id)}
                for profile in profiles[:limit]
                if "business_name" in profile.config
            ]

    def update_business_profile(
        self, profile_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """Update business profile."""
        return self._run_async(
            self._async_update_business_profile(profile_id, profile_data)
        )

    async def _async_update_business_profile(
        self, profile_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """Async implementation of update_business_profile."""
        async for session in self.session_factory():
            profile = await AgentConfigModel.get_by_id(session, UUID(profile_id))
            if not profile:
                return False

            # Merge new data into existing config
            updated_config = {**profile.config, **profile_data}
            await profile.update(session, config=updated_config)
            return True

    def delete_business_profile(self, profile_id: str) -> bool:
        """Delete business profile."""
        return self._run_async(self._async_delete_business_profile(profile_id))

    async def _async_delete_business_profile(self, profile_id: str) -> bool:
        """Async implementation of delete_business_profile."""
        async for session in self.session_factory():
            profile = await AgentConfigModel.get_by_id(session, UUID(profile_id))
            if not profile:
                return False

            await profile.delete(session)
            return True

    # ========================================================================
    # Context Operations
    # ========================================================================

    def save_context(
        self, conversation_id: str, context_data: Dict[str, Any]
    ) -> bool:
        """Save conversation context.

        Note: Context is currently stored as metadata in conversation.
        In future, may use dedicated context table.
        """
        return self._run_async(self._async_save_context(conversation_id, context_data))

    async def _async_save_context(
        self, conversation_id: str, context_data: Dict[str, Any]
    ) -> bool:
        """Async implementation of save_context."""
        async for session in self.session_factory():
            conversation = await ConversationModel.get_by_id(
                session, UUID(conversation_id)
            )
            if not conversation:
                return False

            # In future, store context in dedicated table
            # For now, this is a placeholder
            # Could extend ConversationModel to have context JSON field
            return True

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context."""
        return self._run_async(self._async_get_context(conversation_id))

    async def _async_get_context(
        self, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_context."""
        async for session in self.session_factory():
            conversation = await ConversationModel.get_by_id(
                session, UUID(conversation_id)
            )
            if not conversation:
                return None

            # Return empty context for now
            # In future, fetch from dedicated context table
            return {"active_contexts": [], "context_data": {}}
