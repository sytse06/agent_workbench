"""Simple LangGraph workflow for direct chat endpoint.

Provides a minimal 2-node workflow to maintain PRD's "All through LangGraph"
architecture while providing lightweight chat functionality for testing/debugging.
"""

import logging
from typing import Any, Dict, Optional, TypedDict

from langgraph.graph import StateGraph

from ..models.schemas import ModelConfig
from ..services.llm_service import ChatService

logger = logging.getLogger(__name__)


class SimpleChatState(TypedDict):
    """Minimal state for simple chat workflow.

    This is a lightweight workflow state with only essential fields,
    maintaining LangGraph architecture without full workbench complexity.
    """

    user_message: str
    assistant_response: str
    model_config: ModelConfig
    execution_successful: bool
    error_message: Optional[str]


class SimpleChatWorkflow:
    """Minimal LangGraph workflow for direct chat.

    Implements a 2-node workflow:
    1. process_input: Prepare user message
    2. generate_response: Get LLM response

    This maintains PRD's "All through LangGraph" requirement while
    providing the lightweight functionality needed for testing/debugging.

    Examples:
        >>> workflow = SimpleChatWorkflow(model_config)
        >>> result = await workflow.execute("Hello, how are you?")
        >>> print(result["assistant_response"])
    """

    def __init__(self, model_config: ModelConfig):
        """Initialize simple chat workflow.

        Args:
            model_config: Model configuration for LLM
        """
        self.model_config = model_config
        self.llm_service = ChatService(model_config)
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build minimal 2-node LangGraph workflow.

        Returns:
            Compiled StateGraph workflow
        """
        # Create state graph
        builder = StateGraph(SimpleChatState)

        # Add nodes
        builder.add_node("process_input", self._process_input_node)
        builder.add_node("generate_response", self._generate_response_node)

        # Add edges
        builder.add_edge("process_input", "generate_response")
        builder.set_entry_point("process_input")
        builder.set_finish_point("generate_response")

        return builder.compile()

    async def _process_input_node(self, state: SimpleChatState) -> SimpleChatState:
        """Process user input (Node 1).

        Minimal processing - just validates message exists.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        logger.info("🔄 Simple workflow: Processing input...")

        if not state.get("user_message"):
            logger.error("❌ No user message provided")
            return {
                **state,
                "execution_successful": False,
                "error_message": "No user message provided",
            }

        logger.info(f"✅ Input processed: {state['user_message'][:50]}...")
        return state

    async def _generate_response_node(self, state: SimpleChatState) -> SimpleChatState:
        """Generate LLM response (Node 2).

        Calls LLM service to get response.

        Args:
            state: Current workflow state

        Returns:
            Updated state with assistant response
        """
        logger.info("🤖 Simple workflow: Generating response...")

        try:
            # Get LLM response
            response = await self.llm_service.chat_completion(
                message=state["user_message"],
                conversation_id=None,  # No conversation persistence
            )

            logger.info(f"✅ Response generated: {response.reply[:50]}...")

            return {
                **state,
                "assistant_response": response.reply,
                "execution_successful": True,
                "error_message": None,
            }

        except Exception as e:
            logger.error(f"❌ Response generation failed: {str(e)}")
            return {
                **state,
                "assistant_response": "",
                "execution_successful": False,
                "error_message": str(e),
            }

    async def execute(self, user_message: str) -> Dict[str, Any]:
        """Execute simple chat workflow.

        Args:
            user_message: User's message

        Returns:
            Final workflow state as dictionary

        Raises:
            Exception: If workflow execution fails
        """
        logger.info("🚀 Executing simple chat workflow...")

        # Create initial state
        initial_state: SimpleChatState = {
            "user_message": user_message,
            "assistant_response": "",
            "model_config": self.model_config,
            "execution_successful": False,
            "error_message": None,
        }

        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state)

        logger.info(
            "✅ Simple workflow completed: "
            f"success={final_state['execution_successful']}"
        )

        return final_state
