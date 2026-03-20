"""Thread management API routes."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.api.database import get_session
from agent_workbench.models.database import ThreadMetadata
from agent_workbench.models.schemas import ThreadSummary

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
