"""Unit tests for AuthService.

Tests authentication service methods in isolation with mocked dependencies.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from agent_workbench.core.exceptions import AuthenticationError
from agent_workbench.services.auth_service import AuthService


class MockGradioRequest:
    """Mock Gradio Request for testing."""

    def __init__(self, username: str, email: str = None, avatar_url: str = None):
        """Initialize mock request."""
        self.username = username
        self.email = email
        self.avatar_url = avatar_url
        self.client = {"host": "192.168.1.1"}
        self.headers = {"user-agent": "Mozilla/5.0", "referer": "https://test.com"}


@pytest.fixture
def mock_db():
    """Create mock database."""
    db = MagicMock()
    # Setup default return values
    db.get_user_by_username.return_value = None
    db.create_user.return_value = str(uuid4())
    db.update_user_last_login.return_value = None
    db.create_user_session.return_value = str(uuid4())
    db.update_session_activity.return_value = True
    db.increment_session_messages.return_value = True
    db.increment_session_tool_calls.return_value = True
    db.end_session.return_value = True
    return db


@pytest.fixture
def auth_service(mock_db):
    """Create AuthService with mock database."""
    return AuthService(db=mock_db)


@pytest.mark.asyncio
async def test_get_or_create_user_creates_new_user(auth_service, mock_db):
    """Test user creation when user doesn't exist."""
    request = MockGradioRequest(
        username="newuser", email="new@example.com", avatar_url="https://avatar.url"
    )

    # Mock database responses - use side_effect for successive calls
    new_user_id = str(uuid4())
    new_user_data = {
        "id": new_user_id,
        "username": "newuser",
        "email": "new@example.com",
        "auth_provider": "huggingface",
        "is_active": True,
    }

    # First call returns None (user doesn't exist), second call returns created user
    mock_db.get_user_by_username.side_effect = [None, new_user_data]
    mock_db.create_user.return_value = new_user_id

    # Create user
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    # Verify user creation
    assert user is not None
    assert user["username"] == "newuser"
    assert user["email"] == "new@example.com"
    assert user["auth_provider"] == "huggingface"

    # Verify database calls
    mock_db.create_user.assert_called_once()
    call_kwargs = mock_db.create_user.call_args[1]
    assert call_kwargs["username"] == "newuser"
    assert call_kwargs["auth_provider"] == "huggingface"
    assert call_kwargs["email"] == "new@example.com"
    assert "provider_data" in call_kwargs


@pytest.mark.asyncio
async def test_get_or_create_user_returns_existing_user(auth_service, mock_db):
    """Test user retrieval when user exists."""
    request = MockGradioRequest(username="existinguser")

    # Mock existing user
    existing_user = {
        "id": str(uuid4()),
        "username": "existinguser",
        "email": "existing@example.com",
        "auth_provider": "huggingface",
        "last_login": datetime.utcnow(),
        "is_active": True,
    }
    mock_db.get_user_by_username.return_value = existing_user

    # Get user
    user = await auth_service.get_or_create_user_from_request(
        request=request, provider="huggingface"
    )

    # Verify user retrieval
    assert user == existing_user

    # Verify database calls
    mock_db.get_user_by_username.assert_called()
    mock_db.update_user_last_login.assert_called_once_with(existing_user["id"])
    mock_db.create_user.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_user_missing_username(auth_service):
    """Test error handling when username is missing."""
    request = MagicMock()
    request.username = None

    with pytest.raises(AuthenticationError, match="No username found"):
        await auth_service.get_or_create_user_from_request(
            request=request, provider="huggingface"
        )


@pytest.mark.asyncio
async def test_create_session_success(auth_service, mock_db):
    """Test session creation with metadata extraction."""
    user_id = str(uuid4())
    request = MockGradioRequest(username="testuser")

    # Mock session creation
    session_id = str(uuid4())
    mock_db.create_user_session.return_value = session_id
    mock_db.get_active_user_session.return_value = {
        "id": session_id,
        "user_id": user_id,
        "session_start": datetime.utcnow(),
        "last_activity": datetime.utcnow(),
        "total_messages": 0,
        "total_tool_calls": 0,
    }

    # Create session
    session = await auth_service.create_session(user_id=user_id, request=request)

    # Verify session creation
    assert session is not None
    assert session["id"] == session_id
    assert session["user_id"] == user_id

    # Verify database calls
    mock_db.create_user_session.assert_called_once()
    call_kwargs = mock_db.create_user_session.call_args[1]
    assert call_kwargs["user_id"] == user_id
    assert call_kwargs["ip_address"] == "192.168.1.1"
    assert "user_agent" in call_kwargs

    # Verify activity logging
    mock_db.create_session_activity.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_session_found(auth_service, mock_db):
    """Test retrieval of active session within timeout."""
    user_id = str(uuid4())
    session_id = str(uuid4())

    # Mock active session
    mock_db.get_active_user_session.return_value = {
        "id": session_id,
        "user_id": user_id,
        "last_activity": datetime.utcnow(),
    }

    # Get active session
    session = await auth_service.get_active_session(user_id=user_id, max_age_minutes=30)

    # Verify session retrieval
    assert session is not None
    assert session["id"] == session_id

    # Verify database call with correct timeout
    mock_db.get_active_user_session.assert_called_once()
    call_args = mock_db.get_active_user_session.call_args[0]
    assert call_args[0] == user_id
    # Verify `since` parameter is approximately 30 minutes ago
    since_param = call_args[1]
    expected_since = datetime.utcnow() - timedelta(minutes=30)
    assert abs((since_param - expected_since).total_seconds()) < 5


