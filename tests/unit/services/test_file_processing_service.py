"""Unit tests for FileProcessingService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.services.docling_service import DocumentChunk
from agent_workbench.services.file_processing_service import FileProcessingService


def make_service() -> tuple:
    mock_docling = MagicMock()
    return FileProcessingService(docling=mock_docling), mock_docling


@pytest.mark.unit
def test_convert_calls_docling() -> None:
    svc, mock_docling = make_service()
    mock_docling.convert.return_value = []
    svc.convert("/fake/path.pdf")
    mock_docling.convert.assert_called_once_with("/fake/path.pdf")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_and_build_context_saves_document() -> None:
    svc, mock_docling = make_service()
    chunks = [
        DocumentChunk(index=0, content="Hello", heading="", page=1, token_count=5)
    ]
    mock_docling.build_context_block.return_value = "Hello context"

    mock_session = AsyncMock()

    with patch(
        "agent_workbench.services.file_processing_service.DocumentModel"
    ) as MockDoc:
        MockDoc.create = AsyncMock(return_value=MagicMock())
        result = await svc.save_and_build_context(
            chunks, "test.pdf", "00000000-0000-0000-0000-000000000001", mock_session
        )

    MockDoc.create.assert_called_once()
    mock_session.add.assert_called()
    mock_session.commit.assert_awaited_once()
    assert result == "Hello context"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_save_and_build_context_returns_none_on_empty_chunks() -> None:
    svc, mock_docling = make_service()
    mock_docling.build_context_block.return_value = ""
    mock_session = AsyncMock()

    with patch(
        "agent_workbench.services.file_processing_service.DocumentModel"
    ) as MockDoc:
        MockDoc.create = AsyncMock(return_value=MagicMock())
        result = await svc.save_and_build_context(
            [], "test.pdf", "00000000-0000-0000-0000-000000000001", mock_session
        )

    assert result == ""
