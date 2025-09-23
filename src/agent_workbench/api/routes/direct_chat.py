"""Direct LLM chat endpoints bypassing workflow complexity."""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.schemas import ModelConfig
from ...services.llm_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["direct_chat"])


class DirectChatRequest(BaseModel):
    """Direct chat request bypassing all workflows."""

    message: str
    provider: str = "openrouter"
    model_name: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = False


class DirectChatResponse(BaseModel):
    """Direct chat response."""

    content: str
    conversation_id: str
    model_used: str
    provider_used: str
    latency_ms: Optional[float] = None
    status: str = "success"


class ModelTestRequest(BaseModel):
    """Model connectivity test request."""

    provider: str
    model_name: str
    api_key: Optional[str] = None
    test_message: str = "Test connection"


class ModelTestResponse(BaseModel):
    """Model connectivity test response."""

    status: str
    provider: str
    model: str
    response_length: Optional[int] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    api_key_source: str


@router.post("/direct", response_model=DirectChatResponse)
async def direct_chat(request: DirectChatRequest) -> DirectChatResponse:
    """
    Direct LLM chat bypassing all workflow complexity.

    This endpoint provides immediate model response without:
    - LangGraph workflows
    - State management
    - Conversation persistence
    - Context handling

    Essential for production model testing and fallback scenarios.
    """
    try:
        # Create model configuration
        model_config = ModelConfig(
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            streaming=request.streaming
        )

        # Initialize LLM service
        llm_service = ChatService(model_config)

        # Get response
        import time
        start_time = time.time()

        response = await llm_service.chat_completion(
            message=request.message,
            conversation_id=None  # No conversation persistence
        )

        latency_ms = (time.time() - start_time) * 1000

        return DirectChatResponse(
            content=response.content,
            conversation_id=str(uuid4()),
            model_used=request.model_name,
            provider_used=request.provider,
            latency_ms=latency_ms,
            status="success"
        )

    except Exception as e:
        logger.error(f"Direct chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Direct chat failed: {str(e)}"
        )


@router.post("/test-model", response_model=ModelTestResponse)
async def test_model_connectivity(request: ModelTestRequest) -> ModelTestResponse:
    """
    Test model connectivity for production validation.

    Essential for:
    - Production model switching
    - API key validation
    - Provider availability testing
    - Latency benchmarking
    """
    try:
        # Create model configuration
        model_config = ModelConfig(
            provider=request.provider,
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=100
        )

        # Override API key if provided
        if request.api_key:
            model_config.extra_params = {"api_key": request.api_key}
            api_key_source = "request_override"
        else:
            api_key_source = "environment_variable"

        # Initialize LLM service
        llm_service = ChatService(model_config)

        # Test with simple message
        import time
        start_time = time.time()

        response = await llm_service.chat_completion(
            message=request.test_message,
            conversation_id=None
        )

        latency_ms = (time.time() - start_time) * 1000

        return ModelTestResponse(
            status="success",
            provider=request.provider,
            model=request.model_name,
            response_length=len(response.content),
            latency_ms=latency_ms,
            api_key_source=api_key_source
        )

    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        return ModelTestResponse(
            status="failed",
            provider=request.provider,
            model=request.model_name,
            error=str(e),
            api_key_source=api_key_source if 'api_key_source' in locals() else "unknown"
        )


@router.get("/providers")
async def list_available_providers():
    """List all available LLM providers and their default models."""
    from ...services.providers import PROVIDER_FACTORIES

    providers = {}
    for provider_name, factory_class in PROVIDER_FACTORIES.items():
        providers[provider_name] = {
            "name": provider_name,
            "factory_class": factory_class.__name__,
            "supported": True  # Could add actual availability check
        }

    return {
        "providers": providers,
        "default_provider": "openrouter",
        "default_model": "anthropic/claude-3.5-sonnet"
    }


@router.get("/health")
async def direct_chat_health():
    """Health check for direct chat functionality."""
    return {
        "status": "healthy",
        "service": "direct_chat",
        "endpoints": [
            "/direct",
            "/test-model",
            "/providers",
            "/health"
        ],
        "description": "Direct LLM chat bypassing workflow complexity"
    }