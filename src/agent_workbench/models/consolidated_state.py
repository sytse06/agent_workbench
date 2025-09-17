"""LangGraph state models for unified dual-mode workflow system."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .schemas import ModelConfig
from .standard_messages import StandardMessage


class WorkbenchState(TypedDict):
    """
    LangGraph state model for unified dual-mode workflow orchestration.

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


class ConsolidatedWorkflowRequest(BaseModel):
    """Request model for consolidated workflow execution."""

    conversation_id: Optional[UUID] = None
    user_message: str = Field(..., min_length=1, max_length=10000)
    workflow_mode: Optional[Literal["workbench", "seo_coach"]] = None
    llm_config: Optional[ModelConfig] = None
    parameter_overrides: Optional[Dict[str, Any]] = None
    business_profile: Optional[Dict[str, Any]] = None
    context_data: Optional[Dict[str, Any]] = None
    streaming: bool = False


class ConsolidatedWorkflowResponse(BaseModel):
    """Response model for consolidated workflow execution."""

    conversation_id: UUID
    assistant_response: str
    workflow_mode: str
    execution_successful: bool
    workflow_steps: List[str]
    context_data: Dict[str, Any]
    business_profile: Optional[Dict[str, Any]] = None
    coaching_context: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


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


class CreateConversationRequest(BaseModel):
    """Request model for creating conversations."""

    title: Optional[str] = None
    workflow_mode: Literal["workbench", "seo_coach"] = "workbench"
    llm_config: Optional[ModelConfig] = None
    is_temporary: bool = False


class ConversationResponse(BaseModel):
    """Response model for conversation operations."""

    id: UUID
    title: str
    workflow_mode: str
    created_at: datetime
    last_activity: datetime
    message_count: int
    is_temporary: bool = False
