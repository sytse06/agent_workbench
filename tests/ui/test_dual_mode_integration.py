"""
End-to-end dual-mode functionality tests for UI-003.

Tests complete dual-mode deployment, mode switching, and state isolation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestDualModeDeployment:
    """Test complete dual-mode deployment functionality"""

    def test_workbench_mode_deployment(self):
        """Test workbench mode deployment via APP_MODE"""
        with patch.dict("os.environ", {"APP_MODE": "workbench"}):
            from agent_workbench.main import app

            client = TestClient(app)

            # Test mode endpoint
            response = client.get("/api/mode")
            assert response.status_code == 200

            data = response.json()
            assert data["current_mode"] == "workbench"
            assert "workbench" in data["available_modes"]
            assert data["status"] == "healthy"

    def test_seo_coach_mode_deployment(self):
        """Test SEO coach mode deployment via APP_MODE"""
        with patch.dict("os.environ", {"APP_MODE": "seo_coach"}):
            from agent_workbench.main import app

            client = TestClient(app)

            # Test mode endpoint
            response = client.get("/api/mode")
            assert response.status_code == 200

            data = response.json()
            assert data["current_mode"] == "seo_coach"
            assert "seo_coach" in data["available_modes"]
            assert data["status"] == "healthy"

    def test_invalid_mode_fallback(self):
        """Test invalid APP_MODE falls back to workbench"""
        with patch.dict("os.environ", {"APP_MODE": "invalid_mode"}):
            from agent_workbench.main import app

            client = TestClient(app)

            # Should fallback to workbench mode
            response = client.get("/api/mode")
            assert response.status_code == 200

            data = response.json()
            assert data["current_mode"] == "workbench"

    def test_detailed_health_check_workbench(self):
        """Test detailed health check in workbench mode"""
        with patch.dict("os.environ", {"APP_MODE": "workbench"}):
            from agent_workbench.main import app

            client = TestClient(app)

            response = client.get("/api/health/detailed")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["mode"] == "workbench"
            assert data["interface_available"] is True
            assert "workbench" in data["available_modes"]
            assert "phase" in data
            assert "timestamp" in data

    def test_detailed_health_check_seo_coach(self):
        """Test detailed health check in SEO coach mode"""
        with patch.dict("os.environ", {"APP_MODE": "seo_coach"}):
            from agent_workbench.main import app

            client = TestClient(app)

            response = client.get("/api/health/detailed")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert data["mode"] == "seo_coach"
            assert data["interface_available"] is True
            assert "seo_coach" in data["available_modes"]


class TestModeIsolation:
    """Test that modes operate independently without interference"""

    def test_no_cross_mode_state_contamination(self):
        """Test that modes don't share or contaminate state"""
        from agent_workbench.ui.mode_factory import ModeFactory

        factory = ModeFactory()

        # Create both interfaces
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            with patch(
                "agent_workbench.ui.mode_factory.create_seo_coach_app"
            ) as mock_seo:
                mock_workbench_interface = MagicMock()
                mock_seo_interface = MagicMock()

                mock_workbench.return_value = mock_workbench_interface
                mock_seo.return_value = mock_seo_interface

                workbench = factory.create_interface("workbench")
                seo_coach = factory.create_interface("seo_coach")

                # Interfaces should be independent
                assert workbench != seo_coach
                assert id(workbench) != id(seo_coach)

                # Each factory should be called once
                mock_workbench.assert_called_once()
                mock_seo.assert_called_once()

    def test_mode_registry_isolation(self):
        """Test mode registries don't interfere with each other"""
        from agent_workbench.ui.mode_factory import ModeFactory

        factory1 = ModeFactory()
        factory2 = ModeFactory()

        # Register extension in first factory
        mock_extension = MagicMock()
        factory1.register_extension_mode("test_extension", mock_extension)

        # Second factory should not have the extension
        assert "test_extension" in factory1.extension_registry
        assert "test_extension" not in factory2.extension_registry

        # Available modes should be different
        modes1 = factory1.get_available_modes()
        modes2 = factory2.get_available_modes()

        assert "test_extension" in modes1
        assert "test_extension" not in modes2

    def test_environment_isolation_between_tests(self):
        """Test environment changes don't affect other tests"""
        from agent_workbench.ui.mode_factory import ModeFactory

        factory = ModeFactory()

        # Test with one environment
        with patch.dict("os.environ", {"APP_MODE": "workbench"}):
            mode1 = factory._determine_mode_safe(None)
            assert mode1 == "workbench"

        # Test with different environment
        with patch.dict("os.environ", {"APP_MODE": "seo_coach"}):
            mode2 = factory._determine_mode_safe(None)
            assert mode2 == "seo_coach"

        # Test with no environment (should use default)
        with patch.dict("os.environ", {}, clear=True):
            mode3 = factory._determine_mode_safe(None)
            assert mode3 == "workbench"


