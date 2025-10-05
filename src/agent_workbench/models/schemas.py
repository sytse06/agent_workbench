"""Pydantic schemas for Agent Workbench API."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ModelConfig(BaseModel):
    """Configuration for LLM model parameters.

    Comprehensive model configuration with validation for all supported
    providers. Includes sampling parameters, system prompts, and
    provider-specific extensions.

    Attributes:
        provider: Provider name (openrouter, ollama, openai, anthropic, etc.)
        model_name: Specific model identifier (may include provider prefix)
        temperature: Sampling temperature (0.0=deterministic, 2.0=creative)
        max_tokens: Maximum tokens to generate
        top_p: Nucleus sampling parameter
        frequency_penalty: Penalty for token frequency
        system_prompt: Optional system prompt
        streaming: Whether to stream responses
        extra_params: Provider-specific additional parameters

    Validation:
        - Provider must be in allowed list
        - Model name cannot be empty
        - Temperature and top_p cannot both enforce determinism
        - All numeric parameters have range constraints

    Examples:
        >>> config = ModelConfig(
        ...     provider="anthropic",
        ...     model_name="claude-3.5-sonnet",
        ...     temperature=0.7,
        ...     max_tokens=2000
        ... )
    """

    provider: str = Field(
        ...,
        description="Provider name (openrouter, ollama, openai, anthropic, mistral, google)",
        examples=["openrouter", "anthropic", "ollama", "openai", "mistral"],
    )
    model_name: str = Field(
        ...,
        description="Specific model name for the provider",
        examples=[
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "llama3.1:8b",
            "google/gemini-pro",
        ],
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature",
        examples=[0.3, 0.7, 1.0],
    )
    max_tokens: int = Field(
        default=1000,
        gt=0,
        le=100000,
        description="Maximum tokens to generate",
        examples=[1000, 2000, 4000],
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Top-p sampling parameter",
        examples=[0.9, 0.95, 1.0],
    )
    frequency_penalty: float = Field(
        default=0.0,
        ge=-2.0,
        le=2.0,
        description="Frequency penalty",
        examples=[0.0, 0.5, 1.0],
    )
    system_prompt: Optional[str] = Field(
        None,
        description="System prompt to use",
        examples=["You are a helpful assistant.", "You are an expert Python programmer."],
    )
    streaming: bool = Field(
        default=True,
        description="Whether to use streaming responses",
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific parameters",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "provider": "anthropic",
                "model_name": "claude-3.5-sonnet",
                "temperature": 0.7,
                "max_tokens": 2000,
                "streaming": True,
            }
        }
    )

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Validate that provider is in the allowed list."""
        allowed_providers = {
            "openrouter",
            "ollama",
            "openai",
            "anthropic",
            "mistral",
            "google",
        }
        if v.lower() not in allowed_providers:
            raise ValueError(
                f"Provider '{v}' not supported. Must be one of: {', '.join(sorted(allowed_providers))}"
            )
        return v.lower()

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v: str) -> str:
        """Validate model name format."""
        if not v or not v.strip():
            raise ValueError("Model name cannot be empty")

        # For providers that use format "provider/model"
        if "/" in v:
            parts = v.split("/")
            if len(parts) != 2:
                raise ValueError(
                    "Model name with '/' must have format 'provider/model' (e.g., 'anthropic/claude-3.5-sonnet')"
                )
            if not all(part.strip() for part in parts):
                raise ValueError("Model name parts cannot be empty")

        return v.strip()

    @model_validator(mode="after")
    def validate_sampling_params(self) -> "ModelConfig":
        """Validate that sampling parameters are compatible."""
        # Warn about contradictory sampling settings
        # (temperature=0 means deterministic, but top_p<1 adds randomness)
        if self.temperature == 0.0 and self.top_p < 1.0:
            raise ValueError(
                "Contradictory sampling: temperature=0.0 (deterministic) conflicts with top_p<1.0 (random). "
                "Either use temperature>0 or set top_p=1.0"
            )

        return self


# === Database Model Schemas ===


class ConversationSchema(BaseModel):
    """Unified conversation schema for all CRUD operations."""

    # Optional fields for different operations
    id: Optional[UUID] = Field(
        None,
        description="Conversation ID (auto-generated)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_id: Optional[UUID] = Field(
        None,
        description="User ID who owns the conversation",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Conversation title",
        examples=["Debug Session", "Code Review", "Feature Implementation"],
    )
    llm_config: Optional[ModelConfig] = Field(
        None,
        description="LLM configuration for conversation",
    )

    # Database timestamps (only present in DB/response operations)
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp",
        examples=["2025-01-05T12:00:00Z"],
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp",
        examples=["2025-01-05T12:30:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "React Performance Debugging",
                "created_at": "2025-01-05T12:00:00Z",
                "updated_at": "2025-01-05T12:30:00Z",
            }
        },
    )

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
    id: Optional[UUID] = Field(
        None,
        description="Message ID (auto-generated)",
        examples=["650e8400-e29b-41d4-a716-446655440001"],
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Parent conversation ID",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    role: Optional[str] = Field(
        None,
        pattern=r"^(user|assistant|tool|system)$",
        description="Message role",
        examples=["user", "assistant", "system"],
    )
    content: Optional[str] = Field(
        None,
        description="Message content",
        examples=[
            "How do I implement a binary search tree?",
            "Here's an implementation of a binary search tree...",
        ],
    )
    metadata_: Optional[Dict[str, Any]] = Field(
        None,
        alias="metadata",
        description="Message metadata",
        examples=[{"source": "api", "version": "1.0"}],
    )

    # Database timestamps
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp",
        examples=["2025-01-05T12:01:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "650e8400-e29b-41d4-a716-446655440001",
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "user",
                "content": "How do I implement a binary search tree in Python?",
                "created_at": "2025-01-05T12:01:00Z",
            }
        },
    )

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
    id: Optional[UUID] = Field(
        None,
        description="Agent config ID (auto-generated)",
        examples=["750e8400-e29b-41d4-a716-446655440002"],
    )
    name: Optional[str] = Field(
        None,
        max_length=255,
        description="Configuration name",
        examples=["Code Reviewer", "SEO Analyzer", "Debug Assistant"],
    )
    description: Optional[str] = Field(
        None,
        description="Configuration description",
        examples=["Configuration for automated code review agent"],
    )
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration data",
        examples=[{"max_iterations": 5, "tools": ["git", "linter"]}],
    )

    # Database timestamps
    created_at: Optional[datetime] = Field(
        None,
        description="Creation timestamp",
        examples=["2025-01-05T10:00:00Z"],
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp",
        examples=["2025-01-05T11:00:00Z"],
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "750e8400-e29b-41d4-a716-446655440002",
                "name": "Code Reviewer",
                "description": "Automated code review agent configuration",
                "config": {"max_iterations": 5, "tools": ["git", "linter", "test_runner"]},
                "created_at": "2025-01-05T10:00:00Z",
                "updated_at": "2025-01-05T11:00:00Z",
            }
        },
    )

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
