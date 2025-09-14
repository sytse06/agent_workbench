"""Tests for model API routes."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from agent_workbench.main import app

client = TestClient(app)


class TestModelRoutes:
    """Tests for model API routes."""

    def test_get_providers(self):
        """Test GET /api/v1/models/providers endpoint."""
        # Make request
        response = client.get("/api/v1/models/providers")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return a list (even if empty for now)
        data = response.json()
        assert isinstance(data, list)

    @patch("agent_workbench.api.routes.models.provider_registry")
    def test_get_provider_models(self, mock_provider_registry):
        """Test GET /api/v1/models/{provider} endpoint."""
        # Setup mock
        mock_provider_registry.get_provider_models.return_value = [
            {
                "name": "llama3",
                "display_name": "Llama 3",
                "context_length": 8192,
                "supports_streaming": True,
                "supports_tools": False,
            }
        ]

        # Make request
        response = client.get("/api/v1/models/ollama")

        # Should return 200 OK
        assert response.status_code == 200

        # Should return model list
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["name"] == "llama3"

    def test_get_provider_models_invalid_provider(self):
        """Test GET /api/v1/models/{provider} with invalid provider."""
        # Make request
        response = client.get("/api/v1/models/invalid_provider")

        # Should return 200 OK (returns empty list for invalid providers)
        assert response.status_code == 200

        # Should return empty list
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
