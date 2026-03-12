"""Unit tests for ContentRetrieverTool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.content_retriever_tool import (
    ContentRetrieverTool,
    DocumentRetrievalContext,
    RetrievedChunk,
)
from agent_workbench.services.embedding_service import EmbeddingService


def _make_model_config() -> ModelConfig:
    return ModelConfig(
        provider="anthropic",
        model_name="claude-3-5-haiku-20241022",
    )


def _make_tool() -> ContentRetrieverTool:
    async def fake_session():  # type: ignore[misc]
        return
        yield

    mock_es = MagicMock(spec=EmbeddingService)

    with patch("agent_workbench.services.document_context_graph.DocumentContextGraph"):
        return ContentRetrieverTool(
            session_factory=fake_session,
            model_config=_make_model_config(),
            embedding_service=mock_es,
        )


# --- metadata ---


def test_tool_metadata():
    tool = _make_tool()
    assert tool.name == "document_retrieval"
    assert "uploaded files" in tool.description


# --- _arun no conversation_id ---


@pytest.mark.asyncio
async def test_arun_no_conversation_id_returns_message():
    tool = _make_tool()
    result = await tool._arun("what is this?", config={"configurable": {}})
    assert "No active conversation" in result


@pytest.mark.asyncio
async def test_arun_no_config_returns_message():
    tool = _make_tool()
    result = await tool._arun("what is this?", config=None)
    assert "No active conversation" in result


# --- delegation to DocumentContextGraph ---


@pytest.mark.asyncio
async def test_arun_delegates_to_doc_graph():
    async def fake_session():  # type: ignore[misc]
        return
        yield

    mock_es = MagicMock(spec=EmbeddingService)
    mock_doc_graph = MagicMock()
    mock_doc_graph.ainvoke = AsyncMock(return_value="Graph answer.")

    with patch(
        "agent_workbench.services.document_context_graph.DocumentContextGraph",
        return_value=mock_doc_graph,
    ):
        tool = ContentRetrieverTool(
            session_factory=fake_session,
            model_config=_make_model_config(),
            embedding_service=mock_es,
        )

    result = await tool._arun(
        "what does section 3 say?",
        config={"configurable": {"thread_id": "conv-uuid-123"}},
    )

    mock_doc_graph.ainvoke.assert_awaited_once_with(
        "what does section 3 say?", "conv-uuid-123"
    )
    assert result == "Graph answer."


@pytest.mark.asyncio
async def test_arun_returns_str():
    async def fake_session():  # type: ignore[misc]
        return
        yield

    mock_es = MagicMock(spec=EmbeddingService)
    mock_doc_graph = MagicMock()
    mock_doc_graph.ainvoke = AsyncMock(return_value="Any string answer.")

    with patch(
        "agent_workbench.services.document_context_graph.DocumentContextGraph",
        return_value=mock_doc_graph,
    ):
        tool = ContentRetrieverTool(
            session_factory=fake_session,
            model_config=_make_model_config(),
            embedding_service=mock_es,
        )

    result = await tool._arun(
        "summarize",
        config={"configurable": {"thread_id": "conv-uuid-xyz"}},
    )
    assert isinstance(result, str)


# --- shared models ---


def test_retrieved_chunk_defaults():
    chunk = RetrievedChunk(
        chunk_index=0, content="text", filename="doc.pdf", token_count=5
    )
    assert chunk.score == 0.0
    assert chunk.heading is None
    assert chunk.page is None


def test_document_retrieval_context_defaults():
    ctx = DocumentRetrievalContext(query="q", conversation_id="c")
    assert ctx.chunks == []
    assert ctx.total_tokens == 0
