"""Docling-based document conversion and chunking service."""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

_DOCUMENT_TOKEN_BUDGET = 24_000


@dataclass
class DocumentChunk:
    index: int
    content: str
    heading: str
    page: Optional[int]
    token_count: int


class DoclingService:
    def __init__(self) -> None:
        self._converter = None
        self._chunker = None

    def _ensure_init(self) -> None:
        if self._converter is None:
            from docling.chunking import HierarchicalChunker
            from docling.document_converter import DocumentConverter

            self._converter = DocumentConverter()
            self._chunker = HierarchicalChunker()
            logger.info("DoclingService initialised")

    def convert(self, file_path: str) -> list[DocumentChunk]:
        self._ensure_init()
        assert self._converter is not None
        assert self._chunker is not None

        document = self._converter.convert(file_path).document
        raw_chunks = list(self._chunker.chunk(dl_doc=document))
        chunks = []
        for i, chunk in enumerate(raw_chunks):
            heading = ""
            if hasattr(self._chunker, "contextualize"):
                contextualized = self._chunker.contextualize(chunk)
                chunk_text = chunk.text
                if contextualized != chunk_text:
                    heading = contextualized.replace(chunk_text, "").strip()

            page: Optional[int] = None
            meta = getattr(chunk, "meta", None)
            if meta is not None:
                doc_items = getattr(meta, "doc_items", None)
                if doc_items:
                    prov = getattr(doc_items[0], "prov", None)
                    if prov:
                        page = getattr(prov[0], "page_no", None)

            chunks.append(
                DocumentChunk(
                    index=i,
                    content=chunk.text,
                    heading=heading,
                    page=page,
                    token_count=len(chunk.text) // 4,
                )
            )
        return chunks

    def build_context_block(
        self,
        chunks: list[DocumentChunk],
        token_budget: int = _DOCUMENT_TOKEN_BUDGET,
    ) -> str:
        if not chunks:
            return ""
        selected, used = [], 0
        for chunk in chunks:
            if used + chunk.token_count > token_budget:
                break
            selected.append(chunk)
            used += chunk.token_count
        parts = [
            f"{c.heading}\n{c.content}".strip() if c.heading else c.content
            for c in selected
        ]
        suffix = (
            f"\n\n[Document truncated — {used:,} of "
            f"{sum(c.token_count for c in chunks):,} estimated tokens shown. "
            f"Use the document_retrieval tool to query specific sections by topic.]"
            if len(selected) < len(chunks)
            else ""
        )
        return "\n\n".join(parts) + suffix


_docling_service = DoclingService()
