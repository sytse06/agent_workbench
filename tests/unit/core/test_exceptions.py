"""Tests for core exceptions."""

from agent_workbench.core.exceptions import (
    AgentWorkbenchError,
    LLMProviderError,
    ModelConfigurationError,
)


class TestAgentWorkbenchError:
    """Tests for AgentWorkbenchError class."""

    def test_agent_workbench_error_creation(self):
        """Test AgentWorkbenchError creation."""
        error = AgentWorkbenchError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code is None

    def test_agent_workbench_error_with_error_code(self):
        """Test AgentWorkbenchError creation with error code."""
        error = AgentWorkbenchError("Test error message", "TEST_ERROR")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "TEST_ERROR"


class TestLLMProviderError:
    """Tests for LLMProviderError class."""

    def test_llm_provider_error_creation(self):
        """Test LLMProviderError creation."""
        error = LLMProviderError("Provider error message")

        assert str(error) == "Provider error message"
        assert error.message == "Provider error message"
        assert error.error_code == "LLM_PROVIDER_ERROR"
        assert error.provider is None

    def test_llm_provider_error_with_provider(self):
        """Test LLMProviderError creation with provider."""
        error = LLMProviderError("Provider error message", "openai")

        assert str(error) == "Provider error message"
        assert error.message == "Provider error message"
        assert error.error_code == "LLM_PROVIDER_ERROR"
        assert error.provider == "openai"


class TestModelConfigurationError:
    """Tests for ModelConfigurationError class."""

    def test_model_configuration_error_creation(self):
        """Test ModelConfigurationError creation."""
        error = ModelConfigurationError("Config error message")

        assert str(error) == "Config error message"
        assert error.message == "Config error message"
        assert error.error_code == "MODEL_CONFIG_ERROR"
        assert error.model_config is None

    def test_model_configuration_error_with_config(self):
        """Test ModelConfigurationError creation with config."""
        config = {"provider": "openai", "model_name": "gpt-3.5-turbo"}
        error = ModelConfigurationError("Config error message", config)

        assert str(error) == "Config error message"
        assert error.message == "Config error message"
        assert error.error_code == "MODEL_CONFIG_ERROR"
        assert error.model_config == config
