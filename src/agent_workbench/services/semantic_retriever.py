"""SemanticRetriever — shared retrieval pipeline for document and web content.

Used by DocumentContextGraph (uploaded docs) and WebResearchGraph (web content).
The data source differs; this pipeline is identical for both.
"""

import asyncio

from .content_retriever_tool import RetrievedChunk
from .embedding_service import EmbeddingService

_RETRIEVAL_TOKEN_BUDGET = 16_000


class SemanticRetriever:
    """Encapsulates embedding, selection, and chunking for semantic retrieval."""

    def __init__(self, embedding_service: EmbeddingService) -> None:
        self._embedding_service = embedding_service

    def chunk_text(
        self,
        text: str,
        filename: str,
        chunk_size: int = 512,
    ) -> list[RetrievedChunk]:
        """Split raw text into RetrievedChunk objects.

        Splits on double newlines (paragraphs). Accumulates paragraphs until
        chunk_size token estimate is reached, then starts a new chunk.
        Used by WebResearchGraph to chunk Firecrawl responses before embedding.
        """
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[RetrievedChunk] = []
        current: list[str] = []
        current_tokens = 0
        chunk_index = 0

        for para in paragraphs:
            para_tokens = max(1, len(para) // 4)
            if current_tokens + para_tokens > chunk_size and current:
                content = "\n\n".join(current)
                chunks.append(
                    RetrievedChunk(
                        chunk_index=chunk_index,
                        content=content,
                        filename=filename,
                        token_count=max(1, len(content) // 4),
                    )
                )
                chunk_index += 1
                current = [para]
                current_tokens = para_tokens
            else:
                current.append(para)
                current_tokens += para_tokens

        if current:
            content = "\n\n".join(current)
            chunks.append(
                RetrievedChunk(
                    chunk_index=chunk_index,
                    content=content,
                    filename=filename,
                    token_count=max(1, len(content) // 4),
                )
            )

        if not chunks:
            # Fallback: return the first 2000 chars as a single chunk
            return [
                RetrievedChunk(
                    chunk_index=0,
                    content=text[:2000],
                    filename=filename,
                    token_count=max(1, min(len(text), 2000) // 4),
                )
            ]

        return chunks

    async def embed_chunks(self, chunks: list[RetrievedChunk]) -> list[list[float]]:
        """Embed chunk contents. CPU-bound — runs in thread pool."""
        return await asyncio.to_thread(
            self._embedding_service.embed_batch,
            [c.content for c in chunks],
        )

    async def embed_query(self, query: str) -> list[float]:
        """Embed a single query string. CPU-bound — runs in thread pool."""
        return await asyncio.to_thread(self._embedding_service.embed, query)

    def select(
        self,
        query_vec: list[float],
        chunks: list[RetrievedChunk],
        embeddings: list[list[float]],
        budget: int = _RETRIEVAL_TOKEN_BUDGET,
    ) -> list[RetrievedChunk]:
        """Cosine similarity → top-K within token budget → document order.

        Scores all chunks, greedily selects within token budget, then restores
        original document order for coherent synthesis. Falls back to top-5 by
        score if all chunks exceed the budget.
        """
        scores = self._embedding_service.cosine_similarity(query_vec, embeddings)
        scored = sorted(zip(scores, chunks), key=lambda x: x[0], reverse=True)
        selected, used = [], 0
        for score, chunk in scored:
            if used + chunk.token_count > budget:
                continue
            chunk.score = score
            selected.append(chunk)
            used += chunk.token_count
        if not selected:
            selected = [c for _, c in scored[:5]]
        selected.sort(key=lambda c: c.chunk_index)
        return selected
