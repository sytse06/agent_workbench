"""LiteLLM service for HuggingFace Spaces deployment with OpenRouter integration."""

import logging
import os
from typing import Any, Dict, List, Optional

try:
    import litellm
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False

from ..core.exceptions import LLMProviderError

logger = logging.getLogger(__name__)


class LiteLLMService:
    """Service for LiteLLM-based chat completions via OpenRouter for production HF Spaces."""

    def __init__(self, model: str = "openai/gpt-3.5-turbo"):
        """
        Initialize LiteLLM service with OpenRouter.

        Args:
            model: Model name in OpenRouter format (e.g., "openai/gpt-3.5-turbo", "anthropic/claude-3-haiku")
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is not installed. Run: pip install litellm")

        self.model = model
        self._setup_openrouter()

    def _setup_openrouter(self) -> None:
        """Setup OpenRouter API configuration."""
        openrouter_key = os.getenv('OPENROUTER_API_KEY')

        if openrouter_key:
            # Configure LiteLLM for OpenRouter
            os.environ['OPENROUTER_API_KEY'] = openrouter_key
            # Set OpenRouter as base URL for all calls
            litellm.api_base = "https://openrouter.ai/api/v1"
            logger.info("✅ OpenRouter API configured for LiteLLM")
        else:
            logger.warning("⚠️ OPENROUTER_API_KEY not found in environment variables")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate chat completion using LiteLLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional parameters for the model

        Returns:
            Chat completion response
        """
        try:
            # Use OpenRouter format for model names
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                stream=stream,
                api_base="https://openrouter.ai/api/v1",
                **kwargs
            )

            if stream:
                return response
            else:
                return {
                    "content": response.choices[0].message.content,
                    "model": response.model,
                    "usage": response.usage.dict() if response.usage else None
                }

        except Exception as e:
            logger.error(f"OpenRouter/LiteLLM completion error: {e}")
            raise LLMProviderError(f"Chat completion failed: {str(e)}")

    def get_available_models(self) -> List[str]:
        """Get list of popular OpenRouter models."""
        # Popular OpenRouter models - all accessible with single API key
        return [
            # OpenAI models
            "openai/gpt-3.5-turbo",
            "openai/gpt-4",
            "openai/gpt-4-turbo",
            # Anthropic models
            "anthropic/claude-3-haiku",
            "anthropic/claude-3-sonnet",
            "anthropic/claude-3-opus",
            # Open source models
            "meta-llama/llama-2-70b-chat",
            "mistralai/mixtral-8x7b-instruct",
            "google/gemma-7b-it",
        ]


# Factory function for OpenRouter integration
def create_litellm_service(model: Optional[str] = None) -> LiteLLMService:
    """
    Create LiteLLM service with OpenRouter integration.

    Args:
        model: Specific OpenRouter model to use (e.g., "openai/gpt-3.5-turbo")

    Returns:
        Configured LiteLLM service
    """
    if not model:
        # Default to reliable, fast OpenAI model via OpenRouter
        model = 'openai/gpt-3.5-turbo'

    return LiteLLMService(model=model)