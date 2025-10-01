"""
HuggingFace Hub Database implementation for persistent storage in Spaces.

This provides a SQLite-compatible interface using HuggingFace Hub as the backend,
solving the persistence problem in HuggingFace Spaces deployment.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
from datasets import Dataset, load_dataset
from huggingface_hub import HfApi


class HubDatabase:
    """Database implementation using HuggingFace Hub for persistence."""

    def __init__(self, repo_id: str, token: Optional[str] = None):
        """
        Initialize Hub Database connection.

        Args:
            repo_id: HuggingFace dataset repo (e.g., "sytse06/agent-workbench-db")
            token: HF token (if None, uses HF_TOKEN env var)
        """
        self.repo_id = repo_id
        self.token = token or os.getenv("HF_TOKEN")
        self.api = HfApi(token=self.token)
        self._ensure_repo_exists()

    def _ensure_repo_exists(self):
        """Create the dataset repository if it doesn't exist."""
        try:
            self.api.repo_info(repo_id=self.repo_id, repo_type="dataset")
            print(f"✅ Connected to existing Hub DB: {self.repo_id}")
        except Exception:
            try:
                self.api.create_repo(
                    repo_id=self.repo_id,
                    repo_type="dataset",
                    private=True,  # Keep private by default
                )
                print(f"✅ Created new Hub DB: {self.repo_id}")
            except Exception as e:
                print(f"⚠️ Failed to create Hub DB repo: {e}")

    def _get_table(self, table_name: str) -> pd.DataFrame:
        """Load a table from Hub DB as DataFrame."""
        try:
            dataset = load_dataset(
                self.repo_id, split=table_name, use_auth_token=self.token
            )
            return dataset.to_pandas()
        except Exception:
            # Return empty DataFrame with standard columns if table doesn't exist
            return pd.DataFrame(columns=["id", "created_at", "updated_at"])

    def _save_table(self, table_name: str, df: pd.DataFrame):
        """Save DataFrame to Hub DB as a table."""
        try:
            dataset = Dataset.from_pandas(df)
            dataset.push_to_hub(self.repo_id, split=table_name, token=self.token)
        except Exception as e:
            print(f"⚠️ Failed to save table {table_name}: {e}")

    # Conversation operations (compatible with existing SQLAlchemy models)

    def save_conversation(self, conversation_data: Dict[str, Any]) -> str:
        """Save conversation to Hub DB."""
        df = self._get_table("conversations")

        # Add standard fields
        conversation_id = conversation_data.get("id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        new_row = {
            "id": conversation_id,
            "created_at": conversation_data.get("created_at", now),
            "updated_at": now,
            "title": conversation_data.get("title", ""),
            "mode": conversation_data.get("mode", "workbench"),
            "data": json.dumps(conversation_data.get("data", {})),
        }

        # Update existing or append new
        if conversation_id in df["id"].values:
            df.loc[df["id"] == conversation_id] = new_row
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        self._save_table("conversations", df)
        return conversation_id

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        df = self._get_table("conversations")
        matches = df[df["id"] == conversation_id]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "id": row["id"],
            "title": row["title"],
            "mode": row["mode"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "data": json.loads(row["data"]) if row["data"] else {},
        }

    def list_conversations(
        self, mode: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """List conversations with optional filtering."""
        df = self._get_table("conversations")

        if mode:
            df = df[df["mode"] == mode]

        # Sort by updated_at descending and limit
        df = df.sort_values("updated_at", ascending=False).head(limit)

        conversations = []
        for _, row in df.iterrows():
            conversations.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "mode": row["mode"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "data": json.loads(row["data"]) if row["data"] else {},
                }
            )

        return conversations

    # Business profile operations (for SEO coach)

    def save_business_profile(self, profile_data: Dict[str, Any]) -> str:
        """Save business profile to Hub DB."""
        df = self._get_table("business_profiles")

        profile_id = profile_data.get("id", str(uuid.uuid4()))
        now = datetime.utcnow().isoformat()

        new_row = {
            "id": profile_id,
            "created_at": profile_data.get("created_at", now),
            "updated_at": now,
            "business_name": profile_data.get("business_name", ""),
            "business_type": profile_data.get("business_type", ""),
            "website_url": profile_data.get("website_url", ""),
            "location": profile_data.get("location", ""),
            "data": json.dumps(profile_data.get("data", {})),
        }

        # Update existing or append new
        if profile_id in df["id"].values:
            df.loc[df["id"] == profile_id] = new_row
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        self._save_table("business_profiles", df)
        return profile_id

    def get_business_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """Get business profile by ID."""
        df = self._get_table("business_profiles")
        matches = df[df["id"] == profile_id]

        if matches.empty:
            return None

        row = matches.iloc[0]
        return {
            "id": row["id"],
            "business_name": row["business_name"],
            "business_type": row["business_type"],
            "website_url": row["website_url"],
            "location": row["location"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "data": json.loads(row["data"]) if row["data"] else {},
        }

    # Generic key-value operations

    def set_value(self, key: str, value: Any, table: str = "key_value"):
        """Set a key-value pair."""
        df = self._get_table(table)
        now = datetime.utcnow().isoformat()

        new_row = {
            "id": key,
            "created_at": now,
            "updated_at": now,
            "value": json.dumps(value),
        }

        if key in df["id"].values:
            df.loc[df["id"] == key] = new_row
        else:
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        self._save_table(table, df)

    def get_value(self, key: str, table: str = "key_value", default: Any = None) -> Any:
        """Get a value by key."""
        df = self._get_table(table)
        matches = df[df["id"] == key]

        if matches.empty:
            return default

        value_str = matches.iloc[0]["value"]
        return json.loads(value_str) if value_str else default


# Compatibility layer for existing SQLAlchemy code
class HubSession:
    """Session-like interface for Hub DB to maintain compatibility."""

    def __init__(self, hub_db: HubDatabase):
        self.hub_db = hub_db

    def execute(self, query: str, params: Dict = None):
        """Execute a query (limited compatibility)."""
        # This is a simplified compatibility layer
        # Real implementation would need query parsing
        pass

    def commit(self):
        """Commit changes (automatic in Hub DB)."""
        pass

    def close(self):
        """Close session (no-op in Hub DB)."""
        pass


def create_hub_database(mode: str = "workbench") -> HubDatabase:
    """
    Create Hub Database instance with appropriate repo naming.

    Args:
        mode: Application mode ("workbench" or "seo_coach")

    Returns:
        Configured HubDatabase instance
    """
    # Check if repo ID is explicitly configured
    repo_id = os.getenv("HUB_DB_REPO")

    if not repo_id:
        # Fallback to mode-based repo naming
        username = "sytse06"  # Could be made configurable
        repo_id = f"{username}/agent-{mode}-db"

    return HubDatabase(repo_id=repo_id)
