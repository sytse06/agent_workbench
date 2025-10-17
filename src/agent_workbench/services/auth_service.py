"""Service for handling multi-provider OAuth and session management."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from gradio import Request

from ..core.exceptions import AuthenticationError
from ..database import AdaptiveDatabase

logger = logging.getLogger(__name__)


class AuthService:
    """Handle multi-provider OAuth and session management.

    Supports provider-agnostic authentication with flexible provider-specific
    data storage. Initial implementation uses HuggingFace OAuth via Gradio.

    Examples:
        >>> service = AuthService()
        >>> user = await service.get_or_create_user_from_request(
        ...     request=gradio_request,
        ...     provider="huggingface"
        ... )
        >>> session = await service.create_session(
        ...     user_id=user.id,
        ...     request=gradio_request
        ... )
    """

    def __init__(self, db: Optional[AdaptiveDatabase] = None):
        """Initialize authentication service with optional database instance.

        Args:
            db: AdaptiveDatabase instance (creates new if not provided)
        """
        self.db = db or AdaptiveDatabase()
        self.session_timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))

    async def get_or_create_user_from_request(
        self, request: Request, provider: str = "huggingface"
    ) -> dict:
        """Get or create user from Gradio request.

        Args:
            request: Gradio request object with authenticated user info
            provider: Authentication provider name ("huggingface", "google", etc.)

        Returns:
            User dictionary with populated generic and provider-specific fields

        Implementation:
            - Extract username from request.username
            - Extract provider-specific data into provider_data JSON
            - Populate generic fields (username, email, avatar_url)
            - Create or update user record

        Raises:
            AuthenticationError: If user extraction or creation fails
        """
        try:
            # Extract username from request
            username = getattr(request, "username", None)
            if not username:
                raise AuthenticationError("No username found in request")

            # Check if user already exists
            user = self.db.get_user_by_username(username)

            if user:
                # Update last_login
                self.db.update_user_last_login(user["id"])
                logger.info(f"User {username} logged in (provider: {provider})")
                return user

            # Extract provider-specific data
            provider_data = {}
            email = None
            avatar_url = None

            if provider == "huggingface":
                # HuggingFace-specific extraction
                # Note: Gradio HF auth provides limited user info
                # More detailed info would require HF API call
                provider_data = {
                    "hf_username": username,
                    # Add more HF-specific fields if available from request
                }
                # Email and avatar typically require separate HF API call
                email = getattr(request, "email", None)
                avatar_url = getattr(request, "avatar_url", None)

            elif provider == "google":
                # Google OAuth extraction (future implementation)
                email = getattr(request, "email", None)
                avatar_url = getattr(request, "picture", None)
                provider_data = {
                    "google_id": getattr(request, "sub", None),
                    "google_email_verified": getattr(request, "email_verified", False),
                }

            elif provider == "github":
                # GitHub OAuth extraction (future implementation)
                email = getattr(request, "email", None)
                avatar_url = getattr(request, "avatar_url", None)
                provider_data = {
                    "github_id": getattr(request, "id", None),
                    "github_login": getattr(request, "login", username),
                }

            elif provider == "development":
                # Development mode: local authentication without OAuth
                email = getattr(request, "email", None)
                avatar_url = getattr(request, "avatar_url", None)
                provider_data = {
                    "dev_username": username,
                    "dev_mode": True,
                }

            # Create new user
            self.db.create_user(
                username=username,
                auth_provider=provider,
                email=email,
                avatar_url=avatar_url,
                provider_data=provider_data,
            )

            user = self.db.get_user_by_username(username)
            if not user:
                raise AuthenticationError(f"Failed to create user {username}")

            logger.info(f"Created new user {username} (provider: {provider})")
            return user

        except Exception as e:
            error_msg = f"Failed to get or create user: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def get_active_session(
        self, user_id: str, max_age_minutes: Optional[int] = None
    ) -> Optional[dict]:
        """Get active session within timeout window.

        Args:
            user_id: User UUID string
            max_age_minutes: Maximum age in minutes (uses default if not provided)

        Returns:
            Session dictionary or None if no active session

        Raises:
            AuthenticationError: If session retrieval fails
        """
        try:
            timeout_minutes = max_age_minutes or self.session_timeout_minutes
            since = datetime.utcnow() - timedelta(minutes=timeout_minutes)

            session = self.db.get_active_user_session(user_id, since)

            if session:
                logger.debug(f"Found active session {session['id']} for user {user_id}")

            return session

        except Exception as e:
            error_msg = f"Failed to get active session: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def update_session_activity(self, session_id: str) -> None:
        """Update session last_activity timestamp.

        Args:
            session_id: Session UUID string

        Raises:
            AuthenticationError: If update fails
        """
        try:
            success = self.db.update_session_activity(session_id)
            if not success:
                raise AuthenticationError(f"Session {session_id} not found")

            logger.debug(f"Updated activity for session {session_id}")

        except Exception as e:
            error_msg = f"Failed to update session activity: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def create_session(self, user_id: str, request: Request) -> dict:
        """Create new user session.

        Args:
            user_id: User UUID string
            request: Gradio request object for metadata extraction

        Returns:
            Session dictionary

        Raises:
            AuthenticationError: If session creation fails
        """
        try:
            # Extract request metadata
            # Note: Gradio Request may have limited metadata
            # These fields might not be available in all Gradio versions
            ip_address = (
                getattr(request, "client", {}).get("host", None)
                if hasattr(request, "client")
                else None
            )
            user_agent = (
                getattr(request, "headers", {}).get("user-agent", None)
                if hasattr(request, "headers")
                else None
            )
            referrer = (
                getattr(request, "headers", {}).get("referer", None)
                if hasattr(request, "headers")
                else None
            )

            # Create session
            session_id = self.db.create_user_session(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referrer=referrer,
            )

            # Log session creation activity
            self.db.create_session_activity(
                session_id=session_id,
                user_id=user_id,
                action="session_started",
                metadata={"ip_address": ip_address},
            )

            # Get created session
            # Note: We need to retrieve it to get the full session data
            # This is a workaround since create_user_session returns ID only
            since = datetime.utcnow() - timedelta(seconds=10)
            session = self.db.get_active_user_session(user_id, since)

            if not session:
                raise AuthenticationError(
                    f"Failed to retrieve created session {session_id}"
                )

            logger.info(f"Created session {session_id} for user {user_id}")
            return session

        except Exception as e:
            error_msg = f"Failed to create session: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def log_session_activity(
        self,
        session_id: str,
        user_id: str,
        action: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """Log activity within session.

        Args:
            session_id: Session UUID string
            user_id: User UUID string
            action: Action name (e.g., "message_sent", "tool_called")
            metadata: Additional metadata (optional)

        Raises:
            AuthenticationError: If activity logging fails
        """
        try:
            self.db.create_session_activity(
                session_id=session_id,
                user_id=user_id,
                action=action,
                metadata=metadata,
            )

            logger.debug(f"Logged activity '{action}' for session {session_id}")

        except Exception as e:
            error_msg = f"Failed to log session activity: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def end_session(self, session_id: str) -> None:
        """Mark session as ended.

        Args:
            session_id: Session UUID string

        Raises:
            AuthenticationError: If session end fails
        """
        try:
            success = self.db.end_session(session_id)
            if not success:
                raise AuthenticationError(f"Session {session_id} not found")

            logger.info(f"Ended session {session_id}")

        except Exception as e:
            error_msg = f"Failed to end session: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def increment_session_messages(self, session_id: str) -> None:
        """Increment session's total_messages counter.

        Args:
            session_id: Session UUID string

        Raises:
            AuthenticationError: If increment fails
        """
        try:
            success = self.db.increment_session_messages(session_id)
            if not success:
                raise AuthenticationError(f"Session {session_id} not found")

        except Exception as e:
            error_msg = f"Failed to increment session messages: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e

    async def increment_session_tool_calls(self, session_id: str) -> None:
        """Increment session's total_tool_calls counter.

        Args:
            session_id: Session UUID string

        Raises:
            AuthenticationError: If increment fails
        """
        try:
            success = self.db.increment_session_tool_calls(session_id)
            if not success:
                raise AuthenticationError(f"Session {session_id} not found")

        except Exception as e:
            error_msg = f"Failed to increment session tool calls: {str(e)}"
            logger.error(error_msg)
            raise AuthenticationError(error_msg) from e
