"""Database backend protocol defining the common interface.

This protocol defines the contract that all database backends must implement,
enabling clean separation between interface and implementation.
"""

from typing import Any, Dict, List, Optional, Protocol


class DatabaseBackend(Protocol):
    """Protocol defining the common interface for all database backends.

    This protocol ensures that SQLiteBackend and HubBackend provide
    identical interfaces, making them interchangeable at runtime.

    All methods use Dict[str, Any] for data exchange to remain
    implementation-agnostic and support both SQLAlchemy models
    and Hub DB DataFrames.
    """

    # ========================================================================
    # Conversation Operations
    # ========================================================================

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation data and return conversation ID.

        Args:
            conversation_data: Dictionary containing conversation fields:
                - id (optional): UUID string, auto-generated if not provided
                - title (optional): Conversation title
                - mode (optional): Application mode (workbench/seo_coach)
                - user_id (optional): User UUID string
                - data (optional): Additional metadata

        Returns:
            Conversation ID as string

        Examples:
            >>> conversation_id = backend.save_conversation({
            ...     "title": "Debug Session",
            ...     "mode": "workbench"
            ... })
        """
        ...

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID.

        Args:
            conversation_id: UUID string of the conversation

        Returns:
            Dictionary with conversation data or None if not found:
                - id: UUID string
                - title: Conversation title
                - mode: Application mode
                - created_at: ISO timestamp string
                - updated_at: ISO timestamp string
                - data: Additional metadata dict

        Examples:
            >>> conversation = backend.get_conversation("550e8400-...")
            >>> if conversation:
            ...     print(conversation["title"])
        """
        ...

    def list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List conversations with optional filtering.

        Args:
            mode: Filter by application mode (workbench/seo_coach), None for all
            limit: Maximum number of conversations to return

        Returns:
            List of conversation dictionaries sorted by updated_at descending

        Examples:
            >>> conversations = backend.list_conversations(mode="workbench", limit=10)
            >>> for conv in conversations:
            ...     print(f"{conv['title']} - {conv['updated_at']}")
        """
        ...

    def update_conversation(
        self, conversation_id: str, conversation_data: Dict[str, Any]
    ) -> bool:
        """Update conversation fields.

        Args:
            conversation_id: UUID string of conversation to update
            conversation_data: Dictionary with fields to update (partial
                updates allowed)

        Returns:
            True if update succeeded, False if conversation not found

        Examples:
            >>> success = backend.update_conversation(
            ...     "550e8400-...",
            ...     {"title": "Updated Title"}
            ... )
        """
        ...

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation and all associated messages.

        Args:
            conversation_id: UUID string of conversation to delete

        Returns:
            True if deletion succeeded, False if conversation not found

        Examples:
            >>> deleted = backend.delete_conversation("550e8400-...")
        """
        ...

    # ========================================================================
    # Message Operations
    # ========================================================================

    def save_message(self, message_data: Dict[str, Any]) -> str:
        """Save message data and return message ID.

        Args:
            message_data: Dictionary containing message fields:
                - id (optional): UUID string, auto-generated if not provided
                - conversation_id (required): Parent conversation UUID
                - role (required): Message role (user/assistant/tool/system)
                - content (required): Message content text
                - metadata (optional): Additional metadata dict

        Returns:
            Message ID as string

        Examples:
            >>> message_id = backend.save_message({
            ...     "conversation_id": "550e8400-...",
            ...     "role": "user",
            ...     "content": "How do I debug this?"
            ... })
        """
        ...

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation ordered by created_at.

        Args:
            conversation_id: UUID string of the conversation

        Returns:
            List of message dictionaries ordered chronologically:
                - id: UUID string
                - conversation_id: Parent conversation UUID
                - role: Message role
                - content: Message text
                - metadata: Additional metadata dict
                - created_at: ISO timestamp string

        Examples:
            >>> messages = backend.get_messages("550e8400-...")
            >>> for msg in messages:
            ...     print(f"{msg['role']}: {msg['content']}")
        """
        ...

    def delete_message(self, message_id: str) -> bool:
        """Delete a message.

        Args:
            message_id: UUID string of message to delete

        Returns:
            True if deletion succeeded, False if message not found

        Examples:
            >>> deleted = backend.delete_message("650e8400-...")
        """
        ...

    # ========================================================================
    # Business Profile Operations (SEO Coach Mode)
    # ========================================================================

    def save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save business profile and return profile ID.

        Args:
            profile_data: Dictionary containing business profile fields:
                - id (optional): UUID string, auto-generated if not provided
                - conversation_id (optional): Associated conversation UUID
                - business_name (required): Business name
                - website_url (required): Website URL
                - business_type (required): Type of business
                - target_market (optional): Target market (default: Nederland)
                - seo_experience_level (optional): Experience level

        Returns:
            Profile ID as string

        Examples:
            >>> profile_id = backend.save_business_profile({
            ...     "business_name": "Test Business",
            ...     "website_url": "https://example.com",
            ...     "business_type": "E-commerce"
            ... })
        """
        ...

    def get_business_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile by ID.

        Args:
            profile_id: UUID string of the business profile

        Returns:
            Dictionary with business profile data or None if not found

        Examples:
            >>> profile = backend.get_business_profile("750e8400-...")
            >>> if profile:
            ...     print(profile["business_name"])
        """
        ...

    def list_business_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List business profiles.

        Args:
            limit: Maximum number of profiles to return

        Returns:
            List of business profile dictionaries

        Examples:
            >>> profiles = backend.list_business_profiles(limit=10)
        """
        ...

    def update_business_profile(
        self, profile_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """Update business profile fields.

        Args:
            profile_id: UUID string of profile to update
            profile_data: Dictionary with fields to update

        Returns:
            True if update succeeded, False if profile not found

        Examples:
            >>> success = backend.update_business_profile(
            ...     "750e8400-...",
            ...     {"website_url": "https://newurl.com"}
            ... )
        """
        ...

    def delete_business_profile(self, profile_id: str) -> bool:
        """Delete business profile.

        Args:
            profile_id: UUID string of profile to delete

        Returns:
            True if deletion succeeded, False if profile not found

        Examples:
            >>> deleted = backend.delete_business_profile("750e8400-...")
        """
        ...

    # ========================================================================
    # Context Operations (Workflow State Management)
    # ========================================================================

    def save_context(self, conversation_id: str, context_data: Dict[str, Any]) -> bool:
        """Save conversation context/state data.

        Used to persist LangGraph workflow state between sessions.

        Args:
            conversation_id: UUID string of the conversation
            context_data: Dictionary with context/state data:
                - active_contexts: List of active context identifiers
                - context_data: Arbitrary context data dict
                - workflow_state: LangGraph state data

        Returns:
            True if save succeeded, False otherwise

        Examples:
            >>> success = backend.save_context(
            ...     "550e8400-...",
            ...     {"active_contexts": ["user_prefs"], "workflow_state": {...}}
            ... )
        """
        ...

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context/state data.

        Args:
            conversation_id: UUID string of the conversation

        Returns:
            Dictionary with context data or None if not found

        Examples:
            >>> context = backend.get_context("550e8400-...")
            >>> if context:
            ...     print(context["active_contexts"])
        """
        ...
