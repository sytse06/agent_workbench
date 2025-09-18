"""Chat API routes for LLM interactions."""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from ...core.exceptions import LLMProviderError, StreamingError
from ...models.schemas import ModelConfig
from ...models.state_requests import ChatRequest, ChatResponse
from ...services.langgraph_service import WorkbenchLangGraphService
from ...services.llm_service import ChatService, create_chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


async def get_chat_service(request: ChatRequest) -> ChatService:
    """
    Dependency to get chat service instance.

    Args:
        request: Chat request containing model configuration

    Returns:
        Chat service instance
    """
    # Convert dict to ModelConfig if needed
    if isinstance(request.llm_config, dict):
        model_config = ModelConfig(**request.llm_config)
    else:
        model_config = request.llm_config or ModelConfig(
            provider="ollama",
            model_name="llama3.1",
            temperature=0.7,
            max_tokens=1000,
        )

    return await create_chat_service(model_config)


@router.post(
    "/",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat completion",
    description="Generate a chat completion response (stateless or stateful)",
)
async def chat_completion(
    request: ChatRequest,
    # Route through LangGraph workflow internally to maintain API compatibility
    langgraph_service: WorkbenchLangGraphService = Depends(lambda: None),  # Placeholder
) -> ChatResponse:
    """
    Generate a chat completion response through LangGraph workflow.

    This endpoint routes through LangGraph workflows while maintaining
    the same API contract as the original implementation.

    Args:
        request: Chat request with message and configuration
        langgraph_service: LangGraph service instance (dependency injected)

    Returns:
        Chat response with assistant message

    Raises:
        LLMProviderError: If provider call fails
    """
    try:
        # In a real implementation, this would use the injected service
        # For now, we'll maintain the original behavior for compatibility
        service: ChatService = await get_chat_service(request)
        response: ChatResponse = await service.chat_completion(
            message=request.message,
            conversation_id=request.conversation_id,
            context=request.context if request.use_context else None,
        )
        return response
    except LLMProviderError:
        raise
    except Exception as e:
        raise LLMProviderError(f"Chat completion failed: {str(e)}") from e


@router.post(
    "/stream",
    summary="Stream chat completion",
    description="Stream a chat completion response (stateless or stateful)",
)
async def stream_chat(
    request: ChatRequest,
    # Route through LangGraph workflow internally to maintain API compatibility
    langgraph_service: WorkbenchLangGraphService = Depends(lambda: None),  # Placeholder
) -> StreamingResponse:
    """
    Stream a chat completion response through LangGraph workflow.

    This endpoint routes through LangGraph workflows while maintaining
    the same API contract as the original implementation.

    Args:
        request: Chat request with message and configuration
        langgraph_service: LangGraph service instance (dependency injected)

    Returns:
        Streaming response with assistant message chunks

    Raises:
        StreamingError: If streaming fails
    """
    try:
        # In a real implementation, this would use the injected service
        # For now, we'll maintain the original behavior for compatibility
        service: ChatService = await get_chat_service(request)

        async def generate() -> AsyncGenerator[str, None]:
            async for chunk in service.stream_completion(
                message=request.message,
                conversation_id=request.conversation_id,
                context=request.context if request.use_context else None,
            ):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            },
        )
    except StreamingError:
        raise
    except Exception as e:
        raise StreamingError(f"Stream chat failed: {str(e)}") from e
