"""Conversation API routes for LLM chat interactions."""

from typing import Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...models.api_models import (
    ConversationResponse,
    ConversationSummary,
    CreateConversationRequest,
)
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
    description="Create a new conversation (stateful)",
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
    conversation_id = service.create_conversation(
        title=request.title,
        model_config=request.model_config,
        is_temporary=request.is_temporary,
    )
    return service.get_conversation(conversation_id)


@router.get(
    "/",
    response_model=List[ConversationSummary],
    status_code=status.HTTP_200_OK,
    summary="List conversations",
    description="Get list of conversations (stateful)",
)
async def list_conversations(
    limit: int = 50,
    service: ConversationService = Depends(get_conversation_service),
) -> List[ConversationSummary]:
    """
    Get list of conversations.

    Args:
        limit: Maximum number of conversations to return
        service: Conversation service instance

    Returns:
        List of conversation summaries
    """
    return service.get_conversations(limit=limit)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get conversation",
    description="Get conversation by ID (stateful)",
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
    return service.get_conversation(str(conversation_id))


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete conversation by ID (stateful)",
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
    success = service.delete_conversation(str(conversation_id))
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )


# State management endpoints


@router.get(
    "/{conversation_id}/history",
    response_model=List[Dict],
    summary="Get conversation history",
    description="Get complete conversation history (stateful)",
)
async def get_conversation_history(
    conversation_id: UUID,
):
    """
    Get complete conversation history.

    Args:
        conversation_id: Conversation ID

    Returns:
        List of conversation messages
    """
    # This would use StateManager to get history
    # Implementation would be added when database integration is complete
    return []


@router.delete(
    "/{conversation_id}/history",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear conversation history",
    description="Clear conversation history (stateful)",
)
async def clear_conversation_history(
    conversation_id: UUID,
):
    """
    Clear conversation history.

    Args:
        conversation_id: Conversation ID
    """
    # This would use StateManager to clear history
    # Implementation would be added when database integration is complete
    pass


@router.post(
    "/cleanup-temporary",
    status_code=status.HTTP_200_OK,
    summary="Cleanup temporary conversations",
    description="Clean up expired temporary conversations",
)
async def cleanup_temporary_conversations(
    older_than_minutes: int = 60,
):
    """
    Clean up expired temporary conversations.

    Args:
        older_than_minutes: Age threshold in minutes

    Returns:
        Number of conversations cleaned up
    """
    # This would use TemporaryManager to cleanup
    # Implementation would be added when database integration is complete
    return {"cleaned_up": 0}
