"""LangGraph workflow service — mode-independent execution engine."""

import logging
from typing import Optional

from langgraph.graph import END, START, StateGraph

from ..models.consolidated_state import WorkbenchState
from ..models.schemas import ModelConfig
from .agent_service import AgentService
from .context_service import ContextService
from .langgraph_bridge import LangGraphStateBridge
from .mode_handlers import SEOCoachModeHandler, WorkbenchModeHandler

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = ModelConfig(
    provider="openrouter",
    model_name="anthropic/claude-3.5-sonnet",
    temperature=0.7,
    max_tokens=2000,
)


class LangGraphService:
    """Mode-independent LangGraph workflow service.

    Replaces WorkflowOrchestrator. Both workbench and seo_coach modes route
    through this single service. Mode-specific logic (prompts, Dutch language,
    coaching phases) stays in the mode handlers.

    Nodes:
        load_conversation → validate_input → detect_intent
            → [workbench | seo_coach] → generate_response → save_state → END
        handle_error → save_state → END
    """

    def __init__(
        self,
        state_bridge: LangGraphStateBridge,
        agent_service: AgentService,
        context_service: ContextService,
        model_config: Optional[ModelConfig] = None,
    ) -> None:
        self.state_bridge = state_bridge
        self.agent_service = agent_service
        self.context_service = context_service
        self.workbench_handler = WorkbenchModeHandler(agent_service, context_service)
        self.seo_coach_handler = SEOCoachModeHandler(agent_service, context_service)
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        builder = StateGraph(WorkbenchState)

        builder.add_node("load_conversation", self._load_conversation_node)
        builder.add_node("validate_input", self._validate_input_node)
        builder.add_node("detect_intent", self._detect_intent_node)
        builder.add_node("process_workbench", self._process_workbench_node)
        builder.add_node("process_seo_coach", self._process_seo_coach_node)
        builder.add_node("generate_response", self._generate_response_node)
        builder.add_node("save_state", self._save_state_node)
        builder.add_node("handle_error", self._handle_error_node)

        builder.add_edge(START, "load_conversation")
        builder.add_edge("load_conversation", "validate_input")
        builder.add_edge("validate_input", "detect_intent")

        builder.add_conditional_edges(
            "detect_intent",
            self._route_by_mode,
            {
                "workbench": "process_workbench",
                "seo_coach": "process_seo_coach",
                "error": "handle_error",
            },
        )

        builder.add_edge("process_workbench", "generate_response")
        builder.add_edge("process_seo_coach", "generate_response")
        builder.add_edge("generate_response", "save_state")
        builder.add_edge("save_state", END)
        builder.add_edge("handle_error", "save_state")

        return builder.compile()

    # --- nodes ---

    async def _load_conversation_node(
        self, state: WorkbenchState
    ) -> WorkbenchState:
        try:
            loaded = await self.state_bridge.load_into_langgraph_state(
                conversation_id=state["conversation_id"],
                user_message=state["user_message"],
                workflow_mode=state["workflow_mode"],
                business_profile=state.get("business_profile"),
            )
            # loaded overrides initial state so DB history wins over empty []
            merged = {**state, **loaded}
            merged["workflow_steps"] = state.get("workflow_steps", []) + [
                "Conversation loaded"
            ]
            return WorkbenchState(**merged)  # type: ignore[return-value]

        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return {
                **state,
                "current_error": f"Conversation loading failed: {e}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Load error: {e}"],
            }

    async def _validate_input_node(self, state: WorkbenchState) -> WorkbenchState:
        if not state.get("user_message", "").strip():
            return {
                **state,
                "current_error": "Empty user message",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + ["Validation failed: empty message"],
            }

        mode = state.get("workflow_mode", "workbench")
        if mode not in ("workbench", "seo_coach"):
            return {
                **state,
                "current_error": f"Invalid workflow mode: {mode}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Validation failed: invalid mode {mode}"],
            }

        return {
            **state,
            "workflow_steps": state.get("workflow_steps", [])
            + ["Input validation passed"],
        }

    async def _detect_intent_node(self, state: WorkbenchState) -> WorkbenchState:
        mode = state.get("workflow_mode", "workbench")
        return {
            **state,
            "workflow_steps": state.get("workflow_steps", [])
            + [f"Intent detected: {mode}"],
        }

    async def _process_workbench_node(self, state: WorkbenchState) -> WorkbenchState:
        try:
            return await self.workbench_handler.process_message(state)
        except Exception as e:
            logger.error(f"Workbench processing failed: {e}")
            return {
                **state,
                "current_error": f"Workbench processing failed: {e}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Workbench error: {e}"],
            }

    async def _process_seo_coach_node(self, state: WorkbenchState) -> WorkbenchState:
        try:
            return await self.seo_coach_handler.process_message(state)
        except Exception as e:
            logger.error(f"SEO coach processing failed: {e}")
            return {
                **state,
                "current_error": f"SEO coach processing failed: {e}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"SEO coach error: {e}"],
            }

    async def _generate_response_node(self, state: WorkbenchState) -> WorkbenchState:
        if not state.get("assistant_response"):
            return {
                **state,
                "current_error": "No response generated by mode handler",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + ["Response generation failed: no response from handler"],
            }
        return {
            **state,
            "current_operation": "Response finalized",
            "workflow_steps": state.get("workflow_steps", [])
            + ["Response generated successfully"],
        }

    async def _save_state_node(self, state: WorkbenchState) -> WorkbenchState:
        try:
            await self.state_bridge.save_from_langgraph_state(state)
            return {
                **state,
                "current_operation": "State saved",
                "workflow_steps": state.get("workflow_steps", [])
                + ["State saved to persistence"],
            }
        except Exception as e:
            logger.error(f"State saving failed: {e}")
            return {
                **state,
                "current_error": f"State saving failed: {e}",
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Save error: {e}"],
            }

    async def _handle_error_node(self, state: WorkbenchState) -> WorkbenchState:
        error_msg = state.get("current_error", "Unknown error")
        retry_count = state.get("retry_count", 0)

        if state.get("workflow_mode") == "seo_coach":
            fallback = (
                f"Excuses, er ging iets mis tijdens het verwerken van je SEO vraag.\n\n"
                f"Fout: {error_msg}\n\n"
                f"Probeer het opnieuw, of stel je vraag anders. "
                f"Ik help je graag met SEO advies voor je bedrijf."
            )
        else:
            fallback = (
                f"An error occurred while processing your request.\n"
                f"Error: {error_msg}\n\n"
                f"Please try again or rephrase your question."
            )

        return {
            **state,
            "assistant_response": fallback,
            "execution_successful": False,
            "retry_count": retry_count + 1,
            "current_operation": "Error handled",
            "workflow_steps": state.get("workflow_steps", [])
            + [f"Error handled: {error_msg}"],
        }

    def _route_by_mode(self, state: WorkbenchState) -> str:
        if state.get("current_error"):
            return "error"
        mode = state.get("workflow_mode", "workbench")
        if mode in ("workbench", "seo_coach"):
            return mode
        return "error"

    async def execute_workflow(self, initial_state: WorkbenchState) -> WorkbenchState:
        try:
            result = await self.workflow.ainvoke(initial_state)
            return WorkbenchState(**result)  # type: ignore[return-value]
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                **initial_state,
                "current_error": f"Workflow execution failed: {e}",
                "execution_successful": False,
                "assistant_response": "Workflow execution failed. Please try again.",
                "workflow_steps": initial_state.get("workflow_steps", [])
                + [f"Workflow execution failed: {e}"],
            }

    async def save_turn(
        self,
        state: WorkbenchState,
    ) -> None:
        """Persist state after a streaming turn completes."""
        try:
            await self.state_bridge.save_from_langgraph_state(state)
        except Exception as e:
            logger.error(f"save_turn failed: {e}")
