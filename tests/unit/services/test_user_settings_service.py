"""Unit tests for UserSettingsService.

Tests user settings management in isolation with mocked dependencies.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from agent_workbench.services.user_settings_service import UserSettingsService


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = MagicMock()
    # Setup default return values
    db.get_user_setting.return_value = None
    db.create_user_setting.return_value = str(uuid4())
    db.update_user_setting.return_value = None
    db.get_user_settings.return_value = []
    return db


@pytest.fixture
def settings_service(mock_db):
    """Create UserSettingsService with mock database."""
    return UserSettingsService(db=mock_db)


@pytest.mark.asyncio
async def test_get_setting_exists(settings_service, mock_db):
    """Test retrieving existing setting."""
    user_id = str(uuid4())
    setting_key = "preferred_model"

    # Mock existing setting
    mock_db.get_user_setting.return_value = {
        "id": str(uuid4()),
        "user_id": user_id,
        "setting_key": setting_key,
        "setting_value": {"provider": "anthropic", "model": "claude-3-sonnet"},
        "setting_type": "active",
        "category": "agent",
    }

    # Get setting
    value = await settings_service.get_setting(user_id=user_id, setting_key=setting_key)

    # Verify retrieval
    assert value is not None
    assert value["provider"] == "anthropic"
    assert value["model"] == "claude-3-sonnet"

    # Verify database call
    mock_db.get_user_setting.assert_called_once_with(user_id, setting_key)


@pytest.mark.asyncio
async def test_get_setting_not_exists_returns_default(settings_service, mock_db):
    """Test returning default value when setting doesn't exist."""
    user_id = str(uuid4())
    setting_key = "nonexistent_key"
    default_value = {"default": True}

    # Mock no setting found
    mock_db.get_user_setting.return_value = None

    # Get setting with default
    value = await settings_service.get_setting(
        user_id=user_id, setting_key=setting_key, default=default_value
    )

    # Verify default returned
    assert value == default_value


@pytest.mark.asyncio
async def test_set_setting_create_new(settings_service, mock_db):
    """Test creating new setting."""
    user_id = str(uuid4())
    setting_key = "ui_theme"
    setting_value = {"theme": "dark", "accent_color": "blue"}

    # Mock no existing setting
    mock_db.get_user_setting.return_value = None
    new_setting_id = str(uuid4())
    mock_db.create_user_setting.return_value = new_setting_id

    # Set setting
    await settings_service.set_setting(
        user_id=user_id,
        setting_key=setting_key,
        setting_value=setting_value,
        category="ui",
        setting_type="active",
    )

    # Verify database calls
    mock_db.get_user_setting.assert_called_once_with(user_id, setting_key)
    mock_db.create_user_setting.assert_called_once()

    # Verify creation parameters
    call_kwargs = mock_db.create_user_setting.call_args[1]
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["setting_key"] == setting_key
    assert call_kwargs["setting_value"] == setting_value
    assert call_kwargs["category"] == "ui"
    assert call_kwargs["setting_type"] == "active"


@pytest.mark.asyncio
async def test_set_setting_update_existing(settings_service, mock_db):
    """Test updating existing setting."""
    user_id = str(uuid4())
    setting_key = "preferred_model"
    old_value = {"provider": "anthropic", "model": "claude-3-sonnet"}
    new_value = {"provider": "openai", "model": "gpt-4"}

    # Mock existing setting
    mock_db.get_user_setting.return_value = {
        "id": str(uuid4()),
        "user_id": user_id,
        "setting_key": setting_key,
        "setting_value": old_value,
        "setting_type": "active",
        "category": "agent",
    }

    # Update setting
    await settings_service.set_setting(
        user_id=user_id,
        setting_key=setting_key,
        setting_value=new_value,
        category="agent",
        setting_type="active",
    )

    # Verify database calls
    mock_db.get_user_setting.assert_called_once_with(user_id, setting_key)
    mock_db.update_user_setting.assert_called_once_with(
        user_id=user_id, setting_key=setting_key, setting_value=new_value
    )
    mock_db.create_user_setting.assert_not_called()


@pytest.mark.asyncio
async def test_get_settings_by_category(settings_service, mock_db):
    """Test retrieving all settings in a category."""
    user_id = str(uuid4())
    category = "agent"

    # Mock multiple settings
    mock_db.get_user_settings.return_value = [
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "setting_key": "preferred_model",
            "setting_value": {"provider": "anthropic", "model": "claude-3-sonnet"},
            "setting_type": "active",
            "category": "agent",
        },
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "setting_key": "max_tokens",
            "setting_value": {"max_tokens": 2000},
            "setting_type": "active",
            "category": "agent",
        },
        {
            "id": str(uuid4()),
            "user_id": user_id,
            "setting_key": "ui_theme",
            "setting_value": {"theme": "dark"},
            "setting_type": "active",
            "category": "ui",
        },
    ]

    # Get settings by category
    settings = await settings_service.get_settings_by_category(
        user_id=user_id, category=category
    )

    # Verify filtering
    assert len(settings) == 2
    assert "preferred_model" in settings
    assert "max_tokens" in settings
    assert "ui_theme" not in settings

    # Verify values
    assert settings["preferred_model"]["provider"] == "anthropic"
    assert settings["max_tokens"]["max_tokens"] == 2000


