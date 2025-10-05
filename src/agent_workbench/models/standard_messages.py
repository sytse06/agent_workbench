"""Standard message format for state management."""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from .schemas import ModelConfig
else:
    # Import at runtime to avoid circular imports
    try:
        from .schemas import ModelConfig
    except ImportError:
        ModelConfig = None


class ToolCall(BaseModel):
    """Structured tool/function call representation."""

    id: str = Field(..., description="Unique identifier for the tool call")
    function: str = Field(..., description="Function name to call")
    arguments: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arguments to pass to the function",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "call_abc123",
                "function": "get_weather",
                "arguments": {"location": "San Francisco", "unit": "celsius"},
            }
        }
    )


class StandardMessage(BaseModel):
    """Standard message format for storage portability."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="Tool/function calls made by the assistant",
    )
    tool_call_id: Optional[str] = Field(
        None,
        description="ID of the tool call this message is responding to",
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional message metadata",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "role": "assistant",
                "content": "Let me check the weather for you.",
                "tool_calls": [
                    {
                        "id": "call_abc123",
                        "function": "get_weather",
                        "arguments": {"location": "San Francisco"},
                    }
                ],
                "timestamp": "2025-01-05T12:00:00Z",
            }
        }
    )


class ConversationState(BaseModel):
    """State representation for conversations."""

    conversation_id: UUID
    messages: List[StandardMessage]
    llm_config: "ModelConfig"  # Proper type with forward reference
    context_data: Dict[str, Any]
    active_contexts: List[str]
    metadata: Dict[str, Any]
    updated_at: datetime
