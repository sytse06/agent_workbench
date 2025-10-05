"""Services package for Agent Workbench."""

from ..core.exceptions import (
    AgentWorkbenchError,
    ConversationError,
    LLMProviderError,
    ModelConfigurationError,
    RetryExhaustedError,
    StreamingError,
)
from ..core.retry import retry_api_call, retry_database_operation, retry_llm_call
from ..models.api_models import (
    ChatRequest,
    ChatResponse,
    ConversationResponse,
    ConversationSummary,
    CreateConversationRequest,
    ModelInfo,
    ValidationResult,
)
from ..models.schemas import ModelConfig
from .conversation_service import ConversationService
from .llm_service import ChatService, create_chat_service, get_default_chat_service
from .providers import (
    PROVIDER_FACTORIES,
    ModelRegistry,
    ProviderConfig,
    provider_registry,
)

__all__ = [
    # chat_models
    "ModelConfig",
    "ModelInfo",
    "ChatRequest",
    "ChatResponse",
    "ConversationSummary",
    "ConversationResponse",
    "CreateConversationRequest",
    "ValidationResult",
    # exceptions
    "AgentWorkbenchError",
    "LLMProviderError",
    "ModelConfigurationError",
    "ConversationError",
    "StreamingError",
    "RetryExhaustedError",
    # retry
    "retry_llm_call",
    "retry_api_call",
    "retry_database_operation",
    # providers
    "ProviderConfig",
    "ModelRegistry",
    "provider_registry",
    "PROVIDER_FACTORIES",
    # llm_service
    "ChatService",
    "create_chat_service",
    "get_default_chat_service",
    # conversation_service
    "ConversationService",
]
