"""State management request models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas import ModelConfig


class ChatRequest(BaseModel):
    """Enhanced chat request with state management support."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[UUID] = Field(
        None, description="Existing conversation ID (None = stateless)"
    )
    llm_config: Optional[ModelConfig] = Field(
        None, description="Override conversation model configuration"
    )
    use_context: bool = Field(True, description="Whether to use context injection")
    temperature: Optional[float] = Field(
        None, ge=0.0, le=2.0, description="Override temperature"
    )
    max_tokens: Optional[int] = Field(
        None, gt=0, le=100000, description="Override max tokens"
    )
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional context data to inject"
    )

    model_config = ConfigDict(populate_by_name=True)


class ChatResponse(BaseModel):
    """Enhanced chat response with state management information."""

    content: str = Field(..., description="Assistant response content")
    conversation_id: Optional[UUID] = Field(
        None, description="Conversation ID (None for stateless)"
    )
    message_count: Optional[int] = Field(None, description="Position in conversation")
    model_used: str = Field(..., description="Model identifier used")
    is_temporary: Optional[bool] = Field(
        None, description="Whether this is a temporary conversation"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional response metadata"
    )
    llm_config: Optional[ModelConfig] = Field(
        None, description="Model configuration used"
    )


class ContextUpdateRequest(BaseModel):
    """Request to update conversation context."""

    context_data: Dict[str, Any] = Field(..., description="Context data to inject")
    sources: List[str] = Field(
        default_factory=list, description="Context source tracking"
    )


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: Optional[str] = Field(None, description="Conversation title")
    llm_config: Optional[ModelConfig] = Field(
        None, description="Model configuration for conversation"
    )
    is_temporary: bool = Field(
        False, description="Whether this is a temporary conversation"
    )

    model_config = ConfigDict(populate_by_name=True)


class ConversationSummary(BaseModel):
    """Summary information about a conversation."""

    id: UUID
    title: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    model_config_field: Optional[ModelConfig] = None
    active_contexts: List[str]
    is_temporary: bool
