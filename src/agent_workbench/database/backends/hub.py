"""HuggingFace Hub backend implementation wrapping existing Hub DB.

This backend provides a Protocol-compliant interface to HuggingFace Hub database
for use in HuggingFace Spaces deployment where SQLite persistence is not available.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class HubBackend:
    """HuggingFace Hub database backend.

    Implements the DatabaseBackend protocol by wrapping the existing
    HubDatabase implementation. Provides persistent storage in HuggingFace
    Spaces using datasets as the storage layer.

    Attributes:
        hub_db: Underlying HubDatabase instance

    Examples:
        >>> backend = HubBackend(mode="workbench")
        >>> conversation_id = backend.save_conversation({
        ...     "title": "Debug Session",
        ...     "mode": "workbench"
        ... })
    """

    def __init__(self, mode: str = "workbench"):
        """Initialize Hub backend.

        Args:
            mode: Application mode (workbench/seo_coach) for repo naming
        """
        from agent_workbench.api.hub_database import create_hub_database

        self.hub_db = create_hub_database(mode=mode)

    # ========================================================================
    # Conversation Operations
    # ========================================================================

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation to Hub DB.

        Delegates directly to HubDatabase.save_conversation which handles
        both creates and updates based on presence of ID.
        """
        return self.hub_db.save_conversation(conversation_data)

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation from Hub DB."""
        return self.hub_db.get_conversation(conversation_id)

    def list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List conversations from Hub DB with optional mode filtering."""
        return self.hub_db.list_conversations(mode=mode, limit=limit)

    def update_conversation(
        self, conversation_id: str, conversation_data: Dict[str, Any]
    ) -> bool:
        """Update conversation in Hub DB.

        Hub DB's save_conversation handles updates when ID is present,
        so we fetch existing data, merge updates, and save.
        """
        existing = self.hub_db.get_conversation(conversation_id)
        if not existing:
            return False

        # Merge update data into existing data
        updated_data = {**existing, **conversation_data, "id": conversation_id}
        self.hub_db.save_conversation(updated_data)
        return True

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation from Hub DB.

        Note: Hub DB doesn't have native delete support yet.
        This is a placeholder that would need implementation in Hub DB layer.
        For now, returns False to indicate operation not supported.
        """
        # TODO: Implement delete in HubDatabase layer
        # Could be done by filtering out the row and re-saving the table
        print(
            f"⚠️ Delete conversation not yet implemented for Hub DB: {conversation_id}"
        )
        return False

    # ========================================================================
    # Message Operations
    # ========================================================================

    def save_message(self, message_data: Dict[str, Any]) -> str:
        """Save message to Hub DB.

        Note: Messages are currently not separately stored in Hub DB.
        They could be stored in conversation data or a separate messages table.
        For now, this is a placeholder.
        """
        # TODO: Implement message storage in HubDatabase
        import uuid

        message_id = message_data.get("id", str(uuid.uuid4()))
        print(f"⚠️ Message storage in Hub DB not yet fully implemented: {message_id}")
        # Could store in separate messages table similar to conversations
        return message_id

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages from Hub DB.

        Note: Messages are currently stored within conversation data.
        This would need to be implemented in HubDatabase layer.
        """
        # TODO: Implement message retrieval from HubDatabase
        print(
            "⚠️ Message retrieval from Hub DB not yet fully implemented: "
            f"{conversation_id}"
        )
        return []

    def delete_message(self, message_id: str) -> bool:
        """Delete message from Hub DB.

        Note: Not yet implemented in Hub DB layer.
        """
        # TODO: Implement message deletion in HubDatabase
        print(f"⚠️ Message deletion in Hub DB not yet implemented: {message_id}")
        return False

    # ========================================================================
    # Business Profile Operations
    # ========================================================================

    def save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save business profile to Hub DB."""
        return self.hub_db.save_business_profile(profile_data)

    def get_business_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile from Hub DB."""
        return self.hub_db.get_business_profile(profile_id)

    def list_business_profiles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List business profiles from Hub DB.

        Note: List operation not yet implemented in HubDatabase.
        This would need to be added.
        """
        # TODO: Implement list_business_profiles in HubDatabase
        print("⚠️ List business profiles not yet implemented in Hub DB")
        return []

    def update_business_profile(
        self, profile_id: str, profile_data: Dict[str, Any]
    ) -> bool:
        """Update business profile in Hub DB.

        Similar to conversation updates, fetch existing and merge.
        """
        existing = self.hub_db.get_business_profile(profile_id)
        if not existing:
            return False

        # Merge update data into existing data
        updated_data = {**existing, **profile_data, "id": profile_id}
        self.hub_db.save_business_profile(updated_data)
        return True

    def delete_business_profile(self, profile_id: str) -> bool:
        """Delete business profile from Hub DB.

        Note: Delete not yet implemented in Hub DB layer.
        """
        # TODO: Implement delete in HubDatabase
        print(f"⚠️ Delete business profile not yet implemented in Hub DB: {profile_id}")
        return False

    # ========================================================================
    # Context Operations
    # ========================================================================

    def save_context(self, conversation_id: str, context_data: Dict[str, Any]) -> bool:
        """Save conversation context to Hub DB.

        Context is stored using Hub DB's key-value operations.
        """
        try:
            context_key = f"context_{conversation_id}"
            self.hub_db.set_value(context_key, context_data, table="contexts")
            return True
        except Exception as e:
            print(f"❌ Failed to save context for {conversation_id}: {e}")
            return False

    def get_context(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation context from Hub DB.

        Retrieves context using Hub DB's key-value operations.
        """
        try:
            context_key = f"context_{conversation_id}"
            context = self.hub_db.get_value(context_key, table="contexts")
            return context if context else {"active_contexts": [], "context_data": {}}
        except Exception as e:
            print(f"❌ Failed to get context for {conversation_id}: {e}")
            return None

    # ========================================================================
    # User Operations (Provider-Agnostic Authentication)
    # ========================================================================

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username using Hub DB key-value store."""
        try:
            user_key = f"user_username_{username}"
            return self.hub_db.get_value(user_key, table="users")
        except Exception as e:
            print(f"❌ Failed to get user by username {username}: {e}")
            return None

    def get_user_by_email(self, email: str, provider: str) -> Optional[Dict[str, Any]]:
        """Get user by email and provider using Hub DB key-value store."""
        try:
            user_key = f"user_email_{provider}_{email}"
            return self.hub_db.get_value(user_key, table="users")
        except Exception as e:
            print(f"❌ Failed to get user by email {email}: {e}")
            return None

    def create_user(
        self,
        username: str,
        auth_provider: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
        provider_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new user in Hub DB."""
        import uuid

        try:
            user_id = str(uuid.uuid4())
            user_data = {
                "id": user_id,
                "username": username,
                "email": email,
                "avatar_url": avatar_url,
                "auth_provider": auth_provider,
                "provider_data": provider_data or {},
                "created_at": datetime.utcnow().isoformat(),
                "last_login": datetime.utcnow().isoformat(),
                "is_active": True,
            }

            # Store by user_id (primary key)
            self.hub_db.set_value(f"user_id_{user_id}", user_data, table="users")

            # Store by username (for lookup)
            self.hub_db.set_value(f"user_username_{username}", user_data, table="users")

            # Store by email if provided (for lookup)
            if email:
                self.hub_db.set_value(
                    f"user_email_{auth_provider}_{email}", user_data, table="users"
                )

            return user_id
        except Exception as e:
            print(f"❌ Failed to create user {username}: {e}")
            raise

    def update_user_last_login(self, user_id: str) -> bool:
        """Update user's last_login timestamp."""
        try:
            user = self.hub_db.get_value(f"user_id_{user_id}", table="users")
            if not user:
                return False

            user["last_login"] = datetime.utcnow().isoformat()

            # Update all user keys
            self.hub_db.set_value(f"user_id_{user_id}", user, table="users")
            self.hub_db.set_value(
                f"user_username_{user['username']}", user, table="users"
            )
            if user.get("email"):
                self.hub_db.set_value(
                    f"user_email_{user['auth_provider']}_{user['email']}",
                    user,
                    table="users",
                )

            return True
        except Exception as e:
            print(f"❌ Failed to update user last_login {user_id}: {e}")
            return False

    def update_user_provider_data(
        self, user_id: str, provider_data: Dict[str, Any]
    ) -> bool:
        """Update user's provider-specific data."""
        try:
            user = self.hub_db.get_value(f"user_id_{user_id}", table="users")
            if not user:
                return False

            user["provider_data"] = provider_data

            # Update all user keys
            self.hub_db.set_value(f"user_id_{user_id}", user, table="users")
            self.hub_db.set_value(
                f"user_username_{user['username']}", user, table="users"
            )
            if user.get("email"):
                self.hub_db.set_value(
                    f"user_email_{user['auth_provider']}_{user['email']}",
                    user,
                    table="users",
                )

            return True
        except Exception as e:
            print(f"❌ Failed to update user provider_data {user_id}: {e}")
            return False

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
        import uuid

        try:
            session_id = str(uuid.uuid4())
            session_data = {
                "id": session_id,
                "user_id": user_id,
                "session_start": datetime.utcnow().isoformat(),
                "session_end": None,
                "last_activity": datetime.utcnow().isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "referrer": referrer,
                "total_messages": 0,
                "total_tool_calls": 0,
            }

            self.hub_db.set_value(
                f"session_{session_id}", session_data, table="sessions"
            )
            return session_id
        except Exception as e:
            print(f"❌ Failed to create session for user {user_id}: {e}")
            raise

    def get_active_user_session(
        self, user_id: str, since: datetime
    ) -> Optional[Dict[str, Any]]:
        """Get active session for user (within timeout window).

        Note: Hub DB doesn't have efficient querying, so this is a simplified
        implementation that would need to be optimized in production.
        """
        try:
            # This is a simplified implementation
            # In production, would need to maintain a user_id -> active_session mapping
            session_key = f"active_session_{user_id}"
            session_data = self.hub_db.get_value(session_key, table="sessions")

            if not session_data:
                return None

            # Check if session is still active (within timeout)
            last_activity = datetime.fromisoformat(session_data["last_activity"])
            if last_activity >= since and not session_data.get("session_end"):
                return session_data

            return None
        except Exception as e:
            print(f"❌ Failed to get active session for user {user_id}: {e}")
            return None

    def update_session_activity(self, session_id: str) -> bool:
        """Update session's last_activity timestamp."""
        try:
            session = self.hub_db.get_value(f"session_{session_id}", table="sessions")
            if not session:
                return False

            session["last_activity"] = datetime.utcnow().isoformat()
            self.hub_db.set_value(f"session_{session_id}", session, table="sessions")

            # Update active_session mapping
            self.hub_db.set_value(
                f"active_session_{session['user_id']}", session, table="sessions"
            )

            return True
        except Exception as e:
            print(f"❌ Failed to update session activity {session_id}: {e}")
            return False

    def increment_session_messages(self, session_id: str) -> bool:
        """Increment session's total_messages counter."""
        try:
            session = self.hub_db.get_value(f"session_{session_id}", table="sessions")
            if not session:
                return False

            session["total_messages"] = session.get("total_messages", 0) + 1
            self.hub_db.set_value(f"session_{session_id}", session, table="sessions")
            return True
        except Exception as e:
            print(f"❌ Failed to increment session messages {session_id}: {e}")
            return False

    def increment_session_tool_calls(self, session_id: str) -> bool:
        """Increment session's total_tool_calls counter."""
        try:
            session = self.hub_db.get_value(f"session_{session_id}", table="sessions")
            if not session:
                return False

            session["total_tool_calls"] = session.get("total_tool_calls", 0) + 1
            self.hub_db.set_value(f"session_{session_id}", session, table="sessions")
            return True
        except Exception as e:
            print(f"❌ Failed to increment session tool_calls {session_id}: {e}")
            return False

    def create_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Log activity within a session."""
        import uuid

        try:
            activity_id = str(uuid.uuid4())
            activity_data = {
                "id": activity_id,
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "metadata": metadata or {},
            }

            self.hub_db.set_value(
                f"activity_{activity_id}", activity_data, table="activities"
            )
            return activity_id
        except Exception as e:
            print(f"❌ Failed to create session activity: {e}")
            raise

    def end_session(self, session_id: str) -> bool:
        """Mark session as ended."""
        try:
            session = self.hub_db.get_value(f"session_{session_id}", table="sessions")
            if not session:
                return False

            session["session_end"] = datetime.utcnow().isoformat()
            self.hub_db.set_value(f"session_{session_id}", session, table="sessions")

            # Remove from active_session mapping
            # (Could check if it matches before removing)
            return True
        except Exception as e:
            print(f"❌ Failed to end session {session_id}: {e}")
            return False

    # ========================================================================
    # User Settings Operations (Key-Value Store)
    # ========================================================================

    def get_user_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all settings for a user.

        Note: Hub DB doesn't have efficient list operations.
        This is a simplified implementation.
        """
        try:
            settings_list_key = f"user_settings_list_{user_id}"
            settings_list = (
                self.hub_db.get_value(settings_list_key, table="settings") or []
            )

            # Retrieve each setting
            settings = []
            for setting_key in settings_list:
                setting = self.hub_db.get_value(
                    f"setting_{user_id}_{setting_key}", table="settings"
                )
                if setting:
                    settings.append(setting)

            return settings
        except Exception as e:
            print(f"❌ Failed to get user settings for {user_id}: {e}")
            return []

    def get_user_setting(
        self, user_id: str, setting_key: str
    ) -> Optional[Dict[str, Any]]:
        """Get a specific user setting by key."""
        try:
            setting = self.hub_db.get_value(
                f"setting_{user_id}_{setting_key}", table="settings"
            )
            return setting
        except Exception as e:
            print(f"❌ Failed to get user setting {setting_key}: {e}")
            return None

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
        import uuid

        try:
            setting_id = str(uuid.uuid4())
            setting_data = {
                "id": setting_id,
                "user_id": user_id,
                "setting_key": setting_key,
                "setting_value": setting_value,
                "setting_type": setting_type,
                "category": category,
                "description": description,
                "updated_at": datetime.utcnow().isoformat(),
            }

            self.hub_db.set_value(
                f"setting_{user_id}_{setting_key}", setting_data, table="settings"
            )

            # Add to user's settings list
            settings_list_key = f"user_settings_list_{user_id}"
            settings_list = (
                self.hub_db.get_value(settings_list_key, table="settings") or []
            )
            if setting_key not in settings_list:
                settings_list.append(setting_key)
                self.hub_db.set_value(
                    settings_list_key, settings_list, table="settings"
                )

            return setting_id
        except Exception as e:
            print(f"❌ Failed to create user setting {setting_key}: {e}")
            raise

    def update_user_setting(
        self, user_id: str, setting_key: str, setting_value: Dict[str, Any]
    ) -> bool:
        """Update a user setting's value."""
        try:
            setting = self.hub_db.get_value(
                f"setting_{user_id}_{setting_key}", table="settings"
            )
            if not setting:
                return False

            setting["setting_value"] = setting_value
            setting["updated_at"] = datetime.utcnow().isoformat()

            self.hub_db.set_value(
                f"setting_{user_id}_{setting_key}", setting, table="settings"
            )
            return True
        except Exception as e:
            print(f"❌ Failed to update user setting {setting_key}: {e}")
            return False

    def delete_user_setting(self, user_id: str, setting_key: str) -> bool:
        """Delete a user setting.

        Note: Hub DB doesn't have native delete. This is a placeholder.
        """
        try:
            # In a full implementation, would remove from storage
            # For now, just return True to indicate it would succeed
            print(
                f"⚠️ Delete user setting not fully implemented in Hub DB: {setting_key}"
            )

            # Remove from user's settings list
            settings_list_key = f"user_settings_list_{user_id}"
            settings_list = (
                self.hub_db.get_value(settings_list_key, table="settings") or []
            )
            if setting_key in settings_list:
                settings_list.remove(setting_key)
                self.hub_db.set_value(
                    settings_list_key, settings_list, table="settings"
                )

            return True
        except Exception as e:
            print(f"❌ Failed to delete user setting {setting_key}: {e}")
            return False