@pytest.mark.asyncio
async def test_get_settings_by_category_empty(settings_service, mock_db):
    """Test retrieving settings when category is empty."""
    user_id = str(uuid4())
    category = "nonexistent"

    # Mock no settings
    mock_db.get_user_settings.return_value = []

    # Get settings by category
    settings = await settings_service.get_settings_by_category(
        user_id=user_id, category=category
    )

    # Verify empty result
    assert settings == {}


@pytest.mark.asyncio
async def test_delete_setting_success(settings_service, mock_db):
    """Test deleting existing setting."""
    user_id = str(uuid4())
    setting_key = "old_setting"

    # Mock successful deletion
    mock_db.delete_user_setting.return_value = True

    # Delete setting
    result = await settings_service.delete_setting(
        user_id=user_id, setting_key=setting_key
    )

    # Verify deletion
    assert result is True
    mock_db.delete_user_setting.assert_called_once_with(user_id, setting_key)


@pytest.mark.asyncio
async def test_delete_setting_not_found(settings_service, mock_db):
    """Test deleting non-existent setting."""
    user_id = str(uuid4())
    setting_key = "nonexistent"

    # Mock setting not found
    mock_db.delete_user_setting.return_value = False

    # Delete setting
    result = await settings_service.delete_setting(
        user_id=user_id, setting_key=setting_key
    )

    # Verify not found
    assert result is False


@pytest.mark.asyncio
async def test_active_vs_passive_settings(settings_service, mock_db):
    """Test distinction between active and passive settings."""
    user_id = str(uuid4())

    # Mock no existing settings
    mock_db.get_user_setting.return_value = None

    # Create active setting (user-set preference)
    await settings_service.set_setting(
        user_id=user_id,
        setting_key="preferred_model",
        setting_value={"provider": "anthropic"},
        category="agent",
        setting_type="active",
    )

    # Verify active setting creation
    active_call = mock_db.create_user_setting.call_args_list[0]
    assert active_call[1]["setting_type"] == "active"

    # Reset mock
    mock_db.create_user_setting.reset_mock()

    # Create passive setting (system-learned behavior)
    await settings_service.set_setting(
        user_id=user_id,
        setting_key="avg_response_length",
        setting_value={"avg_tokens": 250},
        category="agent",
        setting_type="passive",
    )

    # Verify passive setting creation
    passive_call = mock_db.create_user_setting.call_args_list[0]
    assert passive_call[1]["setting_type"] == "passive"


@pytest.mark.asyncio
async def test_complex_nested_setting_values(settings_service, mock_db):
    """Test storing complex nested JSON values."""
    user_id = str(uuid4())
    setting_key = "workflow_config"

    # Complex nested value
    complex_value = {
        "workflow_mode": "workbench",
        "model_config": {
            "provider": "anthropic",
            "model": "claude-3-sonnet",
            "temperature": 0.7,
            "max_tokens": 2000,
        },
        "context_settings": {
            "max_context_length": 10000,
            "retrieval_enabled": True,
            "retrieval_params": {"top_k": 5, "score_threshold": 0.8},
        },
        "agent_settings": {
            "tools_enabled": ["web_search", "calculator"],
            "max_iterations": 10,
        },
    }

    # Mock no existing setting
    mock_db.get_user_setting.return_value = None

    # Set complex setting
    await settings_service.set_setting(
        user_id=user_id,
        setting_key=setting_key,
        setting_value=complex_value,
        category="workflow",
        setting_type="active",
    )

    # Verify complex value stored
    call_kwargs = mock_db.create_user_setting.call_args[1]
    assert call_kwargs["setting_value"] == complex_value
    assert call_kwargs["setting_value"]["model_config"]["provider"] == "anthropic"
    assert (
        call_kwargs["setting_value"]["context_settings"]["retrieval_params"]["top_k"]
        == 5
    )


@pytest.mark.asyncio
async def test_get_all_user_settings(settings_service, mock_db):
    """Test retrieving all settings for a user."""
    user_id = str(uuid4())

    # Mock various settings across categories
    mock_db.get_user_settings.return_value = [
        {
            "setting_key": "ui_theme",
            "setting_value": {"theme": "dark"},
            "category": "ui",
        },
        {
            "setting_key": "preferred_model",
            "setting_value": {"provider": "anthropic"},
            "category": "agent",
        },
        {
            "setting_key": "workflow_mode",
            "setting_value": {"mode": "workbench"},
            "category": "workflow",
        },
    ]

    # Get all settings (no category filter)
    all_settings = await settings_service.get_all_settings(user_id=user_id)

    # Verify all settings returned
    assert len(all_settings) == 3
    assert "ui_theme" in all_settings
    assert "preferred_model" in all_settings
    assert "workflow_mode" in all_settings
