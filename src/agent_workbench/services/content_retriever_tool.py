"""ContentRetrieverTool — document retrieval with context isolation."""

import logging
from typing import Any, Callable, Optional, Type

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from ..models.schemas import ModelConfig

logger = logging.getLogger(__name__)

_RETRIEVAL_TOKEN_BUDGET = 16_000
_SYNTHESIS_SYSTEM = (
    "You are a precise document assistant. Answer the query using ONLY the "
    "provided document excerpts. Be concise. After each claim, add a citation "
    "in the format [filename, p.N] or [filename, Section: heading] using the "
    "metadata provided with each excerpt."
)


class RetrievedChunk(BaseModel):
    chunk_index: int
    content: str
    filename: str
    heading: Optional[str] = None
    page: Optional[int] = None
    token_count: int
    score: float = 0.0


class DocumentRetrievalContext(BaseModel):
    """Isolated Pydantic context — never enters MessagesState."""

    query: str
    conversation_id: str
    chunks: list[RetrievedChunk] = Field(default_factory=list)
    total_tokens: int = 0


class ContentRetrieverInput(BaseModel):
    query: str = Field(
        description="Question or topic to search for in attached documents"
    )


class ContentRetrieverTool(BaseTool):
    name: str = "document_retrieval"
    description: str = (
        "Search and retrieve information from documents attached to this conversation. "
        "Use when the user asks about content in uploaded files."
    )
    args_schema: Type[BaseModel] = ContentRetrieverInput

    # Private — injected at construction
    _doc_graph: Any = None

    def __init__(
        self,
        session_factory: Callable,
        model_config: ModelConfig,
        embedding_service: Any,  # EmbeddingService — Any avoids circular import
        **data: Any,
    ):
        super().__init__(**data)
        # Lazy import avoids circular dependency: document_context_graph imports
        # RetrievedChunk and DocumentRetrievalContext from this module.
        from .document_context_graph import DocumentContextGraph

        doc_graph = DocumentContextGraph(
            session_factory=session_factory,
            embedding_service=embedding_service,
            model_config=model_config,
        )
        object.__setattr__(self, "_doc_graph", doc_graph)

    def _run(self, query: str, **kwargs: Any) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        query: str,
        config: RunnableConfig,  # bare type — Optional[T] skips config injection
        **kwargs: Any,
    ) -> str:
        conversation_id = (config or {}).get("configurable", {}).get("thread_id", "")
        if not conversation_id:
            return "No active conversation — cannot retrieve documents."
        return await self._doc_graph.ainvoke(query, conversation_id)
