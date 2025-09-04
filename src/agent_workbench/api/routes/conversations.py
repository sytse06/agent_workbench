"""Conversation API routes for Agent Workbench."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import get_session
from agent_workbench.api.exceptions import ConversationNotFoundError
from agent_workbench.models.database import ConversationModel
from agent_workbench.models.schemas import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


@router.post(
    "/",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create conversation",
    description="Create a new conversation",
)
async def create_conversation(
    request: ConversationCreate, session: AsyncSession = Depends(get_session)
) -> ConversationResponse:
    """Create a new conversation."""
    conversation = await ConversationModel.create(session, **request.model_dump())
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Get conversation",
    description="Get a conversation by ID",
)
async def get_conversation(
    conversation_id: UUID, session: AsyncSession = Depends(get_session)
) -> ConversationResponse:
    """Get conversation by ID."""
    conversation = await ConversationModel.get_by_id(session, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(str(conversation_id))
    return ConversationResponse.model_validate(conversation)


@router.get(
    "/",
    response_model=List[ConversationResponse],
    summary="List conversations",
    description="List all conversations, optionally filtered by user ID",
)
async def list_conversations(
    user_id: Optional[UUID] = None, session: AsyncSession = Depends(get_session)
) -> List[ConversationResponse]:
    """List conversations."""
    if user_id:
        conversations = await ConversationModel.get_by_user(session, user_id)
    else:
        result = await session.execute(ConversationModel.__table__.select())
        conversations = list(result.scalars().all())

    return [ConversationResponse.model_validate(conv) for conv in conversations]


@router.put(
    "/{conversation_id}",
    response_model=ConversationResponse,
    summary="Update conversation",
    description="Update a conversation by ID",
)
async def update_conversation(
    conversation_id: UUID,
    request: ConversationUpdate,
    session: AsyncSession = Depends(get_session),
) -> ConversationResponse:
    """Update conversation."""
    conversation = await ConversationModel.get_by_id(session, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(str(conversation_id))

    updated_conversation = await conversation.update(
        session, **request.model_dump(exclude_unset=True)
    )
    return ConversationResponse.model_validate(updated_conversation)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation",
    description="Delete a conversation by ID",
)
async def delete_conversation(
    conversation_id: UUID, session: AsyncSession = Depends(get_session)
) -> None:
    """Delete conversation."""
    conversation = await ConversationModel.get_by_id(session, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(str(conversation_id))

    await conversation.delete(session)
