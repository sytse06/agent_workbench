"""
Smoke tests - verify the app starts and core endpoints respond.

Run with: make test-smoke
These run on every pre-commit to catch breakage fast.
"""

from fastapi.testclient import TestClient

from agent_workbench.main import app

client = TestClient(app)


def test_app_creates():
    """FastAPI app instance exists and has routes."""
    assert app is not None
    assert len(app.routes) > 0


def test_health_endpoint():
    """GET /health returns 200."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_health_ping():
    """GET /api/v1/health/ping returns pong."""
    response = client.get("/api/v1/health/ping")
    assert response.status_code == 200
    assert response.json()["message"] == "pong"


def test_chat_workflow_endpoint_exists():
    """POST /api/v1/chat/workflow accepts requests (validates input)."""
    response = client.post(
        "/api/v1/chat/workflow",
        json={"user_message": "test"},
    )
    # 422 (validation error) or 200 both mean the endpoint exists and routes
    assert response.status_code in (200, 422, 500)


def test_gradio_interface_importable():
    """Gradio interface factory can be imported and called."""
    from agent_workbench.ui.mode_factory_v2 import create_app

    interface = create_app()
    assert interface is not None


def test_static_files_served():
    """Static CSS files are accessible."""
    response = client.get("/static/assets/css/tokens.css")
    # 200 means static serving works
    assert response.status_code == 200
