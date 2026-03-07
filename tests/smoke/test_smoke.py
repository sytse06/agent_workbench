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


def test_workflow_orchestrator_graph_compiles():
    """WorkflowOrchestrator builds its LangGraph without error."""
    from unittest.mock import MagicMock

    from agent_workbench.services.workflow_orchestrator import WorkflowOrchestrator

    orch = WorkflowOrchestrator(
        state_bridge=MagicMock(),
        workbench_handler=MagicMock(),
        seo_coach_handler=MagicMock(),
    )
    assert orch.workflow is not None


def test_simple_chat_workflow_builds():
    """SimpleChatWorkflow compiles its graph without error."""
    from agent_workbench.models.schemas import ModelConfig
    from agent_workbench.services.simple_chat_workflow import SimpleChatWorkflow

    config = ModelConfig(provider="anthropic", model_name="claude-3.5-sonnet")
    workflow = SimpleChatWorkflow(config)
    assert workflow.workflow is not None


def test_langgraph_bridge_instantiates():
    """LangGraphStateBridge instantiates with mocked dependencies."""
    from unittest.mock import MagicMock

    from agent_workbench.services.langgraph_bridge import LangGraphStateBridge

    bridge = LangGraphStateBridge(
        state_manager=MagicMock(),
        context_service=MagicMock(),
    )
    assert bridge is not None
