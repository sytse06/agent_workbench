"""Streamlined API exceptions for Agent Workbench.

This module consolidates API-specific exceptions and integrates with
the core exception hierarchy for consistent error handling.
"""

from typing import Optional

from fastapi import HTTPException, status

from ..core.exceptions import (
    AgentWorkbenchError,
    ErrorCategory,
)


class APIException(HTTPException):
    """Enhanced base API exception that integrates with core error framework."""

    def __init__(
        self,
        message: str,
        status_code: int,
        error_category: ErrorCategory = ErrorCategory.INTERNAL,
        context: Optional[dict] = None,
    ):
        self.error_category = error_category
        self.context = context or {}

        detail = {
            "message": message,
            "category": error_category.value,
            "error_code": error_category.value,
            "context": self.context,
        }
        super().__init__(status_code=status_code, detail=detail)

    @classmethod
    def from_core_exception(
        cls, exc: AgentWorkbenchError, status_code: int = 500
    ) -> "APIException":
        """Create API exception from core exception."""
        return cls(
            message=exc.message,
            status_code=status_code,
            error_category=exc.category,
            context=exc.context,
        )


class DatabaseError(APIException):
    """Exception for database-related errors."""

    def __init__(self, detail: str = "Database operation failed", **kwargs):
        super().__init__(
            detail,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            ErrorCategory.INTERNAL,
            **kwargs,
        )


class NotFoundError(APIException):
    """Exception for resource not found errors."""

    def __init__(
        self, resource: str = "Resource", resource_id: Optional[str] = None, **kwargs
    ):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"

        context = {"resource_type": resource}
        if resource_id:
            context["resource_id"] = resource_id
        context.update(kwargs.get("context", {}))

        super().__init__(
            message,
            status.HTTP_404_NOT_FOUND,
            ErrorCategory.RESOURCE_NOT_FOUND,
            context,
        )


class ValidationError(APIException):
    """Exception for validation errors."""

    def __init__(
        self, detail: str = "Validation failed", field: Optional[str] = None, **kwargs
    ):
        context = {"field": field} if field else {}
        context.update(kwargs.get("context", {}))
        super().__init__(
            detail, status.HTTP_400_BAD_REQUEST, ErrorCategory.VALIDATION, context
        )


class ConflictError(APIException):
    """Exception for resource conflicts."""

    def __init__(self, detail: str = "Resource conflict", **kwargs):
        super().__init__(
            detail, status.HTTP_409_CONFLICT, ErrorCategory.VALIDATION, **kwargs
        )


# Domain-specific exception factories - use NotFoundError with parameters instead


def ConversationNotFoundError(conversation_id: Optional[str] = None):
    """Factory for conversation not found errors."""
    return NotFoundError(resource="Conversation", resource_id=conversation_id)


def MessageNotFoundError(message_id: Optional[str] = None):
    """Factory for message not found errors."""
    return NotFoundError(resource="Message", resource_id=message_id)


def AgentConfigNotFoundError(config_id: Optional[str] = None):
    """Factory for agent config not found errors."""
    return NotFoundError(resource="Agent configuration", resource_id=config_id)


def AgentConfigConflictError(detail: str = "Agent configuration already exists"):
    """Factory for agent config conflict errors."""
    return ConflictError(detail=detail)
