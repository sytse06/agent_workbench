"""Custom API exceptions for Agent Workbench."""

from typing import Optional

from fastapi import HTTPException, status


class DatabaseError(HTTPException):
    """Base exception for database-related errors."""

    def __init__(
        self,
        detail: str = "Database operation failed",
        error_code: Optional[str] = None,
    ):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"detail": detail, "error_code": error_code or "DATABASE_ERROR"},
        )


class NotFoundError(HTTPException):
    """Exception for when a resource is not found."""

    def __init__(
        self,
        resource: str = "Resource",
        resource_id: Optional[str] = None,
        error_code: Optional[str] = None,
    ):
        detail = f"{resource} not found"
        if resource_id:
            detail = f"{resource} with id '{resource_id}' not found"

        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"detail": detail, "error_code": error_code or "NOT_FOUND"},
        )


class ValidationError(HTTPException):
    """Exception for validation errors."""

    def __init__(
        self, detail: str = "Validation failed", error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": detail, "error_code": error_code or "VALIDATION_ERROR"},
        )


class ConflictError(HTTPException):
    """Exception for conflicts (e.g., duplicate resources)."""

    def __init__(
        self, detail: str = "Resource conflict", error_code: Optional[str] = None
    ):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"detail": detail, "error_code": error_code or "CONFLICT"},
        )


# Specific exceptions for our domain
class ConversationNotFoundError(NotFoundError):
    """Exception for when a conversation is not found."""

    def __init__(self, conversation_id: Optional[str] = None):
        super().__init__(
            resource="Conversation",
            resource_id=conversation_id,
            error_code="CONVERSATION_NOT_FOUND",
        )


class MessageNotFoundError(NotFoundError):
    """Exception for when a message is not found."""

    def __init__(self, message_id: Optional[str] = None):
        super().__init__(
            resource="Message", resource_id=message_id, error_code="MESSAGE_NOT_FOUND"
        )


class AgentConfigNotFoundError(NotFoundError):
    """Exception for when an agent configuration is not found."""

    def __init__(self, config_id: Optional[str] = None):
        super().__init__(
            resource="Agent configuration",
            resource_id=config_id,
            error_code="AGENT_CONFIG_NOT_FOUND",
        )


class AgentConfigConflictError(ConflictError):
    """Exception for when an agent configuration conflicts."""

    def __init__(self, detail: str = "Agent configuration already exists"):
        super().__init__(detail=detail, error_code="AGENT_CONFIG_CONFLICT")
