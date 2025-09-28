"""Provider registry and configuration for LLM services."""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel


@dataclass
class ProviderConfig:
    """Enhanced configuration for LLM providers with factory function."""

    provider_name: str
    factory_func: Any  # Callable[[BaseModel], BaseChatModel]
    default_model: str
    api_key_env_var: Optional[str] = None
    base_url: Optional[str] = None
    requires_api_key: bool = True
    required_packages: Optional[List[str]] = None

    def __post_init__(self):
        if self.required_packages is None:
            self.required_packages = []


class ModelRegistry:
    """Registry for managing LLM providers and their configurations."""

    def __init__(self) -> None:
        self._providers: Dict[str, ProviderConfig] = {}
        self._initialize_default_providers()

    def _initialize_default_providers(self) -> None:
        """Initialize default provider configurations."""
        # Register default providers with their factory functions

        self.register_provider(
            ProviderConfig(
                provider_name="openrouter",
                factory_func=self._create_openrouter_model,
                default_model="mistralai/mistral-7b-instruct",
                api_key_env_var="OPENROUTER_API_KEY",
                base_url="https://openrouter.ai/api/v1",
                requires_api_key=True,
                required_packages=["langchain-openai"],
            )
        )

        self.register_provider(
            ProviderConfig(
                provider_name="ollama",
                factory_func=self._create_ollama_model,
                default_model="llama3.1",
                api_key_env_var=None,
                base_url="http://localhost:11434",
                requires_api_key=False,
                required_packages=["langchain-ollama"],
            )
        )

        self.register_provider(
            ProviderConfig(
                provider_name="openai",
                factory_func=self._create_openai_model,
                default_model="gpt-3.5-turbo",
                api_key_env_var="OPENAI_API_KEY",
                base_url=None,
                requires_api_key=True,
                required_packages=["langchain-openai"],
            )
        )

        self.register_provider(
            ProviderConfig(
                provider_name="anthropic",
                factory_func=self._create_anthropic_model,
                default_model="claude-3-haiku-20240307",
                api_key_env_var="ANTHROPIC_API_KEY",
                base_url=None,
                requires_api_key=True,
                required_packages=["langchain-anthropic"],
            )
        )

        self.register_provider(
            ProviderConfig(
                provider_name="mistral",
                factory_func=self._create_mistral_model,
                default_model="mistral-small",
                api_key_env_var="MISTRAL_API_KEY",
                base_url=None,
                requires_api_key=True,
                required_packages=["langchain-mistralai"],
            )
        )

        self.register_provider(
            ProviderConfig(
                provider_name="google",
                factory_func=self._create_google_model,
                default_model="gemini-2.5-flash",
                api_key_env_var="GEMINI_API_KEY",
                base_url=None,
                requires_api_key=True,
                required_packages=["langchain-google-genai"],
            )
        )

    def register_provider(self, config: ProviderConfig) -> None:
        """
        Register a new provider configuration.

        Args:
            config: Provider configuration to register
        """
        self._providers[config.provider_name.lower()] = config

    def get_provider(self, provider_name: str) -> Optional[ProviderConfig]:
        """
        Get provider configuration by name.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider configuration or None if not found
        """
        return self._providers.get(provider_name.lower())

    def get_available_providers(self) -> List[str]:
        """
        Get list of available provider names.

        Returns:
            List of provider names
        """
        return list(self._providers.keys())

    def get_provider_models(self, provider_name: str) -> List[Dict[str, Any]]:
        """
        Get available models for a provider.

        Args:
            provider_name: Name of the provider

        Returns:
            List of model information dictionaries
        """
        # This would typically be implemented to fetch from provider APIs
        # For now, return empty list - models will be validated at runtime
        return []

    def validate_model_config(self, provider: str, model_name: str) -> bool:
        """Validate if a model configuration is supported.

        Args:
            provider: Provider name
            model_name: Model name

        Returns:
            True if valid, False otherwise
        """
        provider_config = self.get_provider(provider)
        return provider_config is not None

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create a chat model instance using the appropriate provider factory.

        Args:
            model_config: Model configuration

        Returns:
            Chat model instance

        Raises:
            ValueError: If provider not found or model creation fails
        """
        provider_config = self.get_provider(model_config.provider)
        if not provider_config:
            available = ", ".join(self.get_available_providers())
            raise ValueError(
                f"Unsupported provider '{model_config.provider}'. "
                f"Available: {available}"
            )

        try:
            return provider_config.factory_func(model_config)
        except ImportError as e:
            packages = ", ".join(provider_config.required_packages or [])
            raise ImportError(
                f"Provider '{model_config.provider}' requires packages: {packages}. "
                f"Install with: pip install "
                f"{' '.join(provider_config.required_packages or [])}"
            ) from e

    # Factory functions for each provider (replaces separate factory classes)
    def _create_openrouter_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create OpenRouter chat model."""
        from langchain_openai import ChatOpenAI

        api_key = (
            model_config.extra_params.get("api_key")
            if hasattr(model_config, "extra_params") and model_config.extra_params
            else os.getenv("OPENROUTER_API_KEY")
        )

        return ChatOpenAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

    def _create_ollama_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Ollama chat model."""
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model_config.model_name,
            temperature=model_config.temperature,
            num_predict=model_config.max_tokens,
            **getattr(model_config, "extra_params", {}),
        )

    def _create_openai_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create OpenAI chat model."""
        from langchain_openai import ChatOpenAI

        api_key = (
            model_config.extra_params.get("api_key")
            if hasattr(model_config, "extra_params") and model_config.extra_params
            else os.getenv("OPENAI_API_KEY")
        )

        return ChatOpenAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=api_key,
        )

    def _create_anthropic_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Anthropic chat model."""
        from langchain_anthropic import ChatAnthropic

        api_key = (
            model_config.extra_params.get("api_key")
            if hasattr(model_config, "extra_params") and model_config.extra_params
            else os.getenv("ANTHROPIC_API_KEY")
        )

        return ChatAnthropic(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            api_key=api_key,
        )

    def _create_mistral_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Mistral chat model."""
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_tokens=model_config.max_tokens,
            **getattr(model_config, "extra_params", {}),
        )

    def _create_google_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Google chat model."""
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = (
            model_config.extra_params.get("api_key")
            if hasattr(model_config, "extra_params") and model_config.extra_params
            else os.getenv("GEMINI_API_KEY")
        )

        return ChatGoogleGenerativeAI(
            model=model_config.model_name,
            temperature=model_config.temperature,
            max_output_tokens=model_config.max_tokens,
            google_api_key=api_key,
        )


# Global provider registry instance
provider_registry = ModelRegistry()


class ProviderFactory(ABC):
    """Abstract base class for provider factories."""

    @abstractmethod
    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """
        Create a chat model instance from configuration.

        Args:
            model_config: Model configuration

        Returns:
            Chat model instance
        """
        pass


class OpenRouterProvider(ProviderFactory):
    """Provider factory for OpenRouter."""

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create OpenRouter chat model."""
        try:
            import os

            from langchain_openai import ChatOpenAI

            # Get API key from environment or model config
            api_key = (
                model_config.extra_params.get("api_key")
                if hasattr(model_config, "extra_params") and model_config.extra_params
                else os.getenv("OPENROUTER_API_KEY")
            )

            return ChatOpenAI(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key,
            )
        except ImportError as e:
            raise ImportError(
                "OpenRouter provider requires 'langchain-openai' package. "
                "Install it with: pip install langchain-openai"
            ) from e


