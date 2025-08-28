from fastapi.testclient import TestClient
from agent_workbench.main import app


client = TestClient(app)


def test_health_check():
    """Test that the health endpoint returns a successful response."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
