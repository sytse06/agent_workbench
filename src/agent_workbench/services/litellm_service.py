"""LiteLLM service for HuggingFace Spaces deployment with proper API key management."""

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
    """Service for LiteLLM-based chat completions optimized for HF Spaces."""

    def __init__(self, model: str = "gpt-3.5-turbo"):
        """
        Initialize LiteLLM service.

        Args:
            model: Model name (e.g., "gpt-3.5-turbo", "claude-3-sonnet", etc.)
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is not installed. Run: pip install litellm")

        self.model = model
        self._setup_api_keys()

    def _setup_api_keys(self) -> None:
        """Setup API keys from environment variables."""
        # Set common API keys that might be available in HF Spaces
        api_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'HUGGINGFACE_API_KEY': os.getenv('HUGGINGFACE_API_KEY', os.getenv('HF_TOKEN')),
            'MISTRAL_API_KEY': os.getenv('MISTRAL_API_KEY'),
            'GROQ_API_KEY': os.getenv('GROQ_API_KEY'),
        }

        for key, value in api_keys.items():
            if value:
                os.environ[key] = value
                logger.info(f"✅ {key} configured for LiteLLM")

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
            response = await litellm.acompletion(
                model=self.model,
                messages=messages,
                stream=stream,
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
            logger.error(f"LiteLLM completion error: {e}")
            raise LLMProviderError(f"Chat completion failed: {str(e)}")

    def get_available_models(self) -> List[str]:
        """Get list of available models based on configured API keys."""
        models = []

        if os.getenv('OPENAI_API_KEY'):
            models.extend(['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'])

        if os.getenv('ANTHROPIC_API_KEY'):
            models.extend(['claude-3-sonnet', 'claude-3-haiku', 'claude-3-opus'])

        if os.getenv('MISTRAL_API_KEY'):
            models.extend(['mistral-tiny', 'mistral-small', 'mistral-medium'])

        if os.getenv('GROQ_API_KEY'):
            models.extend(['mixtral-8x7b-32768', 'llama2-70b-4096'])

        return models or ['gpt-3.5-turbo']  # Default fallback


# Factory function for easy integration
def create_litellm_service(model: Optional[str] = None) -> LiteLLMService:
    """
    Create LiteLLM service with automatic model detection.

    Args:
        model: Specific model to use, or auto-detect from available API keys

    Returns:
        Configured LiteLLM service
    """
    if not model:
        # Auto-detect best available model
        if os.getenv('OPENAI_API_KEY'):
            model = 'gpt-3.5-turbo'
        elif os.getenv('ANTHROPIC_API_KEY'):
            model = 'claude-3-haiku'
        elif os.getenv('MISTRAL_API_KEY'):
            model = 'mistral-tiny'
        else:
            model = 'gpt-3.5-turbo'  # Default

    return LiteLLMService(model=model)