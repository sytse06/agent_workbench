"""Pydantic schemas for Agent Workbench API."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Configuration for LLM model parameters."""

    provider: str = Field(
        ...,
        description="Provider name (openrouter, ollama, openai, anthropic, mistral)",
    )
    model_name: str = Field(..., description="Specific model name for the provider")
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=1000, gt=0, le=100000, description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Top-p sampling parameter"
    )
    frequency_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    system_prompt: Optional[str] = Field(None, description="System prompt to use")
    streaming: bool = Field(
        default=True, description="Whether to use streaming responses"
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific parameters"
    )


# === Database Model Schemas ===


class ConversationSchema(BaseModel):
    """Unified conversation schema for all CRUD operations."""

    # Optional fields for different operations
    id: Optional[UUID] = Field(None, description="Conversation ID (auto-generated)")
    user_id: Optional[UUID] = Field(
        None, description="User ID who owns the conversation"
    )
    title: Optional[str] = Field(None, max_length=255, description="Conversation title")
    llm_config: Optional[ModelConfig] = Field(
        None, description="LLM configuration for conversation"
    )

    # Database timestamps (only present in DB/response operations)
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def for_create(cls, **kwargs) -> "ConversationSchema":
        """Create schema for conversation creation (excludes id, timestamps)."""
        excluded_fields = {"id", "created_at", "updated_at"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        return cls(**filtered_kwargs)

    @classmethod
    def for_update(cls, **kwargs) -> "ConversationSchema":
        """Create schema for conversation updates (excludes id, created_at)."""
        excluded_fields = {"id", "created_at"}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in excluded_fields}
        # For updates, all fields are optional
        return cls(**{k: v for k, v in filtered_kwargs.items() if v is not None})

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return self.model_dump(exclude_none=True, exclude={"id", "llm_config"})

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return self.model_dump(exclude_none=True)


# Backwards compatibility aliases - these will be removed in next phase
ConversationBase = ConversationSchema
ConversationCreate = ConversationSchema
ConversationUpdate = ConversationSchema
ConversationInDB = ConversationSchema
ConversationResponse = ConversationSchema


class MessageSchema(BaseModel):
    """Unified message schema for all CRUD operations."""

    # Optional fields for different operations
    id: Optional[UUID] = Field(None, description="Message ID (auto-generated)")
    conversation_id: Optional[UUID] = Field(None, description="Parent conversation ID")
    role: Optional[str] = Field(
        None, pattern=r"^(user|assistant|tool|system)$", description="Message role"
    )
    content: Optional[str] = Field(None, description="Message content")
    metadata_: Optional[Dict[str, Any]] = Field(
        None, alias="metadata", description="Message metadata"
    )

    # Database timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def for_create(
        cls,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> "MessageSchema":
        """Create schema for message creation with required fields."""
        return cls(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata,
        )

    @classmethod
    def for_update(cls, **kwargs) -> "MessageSchema":
        """Create schema for message updates (content and metadata only)."""
        allowed_fields = {"content", "metadata_"}
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k in allowed_fields and v is not None
        }
        return cls(**filtered_kwargs)

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return self.model_dump(exclude_none=True, exclude={"id", "created_at"})

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return self.model_dump(exclude_none=True)


# Backwards compatibility aliases - these will be removed in next phase
MessageBase = MessageSchema
MessageCreate = MessageSchema
MessageUpdate = MessageSchema
MessageInDB = MessageSchema
MessageResponse = MessageSchema


class AgentConfigSchema(BaseModel):
    """Unified agent configuration schema for all CRUD operations."""

    # Optional fields for different operations
    id: Optional[UUID] = Field(None, description="Agent config ID (auto-generated)")
    name: Optional[str] = Field(None, max_length=255, description="Configuration name")
    description: Optional[str] = Field(None, description="Configuration description")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration data")

    # Database timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True

    @classmethod
    def for_create(
        cls, name: str, config: Dict[str, Any], description: Optional[str] = None
    ) -> "AgentConfigSchema":
        """Create schema for agent config creation with required fields."""
        return cls(name=name, description=description, config=config)

    @classmethod
    def for_update(cls, **kwargs) -> "AgentConfigSchema":
        """Create schema for agent config updates (all fields optional)."""
        allowed_fields = {"name", "description", "config"}
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k in allowed_fields and v is not None
        }
        return cls(**filtered_kwargs)

    def to_db_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for database operations."""
        return self.model_dump(
            exclude_none=True, exclude={"id", "created_at", "updated_at"}
        )

    def to_response_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return self.model_dump(exclude_none=True)


# Backwards compatibility aliases - these will be removed in next phase
AgentConfigBase = AgentConfigSchema
AgentConfigCreate = AgentConfigSchema
AgentConfigUpdate = AgentConfigSchema
AgentConfigInDB = AgentConfigSchema
AgentConfigResponse = AgentConfigSchema


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


class ConversationSummary(BaseModel):
    """Summary information about a conversation."""

    id: UUID
    title: str
    created_at: datetime
    message_count: int
    llm_config: Optional[ModelConfig] = None
