"""WebResearchGraph — inner subgraph for multi-turn web content retrieval.

Mirrors the structure of DocumentContextGraph but the data source is Firecrawl
instead of the document DB. Caches chunks and embeddings by (conversation_id,
cache_key) so follow-up questions on the same URL/query skip the API call and
re-embedding entirely.

execute_node is stubbed when firecrawl_client is None (PR-2.5b). Real dispatch
is wired in PR-2.5c.
"""

import logging
from typing import Any, Optional, Type

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from ..models.schemas import ModelConfig
from .providers import provider_registry
from .semantic_retriever import SemanticRetriever

logger = logging.getLogger(__name__)

VALID_SKILLS = {"scrape", "search", "crawl", "extract"}

# Raw content from Firecrawl is trimmed before chunking to prevent oversized inputs.
# Rough estimate: 4 chars ≈ 1 token.
_WEB_TOKEN_BUDGET = 12_000
_WEB_CHAR_BUDGET = _WEB_TOKEN_BUDGET * 4

_WEB_SYNTHESIS_SYSTEM = (
    "You are a precise web research assistant. Answer the query using ONLY "
    "the provided web content. Be concise. Cite sources as [source](url) "
    "inline where possible. If the content does not answer the query, say so "
    "directly."
)

# Module-level caches keyed by conversation_id → cache_key.
# cache_key = URL for scrape/crawl/extract, normalized query for search.
_web_chunk_cache: dict[str, dict[str, list]] = {}
_web_embedding_cache: dict[str, dict[str, list]] = {}


class WebResearchState(TypedDict, total=False):
    """State for the web research subgraph.

    All fields optional (total=False) so nodes return partial updates.
    """

    query: str
    url: Optional[str]
    conversation_id: str
    skills_catalog: str  # SKILLS.md body — never leaves subgraph
    matched_skill: str  # scrape | search | crawl | extract
    chunks: list  # list[RetrievedChunk]
    chunk_embeddings: list  # list[list[float]]
    answer: str


def _cache_key(state: WebResearchState) -> str:
    """Derive cache key from matched skill and state.

    URL-bearing skills key on the URL; search keys on the query string.
    """
    skill = state.get("matched_skill", "search")
    if skill in ("scrape", "crawl", "extract") and state.get("url"):
        return str(state["url"])
    return str(state.get("query", ""))


