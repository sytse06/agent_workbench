"""LangGraph workflow orchestrator for unified dual-mode operation."""

import logging

from langgraph.graph import END, START, StateGraph

from ..models.consolidated_state import WorkbenchState
from .langgraph_bridge import LangGraphStateBridge
from .mode_handlers import SEOCoachModeHandler, WorkbenchModeHandler

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """LangGraph workflow orchestrator supporting both modes."""

    def __init__(
        self,
        state_bridge: LangGraphStateBridge,
        workbench_handler: WorkbenchModeHandler,
        seo_coach_handler: SEOCoachModeHandler,
    ):
        """
        Initialize workflow orchestrator.

        Args:
            state_bridge: Bridge for state persistence
            workbench_handler: Workbench mode processor
            seo_coach_handler: SEO coach mode processor
        """
        self.state_bridge = state_bridge
        self.workbench_handler = workbench_handler
        self.seo_coach_handler = seo_coach_handler
        self.workflow = self._build_consolidated_workflow()

    def _build_consolidated_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow supporting both workbench and seo_coach modes.

        Returns:
            Compiled StateGraph workflow
        """
        builder = StateGraph(WorkbenchState)

        # Core workflow nodes
        builder.add_node("load_conversation", self._load_conversation_node)
        builder.add_node("validate_input", self._validate_input_node)
        builder.add_node("detect_intent", self._detect_intent_node)
        builder.add_node("process_workbench", self._process_workbench_node)
        builder.add_node("process_seo_coach", self._process_seo_coach_node)
        builder.add_node("generate_response", self._generate_response_node)
        builder.add_node("save_state", self._save_state_node)
        builder.add_node("handle_error", self._handle_error_node)

        # Workflow routing
        builder.add_edge(START, "load_conversation")
        builder.add_edge("load_conversation", "validate_input")
        builder.add_edge("validate_input", "detect_intent")

        # Conditional routing by mode
        builder.add_conditional_edges(
            "detect_intent",
            self._route_by_mode,
            {
                "workbench": "process_workbench",
                "seo_coach": "process_seo_coach",
                "error": "handle_error",
            },
        )

        # Both modes converge at response generation
        builder.add_edge("process_workbench", "generate_response")
        builder.add_edge("process_seo_coach", "generate_response")
        builder.add_edge("generate_response", "save_state")
        builder.add_edge("save_state", END)

        # Error handling
        builder.add_edge("handle_error", "save_state")

        return builder.compile()

    async def _load_conversation_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Load conversation data and initialize state.

        Args:
            state: Current workflow state

        Returns:
            Updated state with conversation data
        """
        try:
            # State bridge handles loading from LLM-001B persistence
            updated_state = await self.state_bridge.load_into_langgraph_state(
                conversation_id=state["conversation_id"],
                user_message=state["user_message"],
                workflow_mode=state["workflow_mode"],
                business_profile=state.get("business_profile"),
            )

            # Merge with current state, preserving new data
            merged_state = {**updated_state, **state}
            merged_state["workflow_steps"] = state.get("workflow_steps", []) + [
                "Conversation loaded"
            ]

            return WorkbenchState(**merged_state)  # type: ignore

        except Exception as e:
            logger.error(f"Failed to load conversation: {str(e)}")
            return {
                **state,
                "current_error": f"Conversation loading failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Load error: {str(e)}"],
            }

    async def _validate_input_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Validate input data and workflow requirements.

        Args:
            state: Current workflow state

        Returns:
            Updated state with validation results
        """
        try:
            # Basic validation
            if not state.get("user_message", "").strip():
                return {
                    **state,
                    "current_error": "Empty user message",
                    "execution_successful": False,
                    "workflow_steps": state.get("workflow_steps", [])
                    + ["Validation failed: empty message"],
                }

            # Mode-specific validation
            workflow_mode = state.get("workflow_mode", "workbench")
            if workflow_mode not in ["workbench", "seo_coach"]:
                return {
                    **state,
                    "current_error": f"Invalid workflow mode: {workflow_mode}",
                    "execution_successful": False,
                    "workflow_steps": state.get("workflow_steps", [])
                    + [f"Validation failed: invalid mode {workflow_mode}"],
                }

            # SEO coach specific validation
            if workflow_mode == "seo_coach":
                # Business profile validation could be added here
                pass

            return {
                **state,
                "workflow_steps": state.get("workflow_steps", [])
                + ["Input validation passed"],
            }

        except Exception as e:
            logger.error(f"Input validation failed: {str(e)}")
            return {
                **state,
                "current_error": f"Validation error: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Validation error: {str(e)}"],
            }

    async def _detect_intent_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Detect user intent and prepare for mode-specific processing.

        Args:
            state: Current workflow state

        Returns:
            Updated state with intent analysis
        """
        try:
            workflow_mode = state.get("workflow_mode", "workbench")
            # Intent detection logic could be enhanced here
            # For now, we'll add the mode to workflow steps for tracking
            workflow_steps = state.get("workflow_steps", [])
            workflow_steps.append(f"Intent detected: {workflow_mode}")

            return {**state, "workflow_steps": workflow_steps}

        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return {
                **state,
                "current_error": f"Intent detection failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Intent detection error: {str(e)}"],
            }

    async def _process_workbench_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Process message using workbench mode handler.

        Args:
            state: Current workflow state

        Returns:
            Updated state with workbench processing results
        """
        try:
            return await self.workbench_handler.process_message(state)
        except Exception as e:
            logger.error(f"Workbench processing failed: {str(e)}")
            return {
                **state,
                "current_error": f"Workbench processing failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Workbench error: {str(e)}"],
            }

    async def _process_seo_coach_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Process message using SEO coach mode handler.

        Args:
            state: Current workflow state

        Returns:
            Updated state with SEO coaching results
        """
        try:
            return await self.seo_coach_handler.process_message(state)
        except Exception as e:
            logger.error(f"SEO coach processing failed: {str(e)}")
            return {
                **state,
                "current_error": f"SEO coach processing failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"SEO coach error: {str(e)}"],
            }

    async def _generate_response_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Finalize response generation and add metadata.

        Args:
            state: Current workflow state

        Returns:
            Updated state with finalized response
        """
        try:
            # Response should already be generated by mode handlers
            if not state.get("assistant_response"):
                return {
                    **state,
                    "current_error": "No response generated by mode handler",
                    "execution_successful": False,
                    "workflow_steps": state.get("workflow_steps", [])
                    + ["Response generation failed: no response from handler"],
                }

            # Add response metadata
            return {
                **state,
                "current_operation": "Response finalized",
                "workflow_steps": state.get("workflow_steps", [])
                + ["Response generated successfully"],
            }

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return {
                **state,
                "current_error": f"Response generation failed: {str(e)}",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Response generation error: {str(e)}"],
            }

    async def _save_state_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Save workflow state back to persistence layer.

        Args:
            state: Current workflow state

        Returns:
            Updated state with save confirmation
        """
        try:
            await self.state_bridge.save_from_langgraph_state(state)

            return {
                **state,
                "current_operation": "State saved",
                "workflow_steps": state.get("workflow_steps", [])
                + ["State saved to persistence"],
            }

        except Exception as e:
            logger.error(f"State saving failed: {str(e)}")
            return {
                **state,
                "current_error": f"State saving failed: {str(e)}",
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Save error: {str(e)}"],
            }

    async def _handle_error_node(self, state: WorkbenchState) -> WorkbenchState:
        """
        Handle workflow errors and prepare fallback response.

        Args:
            state: Current workflow state with error

        Returns:
            Updated state with error handling
        """
        try:
            error_msg = state.get("current_error", "Unknown error")
            retry_count = state.get("retry_count", 0)

            # Prepare fallback response
            if state.get("workflow_mode") == "seo_coach":
                fallback_response = f"""Excuses, er ging iets mis tijdens het
verwerken van je SEO vraag.

Fout: {error_msg}

Probeer het opnieuw, of stel je vraag anders. Ik help je graag met
SEO advies voor je bedrijf."""
            else:
                fallback_response = f"""An error occurred while processing your request.
Error: {error_msg}
Please try again or rephrase your question. I'm here to help with your
technical workflow needs."""

            return {
                **state,
                "assistant_response": fallback_response,
                "execution_successful": False,
                "retry_count": retry_count + 1,
                "current_operation": "Error handled",
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Error handled: {error_msg}"],
            }

        except Exception as e:
            logger.error(f"Error handling failed: {str(e)}")
            return {
                **state,
                "assistant_response": "A critical error occurred. Please try again.",
                "execution_successful": False,
                "workflow_steps": state.get("workflow_steps", [])
                + [f"Critical error in error handler: {str(e)}"],
            }

    def _route_by_mode(self, state: WorkbenchState) -> str:
        """
        Route workflow based on mode and validation.

        Args:
            state: Current workflow state

        Returns:
            Next node name
        """
        if state.get("current_error"):
            return "error"

        workflow_mode = state.get("workflow_mode", "workbench")
        if workflow_mode in ["workbench", "seo_coach"]:
            return workflow_mode

        return "error"

    async def execute_workflow(self, initial_state: WorkbenchState) -> WorkbenchState:
        """
        Execute the complete workflow from start to end.

        Args:
            initial_state: Initial workflow state

        Returns:
            Final workflow state
        """
        try:
            result = await self.workflow.ainvoke(initial_state)
            return WorkbenchState(**result)  # type: ignore
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            return {
                **initial_state,
                "current_error": f"Workflow execution failed: {str(e)}",
                "execution_successful": False,
                "assistant_response": "Workflow execution failed. Please try again.",
                "workflow_steps": initial_state.get("workflow_steps", [])
                + [f"Workflow execution failed: {str(e)}"],
            }
