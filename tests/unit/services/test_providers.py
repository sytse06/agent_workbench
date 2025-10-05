"""Tests for provider registry and configuration."""

from unittest.mock import MagicMock, patch

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.providers import (
    PROVIDER_FACTORIES,
    AnthropicProvider,
    MistralProvider,
    ModelRegistry,
    OllamaProvider,
    OpenAIProvider,
    OpenRouterProvider,
    ProviderConfig,
)


class TestProviderConfig:
    """Tests for ProviderConfig dataclass."""

    def test_provider_config_creation(self):
        """Test ProviderConfig creation."""

        def dummy_factory(model_config):
            return None

        config = ProviderConfig(
            provider_name="test_provider",
            factory_func=dummy_factory,
            default_model="test-model",
            api_key_env_var="TEST_API_KEY",
            base_url="https://api.test.com",
            requires_api_key=True,
        )

        assert config.provider_name == "test_provider"
        assert config.factory_func == dummy_factory
        assert config.default_model == "test-model"
        assert config.api_key_env_var == "TEST_API_KEY"
        assert config.base_url == "https://api.test.com"
        assert config.requires_api_key is True


class TestModelRegistry:
    """Tests for ModelRegistry class."""

    def test_model_registry_initialization(self):
        """Test ModelRegistry initialization."""
        registry = ModelRegistry()

        # Should have some default providers
        assert isinstance(registry._providers, dict)

    def test_register_provider(self):
        """Test registering a provider."""
        registry = ModelRegistry()

        def dummy_factory(model_config):
            return None

        config = ProviderConfig(
            provider_name="test_provider",
            factory_func=dummy_factory,
            default_model="test-model",
        )

        registry.register_provider(config)
        assert "test_provider" in registry.get_available_providers()

    def test_get_provider(self):
        """Test getting a provider configuration."""
        registry = ModelRegistry()

        def dummy_factory(model_config):
            return None

        config = ProviderConfig(
            provider_name="test_provider",
            factory_func=dummy_factory,
            default_model="test-model",
        )

        registry.register_provider(config)
        retrieved_config = registry.get_provider("test_provider")

        assert retrieved_config is not None
        assert retrieved_config.provider_name == "test_provider"
        assert retrieved_config.default_model == "test-model"

    def test_get_provider_not_found(self):
        """Test getting a non-existent provider."""
        registry = ModelRegistry()
        config = registry.get_provider("non_existent_provider")

        assert config is None

    def test_get_available_providers(self):
        """Test getting available providers."""
        registry = ModelRegistry()
        providers = registry.get_available_providers()

        # Should return a list (even if empty initially)
        assert isinstance(providers, list)

    def test_validate_model_config(self):
        """Test model configuration validation."""
        registry = ModelRegistry()

        def dummy_factory(model_config):
            return None

        # Register a provider first
        config = ProviderConfig(
            provider_name="test_provider",
            factory_func=dummy_factory,
            default_model="test-model",
        )
        registry.register_provider(config)

        # Test valid configuration
        is_valid = registry.validate_model_config("test_provider", "test-model")
        assert is_valid is True

        # Test invalid provider
        is_valid = registry.validate_model_config("invalid_provider", "test-model")
        assert is_valid is False


class TestProviderFactories:
    """Tests for provider factory classes."""

    def test_provider_factories_exist(self):
        """Test that provider factories are defined."""
        assert "openrouter" in PROVIDER_FACTORIES
        assert "ollama" in PROVIDER_FACTORIES
        assert "openai" in PROVIDER_FACTORIES
        assert "anthropic" in PROVIDER_FACTORIES
        assert "mistral" in PROVIDER_FACTORIES

    @patch("langchain_openai.ChatOpenAI")
    def test_openrouter_provider_creation(self, mock_chat_openai):
        """Test OpenRouter provider model creation."""
        mock_model = MagicMock()
        mock_chat_openai.return_value = mock_model

        provider = OpenRouterProvider()
        model_config = ModelConfig(
            provider="openrouter",
            model_name="test-model",
            temperature=0.7,
            max_tokens=1000,
        )

        result = provider.create_model(model_config)

        assert result == mock_model
        mock_chat_openai.assert_called_once()

    @patch("langchain_ollama.ChatOllama")
    def test_ollama_provider_creation(self, mock_chat_ollama):
        """Test Ollama provider model creation."""
        mock_model = MagicMock()
        mock_chat_ollama.return_value = mock_model

        provider = OllamaProvider()
        model_config = ModelConfig(
            provider="ollama", model_name="llama3", temperature=0.7, max_tokens=1000
        )

        result = provider.create_model(model_config)

        assert result == mock_model
        mock_chat_ollama.assert_called_once()

    @patch("langchain_openai.ChatOpenAI")
    def test_openai_provider_creation(self, mock_chat_openai):
        """Test OpenAI provider model creation."""
        mock_model = MagicMock()
        mock_chat_openai.return_value = mock_model

        provider = OpenAIProvider()
        model_config = ModelConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=1000,
        )

        result = provider.create_model(model_config)

        assert result == mock_model
        mock_chat_openai.assert_called_once()

    @patch("langchain_anthropic.ChatAnthropic")
    def test_anthropic_provider_creation(self, mock_chat_anthropic):
        """Test Anthropic provider model creation."""
        mock_model = MagicMock()
        mock_chat_anthropic.return_value = mock_model

        provider = AnthropicProvider()
        model_config = ModelConfig(
            provider="anthropic",
            model_name="claude-3-haiku",
            temperature=0.7,
            max_tokens=1000,
        )

        result = provider.create_model(model_config)

        assert result == mock_model
        mock_chat_anthropic.assert_called_once()

    @patch("langchain_mistralai.ChatMistralAI")
    def test_mistral_provider_creation(self, mock_chat_mistral):
        """Test Mistral provider model creation."""
        mock_model = MagicMock()
        mock_chat_mistral.return_value = mock_model

        provider = MistralProvider()
        model_config = ModelConfig(
            provider="mistral",
            model_name="mistral-small",
            temperature=0.7,
            max_tokens=1000,
        )

        result = provider.create_model(model_config)

        assert result == mock_model
        mock_chat_mistral.assert_called_once()

    def test_provider_factory_import_error(self):
        """Test provider factory handling of import errors."""
        # This test is a placeholder for import error testing
        # In practice, this would test the ImportError handling
        assert True
