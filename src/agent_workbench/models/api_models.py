"""API request and response models - single source of truth."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .schemas import ModelConfig

# ============================================================================
# Chat Models
# ============================================================================


class ChatRequest(BaseModel):
    """Request for chat completion with optional conversation state.

    Used to send messages to the chat API, either creating a new conversation
    or continuing an existing one. Supports model configuration overrides and
    context injection for enhanced responses.

    Examples:
        New conversation:
            >>> request = ChatRequest(
            ...     message="Explain closures in JavaScript",
            ...     llm_config=ModelConfig(
            ...         provider="anthropic", model_name="claude-3.5-sonnet"
            ...     )
            ... )

        Continue existing conversation:
            >>> request = ChatRequest(
            ...     message="Can you give an example?",
            ...     conversation_id=UUID("550e8400-e29b-41d4-a716-446655440000")
            ... )
    """

    message: str = Field(
        ..., description="User message", min_length=1, max_length=10000
    )
    conversation_id: Optional[UUID] = Field(
        None,
        description="Existing conversation ID (None creates new conversation)",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    llm_config: Optional[ModelConfig] = Field(
        None,
        description="Model configuration (None uses conversation default)",
    )
    use_context: bool = Field(
        True,
        description="Whether to inject conversation context",
    )
    temperature: Optional[float] = Field(
        None,
        ge=0.0,
        le=2.0,
        description="Override temperature for this request",
        examples=[0.7, 0.3, 1.0],
    )
    max_tokens: Optional[int] = Field(
        None,
        gt=0,
        le=100000,
        description="Override max tokens for this request",
        examples=[1000, 2000, 4000],
    )
    context: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional context data to inject",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "message": "Explain the concept of closures in JavaScript",
                "conversation_id": None,
                "llm_config": None,
                "use_context": True,
            }
        },
    )


class ChatResponse(BaseModel):
    """Response from chat completion with conversation metadata.

    Contains the assistant's response along with conversation tracking
    information and model usage details. Used to return chat completions
    to API clients.

    Attributes:
        message: The assistant's response text
        conversation_id: UUID of the conversation this message belongs to
        message_count: Position in conversation (1-indexed)
        model_used: Full model identifier (provider/model-name format)
        is_temporary: Whether conversation will be auto-deleted
        metadata: Additional response metadata (e.g., token usage)
        llm_config: Model configuration used for generation

    Examples:
        >>> response = ChatResponse(
        ...     message="A closure is a function that captures...",
        ...     conversation_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        ...     model_used="anthropic/claude-3.5-sonnet",
        ...     message_count=1
        ... )
    """

    message: str = Field(..., description="Assistant response content")
    conversation_id: UUID = Field(
        ...,
        description="Conversation ID for this exchange",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    message_count: Optional[int] = Field(
        None,
        description="Position in conversation (1-indexed)",
        examples=[1, 5, 10],
    )
    model_used: str = Field(
        ...,
        description="Model identifier that generated response",
        examples=[
            "anthropic/claude-3.5-sonnet",
            "openai/gpt-4o",
            "llama3.1:8b",
        ],
    )
    is_temporary: Optional[bool] = Field(
        None,
        description="Whether this is a temporary conversation",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional response metadata",
    )
    llm_config: Optional[ModelConfig] = Field(
        None,
        description="Model configuration used for this response",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": (
                    "A closure is a function that captures variables "
                    "from its outer scope..."
                ),
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "message_count": 1,
                "model_used": "anthropic/claude-3.5-sonnet",
            }
        }
    )


# ============================================================================
# Conversation Models
# ============================================================================


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation.

    Creates a new conversation with optional title and model configuration.
    Conversations can be permanent (stored in database) or temporary
    (auto-deleted after session).

    Examples:
        >>> request = CreateConversationRequest(
        ...     title="Debugging React Performance",
        ...     llm_config=ModelConfig(
        ...         provider="anthropic",
        ...         model_name="claude-3.5-sonnet"
        ...     ),
        ...     is_temporary=False
        ... )
    """

    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Conversation title",
        examples=["JavaScript Closures Discussion", "Debug Session", "Code Review"],
    )
    llm_config: Optional[ModelConfig] = Field(
        None,
        description="Model configuration for conversation",
    )
    is_temporary: bool = Field(
        False,
        description="Whether this is a temporary conversation",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "example": {
                "title": "Debugging React Performance Issue",
                "llm_config": {
                    "provider": "anthropic",
                    "model_name": "claude-3.5-sonnet",
                    "temperature": 0.7,
                },
                "is_temporary": False,
            }
        },
    )


