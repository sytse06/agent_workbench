"""Model configuration service for dynamic provider-model management."""

import os
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ModelOption:
    """Represents a model option with provider and display info."""
    provider: str
    model_name: str
    display_name: str
    description: str = ""


class ModelConfigService:
    """Service for managing model configurations from environment variables."""

    def __init__(self):
        self.refresh_config()

    def refresh_config(self):
        """Refresh configuration from environment variables."""
        # Primary provider-model pairs
        self.default_provider = os.getenv("DEFAULT_PROVIDER", "openrouter")
        self.default_primary = os.getenv("DEFAULT_PRIMARY_MODEL", "anthropic/claude-3.5-sonnet")
        self.default_secondary = os.getenv("DEFAULT_SECONDARY_MODEL", "openai/gpt-4o-mini")

        # Secondary provider-model pairs
        self.secondary_provider = os.getenv("SECONDARY_PROVIDER", "anthropic")
        self.secondary_primary = os.getenv("SECONDARY_PRIMARY_MODEL", "claude-3-5-sonnet-20241022")
        self.secondary_secondary = os.getenv("SECONDARY_SECONDARY_MODEL", "claude-3-haiku-20240307")

        # Model parameters
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.7"))
        self.default_max_tokens = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))

    def get_provider_choices(self) -> List[str]:
        """Get list of available provider choices for UI."""
        return [self.default_provider, self.secondary_provider]

    def get_model_options(self) -> List[ModelOption]:
        """Get all model options organized by provider."""
        return [
            ModelOption(
                provider=self.default_provider,
                model_name=self.default_primary,
                display_name=f"{self.default_provider}: {self._get_display_name(self.default_primary)}",
                description="Primary model (recommended)"
            ),
            ModelOption(
                provider=self.default_provider,
                model_name=self.default_secondary,
                display_name=f"{self.default_provider}: {self._get_display_name(self.default_secondary)}",
                description="Secondary model (faster/cheaper)"
            ),
            ModelOption(
                provider=self.secondary_provider,
                model_name=self.secondary_primary,
                display_name=f"{self.secondary_provider}: {self._get_display_name(self.secondary_primary)}",
                description="Direct API primary"
            ),
            ModelOption(
                provider=self.secondary_provider,
                model_name=self.secondary_secondary,
                display_name=f"{self.secondary_provider}: {self._get_display_name(self.secondary_secondary)}",
                description="Direct API secondary"
            ),
        ]

    def get_model_choices_for_ui(self) -> Tuple[List[str], str]:
        """Get model choices formatted for Gradio dropdown."""
        options = self.get_model_options()
        choices = [opt.display_name for opt in options]
        default = choices[0]  # First option as default
        return choices, default

    def get_provider_choices_for_ui(self) -> Tuple[List[str], str]:
        """Get provider choices formatted for Gradio dropdown."""
        choices = self.get_provider_choices()
        default = choices[0]  # First provider as default
        return choices, default

    def parse_model_selection(self, display_name: str) -> Tuple[str, str]:
        """Parse a display name back to provider and model."""
        options = self.get_model_options()
        for opt in options:
            if opt.display_name == display_name:
                return opt.provider, opt.model_name

        # Fallback to default
        return self.default_provider, self.default_primary

    def get_default_model_config(self) -> Dict[str, any]:
        """Get default model configuration."""
        return {
            "provider": self.default_provider,
            "model_name": self.default_primary,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
        }

    def _get_display_name(self, model_name: str) -> str:
        """Convert model name to user-friendly display name."""
        # Remove provider prefix if present
        if "/" in model_name:
            return model_name.split("/", 1)[1]
        return model_name

    def get_models_by_provider(self, provider: str) -> List[str]:
        """Get all models available for a specific provider."""
        options = self.get_model_options()
        return [opt.model_name for opt in options if opt.provider == provider]


# Global instance
model_config_service = ModelConfigService()