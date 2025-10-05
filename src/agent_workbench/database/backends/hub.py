"""HuggingFace Hub backend implementation wrapping existing Hub DB.

This backend provides a Protocol-compliant interface to HuggingFace Hub database
for use in HuggingFace Spaces deployment where SQLite persistence is not available.
"""

from typing import Any, Dict, List, Optional

from agent_workbench.api.hub_database import HubDatabase


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
        print(f"⚠️ Delete conversation not yet implemented for Hub DB: {conversation_id}")
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
        print(
            f"⚠️ Message storage in Hub DB not yet fully implemented: {message_id}"
        )
        # Could store in separate messages table similar to conversations
        return message_id

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get messages from Hub DB.

        Note: Messages are currently stored within conversation data.
        This would need to be implemented in HubDatabase layer.
        """
        # TODO: Implement message retrieval from HubDatabase
        print(f"⚠️ Message retrieval from Hub DB not yet fully implemented: {conversation_id}")
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

    def save_context(
        self, conversation_id: str, context_data: Dict[str, Any]
    ) -> bool:
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
