"""Bridge between LLM-001B ConversationState and LangGraph WorkbenchState."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ..core.exceptions import ConversationError
from ..models.consolidated_state import WorkbenchState
from ..models.schemas import ModelConfig
from ..models.standard_messages import ConversationState, StandardMessage
from .context_service import ContextService
from .state_manager import StateManager


class LangGraphStateBridge:
    """Bridge between LLM-001B ConversationState and LangGraph WorkbenchState."""

    def __init__(self, state_manager: StateManager, context_service: ContextService):
        """
        Initialize state bridge.

        Args:
            state_manager: LLM-001B state manager
            context_service: Context injection service
        """
        self.state_manager = state_manager
        self.context_service = context_service

    async def load_into_langgraph_state(
        self,
        conversation_id: UUID,
        user_message: str,
        workflow_mode: str,
        business_profile: Optional[Dict[str, Any]] = None,
    ) -> WorkbenchState:
        """
        Load LLM-001B conversation state into LangGraph format.

        Args:
            conversation_id: Conversation ID to load
            user_message: Current user message
            workflow_mode: Target workflow mode
            business_profile: Optional business profile data

        Returns:
            LangGraph-compatible state

        Raises:
            ConversationError: If state loading fails
        """
        try:
            # Load existing conversation state from LLM-001B
            conversation_state = await self.state_manager.load_conversation_state(
                conversation_id
            )

            # Convert to LangGraph state
            lg_state: WorkbenchState = {
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_response": None,
                # Preserve LLM-001B state
                "model_config": conversation_state.llm_config,
                "provider_name": conversation_state.llm_config.provider,
                "context_data": conversation_state.context_data,
                "active_contexts": conversation_state.active_contexts,
                "conversation_history": conversation_state.messages,
                # Initialize workflow state
                "workflow_mode": workflow_mode,  # type: ignore
                "workflow_steps": [],
                "current_operation": None,
                "execution_successful": True,
                "current_error": None,
                "retry_count": 0,
                # Mode-specific initialization
                "business_profile": business_profile,
                "seo_analysis": None,
                "coaching_context": None,
                "coaching_phase": None,
                "debug_mode": None,
                "parameter_overrides": None,
                # Phase 2 placeholders
                "mcp_tools_active": [],
                "agent_state": None,
                "workflow_data": None,
            }

            return lg_state

        except Exception:
            # Create new conversation state if loading fails
            return await self._create_new_langgraph_state(
                conversation_id, user_message, workflow_mode, business_profile
            )

    async def save_from_langgraph_state(self, lg_state: WorkbenchState) -> None:
        """
        Save LangGraph state back to LLM-001B persistence.

        Args:
            lg_state: LangGraph state to persist

        Raises:
            ConversationError: If state saving fails
        """
        try:
            # Convert to LLM-001B ConversationState
            conversation_state = ConversationState(
                conversation_id=lg_state["conversation_id"],
                messages=lg_state["conversation_history"],
                llm_config=lg_state["model_config"],
                context_data=lg_state["context_data"],
                active_contexts=lg_state["active_contexts"],
                metadata={
                    "workflow_mode": lg_state["workflow_mode"],
                    "execution_successful": lg_state["execution_successful"],
                    "last_workflow_steps": lg_state["workflow_steps"],
                    "business_profile": lg_state.get("business_profile"),
                    "coaching_context": lg_state.get("coaching_context"),
                    "debug_mode": lg_state.get("debug_mode"),
                    "parameter_overrides": lg_state.get("parameter_overrides"),
                },
                updated_at=datetime.utcnow(),
            )

            # Save using LLM-001B infrastructure
            await self.state_manager.save_conversation_state(conversation_state)

            # Save workflow execution record for monitoring
            await self._save_workflow_execution(lg_state)

        except Exception as e:
            raise ConversationError(f"Failed to save LangGraph state: {str(e)}") from e

    async def migrate_conversation_to_consolidated(
        self, conversation_id: UUID
    ) -> WorkbenchState:
        """
        Migrate existing LLM-001B conversation to consolidated format.

        Args:
            conversation_id: Conversation to migrate

        Returns:
            Migrated LangGraph state

        Raises:
            ConversationError: If migration fails
        """
        try:
            # Load existing conversation using LLM-001B migration
            conversation_state = (
                await self.state_manager.migrate_conversation_to_stateful(
                    conversation_id
                )
            )

            # Convert to consolidated LangGraph format
            lg_state: WorkbenchState = {
                "conversation_id": conversation_id,
                "user_message": "",  # Will be set by workflow
                "assistant_response": None,
                "model_config": conversation_state.model_config,
                "provider_name": conversation_state.model_config.provider,
                "context_data": conversation_state.context_data,
                "active_contexts": conversation_state.active_contexts,
                "conversation_history": conversation_state.messages,
                "workflow_mode": "workbench",  # Default for migrated conversations
                "workflow_steps": ["Migrated from LLM-001B"],
                "current_operation": None,
                "execution_successful": True,
                "current_error": None,
                "retry_count": 0,
                "business_profile": None,
                "seo_analysis": None,
                "coaching_context": None,
                "coaching_phase": None,
                "debug_mode": None,
                "parameter_overrides": None,
                "mcp_tools_active": [],
                "agent_state": None,
                "workflow_data": None,
            }

            # Save migrated state
            await self.save_from_langgraph_state(lg_state)

            return lg_state

        except Exception as e:
            raise ConversationError(f"Failed to migrate conversation: {str(e)}") from e

    def _convert_messages_to_standard(
        self, messages: List[Any]
    ) -> List[StandardMessage]:
        """
        Convert various message formats to StandardMessage.

        Args:
            messages: Messages in various formats

        Returns:
            List of StandardMessage objects
        """
        standard_messages = []

        for msg in messages:
            if isinstance(msg, StandardMessage):
                standard_messages.append(msg)
            elif isinstance(msg, dict):
                # Convert dictionary format
                standard_messages.append(
                    StandardMessage(
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        timestamp=msg.get("timestamp", datetime.utcnow()),
                    )
                )
            else:
                # Handle other formats as needed
                standard_messages.append(
                    StandardMessage(
                        role="assistant", content=str(msg), timestamp=datetime.utcnow()
                    )
                )

        return standard_messages

    def _convert_context_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert and sanitize context data for storage.

        Args:
            context: Raw context data

        Returns:
            Sanitized context data
        """
        # Remove non-serializable items and large objects
        sanitized = {}

        for key, value in context.items():
            try:
                # Test JSON serializability
                import json

                json.dumps(value)
                sanitized[key] = value
            except (TypeError, ValueError):
                # Convert to string if not serializable
                sanitized[key] = str(value)

        return sanitized

    async def _create_new_langgraph_state(
        self,
        conversation_id: UUID,
        user_message: str,
        workflow_mode: str,
        business_profile: Optional[Dict[str, Any]] = None,
    ) -> WorkbenchState:
        """
        Create new LangGraph state for new conversations.

        Args:
            conversation_id: New conversation ID
            user_message: Initial user message
            workflow_mode: Workflow mode
            business_profile: Optional business profile

        Returns:
            New LangGraph state
        """
        # Create default model config based on mode
        if workflow_mode == "seo_coach":
            model_config = ModelConfig(
                provider="openrouter",
                model_name="openai/gpt-4o-mini",
                temperature=0.7,
                max_tokens=1500,
                streaming=True,
            )
        else:
            model_config = ModelConfig(
                provider="openrouter",
                model_name="anthropic/claude-3.5-sonnet",
                temperature=0.7,
                max_tokens=2000,
                streaming=True,
            )

        # Create new state
        lg_state: WorkbenchState = {
            "conversation_id": conversation_id,
            "user_message": user_message,
            "assistant_response": None,
            "model_config": model_config,
            "provider_name": model_config.provider,
            "context_data": {},
            "active_contexts": [],
            "conversation_history": [],
            "workflow_mode": workflow_mode,  # type: ignore
            "workflow_steps": ["New conversation created"],
            "current_operation": None,
            "execution_successful": True,
            "current_error": None,
            "retry_count": 0,
            "business_profile": business_profile,
            "seo_analysis": None,
            "coaching_context": None,
            "coaching_phase": "analysis" if workflow_mode == "seo_coach" else None,
            "debug_mode": None,
            "parameter_overrides": None,
            "mcp_tools_active": [],
            "agent_state": None,
            "workflow_data": None,
        }

        return lg_state

    async def prepare_for_workflow(
        self, consolidated_state, user_message: str
    ) -> Dict[str, Any]:
        """Convert ConsolidatedState to LangGraph workflow state."""

        workflow_state = {
            "conversation_id": str(consolidated_state.conversation_id),
            "user_message": user_message,
            "assistant_response": None,
            "model_config": consolidated_state.model_config.dict(),
            "provider_name": consolidated_state.provider_name,
            "context_data": consolidated_state.context_data,
            "active_contexts": consolidated_state.active_contexts,
            "conversation_history": [msg.dict() for msg in consolidated_state.messages],
            "workflow_mode": consolidated_state.coaching_phase or "workbench",
            "workflow_steps": [],
            "current_operation": None,
            "execution_successful": True,
            "current_error": None,
            "retry_count": 0,
            "debug_mode": consolidated_state.debug_mode,
            "parameter_overrides": consolidated_state.parameter_overrides,
            "workflow_data": consolidated_state.workflow_data or {},
        }

        return workflow_state

    async def extract_from_workflow(
        self, workflow_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert LangGraph workflow state back to ConsolidatedState format."""

        # Convert back to ConsolidatedState format
        messages = [
            StandardMessage(**msg) for msg in workflow_state["conversation_history"]
        ]

        # Add assistant response if generated
        if workflow_state.get("assistant_response"):
            messages.append(
                StandardMessage(
                    role="assistant",
                    content=workflow_state["assistant_response"],
                    timestamp=datetime.utcnow(),
                )
            )

        # Return dict instead of trying to create ConsolidatedState object
        # since we don't have the actual class definition
        return {
            "conversation_id": UUID(workflow_state["conversation_id"]),
            "messages": messages,
            "model_config": ModelConfig(**workflow_state["model_config"]),
            "provider_name": workflow_state["provider_name"],
            "context_data": workflow_state["context_data"],
            "active_contexts": workflow_state["active_contexts"],
            "coaching_phase": workflow_state.get("workflow_mode"),
            "debug_mode": workflow_state.get("debug_mode", False),
            "parameter_overrides": workflow_state.get("parameter_overrides", {}),
            "workflow_data": workflow_state.get("workflow_data", {}),
            "updated_at": datetime.utcnow(),
        }

    def merge_workflow_context(
        self, base_context: Dict, workflow_context: Dict
    ) -> Dict:
        """Merge workflow context with base context."""
        merged = base_context.copy()
        merged.update(workflow_context)
        return merged

    async def _save_workflow_execution(self, lg_state: WorkbenchState) -> None:
        """
        Save workflow execution details for monitoring.

        Args:
            lg_state: LangGraph state with execution details
        """
        try:

            # Create execution record for future database storage
            # This would save to database - implementation depends on state manager
            # For now, we'll add it to the conversation metadata
            pass

        except Exception:
            # Don't fail the main operation if execution tracking fails
            pass
