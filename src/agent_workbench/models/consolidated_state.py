"""LangGraph state models for unified dual-mode workflow system."""

from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import TypedDict

from .schemas import ModelConfig
from .standard_messages import StandardMessage


class WorkbenchState(TypedDict):
    """
    LangGraph state model for unified dual-mode workflow orchestration.

    TypedDict for LangGraph compatibility - provides type hints without
    runtime validation. Use ValidatedWorkbenchState for validation before
    converting to this format.

    Follows GAIA agent patterns with TypedDict for LangGraph compatibility.
    """

    # Core conversation state
    conversation_id: UUID
    user_message: str
    assistant_response: Optional[str]

    # Model and provider configuration
    model_config: ModelConfig
    provider_name: str

    # Context and conversation memory
    context_data: Dict[str, Any]
    active_contexts: List[str]
    conversation_history: List[StandardMessage]

    # Workflow orchestration
    workflow_mode: Literal["workbench", "seo_coach"]
    workflow_steps: List[str]
    current_operation: Optional[str]
    execution_successful: bool

    # Error handling and recovery
    current_error: Optional[str]
    retry_count: int

    # SEO Coach specific state
    business_profile: Optional[Dict[str, Any]]
    seo_analysis: Optional[Dict[str, Any]]
    coaching_context: Optional[Dict[str, Any]]
    coaching_phase: Optional[
        Literal["analysis", "recommendations", "implementation", "monitoring"]
    ]

    # Workbench specific state
    debug_mode: Optional[bool]
    parameter_overrides: Optional[Dict[str, Any]]

    # Phase 2 extensions (empty for now)
    mcp_tools_active: List[str]
    agent_state: Optional[Dict[str, Any]]
    workflow_data: Optional[Dict[str, Any]]

    # File processing (Phase 2.2)
    document_context: Optional[str]
    document_filename: Optional[str]


