"""Model API routes for LLM provider and model discovery."""

from typing import List

from fastapi import APIRouter, status

from ...services.chat_models import ModelInfo
from ...services.providers import provider_registry

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get(
    "/providers",
    response_model=List[str],
    status_code=status.HTTP_200_OK,
    summary="Get available providers",
    description="Get list of available LLM providers",
)
async def get_providers() -> List[str]:
    """
    Get list of available LLM providers.

    Returns:
        List of provider names
    """
    return provider_registry.get_available_providers()


@router.get(
    "/{provider}",
    response_model=List[ModelInfo],
    status_code=status.HTTP_200_OK,
    summary="Get provider models",
    description="Get list of available models for a specific provider",
)
async def get_provider_models(provider: str) -> List[ModelInfo]:
    """
    Get list of available models for a specific provider.

    Args:
        provider: Provider name

    Returns:
        List of model information
    """
    # Get models from provider registry
    provider_models = provider_registry.get_provider_models(provider)

    # Convert to ModelInfo objects
    model_info_list = []
    for model_data in provider_models:
        model_info_list.append(ModelInfo(**model_data))

    return model_info_list
