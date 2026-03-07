"""Unit tests for ValidatedWorkbenchState validation and TypedDict conversion."""

from uuid import uuid4

import pydantic
import pytest

from agent_workbench.models.consolidated_state import ValidatedWorkbenchState
from agent_workbench.models.schemas import ModelConfig


def valid_state_data(**overrides):
    data = {
        "conversation_id": uuid4(),
        "user_message": "test message",
        "model_config": ModelConfig(
            provider="anthropic", model_name="claude-3.5-sonnet"
        ),
        "provider_name": "anthropic",
        "workflow_mode": "workbench",
    }
    data.update(overrides)
    return data


# --- provider_name validation ---


def test_valid_provider_name_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(provider_name="anthropic"))
    assert state.provider_name == "anthropic"


def test_provider_name_with_underscore_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(provider_name="open_router"))
    assert state.provider_name == "open_router"


def test_provider_name_uppercase_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(provider_name="Anthropic"))


def test_provider_name_with_space_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(provider_name="open router"))


# --- retry_count validation ---


def test_retry_count_zero_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(retry_count=0))
    assert state.retry_count == 0


def test_retry_count_five_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(retry_count=5))
    assert state.retry_count == 5


def test_retry_count_six_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(retry_count=6))


def test_retry_count_negative_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(retry_count=-1))


# --- workflow_steps validation ---


def test_workflow_steps_valid_strings_accepted():
    state = ValidatedWorkbenchState(
        **valid_state_data(workflow_steps=["init", "load_context"])
    )
    assert len(state.workflow_steps) == 2


def test_workflow_steps_empty_string_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(workflow_steps=["init", ""]))


def test_workflow_steps_whitespace_only_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(workflow_steps=["   "]))


# --- user_message validation ---


def test_empty_user_message_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(user_message=""))


# --- to_typeddict / from_typeddict roundtrip ---


def test_to_typeddict_contains_model_config_key():
    state = ValidatedWorkbenchState(**valid_state_data())
    td = state.to_typeddict()
    assert "model_config" in td
    assert "model_config_field" not in td


def test_from_typeddict_roundtrip_preserves_fields():
    original = ValidatedWorkbenchState(**valid_state_data(provider_name="openai"))
    td = original.to_typeddict()
    restored = ValidatedWorkbenchState.from_typeddict(td)
    assert restored.provider_name == "openai"
    assert restored.workflow_mode == original.workflow_mode


def test_from_typeddict_roundtrip_preserves_conversation_id():
    cid = uuid4()
    original = ValidatedWorkbenchState(**valid_state_data(conversation_id=cid))
    td = original.to_typeddict()
    restored = ValidatedWorkbenchState.from_typeddict(td)
    assert restored.conversation_id == cid


# --- workflow_mode ---


def test_workbench_mode_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(workflow_mode="workbench"))
    assert state.workflow_mode == "workbench"


def test_seo_coach_mode_accepted():
    state = ValidatedWorkbenchState(**valid_state_data(workflow_mode="seo_coach"))
    assert state.workflow_mode == "seo_coach"


def test_invalid_workflow_mode_rejected():
    with pytest.raises(pydantic.ValidationError):
        ValidatedWorkbenchState(**valid_state_data(workflow_mode="unknown"))
