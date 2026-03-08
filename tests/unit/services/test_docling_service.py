"""Unit tests for DoclingService."""

from unittest.mock import MagicMock

import pytest

from agent_workbench.services.docling_service import DoclingService, DocumentChunk


@pytest.mark.unit
def test_init_does_not_import_docling() -> None:
    """DoclingService() does not import docling on __init__."""
    svc = DoclingService()
    assert svc._converter is None
    assert svc._chunker is None


@pytest.mark.unit
def test_convert_returns_document_chunks() -> None:
    svc = DoclingService()
    mock_converter = MagicMock()
    mock_chunker = MagicMock()
    mock_chunk = MagicMock()
    mock_chunk.text = "Hello world this is content"
    mock_chunk.meta = MagicMock()
    mock_chunk.meta.doc_items = [MagicMock()]
    mock_chunk.meta.doc_items[0].prov = [MagicMock()]
    mock_chunk.meta.doc_items[0].prov[0].page_no = 1
    mock_chunker.chunk.return_value = [mock_chunk]
    mock_chunker.contextualize = MagicMock(
        return_value="Section\nHello world this is content"
    )
    svc._converter = mock_converter
    svc._chunker = mock_chunker
    mock_converter.convert.return_value.document = MagicMock()

    chunks = svc.convert("/fake/path.pdf")

    assert len(chunks) == 1
    assert isinstance(chunks[0], DocumentChunk)
    assert chunks[0].content == "Hello world this is content"
    assert chunks[0].page == 1
    assert chunks[0].index == 0


@pytest.mark.unit
def test_build_context_block_no_truncation() -> None:
    chunks = [
        DocumentChunk(
            index=0, content="Content A", heading="", page=1, token_count=100
        ),
        DocumentChunk(
            index=1, content="Content B", heading="", page=2, token_count=100
        ),
    ]
    svc = DoclingService()
    result = svc.build_context_block(chunks, token_budget=1000)
    assert "Content A" in result
    assert "Content B" in result
    assert "document_retrieval" not in result


@pytest.mark.unit
def test_build_context_block_truncates_with_suffix() -> None:
    chunks = [
        DocumentChunk(
            index=0, content="Content A", heading="", page=1, token_count=100
        ),
        DocumentChunk(
            index=1, content="Content B", heading="", page=2, token_count=100
        ),
    ]
    svc = DoclingService()
    result = svc.build_context_block(chunks, token_budget=150)
    assert "Content A" in result
    assert "Content B" not in result
    assert "document_retrieval" in result


@pytest.mark.unit
def test_build_context_block_empty() -> None:
    svc = DoclingService()
    result = svc.build_context_block([], token_budget=1000)
    assert result == ""
