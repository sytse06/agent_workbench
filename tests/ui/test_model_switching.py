# Model switching tests

from unittest.mock import MagicMock, patch

import pytest

from agent_workbench.ui.components.settings import (
    get_available_providers,
    get_provider_models,
)
from agent_workbench.ui.components.simple_client import LangGraphClient


@pytest.mark.asyncio
async def test_get_available_providers():
    """Test getting list of available providers"""
    providers = await get_available_providers()
    expected = ["openrouter", "ollama", "openai", "anthropic"]

    assert providers == expected
    assert len(providers) == 4


@pytest.mark.asyncio
async def test_get_provider_models():
    """Test getting models for specific providers"""
    # Test openrouter
    models = await get_provider_models("openrouter")
    expected = ["claude-3-5-sonnet-20241022", "gpt-4", "llama3.1"]
    assert models == expected

    # Test ollama
    models = await get_provider_models("ollama")
    expected = ["llama3.1", "mistral-7b", "phi3"]
    assert models == expected

    # Test unknown provider
    models = await get_provider_models("unknown")
    expected = ["llama3.1"]  # Default
    assert models == expected


@pytest.mark.asyncio
async def test_model_configuration_changes():
    """Test that different model configurations work correctly"""
    client = LangGraphClient()

    # Mock the HTTP client
    with patch.object(client.client, "post") as mock_post:
        from unittest.mock import Mock

        mock_response = Mock()
        mock_response.json.return_value = {
            "assistant_response": "Test response",
            "conversation_id": "test-config-id",
            "workflow_mode": "workbench",
            "execution_successful": True,
            "metadata": {},
        }
        mock_response.raise_for_status = MagicMock(return_value=None)
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_post.return_value = mock_response

        # Test different model configurations
        configs = [
            {
                "provider": "openrouter",
                "model_name": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
            },
            {"provider": "ollama", "model_name": "llama3.1", "temperature": 0.5},
            {"provider": "openai", "model_name": "gpt-4", "temperature": 0.9},
        ]

        for config in configs:
            result = await client.send_message(
                message="Hello", conversation_id="test-config-id", model_config=config
            )

            assert result["assistant_response"] == "Test response"
            assert result["reply"] == "Test response"  # Legacy compatibility
            assert result["conversation_id"] == "test-config-id"


if __name__ == "__main__":
    pytest.main([__file__])
