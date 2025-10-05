"""Adaptive database adapter that auto-selects backend based on environment.

This adapter provides a unified database interface that automatically chooses
between SQLite (local/Docker) and Hub DB (HuggingFace Spaces) backends based
on environment detection.
"""

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

    def save_context(
        self, conversation_id: str, context_data: Dict[str, Any]
    ) -> bool:
        """Save conversation context (delegates to backend)."""
        return self.backend.save_context(conversation_id, context_data)

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context (delegates to backend)."""
        return self.backend.get_context(conversation_id)


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
