"""Memory routes — read/write long-term memory files per session."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ...services.memory_store import get_store, read_memory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])


class MemoryWriteRequest(BaseModel):
    session_id: str
    content: str


@router.get("/{key}")
async def get_memory(
    key: str,
    session_id: Optional[str] = Query(default=None),
) -> dict:
    """Read a memory file for the given session."""
    if key not in ("agents", "domain_context"):
        raise HTTPException(status_code=400, detail=f"Invalid key {key!r}")
    if not session_id:
        return {"content": ""}
    store = get_store()
    if store is None:
        return {"content": ""}
    content = await read_memory(store, session_id, key)
    return {"content": content}


@router.put("/{key}", status_code=200)
async def put_memory(key: str, body: MemoryWriteRequest) -> dict:
    """Write a memory file for the given session."""
    if key not in ("agents", "domain_context"):
        raise HTTPException(status_code=400, detail=f"Invalid key {key!r}")
    store = get_store()
    if store is None:
        raise HTTPException(status_code=503, detail="Memory store not available")
    await store.aput((body.session_id, "memories"), key, {"content": body.content})
    return {"status": "ok"}
