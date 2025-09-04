"""Unit tests for health check API routes."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent_workbench.api.routes.health import router


@pytest.fixture
def app():
    """Create a FastAPI app with the health router."""
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


def test_health_check_healthy(client, mocker):
    """Test health check when database is connected."""
    # Mock the check_database_connection function to return True
    mocker.patch(
        "src.agent_workbench.api.routes.health.check_database_connection",
        return_value=True,
    )

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "healthy"
    assert json_response["database_connected"] is True
    assert "timestamp" in json_response


def test_health_check_unhealthy(client, mocker):
    """Test health check when database is not connected."""
    # Mock the check_database_connection function to return False
    mocker.patch(
        "src.agent_workbench.api.routes.health.check_database_connection",
        return_value=False,
    )

    response = client.get("/api/v1/health/")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "unhealthy"
    assert json_response["database_connected"] is False
    assert "timestamp" in json_response


def test_ping(client):
    """Test ping endpoint."""
    response = client.get("/api/v1/health/ping")

    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "pong"
    assert "timestamp" in json_response
