"""
Adaptive Database Layer - automatically chooses between SQLite and Hub DB.

This layer provides a unified interface that:
- Uses SQLite for local development (fast, full SQL support)
- Uses Hub DB for HuggingFace Spaces (persistent, managed)
- Maintains compatibility with existing SQLAlchemy code where possible
"""

import os
from typing import Optional

from .hub_database import create_hub_database


def detect_environment() -> str:
    """
    Detect the current runtime environment.

    Returns:
        "hf_spaces" if running in HuggingFace Spaces
        "local" for local development
    """
    # HuggingFace Spaces sets these environment variables
    if os.getenv("SPACE_ID") or os.getenv("SPACE_AUTHOR_NAME"):
        return "hf_spaces"

    # Check if we're explicitly configured for Hub DB
    if os.getenv("USE_HUB_DB", "").lower() in ("true", "1", "yes"):
        return "hf_spaces"

    return "local"


class AdaptiveDatabase:
    """
    Database adapter that automatically chooses the appropriate backend.

    Provides a unified interface for both SQLite and Hub DB backends,
    making the transition transparent to the application code.
    """

    def __init__(self, mode: str = "workbench"):
        """
        Initialize the adaptive database.

        Args:
            mode: Application mode ("workbench" or "seo_coach")
        """
        self.mode = mode
        self.environment = detect_environment()
        self.backend = None

        print(f"🔍 Detected environment: {self.environment}")

        if self.environment == "hf_spaces":
            self._init_hub_db()
        else:
            self._init_sqlite()

    def _init_hub_db(self):
        """Initialize HuggingFace Hub DB backend."""
        try:
            self.backend = create_hub_database(mode=self.mode)
            self.backend_type = "hub_db"
            print(f"✅ Initialized Hub DB backend for {self.mode}")
        except Exception as e:
            print(f"⚠️ Failed to initialize Hub DB: {e}")
            print("🔄 Falling back to SQLite...")
            self._init_sqlite()

    def _init_sqlite(self):
        """Initialize SQLite backend (import only when needed)."""
        try:
            from .database import get_session, init_database

            self.get_session = get_session
            self.init_database = init_database
            self.backend_type = "sqlite"
            print(f"✅ Initialized SQLite backend for {self.mode}")
        except ImportError as e:
            print(f"⚠️ Failed to initialize SQLite: {e}")
            raise RuntimeError("No available database backend")

    # Unified interface methods

    def save_conversation(self, conversation_data: dict) -> str:
        """Save conversation data."""
        if self.backend_type == "hub_db":
            return self.backend.save_conversation(conversation_data)
        else:
            # For SQLite, we'd need to implement SQLAlchemy operations
            # This is a placeholder for the existing SQLAlchemy code
            return self._sqlite_save_conversation(conversation_data)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get conversation by ID."""
        if self.backend_type == "hub_db":
            return self.backend.get_conversation(conversation_id)
        else:
            return self._sqlite_get_conversation(conversation_id)

    def list_conversations(self, mode: Optional[str] = None, limit: int = 50) -> list:
        """List conversations."""
        if self.backend_type == "hub_db":
            return self.backend.list_conversations(mode=mode, limit=limit)
        else:
            return self._sqlite_list_conversations(mode=mode, limit=limit)

    def save_business_profile(self, profile_data: dict) -> str:
        """Save business profile."""
        if self.backend_type == "hub_db":
            return self.backend.save_business_profile(profile_data)
        else:
            return self._sqlite_save_business_profile(profile_data)

    def get_business_profile(self, profile_id: str) -> Optional[dict]:
        """Get business profile by ID."""
        if self.backend_type == "hub_db":
            return self.backend.get_business_profile(profile_id)
        else:
            return self._sqlite_get_business_profile(profile_id)

    # SQLite compatibility methods (to be implemented)

    def _sqlite_save_conversation(self, conversation_data: dict) -> str:
        """Save conversation using SQLAlchemy."""
        # TODO: Implement using existing SQLAlchemy models
        # This would use the existing database.py models
        raise NotImplementedError("SQLite conversation saving not yet implemented")

    def _sqlite_get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Get conversation using SQLAlchemy."""
        # TODO: Implement using existing SQLAlchemy models
        raise NotImplementedError("SQLite conversation retrieval not yet implemented")

    def _sqlite_list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> list:
        """List conversations using SQLAlchemy."""
        # TODO: Implement using existing SQLAlchemy models
        raise NotImplementedError("SQLite conversation listing not yet implemented")

    def _sqlite_save_business_profile(self, profile_data: dict) -> str:
        """Save business profile using SQLAlchemy."""
        # TODO: Implement using existing SQLAlchemy models
        raise NotImplementedError("SQLite business profile saving not yet implemented")

    def _sqlite_get_business_profile(self, profile_id: str) -> Optional[dict]:
        """Get business profile using SQLAlchemy."""
        # TODO: Implement using existing SQLAlchemy models
        raise NotImplementedError(
            "SQLite business profile retrieval not yet implemented"
        )


# Global database instance
_adaptive_db: Optional[AdaptiveDatabase] = None


def get_adaptive_database(mode: str = "workbench") -> AdaptiveDatabase:
    """
    Get or create the global adaptive database instance.

    Args:
        mode: Application mode ("workbench" or "seo_coach")

    Returns:
        Configured AdaptiveDatabase instance
    """
    global _adaptive_db

    if _adaptive_db is None:
        _adaptive_db = AdaptiveDatabase(mode=mode)

    return _adaptive_db


def is_hub_db_environment() -> bool:
    """Check if we're running in an environment that should use Hub DB."""
    return detect_environment() == "hf_spaces"


async def init_adaptive_database(mode: str = "workbench"):
    """
    Initialize the adaptive database for the given mode.

    This should be called during application startup.
    """
    db = get_adaptive_database(mode=mode)

    if db.backend_type == "sqlite":
        # Initialize SQLite database
        await db.init_database()
        print("✅ SQLite database initialized")
    else:
        # Hub DB is initialized on first use
        print("✅ Hub DB ready for use")

    return db
