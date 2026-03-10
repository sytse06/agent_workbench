"""Unit tests for AgentService streaming and batch invocation."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessageChunk

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.agent_service import AgentResponse, AgentService, _split_think_tags


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


# --- _split_think_tags unit tests ---

def test_split_plain_text_no_tags():
    segments, in_think = _split_think_tags("Hello world", False)
    assert segments == [("answer", "Hello world")]
    assert in_think is False


def test_split_full_think_block_in_one_chunk():
    segments, in_think = _split_think_tags("<think>reasoning</think>answer", False)
    assert segments == [("thinking", "reasoning"), ("answer", "answer")]
    assert in_think is False


def test_split_open_tag_only():
    # <think> arrives but </think> in later chunk
    segments, in_think = _split_think_tags("<think>start of reasoning", False)
    assert segments == [("thinking", "start of reasoning")]
    assert in_think is True


def test_split_close_tag_only():
    # already inside think, </think> arrives
    segments, in_think = _split_think_tags("end of reasoning</think>answer", True)
    assert segments == [("thinking", "end of reasoning"), ("answer", "answer")]
    assert in_think is False


def test_split_text_before_think_tag():
    segments, in_think = _split_think_tags("preamble<think>thought</think>answer", False)
    assert segments == [
        ("answer", "preamble"),
        ("thinking", "thought"),
        ("answer", "answer"),
    ]
    assert in_think is False


def test_split_empty_think_block():
    segments, in_think = _split_think_tags("<think></think>answer", False)
    assert ("answer", "answer") in segments
    assert in_think is False


# --- astream: Ollama <think> tag streaming (Qwen3, deepseek-r1) ---

@pytest.mark.asyncio
async def test_astream_think_tags_in_text_yields_thinking_and_answer():
    svc = _mock_service()
    # Simulate Ollama streaming: <think> and </think> in separate chunks
    chunks = [
        AIMessageChunk(content="<think>"),
        AIMessageChunk(content="Let me reason about this"),
        AIMessageChunk(content="</think>"),
        AIMessageChunk(content="The answer is 42"),
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
    assert any("Let me reason" in e["content"] for e in thinking_events)
    assert any("42" in e["content"] for e in answer_events)


@pytest.mark.asyncio
async def test_astream_think_tags_full_block_in_one_chunk():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="<think>reasoning</think>answer")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    assert any(e["type"] == "thinking_chunk" and "reasoning" in e["content"] for e in events)
    assert any(e["type"] == "answer_chunk" and "answer" in e["content"] for e in events)


@pytest.mark.asyncio
async def test_astream_done_event_reasoning_from_think_tags():
    svc = _mock_service()
    chunks = [AIMessageChunk(content="<think>thoughts</think>result")]

    async def fake_astream(messages):
        for c in chunks:
            yield c

    svc._default_model.astream = fake_astream

    events = []
    async for event in svc.astream([{"role": "user", "content": "hi"}]):
        events.append(event)

    done = events[-1]
    assert done["response"].reasoning == "thoughts"
    assert done["response"].message == "result"