@pytest.mark.asyncio
async def test_get_active_session_not_found(auth_service, mock_db):
    """Test when no active session exists."""
    user_id = str(uuid4())

    # Mock no active session
    mock_db.get_active_user_session.return_value = None

    # Get active session
    session = await auth_service.get_active_session(user_id=user_id, max_age_minutes=30)

    # Verify no session returned
    assert session is None


@pytest.mark.asyncio
async def test_update_session_activity_success(auth_service, mock_db):
    """Test session activity timestamp update."""
    session_id = str(uuid4())

    # Mock successful update
    mock_db.update_session_activity.return_value = True

    # Update activity
    await auth_service.update_session_activity(session_id)

    # Verify database call
    mock_db.update_session_activity.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_update_session_activity_not_found(auth_service, mock_db):
    """Test error when session not found."""
    session_id = str(uuid4())

    # Mock session not found
    mock_db.update_session_activity.return_value = False

    # Attempt update
    with pytest.raises(AuthenticationError, match="Session .* not found"):
        await auth_service.update_session_activity(session_id)


@pytest.mark.asyncio
async def test_log_session_activity(auth_service, mock_db):
    """Test activity logging with metadata."""
    session_id = str(uuid4())
    user_id = str(uuid4())
    action = "message_sent"
    metadata = {"content_length": 150}

    # Log activity
    await auth_service.log_session_activity(
        session_id=session_id, user_id=user_id, action=action, metadata=metadata
    )

    # Verify database call
    mock_db.create_session_activity.assert_called_once_with(
        session_id=session_id, user_id=user_id, action=action, metadata=metadata
    )


@pytest.mark.asyncio
async def test_end_session_success(auth_service, mock_db):
    """Test session termination."""
    session_id = str(uuid4())

    # Mock successful end
    mock_db.end_session.return_value = True

    # End session
    await auth_service.end_session(session_id)

    # Verify database call
    mock_db.end_session.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_end_session_not_found(auth_service, mock_db):
    """Test error when ending non-existent session."""
    session_id = str(uuid4())

    # Mock session not found
    mock_db.end_session.return_value = False

    # Attempt to end session
    with pytest.raises(AuthenticationError, match="Session .* not found"):
        await auth_service.end_session(session_id)


@pytest.mark.asyncio
async def test_increment_session_messages(auth_service, mock_db):
    """Test message counter increment."""
    session_id = str(uuid4())

    # Mock successful increment
    mock_db.increment_session_messages.return_value = True

    # Increment counter
    await auth_service.increment_session_messages(session_id)

    # Verify database call
    mock_db.increment_session_messages.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_increment_session_tool_calls(auth_service, mock_db):
    """Test tool call counter increment."""
    session_id = str(uuid4())

    # Mock successful increment
    mock_db.increment_session_tool_calls.return_value = True

    # Increment counter
    await auth_service.increment_session_tool_calls(session_id)

    # Verify database call
    mock_db.increment_session_tool_calls.assert_called_once_with(session_id)


@pytest.mark.asyncio
async def test_provider_specific_data_extraction(auth_service, mock_db):
    """Test provider-specific data extraction for different providers."""
    # Test HuggingFace
    hf_request = MockGradioRequest(
        username="hf_user", email="hf@example.com", avatar_url="https://hf.co/pic"
    )

    new_user_id = str(uuid4())
    new_user_data = {
        "id": new_user_id,
        "username": "hf_user",
        "email": "hf@example.com",
        "auth_provider": "huggingface",
        "provider_data": {"hf_username": "hf_user"},
        "is_active": True,
    }

    # First call returns None (user doesn't exist), second call returns created user
    mock_db.get_user_by_username.side_effect = [None, new_user_data]
    mock_db.create_user.return_value = new_user_id

    await auth_service.get_or_create_user_from_request(
        request=hf_request, provider="huggingface"
    )

    # Verify HuggingFace-specific data
    call_kwargs = mock_db.create_user.call_args[1]
    assert "provider_data" in call_kwargs
    assert "hf_username" in call_kwargs["provider_data"]


@pytest.mark.asyncio
async def test_session_timeout_configuration(mock_db):
    """Test session timeout can be configured."""
    # Test with custom timeout
    with patch.dict("os.environ", {"SESSION_TIMEOUT_MINUTES": "60"}):
        service = AuthService(db=mock_db)
        assert service.session_timeout_minutes == 60

    # Test with default timeout
    with patch.dict("os.environ", {}, clear=True):
        service = AuthService(db=mock_db)
        assert service.session_timeout_minutes == 30