class WebResearchGraph:
    """Compiled StateGraph for web content retrieval with multi-turn caching."""

    def __init__(
        self,
        skills_catalog: str,
        semantic_retriever: SemanticRetriever,
        model_config: ModelConfig,
        firecrawl_client: Optional[Any] = None,
    ) -> None:
        self._skills_catalog = skills_catalog
        self._semantic_retriever = semantic_retriever
        self._model_config = model_config
        self._firecrawl_client = firecrawl_client
        self._graph: CompiledStateGraph = self._build()

    def _build(self) -> CompiledStateGraph:
        skills_catalog = self._skills_catalog
        semantic_retriever = self._semantic_retriever
        model_config = self._model_config
        firecrawl_client = self._firecrawl_client

        async def load_skills_node(state: WebResearchState) -> dict:
            return {"skills_catalog": skills_catalog}

        async def match_skill_node(state: WebResearchState) -> dict:
            from langchain_core.messages import HumanMessage, SystemMessage

            logger.info(
                "WebResearchGraph.match_skill: query=%r url=%r",
                state.get("query"),
                state.get("url"),
            )
            model = provider_registry.create_model(model_config)
            response = await model.ainvoke(
                [
                    SystemMessage(
                        content=(
                            "You are a skill router. Given a user query and a skills "
                            "catalog, respond with ONLY the skill name that best "
                            "matches. "
                            f"Valid values: {', '.join(sorted(VALID_SKILLS))}"
                        )
                    ),
                    HumanMessage(
                        content=(
                            f"Skills catalog:\n{state['skills_catalog']}\n\n"
                            f"Query: {state['query']}\n"
                            f"URL provided: {state.get('url') or 'none'}"
                        )
                    ),
                ]
            )
            skill = str(response.content).strip().lower()
            matched = skill if skill in VALID_SKILLS else "search"
            logger.info("WebResearchGraph.match_skill: matched=%r", matched)
            return {"matched_skill": matched}

        async def execute_node(state: WebResearchState) -> dict:
            key = _cache_key(state)
            conv_id = state["conversation_id"]
            logger.info(
                "WebResearchGraph.execute: skill=%r key=%r cache_keys=%r",
                state.get("matched_skill"),
                key,
                list(_web_chunk_cache.get(conv_id, {}).keys()),
            )
            if conv_id in _web_chunk_cache and key in _web_chunk_cache[conv_id]:
                logger.info(
                    "WebResearchGraph.execute: cache HIT — %d chunks",
                    len(_web_chunk_cache[conv_id][key]),
                )
                return {"chunks": _web_chunk_cache[conv_id][key]}

            if firecrawl_client is None:
                raw = (
                    "No web content available — FIRECRAWL_API_KEY is not set. "
                    "The web_research tool requires a Firecrawl API key to fetch "
                    "live content."
                )
                logger.warning("WebResearchGraph.execute: firecrawl_client is None")
            else:
                raw = await _dispatch(firecrawl_client, state)
                if len(raw) > _WEB_CHAR_BUDGET:
                    raw = raw[:_WEB_CHAR_BUDGET]
                    logger.info(
                        "WebResearchGraph.execute: trimmed raw to %d chars",
                        _WEB_CHAR_BUDGET,
                    )

            chunks = semantic_retriever.chunk_text(raw, filename=key or "web")
            logger.info("WebResearchGraph.execute: chunked into %d chunks", len(chunks))
            _web_chunk_cache.setdefault(conv_id, {})[key] = chunks
            return {"chunks": chunks}

        async def embed_chunks_node(state: WebResearchState) -> dict:
            key = _cache_key(state)
            conv_id = state["conversation_id"]
            logger.info(
                "WebResearchGraph.embed_chunks: conv_id=%r key=%r",
                conv_id,
                key,
            )
            if conv_id in _web_embedding_cache and key in _web_embedding_cache[conv_id]:
                logger.info(
                    "WebResearchGraph.embed_chunks: cache HIT — %d embeddings",
                    len(_web_embedding_cache[conv_id][key]),
                )
                return {"chunk_embeddings": _web_embedding_cache[conv_id][key]}

            chunks = state.get("chunks") or []
            if not chunks:
                return {"chunk_embeddings": []}

            embeddings = await semantic_retriever.embed_chunks(chunks)
            logger.info(
                "WebResearchGraph.embed_chunks: computed %d embeddings", len(embeddings)
            )
            _web_embedding_cache.setdefault(conv_id, {})[key] = embeddings
            return {"chunk_embeddings": embeddings}

        async def retrieve_node(state: WebResearchState) -> dict:
            from langchain_core.messages import HumanMessage, SystemMessage

            chunks = state.get("chunks") or []
            embeddings = state.get("chunk_embeddings") or []
            logger.info(
                "WebResearchGraph.retrieve: chunks=%d embeddings=%d",
                len(chunks),
                len(embeddings),
            )
            if not chunks or not embeddings:
                return {"answer": "No web content could be retrieved."}

            query_vec = await semantic_retriever.embed_query(state["query"])
            selected = semantic_retriever.select(query_vec, chunks, embeddings)

            parts = [f"[{c.filename}]\n{c.content}" for c in selected]
            model = provider_registry.create_model(model_config)
            response = await model.ainvoke(
                [
                    SystemMessage(content=_WEB_SYNTHESIS_SYSTEM),
                    HumanMessage(
                        content=(
                            f"Web content:\n\n{chr(10).join(parts)}"
                            f"\n\nQuery: {state['query']}"
                        )
                    ),
                ]
            )
            return {"answer": str(response.content)}

        builder = StateGraph(WebResearchState)
        builder.add_node("load_skills", load_skills_node)
        builder.add_node("match_skill", match_skill_node)
        builder.add_node("execute", execute_node)
        builder.add_node("embed_chunks", embed_chunks_node)
        builder.add_node("retrieve", retrieve_node)
        builder.set_entry_point("load_skills")
        builder.add_edge("load_skills", "match_skill")
        builder.add_edge("match_skill", "execute")
        builder.add_edge("execute", "embed_chunks")
        builder.add_edge("embed_chunks", "retrieve")
        builder.add_edge("retrieve", END)
        return builder.compile()

    async def ainvoke(
        self,
        query: str,
        conversation_id: str,
        url: Optional[str] = None,
    ) -> str:
        result = await self._graph.ainvoke(
            {"query": query, "conversation_id": conversation_id, "url": url}
        )
        return result.get("answer", "No answer produced.")


async def _dispatch(firecrawl_client: Any, state: WebResearchState) -> str:
    """Dispatch to the correct FirecrawlClient method based on matched_skill."""
    skill = state.get("matched_skill", "search")
    url = state.get("url") or ""
    query = state.get("query", "")

    if skill == "scrape":
        return await firecrawl_client.scrape(url or query)
    if skill == "crawl":
        return await firecrawl_client.crawl(url or query)
    if skill == "extract":
        return await firecrawl_client.extract(url or query, query)
    # search (default)
    return await firecrawl_client.search(query)


# --- Tool wrapper ---


class WebResearchInput(BaseModel):
    query: str = Field(description="The research question or topic to search for")
    url: Optional[str] = Field(
        default=None,
        description=(
            "Specific URL to scrape or crawl (if the user referenced one). "
            "Omit for general web searches."
        ),
    )


class WebResearchTool(BaseTool):
    name: str = "web_research"
    description: str = "Search and retrieve content from the web."
    args_schema: Type[BaseModel] = WebResearchInput

    _graph: Any = None

    def __init__(self, graph: Any, description: str, **data: Any) -> None:
        super().__init__(description=description, **data)
        object.__setattr__(self, "_graph", graph)

    def _run(self, query: str, url: Optional[str] = None, **kwargs: Any) -> str:
        raise NotImplementedError("Use async version")

    async def _arun(
        self,
        query: str,
        url: Optional[str] = None,
        config: RunnableConfig = None,  # type: ignore[assignment]  # bare type required for config injection
        **kwargs: Any,
    ) -> str:
        conversation_id = (config or {}).get("configurable", {}).get("thread_id", "")
        if not conversation_id:
            return "No active conversation — cannot perform web research."
        return await self._graph.ainvoke(query, conversation_id, url)
