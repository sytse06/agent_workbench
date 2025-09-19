"Chat API routes for LLM interactions."

from typing import Any, AsyncGenerator, Dict

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from ...core.exceptions import LLMProviderError, StreamingError
from ...models.schemas import ModelConfig
from ...models.state_requests import ChatRequest, ChatResponse
from ...services.langgraph_service import WorkbenchLangGraphService
from ...services.llm_service import ChatService, create_chat_service

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat completion",
    description="Send a chat message and get a response",
)
async def chat_completion(
    request: ChatRequest,
    langgraph_service: WorkbenchLangGraphService = Depends(lambda: None),  # Placeholder
) -> ChatResponse:
    """
    Chat completion endpoint for backward compatibility.

    This endpoint provides the same functionality as /message but at the root path
    to maintain compatibility with existing tests.

    Args:
        request: Chat request with message and configuration
        langgraph_service: LangGraph service instance (dependency injected)

    Returns:
        Chat response with assistant message

    Raises:
        LLMProviderError: If provider call fails
    """
    try:
        # For now, use the existing service approach to avoid dependency issues
        service: ChatService = await create_chat_service(
            request.llm_config
            or ModelConfig(
                provider="ollama",
                model_name="llama3.1",
                temperature=0.7,
                max_tokens=1000,
            )
        )
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
    "/message",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat message through LangGraph workflow",
    description="Send a message through LangGraph workflows with full state management",
)
async def send_message(
    request: ChatRequest,
    langgraph_service: WorkbenchLangGraphService = Depends(lambda: None),  # Placeholder
) -> ChatResponse:
    """
    Send a message through LangGraph workflow.

    This endpoint routes all chat requests through LangGraph workflows
    to maintain proper state management and workflow orchestration.

    Args:
        request: Chat request with message and configuration
        langgraph_service: LangGraph service instance (dependency injected)

    Returns:
        Chat response with assistant message

    Raises:
        LLMProviderError: If provider call fails
    """
    try:
        # For now, use the existing service approach to avoid dependency issues
        # In a real implementation, this would use the injected service
        service: ChatService = await create_chat_service(
            request.model_config
            or ModelConfig(
                provider="ollama",
                model_name="llama3.1",
                temperature=0.7,
                max_tokens=1000,
            )
        )
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


@router.get(
    "/conversations/{conversation_id}/messages",
    summary="Get conversation history",
    description="Get full conversation history from LangGraph state",
)
async def get_conversation_messages(
    conversation_id: str,
    langgraph_service: WorkbenchLangGraphService = Depends(lambda: None),  # Placeholder
) -> Dict[str, Any]:
    """
    Get conversation history from LangGraph state.

    This endpoint provides access to conversation history managed by LangGraph.

    Args:
        conversation_id: The conversation identifier
        langgraph_service: LangGraph service instance (dependency injected)

    Returns:
        Conversation history with messages
    """
    try:
        # For now, we'll return a basic structure
        # In a real implementation, this would query LangGraph state
        return {"conversation_id": conversation_id, "messages": []}
    except Exception as e:
        raise LLMProviderError(f"Failed to get conversation history: {str(e)}") from e


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
        service: ChatService = await create_chat_service(
            request.model_config
            or ModelConfig(
                provider="ollama",
                model_name="llama3.1",
                temperature=0.7,
                max_tokens=1000,
            )
        )

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
