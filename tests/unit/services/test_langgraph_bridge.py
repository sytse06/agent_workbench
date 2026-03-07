"""Unit tests for LangGraphStateBridge conversion logic."""

from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from agent_workbench.models.standard_messages import StandardMessage
from agent_workbench.services.langgraph_bridge import LangGraphStateBridge


@pytest.fixture
def bridge():
    return LangGraphStateBridge(
        state_manager=MagicMock(),
        context_service=MagicMock(),
    )


# --- _convert_messages_to_standard ---


def test_convert_dict_message_preserves_role_and_content(bridge):
    msgs = [{"role": "user", "content": "hello"}]
    result = bridge._convert_messages_to_standard(msgs)
    assert len(result) == 1
    assert result[0].role == "user"
    assert result[0].content == "hello"


def test_convert_dict_message_preserves_metadata(bridge):
    msgs = [{"role": "assistant", "content": "hi", "metadata": {"key": "val"}}]
    result = bridge._convert_messages_to_standard(msgs)
    assert result[0].metadata == {"key": "val"}


def test_convert_dict_message_without_metadata_gives_none(bridge):
    msgs = [{"role": "user", "content": "test"}]
    result = bridge._convert_messages_to_standard(msgs)
    assert result[0].metadata is None


def test_convert_standard_message_passthrough(bridge):
    msg = StandardMessage(role="user", content="original")
    result = bridge._convert_messages_to_standard([msg])
    assert result[0] is msg


def test_convert_unknown_type_becomes_assistant_string(bridge):
    result = bridge._convert_messages_to_standard(["raw string"])
    assert result[0].role == "assistant"
    assert result[0].content == "raw string"


def test_convert_mixed_formats(bridge):
    sm = StandardMessage(role="user", content="first")
    msgs = [sm, {"role": "assistant", "content": "second"}]
    result = bridge._convert_messages_to_standard(msgs)
    assert len(result) == 2
    assert result[0] is sm
    assert result[1].role == "assistant"


# --- _convert_context_data ---


def test_convert_context_data_passes_serializable_values(bridge):
    ctx = {"key": "value", "number": 42, "list": [1, 2]}
    result = bridge._convert_context_data(ctx)
    assert result == ctx


def test_convert_context_data_stringifies_non_serializable(bridge):
    ctx = {"bad": object()}
    result = bridge._convert_context_data(ctx)
    assert isinstance(result["bad"], str)


def test_convert_context_data_empty_input(bridge):
    assert bridge._convert_context_data({}) == {}


# --- merge_workflow_context ---


def test_merge_workflow_context_workflow_overrides_base(bridge):
    base = {"a": 1, "b": 2}
    workflow = {"b": 99, "c": 3}
    result = bridge.merge_workflow_context(base, workflow)
    assert result == {"a": 1, "b": 99, "c": 3}


def test_merge_workflow_context_does_not_mutate_base(bridge):
    base = {"a": 1}
    bridge.merge_workflow_context(base, {"b": 2})
    assert "b" not in base


def test_merge_workflow_context_empty_workflow(bridge):
    base = {"a": 1}
    result = bridge.merge_workflow_context(base, {})
    assert result == {"a": 1}


# --- extract_from_workflow ---


@pytest.mark.asyncio
async def test_extract_from_workflow_builds_messages(bridge):
    workflow_state = {
        "conversation_id": str(uuid4()),
        "conversation_history": [
            {
                "role": "user",
                "content": "hello",
                "timestamp": datetime.utcnow().isoformat(),
            },
        ],
        "assistant_response": "world",
        "model_config": {
            "provider": "anthropic",
            "model_name": "claude-3.5-sonnet",
            "temperature": 0.7,
            "max_tokens": 2000,
            "streaming": True,
        },
        "provider_name": "anthropic",
        "context_data": {},
        "active_contexts": [],
        "workflow_mode": "workbench",
        "debug_mode": False,
        "parameter_overrides": {},
        "workflow_data": {},
    }
    result = await bridge.extract_from_workflow(workflow_state)
    roles = [m.role for m in result["messages"]]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_extract_from_workflow_no_assistant_response(bridge):
    workflow_state = {
        "conversation_id": str(uuid4()),
        "conversation_history": [],
        "assistant_response": None,
        "model_config": {
            "provider": "anthropic",
            "model_name": "claude-3.5-sonnet",
            "temperature": 0.7,
            "max_tokens": 2000,
            "streaming": True,
        },
        "provider_name": "anthropic",
        "context_data": {},
        "active_contexts": [],
        "workflow_mode": "workbench",
        "debug_mode": False,
        "parameter_overrides": {},
        "workflow_data": {},
    }
    result = await bridge.extract_from_workflow(workflow_state)
    assert result["messages"] == []


# --- _create_new_langgraph_state ---


@pytest.mark.asyncio
async def test_create_new_state_workbench_uses_claude(bridge):
    state = await bridge._create_new_langgraph_state(
        conversation_id=uuid4(),
        user_message="debug this",
        workflow_mode="workbench",
    )
    assert "claude" in state["model_config"].model_name.lower()


@pytest.mark.asyncio
async def test_create_new_state_seo_coach_uses_gpt(bridge):
    state = await bridge._create_new_langgraph_state(
        conversation_id=uuid4(),
        user_message="help met seo",
        workflow_mode="seo_coach",
    )
    assert "gpt" in state["model_config"].model_name.lower()


@pytest.mark.asyncio
async def test_create_new_state_sets_correct_mode(bridge):
    state = await bridge._create_new_langgraph_state(
        conversation_id=uuid4(),
        user_message="test",
        workflow_mode="workbench",
    )
    assert state["workflow_mode"] == "workbench"
    assert state["conversation_history"] == []
    assert state["execution_successful"] is True
