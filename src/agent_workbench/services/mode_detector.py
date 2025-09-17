"""Mode detection and routing logic for dual-mode operation."""

import os
from typing import Literal, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import ConversationModel


class ModeDetector:
    """Detects and manages workflow mode routing."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        """
        Initialize mode detector.

        Args:
            db_session: Database session for conversation lookups
        """
        self.db_session = db_session

    def detect_mode_from_environment(self) -> Literal["workbench", "seo_coach"]:
        """
        Detect mode from environment variables.

        Returns:
            Detected workflow mode
        """
        app_mode = os.getenv("APP_MODE", "").lower()

        if app_mode == "seo_coach":
            return "seo_coach"
        elif app_mode == "workbench":
            return "workbench"

        # Default based on other environment hints
        if os.getenv("SEO_COACH_MODE", "").lower() == "true":
            return "seo_coach"

        # We ensure we only return valid literals
        return "workbench"  # Default mode - explicitly type as Literal

    async def detect_mode_from_conversation(
        self, conversation_id: UUID
    ) -> Optional[Literal["workbench", "seo_coach"]]:
        """
        Detect mode from existing conversation.

        Args:
            conversation_id: Conversation ID to check

        Returns:
            Detected workflow mode or None if not found
        """
        if not self.db_session:
            return None

        try:
            # Query conversation for workflow_mode
            result = await self.db_session.execute(
                select(ConversationModel.workflow_mode).where(
                    ConversationModel.id == conversation_id
                )
            )
            mode = result.scalar_one_or_none()
            if isinstance(mode, str):
                if mode == "workbench":
                    return "workbench"
                elif mode == "seo_coach":
                    return "seo_coach"
            return None

        except Exception:
            # If conversation doesn't exist or has no mode, return None
            return None

    def detect_mode_from_request(
        self, request: dict
    ) -> Optional[Literal["workbench", "seo_coach"]]:
        """
        Detect mode from request parameters.

        Args:
            request: Request data dictionary

        Returns:
            Detected workflow mode or None
        """
        # Check explicit workflow_mode in request
        if "workflow_mode" in request and request["workflow_mode"]:
            mode = request["workflow_mode"]
            if isinstance(mode, str) and mode in ["workbench", "seo_coach"]:
                if mode == "workbench":
                    return "workbench"
                elif mode == "seo_coach":
                    return "seo_coach"

        # Check for business profile indicators
        if "business_profile" in request and request["business_profile"]:
            return "seo_coach"

        # Check for SEO-related indicators in message
        if "user_message" in request:
            message = request["user_message"].lower()
            seo_keywords = [
                "seo",
                "website",
                "google",
                "zoekresultaten",
                "vindbaarheid",
                "bedrijf",
                "marketing",
                "online",
                "bezoekers",
                "zoekmachine",
            ]
            if any(keyword in message for keyword in seo_keywords):
                return "seo_coach"

        return None

    async def get_effective_mode(
        self,
        conversation_id: Optional[UUID] = None,
        requested_mode: Optional[str] = None,
        request_data: Optional[dict] = None,
    ) -> Literal["workbench", "seo_coach"]:
        """
        Determine the effective workflow mode using priority rules.

        Priority order:
        1. Explicitly requested mode
        2. Mode from existing conversation
        3. Mode detected from request content
        4. Environment-based mode
        5. Default to workbench

        Args:
            conversation_id: Existing conversation ID
            requested_mode: Explicitly requested mode
            request_data: Request data for content analysis

        Returns:
            Effective workflow mode
        """
        # 1. Explicit request mode (highest priority)
        if requested_mode and requested_mode in ["workbench", "seo_coach"]:
            if requested_mode == "workbench":
                return "workbench"
            else:
                return "seo_coach"

        # 2. Mode from existing conversation
        if conversation_id:
            conversation_mode = await self.detect_mode_from_conversation(
                conversation_id
            )
            if conversation_mode:
                return conversation_mode

        # 3. Mode from request content
        if request_data:
            request_mode = self.detect_mode_from_request(request_data)
            if request_mode:
                return request_mode

        # 4. Environment-based mode
        return self.detect_mode_from_environment()

        # 5. Default fallback is handled in detect_mode_from_environment

    def is_valid_mode(self, mode: str) -> bool:
        """
        Check if mode is valid.

        Args:
            mode: Mode to validate

        Returns:
            True if mode is valid
        """
        return mode in ["workbench", "seo_coach"]

    def get_default_model_config_for_mode(self, mode: str) -> dict:
        """
        Get default model configuration for a specific mode.

        Args:
            mode: Workflow mode

        Returns:
            Default model configuration
        """
        if mode == "seo_coach":
            return {
                "provider": "openrouter",
                "model_name": "openai/gpt-4o-mini",
                "temperature": 0.7,
                "max_tokens": 1500,
                "streaming": True,
            }

        # Workbench mode default
        return {
            "provider": "openrouter",
            "model_name": "qwen/qwq-32b-preview",
            "temperature": 0.7,
            "max_tokens": 2000,
            "streaming": True,
        }
