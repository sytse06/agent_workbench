"""Unit tests for WorkflowOrchestrator routing and node logic."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.workflow_orchestrator import WorkflowOrchestrator


def make_orchestrator():
    state_bridge = MagicMock()
    workbench_handler = MagicMock()
    seo_coach_handler = MagicMock()
    return WorkflowOrchestrator(state_bridge, workbench_handler, seo_coach_handler)


def minimal_state(**overrides):
    state = {
        "conversation_id": uuid4(),
        "user_message": "test message",
        "assistant_response": None,
        "model_config": ModelConfig(
            provider="anthropic", model_name="claude-3.5-sonnet"
        ),
        "provider_name": "anthropic",
        "context_data": {},
        "active_contexts": [],
        "conversation_history": [],
        "workflow_mode": "workbench",
        "workflow_steps": [],
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
    state.update(overrides)
    return state


# --- graph compilation ---


def test_workflow_graph_compiles_without_error():
    orch = make_orchestrator()
    assert orch.workflow is not None


# --- _route_by_mode ---


def test_route_workbench_mode(make_orch=None):
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="workbench")
    assert orch._route_by_mode(state) == "workbench"


def test_route_seo_coach_mode():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="seo_coach")
    assert orch._route_by_mode(state) == "seo_coach"


def test_route_error_when_current_error_set():
    orch = make_orchestrator()
    state = minimal_state(current_error="something went wrong")
    assert orch._route_by_mode(state) == "error"


def test_route_error_on_invalid_mode():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="unknown_mode")
    assert orch._route_by_mode(state) == "error"


# --- _validate_input_node ---


@pytest.mark.asyncio
async def test_validate_passes_for_valid_state():
    orch = make_orchestrator()
    state = minimal_state()
    result = await orch._validate_input_node(state)
    assert result["execution_successful"] is True
    assert any("passed" in step for step in result["workflow_steps"])


@pytest.mark.asyncio
async def test_validate_fails_on_empty_message():
    orch = make_orchestrator()
    state = minimal_state(user_message="   ")
    result = await orch._validate_input_node(state)
    assert result["execution_successful"] is False
    assert result["current_error"] is not None


@pytest.mark.asyncio
async def test_validate_fails_on_invalid_mode():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="invalid")
    result = await orch._validate_input_node(state)
    assert result["execution_successful"] is False


@pytest.mark.asyncio
async def test_validate_passes_for_seo_coach_mode():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="seo_coach")
    result = await orch._validate_input_node(state)
    assert result["execution_successful"] is True


# --- _detect_intent_node ---


@pytest.mark.asyncio
async def test_detect_intent_appends_mode_to_steps():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="workbench")
    result = await orch._detect_intent_node(state)
    assert any("workbench" in step for step in result["workflow_steps"])


@pytest.mark.asyncio
async def test_detect_intent_preserves_existing_steps():
    orch = make_orchestrator()
    state = minimal_state(workflow_steps=["step_one"])
    result = await orch._detect_intent_node(state)
    assert "step_one" in result["workflow_steps"]


# --- _handle_error_node ---


@pytest.mark.asyncio
async def test_handle_error_returns_english_fallback_for_workbench():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="workbench", current_error="LLM timeout")
    result = await orch._handle_error_node(state)
    assert result["assistant_response"] is not None
    assert result["execution_successful"] is False
    assert "LLM timeout" in result["assistant_response"]


@pytest.mark.asyncio
async def test_handle_error_returns_dutch_fallback_for_seo_coach():
    orch = make_orchestrator()
    state = minimal_state(workflow_mode="seo_coach", current_error="fout")
    result = await orch._handle_error_node(state)
    assert result["assistant_response"] is not None
    # Dutch fallback contains Dutch words
    assert any(
        word in result["assistant_response"] for word in ["Excuses", "SEO", "opnieuw"]
    )


@pytest.mark.asyncio
async def test_handle_error_increments_retry_count():
    orch = make_orchestrator()
    state = minimal_state(retry_count=1, current_error="err")
    result = await orch._handle_error_node(state)
    assert result["retry_count"] == 2


# --- _generate_response_node ---


@pytest.mark.asyncio
async def test_generate_response_fails_when_no_response():
    orch = make_orchestrator()
    state = minimal_state(assistant_response=None)
    result = await orch._generate_response_node(state)
    assert result["execution_successful"] is False


@pytest.mark.asyncio
async def test_generate_response_passes_when_response_exists():
    orch = make_orchestrator()
    state = minimal_state(assistant_response="Here is the answer.")
    result = await orch._generate_response_node(state)
    assert result["execution_successful"] is True
