"""Simple LLM chat endpoints using minimal LangGraph workflow.

Maintains PRD's "All through LangGraph" architecture while providing
lightweight chat functionality for testing and debugging.
"""

import logging
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.schemas import ModelConfig
from ...services.agent_service import AgentService
from ...services.llm_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["simple_chat"])


class SimpleChatRequest(BaseModel):
    """Simple chat request using minimal LangGraph workflow."""

    message: str
    provider: str = "openrouter"
    model_name: str = "anthropic/claude-3.5-sonnet"
    temperature: float = 0.7
    max_tokens: int = 2000
    streaming: bool = False


class SimpleChatResponse(BaseModel):
    """Simple chat response from minimal workflow."""

    content: str
    conversation_id: str
    model_used: str
    provider_used: str
    latency_ms: Optional[float] = None
    status: str = "success"
    workflow_steps: list[str] = ["process_input", "generate_response"]


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


@router.post("/simple", response_model=SimpleChatResponse)
async def simple_chat(request: SimpleChatRequest) -> SimpleChatResponse:
    """
    Simple LLM chat using minimal LangGraph workflow.

    This endpoint provides a lightweight 2-node workflow:
    1. process_input: Validate user message
    2. generate_response: Get LLM response

    Maintains PRD's "All through LangGraph" architecture while providing
    the lightweight functionality needed for testing/debugging.

    Essential for:
    - Production model testing
    - API debugging
    - Provider validation
    - Quick LLM checks without full workflow complexity
    """
    logger.info("=" * 80)
    logger.info("🚀 SIMPLE CHAT REQUEST RECEIVED")
    logger.info(f"📝 Message: {request.message[:100]}...")
    logger.info(f"🔧 Provider: {request.provider}")
    logger.info(f"🤖 Model: {request.model_name}")
    logger.info(f"🌡️  Temperature: {request.temperature}")
    logger.info(f"📊 Max tokens: {request.max_tokens}")
    logger.info("=" * 80)

    try:
        logger.info("🔧 Creating model configuration...")
        # Create model configuration
        model_config = ModelConfig(
            provider=request.provider,
            model_name=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            streaming=request.streaming,
        )
        logger.info(f"✅ Model config created: {model_config}")

        logger.info("🔧 Initializing AgentService...")
        agent = AgentService(model_config)
        logger.info("✅ AgentService initialized")

        import time

        start_time = time.time()
        logger.info("🤖 Executing agent...")

        response = await agent.run(
            messages=[{"role": "user", "content": request.message}]
        )

        latency_ms = (time.time() - start_time) * 1000
        logger.info(f"✅ Agent completed in {latency_ms:.0f}ms")

        logger.info(f"📝 Response preview: {response.message[:100]}...")

        result = SimpleChatResponse(
            content=response.message,
            conversation_id=str(uuid4()),
            model_used=request.model_name,
            provider_used=request.provider,
            latency_ms=latency_ms,
            status="success",
            workflow_steps=["agent_run"],
        )
        logger.info("✅ SimpleChatResponse created successfully")
        logger.info("=" * 80)
        return result

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error("=" * 80)
        logger.error(f"❌ SIMPLE CHAT FAILED: {str(e)}")
        logger.error(f"❌ Exception type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Traceback:\n{traceback.format_exc()}")
        logger.error("=" * 80)
        raise HTTPException(status_code=500, detail=f"Simple chat failed: {str(e)}")


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
    api_key_source = "environment_variable"
    try:
        # Create model configuration
        model_config = ModelConfig(
            provider=request.provider,
            model_name=request.model_name,
            temperature=0.7,
            max_tokens=100,
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
            message=request.test_message, conversation_id=None
        )

        latency_ms = (time.time() - start_time) * 1000

        return ModelTestResponse(
            status="success",
            provider=request.provider,
            model=request.model_name,
            response_length=len(response.message),
            latency_ms=latency_ms,
            api_key_source=api_key_source,
        )

    except Exception as e:
        logger.error(f"Model test failed: {str(e)}")
        return ModelTestResponse(
            status="failed",
            provider=request.provider,
            model=request.model_name,
            error=str(e),
            api_key_source=api_key_source,
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
            "supported": True,  # Could add actual availability check
        }

    return {
        "providers": providers,
        "default_provider": "openrouter",
        "default_model": "anthropic/claude-3.5-sonnet",
    }


@router.get("/health")
async def simple_chat_health():
    """Health check for simple chat functionality."""
    return {
        "status": "healthy",
        "service": "simple_chat",
        "endpoints": ["/simple", "/test-model", "/providers", "/health"],
        "description": "Simple LLM chat using minimal 2-node LangGraph workflow",
        "architecture": "LangGraph-based (maintains PRD compliance)",
    }
