"""Pydantic models for LLM service configuration and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models.schemas import ModelConfig


class ModelInfo(BaseModel):
    """Information about a specific model."""

    name: str = Field(..., description="Model name")
    display_name: str = Field(..., description="Human-readable model name")
    context_length: int = Field(..., description="Maximum context length in tokens")
    supports_streaming: bool = Field(..., description="Whether streaming is supported")
    supports_tools: bool = Field(..., description="Whether tool calling is supported")


class ChatRequest(BaseModel):
    """Request for chat completion."""

    message: str = Field(..., description="User message")
    conversation_id: Optional[UUID] = Field(
        None, description="Existing conversation ID"
    )
    llm_config: ModelConfig = Field(..., description="Model configuration")


class ChatResponse(BaseModel):
    """Response from chat completion."""

    message: str = Field(..., description="Assistant response")
    conversation_id: UUID = Field(..., description="Conversation ID")
    llm_config: ModelConfig = Field(..., description="Model configuration used")


class ConversationResponse(BaseModel):
    """Full conversation response."""

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    llm_config: Optional[ModelConfig] = None


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""

    title: Optional[str] = None
    llm_config: Optional[ModelConfig] = None

    model_config = ConfigDict(extra="forbid")


class ValidationResult(BaseModel):
    """Result of model configuration validation."""

    is_valid: bool
    errors: List[str] = Field(default_factory=list)
