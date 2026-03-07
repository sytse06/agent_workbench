"""Unit tests for WorkbenchModeHandler and SEOCoachModeHandler pure logic."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.mode_handlers import (
    SEOCoachModeHandler,
    WorkbenchModeHandler,
)


def make_workbench_handler():
    return WorkbenchModeHandler(
        agent_service=MagicMock(),
        context_service=MagicMock(),
    )


def make_seo_handler():
    return SEOCoachModeHandler(
        agent_service=MagicMock(),
        context_service=MagicMock(),
    )


def minimal_state(**overrides):
    state = {
        "conversation_id": uuid4(),
        "user_message": "test",
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
        "coaching_phase": "analysis",
        "debug_mode": False,
        "parameter_overrides": None,
        "mcp_tools_active": [],
        "agent_state": None,
        "workflow_data": None,
    }
    state.update(overrides)
    return state


# --- WorkbenchModeHandler._apply_parameter_overrides ---


def test_apply_overrides_changes_temperature():
    handler = make_workbench_handler()
    config = ModelConfig(
        provider="anthropic", model_name="claude-3.5-sonnet", temperature=0.7
    )
    result = handler._apply_parameter_overrides(config, {"temperature": 0.2})
    assert result.temperature == 0.2


def test_apply_overrides_does_not_mutate_original():
    handler = make_workbench_handler()
    config = ModelConfig(
        provider="anthropic", model_name="claude-3.5-sonnet", temperature=0.7
    )
    handler._apply_parameter_overrides(config, {"temperature": 0.1})
    assert config.temperature == 0.7


def test_apply_overrides_preserves_unoverridden_fields():
    handler = make_workbench_handler()
    config = ModelConfig(
        provider="anthropic",
        model_name="claude-3.5-sonnet",
        temperature=0.7,
        max_tokens=1000,
    )
    result = handler._apply_parameter_overrides(config, {"temperature": 0.5})
    assert result.max_tokens == 1000
    assert result.model_name == "claude-3.5-sonnet"


# --- WorkbenchModeHandler._build_technical_context ---


def test_build_technical_context_contains_required_keys():
    handler = make_workbench_handler()
    state = minimal_state()
    result = handler._build_technical_context(state)
    assert "session_type" in result
    assert "debug_mode" in result
    assert "conversation_length" in result
    assert result["session_type"] == "workbench"


def test_build_technical_context_propagates_debug_mode():
    handler = make_workbench_handler()
    state = minimal_state(debug_mode=True)
    result = handler._build_technical_context(state)
    assert result["debug_mode"] is True


def test_build_technical_context_includes_overrides_when_present():
    handler = make_workbench_handler()
    state = minimal_state(parameter_overrides={"temperature": 0.1})
    result = handler._build_technical_context(state)
    assert "parameter_overrides" in result


def test_build_technical_context_excludes_overrides_when_absent():
    handler = make_workbench_handler()
    state = minimal_state(parameter_overrides=None)
    result = handler._build_technical_context(state)
    assert "parameter_overrides" not in result


def test_build_technical_context_reflects_history_length():
    from agent_workbench.models.standard_messages import StandardMessage

    handler = make_workbench_handler()
    history = [StandardMessage(role="user", content="hi")]
    state = minimal_state(conversation_history=history)
    result = handler._build_technical_context(state)
    assert result["conversation_length"] == 1


# --- SEOCoachModeHandler._update_coaching_phase ---


@pytest.mark.asyncio
async def test_coaching_phase_analyse_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="kun je mijn website analyseren?")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "analysis"


@pytest.mark.asyncio
async def test_coaching_phase_check_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="kun je dat even checken?")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "analysis"


@pytest.mark.asyncio
async def test_coaching_phase_aanbeveling_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="geef me een aanbeveling")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "recommendations"


@pytest.mark.asyncio
async def test_coaching_phase_wat_moet_ik_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="wat moet ik nu doen?")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "recommendations"


@pytest.mark.asyncio
async def test_coaching_phase_hoe_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="hoe doe ik dat?")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "implementation"


@pytest.mark.asyncio
async def test_coaching_phase_implementeren_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="ik wil dit implementeren")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "implementation"


@pytest.mark.asyncio
async def test_coaching_phase_resultaat_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="mijn resultaat bekijken")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "monitoring"


@pytest.mark.asyncio
async def test_coaching_phase_monitoring_keyword():
    handler = make_seo_handler()
    state = minimal_state(user_message="monitoring instellen")
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "monitoring"


@pytest.mark.asyncio
async def test_coaching_phase_unknown_preserves_current():
    handler = make_seo_handler()
    state = minimal_state(
        user_message="vertel me meer", coaching_phase="recommendations"
    )
    result = await handler._update_coaching_phase(state)
    assert result["coaching_phase"] == "recommendations"


# --- SEOCoachModeHandler._build_coaching_context ---


@pytest.mark.asyncio
async def test_build_coaching_context_defaults_when_no_profile():
    handler = make_seo_handler()
    state = minimal_state(business_profile=None)
    result = await handler._build_coaching_context(state)
    biz = result["business_context"]
    assert biz["target_market"] == "Nederland"
    assert biz["experience_level"] == "beginner"


@pytest.mark.asyncio
async def test_build_coaching_context_uses_profile_values():
    handler = make_seo_handler()
    state = minimal_state(
        business_profile={
            "business_name": "Bakkerij de Zon",
            "business_type": "bakkerij",
            "target_market": "Amsterdam",
            "seo_experience_level": "intermediate",
            "website_url": "https://bakkerijdezon.nl",
        }
    )
    result = await handler._build_coaching_context(state)
    biz = result["business_context"]
    assert biz["business_name"] == "Bakkerij de Zon"
    assert biz["business_type"] == "bakkerij"
    assert biz["target_market"] == "Amsterdam"
    assert biz["experience_level"] == "intermediate"


@pytest.mark.asyncio
async def test_build_coaching_context_includes_required_keys():
    handler = make_seo_handler()
    state = minimal_state()
    result = await handler._build_coaching_context(state)
    assert "business_context" in result
    assert "coaching_phase" in result
    assert "session_info" in result
