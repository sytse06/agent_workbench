"""Unit tests for /api/v1/threads endpoint."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_workbench.api.database import get_session
from agent_workbench.api.routes.threads import router


def _make_app(mock_session):
    """Build an isolated FastAPI test app with the threads router."""
    app = FastAPI()
    app.include_router(router)

    async def override_session():
        yield mock_session

    app.dependency_overrides[get_session] = override_session
    return app


def _make_row(title="Test", preview="Preview text", offset_days=0):
    row = MagicMock()
    row.thread_id = uuid4()
    row.title = title
    row.preview = preview
    row.created_at = datetime(2026, 3, 19, 12, 0, 0)
    row.last_updated_at = datetime(2026, 3, 19 - offset_days, 13, 0, 0)
    return row


def _mock_session_with_rows(rows):
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = rows
    mock_session.execute = AsyncMock(return_value=mock_result)
    return mock_session


def test_get_threads_returns_ordered_list():
    """GET /threads returns threads in the order returned by the DB query."""
    row1 = _make_row(title="Thread 1", offset_days=0)
    row2 = _make_row(title="Thread 2", offset_days=1)
    client = TestClient(_make_app(_mock_session_with_rows([row1, row2])))

    response = client.get("/api/v1/threads/")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Thread 1"
    assert data[1]["title"] == "Thread 2"
    # Verify required fields are present
    assert "thread_id" in data[0]
    assert "preview" in data[0]
    assert "created_at" in data[0]
    assert "last_updated_at" in data[0]


def test_get_threads_empty_returns_empty_list():
    """GET /threads returns [] when no threads exist."""
    client = TestClient(_make_app(_mock_session_with_rows([])))

    response = client.get("/api/v1/threads/")

    assert response.status_code == 200
    assert response.json() == []
