"""Unit tests for agent configuration API routes."""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.routes.agent_configs import router
from agent_workbench.models.schemas import AgentConfigResponse


@pytest.fixture
def app():
    """Create a FastAPI app with the agent config router."""
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


@pytest.mark.asyncio
async def test_create_agent_config_success(client, mocker):
    """Test successful agent configuration creation."""
    # Mock the session.execute method to return None (no existing config)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None

    # Mock the select function properly
    mock_select = mocker.patch("sqlalchemy.select")
    mock_select.return_value.where.return_value = MagicMock()

    mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", return_value=mock_result
    )

    # Mock the AgentConfigModel.create method
    mock_agent_config = MagicMock()
    mock_agent_config.id = uuid4()
    mock_agent_config.name = "Test Agent Config"
    mock_agent_config.description = "Test configuration"
    mock_agent_config.config = {"model": "gpt-4"}
    mock_agent_config.created_at = "2025-01-01T00:00:00"
    mock_agent_config.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.create",
        return_value=mock_agent_config,
    )

    # Mock the AgentConfigResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.AgentConfigResponse.model_validate",
        return_value=AgentConfigResponse(
            id=mock_agent_config.id,
            name=mock_agent_config.name,
            description=mock_agent_config.description,
            config=mock_agent_config.config,
            created_at=mock_agent_config.created_at,
            updated_at=mock_agent_config.updated_at,
        ),
    )

    response = client.post(
        "/api/v1/agent-configs/",
        json={
            "name": "Test Agent Config",
            "description": "Test configuration",
            "config": {"model": "gpt-4"},
        },
    )

    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["name"] == "Test Agent Config"


def test_create_agent_config_conflict(client, mocker):
    """Test agent configuration creation with conflict."""
    # Mock the session.execute method to return an existing config
    mock_existing_config = MagicMock()
    mock_existing_config.name = "Test Agent Config"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_existing_config

    mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", return_value=mock_result
    )

    response = client.post(
        "/api/v1/agent-configs/",
        json={"name": "Test Agent Config", "config": {"model": "gpt-4"}},
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]["message"]


def test_get_agent_config_success(client, mocker):
    """Test successful agent configuration retrieval."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method
    mock_agent_config = MagicMock()
    mock_agent_config.id = UUID(config_id)
    mock_agent_config.name = "Test Agent Config"
    mock_agent_config.description = "Test configuration"
    mock_agent_config.config = {"model": "gpt-4"}
    mock_agent_config.created_at = "2025-01-01T00:00:00"
    mock_agent_config.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id",
        return_value=mock_agent_config,
    )

    # Mock the AgentConfigResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.AgentConfigResponse.model_validate",
        return_value=AgentConfigResponse(
            id=mock_agent_config.id,
            name=mock_agent_config.name,
            description=mock_agent_config.description,
            config=mock_agent_config.config,
            created_at=mock_agent_config.created_at,
            updated_at=mock_agent_config.updated_at,
        ),
    )

    response = client.get(f"/api/v1/agent-configs/{config_id}")

    assert response.status_code == 200
    assert response.json()["id"] == config_id


def test_get_agent_config_not_found(client, mocker):
    """Test agent configuration not found error."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id", return_value=None
    )

    response = client.get(f"/api/v1/agent-configs/{config_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_list_agent_configs_success(client, mocker):
    """Test successful agent configurations listing."""
    # Mock the AgentConfigModel.get_all method
    mock_config1 = MagicMock()
    mock_config1.id = uuid4()
    mock_config1.name = "Test Config 1"
    mock_config1.description = "First test configuration"
    mock_config1.config = {"model": "gpt-4"}
    mock_config1.created_at = "2025-01-01T00:00:00"
    mock_config1.updated_at = "2025-01-01T00:00:00"

    mock_config2 = MagicMock()
    mock_config2.id = uuid4()
    mock_config2.name = "Test Config 2"
    mock_config2.description = "Second test configuration"
    mock_config2.config = {"model": "gpt-3.5-turbo"}
    mock_config2.created_at = "2025-01-01T00:00:00"
    mock_config2.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_all",
        return_value=[mock_config1, mock_config2],
    )

    # Mock the AgentConfigResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.AgentConfigResponse.model_validate",
        side_effect=[
            AgentConfigResponse(
                id=mock_config1.id,
                name=mock_config1.name,
                description=mock_config1.description,
                config=mock_config1.config,
                created_at=mock_config1.created_at,
                updated_at=mock_config1.updated_at,
            ),
            AgentConfigResponse(
                id=mock_config2.id,
                name=mock_config2.name,
                description=mock_config2.description,
                config=mock_config2.config,
                created_at=mock_config2.created_at,
                updated_at=mock_config2.updated_at,
            ),
        ],
    )

    response = client.get("/api/v1/agent-configs/")

    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["name"] == "Test Config 1"
    assert response.json()[1]["name"] == "Test Config 2"


