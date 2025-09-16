"""Context management API routes."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...models.state_requests import ContextUpdateRequest
from ...services.context_service import ContextService

router = APIRouter(prefix="/api/v1/conversations", tags=["context"])


# Note: In a full implementation, this would use dependency injection
# for the ContextService instance
def get_context_service():
    """Get context service instance."""
    # This would typically be injected via DI
    return ContextService()


@router.put(
    "/{conversation_id}/context",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update conversation context",
    description="Update the context data for a conversation",
)
async def update_conversation_context(
    conversation_id: UUID,
    request: ContextUpdateRequest,
    service: ContextService = Depends(get_context_service),
):
    """
    Update conversation context data.

    Args:
        conversation_id: Conversation ID
        request: Context update request
        service: Context service instance
    """
    try:
        await service.update_conversation_context(
            conversation_id=conversation_id,
            context_data=request.context_data,
            sources=request.sources,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update context: {str(e)}",
        ) from e


@router.delete(
    "/{conversation_id}/context",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear conversation context",
    description="Clear context data for a conversation",
)
async def clear_conversation_context(
    conversation_id: UUID,
    source: Optional[str] = None,
    service: ContextService = Depends(get_context_service),
):
    """
    Clear conversation context data.

    Args:
        conversation_id: Conversation ID
        source: Specific source to clear (None = clear all)
        service: Context service instance
    """
    try:
        await service.clear_conversation_context(
            conversation_id=conversation_id,
            source=source,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear context: {str(e)}",
        ) from e


@router.get(
    "/{conversation_id}/context",
    response_model=List[str],
    summary="Get active contexts",
    description="Get active context sources for a conversation",
)
async def get_conversation_context(
    conversation_id: UUID,
    service: ContextService = Depends(get_context_service),
):
    """
    Get active context sources for conversation.

    Args:
        conversation_id: Conversation ID
        service: Context service instance

    Returns:
        List of active context sources
    """
    try:
        return await service.get_active_contexts(conversation_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get context: {str(e)}",
        ) from e
