"""Unit tests for SemanticRetriever."""

from unittest.mock import MagicMock

import pytest

from agent_workbench.services.content_retriever_tool import RetrievedChunk
from agent_workbench.services.embedding_service import EmbeddingService
from agent_workbench.services.semantic_retriever import (
    _RETRIEVAL_TOKEN_BUDGET,
    SemanticRetriever,
)


def _make_retriever(
    embed_return=None,
    embed_batch_return=None,
    cosine_return=None,
) -> SemanticRetriever:
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = embed_return or [0.1] * 384
    mock_es.embed_batch.return_value = embed_batch_return or [[0.1] * 384]
    mock_es.cosine_similarity.return_value = cosine_return or [0.9]
    return SemanticRetriever(mock_es)


def _make_chunk(
    content: str = "text",
    token_count: int = 10,
    chunk_index: int = 0,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_index=chunk_index,
        content=content,
        filename="test.pdf",
        token_count=token_count,
    )


# --- chunk_text ---


def test_chunk_text_returns_at_least_one_chunk():
    r = _make_retriever()
    chunks = r.chunk_text("Hello world.", filename="page.md")
    assert len(chunks) >= 1


def test_chunk_text_fallback_on_empty_string():
    r = _make_retriever()
    chunks = r.chunk_text("", filename="empty.md")
    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0


def test_chunk_text_chunk_index_is_sequential():
    r = _make_retriever()
    text = "\n\n".join(f"Paragraph {i} " * 50 for i in range(20))
    chunks = r.chunk_text(text, filename="long.md", chunk_size=100)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_text_assigns_filename():
    r = _make_retriever()
    chunks = r.chunk_text("Some content.", filename="article.md")
    assert all(c.filename == "article.md" for c in chunks)


def test_chunk_text_token_count_positive():
    r = _make_retriever()
    chunks = r.chunk_text("A" * 100, filename="doc.md")
    assert all(c.token_count > 0 for c in chunks)


# --- embed_chunks ---


@pytest.mark.asyncio
async def test_embed_chunks_calls_embed_batch_once():
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed_batch.return_value = [[0.1] * 384, [0.2] * 384]
    r = SemanticRetriever(mock_es)

    chunks = [_make_chunk("first"), _make_chunk("second", chunk_index=1)]
    result = await r.embed_chunks(chunks)

    mock_es.embed_batch.assert_called_once_with(["first", "second"])
    assert len(result) == 2


@pytest.mark.asyncio
async def test_embed_chunks_returns_n_embeddings_for_n_chunks():
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed_batch.return_value = [[0.0] * 384] * 5
    r = SemanticRetriever(mock_es)

    chunks = [_make_chunk(f"c{i}", chunk_index=i) for i in range(5)]
    result = await r.embed_chunks(chunks)
    assert len(result) == 5


# --- embed_query ---


@pytest.mark.asyncio
async def test_embed_query_calls_embed_once():
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [0.5] * 384
    r = SemanticRetriever(mock_es)

    result = await r.embed_query("what is langraph?")

    mock_es.embed.assert_called_once_with("what is langraph?")
    assert len(result) == 384


# --- select ---


def test_select_respects_token_budget():
    # 3 chunks × 6000 tokens = 18_000, budget = 16_000 → only 2 fit
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.cosine_similarity.return_value = [0.9, 0.9, 0.9]
    r = SemanticRetriever(mock_es)

    chunks = [
        _make_chunk("A", token_count=6000, chunk_index=0),
        _make_chunk("B", token_count=6000, chunk_index=1),
        _make_chunk("C", token_count=6000, chunk_index=2),
    ]
    embeddings = [[0.1] * 384] * 3
    query_vec = [0.1] * 384

    selected = r.select(query_vec, chunks, embeddings)
    total = sum(c.token_count for c in selected)
    assert total <= _RETRIEVAL_TOKEN_BUDGET


def test_select_restores_document_order():
    # Scores are reversed: chunk_index 2 scores highest
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.cosine_similarity.return_value = [0.3, 0.6, 0.9]
    r = SemanticRetriever(mock_es)

    chunks = [
        _make_chunk("first", token_count=10, chunk_index=0),
        _make_chunk("second", token_count=10, chunk_index=1),
        _make_chunk("third", token_count=10, chunk_index=2),
    ]
    embeddings = [[0.1] * 384] * 3
    query_vec = [0.1] * 384

    selected = r.select(query_vec, chunks, embeddings)
    indices = [c.chunk_index for c in selected]
    assert indices == sorted(indices)


def test_select_fallback_when_all_chunks_exceed_budget():
    # Each chunk exceeds budget on its own
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.cosine_similarity.return_value = [0.9, 0.8, 0.7, 0.6, 0.5, 0.4]
    r = SemanticRetriever(mock_es)

    chunks = [_make_chunk(f"c{i}", token_count=20_000, chunk_index=i) for i in range(6)]
    embeddings = [[0.1] * 384] * 6
    query_vec = [0.1] * 384

    selected = r.select(query_vec, chunks, embeddings, budget=16_000)
    # Fallback: top-5 by score
    assert len(selected) == 5


def test_select_custom_budget():
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.cosine_similarity.return_value = [0.9, 0.9, 0.9]
    r = SemanticRetriever(mock_es)

    chunks = [_make_chunk("x", token_count=100, chunk_index=i) for i in range(3)]
    embeddings = [[0.1] * 384] * 3
    query_vec = [0.1] * 384

    selected = r.select(query_vec, chunks, embeddings, budget=150)
    assert sum(c.token_count for c in selected) <= 150
