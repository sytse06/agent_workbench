"""Pydantic schemas for Agent Workbench API."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field

# === Database Model Schemas ===


class ConversationBase(BaseModel):
    """Base schema for conversation."""

    user_id: Optional[UUID] = None
    title: Optional[str] = Field(None, max_length=255)


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""

    pass


class ConversationUpdate(ConversationBase):
    """Schema for updating a conversation."""

    pass


class ConversationInDB(ConversationBase):
    """Schema for conversation in database."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationResponse(ConversationInDB):
    """Schema for conversation API response."""

    pass


class MessageBase(BaseModel):
    """Base schema for message."""

    conversation_id: UUID
    role: str = Field(..., pattern=r"^(user|assistant|tool|system)$")
    content: str
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class MessageCreate(MessageBase):
    """Schema for creating a message."""

    pass


class MessageUpdate(BaseModel):
    """Schema for updating a message."""

    content: Optional[str] = None
    metadata_: Optional[Dict[str, Any]] = Field(None, alias="metadata")


class MessageInDB(MessageBase):
    """Schema for message in database."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(MessageInDB):
    """Schema for message API response."""

    pass


class AgentConfigBase(BaseModel):
    """Base schema for agent configuration."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    config: Dict[str, Any]


class AgentConfigCreate(AgentConfigBase):
    """Schema for creating an agent configuration."""

    pass


class AgentConfigUpdate(BaseModel):
    """Schema for updating an agent configuration."""

    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class AgentConfigInDB(AgentConfigBase):
    """Schema for agent configuration in database."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentConfigResponse(AgentConfigInDB):
    """Schema for agent configuration API response."""

    pass


# === API Request/Response Schemas ===


class HealthCheckResponse(BaseModel):
    """Schema for health check response."""

    status: str
    database_connected: bool
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str
    error_code: Optional[str] = None