class ValidatedWorkbenchState(BaseModel):
    """
    Validated Pydantic wrapper for WorkbenchState.

    Provides comprehensive validation for workflow state before conversion
    to TypedDict format for LangGraph execution. Use this model to validate
    state data, then call .to_typeddict() to get LangGraph-compatible format.

    Examples:
        >>> validated = ValidatedWorkbenchState(
        ...     conversation_id=UUID("..."),
        ...     user_message="Debug this code",
        ...     model_config=ModelConfig(
        ...         provider="anthropic",
        ...         model_name="claude-3.5-sonnet"
        ...     ),
        ...     provider_name="anthropic",
        ...     workflow_mode="workbench"
        ... )
        >>> state: WorkbenchState = validated.to_typeddict()
    """

    # Core conversation state
    conversation_id: UUID = Field(
        ...,
        description="Conversation identifier",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    user_message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User's input message",
        examples=[
            "How do I optimize this SQL query?",
            "Analyze SEO for my website",
        ],
    )
    assistant_response: Optional[str] = Field(
        None,
        max_length=50000,
        description="Assistant's generated response",
    )

    # Model and provider configuration
    model_config_field: ModelConfig = Field(
        ...,
        alias="model_config",
        description="LLM model configuration",
    )
    provider_name: str = Field(
        ...,
        pattern=r"^[a-z_]+$",
        description="Provider name (lowercase with underscores)",
        examples=["anthropic", "openai", "ollama"],
    )

    # Context and conversation memory
    context_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Conversation context data",
    )
    active_contexts: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="List of active context identifiers",
        examples=[["user_preferences", "session_data"]],
    )
    conversation_history: List[StandardMessage] = Field(
        default_factory=list,
        max_length=1000,
        description="Full conversation message history",
    )

    # Workflow orchestration
    workflow_mode: Literal["workbench", "seo_coach"] = Field(
        default="workbench",
        description="Current workflow execution mode",
    )
    workflow_steps: List[str] = Field(
        default_factory=list,
        max_length=100,
        description="Executed workflow steps",
        examples=[["init", "load_context", "generate_response", "save_state"]],
    )
    current_operation: Optional[str] = Field(
        None,
        max_length=100,
        description="Currently executing operation",
        examples=["generating_response", "loading_context", "saving_state"],
    )
    execution_successful: bool = Field(
        default=True,
        description="Whether workflow execution succeeded",
    )

    # Error handling and recovery
    current_error: Optional[str] = Field(
        None,
        max_length=1000,
        description="Current error message if any",
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        le=5,
        description="Number of retry attempts",
    )

    # SEO Coach specific state
    business_profile: Optional[Dict[str, Any]] = Field(
        None,
        description="Business profile data for SEO coaching",
    )
    seo_analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="SEO analysis results",
    )
    coaching_context: Optional[Dict[str, Any]] = Field(
        None,
        description="SEO coaching context and recommendations",
    )
    coaching_phase: Optional[
        Literal["analysis", "recommendations", "implementation", "monitoring"]
    ] = Field(
        None,
        description="Current phase in SEO coaching workflow",
    )

    # Workbench specific state
    debug_mode: Optional[bool] = Field(
        None,
        description="Whether debug mode is enabled",
    )
    parameter_overrides: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameter overrides for workbench mode",
    )

    # Phase 2 extensions
    mcp_tools_active: List[str] = Field(
        default_factory=list,
        max_length=50,
        description="List of active MCP tool identifiers",
        examples=[["web_search", "code_execution", "file_access"]],
    )
    agent_state: Optional[Dict[str, Any]] = Field(
        None,
        description="Multi-agent system state data",
    )
    workflow_data: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional workflow-specific data",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                "user_message": "Help me debug this Python error",
                "model_config": {
                    "provider": "anthropic",
                    "model_name": "claude-3.5-sonnet",
                    "temperature": 0.7,
                },
                "provider_name": "anthropic",
                "workflow_mode": "workbench",
                "workflow_steps": [
                    "init",
                    "load_context",
                    "generate_response",
                ],
                "execution_successful": True,
                "retry_count": 0,
            }
        },
    )

    @field_validator("provider_name")
    @classmethod
    def validate_provider_name(cls, v: str) -> str:
        """Validate provider name format."""
        if not v.islower():
            raise ValueError("Provider name must be lowercase")
        if " " in v:
            raise ValueError("Provider name cannot contain spaces")
        return v

    @field_validator("workflow_steps")
    @classmethod
    def validate_workflow_steps(cls, v: List[str]) -> List[str]:
        """Validate workflow steps list."""
        if len(v) > 100:
            raise ValueError("Workflow steps cannot exceed 100 entries")
        # Ensure no empty step names
        if any(not step.strip() for step in v):
            raise ValueError("Workflow steps cannot be empty strings")
        return v

    @field_validator("retry_count")
    @classmethod
    def validate_retry_count(cls, v: int) -> int:
        """Validate retry count is within safe bounds."""
        if v > 5:
            raise ValueError("Retry count cannot exceed 5 to prevent infinite loops")
        return v

    def to_typeddict(self) -> WorkbenchState:
        """Convert validated state to TypedDict for LangGraph.

        Returns:
            WorkbenchState TypedDict ready for LangGraph execution
        """
        data = self.model_dump(by_alias=True)
        # TypedDict expects 'model_config', not 'model_config_field'
        if "model_config_field" in data:
            data["model_config"] = data.pop("model_config_field")
        return data  # type: ignore

    @classmethod
    def from_typeddict(cls, state: WorkbenchState) -> "ValidatedWorkbenchState":
        """Create validated state from TypedDict.

        Args:
            state: WorkbenchState TypedDict from LangGraph

        Returns:
            Validated WorkbenchState instance
        """
        # Handle the alias mapping
        state_copy = dict(state)
        if "model_config" in state_copy:
            state_copy["model_config_field"] = state_copy.pop("model_config")
        return cls(**state_copy)


class ConsolidatedWorkflowRequest(BaseModel):
    """Request model for consolidated workflow execution."""

    conversation_id: Optional[Union[UUID, str]] = None
    user_message: str = Field(..., min_length=1, max_length=10000)
    workflow_mode: Optional[Literal["workbench", "seo_coach"]] = None
    llm_config: Optional[ModelConfig] = None
    parameter_overrides: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
    context_data: Optional[Dict[str, Any]] = None
    streaming: bool = False
    pending_files: Optional[List[Any]] = None  # items may be str paths or dicts
    document_context: Optional[str] = None
    document_filename: Optional[str] = None
    active_tools: List[str] = Field(default_factory=list)


class ConsolidatedWorkflowResponse(BaseModel):
    """Response model for consolidated workflow execution."""

    conversation_id: Union[UUID, str]
    assistant_response: str
    workflow_mode: str
    execution_successful: bool
    workflow_steps: List[str]
    context_data: Dict[str, Any]
    business_profile: Optional[Dict[str, Any]] = None
    coaching_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    response_metadata: Optional[Dict[str, Any]] = None


class WorkflowUpdate(BaseModel):
    """Streaming workflow update model."""

    conversation_id: UUID
    current_step: str
    progress_percentage: float
    partial_response: Optional[str] = None
    workflow_steps: List[str]
    error: Optional[str] = None


class ContextUpdateRequest(BaseModel):
    """Request model for context updates."""

    context_data: Dict[str, Any]
    sources: List[str]
    merge_strategy: Literal["replace", "merge", "append"] = "merge"
