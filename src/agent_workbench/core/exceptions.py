"""Custom exceptions for Agent Workbench LLM service."""

from typing import Optional


class AgentWorkbenchError(Exception):
    """Base exception for Agent Workbench."""

    def __init__(self, message: str, error_code: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class LLMProviderError(AgentWorkbenchError):
    """Exception raised when there's an error with LLM provider."""

    def __init__(self, message: str, provider: Optional[str] = None):
        self.provider = provider
        super().__init__(message, "LLM_PROVIDER_ERROR")


class ModelConfigurationError(AgentWorkbenchError):
    """Exception raised when model configuration is invalid."""

    def __init__(self, message: str, model_config: Optional[dict] = None):
        self.model_config = model_config
        super().__init__(message, "MODEL_CONFIG_ERROR")


class ConversationError(AgentWorkbenchError):
    """Exception raised when there's an error with conversation management."""

    def __init__(self, message: str, conversation_id: Optional[str] = None):
        self.conversation_id = conversation_id
        super().__init__(message, "CONVERSATION_ERROR")


class StreamingError(AgentWorkbenchError):
    """Exception raised when there's an error with streaming responses."""

    def __init__(self, message: str):
        super().__init__(message, "STREAMING_ERROR")


class RetryExhaustedError(AgentWorkbenchError):
    """Exception raised when retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int):
        self.attempts = attempts
        super().__init__(message, "RETRY_EXHAUSTED")
