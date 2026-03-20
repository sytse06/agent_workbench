"""Unit tests for memory API routes."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from agent_workbench.main import app


def test_get_memory_no_session_returns_empty():
    with TestClient(app) as client:
        resp = client.get("/api/v1/memory/agents")
        assert resp.status_code == 200
        assert resp.json()["content"] == ""


def test_get_memory_invalid_key_returns_400():
    with TestClient(app) as client:
        resp = client.get("/api/v1/memory/invalid_key?session_id=abc")
        assert resp.status_code == 400


def test_put_memory_invalid_key_returns_400():
    with TestClient(app) as client:
        resp = client.put(
            "/api/v1/memory/invalid_key",
            json={"session_id": "abc", "content": "test"},
        )
        assert resp.status_code == 400


def test_get_memory_no_store_returns_empty():
    with patch("agent_workbench.services.memory_store.get_store", return_value=None):
        with TestClient(app) as client:
            resp = client.get("/api/v1/memory/agents?session_id=test-session")
            assert resp.status_code == 200
            assert resp.json()["content"] == ""


def test_put_memory_no_store_returns_503():
    with patch("agent_workbench.api.routes.memory.get_store", return_value=None):
        with TestClient(app) as client:
            resp = client.put(
                "/api/v1/memory/agents",
                json={"session_id": "abc", "content": "test"},
            )
            assert resp.status_code == 503
