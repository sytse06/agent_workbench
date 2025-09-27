"""Unit tests for message API routes."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.routes.messages import router
from agent_workbench.models.schemas import MessageResponse


@pytest.fixture
def app():
    """Create a FastAPI app with the message router."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return AsyncMock(spec=AsyncSession)


def test_create_message_success(client, mocker):
    """Test successful message creation."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method
    mock_conversation = MagicMock()
    mock_conversation.id = UUID(conversation_id)

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id",
        return_value=mock_conversation,
    )

    # Mock the MessageModel.create method
    mock_message = MagicMock()
    mock_message.id = uuid4()
    mock_message.conversation_id = UUID(conversation_id)
    mock_message.role = "user"
    mock_message.content = "Test message content"
    mock_message.metadata_ = {"key": "value"}
    mock_message.created_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.MessageModel.create", return_value=mock_message
    )

    # Mock the MessageResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.MessageResponse.model_validate",
        return_value=MessageResponse(
            id=mock_message.id,
            conversation_id=mock_message.conversation_id,
            role=mock_message.role,
            content=mock_message.content,
            metadata=mock_message.metadata_,
            created_at=mock_message.created_at,
        ),
    )

    response = client.post(
        "/api/v1/messages/",
        json={
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Test message content",
            "metadata": {"key": "value"},
        },
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["content"] == "Test message content"


def test_create_message_conversation_not_found(client, mocker):
    """Test message creation with conversation not found."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id", return_value=None
    )

    response = client.post(
        "/api/v1/messages/",
        json={
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Test message content",
        },
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_get_message_success(client, mocker):
    """Test successful message retrieval."""
    message_id = str(uuid4())
    conversation_id = str(uuid4())

    # Mock the MessageModel.get_by_id method
    mock_message = MagicMock()
    mock_message.id = UUID(message_id)
    mock_message.conversation_id = UUID(conversation_id)
    mock_message.role = "user"
    mock_message.content = "Test message content"
    mock_message.metadata_ = {"key": "value"}
    mock_message.created_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id",
        return_value=mock_message,
    )

    # Mock the MessageResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.MessageResponse.model_validate",
        return_value=MessageResponse(
            id=mock_message.id,
            conversation_id=mock_message.conversation_id,
            role=mock_message.role,
            content=mock_message.content,
            metadata=mock_message.metadata_,
            created_at=mock_message.created_at,
        ),
    )

    response = client.get(f"/api/v1/messages/{message_id}")

    assert response.status_code == 200
    assert response.json()["id"] == message_id


def test_get_message_not_found(client, mocker):
    """Test message not found error."""
    message_id = str(uuid4())

    # Mock the MessageModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id", return_value=None
    )

    response = client.get(f"/api/v1/messages/{message_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_list_messages_success(client, mocker):
    """Test successful messages listing."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method
    mock_conversation = MagicMock()
    mock_conversation.id = UUID(conversation_id)

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id",
        return_value=mock_conversation,
    )

    # Mock the MessageModel.get_by_conversation method
    mock_message1 = MagicMock()
    mock_message1.id = uuid4()
    mock_message1.conversation_id = UUID(conversation_id)
    mock_message1.role = "user"
    mock_message1.content = "First message"
    mock_message1.created_at = "2025-01-01T00:00:00"

    mock_message2 = MagicMock()
    mock_message2.id = uuid4()
    mock_message2.conversation_id = UUID(conversation_id)
    mock_message2.role = "assistant"
    mock_message2.content = "Second message"
    mock_message2.created_at = "2025-01-01T00:01:00"

    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_conversation",
        return_value=[mock_message1, mock_message2],
    )

    # Mock the MessageResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.MessageResponse.model_validate",
        side_effect=[
            MessageResponse(
                id=mock_message1.id,
                conversation_id=mock_message1.conversation_id,
                role=mock_message1.role,
                content=mock_message1.content,
                created_at=mock_message1.created_at,
            ),
            MessageResponse(
                id=mock_message2.id,
                conversation_id=mock_message2.conversation_id,
                role=mock_message2.role,
                content=mock_message2.content,
                created_at=mock_message2.created_at,
            ),
        ],
    )

    response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["content"] == "First message"
    assert response.json()[1]["content"] == "Second message"


def test_list_messages_conversation_not_found(client, mocker):
    """Test messages listing with conversation not found."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id", return_value=None
    )

    response = client.get(f"/api/v1/messages/?conversation_id={conversation_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_update_message_success(client, mocker):
    """Test successful message update."""
    message_id = str(uuid4())
    conversation_id = str(uuid4())

    # Mock the MessageModel.get_by_id method
    mock_message = MagicMock()
    mock_message.id = UUID(message_id)
    mock_message.conversation_id = UUID(conversation_id)
    mock_message.role = "user"
    mock_message.content = "Original content"
    mock_message.created_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id",
        return_value=mock_message,
    )

    # Mock the message.update method
    updated_message = MagicMock()
    updated_message.id = mock_message.id
    updated_message.conversation_id = mock_message.conversation_id
    updated_message.role = "user"
    updated_message.content = "Updated content"
    updated_message.created_at = mock_message.created_at

    # Make the update method awaitable
    mock_update = mocker.AsyncMock(return_value=updated_message)
    mock_message.update = mock_update

    mocker.patch.object(mock_message, "update", mock_update)

    # Mock the MessageResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.MessageResponse.model_validate",
        return_value=MessageResponse(
            id=updated_message.id,
            conversation_id=updated_message.conversation_id,
            role=updated_message.role,
            content=updated_message.content,
            created_at=updated_message.created_at,
        ),
    )

    response = client.put(
        f"/api/v1/messages/{message_id}", json={"content": "Updated content"}
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated content"


def test_update_message_not_found(client, mocker):
    """Test message update with not found error."""
    message_id = str(uuid4())

    # Mock the MessageModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id", return_value=None
    )

    response = client.put(
        f"/api/v1/messages/{message_id}", json={"content": "Updated content"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_delete_message_success(client, mocker):
    """Test successful message deletion."""
    message_id = str(uuid4())

    # Mock the MessageModel.get_by_id method
    mock_message = MagicMock()
    mock_message.id = UUID(message_id)

    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id",
        return_value=mock_message,
    )

    # Mock the message.delete method to be awaitable
    mock_delete = mocker.AsyncMock(return_value=None)
    mock_message.delete = mock_delete

    mocker.patch.object(mock_message, "delete", mock_delete)

    response = client.delete(f"/api/v1/messages/{message_id}")

    assert response.status_code == 204


def test_delete_message_not_found(client, mocker):
    """Test message deletion with not found error."""
    message_id = str(uuid4())

    # Mock the MessageModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.MessageModel.get_by_id", return_value=None
    )

    response = client.delete(f"/api/v1/messages/{message_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]
