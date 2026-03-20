"""Thread management API routes."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import get_session
from agent_workbench.models.database import DocumentModel, ThreadMetadata
from agent_workbench.models.schemas import ThreadMessage, ThreadSummary
from agent_workbench.services.consolidated_service import get_agent_graph

router = APIRouter(prefix="/api/v1/threads", tags=["threads"])


@router.get("/", response_model=List[ThreadSummary])
async def list_threads(
    session: AsyncSession = Depends(get_session),
) -> List[ThreadSummary]:
    """Return all threads ordered by last_updated_at DESC."""
    result = await session.execute(
        select(ThreadMetadata).order_by(ThreadMetadata.last_updated_at.desc())
    )
    rows = result.scalars().all()
    return [
        ThreadSummary(
            thread_id=row.thread_id,
            title=row.title,
            preview=row.preview,
            created_at=row.created_at,
            last_updated_at=row.last_updated_at,
        )
        for row in rows
    ]


@router.get("/{thread_id}/messages", response_model=List[ThreadMessage])
async def get_thread_messages(thread_id: UUID) -> List[ThreadMessage]:
    """Reconstruct message history for a thread from the LangGraph checkpointer."""
    agent_graph = get_agent_graph()
    if agent_graph is None:
        raise HTTPException(status_code=503, detail="Agent service not ready")

    state = await agent_graph.get_state(str(thread_id))
    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    messages = state.values.get("messages", [])
    result: List[ThreadMessage] = []
    for msg in messages:
        role = getattr(msg, "type", None) or getattr(msg, "role", "unknown")
        # LangChain message types: "human" -> "user", "ai" -> "assistant"
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if content:
            result.append(ThreadMessage(role=role, content=content))
    return result


@router.delete("/{thread_id}", status_code=204)
async def delete_thread(
    thread_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete a thread: metadata row + associated documents.

    Note: the LangGraph checkpointer does not expose a delete API in the
    open-source library. The checkpoint entries become orphaned but are
    harmless — they will never appear in GET /threads and cost negligible
    storage.
    """
    # Verify thread exists
    result = await session.execute(
        select(ThreadMetadata).where(ThreadMetadata.thread_id == thread_id)
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Delete documents (conversation_id == thread_id in current schema)
    await session.execute(
        delete(DocumentModel).where(DocumentModel.conversation_id == thread_id)
    )

    # Delete thread metadata
    await session.delete(row)
    await session.commit()
