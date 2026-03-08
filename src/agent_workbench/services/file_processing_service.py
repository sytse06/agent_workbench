"""File processing service: Docling conversion → chunks → DB storage → context block."""

import logging
import os
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from agent_workbench.models.database import DocumentChunkModel, DocumentModel
from agent_workbench.services.docling_service import DoclingService, DocumentChunk

logger = logging.getLogger(__name__)

_MIME_MAP = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
    ".md": "text/markdown",
}


class FileProcessingService:
    def __init__(self, docling: DoclingService) -> None:
        self.docling = docling

    def convert(self, file_path: str) -> list[DocumentChunk]:
        """Synchronous Docling conversion — safe to run via asyncio.to_thread."""
        return self.docling.convert(file_path)

    async def save_and_build_context(
        self,
        chunks: list[DocumentChunk],
        filename: str,
        conversation_id: str,
        session: AsyncSession,
    ) -> Optional[str]:
        """Save document + chunks to DB and return the context block string."""
        ext = os.path.splitext(filename)[1].lower()
        doc_id = uuid4()

        await DocumentModel.create(
            session,
            id=doc_id,
            conversation_id=UUID(conversation_id) if conversation_id else None,
            filename=filename,
            mime_type=_MIME_MAP.get(ext),
            status="processed",
            total_tokens=sum(c.token_count for c in chunks),
        )

        for chunk in chunks:
            session.add(
                DocumentChunkModel(
                    id=uuid4(),
                    document_id=doc_id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    heading=chunk.heading or None,
                    page=chunk.page,
                    token_count=chunk.token_count,
                )
            )
        await session.commit()

        return self.docling.build_context_block(chunks)