class ConversationResponse(BaseModel):
    """Full conversation with messages.

    Complete conversation object containing all messages and metadata.
    Returned when fetching a specific conversation by ID.

    Attributes:
        id: Conversation UUID
        title: Conversation title
        created_at: Creation timestamp
        updated_at: Last modification timestamp
        messages: List of message dictionaries (role, content, timestamp)
        llm_config: Model configuration for the conversation

    Examples:
        >>> response = ConversationResponse(
        ...     id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        ...     title="Debug Session",
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now(),
        ...     messages=[
        ...         {"role": "user", "content": "Help debug this code"},
        ...         {"role": "assistant", "content": "I'll help you..."}
        ...     ]
        ... )
    """

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[Dict[str, Any]] = Field(default_factory=list)
    llm_config: Optional[ModelConfig] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationSummary(BaseModel):
    """Summary information about a conversation.

    Lightweight conversation representation for list views. Contains
    essential metadata without message content for efficient querying.

    Attributes:
        id: Conversation UUID
        title: Conversation title
        created_at: Creation timestamp
        last_activity: Last message timestamp
        message_count: Total number of messages
        llm_config: Model configuration
        active_contexts: List of active context identifiers
        is_temporary: Whether conversation is temporary

    Examples:
        >>> summary = ConversationSummary(
        ...     id=UUID("550e8400-e29b-41d4-a716-446655440000"),
        ...     title="Debug Session",
        ...     created_at=datetime.now(),
        ...     last_activity=datetime.now(),
        ...     message_count=5,
        ...     active_contexts=["user_preferences"]
        ... )
    """

    id: UUID
    title: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    llm_config: Optional[ModelConfig] = None
    active_contexts: List[str] = Field(default_factory=list)
    is_temporary: bool = False

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Context Models
# ============================================================================


class ContextUpdateRequest(BaseModel):
    """Request to update conversation context.

    Used to inject additional context into conversations for enhanced
    responses. Context can include user preferences, environment state,
    or any other relevant data.

    Examples:
        >>> request = ContextUpdateRequest(
        ...     context_data={
        ...         "current_file": "src/App.tsx",
        ...         "open_files": ["App.tsx", "Button.tsx"]
        ...     },
        ...     sources=["editor_state"]
        ... )
    """

    context_data: Dict[str, Any] = Field(
        ...,
        description="Context data to inject",
        examples=[{"user_preferences": {"theme": "dark"}, "session_data": {}}],
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Context source tracking",
        examples=[["user_input", "system_detection", "api_call"]],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "context_data": {
                    "current_file": "src/components/Button.tsx",
                    "open_files": ["App.tsx", "Button.tsx"],
                },
                "sources": ["editor_state"],
            }
        }
    )


# ============================================================================
# Model Information
# ============================================================================


class ModelInfo(BaseModel):
    """Information about a specific LLM model.

    Provides metadata about available models including capabilities
    and limitations. Used for model selection and validation.

    Attributes:
        name: Full model identifier (provider/model-name format)
        display_name: Human-readable model name for UI
        context_length: Maximum context window in tokens
        supports_streaming: Whether the model supports streaming responses
        supports_tools: Whether the model supports function/tool calling

    Examples:
        >>> model_info = ModelInfo(
        ...     name="anthropic/claude-3.5-sonnet",
        ...     display_name="Claude 3.5 Sonnet",
        ...     context_length=200000,
        ...     supports_streaming=True,
        ...     supports_tools=True
        ... )
    """

    name: str = Field(
        ...,
        description="Model identifier",
        examples=["anthropic/claude-3.5-sonnet", "openai/gpt-4o", "llama3.1:8b"],
    )
    display_name: str = Field(
        ...,
        description="Human-readable model name",
        examples=["Claude 3.5 Sonnet", "GPT-4o", "Llama 3.1 8B"],
    )
    context_length: int = Field(
        ...,
        description="Maximum context length in tokens",
        gt=0,
        examples=[200000, 128000, 8192],
    )
    supports_streaming: bool = Field(
        ...,
        description="Whether streaming is supported",
    )
    supports_tools: bool = Field(
        ...,
        description="Whether tool/function calling is supported",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "anthropic/claude-3.5-sonnet",
                "display_name": "Claude 3.5 Sonnet",
                "context_length": 200000,
                "supports_streaming": True,
                "supports_tools": True,
            }
        }
    )


# ============================================================================
# Validation Models
# ============================================================================


class ValidationResult(BaseModel):
    """Result of model configuration validation.

    Contains validation status and any errors encountered during
    model configuration validation.

    Attributes:
        is_valid: Whether the configuration passed validation
        errors: List of validation error messages (empty if valid)

    Examples:
        Valid configuration:
            >>> result = ValidationResult(is_valid=True, errors=[])

        Invalid configuration:
            >>> result = ValidationResult(
            ...     is_valid=False,
            ...     errors=[
            ...         "Provider 'unknown_provider' is not supported",
            ...         "Temperature 3.0 exceeds maximum of 2.0"
            ...     ]
            ... )
    """

    is_valid: bool = Field(
        ...,
        description="Whether the validation passed",
    )
    errors: List[str] = Field(
        default_factory=list,
        description="List of validation errors",
        examples=[
            ["Invalid provider: 'unknown'", "Temperature must be between 0 and 2"]
        ],
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": False,
                "errors": [
                    "Provider 'unknown_provider' is not supported",
                    "Temperature 3.0 exceeds maximum of 2.0",
                ],
            }
        }
    )
