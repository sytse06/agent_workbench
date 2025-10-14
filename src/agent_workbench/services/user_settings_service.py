"""Service for managing user settings (key-value store)."""

import logging
from typing import Any, Dict, List, Literal, Optional

from ..core.exceptions import ValidationError
from ..database import AdaptiveDatabase

logger = logging.getLogger(__name__)


class UserSettingsService:
    """Manage user settings with flexible key-value storage.

    Provides CRUD operations for user settings with support for:
    - Active settings (user-configured)
    - Passive settings (system-learned)
    - Categorized settings (ui, agent, workflow, etc.)

    Examples:
        >>> service = UserSettingsService()
        >>> await service.set_setting(
        ...     user_id="550e8400-...",
        ...     setting_key="preferred_model",
        ...     setting_value={"model": "gpt-4", "temperature": 0.7},
        ...     category="agent"
        ... )
        >>> value = await service.get_setting(
        ...     user_id="550e8400-...",
        ...     setting_key="preferred_model"
        ... )
    """

    def __init__(self, db: Optional[AdaptiveDatabase] = None):
        """Initialize user settings service with optional database instance.

        Args:
            db: AdaptiveDatabase instance (creates new if not provided)
        """
        self.db = db or AdaptiveDatabase()

    async def get_setting(
        self, user_id: str, setting_key: str, default: Any = None
    ) -> Any:
        """Get user setting value.

        Args:
            user_id: User UUID string
            setting_key: Setting key
            default: Default value if setting not found

        Returns:
            Setting value (dict) or default if not found

        Raises:
            ValidationError: If user_id or setting_key is invalid
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not setting_key:
                raise ValidationError("setting_key is required")

            setting = self.db.get_user_setting(user_id, setting_key)

            if not setting:
                logger.debug(
                    f"Setting '{setting_key}' not found for user {user_id}, "
                    f"returning default"
                )
                return default

            return setting["setting_value"]

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to get setting '{setting_key}': {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, field=setting_key) from e

    async def set_setting(
        self,
        user_id: str,
        setting_key: str,
        setting_value: Any,
        category: str = "general",
        setting_type: Literal["active", "passive"] = "active",
        description: Optional[str] = None,
    ) -> None:
        """Save user setting.

        Args:
            user_id: User UUID string
            setting_key: Setting key
            setting_value: Setting value (will be converted to dict if needed)
            category: Setting category (default: "general")
            setting_type: "active" (user-set) or "passive" (system-learned)
            description: Optional setting description

        Raises:
            ValidationError: If validation fails
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not setting_key:
                raise ValidationError("setting_key is required")
            if setting_type not in ("active", "passive"):
                raise ValidationError(
                    "setting_type must be 'active' or 'passive'",
                    field="setting_type"
                )

            # Ensure setting_value is a dict (protocol requirement)
            if not isinstance(setting_value, dict):
                setting_value = {"value": setting_value}

            # Check if setting exists
            existing = self.db.get_user_setting(user_id, setting_key)

            if existing:
                # Update existing setting
                success = self.db.update_user_setting(
                    user_id=user_id,
                    setting_key=setting_key,
                    setting_value=setting_value,
                )
                if not success:
                    raise ValidationError(f"Failed to update setting '{setting_key}'")

                logger.debug(f"Updated setting '{setting_key}' for user {user_id}")
            else:
                # Create new setting
                self.db.create_user_setting(
                    user_id=user_id,
                    setting_key=setting_key,
                    setting_value=setting_value,
                    setting_type=setting_type,
                    category=category,
                    description=description,
                )

                logger.info(f"Created setting '{setting_key}' for user {user_id}")

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to set setting '{setting_key}': {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, field=setting_key) from e

    async def get_settings_by_category(
        self, user_id: str, category: str
    ) -> Dict[str, Any]:
        """Get all settings in a category.

        Args:
            user_id: User UUID string
            category: Category name

        Returns:
            Dictionary mapping setting keys to values

        Raises:
            ValidationError: If user_id or category is invalid
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not category:
                raise ValidationError("category is required")

            # Get all settings for user
            all_settings = self.db.get_user_settings(user_id)

            # Filter by category
            category_settings = {}
            for setting in all_settings:
                if setting.get("category") == category:
                    category_settings[setting["setting_key"]] = setting["setting_value"]

            logger.debug(
                f"Retrieved {len(category_settings)} settings in category "
                f"'{category}' for user {user_id}"
            )
            return category_settings

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to get settings for category '{category}': {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, field="category") from e

    async def get_all_settings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all settings for a user.

        Args:
            user_id: User UUID string

        Returns:
            List of setting dictionaries

        Raises:
            ValidationError: If user_id is invalid
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")

            settings = self.db.get_user_settings(user_id)

            logger.debug(f"Retrieved {len(settings)} settings for user {user_id}")
            return settings

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to get all settings: {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e

    async def delete_setting(self, user_id: str, setting_key: str) -> bool:
        """Delete user setting.

        Args:
            user_id: User UUID string
            setting_key: Setting key to delete

        Returns:
            True if deletion succeeded, False if setting not found

        Raises:
            ValidationError: If user_id or setting_key is invalid
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not setting_key:
                raise ValidationError("setting_key is required")

            success = self.db.delete_user_setting(user_id, setting_key)

            if success:
                logger.info(f"Deleted setting '{setting_key}' for user {user_id}")
            else:
                logger.debug(f"Setting '{setting_key}' not found for user {user_id}")

            return success

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to delete setting '{setting_key}': {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, field=setting_key) from e

    async def has_setting(self, user_id: str, setting_key: str) -> bool:
        """Check if a setting exists for a user.

        Args:
            user_id: User UUID string
            setting_key: Setting key

        Returns:
            True if setting exists, False otherwise

        Raises:
            ValidationError: If user_id or setting_key is invalid
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not setting_key:
                raise ValidationError("setting_key is required")

            setting = self.db.get_user_setting(user_id, setting_key)
            return setting is not None

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to check setting existence '{setting_key}': {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg, field=setting_key) from e

    async def bulk_set_settings(
        self,
        user_id: str,
        settings: Dict[str, Any],
        category: str = "general",
        setting_type: Literal["active", "passive"] = "active",
    ) -> None:
        """Set multiple settings at once.

        Args:
            user_id: User UUID string
            settings: Dictionary mapping setting keys to values
            category: Category for all settings
            setting_type: Type for all settings ("active" or "passive")

        Raises:
            ValidationError: If validation fails
        """
        try:
            if not user_id:
                raise ValidationError("user_id is required")
            if not settings:
                raise ValidationError("settings dictionary is required")

            for key, value in settings.items():
                await self.set_setting(
                    user_id=user_id,
                    setting_key=key,
                    setting_value=value,
                    category=category,
                    setting_type=setting_type,
                )

            logger.info(f"Bulk set {len(settings)} settings for user {user_id}")

        except ValidationError:
            raise
        except Exception as e:
            error_msg = f"Failed to bulk set settings: {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e
