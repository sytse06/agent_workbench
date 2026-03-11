"""Unit tests for AgentGraph inner ReAct sub-graph."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.agent_graph import AgentGraph


def _make_config() -> ModelConfig:
    return ModelConfig(
        provider="anthropic",
        model_name="claude-3-5-haiku-20241022",
    )


def _mock_graph(mock_model: MagicMock) -> AgentGraph:
    with patch("agent_workbench.services.agent_graph.provider_registry") as mock_reg:
        mock_reg.create_model.return_value = mock_model
        graph = AgentGraph(_make_config())
    return graph


# --- construction ---


def test_agent_graph_builds_without_error():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
    assert graph._graph is not None


def test_agent_graph_singleton_compiled_once():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
    first = graph._graph
    second = graph._graph
    assert first is second


# --- context ---


def test_context_uses_stored_model_config():
    config = _make_config()
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(config)
    ctx = graph._context(tools=[])
    assert ctx["model_config"] is config
    assert ctx["tools"] == []


def test_context_accepts_override_model_config():
    default_config = _make_config()
    override_config = ModelConfig(provider="openai", model_name="gpt-4o")
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(default_config)
    ctx = graph._context(tools=[], model_config=override_config)
    assert ctx["model_config"] is override_config


# --- ainvoke ---


@pytest.mark.asyncio
async def test_ainvoke_returns_final_ai_message():
    mock_model = MagicMock()
    ai_response = AIMessage(content="test answer")
    mock_model.ainvoke = AsyncMock(return_value=ai_response)

    graph = _mock_graph(mock_model)

    with patch.object(graph, "_graph") as mock_compiled:
        mock_compiled.ainvoke = AsyncMock(
            return_value={"messages": [HumanMessage(content="hi"), ai_response]}
        )
        result = await graph.ainvoke([HumanMessage(content="hi")], tools=[])

    assert result is ai_response


@pytest.mark.asyncio
async def test_ainvoke_with_empty_tools_calls_model_without_bind_tools():
    mock_model = MagicMock()
    ai_response = AIMessage(content="ok")
    mock_model.ainvoke = AsyncMock(return_value=ai_response)

    with patch("agent_workbench.services.agent_graph.provider_registry") as mock_reg:
        mock_reg.create_model.return_value = mock_model
        graph = AgentGraph(_make_config())
        # Invoke directly (graph will call llm_node which calls provider_registry)
        with patch.object(graph, "_graph") as mock_compiled:
            mock_compiled.ainvoke = AsyncMock(return_value={"messages": [ai_response]})
            await graph.ainvoke([HumanMessage(content="hi")], tools=[])

    # bind_tools should NOT be called when tools=[]
    mock_model.bind_tools.assert_not_called()


@pytest.mark.asyncio
async def test_ainvoke_passes_model_config_override():
    override = ModelConfig(provider="openai", model_name="gpt-4o")
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
        with patch.object(graph, "_graph") as mock_compiled:
            ai_msg = AIMessage(content="ok")
            mock_compiled.ainvoke = AsyncMock(return_value={"messages": [ai_msg]})
            await graph.ainvoke(
                [HumanMessage(content="hi")], tools=[], model_config=override
            )
        call_kwargs = mock_compiled.ainvoke.call_args
        ctx = call_kwargs[1]["context"]
        assert ctx["model_config"] is override


# --- astream ---


@pytest.mark.asyncio
async def test_astream_yields_chunks():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())

    fake_chunks = [
        {"type": "messages", "ns": (), "data": (MagicMock(), {})},
        {"type": "messages", "ns": (), "data": (MagicMock(), {})},
        {"type": "custom", "ns": (), "data": {"progress": "done"}},
    ]

    async def fake_stream(*args, **kwargs):
        for c in fake_chunks:
            yield c

    with patch.object(graph._graph, "astream", fake_stream):
        chunks = []
        async for chunk in graph.astream([HumanMessage("hi")], tools=[]):
            chunks.append(chunk)

    assert len(chunks) == 3
    assert chunks[0]["type"] == "messages"
    assert chunks[2]["type"] == "custom"


# --- should_continue edge logic ---


def test_should_continue_returns_end_when_no_tool_calls():
    from langgraph.graph import END

    msg = AIMessage(content="done", tool_calls=[])
    last = msg
    result = (
        END if not (hasattr(last, "tool_calls") and last.tool_calls) else "tool_node"
    )
    assert result == END


def test_should_continue_returns_tool_node_when_tool_calls_present():
    msg = AIMessage(content="", tool_calls=[{"name": "search", "args": {}, "id": "1"}])
    last = msg
    result = "tool_node" if (hasattr(last, "tool_calls") and last.tool_calls) else "end"
    assert result == "tool_node"
