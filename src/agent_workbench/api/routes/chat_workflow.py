"""Workflow chat endpoints using full LangGraph orchestration for dual-mode operation.

This is the primary chat endpoint for Agent Workbench, providing:
- Full LangGraph StateGraph workflow orchestration
- Dual-mode operation (workbench/seo_coach)
- Complete state management and persistence
- Context injection and management
- Business profile integration for SEO Coach mode

Architecture: LangGraph-Centered (PRD compliant)
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ...core.exceptions import ConversationError, LLMProviderError
from ...models.business_models import BusinessProfile, SEOAnalysisContext
from ...models.consolidated_state import (
    ConsolidatedWorkflowRequest,
    ConsolidatedWorkflowResponse,
    ContextUpdateRequest,
)
from ...services.consolidated_service import (
    ConsolidatedWorkbenchService,
    get_consolidated_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Workflow Chat"])


@router.post("/workflow", response_model=ConsolidatedWorkflowResponse)
async def workflow_chat(
    request: ConsolidatedWorkflowRequest,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Execute full LangGraph workflow for both workbench and seo_coach modes.

    This is the PRIMARY chat endpoint providing complete workflow orchestration
    with state management, context injection, and dual-mode support.

    Args:
        request: Workflow request with user message and configuration
        service: Consolidated workbench service

    Returns:
        Workflow response with assistant message and execution details

    Raises:
        HTTPException: If workflow execution fails
    """
    try:
        # Enhanced debug logging for request tracking
        logger.info("🎯 DEBUG: Received consolidated chat request")
        logger.info(f"🎯 DEBUG: Message: {request.user_message[:50]}...")
        logger.info(f"🎯 DEBUG: Workflow mode: {request.workflow_mode}")
        logger.info(f"🎯 DEBUG: Model config: {request.model_config}")
        logger.info(f"🎯 DEBUG: Conversation ID: {request.conversation_id}")

        logger.info(
            f"Processing consolidated chat request for mode: {request.workflow_mode}"
        )

        response = await service.execute_workflow(request)

        logger.info("🎯 DEBUG: Workflow execution completed")
        logger.info(f"🎯 DEBUG: Response success: {response.execution_successful}")
        response_len = (
            len(response.assistant_response) if response.assistant_response else 0
        )
        logger.info(f"🎯 DEBUG: Assistant response length: {response_len}")

        logger.info(
            f"Consolidated chat completed successfully for conversation: "
            f"{response.conversation_id}"
        )

        return response

    except ConversationError as e:
        logger.error(f"Conversation error in consolidated chat: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except LLMProviderError as e:
        logger.error(f"LLM provider error in consolidated chat: {str(e)}")
        raise HTTPException(
            status_code=503, detail=f"LLM service unavailable: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in consolidated chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/workflow/stream")
async def workflow_chat_stream(
    request: ConsolidatedWorkflowRequest,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Stream full LangGraph workflow execution with real-time updates.

    Args:
        request: Workflow request
        service: Consolidated workbench service

    Returns:
        Streaming response with workflow updates
    """
    try:

        import json

        async def generate_stream():
            """Generate streaming workflow updates as SSE."""
            async for event in service.stream_workflow(request):
                # Serialize: replace AgentResponse object in "done" event
                payload = dict(event)
                resp_obj = payload.get("response")
                if payload.get("type") == "done" and hasattr(resp_obj, "model_dump"):
                    payload["response"] = payload["response"].model_dump()
                yield f"data: {json.dumps(payload)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            },
        )

    except Exception as e:
        logger.error(f"Streaming error: {str(e)}")
        raise HTTPException(status_code=500, detail="Streaming failed")


@router.get("/consolidated/state/{conversation_id}")
async def get_conversation_state(
    conversation_id: UUID,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Get current conversation state in LangGraph format.

    Args:
        conversation_id: Conversation ID
        service: Consolidated workbench service

    Returns:
        Current conversation state
    """
    try:
        state = await service.get_conversation_state(conversation_id)

        # Convert WorkbenchState to JSON-serializable format
        return {
            "conversation_id": str(state["conversation_id"]),
            "workflow_mode": state["workflow_mode"],
            "execution_successful": state["execution_successful"],
            "workflow_steps": state["workflow_steps"],
            "context_data": state["context_data"],
            "business_profile": state.get("business_profile"),
            "coaching_context": state.get("coaching_context"),
            "coaching_phase": state.get("coaching_phase"),
            "debug_mode": state.get("debug_mode"),
            "conversation_history": state.get("conversation_history", []),
        }

    except ConversationError as e:
        logger.error(f"Failed to get conversation state: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting conversation state: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# NEW: Required API endpoint for UI conversation state
@router.get("/conversations/{conversation_id}/state")
async def get_conversation_state_for_ui(
    conversation_id: str,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """Get conversation state for UI history display"""
    try:
        state = await service.get_conversation_state(UUID(conversation_id))
        return {
            "conversation_id": conversation_id,
            "conversation_history": state.get("conversation_history", []),
            "workflow_mode": state.get("workflow_mode", "workbench"),
            "context_data": state.get("context_data", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Conversation not found: {str(e)}")


# SEO Coach specific endpoints


@router.post("/seo/business-profile", response_model=dict)
async def create_business_profile(
    profile: BusinessProfile,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Create business profile for SEO coaching.

    Args:
        profile: Business profile data
        service: Consolidated workbench service

    Returns:
        Created business profile information
    """
    try:
        profile_id = await service.create_business_profile(
            profile_data=profile.model_dump(exclude={"id", "created_at"}),
            conversation_id=profile.conversation_id,
        )

        return {
            "profile_id": str(profile_id),
            "conversation_id": str(profile.conversation_id),
            "message": "Business profile created successfully",
        }

    except ConversationError as e:
        logger.error(f"Failed to create business profile: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating business profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/seo/analysis/{conversation_id}")
async def update_seo_analysis(
    conversation_id: UUID,
    analysis: SEOAnalysisContext,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Update SEO analysis data for conversation.

    Args:
        conversation_id: Conversation ID
        analysis: SEO analysis context
        service: Consolidated workbench service

    Returns:
        Update confirmation
    """
    try:
        await service.update_seo_analysis(
            conversation_id=conversation_id, analysis_data=analysis.model_dump()
        )

        return {
            "conversation_id": str(conversation_id),
            "message": "SEO analysis updated successfully",
            "analysis_timestamp": analysis.analysis_timestamp.isoformat(),
        }

    except ConversationError as e:
        logger.error(f"Failed to update SEO analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating SEO analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Context management endpoints


@router.put("/context/{conversation_id}")
async def update_conversation_context(
    conversation_id: UUID,
    request: ContextUpdateRequest,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Update conversation context data.

    Args:
        conversation_id: Conversation ID
        request: Context update request
        service: Consolidated workbench service

    Returns:
        Update confirmation
    """
    try:
        if service.context_service:
            await service.context_service.update_conversation_context(
                conversation_id=conversation_id,
                context_data=request.context_data,
                sources=request.sources,
            )

        return {
            "conversation_id": str(conversation_id),
            "message": "Context updated successfully",
            "sources": request.sources,
        }

    except ConversationError as e:
        logger.error(f"Failed to update context: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating context: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/context/{conversation_id}")
async def clear_conversation_context(
    conversation_id: UUID,
    source: Optional[str] = None,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Clear conversation context data.

    Args:
        conversation_id: Conversation ID
        source: Optional specific source to clear
        service: Consolidated workbench service

    Returns:
        Clear confirmation
    """
    try:
        if service.context_service:
            await service.context_service.clear_conversation_context(
                conversation_id=conversation_id, source=source
            )

        message = (
            f"Context cleared{' for source: ' + source if source else ' completely'}"
        )
        return {
            "conversation_id": str(conversation_id),
            "message": message,
        }

    except ConversationError as e:
        logger.error(f"Failed to clear context: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error clearing context: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/context/{conversation_id}")
async def get_conversation_context(
    conversation_id: UUID,
    service: ConsolidatedWorkbenchService = Depends(get_consolidated_service),
):
    """
    Get current conversation context.

    Args:
        conversation_id: Conversation ID
        service: Consolidated workbench service

    Returns:
        Current context data
    """
    try:
        if service.context_service:
            active_contexts = await service.context_service.get_active_contexts(
                conversation_id
            )
        else:
            active_contexts = []

        return {
            "conversation_id": str(conversation_id),
            "active_contexts": active_contexts,
            "message": "Context retrieved successfully",
        }

    except ConversationError as e:
        logger.error(f"Failed to get context: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting context: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
