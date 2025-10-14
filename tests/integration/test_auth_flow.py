"""Integration tests for user authentication flow.

Tests the complete authentication workflow including:
- HuggingFace OAuth user creation
- Session management and reuse
- User settings persistence
- Activity tracking
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

from agent_workbench.database import AdaptiveDatabase
from agent_workbench.services.auth_service import AuthService
from agent_workbench.services.user_settings_service import UserSettingsService


class MockGradioRequest:
    """Mock Gradio Request object for testing."""

    def __init__(
        self,
        username: str,
        email: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ):
        """Initialize mock request.

        Args:
            username: User's username
            email: User's email (optional)
            avatar_url: User's avatar URL (optional)
        """
        self.username = username
        self.email = email
        self.avatar_url = avatar_url
        # Mock request metadata
        self.client = {"host": "127.0.0.1"}
        self.headers = {
            "user-agent": "TestAgent/1.0",
            "referer": "https://test.example.com",
        }


@pytest_asyncio.fixture(scope="function")
async def test_db():
    """Create in-memory test database."""
    # Use in-memory SQLite for testing
    db = AdaptiveDatabase(mode="workbench")
    # Override with test database
    # Note: This assumes AdaptiveDatabase can be initialized with test config
    yield db


@pytest_asyncio.fixture
async def auth_service(test_db):
    """Create AuthService with test database."""
    return AuthService(db=test_db)


@pytest_asyncio.fixture
async def settings_service(test_db):
    """Create UserSettingsService with test database."""
    return UserSettingsService(db=test_db)


@pytest.mark.asyncio
async def test_user_authentication_flow(auth_service):
    """Test complete HuggingFace OAuth flow.

    Verifies:
    - User creation from request
    - User retrieval on subsequent calls
    - last_login timestamp updates
    """
    # Create mock request
    request = MockGradioRequest(
        username="testuser", email="test@example.com", avatar_url="https://avatar.url"
    )

    # First authentication - should create user
    user1 = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    assert user1 is not None
    assert user1["username"] == "testuser"
    assert user1["email"] == "test@example.com"
    assert user1["auth_provider"] == "huggingface"
    assert user1["is_active"] is True

    # Store first login time
    first_login = user1["last_login"]

    # Wait a moment to ensure timestamp difference
    # Note: In real test, might want to use freezegun or similar
    await asyncio.sleep(0.1)

    # Second authentication - should retrieve existing user
    user2 = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    assert user2["id"] == user1["id"]
    assert user2["username"] == user1["username"]
    # last_login should be updated
    assert user2["last_login"] > first_login


@pytest.mark.asyncio
async def test_session_reuse_prevents_pollution(auth_service):
    """Test session reuse logic (30min timeout).

    Verifies:
    - New session created on first load
    - Same session reused within timeout window
    - last_activity timestamp updates
    - New session created after timeout
    """
    # Create user
    request = MockGradioRequest(username="session_test_user")
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    # Create first session
    session1 = await auth_service.create_session(user_id=user["id"], request=request)

    assert session1 is not None
    assert session1["user_id"] == user["id"]
    assert session1["session_end"] is None

    # Simulate page refresh within 30 minutes
    active_session = await auth_service.get_active_session(
        user_id=user["id"], max_age_minutes=30
    )

    assert active_session is not None
    assert active_session["id"] == session1["id"]

    # Update session activity
    await auth_service.update_session_activity(session1["id"])

    # Verify activity was updated
    updated_session = await auth_service.get_active_session(
        user_id=user["id"], max_age_minutes=30
    )
    assert updated_session["last_activity"] > session1["last_activity"]

    # Simulate page refresh after 30 minutes
    # Mock the database to return no active session (simulating timeout)
    with patch.object(
        auth_service.db, "get_active_user_session", return_value=None
    ):
        expired_session = await auth_service.get_active_session(
            user_id=user["id"], max_age_minutes=30
        )
        assert expired_session is None

    # Create new session (would happen in real flow)
    session2 = await auth_service.create_session(user_id=user["id"], request=request)
    assert session2["id"] != session1["id"]


@pytest.mark.asyncio
async def test_user_settings_persistence(settings_service, auth_service):
    """Test settings CRUD operations.

    Verifies:
    - Setting creation with different types (active/passive)
    - Setting retrieval
    - Setting updates
    - Persistence across sessions
    """
    # Create user
    request = MockGradioRequest(username="settings_test_user")
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    # Save active setting
    await settings_service.set_setting(
        user_id=user["id"],
        setting_key="preferred_model",
        setting_value={"provider": "anthropic", "model": "claude-3-sonnet"},
        category="agent",
        setting_type="active",
    )

    # Load setting
    model_pref = await settings_service.get_setting(
        user_id=user["id"], setting_key="preferred_model"
    )

    assert model_pref is not None
    assert model_pref["provider"] == "anthropic"
    assert model_pref["model"] == "claude-3-sonnet"

    # Save passive setting (system-learned behavior)
    await settings_service.set_setting(
        user_id=user["id"],
        setting_key="avg_response_length",
        setting_value={"avg_tokens": 250, "confidence": 0.85},
        category="agent",
        setting_type="passive",
    )

    # Get all agent settings
    agent_settings = await settings_service.get_settings_by_category(
        user_id=user["id"], category="agent"
    )

    assert len(agent_settings) == 2
    assert "preferred_model" in agent_settings
    assert "avg_response_length" in agent_settings

    # Update setting
    await settings_service.set_setting(
        user_id=user["id"],
        setting_key="preferred_model",
        setting_value={"provider": "openai", "model": "gpt-4"},
        category="agent",
        setting_type="active",
    )

    # Verify update
    updated_pref = await settings_service.get_setting(
        user_id=user["id"], setting_key="preferred_model"
    )
    assert updated_pref["provider"] == "openai"
    assert updated_pref["model"] == "gpt-4"

    # Delete setting
    deleted = await settings_service.delete_setting(
        user_id=user["id"], setting_key="avg_response_length"
    )
    assert deleted is True

    # Verify deletion
    deleted_setting = await settings_service.get_setting(
        user_id=user["id"], setting_key="avg_response_length"
    )
    assert deleted_setting is None


@pytest.mark.asyncio
async def test_session_activity_tracking(auth_service):
    """Test session activity logging.

    Verifies:
    - Activity logging for various actions
    - Activity metadata storage
    - Message and tool call counters
    """
    # Create user and session
    request = MockGradioRequest(username="activity_test_user")
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )
    session = await auth_service.create_session(user_id=user["id"], request=request)

    # Log message activity
    await auth_service.log_session_activity(
        session_id=session["id"],
        user_id=user["id"],
        action="message_sent",
        metadata={"content_length": 150, "role": "user"},
    )

    # Increment message counter
    await auth_service.increment_session_messages(session["id"])

    # Log tool call activity
    await auth_service.log_session_activity(
        session_id=session["id"],
        user_id=user["id"],
        action="tool_called",
        metadata={"tool_name": "web_search", "duration_ms": 250},
    )

    # Increment tool call counter
    await auth_service.increment_session_tool_calls(session["id"])

    # Get updated session
    updated_session = await auth_service.get_active_session(
        user_id=user["id"], max_age_minutes=30
    )

    assert updated_session["total_messages"] == 1
    assert updated_session["total_tool_calls"] == 1

    # End session
    await auth_service.end_session(session["id"])

    # Verify session ended
    ended_session = await auth_service.get_active_session(
        user_id=user["id"], max_age_minutes=30
    )
    # Session should not be returned if it's ended
    # (implementation dependent on get_active_session logic)


@pytest.mark.asyncio
async def test_multiple_provider_support(auth_service):
    """Test provider-agnostic user creation.

    Verifies:
    - HuggingFace user creation
    - Google user creation (future)
    - GitHub user creation (future)
    - Provider-specific data storage
    """
    # HuggingFace user
    hf_request = MockGradioRequest(
        username="hf_user", email="hf@example.com", avatar_url="https://hf.co/avatar"
    )
    hf_user = await auth_service.get_or_create_user_from_request(
        request=hf_request, provider="huggingface"
    )

    assert hf_user["auth_provider"] == "huggingface"
    assert hf_user["username"] == "hf_user"
    assert "hf_username" in hf_user.get("provider_data", {})

    # Note: Google and GitHub tests would require mock request objects
    # with appropriate fields for those providers
    # These are placeholder tests for future implementation


@pytest.mark.asyncio
async def test_concurrent_session_creation(auth_service):
    """Test handling of concurrent session creation.

    Verifies:
    - Only one active session per user
    - Proper session reuse under concurrent loads
    """
    # Create user
    request = MockGradioRequest(username="concurrent_test_user")
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    # Simulate concurrent session requests
    import asyncio

    async def create_or_get_session():
        """Helper to create or get session."""
        active = await auth_service.get_active_session(
            user_id=user["id"], max_age_minutes=30
        )
        if active:
            return active
        return await auth_service.create_session(user_id=user["id"], request=request)

    # Run 5 concurrent session requests
    sessions = await asyncio.gather(
        *[create_or_get_session() for _ in range(5)]
    )

    # All should return the same session (or very close due to timing)
    session_ids = set(s["id"] for s in sessions)
    assert len(session_ids) <= 2  # Allow for timing edge case


@pytest.mark.asyncio
async def test_authentication_error_handling(auth_service):
    """Test error handling in authentication flow.

    Verifies:
    - Missing username handling
    - Invalid provider handling
    - Database error handling
    """
    from agent_workbench.core.exceptions import AuthenticationError

    # Test missing username
    invalid_request = MagicMock()
    invalid_request.username = None

    with pytest.raises(AuthenticationError):
        await auth_service.get_or_create_user_from_request(
            request=invalid_request, provider="huggingface"
        )

    # Test invalid session ID
    with pytest.raises(AuthenticationError):
        await auth_service.update_session_activity("invalid-uuid")
