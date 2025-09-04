"""Message API routes for Agent Workbench."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import get_session
from agent_workbench.api.exceptions import (
    ConversationNotFoundError,
    MessageNotFoundError,
)
from agent_workbench.models.database import ConversationModel, MessageModel
from agent_workbench.models.schemas import MessageCreate, MessageResponse, MessageUpdate

router = APIRouter(prefix="/api/v1/messages", tags=["messages"])


@router.post(
    "/",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create message",
    description="Create a new message",
)
async def create_message(
    request: MessageCreate, session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Create a new message."""
    # Verify conversation exists
    conversation = await ConversationModel.get_by_id(session, request.conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(str(request.conversation_id))

    message = await MessageModel.create(session, **request.model_dump(by_alias=True))
    return MessageResponse.model_validate(message)


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Get message",
    description="Get a message by ID",
)
async def get_message(
    message_id: UUID, session: AsyncSession = Depends(get_session)
) -> MessageResponse:
    """Get message by ID."""
    message = await MessageModel.get_by_id(session, message_id)
    if message is None:
        raise MessageNotFoundError(str(message_id))
    return MessageResponse.model_validate(message)


@router.get(
    "/",
    response_model=List[MessageResponse],
    summary="List messages",
    description="List messages for a conversation",
)
async def list_messages(
    conversation_id: UUID, session: AsyncSession = Depends(get_session)
) -> List[MessageResponse]:
    """List messages for a conversation."""
    # Verify conversation exists
    conversation = await ConversationModel.get_by_id(session, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(str(conversation_id))

    messages = await MessageModel.get_by_conversation(session, conversation_id)
    return [MessageResponse.model_validate(msg) for msg in messages]


@router.put(
    "/{message_id}",
    response_model=MessageResponse,
    summary="Update message",
    description="Update a message by ID",
)
async def update_message(
    message_id: UUID,
    request: MessageUpdate,
    session: AsyncSession = Depends(get_session),
) -> MessageResponse:
    """Update message."""
    message = await MessageModel.get_by_id(session, message_id)
    if message is None:
        raise MessageNotFoundError(str(message_id))

    update_data = request.model_dump(exclude_unset=True, by_alias=True)
    updated_message = await message.update(session, **update_data)
    return MessageResponse.model_validate(updated_message)


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete message",
    description="Delete a message by ID",
)
async def delete_message(
    message_id: UUID, session: AsyncSession = Depends(get_session)
) -> None:
    """Delete message."""
    message = await MessageModel.get_by_id(session, message_id)
    if message is None:
        raise MessageNotFoundError(str(message_id))

    await message.delete(session)