class OllamaProvider(ProviderFactory):
    """Provider factory for Ollama."""

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Ollama chat model."""
        try:
            from langchain_ollama import ChatOllama

            return ChatOllama(
                model=model_config.model_name,
                temperature=model_config.temperature,
                num_predict=model_config.max_tokens,
                **model_config.extra_params,
            )
        except ImportError as e:
            raise ImportError(
                "Ollama provider requires 'langchain-ollama' package. "
                "Install it with: pip install langchain-ollama"
            ) from e


class OpenAIProvider(ProviderFactory):
    """Provider factory for OpenAI."""

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create OpenAI chat model."""
        try:
            import os

            from langchain_openai import ChatOpenAI

            # Get API key from environment
            api_key = (
                model_config.extra_params.get("api_key")
                if hasattr(model_config, "extra_params") and model_config.extra_params
                else os.getenv("OPENAI_API_KEY")
            )

            return ChatOpenAI(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                api_key=api_key,
            )
        except ImportError as e:
            raise ImportError(
                "OpenAI provider requires 'langchain-openai' package. "
                "Install it with: pip install langchain-openai"
            ) from e


class AnthropicProvider(ProviderFactory):
    """Provider factory for Anthropic."""

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Anthropic chat model."""
        try:
            import os

            from langchain_anthropic import ChatAnthropic

            # Get API key from environment
            api_key = (
                model_config.extra_params.get("api_key")
                if hasattr(model_config, "extra_params") and model_config.extra_params
                else os.getenv("ANTHROPIC_API_KEY")
            )

            return ChatAnthropic(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                api_key=api_key,
            )
        except ImportError as e:
            raise ImportError(
                "Anthropic provider requires 'langchain-anthropic' package. "
                "Install it with: pip install langchain-anthropic"
            ) from e


class MistralProvider(ProviderFactory):
    """Provider factory for Mistral."""

    def create_model(self, model_config: BaseModel) -> BaseChatModel:
        """Create Mistral chat model."""
        try:
            from langchain_mistralai import ChatMistralAI

            return ChatMistralAI(
                model=model_config.model_name,
                temperature=model_config.temperature,
                max_tokens=model_config.max_tokens,
                **model_config.extra_params,
            )
        except ImportError as e:
            raise ImportError(
                "Mistral provider requires 'langchain-mistralai' package. "
                "Install it with: pip install langchain-mistralai"
            ) from e


# Provider factory registry
PROVIDER_FACTORIES: Dict[str, Type[ProviderFactory]] = {
    "openrouter": OpenRouterProvider,
    "ollama": OllamaProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "mistral": MistralProvider,
    "google": "GoogleProvider",  # Will be added if needed
}
