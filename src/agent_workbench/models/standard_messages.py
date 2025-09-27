"""Standard message format for state management."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    pass
else:
    # Import at runtime to avoid circular imports
    try:
        from .schemas import ModelConfig
    except ImportError:
        ModelConfig = None


class StandardMessage(BaseModel):
    """Standard message format for storage portability."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ConversationState(BaseModel):
    """State representation for conversations."""

    conversation_id: UUID
    messages: List[StandardMessage]
    llm_config: Any  # Use Any to avoid forward reference issues
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime
