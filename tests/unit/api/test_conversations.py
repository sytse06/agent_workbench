"""Unit tests for conversation API routes."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.routes.conversations import router
from agent_workbench.models.schemas import ConversationResponse


@pytest.fixture
def app():
    """Create a FastAPI app with the conversation router."""
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


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {"user_id": str(uuid4()), "title": "Test Conversation"}


@pytest.fixture
def sample_conversation_response(sample_conversation_data):
    """Sample conversation response for testing."""
    data = sample_conversation_data.copy()
    data["id"] = str(uuid4())
    data["created_at"] = "2025-01-01T00:00:00"
    data["updated_at"] = "2025-01-01T00:00:00"
    return data


def test_create_conversation_success(client, mocker):
    """Test successful conversation creation."""
    # Mock the ConversationModel.create method
    mock_conversation = MagicMock()
    mock_conversation.id = uuid4()
    mock_conversation.user_id = uuid4()
    mock_conversation.title = "Test Conversation"
    mock_conversation.created_at = "2025-01-01T00:00:00"
    mock_conversation.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.create",
        return_value=mock_conversation,
    )

    # Mock the ConversationResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.ConversationResponse.model_validate",
        return_value=ConversationResponse(
            id=mock_conversation.id,
            user_id=mock_conversation.user_id,
            title=mock_conversation.title,
            created_at=mock_conversation.created_at,
            updated_at=mock_conversation.updated_at,
        ),
    )

    response = client.post(
        "/api/v1/conversations/",
        json={"user_id": str(uuid4()), "title": "Test Conversation"},
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["title"] == "Test Conversation"


def test_get_conversation_success(client, mocker):
    """Test successful conversation retrieval."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method
    mock_conversation = MagicMock()
    mock_conversation.id = UUID(conversation_id)
    mock_conversation.user_id = uuid4()
    mock_conversation.title = "Test Conversation"
    mock_conversation.created_at = "2025-01-01T00:00:00"
    mock_conversation.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id",
        return_value=mock_conversation,
    )

    # Mock the ConversationResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.ConversationResponse.model_validate",
        return_value=ConversationResponse(
            id=mock_conversation.id,
            user_id=mock_conversation.user_id,
            title=mock_conversation.title,
            created_at=mock_conversation.created_at,
            updated_at=mock_conversation.updated_at,
        ),
    )

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 200
    assert response.json()["id"] == conversation_id


def test_get_conversation_not_found(client, mocker):
    """Test conversation not found error."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id", return_value=None
    )

    response = client.get(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["detail"]


def test_list_conversations_success(client, mocker):
    """Test successful conversations listing."""
    # Mock the session.execute method to return conversations
    mock_conversation1 = MagicMock()
    mock_conversation1.id = uuid4()
    mock_conversation1.user_id = uuid4()
    mock_conversation1.title = "Test Conversation 1"
    mock_conversation1.created_at = "2025-01-01T00:00:00"
    mock_conversation1.updated_at = "2025-01-01T00:00:00"

    mock_conversation2 = MagicMock()
    mock_conversation2.id = uuid4()
    mock_conversation2.user_id = uuid4()
    mock_conversation2.title = "Test Conversation 2"
    mock_conversation2.created_at = "2025-01-01T00:00:00"
    mock_conversation2.updated_at = "2025-01-01T00:00:00"

    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [mock_conversation1, mock_conversation2]

    mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", return_value=mock_result
    )

    # Mock the ConversationResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.ConversationResponse.model_validate",
        side_effect=[
            ConversationResponse(
                id=mock_conversation1.id,
                user_id=mock_conversation1.user_id,
                title=mock_conversation1.title,
                created_at=mock_conversation1.created_at,
                updated_at=mock_conversation1.updated_at,
            ),
            ConversationResponse(
                id=mock_conversation2.id,
                user_id=mock_conversation2.user_id,
                title=mock_conversation2.title,
                created_at=mock_conversation2.created_at,
                updated_at=mock_conversation2.updated_at,
            ),
        ],
    )

    response = client.get("/api/v1/conversations/")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["title"] == "Test Conversation 1"
    assert response.json()[1]["title"] == "Test Conversation 2"


def test_update_conversation_success(client, mocker):
    """Test successful conversation update."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method
    mock_conversation = MagicMock()
    mock_conversation.id = UUID(conversation_id)
    mock_conversation.user_id = uuid4()
    mock_conversation.title = "Original Title"
    mock_conversation.created_at = "2025-01-01T00:00:00"
    mock_conversation.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id",
        return_value=mock_conversation,
    )

    # Mock the conversation.update method
    updated_conversation = MagicMock()
    updated_conversation.id = mock_conversation.id
    updated_conversation.user_id = mock_conversation.user_id
    updated_conversation.title = "Updated Title"
    updated_conversation.created_at = mock_conversation.created_at
    updated_conversation.updated_at = "2025-01-02T00:00:00"

    # Make the update method awaitable
    mock_update = mocker.AsyncMock(return_value=updated_conversation)
    mock_conversation.update = mock_update

    mocker.patch.object(mock_conversation, "update", mock_update)

    # Mock the ConversationResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.ConversationResponse.model_validate",
        return_value=ConversationResponse(
            id=updated_conversation.id,
            user_id=updated_conversation.user_id,
            title=updated_conversation.title,
            created_at=updated_conversation.created_at,
            updated_at=updated_conversation.updated_at,
        ),
    )

    response = client.put(
        f"/api/v1/conversations/{conversation_id}", json={"title": "Updated Title"}
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_update_conversation_not_found(client, mocker):
    """Test conversation update with not found error."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id", return_value=None
    )

    response = client.put(
        f"/api/v1/conversations/{conversation_id}", json={"title": "Updated Title"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["detail"]


def test_delete_conversation_success(client, mocker):
    """Test successful conversation deletion."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method
    mock_conversation = MagicMock()
    mock_conversation.id = UUID(conversation_id)

    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id",
        return_value=mock_conversation,
    )

    # Mock the conversation.delete method to be awaitable
    mock_delete = mocker.AsyncMock(return_value=None)
    mock_conversation.delete = mock_delete

    mocker.patch.object(mock_conversation, "delete", mock_delete)

    response = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 204


def test_delete_conversation_not_found(client, mocker):
    """Test conversation deletion with not found error."""
    conversation_id = str(uuid4())

    # Mock the ConversationModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.ConversationModel.get_by_id", return_value=None
    )

    response = client.delete(f"/api/v1/conversations/{conversation_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["detail"]