class TestLangGraphIntegration:
    """Test LangGraph integration works correctly for both modes"""

    @pytest.mark.asyncio
    async def test_workbench_langgraph_routing(self):
        """Test workbench mode routes to correct LangGraph workflow"""

        # Mock the consolidated service response
        mock_response_data = {
            "conversation_id": "test-123",
            "assistant_response": "Workbench response",
            "workflow_steps": ["workbench_processing"],
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {"workflow_mode": "workbench"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            # Set up the async context manager
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock()
            mock_client_instance.post.return_value = mock_response

            from agent_workbench.ui.components.simple_client import (
                SimpleLangGraphClient,
            )

            async with SimpleLangGraphClient() as client:
                model_config = {
                    "provider": "openrouter",
                    "model_name": "anthropic/claude-3-5-sonnet-20241022",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                }

                response = await client.send_message(
                    message="Test workbench message",
                    conversation_id="test-123",
                    model_config=model_config,
                )

                # Verify correct workflow routing
                assert response["execution_successful"]
                assert response["assistant_response"] == "Workbench response"
                assert "workbench_processing" in response.get("workflow_steps", [])

    @pytest.mark.asyncio
    async def test_seo_coach_langgraph_routing(self):
        """Test SEO coach mode routes to correct LangGraph workflow"""

        # Mock the consolidated service response for SEO coach
        mock_response_data = {
            "conversation_id": "test-456",
            "assistant_response": "SEO coaching response",
            "workflow_steps": ["seo_coach_processing"],
            "workflow_mode": "seo_coach",
            "execution_successful": True,
            "business_profile": {"business_name": "Test Business"},
            "coaching_context": {"phase": "analysis"},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data

            # Set up the async context manager
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock()
            mock_client_instance.post.return_value = mock_response

            from agent_workbench.ui.seo_coach_app import _handle_coaching_message

            # Mock business profile
            profile = {
                "business_name": "Test Business",
                "website_url": "https://test.com",
                "business_type": "Restaurant",
                "location": "Amsterdam",
                "target_keywords": "test",
                "seo_experience": "beginner",
            }

            # Test the SEO coach message handling
            result = await _handle_coaching_message(
                "Test SEO message", "test-456", profile
            )

            # Should return empty string and updated history
            assert isinstance(result, tuple)
            assert len(result) == 2


class TestErrorHandlingIntegration:
    """Test error handling works correctly in both modes"""

    def test_interface_creation_error_fallback(self):
        """Test graceful fallback when interface creation fails"""
        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_workbench.side_effect = Exception("Interface creation failed")

            from agent_workbench.main import app

            client = TestClient(app)

            # Should still provide API endpoints even if interface fails
            response = client.get("/api/mode")
            assert response.status_code == 200

    def test_invalid_mode_error_handling(self):
        """Test error handling for invalid modes"""
        from agent_workbench.ui.mode_factory import InvalidModeError, ModeFactory

        factory = ModeFactory()

        with pytest.raises(InvalidModeError):
            factory.create_interface("completely_invalid_mode")

    def test_mode_info_error_handling(self):
        """Test mode info endpoint error handling"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory_class.side_effect = Exception("Factory initialization failed")

            from agent_workbench.main import app

            client = TestClient(app)

            response = client.get("/api/mode")
            # Should return error status
            assert response.status_code == 500

    def test_health_check_degraded_state(self):
        """Test health check in degraded state"""
        with patch("agent_workbench.ui.mode_factory.ModeFactory") as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_interface.side_effect = Exception("Interface error")

            from agent_workbench.main import app

            client = TestClient(app)

            response = client.get("/api/health/detailed")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "degraded"
            assert data["interface_available"] is False
            assert "error" in data


class TestPerformanceIntegration:
    """Test performance aspects of dual-mode operation"""

    def test_mode_switching_performance(self):
        """Test mode switching doesn't significantly impact performance"""
        import time

        from agent_workbench.ui.mode_factory import ModeFactory

        factory = ModeFactory()

        # Test multiple mode determinations
        start_time = time.time()

        for _ in range(100):
            with patch.dict("os.environ", {"APP_MODE": "workbench"}):
                mode = factory._determine_mode_safe(None)
                assert mode == "workbench"

        end_time = time.time()
        duration = end_time - start_time

        # Should complete 100 mode determinations in reasonable time
        assert duration < 1.0  # Less than 1 second

    def test_interface_creation_caching(self):
        """Test that interface creation doesn't cache inappropriately"""
        from agent_workbench.ui.mode_factory import ModeFactory

        factory = ModeFactory()

        with patch(
            "agent_workbench.ui.mode_factory.create_workbench_app"
        ) as mock_workbench:
            mock_interface1 = MagicMock()
            mock_interface2 = MagicMock()

            # Each call should return a new interface (no caching)
            mock_workbench.side_effect = [mock_interface1, mock_interface2]

            interface1 = factory.create_interface("workbench")
            interface2 = factory.create_interface("workbench")

            # Should be called twice (no caching)
            assert mock_workbench.call_count == 2
            assert interface1 == mock_interface1
            assert interface2 == mock_interface2


class TestDeploymentScenarios:
    """Test various deployment scenarios"""

    def test_docker_environment_simulation(self):
        """Test Docker-like environment variable setup"""
        docker_env = {
            "APP_MODE": "seo_coach",
            "DATABASE_URL": "sqlite+aiosqlite:///./data/agent_workbench.db",
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
        }

        with patch.dict("os.environ", docker_env):
            from agent_workbench.ui.mode_factory import get_mode_from_environment

            mode = get_mode_from_environment()
            assert mode == "seo_coach"

    def test_production_environment_simulation(self):
        """Test production-like environment"""
        prod_env = {"APP_MODE": "workbench", "DEBUG": "false", "LOG_LEVEL": "INFO"}

        with patch.dict("os.environ", prod_env):
            from agent_workbench.main import app

            client = TestClient(app)

            response = client.get("/api/mode")
            assert response.status_code == 200

            data = response.json()
            assert data["current_mode"] == "workbench"
            assert data["phase"] == "1"

    def test_staging_environment_simulation(self):
        """Test staging environment with mode switching"""
        staging_env = {"APP_MODE": "seo_coach", "DEBUG": "true"}

        with patch.dict("os.environ", staging_env):
            from agent_workbench.main import app

            client = TestClient(app)

            # Test that both modes are available for testing
            response = client.get("/api/mode")
            assert response.status_code == 200

            data = response.json()
            assert "workbench" in data["available_modes"]
            assert "seo_coach" in data["available_modes"]
            assert data["current_mode"] == "seo_coach"
