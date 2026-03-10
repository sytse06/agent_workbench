"""Unit tests for AgentService streaming and batch invocation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.agent_service import AgentResponse, AgentService


def _make_config() -> ModelConfig:
    return ModelConfig(
        provider="anthropic",
        model_name="claude-3-5-haiku-20241022",
    )


def _mock_service() -> AgentService:
    with patch("agent_workbench.services.agent_service.provider_registry") as mock_reg:
        mock_reg.create_model.return_value = MagicMock()
        svc = AgentService(_make_config())
    return svc


# --- astream: plain text (Ollama / any provider) ---


@pytest.mark.asyncio
async def test_astream_plain_text_yields_answer_chunks():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="Hello"), AIMessageChunk(content=" world")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    answer_events = [e for e in events if e["type"] == "answer_chunk"]
    assert len(answer_events) == 2
    assert answer_events[0]["content"] == "Hello"
    assert answer_events[1]["content"] == " world"


@pytest.mark.asyncio
async def test_astream_plain_text_no_thinking_chunks():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="Answer")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    assert not any(e["type"] == "thinking_chunk" for e in events)


# --- astream: Anthropic extended thinking (non_standard blocks) ---


@pytest.mark.asyncio
async def test_astream_anthropic_thinking_yields_thinking_chunks():
    svc = _mock_service()
    chunks = [
        AIMessageChunk(content=[{"type": "thinking", "thinking": "Let me think..."}]),
        AIMessageChunk(content=[{"type": "text", "text": "The answer is 42"}]),
    ]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    thinking_events = [e for e in events if e["type"] == "thinking_chunk"]
    answer_events = [e for e in events if e["type"] == "answer_chunk"]
    assert len(thinking_events) == 1
    assert thinking_events[0]["content"] == "Let me think..."
    assert len(answer_events) == 1
    assert answer_events[0]["content"] == "The answer is 42"


# --- astream: OpenAI o-series reasoning (standardized) ---


@pytest.mark.asyncio
async def test_astream_openai_reasoning_yields_thinking_chunks():
    svc = _mock_service()
    chunks = [
        AIMessageChunk(content=[{"type": "reasoning", "data": "My reasoning..."}]),
        AIMessageChunk(content=[{"type": "text", "text": "Final answer"}]),
    ]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    thinking_events = [e for e in events if e["type"] == "thinking_chunk"]
    assert len(thinking_events) == 1
    assert thinking_events[0]["content"] == "My reasoning..."


# --- astream: done event ---


@pytest.mark.asyncio
async def test_astream_yields_done_event_last():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="hi")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    assert events[-1]["type"] == "done"
    assert isinstance(events[-1]["response"], AgentResponse)


@pytest.mark.asyncio
async def test_astream_done_event_contains_full_answer():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="Hello"), AIMessageChunk(content=" world")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    done = events[-1]
    assert done["response"].message == "Hello world"


@pytest.mark.asyncio
async def test_astream_done_event_contains_reasoning():
    svc = _mock_service()
    chunks = [
        AIMessageChunk(content=[{"type": "thinking", "thinking": "Thoughts"}]),
        AIMessageChunk(content=[{"type": "text", "text": "Answer"}]),
    ]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    done = events[-1]
    assert done["response"].reasoning == "Thoughts"


# --- run: batch invocation ---


@pytest.mark.asyncio
async def test_run_returns_agent_response():
    svc = _mock_service()
    mock_response = MagicMock()
    mock_response.content = "batch answer"
    svc._default_model.ainvoke = AsyncMock(return_value=mock_response)

    result = await svc.run([{"role": "user", "content": "hi"}])
    assert isinstance(result, AgentResponse)
    assert result.message == "batch answer"
