"""Adaptive database adapter that auto-selects backend based on environment.

This adapter provides a unified database interface that automatically chooses
between SQLite (local/Docker) and Hub DB (HuggingFace Spaces) backends based
on environment detection.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .backends.hub import HubBackend
from .backends.sqlite import SQLiteBackend
from .detection import detect_environment
from .protocol import DatabaseBackend


class AdaptiveDatabase:
    """Database adapter that automatically chooses backend based on environment.

    Provides a clean, unified interface for database operations while
    transparently delegating to either SQLite or Hub DB backend depending
    on the runtime environment.

    All if/else branching is eliminated - the adapter simply delegates
    to the appropriate backend implementation chosen at initialization.

    Attributes:
        mode: Application mode (workbench/seo_coach)
        environment: Detected environment ("local" or "hf_spaces")
        backend: Database backend implementation (SQLiteBackend or HubBackend)

    Examples:
        >>> # Auto-detects environment and creates appropriate backend
        >>> db = AdaptiveDatabase(mode="workbench")
        >>> conversation_id = db.save_conversation({
        ...     "title": "Debug Session",
        ...     "mode": "workbench"
        ... })
    """

    def __init__(self, mode: str = "workbench"):
        """Initialize adaptive database with environment-based backend selection.

        Args:
            mode: Application mode (workbench/seo_coach) for configuration
        """
        self.mode = mode
        self.environment = detect_environment()
        self.backend: DatabaseBackend = self._create_backend()

        print(f"🔍 Detected environment: {self.environment}")
        print(f"✅ Initialized {self.backend.__class__.__name__} for {self.mode}")

    def _create_backend(self) -> DatabaseBackend:
        """Create appropriate backend based on detected environment.

        Returns:
            SQLiteBackend for local/Docker environments
            HubBackend for HuggingFace Spaces environments

        Raises:
            RuntimeError: If no database backend can be initialized
        """
        if self.environment == "hf_spaces":
            try:
                return HubBackend(mode=self.mode)
            except Exception as e:
                print(f"⚠️ Failed to initialize Hub DB: {e}")
                print("🔄 Falling back to SQLite...")
                # Fallback to SQLite if Hub DB fails
                return self._create_sqlite_backend()
        else:
            return self._create_sqlite_backend()

    def _create_sqlite_backend(self) -> SQLiteBackend:
        """Create SQLite backend with session factory.

        Returns:
            Initialized SQLiteBackend

        Raises:
            RuntimeError: If SQLite backend cannot be initialized
        """
        try:
            from agent_workbench.api.database import get_session

            return SQLiteBackend(session_factory=get_session)
        except ImportError as e:
            raise RuntimeError(f"No available database backend: {e}")

    # ========================================================================
    # Conversation Operations - Simple Delegation
    # ========================================================================

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation (delegates to backend)."""
        return self.backend.save_conversation(conversation_data)

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation (delegates to backend)."""
        return self.backend.get_conversation(conversation_id)

    def list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List conversations (delegates to backend)."""
        return self.backend.list_conversations(mode=mode, limit=limit)

    def update_conversation(
        self, conversation_id: str, conversation_data: Dict[str, Any]
    ) -> bool:
        """Update conversation (delegates to backend)."""
        return self.backend.update_conversation(conversation_id, conversation_data)

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation (delegates to backend)."""
        return self.backend.delete_conversation(conversation_id)

    # ========================================================================
    # Message Operations - Simple Delegation
    # ========================================================================

    def save_message(self, message_data: Dict[str, Any]) -> str:
        """Save message (delegates to backend)."""
        return self.backend.save_message(message_data)

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages (delegates to backend)."""
        return self.backend.get_messages(conversation_id)

    def delete_message(self, message_id: str) -> bool:
        """Delete message (delegates to backend)."""
        return self.backend.delete_message(message_id)

    # ========================================================================
    # Business Profile Operations - Simple Delegation
    # ========================================================================

    def save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save business profile (delegates to backend)."""
        return self.backend.save_business_profile(profile_data)

    def get_business_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile (delegates to backend)."""
        return self.backend.get_business_profile(profile_id)

    def list_business_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List business profiles (delegates to backend)."""
        return self.backend.list_business_profiles(limit=limit)

    def update_business_profile(
        self, profile_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """Update business profile (delegates to backend)."""
        return self.backend.update_business_profile(profile_id, profile_data)

    def delete_business_profile(self, profile_id: str) -> bool:
        """Delete business profile (delegates to backend)."""
        return self.backend.delete_business_profile(profile_id)

    # ========================================================================
    # Context Operations - Simple Delegation
    # ========================================================================

    def save_context(self, conversation_id: str, context_data: Dict[str, Any]) -> bool:
        """Save conversation context (delegates to backend)."""
        return self.backend.save_context(conversation_id, context_data)

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context (delegates to backend)."""
        return self.backend.get_context(conversation_id)

    # ========================================================================
    # User Operations - Simple Delegation
    # ========================================================================

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (delegates to backend)."""
        return self.backend.get_user_by_username(username)

    def get_user_by_email(self, email: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get user by email and provider (delegates to backend)."""
        return self.backend.get_user_by_email(email, provider)

    def create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new user (delegates to backend)."""
        return self.backend.create_user(
            username=username,
            auth_provider=auth_provider,
            email=email,
            avatar_url=avatar_url,
            provider_data=provider_data,
        )

    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last_login timestamp (delegates to backend)."""
        return self.backend.update_user_last_login(user_id)

    def update_user_provider_data(
        self, user_id: str, provider_data: Dict[str, Any]
    ) -> bool:
        """Update user's provider-specific data (delegates to backend)."""
        return self.backend.update_user_provider_data(user_id, provider_data)

    # ========================================================================
    # Session Operations - Simple Delegation
    # ========================================================================

    def create_user_session(
        self,
        user_id: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
    ) -> str:
        """Create a new user session (delegates to backend)."""
        return self.backend.create_user_session(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
        )

    def get_active_user_session(
        self, user_id: str, since: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get active session for user (delegates to backend)."""
        return self.backend.get_active_user_session(user_id, since)

    def update_session_activity(self, session_id: str) -> bool:
        """Update session's last_activity timestamp (delegates to backend)."""
        return self.backend.update_session_activity(session_id)

    def increment_session_messages(self, session_id: str) -> bool:
        """Increment session's total_messages counter (delegates to backend)."""
        return self.backend.increment_session_messages(session_id)

    def increment_session_tool_calls(self, session_id: str) -> bool:
        """Increment session's total_tool_calls counter (delegates to backend)."""
        return self.backend.increment_session_tool_calls(session_id)

    def create_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log activity within a session (delegates to backend)."""
        return self.backend.create_session_activity(
            session_id=session_id,
            user_id=user_id,
            action=action,
            metadata=metadata,
        )

    def end_session(self, session_id: str) -> bool:
        """Mark session as ended (delegates to backend)."""
        return self.backend.end_session(session_id)

    # ========================================================================
    # User Settings Operations - Simple Delegation
    # ========================================================================

    def get_user_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all settings for a user (delegates to backend)."""
        return self.backend.get_user_settings(user_id)

    def get_user_setting(
        self, user_id: str, setting_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific user setting by key (delegates to backend)."""
        return self.backend.get_user_setting(user_id, setting_key)

    def create_user_setting(
        self,
        user_id: str,
        setting_key: str,
        setting_value: Dict[str, Any],
        setting_type: str = "active",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Create a new user setting (delegates to backend)."""
        return self.backend.create_user_setting(
            user_id=user_id,
            setting_key=setting_key,
            setting_value=setting_value,
            setting_type=setting_type,
            category=category,
            description=description,
        )

    def update_user_setting(
        self, user_id: str, setting_key: str, setting_value: Dict[str, Any]
    ) -> bool:
        """Update a user setting's value (delegates to backend)."""
        return self.backend.update_user_setting(user_id, setting_key, setting_value)

    def delete_user_setting(self, user_id: str, setting_key: str) -> bool:
        """Delete a user setting (delegates to backend)."""
        return self.backend.delete_user_setting(user_id, setting_key)


# ============================================================================
# Global Database Instance Management
# ============================================================================

_adaptive_db: Optional[AdaptiveDatabase] = None


def get_adaptive_database(mode: str = "workbench") -> AdaptiveDatabase:
    """Get or create the global adaptive database instance.

    Singleton pattern for database access across the application.

    Args:
        mode: Application mode (workbench/seo_coach)

    Returns:
        Configured AdaptiveDatabase instance

    Examples:
        >>> db = get_adaptive_database(mode="workbench")
        >>> conversations = db.list_conversations(limit=10)
    """
    global _adaptive_db

    if _adaptive_db is None:
        _adaptive_db = AdaptiveDatabase(mode=mode)

    return _adaptive_db


async def init_adaptive_database(mode: str = "workbench") -> AdaptiveDatabase:
    """Initialize the adaptive database for the given mode.

    This should be called during application startup to ensure
    the database backend is properly initialized.

    Args:
        mode: Application mode (workbench/seo_coach)

    Returns:
        Initialized AdaptiveDatabase instance

    Examples:
        >>> db = await init_adaptive_database(mode="workbench")
        >>> print(f"Database initialized: {db.environment}")
    """
    db = get_adaptive_database(mode=mode)

    # If using SQLite backend, ensure database is initialized
    if isinstance(db.backend, SQLiteBackend):
        try:
            from agent_workbench.api.database import init_database

            await init_database()
            print("✅ SQLite database initialized")
        except Exception as e:
            print(f"⚠️ Failed to initialize SQLite database: {e}")
    else:
        # Hub DB is initialized on first use
        print("✅ Hub DB ready for use")

    return db
