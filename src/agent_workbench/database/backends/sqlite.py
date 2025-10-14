"""SQLite backend implementation using SQLAlchemy async models.

This backend provides a Protocol-compliant interface to SQLite database
using SQLAlchemy ORM with async/await support.
"""

import asyncio
import concurrent.futures
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.models.database import (
    AgentConfigModel,
    ConversationModel,
    MessageModel,
    SessionActivityModel,
    UserModel,
    UserSessionModel,
    UserSettingModel,
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
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)

    def _run_async(self, coro):
        """Helper to run async operations synchronously for Protocol compatibility.

        The Protocol interface is synchronous, but SQLAlchemy is async.
        This helper runs async operations in a separate thread to avoid
        "event loop already running" errors in pytest-asyncio.
        """

        def run_in_new_loop(coro_func):
            """Run coroutine in a new event loop in separate thread."""
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(coro_func)
            finally:
                new_loop.close()

        # Run in thread pool to avoid event loop conflicts
        future = self._executor.submit(run_in_new_loop, coro)
        return future.result()

    # ========================================================================
    # Conversation Operations
    # ========================================================================

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation using SQLAlchemy async models."""
        return self._run_async(self._async_save_conversation(conversation_data))

    async def _async_save_conversation(self, conversation_data: Dict[str, Any]) -> str:
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
                k: v for k, v in conversation_data.items() if k in ["user_id", "title"]
            }

            # Convert user_id string to UUID if provided
            if "user_id" in create_data and isinstance(create_data["user_id"], str):
                create_data["user_id"] = UUID(create_data["user_id"])

            conversation = await ConversationModel.create(session, **create_data)
            return str(conversation.id)

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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
                k: v for k, v in conversation_data.items() if k in ["title", "user_id"]
            }

            # Convert user_id string to UUID if provided
            if "user_id" in update_data and isinstance(update_data["user_id"], str):
                update_data["user_id"] = UUID(update_data["user_id"])

            await conversation.update(session, **update_data)
            return True

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages using SQLAlchemy async models."""
        return self._run_async(self._async_get_messages(conversation_id))

    async def _async_get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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
                "description": (
                    f"Business profile for "
                    f"{profile_data.get('business_name', 'Unknown')}"
                ),
                "config": profile_data,
            }

            if "id" in profile_data:
                create_data["id"] = UUID(profile_data["id"])

            profile = await AgentConfigModel.create(session, **create_data)
            return str(profile.id)

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

    def list_business_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List business profiles."""
        return self._run_async(self._async_list_business_profiles(limit))

    async def _async_list_business_profiles(
        self, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Async implementation of list_business_profiles."""
        async for session in self.session_factory():
            profiles = await AgentConfigModel.get_all(session)

            # Filter for business profiles (simplified - in production would
            # need better filtering)
            return [
                {**profile.config, "id": str(profile.id)}
                for profile in profiles[:limit]
                if "business_name" in profile.config
            ]

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

    def save_context(self, conversation_id: str, context_data: Dict[str, Any]) -> bool:
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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

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

        # Fallback if session factory yields no sessions
        raise RuntimeError("No database session available")

    # ========================================================================
    # User Operations (Provider-Agnostic Authentication)
    # ========================================================================

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username."""
        return self._run_async(self._async_get_user_by_username(username))

    async def _async_get_user_by_username(
        self, username: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_user_by_username."""
        async for session in self.session_factory():
            user = await UserModel.get_by_username(session, username)
            if not user:
                return None

            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "auth_provider": user.auth_provider,
                "provider_data": user.provider_data,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat(),
                "is_active": user.is_active,
            }

        raise RuntimeError("No database session available")

    def get_user_by_email(
        self, email: str, provider: str
    ) -> Optional[Dict[str, Any]]:
        """Get user by email and provider."""
        return self._run_async(self._async_get_user_by_email(email, provider))

    async def _async_get_user_by_email(
        self, email: str, provider: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_user_by_email."""
        async for session in self.session_factory():
            user = await UserModel.get_by_email(session, email, provider)
            if not user:
                return None

            return {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "avatar_url": user.avatar_url,
                "auth_provider": user.auth_provider,
                "provider_data": user.provider_data,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat(),
                "is_active": user.is_active,
            }

        raise RuntimeError("No database session available")

    def create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new user."""
        return self._run_async(
            self._async_create_user(
                username, auth_provider, email, avatar_url, provider_data
            )
        )

    async def _async_create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Async implementation of create_user."""
        async for session in self.session_factory():
            user = await UserModel.create(
                session,
                username=username,
                auth_provider=auth_provider,
                email=email,
                avatar_url=avatar_url,
                provider_data=provider_data,
            )
            return str(user.id)

        raise RuntimeError("No database session available")

    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last_login timestamp."""
        return self._run_async(self._async_update_user_last_login(user_id))

    async def _async_update_user_last_login(self, user_id: str) -> bool:
        """Async implementation of update_user_last_login."""
        async for session in self.session_factory():
            user = await UserModel.get_by_id(session, UUID(user_id))
            if not user:
                return False

            await user.update(session, last_login=datetime.utcnow())
            return True

        raise RuntimeError("No database session available")

    def update_user_provider_data(
        self, user_id: str, provider_data: Dict[str, Any]
    ) -> bool:
        """Update user's provider-specific data."""
        return self._run_async(
            self._async_update_user_provider_data(user_id, provider_data)
        )

    async def _async_update_user_provider_data(
        self, user_id: str, provider_data: Dict[str, Any]
    ) -> bool:
        """Async implementation of update_user_provider_data."""
        async for session in self.session_factory():
            user = await UserModel.get_by_id(session, UUID(user_id))
            if not user:
                return False

            await user.update(session, provider_data=provider_data)
            return True

        raise RuntimeError("No database session available")

    # ========================================================================
    # Session Operations (User Session Tracking)
    # ========================================================================

    def create_user_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> str:
        """Create a new user session."""
        return self._run_async(
            self._async_create_user_session(user_id, ip_address, user_agent, referrer)
        )

    async def _async_create_user_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> str:
        """Async implementation of create_user_session."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.create(
                session,
                user_id=UUID(user_id),
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
            )
            return str(user_session.id)

        raise RuntimeError("No database session available")

    def get_active_user_session(
        self, user_id: str, since: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get active session for user (within timeout window)."""
        return self._run_async(self._async_get_active_user_session(user_id, since))

    async def _async_get_active_user_session(
        self, user_id: str, since: datetime
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_active_user_session."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.get_active_by_user(
                session, UUID(user_id), since
            )
            if not user_session:
                return None

            return {
                "id": str(user_session.id),
                "user_id": str(user_session.user_id),
                "session_start": user_session.session_start.isoformat(),
                "session_end": (
                    user_session.session_end.isoformat()
                    if user_session.session_end
                    else None
                ),
                "last_activity": user_session.last_activity.isoformat(),
                "ip_address": user_session.ip_address,
                "user_agent": user_session.user_agent,
                "referrer": user_session.referrer,
                "total_messages": user_session.total_messages,
                "total_tool_calls": user_session.total_tool_calls,
            }

        raise RuntimeError("No database session available")

    def update_session_activity(self, session_id: str) -> bool:
        """Update session's last_activity timestamp."""
        return self._run_async(self._async_update_session_activity(session_id))

    async def _async_update_session_activity(self, session_id: str) -> bool:
        """Async implementation of update_session_activity."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.get_by_id(session, UUID(session_id))
            if not user_session:
                return False

            await user_session.update(session, last_activity=datetime.utcnow())
            return True

        raise RuntimeError("No database session available")

    def increment_session_messages(self, session_id: str) -> bool:
        """Increment session's total_messages counter."""
        return self._run_async(self._async_increment_session_messages(session_id))

    async def _async_increment_session_messages(self, session_id: str) -> bool:
        """Async implementation of increment_session_messages."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.get_by_id(session, UUID(session_id))
            if not user_session:
                return False

            await user_session.update(
                session, total_messages=user_session.total_messages + 1
            )
            return True

        raise RuntimeError("No database session available")

    def increment_session_tool_calls(self, session_id: str) -> bool:
        """Increment session's total_tool_calls counter."""
        return self._run_async(self._async_increment_session_tool_calls(session_id))

    async def _async_increment_session_tool_calls(self, session_id: str) -> bool:
        """Async implementation of increment_session_tool_calls."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.get_by_id(session, UUID(session_id))
            if not user_session:
                return False

            await user_session.update(
                session, total_tool_calls=user_session.total_tool_calls + 1
            )
            return True

        raise RuntimeError("No database session available")

    def create_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log activity within a session."""
        return self._run_async(
            self._async_create_session_activity(session_id, user_id, action, metadata)
        )

    async def _async_create_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Async implementation of create_session_activity."""
        async for session in self.session_factory():
            activity = await SessionActivityModel.create(
                session,
                session_id=UUID(session_id),
                user_id=UUID(user_id),
                action=action,
                activity_metadata=metadata,
            )
            return str(activity.id)

        raise RuntimeError("No database session available")

    def end_session(self, session_id: str) -> bool:
        """Mark session as ended."""
        return self._run_async(self._async_end_session(session_id))

    async def _async_end_session(self, session_id: str) -> bool:
        """Async implementation of end_session."""
        async for session in self.session_factory():
            user_session = await UserSessionModel.get_by_id(session, UUID(session_id))
            if not user_session:
                return False

            await user_session.update(session, session_end=datetime.utcnow())
            return True

        raise RuntimeError("No database session available")

    # ========================================================================
    # User Settings Operations (Key-Value Store)
    # ========================================================================

    def get_user_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all settings for a user."""
        return self._run_async(self._async_get_user_settings(user_id))

    async def _async_get_user_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Async implementation of get_user_settings."""
        async for session in self.session_factory():
            settings = await UserSettingModel.get_by_user(session, UUID(user_id))

            return [
                {
                    "id": str(setting.id),
                    "user_id": str(setting.user_id),
                    "setting_key": setting.setting_key,
                    "setting_value": setting.setting_value,
                    "setting_type": setting.setting_type,
                    "category": setting.category,
                    "description": setting.description,
                    "updated_at": setting.updated_at.isoformat(),
                }
                for setting in settings
            ]

        raise RuntimeError("No database session available")

    def get_user_setting(
        self, user_id: str, setting_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific user setting by key."""
        return self._run_async(self._async_get_user_setting(user_id, setting_key))

    async def _async_get_user_setting(
        self, user_id: str, setting_key: str
    ) -> Optional[Dict[str, Any]]:
        """Async implementation of get_user_setting."""
        async for session in self.session_factory():
            setting = await UserSettingModel.get_by_user_and_key(
                session, UUID(user_id), setting_key
            )
            if not setting:
                return None

            return {
                "id": str(setting.id),
                "user_id": str(setting.user_id),
                "setting_key": setting.setting_key,
                "setting_value": setting.setting_value,
                "setting_type": setting.setting_type,
                "category": setting.category,
                "description": setting.description,
                "updated_at": setting.updated_at.isoformat(),
            }

        raise RuntimeError("No database session available")

    def create_user_setting(
        self,
        user_id: str,
        setting_key: str,
        setting_value: Dict[str, Any],
        setting_type: str = "active",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Create a new user setting."""
        return self._run_async(
            self._async_create_user_setting(
                user_id, setting_key, setting_value, setting_type, category, description
            )
        )

    async def _async_create_user_setting(
        self,
        user_id: str,
        setting_key: str,
        setting_value: Dict[str, Any],
        setting_type: str = "active",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Async implementation of create_user_setting."""
        async for session in self.session_factory():
            setting = await UserSettingModel.create(
                session,
                user_id=UUID(user_id),
                setting_key=setting_key,
                setting_value=setting_value,
                setting_type=setting_type,
                category=category,
                description=description,
            )
            return str(setting.id)

        raise RuntimeError("No database session available")

    def update_user_setting(
        self, user_id: str, setting_key: str, setting_value: Dict[str, Any]
    ) -> bool:
        """Update a user setting's value."""
        return self._run_async(
            self._async_update_user_setting(user_id, setting_key, setting_value)
        )

    async def _async_update_user_setting(
        self, user_id: str, setting_key: str, setting_value: Dict[str, Any]
    ) -> bool:
        """Async implementation of update_user_setting."""
        async for session in self.session_factory():
            setting = await UserSettingModel.get_by_user_and_key(
                session, UUID(user_id), setting_key
            )
            if not setting:
                return False

            await setting.update(session, setting_value=setting_value)
            return True

        raise RuntimeError("No database session available")

    def delete_user_setting(self, user_id: str, setting_key: str) -> bool:
        """Delete a user setting."""
        return self._run_async(self._async_delete_user_setting(user_id, setting_key))

    async def _async_delete_user_setting(
        self, user_id: str, setting_key: str
    ) -> bool:
        """Async implementation of delete_user_setting."""
        async for session in self.session_factory():
            setting = await UserSettingModel.get_by_user_and_key(
                session, UUID(user_id), setting_key
            )
            if not setting:
                return False

            await setting.delete(session)
            return True

        raise RuntimeError("No database session available")
