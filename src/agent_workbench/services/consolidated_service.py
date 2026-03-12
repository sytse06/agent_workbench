"""Main consolidated service integrating LLM-001B with LangGraph workflows."""

import asyncio
import logging
import os
import time
from typing import Any, Dict, Literal, Optional, Union
from uuid import UUID, uuid4

import aiosqlite
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from sqlalchemy.ext.asyncio import AsyncSession

from ..api.database import get_session
from ..core.exceptions import ConversationError
from ..models.consolidated_state import (
    ConsolidatedWorkflowRequest,
    ConsolidatedWorkflowResponse,
    WorkbenchState,
)
from ..models.schemas import ModelConfig
from .agent_graph import AgentGraph
from .agent_service import AgentResponse, AgentService, _split_think_tags
from .context_service import ContextService
from .conversation_service import ConversationService
from .langgraph_bridge import LangGraphStateBridge
from .langgraph_service import LangGraphService
from .mode_detector import ModeDetector
from .state_manager import StateManager

logger = logging.getLogger(__name__)

# Module-level checkpointer. Starts as MemorySaver (in-process only).
# init_checkpointer() swaps it to AsyncSqliteSaver at app startup for
# cross-restart persistence. Falls back to MemorySaver on init failure.
_checkpointer: BaseCheckpointSaver = MemorySaver()
_checkpointer_conn: Optional[aiosqlite.Connection] = None

# Module-level EmbeddingService singleton. Lazy-loads all-MiniLM-L6-v2 (~80MB)
# on first embed() call. Shared across all requests — stateless after init.
from .embedding_service import EmbeddingService  # noqa: E402

_embedding_service: EmbeddingService = EmbeddingService()


async def init_checkpointer(
    db_path: str = "data/langgraph_checkpoints.db",
) -> None:
    """Open AsyncSqliteSaver at app startup. Call from FastAPI lifespan."""
    global _checkpointer, _checkpointer_conn
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    _checkpointer_conn = await aiosqlite.connect(db_path)
    saver = AsyncSqliteSaver(_checkpointer_conn)
    await saver.setup()
    _checkpointer = saver
    logger.info("LangGraph AsyncSqliteSaver initialized at %s", db_path)


async def close_checkpointer() -> None:
    """Close the checkpointer connection at app shutdown."""
    global _checkpointer_conn
    if _checkpointer_conn is not None:
        await _checkpointer_conn.close()
        _checkpointer_conn = None
        logger.info("LangGraph checkpointer connection closed")


