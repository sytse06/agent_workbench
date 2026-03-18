"""DocumentContextGraph — inner subgraph for multi-turn document retrieval.

Caches chunk embeddings in module-level dicts keyed by conversation_id so they
persist across tool calls within a session without LangGraph checkpointing.
On turn 2+, load_chunks and embed_chunks nodes are no-ops — only the query is
re-embedded (~50ms vs. full batch).

Checkpoint policy (whether to persist caches across restarts) is deferred to PR-2.6a.
"""

import logging
from typing import Callable

from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from ..models.schemas import ModelConfig
from .content_retriever_tool import (
    _SYNTHESIS_SYSTEM,
    DocumentRetrievalContext,
    RetrievedChunk,
)
from .providers import provider_registry
from .semantic_retriever import SemanticRetriever

logger = logging.getLogger(__name__)

# Module-level caches keyed by conversation_id — avoids MemorySaver serialization
# issues with Pydantic models. Float vectors stay in-process, not written to SQLite.
_chunk_cache: dict[str, list] = {}  # conversation_id → list[RetrievedChunk]
_embedding_cache: dict[str, list] = {}  # conversation_id → list[list[float]]


class DocumentContextState(TypedDict, total=False):
    """State for the document context subgraph.

    All fields are optional (total=False) so nodes can return partial updates.
    """

    conversation_id: str
    query: str
    chunks: list  # list[RetrievedChunk] — typed as list for TypedDict compat
    chunk_embeddings: list  # list[list[float]]
    answer: str


class DocumentContextGraph:
    """Compiled StateGraph for document retrieval with embedding cache."""

    def __init__(
        self,
        session_factory: Callable,
        semantic_retriever: SemanticRetriever,
        model_config: ModelConfig,
    ) -> None:
        self._session_factory = session_factory
        self._semantic_retriever = semantic_retriever
        self._model_config = model_config
        self._graph: CompiledStateGraph = self._build()

    def _build(self) -> CompiledStateGraph:
        session_factory = self._session_factory
        semantic_retriever = self._semantic_retriever
        model_config = self._model_config

        async def load_chunks_node(state: DocumentContextState) -> dict:
            conv_id = state.get("conversation_id", "")
            logger.info(
                "DocumentContextGraph.load_chunks: conv_id=%r cache_keys=%r",
                conv_id,
                list(_chunk_cache.keys()),
            )
            if conv_id in _chunk_cache:
                cached = _chunk_cache[conv_id]
                logger.info(
                    "DocumentContextGraph.load_chunks: cache HIT — %d chunks",
                    len(cached),
                )
                return {"chunks": cached}
            chunks = await _fetch_chunks(session_factory, conv_id)
            logger.info(
                "DocumentContextGraph.load_chunks: fetched %d chunks from DB",
                len(chunks),
            )
            _chunk_cache[conv_id] = chunks
            return {"chunks": chunks}

        async def embed_chunks_node(state: DocumentContextState) -> dict:
            conv_id = state.get("conversation_id", "")
            logger.info(
                "DocumentContextGraph.embed_chunks: conv_id=%r embedding_cache_keys=%r",
                conv_id,
                list(_embedding_cache.keys()),
            )
            if conv_id in _embedding_cache:
                cached = _embedding_cache[conv_id]
                logger.info(
                    "DocumentContextGraph.embed_chunks: cache HIT — %d embeddings",
                    len(cached),
                )
                return {"chunk_embeddings": cached}
            chunks = state.get("chunks") or []
            logger.info(
                "DocumentContextGraph.embed_chunks: computing embeddings for %d chunks",
                len(chunks),
            )
            if not chunks:
                return {"chunk_embeddings": []}
            embeddings = await semantic_retriever.embed_chunks(chunks)
            logger.info(
                "DocumentContextGraph.embed_chunks: stored %d embeddings",
                len(embeddings),
            )
            _embedding_cache[conv_id] = embeddings
            return {"chunk_embeddings": embeddings}

        async def retrieve_node(state: DocumentContextState) -> dict:
            chunks = state.get("chunks") or []
            embeddings = state.get("chunk_embeddings") or []
            logger.info(
                "DocumentContextGraph.retrieve: chunks=%d embeddings=%d",
                len(chunks),
                len(embeddings),
            )
            if not chunks or not embeddings:
                return {
                    "answer": "No documents have been attached to this conversation."
                }

            query_vec = await semantic_retriever.embed_query(state["query"])
            selected = semantic_retriever.select(query_vec, chunks, embeddings)

            ctx = DocumentRetrievalContext(
                query=state["query"],
                conversation_id=state["conversation_id"],
                chunks=selected,
                total_tokens=sum(c.token_count for c in selected),
            )
            answer = await _synthesize(ctx, model_config)
            return {"answer": answer}

        builder = StateGraph(DocumentContextState)
        builder.add_node("load_chunks", load_chunks_node)
        builder.add_node("embed_chunks", embed_chunks_node)
        builder.add_node("retrieve", retrieve_node)
        builder.set_entry_point("load_chunks")
        builder.add_edge("load_chunks", "embed_chunks")
        builder.add_edge("embed_chunks", "retrieve")
        builder.add_edge("retrieve", END)
        return builder.compile()

    async def ainvoke(self, query: str, conversation_id: str) -> str:
        result = await self._graph.ainvoke(
            {"query": query, "conversation_id": conversation_id},
        )
        return result.get("answer", "No answer produced.")


async def _fetch_chunks(session_factory: Callable, conversation_id: str) -> list:
    from uuid import UUID

    from sqlalchemy import select

    from ..models.database import DocumentChunkModel, DocumentModel

    chunks = []
    async for session in session_factory():
        result = await session.execute(
            select(DocumentChunkModel, DocumentModel.filename)
            .join(DocumentModel)
            .where(DocumentModel.conversation_id == UUID(conversation_id))
            .order_by(DocumentChunkModel.chunk_index)
        )
        for chunk_row, filename in result:
            chunks.append(
                RetrievedChunk(
                    chunk_index=chunk_row.chunk_index,
                    content=chunk_row.content,
                    filename=filename,
                    heading=chunk_row.heading,
                    page=chunk_row.page,
                    token_count=chunk_row.token_count,
                )
            )
    return chunks


async def _synthesize(ctx: DocumentRetrievalContext, model_config: ModelConfig) -> str:
    from langchain_core.messages import HumanMessage, SystemMessage

    parts = []
    for c in ctx.chunks:
        ref = c.filename
        if c.page:
            ref += f", p.{c.page}"
        if c.heading:
            ref += f", Section: {c.heading}"
        parts.append(f"[{ref}]\n{c.content}")

    model = provider_registry.create_model(model_config)
    response = await model.ainvoke(
        [
            SystemMessage(content=_SYNTHESIS_SYSTEM),
            HumanMessage(
                content=(
                    f"Document excerpts:\n\n{chr(10).join(parts)}"
                    f"\n\nQuery: {ctx.query}"
                )
            ),
        ]
    )
    return str(response.content)
