"""Conversation API routes for LLM chat interactions."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status

from ...models.schemas import ConversationResponse, ConversationSummary
from ...services.chat_models import CreateConversationRequest
from ...services.conversation_service import ConversationService

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


async def get_conversation_service() -> ConversationService:
    """
    Dependency to get conversation service instance.

    Returns:
        Conversation service instance
    """
    return ConversationService()


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation",
)
async def create_conversation(
    request: CreateConversationRequest,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """
    Create a new conversation.

    Args:
        request: Create conversation request
        service: Conversation service instance

    Returns:
        Created conversation response
    """
    conversation_id = await service.create_conversation(
        title=request.title, model_config=request.llm_config
    )
    return await service.get_conversation(conversation_id)


@router.get(
    "/",
    response_model=List[ConversationSummary],
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="Get list of conversations",
)
async def list_conversations(
    limit: int = 50, service: ConversationService = Depends(get_conversation_service)
) -> List[ConversationSummary]:
    """
    Get list of conversations.

    Args:
        limit: Maximum number of conversations to return
        service: Conversation service instance

    Returns:
        List of conversation summaries
    """
    return await service.get_conversations(limit=limit)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation",
    description="Get conversation by ID",
)
async def get_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> ConversationResponse:
    """
    Get conversation by ID.

    Args:
        conversation_id: Conversation ID
        service: Conversation service instance

    Returns:
        Conversation response
    """
    return await service.get_conversation(conversation_id)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete conversation by ID",
)
async def delete_conversation(
    conversation_id: UUID,
    service: ConversationService = Depends(get_conversation_service),
) -> None:
    """
    Delete conversation by ID.

    Args:
        conversation_id: Conversation ID
        service: Conversation service instance
    """
    success = await service.delete_conversation(conversation_id)
    if not success:
        # This would typically raise an exception
        pass
