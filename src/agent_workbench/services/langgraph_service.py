"""Main LangGraph workflow orchestration service."""

from typing import Any, Dict
from uuid import UUID

from langgraph.graph import END, START, StateGraph

from ..models.state_requests import ChatRequest, ChatResponse
from ..services.context_service import ContextService
from ..services.langgraph_bridge import LangGraphStateBridge
from ..services.llm_service import ChatService
from ..services.workflow_nodes import WorkflowNodes


class WorkbenchLangGraphService:
    """Main LangGraph workflow orchestration service for workbench mode."""

    def __init__(
        self,
        state_bridge: LangGraphStateBridge,
        llm_service: ChatService,
        context_service: ContextService,
    ):
        """
        Initialize LangGraph workflow service.

        Args:
            state_bridge: State bridge for conversion between formats
            llm_service: LLM service for chat completion
            context_service: Context service for conversation management
        """
        self.state_bridge = state_bridge
        self.llm_service = llm_service
        self.context_service = context_service
        self.workflow_nodes = WorkflowNodes(state_bridge, llm_service, context_service)
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build LangGraph workflow using existing WorkbenchState.

        Returns:
            Configured StateGraph workflow
        """
        builder = StateGraph(dict)  # Use dict to align with existing WorkbenchState

        # Core workflow nodes
        builder.add_node(
            "load_conversation", self.workflow_nodes.load_conversation_node
        )
        builder.add_node("process_message", self.workflow_nodes.process_message_node)
        builder.add_node(
            "generate_response", self.workflow_nodes.generate_response_node
        )
        builder.add_node("save_state", self.workflow_nodes.save_state_node)
        builder.add_node("handle_error", self.workflow_nodes.handle_error_node)

        # Workflow routing
        builder.add_edge(START, "load_conversation")
        builder.add_edge("load_conversation", "process_message")
        builder.add_edge("process_message", "generate_response")
        builder.add_edge("generate_response", "save_state")
        builder.add_edge("save_state", END)

        # Error handling
        builder.add_edge("handle_error", END)

        return builder.compile()

    async def execute_chat_workflow(self, request: ChatRequest) -> ChatResponse:
        """
        Execute chat workflow through LangGraph.

        Args:
            request: Chat request with conversation context

        Returns:
            Chat response with assistant reply
        """
        # Create initial workflow state
        initial_state = self._create_initial_state(request)

        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state)

        # Handle any errors
        if final_state.get("current_error"):
            # In a real implementation, you might want to raise an exception
            # For now, we'll return the error in the response
            pass

        # Return response
        return ChatResponse(
            content=final_state.get("assistant_response", ""),
            conversation_id=UUID(final_state["conversation_id"]),
            model_used=final_state.get("provider_name", "unknown"),
            metadata={
                "workflow_steps": final_state.get("workflow_steps", []),
                "execution_successful": final_state.get("execution_successful", False),
                "error": final_state.get("current_error"),
            },
        )

    async def stream_chat_workflow(self, request: ChatRequest) -> Any:
        """
        Stream chat workflow through LangGraph.

        Args:
            request: Chat request with conversation context

        Yields:
            Streaming response chunks
        """
        # This would implement streaming logic
        # For now, we'll delegate to the regular workflow
        response = await self.execute_chat_workflow(request)
        yield response.content

    def _create_initial_state(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Create initial workflow state from request.

        Args:
            request: Chat request

        Returns:
            Initial workflow state dictionary
        """
        return {
            "conversation_id": (
                str(request.conversation_id) if request.conversation_id else None
            ),
            "user_message": request.message,
            "assistant_response": None,
            "model_config": (
                request.model_config.dict() if request.model_config else None
            ),
            "provider_name": (
                request.model_config.provider if request.model_config else None
            ),
            "context_data": request.context_data if request.context_data else {},
            "active_contexts": [],
            "conversation_history": [],
            "workflow_mode": "workbench",
            "workflow_steps": ["Workflow initialized"],
            "current_operation": "chat_completion",
            "execution_successful": True,
            "current_error": None,
            "retry_count": 0,
            # Phase 2 placeholders
            "mcp_tools_active": [],
            "agent_state": None,
            "workflow_data": None,
        }


# Dependency injection for FastAPI
async def get_langgraph_service() -> WorkbenchLangGraphService:
    """
    Get initialized LangGraph service instance.

    Returns:
        LangGraph service instance
    """
    # This would be implemented with proper dependency injection
    # For now, we'll create a basic implementation
    # In a real implementation, this would use the existing service dependencies
    raise NotImplementedError("Service initialization not implemented yet")