def test_update_agent_config_success(client, mocker):
    """Test successful agent configuration update."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method
    mock_agent_config = MagicMock()
    mock_agent_config.id = UUID(config_id)
    mock_agent_config.name = "Original Name"
    mock_agent_config.description = "Original description"
    mock_agent_config.config = {"model": "gpt-4"}
    mock_agent_config.created_at = "2025-01-01T00:00:00"
    mock_agent_config.updated_at = "2025-01-01T00:00:00"

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id",
        return_value=mock_agent_config,
    )

    # Mock the session.execute method to return None (no conflicting config)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", return_value=mock_result
    )

    # Mock the agent_config.update method
    updated_config = MagicMock()
    updated_config.id = mock_agent_config.id
    updated_config.name = "Updated Name"
    updated_config.description = "Updated description"
    updated_config.config = mock_agent_config.config
    updated_config.created_at = mock_agent_config.created_at
    updated_config.updated_at = "2025-01-02T00:00:00"

    # Make the update method awaitable
    mock_update = mocker.AsyncMock(return_value=updated_config)
    mock_agent_config.update = mock_update

    mocker.patch.object(mock_agent_config, "update", mock_update)

    # Mock the AgentConfigResponse.model_validate method
    mocker.patch(
        "agent_workbench.models.schemas.AgentConfigResponse.model_validate",
        return_value=AgentConfigResponse(
            id=updated_config.id,
            name=updated_config.name,
            description=updated_config.description,
            config=updated_config.config,
            created_at=updated_config.created_at,
            updated_at=updated_config.updated_at,
        ),
    )

    response = client.put(
        f"/api/v1/agent-configs/{config_id}",
        json={"name": "Updated Name", "description": "Updated description"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_update_agent_config_not_found(client, mocker):
    """Test agent configuration update with not found error."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id", return_value=None
    )

    response = client.put(
        f"/api/v1/agent-configs/{config_id}", json={"name": "Updated Name"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]


def test_update_agent_config_conflict(client, mocker):
    """Test agent configuration update with conflict."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method
    mock_agent_config = MagicMock()
    mock_agent_config.id = UUID(config_id)
    mock_agent_config.name = "Original Name"

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id",
        return_value=mock_agent_config,
    )

    # Mock the session.execute method to return a conflicting config
    mock_conflicting_config = MagicMock()
    mock_conflicting_config.id = uuid4()  # Different ID
    mock_conflicting_config.name = "Updated Name"

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_conflicting_config

    mocker.patch(
        "sqlalchemy.ext.asyncio.AsyncSession.execute", return_value=mock_result
    )

    response = client.put(
        f"/api/v1/agent-configs/{config_id}", json={"name": "Updated Name"}
    )

    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]["message"]


def test_delete_agent_config_success(client, mocker):
    """Test successful agent configuration deletion."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method
    mock_agent_config = MagicMock()
    mock_agent_config.id = UUID(config_id)

    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id",
        return_value=mock_agent_config,
    )

    # Mock the agent_config.delete method to be awaitable
    mock_delete = mocker.AsyncMock(return_value=None)
    mock_agent_config.delete = mock_delete

    mocker.patch.object(mock_agent_config, "delete", mock_delete)

    response = client.delete(f"/api/v1/agent-configs/{config_id}")

    assert response.status_code == 204


def test_delete_agent_config_not_found(client, mocker):
    """Test agent configuration deletion with not found error."""
    config_id = str(uuid4())

    # Mock the AgentConfigModel.get_by_id method to return None
    mocker.patch(
        "agent_workbench.models.database.AgentConfigModel.get_by_id", return_value=None
    )

    response = client.delete(f"/api/v1/agent-configs/{config_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"]["message"]
