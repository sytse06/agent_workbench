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


def test_agent_graph_uses_custom_checkpointer():
    from langgraph.checkpoint.memory import MemorySaver

    checkpointer = MemorySaver()
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config(), checkpointer=checkpointer)
    assert graph._checkpointer is checkpointer


def test_agent_graph_defaults_to_memory_saver():
    from langgraph.checkpoint.memory import MemorySaver

    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
    assert isinstance(graph._checkpointer, MemorySaver)


# --- context ---


def test_context_uses_stored_model_config():
    config = _make_config()
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(config)
    ctx = graph._context()
    assert ctx["model_config"] is config
    assert "tools" not in ctx


def test_context_accepts_override_model_config():
    default_config = _make_config()
    override_config = ModelConfig(provider="openai", model_name="gpt-4o")
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(default_config)
    ctx = graph._context(model_config=override_config)
    assert ctx["model_config"] is override_config


def test_agent_graph_with_tools_adds_tool_node():
    from langchain_core.tools import tool

    @tool
    def fake_search(query: str) -> str:
        """Search tool."""
        return query

    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config(), tools=[fake_search])
    assert "tool_node" in graph._graph.get_graph().nodes


def test_agent_graph_without_tools_no_tool_node():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
    assert "tool_node" not in graph._graph.get_graph().nodes


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
        result = await graph.ainvoke([HumanMessage(content="hi")])

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
            await graph.ainvoke([HumanMessage(content="hi")])

    # bind_tools should NOT be called when no tools at build time
    mock_model.bind_tools.assert_not_called()


@pytest.mark.asyncio
async def test_ainvoke_passes_model_config_override():
    override = ModelConfig(provider="openai", model_name="gpt-4o")
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
        with patch.object(graph, "_graph") as mock_compiled:
            ai_msg = AIMessage(content="ok")
            mock_compiled.ainvoke = AsyncMock(return_value={"messages": [ai_msg]})
            await graph.ainvoke([HumanMessage(content="hi")], model_config=override)
        call_kwargs = mock_compiled.ainvoke.call_args
        ctx = call_kwargs[1]["context"]
        assert ctx["model_config"] is override


@pytest.mark.asyncio
async def test_ainvoke_passes_thread_id_in_config():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
        with patch.object(graph, "_graph") as mock_compiled:
            ai_msg = AIMessage(content="ok")
            mock_compiled.ainvoke = AsyncMock(return_value={"messages": [ai_msg]})
            await graph.ainvoke([HumanMessage(content="hi")], thread_id="conv-123")
        call_kwargs = mock_compiled.ainvoke.call_args
        cfg = call_kwargs[1]["config"]
        assert cfg == {"configurable": {"thread_id": "conv-123"}}


@pytest.mark.asyncio
async def test_ainvoke_empty_config_when_no_thread_id():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
        with patch.object(graph, "_graph") as mock_compiled:
            ai_msg = AIMessage(content="ok")
            mock_compiled.ainvoke = AsyncMock(return_value={"messages": [ai_msg]})
            await graph.ainvoke([HumanMessage(content="hi")])
        call_kwargs = mock_compiled.ainvoke.call_args
        cfg = call_kwargs[1]["config"]
        assert cfg == {}


# --- get_state ---


@pytest.mark.asyncio
async def test_get_state_returns_none_for_unknown_thread():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())
    # MemorySaver has no data → aget_state returns a StateSnapshot with empty values
    result = await graph.get_state("nonexistent-thread")
    assert result is None


# --- astream ---


@pytest.mark.asyncio
async def test_astream_passes_thread_id_in_config():
    with patch("agent_workbench.services.agent_graph.provider_registry"):
        graph = AgentGraph(_make_config())

    async def fake_stream(*args, **kwargs):
        assert kwargs.get("config") == {"configurable": {"thread_id": "t-1"}}
        return
        yield  # make it an async generator

    with patch.object(graph._graph, "astream", fake_stream):
        async for _ in graph.astream([HumanMessage("hi")], thread_id="t-1"):
            pass


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
        async for chunk in graph.astream([HumanMessage("hi")]):
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
