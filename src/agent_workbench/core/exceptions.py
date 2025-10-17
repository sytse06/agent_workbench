"""Streamlined exception hierarchy for Agent Workbench.

Consolidated from 13+ exception classes to 6 core types:
- AgentWorkbenchError: Enhanced base with error categorization
- LLMProviderError: Provider-related errors
- ModelConfigurationError: Configuration errors
- ConversationError: Conversation management errors
- StreamingError: Streaming response errors
- ValidationError: Input validation errors
- ResourceNotFoundError: Resource lookup errors
"""

from enum import Enum
from typing import Any, Dict, Optional


class ErrorCategory(Enum):
    """Categorization of error types for consistent handling."""

    PROVIDER = "PROVIDER_ERROR"
    CONFIGURATION = "CONFIGURATION_ERROR"
    CONVERSATION = "CONVERSATION_ERROR"
    STREAMING = "STREAMING_ERROR"
    VALIDATION = "VALIDATION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    AUTHENTICATION = "AUTHENTICATION_ERROR"
    RATE_LIMIT = "RATE_LIMIT_ERROR"
    NETWORK = "NETWORK_ERROR"
    INTERNAL = "INTERNAL_ERROR"


class AgentWorkbenchError(Exception):
    """Enhanced base exception for Agent Workbench with error categorization."""

    message: str
    category: ErrorCategory
    error_code: Optional[str]
    context: Dict[str, Any]

    def __init__(
        self,
        message: str,
        error_code_or_category=None,  # Backwards compatibility
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message = message

        # Handle backwards compatibility
        if isinstance(error_code_or_category, str):
            # Old API: AgentWorkbenchError("message", "ERROR_CODE")
            self.error_code = error_code_or_category
            self.category = ErrorCategory.INTERNAL
        elif isinstance(error_code_or_category, ErrorCategory):
            # New API: AgentWorkbenchError("message", ErrorCategory.PROVIDER)
            self.category = error_code_or_category
            self.error_code = error_code or error_code_or_category.value
        elif error_code_or_category is None:
            # Default case - maintain backwards compatibility
            self.category = ErrorCategory.INTERNAL
            self.error_code = error_code  # Can be None for backwards compatibility
        else:
            # Fallback
            self.category = ErrorCategory.INTERNAL
            self.error_code = error_code or ErrorCategory.INTERNAL.value

        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "message": self.message,
            "category": self.category.value,
            "error_code": self.error_code,
            "context": self.context,
        }


class LLMProviderError(AgentWorkbenchError):
    """Exception for LLM provider-related errors."""

    def __init__(self, message: str, provider: Optional[str] = None, **kwargs):
        context = {"provider": provider} if provider else {}
        context.update(kwargs.get("context", {}))
        # Maintain backwards compatibility with specific error code
        super().__init__(
            message,
            ErrorCategory.PROVIDER,
            error_code="LLM_PROVIDER_ERROR",
            context=context,
        )
        self.provider = provider


class ModelConfigurationError(AgentWorkbenchError):
    """Exception for model configuration errors."""

    def __init__(self, message: str, model_config: Optional[dict] = None, **kwargs):
        context = {"model_config": model_config} if model_config else {}
        context.update(kwargs.get("context", {}))
        # Maintain backwards compatibility with specific error code
        super().__init__(
            message,
            ErrorCategory.CONFIGURATION,
            error_code="MODEL_CONFIG_ERROR",
            context=context,
        )
        self.model_config = model_config


class ConversationError(AgentWorkbenchError):
    """Exception for conversation management errors."""

    def __init__(self, message: str, conversation_id: Optional[str] = None, **kwargs):
        context = {"conversation_id": conversation_id} if conversation_id else {}
        context.update(kwargs.get("context", {}))
        # Maintain backwards compatibility with specific error code
        super().__init__(
            message,
            ErrorCategory.CONVERSATION,
            error_code="CONVERSATION_ERROR",
            context=context,
        )
        self.conversation_id = conversation_id


class StreamingError(AgentWorkbenchError):
    """Exception for streaming response errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCategory.STREAMING, **kwargs)


class ValidationError(AgentWorkbenchError):
    """Exception for validation errors."""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        context = {"field": field} if field else {}
        context.update(kwargs.get("context", {}))
        super().__init__(message, ErrorCategory.VALIDATION, context=context)
        self.field = field


class ResourceNotFoundError(AgentWorkbenchError):
    """Exception for resource not found errors."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs,
    ):
        context = {}
        if resource_type:
            context["resource_type"] = resource_type
        if resource_id:
            context["resource_id"] = resource_id
        context.update(kwargs.get("context", {}))
        super().__init__(message, ErrorCategory.RESOURCE_NOT_FOUND, context=context)
        self.resource_type = resource_type
        self.resource_id = resource_id


class AuthenticationError(AgentWorkbenchError):
    """Exception for authentication and authorization errors."""

    def __init__(self, message: str, user_id: Optional[str] = None, **kwargs):
        context = {"user_id": user_id} if user_id else {}
        context.update(kwargs.get("context", {}))
        super().__init__(
            message,
            ErrorCategory.AUTHENTICATION,
            error_code="AUTHENTICATION_ERROR",
            context=context,
        )
        self.user_id = user_id


# Backwards compatibility aliases - these will be removed in next phase
class RetryExhaustedError(AgentWorkbenchError):
    """Exception raised when retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int):
        self.attempts = attempts
        super().__init__(
            message, ErrorCategory.INTERNAL, context={"attempts": attempts}
        )
