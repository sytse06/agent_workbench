"""Database backend protocol defining the common interface.

This protocol defines the contract that all database backends must implement,
enabling clean separation between interface and implementation.
"""

from datetime import datetime
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

    # ========================================================================
    # User Operations (Provider-Agnostic Authentication)
    # ========================================================================

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username (provider-agnostic).

        Args:
            username: Username string

        Returns:
            Dictionary with user data or None if not found:
                - id: UUID string
                - username: Username
                - email: Email address (optional)
                - avatar_url: Avatar URL (optional)
                - auth_provider: Provider name (huggingface, google, etc.)
                - provider_data: Provider-specific data dict
                - created_at: ISO timestamp string
                - last_login: ISO timestamp string
                - is_active: Boolean

        Examples:
            >>> user = backend.get_user_by_username("johndoe")
            >>> if user:
            ...     print(user["email"])
        """
        ...

    def get_user_by_email(self, email: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get user by email and provider.

        Args:
            email: Email address
            provider: Authentication provider name

        Returns:
            Dictionary with user data or None if not found

        Examples:
            >>> user = backend.get_user_by_email("john@example.com", "google")
        """
        ...

    def create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new user.

        Args:
            username: Username
            auth_provider: Provider name (huggingface, google, etc.)
            email: Email address (optional)
            avatar_url: Avatar URL (optional)
            provider_data: Provider-specific data (optional)

        Returns:
            User ID as string

        Examples:
            >>> user_id = backend.create_user(
            ...     username="johndoe",
            ...     auth_provider="huggingface",
            ...     email="john@example.com",
            ...     provider_data={"hf_user_id": "12345"}
            ... )
        """
        ...

    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last_login timestamp.

        Args:
            user_id: UUID string of user

        Returns:
            True if update succeeded, False if user not found

        Examples:
            >>> success = backend.update_user_last_login("550e8400-...")
        """
        ...

    def update_user_provider_data(
        self, user_id: str, provider_data: Dict[str, Any]
    ) -> bool:
        """Update user's provider-specific data.

        Args:
            user_id: UUID string of user
            provider_data: Provider-specific data dict

        Returns:
            True if update succeeded, False if user not found

        Examples:
            >>> success = backend.update_user_provider_data(
            ...     "550e8400-...",
            ...     {"hf_user_id": "12345", "hf_avatar_url": "https://..."}
            ... )
        """
        ...

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
        """Create a new user session.

        Args:
            user_id: UUID string of user
            ip_address: IP address (optional)
            user_agent: User agent string (optional)
            referrer: Referrer URL (optional)

        Returns:
            Session ID as string

        Examples:
            >>> session_id = backend.create_user_session(
            ...     user_id="550e8400-...",
            ...     ip_address="127.0.0.1",
            ...     user_agent="Mozilla/5.0..."
            ... )
        """
        ...

    def get_active_user_session(
        self, user_id: str, since: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get active session for user (within timeout window).

        Args:
            user_id: UUID string of user
            since: Datetime threshold for active session

        Returns:
            Dictionary with session data or None if no active session:
                - id: Session UUID string
                - user_id: User UUID string
                - session_start: ISO timestamp string
                - session_end: ISO timestamp string (optional)
                - last_activity: ISO timestamp string
                - ip_address: IP address
                - user_agent: User agent string
                - referrer: Referrer URL
                - total_messages: Message count
                - total_tool_calls: Tool call count

        Examples:
            >>> from datetime import datetime, timedelta
            >>> since = datetime.utcnow() - timedelta(minutes=30)
            >>> session = backend.get_active_user_session("550e8400-...", since)
        """
        ...

    def update_session_activity(self, session_id: str) -> bool:
        """Update session's last_activity timestamp.

        Args:
            session_id: UUID string of session

        Returns:
            True if update succeeded, False if session not found

        Examples:
            >>> success = backend.update_session_activity("650e8400-...")
        """
        ...

    def increment_session_messages(self, session_id: str) -> bool:
        """Increment session's total_messages counter.

        Args:
            session_id: UUID string of session

        Returns:
            True if update succeeded, False if session not found

        Examples:
            >>> success = backend.increment_session_messages("650e8400-...")
        """
        ...

    def increment_session_tool_calls(self, session_id: str) -> bool:
        """Increment session's total_tool_calls counter.

        Args:
            session_id: UUID string of session

        Returns:
            True if update succeeded, False if session not found

        Examples:
            >>> success = backend.increment_session_tool_calls("650e8400-...")
        """
        ...

    def create_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log activity within a session.

        Args:
            session_id: UUID string of session
            user_id: UUID string of user
            action: Action name (e.g., "message_sent", "tool_called")
            metadata: Additional metadata (optional)

        Returns:
            Activity ID as string

        Examples:
            >>> activity_id = backend.create_session_activity(
            ...     session_id="650e8400-...",
            ...     user_id="550e8400-...",
            ...     action="message_sent",
            ...     metadata={"message_id": "750e8400-..."}
            ... )
        """
        ...

    def end_session(self, session_id: str) -> bool:
        """Mark session as ended.

        Args:
            session_id: UUID string of session

        Returns:
            True if update succeeded, False if session not found

        Examples:
            >>> success = backend.end_session("650e8400-...")
        """
        ...

    # ========================================================================
    # User Settings Operations (Key-Value Store)
    # ========================================================================

    def get_user_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all settings for a user.

        Args:
            user_id: UUID string of user

        Returns:
            List of setting dictionaries:
                - id: Setting UUID string
                - user_id: User UUID string
                - setting_key: Setting key
                - setting_value: Setting value (dict)
                - setting_type: Type (active/passive)
                - category: Category (optional)
                - description: Description (optional)
                - updated_at: ISO timestamp string

        Examples:
            >>> settings = backend.get_user_settings("550e8400-...")
            >>> for setting in settings:
            ...     print(f"{setting['setting_key']}: {setting['setting_value']}")
        """
        ...

    def get_user_setting(
        self, user_id: str, setting_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific user setting by key.

        Args:
            user_id: UUID string of user
            setting_key: Setting key

        Returns:
            Dictionary with setting data or None if not found

        Examples:
            >>> setting = backend.get_user_setting("550e8400-...", "preferred_model")
            >>> if setting:
            ...     print(setting["setting_value"])
        """
        ...

    def create_user_setting(
        self,
        user_id: str,
        setting_key: str,
        setting_value: Dict[str, Any],
        setting_type: str = "active",
        category: Optional[str] = None,
        description: Optional[str] = None,
    ) -> str:
        """Create a new user setting.

        Args:
            user_id: UUID string of user
            setting_key: Setting key
            setting_value: Setting value (dict)
            setting_type: Type (active/passive), default "active"
            category: Category (optional)
            description: Description (optional)

        Returns:
            Setting ID as string

        Examples:
            >>> setting_id = backend.create_user_setting(
            ...     user_id="550e8400-...",
            ...     setting_key="preferred_model",
            ...     setting_value={"model": "gpt-4", "temperature": 0.7},
            ...     setting_type="active",
            ...     category="agent"
            ... )
        """
        ...

    def update_user_setting(
        self, user_id: str, setting_key: str, setting_value: Dict[str, Any]
    ) -> bool:
        """Update a user setting's value.

        Args:
            user_id: UUID string of user
            setting_key: Setting key
            setting_value: New setting value (dict)

        Returns:
            True if update succeeded, False if setting not found

        Examples:
            >>> success = backend.update_user_setting(
            ...     user_id="550e8400-...",
            ...     setting_key="preferred_model",
            ...     setting_value={"model": "gpt-4-turbo", "temperature": 0.8}
            ... )
        """
        ...

    def delete_user_setting(self, user_id: str, setting_key: str) -> bool:
        """Delete a user setting.

        Args:
            user_id: UUID string of user
            setting_key: Setting key

        Returns:
            True if deletion succeeded, False if setting not found

        Examples:
            >>> deleted = backend.delete_user_setting("550e8400-...", "old_setting")
        """
        ...