class ConsolidatedWorkbenchService:
    """Main service integrating LLM-001B persistence with LangGraph workflows."""

    def __init__(self) -> None:
        """Initialize consolidated workbench service."""
        # Core LLM-001B components (preserved)
        self.default_model_config = ModelConfig(
            provider="openrouter",
            model_name="anthropic/claude-3.5-sonnet",
            temperature=0.7,
            max_tokens=2000,
        )

        # Initialize dependencies (will be injected at runtime)
        self.db_session: Optional[AsyncSession] = None
        self.state_manager: Optional[StateManager] = None
        self.conversation_service: Optional[ConversationService] = None
        self.context_service: Optional[ContextService] = None

        # LangGraph orchestration components
        self.state_bridge: Optional[LangGraphStateBridge] = None
        self.mode_detector: Optional[ModeDetector] = None
        self.agent_service: Optional[AgentService] = None
        self.lang_graph_service: Optional[LangGraphService] = None
        self.agent_graph: Optional[AgentGraph] = None
        self.file_processing_service: Optional[Any] = None

    def _ensure_uuid(
        self, conversation_id: Optional[Union[UUID, str]]
    ) -> Optional[UUID]:
        """Convert string UUID to UUID object if needed."""
        if conversation_id is None:
            return None
        if isinstance(conversation_id, str):
            try:
                return UUID(conversation_id)
            except ValueError:
                logger.warning(f"Invalid UUID string: {conversation_id}")
                return None
        return conversation_id

    async def initialize(self, db_session: AsyncSession) -> None:
        """
        Initialize service with database session and dependencies.

        Args:
            db_session: Database session for operations
        """
        self.db_session = db_session

        # Core components
        self.state_manager = StateManager(db_session)
        self.conversation_service = ConversationService()
        self.context_service = ContextService()

        # Agent + LangGraph service
        from .content_retriever_tool import ContentRetrieverTool

        retriever = ContentRetrieverTool(
            session_factory=get_session,
            model_config=self.default_model_config,
            embedding_service=_embedding_service,
        )
        self.agent_service = AgentService(self.default_model_config)
        self.agent_graph = AgentGraph(
            self.default_model_config,
            tools=[retriever],
            checkpointer=_checkpointer,
        )
        self.state_bridge = LangGraphStateBridge(
            self.state_manager, self.context_service
        )
        self.mode_detector = ModeDetector(db_session)
        self.lang_graph_service = LangGraphService(
            state_bridge=self.state_bridge,
            agent_service=self.agent_service,
            context_service=self.context_service,
            agent_graph=self.agent_graph,
        )

        # File processing service
        from .docling_service import _docling_service
        from .file_processing_service import FileProcessingService

        self.file_processing_service = FileProcessingService(docling=_docling_service)

    async def execute_workflow(
        self, request: ConsolidatedWorkflowRequest
    ) -> ConsolidatedWorkflowResponse:
        """
        Execute consolidated workflow for both workbench and seo_coach modes.

        Args:
            request: Consolidated workflow request

        Returns:
            Consolidated workflow response

        Raises:
            ConversationError: If workflow execution fails
            LLMProviderError: If LLM processing fails
        """
        try:
            logger.info("🎯 DEBUG: Starting workflow execution")
            _start_time = time.monotonic()

            # Convert conversation_id to UUID if it's a string
            conversation_id = self._ensure_uuid(request.conversation_id)
            logger.info(f"🎯 DEBUG: Conversation ID: {conversation_id}")

            # Determine effective workflow mode
            effective_mode = (
                await self.mode_detector.get_effective_mode(
                    conversation_id=conversation_id,
                    requested_mode=request.workflow_mode,
                    request_data=request.model_dump(),
                )
                if self.mode_detector
                else "workbench"
            )
            logger.info(f"🎯 DEBUG: Effective workflow mode: {effective_mode}")

            # Create or use existing conversation
            if not conversation_id:
                logger.info("🎯 DEBUG: Creating new conversation")
                conversation_id = await self._create_conversation(
                    request, effective_mode
                )
                logger.info(f"🎯 DEBUG: Created conversation: {conversation_id}")

            # Process pending files if any
            if request.pending_files and self.file_processing_service:
                context_parts = []
                filenames = []
                for file_info in request.pending_files:
                    if isinstance(file_info, str):
                        file_path = file_info
                        filename = os.path.basename(file_info)
                    else:
                        file_path = file_info.get("path") or file_info.get("name", "")
                        filename = file_info.get("orig_name") or file_info.get(
                            "name", "document"
                        )
                    if not file_path:
                        continue
                    try:
                        chunks = await asyncio.to_thread(
                            self.file_processing_service.convert, file_path
                        )
                        context_block = (
                            await self.file_processing_service.save_and_build_context(
                                chunks, filename, str(conversation_id), self.db_session
                            )
                        )
                        if context_block:
                            context_parts.append(
                                f"=== Document: {filename} ===\n{context_block}"
                            )
                            filenames.append(filename)
                    except Exception as e:
                        logger.error(f"File processing failed for {filename}: {e}")
                if context_parts:
                    request = request.model_copy(
                        update={
                            "document_context": "\n\n".join(context_parts),
                            "document_filename": ", ".join(filenames),
                        }
                    )

            # Prepare initial workflow state
            logger.info("🎯 DEBUG: Preparing initial workflow state")
            initial_state = await self._prepare_initial_state(
                request, conversation_id, effective_mode
            )
            model_info = (
                f"{initial_state['model_config'].provider}/"
                f"{initial_state['model_config'].model_name}"
            )
            logger.info(f"🎯 DEBUG: Initial state prepared with model: {model_info}")

            # Execute LangGraph workflow
            logger.info("🎯 DEBUG: Executing LangGraph workflow")
            final_state = (
                await self.lang_graph_service.execute_workflow(initial_state)
                if self.lang_graph_service
                else initial_state
            )
            logger.info("🎯 DEBUG: Workflow execution completed")

            # CRITICAL: Ensure assistant_response is never None
            if final_state.get("assistant_response") is None:
                logger.warning(
                    "🎯 DEBUG: Assistant response is None, using direct LLM fallback"
                )
                # Direct LLM fallback when workflow fails
                final_state["assistant_response"] = await self._direct_llm_fallback(
                    request
                )
                final_state["workflow_steps"].append("Direct LLM fallback used")
                fallback_response = final_state["assistant_response"]
                fallback_len = len(fallback_response) if fallback_response else 0
                logger.info(
                    f"🎯 DEBUG: Fallback response generated: {fallback_len} chars"
                )
            else:
                assistant_response = final_state["assistant_response"]
                response_len = len(assistant_response) if assistant_response else 0
                logger.info(
                    f"🎯 DEBUG: Assistant response available: {response_len} chars"
                )

            # Convert to response format
            logger.info("🎯 DEBUG: Converting to response format")
            elapsed = time.monotonic() - _start_time
            return self._convert_to_response(final_state, duration=elapsed)

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            # Return error response instead of raising exception
            return ConsolidatedWorkflowResponse(
                conversation_id=request.conversation_id or uuid4(),
                assistant_response=f"Error: {str(e)}",
                workflow_mode=request.workflow_mode or "workbench",
                execution_successful=False,
                workflow_steps=["error"],
                context_data={},
                metadata={"error": str(e)},
            )

    async def stream_workflow(  # type: ignore[return]
        self, request: ConsolidatedWorkflowRequest
    ):
        """Stream workflow — yields event dicts (thinking_chunk, answer_chunk, done).

        State is saved after the 'done' event.
        """
        if self.agent_service is None or self.lang_graph_service is None:
            yield {"type": "answer_chunk", "content": "Service not initialized."}
            return

        conversation_id = self._ensure_uuid(request.conversation_id)
        effective_mode = (
            await self.mode_detector.get_effective_mode(
                conversation_id=conversation_id,
                requested_mode=request.workflow_mode,
                request_data=request.model_dump(),
            )
            if self.mode_detector
            else "workbench"
        )

        if not conversation_id:
            conversation_id = await self._create_conversation(request, effective_mode)

        if request.pending_files and self.file_processing_service:
            context_parts = []
            filenames = []
            for file_info in request.pending_files:
                if isinstance(file_info, str):
                    file_path = file_info
                    filename = os.path.basename(file_info)
                else:
                    file_path = file_info.get("path") or file_info.get("name", "")
                    filename = file_info.get("orig_name") or file_info.get(
                        "name", "document"
                    )
                if not file_path:
                    continue
                yield {"type": "processing_file", "filename": filename}
                try:
                    chunks = await asyncio.to_thread(
                        self.file_processing_service.convert, file_path
                    )
                    context_block = (
                        await self.file_processing_service.save_and_build_context(
                            chunks, filename, str(conversation_id), self.db_session
                        )
                    )
                    if context_block:
                        context_parts.append(
                            f"=== Document: {filename} ===\n{context_block}"
                        )
                        filenames.append(filename)
                except Exception as e:
                    logger.error(f"File processing failed for {filename}: {e}")
            if context_parts:
                request = request.model_copy(
                    update={
                        "document_context": "\n\n".join(context_parts),
                        "document_filename": ", ".join(filenames),
                    }
                )

        initial_state = await self._prepare_initial_state(
            request, conversation_id, effective_mode
        )

        # Load history into state
        try:
            if self.state_bridge is None:
                raise AttributeError("state_bridge not initialized")
            loaded = await self.state_bridge.load_into_langgraph_state(
                conversation_id=conversation_id,
                user_message=request.user_message,
                workflow_mode=effective_mode,
                business_profile=request.business_profile,
            )
            initial_state = {**initial_state, **loaded}  # type: ignore[assignment]
        except Exception:
            pass  # history load failure is non-fatal; proceed without history

        # Build messages using the appropriate mode handler
        if effective_mode == "seo_coach":
            seo_handler = self.lang_graph_service.seo_coach_handler
            model_config = seo_handler._get_dutch_coaching_config(initial_state)
            messages = await seo_handler._build_coaching_messages(
                initial_state, model_config
            )
        else:
            wb_handler = self.lang_graph_service.workbench_handler
            model_config = initial_state["model_config"]
            messages = await wb_handler._build_workbench_messages(
                initial_state, model_config
            )

        answer_acc = ""
        thinking_acc = ""
        in_think = False
        seo_model_config = model_config if effective_mode == "seo_coach" else None

        # Determine which messages to pass to AgentGraph.
        # If the checkpointer already has history for this thread (from a previous
        # turn in the same process run), pass only the new user message to avoid
        # duplicating context in MessagesState. Otherwise pass the full message list
        # built by the mode handler (first turn or after a server restart).
        thread_id = str(conversation_id) if conversation_id else None
        agent_messages = messages
        if thread_id and self.agent_graph is not None:
            existing = await self.agent_graph.get_state(thread_id)
            if existing is not None:
                from langchain_core.messages import HumanMessage as _HumanMessage

                agent_messages = [_HumanMessage(content=request.user_message)]

        if self.agent_graph is not None:
            async for chunk in self.agent_graph.astream(
                agent_messages,
                model_config=seo_model_config,
                thread_id=thread_id,
            ):
                if chunk["type"] == "messages":
                    message_chunk, _meta = chunk["data"]
                    for block in message_chunk.content_blocks:
                        block_type = block.get("type")
                        if block_type == "text":
                            text = block.get("text", "")
                            if text:
                                segments, in_think = _split_think_tags(text, in_think)
                                for seg_type, seg_text in segments:
                                    if not seg_text:
                                        continue
                                    if seg_type == "thinking":
                                        thinking_acc += seg_text
                                        yield {
                                            "type": "thinking_chunk",
                                            "content": seg_text,
                                        }
                                    else:
                                        answer_acc += seg_text
                                        yield {
                                            "type": "answer_chunk",
                                            "content": seg_text,
                                        }
                        elif block_type == "reasoning":
                            data = block.get("data", "")
                            if data:
                                thinking_acc += data
                                yield {"type": "thinking_chunk", "content": data}
                        elif block_type == "non_standard":
                            inner = block.get("value", {})
                            if inner.get("type") == "thinking":
                                text = inner.get("thinking", "")
                                if text:
                                    thinking_acc += text
                                    yield {"type": "thinking_chunk", "content": text}
        else:
            # Fallback: use agent_service if agent_graph not initialized
            messages_dicts = [{"role": m.type, "content": m.content} for m in messages]
            async for event in self.agent_service.astream(
                messages=messages_dicts,
                model_config=seo_model_config,
            ):
                yield event
                if event["type"] == "done":
                    answer_acc = event["response"].message

        yield {
            "type": "done",
            "response": AgentResponse(
                message=answer_acc,
                reasoning=thinking_acc or None,
                task_id=None,
                conversation_id=str(conversation_id) if conversation_id else None,
            ),
        }
        final_response_text = answer_acc

        # Persist the turn after streaming completes
        if final_response_text:
            from ..models.standard_messages import StandardMessage

            history = list(initial_state.get("conversation_history", []))
            history.append(StandardMessage(role="user", content=request.user_message))
            history.append(
                StandardMessage(role="assistant", content=final_response_text)
            )
            save_state = {**initial_state, "conversation_history": history}  # type: ignore[assignment]
            await self.lang_graph_service.save_turn(save_state)  # type: ignore[arg-type]

    async def get_conversation_state(self, conversation_id: UUID) -> WorkbenchState:
        """
        Get current conversation state in LangGraph format.

        Args:
            conversation_id: Conversation ID

        Returns:
            Current conversation state

        Raises:
            ConversationError: If conversation not found
        """
        try:
            if self.state_bridge:
                return await self.state_bridge.load_into_langgraph_state(
                    conversation_id=conversation_id,
                    user_message="",  # Empty for state retrieval
                    workflow_mode="workbench",  # Default mode
                )
            else:
                # Return default state if bridge not available
                return WorkbenchState(
                    conversation_id=conversation_id,
                    user_message="",
                    assistant_response=None,
                    model_config=self.default_model_config,
                    provider_name=self.default_model_config.provider,
                    context_data={},
                    active_contexts=[],
                    conversation_history=[],
                    workflow_mode="workbench",
                    workflow_steps=["Default state"],
                    current_operation=None,
                    execution_successful=True,
                    current_error=None,
                    retry_count=0,
                    business_profile=None,
                    seo_analysis=None,
                    coaching_context=None,
                    coaching_phase=None,
                    debug_mode=None,
                    parameter_overrides=None,
                    mcp_tools_active=[],
                    agent_state=None,
                    workflow_data=None,
                    document_context=None,
                    document_filename=None,
                )
        except Exception as e:
            logger.error(f"Failed to get conversation state: {str(e)}")
            raise ConversationError(
                f"Failed to get conversation state: {str(e)}"
            ) from e

    async def create_business_profile(
        self, profile_data: Dict[str, Any], conversation_id: UUID
    ) -> UUID:
        """
        Create business profile for SEO coaching.

        Args:
            profile_data: Business profile information
            conversation_id: Associated conversation ID

        Returns:
            Business profile ID

        Raises:
            ConversationError: If profile creation fails
        """
        if self.db_session is None:
            raise ConversationError("Database session not initialized")

        try:
            from ..models.business_models import BusinessProfileDB

            # Create business profile
            profile_id = uuid4()
            profile = BusinessProfileDB(
                id=profile_id,
                conversation_id=conversation_id,
                business_name=profile_data["business_name"],
                website_url=profile_data["website_url"],
                business_type=profile_data["business_type"],
                target_market=profile_data.get("target_market", "Nederland"),
                seo_experience_level=profile_data.get(
                    "seo_experience_level", "beginner"
                ),
            )

            self.db_session.add(profile)
            await self.db_session.commit()

            return profile_id

        except Exception as e:
            if self.db_session is not None:
                await self.db_session.rollback()
            logger.error(f"Failed to create business profile: {str(e)}")
            raise ConversationError(
                f"Failed to create business profile: {str(e)}"
            ) from e

    async def update_seo_analysis(
        self, conversation_id: UUID, analysis_data: Dict[str, Any]
    ) -> None:
        """
        Update SEO analysis data for conversation.

        Args:
            conversation_id: Conversation ID
            analysis_data: SEO analysis information

        Raises:
            ConversationError: If update fails
        """
        try:
            # Update context with SEO analysis
            if self.context_service:
                await self.context_service.update_conversation_context(
                    conversation_id, {"seo_analysis": analysis_data}, ["seo_analysis"]
                )

        except Exception as e:
            logger.error(f"Failed to update SEO analysis: {str(e)}")
            raise ConversationError(f"Failed to update SEO analysis: {str(e)}") from e

    async def _create_conversation(
        self, request: ConsolidatedWorkflowRequest, workflow_mode: str
    ) -> UUID:
        """
        Create new conversation for the request.

        Args:
            request: Workflow request
            workflow_mode: Determined workflow mode

        Returns:
            New conversation ID
        """
        if self.state_manager is None:
            # Fallback to creating UUID if state manager not available
            return uuid4()

        # Use model config from request or default
        model_config = request.llm_config or self.default_model_config

        # Apply mode-specific model config
        if workflow_mode == "seo_coach":
            model_config = ModelConfig(
                provider="openrouter",
                model_name="openai/gpt-4o-mini",
                temperature=0.7,
                max_tokens=1500,
                streaming=request.streaming,
            )

        return await self.state_manager.create_conversation(
            model_config=model_config,
            title=f"Conversation ({workflow_mode})",
            is_temporary=False,
        )

    async def _prepare_initial_state(
        self,
        request: ConsolidatedWorkflowRequest,
        conversation_id: UUID,
        workflow_mode: str,
    ) -> WorkbenchState:
        """
        Prepare initial LangGraph state for workflow execution.

        Args:
            request: Workflow request
            conversation_id: Conversation ID
            workflow_mode: Determined workflow mode

        Returns:
            Initial workflow state
        """
        # Get model config
        model_config = request.llm_config or self.default_model_config

        # Apply parameter overrides
        if request.parameter_overrides:
            config_dict = model_config.model_dump()
            config_dict.update(request.parameter_overrides)
            model_config = ModelConfig(**config_dict)

        # Ensure workflow_mode is a valid literal
        validated_mode: Literal["workbench", "seo_coach"]
        if workflow_mode == "seo_coach":
            validated_mode = "seo_coach"
        else:
            validated_mode = "workbench"

        # Create initial state
        initial_state: WorkbenchState = {
            "conversation_id": conversation_id,
            "user_message": request.user_message,
            "assistant_response": None,
            "model_config": model_config,
            "provider_name": model_config.provider,
            "context_data": request.context_data or {},
            "active_contexts": [],
            "conversation_history": [],
            "workflow_mode": validated_mode,
            "workflow_steps": ["Workflow initialized"],
            "current_operation": None,
            "execution_successful": True,
            "current_error": None,
            "retry_count": 0,
            "business_profile": request.business_profile,
            "seo_analysis": None,
            "coaching_context": None,
            "coaching_phase": "analysis" if validated_mode == "seo_coach" else None,
            "debug_mode": None,
            "parameter_overrides": request.parameter_overrides,
            "mcp_tools_active": [],
            "agent_state": None,
            "workflow_data": None,
            "document_context": request.document_context,
            "document_filename": request.document_filename,
        }

        return initial_state

    async def _direct_llm_fallback(self, request: ConsolidatedWorkflowRequest) -> str:
        """
        Direct LLM fallback when workflow fails.

        Args:
            request: Original workflow request

        Returns:
            Direct LLM response
        """
        try:
            model_config = request.llm_config or self.default_model_config
            fallback_agent = AgentService(model_config)
            response = await fallback_agent.run(
                messages=[{"role": "user", "content": request.user_message}]
            )
            return response.message

        except Exception as e:
            logger.error(f"Direct LLM fallback failed: {str(e)}")
            return (
                f"Fallback failed: {str(e)}. Original message: {request.user_message}"
            )

    def _convert_to_response(
        self, final_state: WorkbenchState, duration: Optional[float] = None
    ) -> ConsolidatedWorkflowResponse:
        """
        Convert final workflow state to response format.

        Args:
            final_state: Final LangGraph state
            duration: Elapsed execution time in seconds

        Returns:
            Consolidated workflow response
        """
        response_metadata: Dict[str, Any] = {"status": "done"}
        if duration is not None:
            response_metadata["duration"] = round(duration, 3)

        return ConsolidatedWorkflowResponse(
            conversation_id=final_state["conversation_id"],
            assistant_response=final_state.get("assistant_response") or "",
            workflow_mode=final_state["workflow_mode"],
            execution_successful=final_state["execution_successful"],
            workflow_steps=final_state["workflow_steps"],
            context_data=final_state["context_data"],
            business_profile=final_state.get("business_profile"),
            coaching_context=final_state.get("coaching_context"),
            metadata={
                "retry_count": final_state.get("retry_count", 0),
                "current_operation": final_state.get("current_operation"),
                "coaching_phase": final_state.get("coaching_phase"),
                "debug_mode": final_state.get("debug_mode"),
                "provider_used": final_state["provider_name"],
            },
            response_metadata=response_metadata,
        )


# Dependency injection for FastAPI
async def get_consolidated_service():  # type: ignore
    """
    Get initialized consolidated service instance.

    Yields:
        Consolidated workbench service
    """
    service = ConsolidatedWorkbenchService()

    # Get database session and initialize
    async for db_session in get_session():
        await service.initialize(db_session)
        yield service
        # Clean up happens automatically when the request ends
