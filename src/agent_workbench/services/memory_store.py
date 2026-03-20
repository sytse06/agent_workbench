"""Long-term memory store — module-level AsyncSqliteStore singleton."""

import logging
import os
from typing import Optional

import aiosqlite
from langgraph.store.base import BaseStore
from langgraph.store.sqlite.aio import AsyncSqliteStore

logger = logging.getLogger(__name__)

_store: Optional[BaseStore] = None
_store_conn: Optional[aiosqlite.Connection] = None


async def init_store(db_path: str = "data/langgraph_store.db") -> None:
    """Open AsyncSqliteStore at app startup. Call from FastAPI lifespan."""
    global _store, _store_conn
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    _store_conn = await aiosqlite.connect(db_path)
    store = AsyncSqliteStore(_store_conn)
    await store.setup()
    _store = store
    logger.info("LangGraph AsyncSqliteStore initialized at %s", db_path)


async def close_store() -> None:
    """Close the store connection at app shutdown."""
    global _store_conn
    if _store_conn is not None:
        await _store_conn.close()
        _store_conn = None
        logger.info("LangGraph store connection closed")


def get_store() -> Optional[BaseStore]:
    """Return the module-level store singleton."""
    return _store


async def read_memory(store: BaseStore, session_id: str, key: str) -> str:
    """Read a memory file. Returns empty string if not found."""
    try:
        item = await store.aget((session_id, "memories"), key)
        if item and item.value:
            return item.value.get("content", "")
    except Exception:
        pass
    return ""
