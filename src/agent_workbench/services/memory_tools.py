"""UpdateMemoryTool — agent tool to write long-term memory files."""

import logging
from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedStore
from langgraph.store.base import BaseStore

logger = logging.getLogger(__name__)


@tool
async def update_memory(
    key: Annotated[
        str,
        "Memory file to update: 'agents' (behavioral notes: tone, preferences,"
        " corrections) or 'domain_context' (project/domain knowledge: tech stack,"
        " goals, business context).",
    ],
    content: Annotated[
        str,
        "Full new content for the memory file. Replaces existing content"
        " entirely — write the complete updated file.",
    ],
    config: RunnableConfig,
    store: Annotated[BaseStore, InjectedStore()],
) -> str:
    """Update a long-term memory file about this user.

    Use 'agents' to save behavioral preferences, tone corrections, and tool habits.
    Use 'domain_context' to save project context, tech stack, and domain knowledge.
    Call when the user asks to remember something, corrects you, or reveals context.
    """
    if key not in ("agents", "domain_context"):
        return f"Invalid key {key!r}. Use 'agents' or 'domain_context'."
    session_id = (config.get("configurable") or {}).get("session_id", "anonymous")
    await store.aput((session_id, "memories"), key, {"content": content})
    logger.info("Memory updated: key=%r session=%s", key, session_id[:8])
    return f"Memory '{key}' updated."
