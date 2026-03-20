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


def test_delete_nonexistent_thread_returns_404():
    """DELETE /threads/{id} returns 404 when thread does not exist."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    client = TestClient(_make_app(mock_session))
    response = client.delete(f"/api/v1/threads/{uuid4()}")
    assert response.status_code == 404


def test_delete_existing_thread_returns_204():
    """DELETE /threads/{id} returns 204 and deletes metadata row."""
    mock_session = AsyncMock()
    mock_row = MagicMock()
    mock_select_result = MagicMock()
    mock_select_result.scalar_one_or_none.return_value = mock_row
    mock_delete_result = MagicMock()
    # First execute = SELECT (returns row), second = DELETE documents
    mock_session.execute = AsyncMock(
        side_effect=[mock_select_result, mock_delete_result]
    )
    mock_session.delete = AsyncMock()
    mock_session.commit = AsyncMock()

    client = TestClient(_make_app(mock_session))
    response = client.delete(f"/api/v1/threads/{uuid4()}")
    assert response.status_code == 204
    mock_session.delete.assert_called_once_with(mock_row)


def test_get_thread_messages_service_not_ready(mocker):
    """GET /threads/{id}/messages returns 503 when agent service not ready."""
    mocker.patch(
        "agent_workbench.api.routes.threads.get_agent_graph",
        return_value=None,
    )
    mock_session = AsyncMock()
    client = TestClient(_make_app(mock_session))
    response = client.get(f"/api/v1/threads/{uuid4()}/messages")
    assert response.status_code == 503


def test_get_thread_messages_thread_not_found(mocker):
    """GET /threads/{id}/messages returns 404 when thread has no checkpointed state."""
    mock_graph = AsyncMock()
    mock_graph.get_state = AsyncMock(return_value=None)
    mocker.patch(
        "agent_workbench.api.routes.threads.get_agent_graph",
        return_value=mock_graph,
    )
    mock_session = AsyncMock()
    client = TestClient(_make_app(mock_session))
    response = client.get(f"/api/v1/threads/{uuid4()}/messages")
    assert response.status_code == 404
