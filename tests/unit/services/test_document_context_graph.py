"""Unit tests for DocumentContextGraph."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.content_retriever_tool import RetrievedChunk
from agent_workbench.services.document_context_graph import (
    DocumentContextGraph,
)
from agent_workbench.services.embedding_service import EmbeddingService


def _make_config() -> ModelConfig:
    return ModelConfig(provider="anthropic", model_name="claude-3-5-haiku-20241022")


def _make_chunk(
    content: str, token_count: int = 10, chunk_index: int = 0
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_index=chunk_index,
        content=content,
        filename="test.pdf",
        token_count=token_count,
    )


def _make_graph(session_factory=None, embedding_service=None) -> DocumentContextGraph:
    if session_factory is None:

        async def session_factory():  # type: ignore[misc]
            return
            yield

    if embedding_service is None:
        embedding_service = MagicMock(spec=EmbeddingService)
        embedding_service.embed.return_value = [0.1] * 384
        embedding_service.embed_batch.return_value = [[0.1] * 384]
        embedding_service.cosine_similarity.return_value = [0.9]
    with patch("agent_workbench.services.document_context_graph.provider_registry"):
        return DocumentContextGraph(
            session_factory=session_factory,
            embedding_service=embedding_service,
            model_config=_make_config(),
        )


# --- graph builds ---


def test_document_context_graph_builds_without_error():
    graph = _make_graph()
    assert graph._graph is not None


def test_document_context_graph_has_expected_nodes():
    graph = _make_graph()
    nodes = graph._graph.get_graph().nodes
    assert "load_chunks" in nodes
    assert "embed_chunks" in nodes
    assert "retrieve" in nodes


# --- load_chunks_node cache behaviour ---


@pytest.mark.asyncio
async def test_load_chunks_node_skips_when_already_loaded():
    """Second ainvoke skips _fetch_chunks — chunk cache dict has a hit."""
    import agent_workbench.services.document_context_graph as dcg

    chunks = [_make_chunk("cached content", token_count=10)]
    conv_id = "conv-cache-load-test"

    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [0.5] * 384
    mock_es.embed_batch.return_value = [[0.5] * 384]
    mock_es.cosine_similarity.return_value = [0.9]

    with patch(
        "agent_workbench.services.document_context_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="answer"))
        mock_reg.create_model.return_value = mock_model

        graph = _make_graph(embedding_service=mock_es)

        fetch_mock = AsyncMock(return_value=chunks)
        with patch(
            "agent_workbench.services.document_context_graph._fetch_chunks",
            fetch_mock,
        ):
            # Pre-populate cache so load_chunks_node skips fetch
            dcg._chunk_cache[conv_id] = chunks
            dcg._embedding_cache[conv_id] = [[0.5] * 384]
            try:
                await graph.ainvoke("query", conv_id)
            finally:
                dcg._chunk_cache.pop(conv_id, None)
                dcg._embedding_cache.pop(conv_id, None)

    fetch_mock.assert_not_called()


# --- embed_chunks_node cache behaviour ---


@pytest.mark.asyncio
async def test_embed_chunks_node_skips_when_embeddings_computed():
    """Second ainvoke reuses cached embeddings — embed_batch not called again."""
    import agent_workbench.services.document_context_graph as dcg

    mock_embedding_service = MagicMock(spec=EmbeddingService)
    mock_embedding_service.embed.return_value = [0.5] * 384
    mock_embedding_service.embed_batch.return_value = [[0.5] * 384]
    mock_embedding_service.cosine_similarity.return_value = [0.9]

    chunks = [_make_chunk("content about python", token_count=10)]
    conv_id = "conv-embed-test"

    async def fake_session():  # type: ignore[misc]
        return
        yield

    # Ensure no stale cache from other tests
    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    with patch(
        "agent_workbench.services.document_context_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(
            return_value=MagicMock(content="synthesized answer")
        )
        mock_reg.create_model.return_value = mock_model

        graph = DocumentContextGraph(
            session_factory=fake_session,
            embedding_service=mock_embedding_service,
            model_config=_make_config(),
        )

        with patch(
            "agent_workbench.services.document_context_graph._fetch_chunks",
            AsyncMock(return_value=chunks),
        ):
            # First call — should embed
            await graph.ainvoke("first query", conv_id)
            first_call_count = mock_embedding_service.embed_batch.call_count

            # Second call — embedding cache hit, should skip embed_batch
            await graph.ainvoke("second query", conv_id)
            second_call_count = mock_embedding_service.embed_batch.call_count

    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    assert first_call_count == 1
    assert second_call_count == 1  # not called again


# --- retrieve_node ---


@pytest.mark.asyncio
async def test_retrieve_node_returns_message_when_no_chunks():
    import agent_workbench.services.document_context_graph as dcg

    conv_id = "conv-empty"
    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    graph = _make_graph()
    with patch(
        "agent_workbench.services.document_context_graph._fetch_chunks",
        AsyncMock(return_value=[]),
    ):
        result = await graph.ainvoke("any query", conv_id)
    assert "No documents" in result


@pytest.mark.asyncio
async def test_retrieve_node_respects_token_budget():
    import agent_workbench.services.document_context_graph as dcg

    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [1.0] + [0.0] * 383
    # All chunks score equally high
    mock_es.embed_batch.return_value = [[1.0] + [0.0] * 383] * 3
    mock_es.cosine_similarity.return_value = [0.9, 0.9, 0.9]

    # Chunks totalling 18_000 tokens — exceeds 16_000 budget
    chunks = [
        _make_chunk("chunk A", token_count=6000, chunk_index=0),
        _make_chunk("chunk B", token_count=6000, chunk_index=1),
        _make_chunk("chunk C", token_count=6000, chunk_index=2),
    ]
    conv_id = "conv-budget-test"
    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    async def fake_session():  # type: ignore[misc]
        return
        yield

    with patch(
        "agent_workbench.services.document_context_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="answer"))
        mock_reg.create_model.return_value = mock_model

        graph = DocumentContextGraph(
            session_factory=fake_session,
            embedding_service=mock_es,
            model_config=_make_config(),
        )

        # Capture what _synthesize receives
        synthesized_chunks = []

        async def fake_synthesize(ctx, model_config):  # type: ignore[misc]
            synthesized_chunks.extend(ctx.chunks)
            return "answer"

        with patch(
            "agent_workbench.services.document_context_graph._fetch_chunks",
            AsyncMock(return_value=chunks),
        ):
            with patch(
                "agent_workbench.services.document_context_graph._synthesize",
                new=fake_synthesize,
            ):
                await graph.ainvoke("query", conv_id)

    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    total_tokens = sum(c.token_count for c in synthesized_chunks)
    assert total_tokens <= 16_000


@pytest.mark.asyncio
async def test_retrieve_node_restores_document_order():
    import agent_workbench.services.document_context_graph as dcg

    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [1.0] + [0.0] * 383
    mock_es.embed_batch.return_value = [[1.0] + [0.0] * 383] * 3
    # Reverse score order: chunk_index 2 scores highest
    mock_es.cosine_similarity.return_value = [0.3, 0.6, 0.9]

    chunks = [
        _make_chunk("first in doc", token_count=10, chunk_index=0),
        _make_chunk("second in doc", token_count=10, chunk_index=1),
        _make_chunk("third in doc", token_count=10, chunk_index=2),
    ]
    conv_id = "conv-order-test"
    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    async def fake_session():  # type: ignore[misc]
        return
        yield

    with patch(
        "agent_workbench.services.document_context_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="answer"))
        mock_reg.create_model.return_value = mock_model

        graph = DocumentContextGraph(
            session_factory=fake_session,
            embedding_service=mock_es,
            model_config=_make_config(),
        )

        received_order = []

        async def fake_synthesize(ctx, model_config):  # type: ignore[misc]
            received_order.extend(c.chunk_index for c in ctx.chunks)
            return "answer"

        with patch(
            "agent_workbench.services.document_context_graph._fetch_chunks",
            AsyncMock(return_value=chunks),
        ):
            with patch(
                "agent_workbench.services.document_context_graph._synthesize",
                new=fake_synthesize,
            ):
                await graph.ainvoke("query", conv_id)

    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    assert received_order == sorted(received_order)


# --- ainvoke ---


@pytest.mark.asyncio
async def test_ainvoke_returns_str():
    import agent_workbench.services.document_context_graph as dcg

    conv_id = "conv-str-test"
    dcg._chunk_cache.pop(conv_id, None)
    dcg._embedding_cache.pop(conv_id, None)

    graph = _make_graph()
    with patch(
        "agent_workbench.services.document_context_graph._fetch_chunks",
        AsyncMock(return_value=[]),
    ):
        result = await graph.ainvoke("query", conv_id)
    assert isinstance(result, str)
