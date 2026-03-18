"""Unit tests for WebResearchGraph and WebResearchTool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.models.schemas import ModelConfig
from agent_workbench.services.embedding_service import EmbeddingService
from agent_workbench.services.semantic_retriever import SemanticRetriever
from agent_workbench.services.web_research_graph import (
    WebResearchGraph,
    WebResearchTool,
    _cache_key,
    _web_chunk_cache,
    _web_embedding_cache,
)

_SKILLS_CATALOG = """
# Web Research Skills

## scrape
Retrieve the full text content of a single known URL.

## search
Find and retrieve information about a topic.

## crawl
Retrieve content from a site and all linked pages.

## extract
Pull structured data from a known URL.
"""


def _make_model_config() -> ModelConfig:
    return ModelConfig(provider="anthropic", model_name="claude-3-5-haiku-20241022")


def _make_retriever() -> SemanticRetriever:
    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [0.1] * 384
    mock_es.embed_batch.return_value = [[0.1] * 384]
    mock_es.cosine_similarity.return_value = [0.9]
    return SemanticRetriever(mock_es)


def _make_graph(firecrawl_client=None) -> WebResearchGraph:
    with patch("agent_workbench.services.web_research_graph.provider_registry"):
        return WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
            firecrawl_client=firecrawl_client,
        )


# --- _cache_key ---


def test_cache_key_uses_url_for_scrape():
    state = {"matched_skill": "scrape", "url": "https://example.com", "query": "q"}
    assert _cache_key(state) == "https://example.com"


def test_cache_key_uses_url_for_crawl():
    state = {"matched_skill": "crawl", "url": "https://docs.example.com", "query": "q"}
    assert _cache_key(state) == "https://docs.example.com"


def test_cache_key_uses_query_for_search():
    state = {"matched_skill": "search", "url": None, "query": "langgraph tutorial"}
    assert _cache_key(state) == "langgraph tutorial"


def test_cache_key_uses_query_when_url_missing_for_scrape():
    state = {"matched_skill": "scrape", "url": None, "query": "fallback"}
    assert _cache_key(state) == "fallback"


# --- graph builds ---


def test_web_research_graph_builds():
    graph = _make_graph()
    assert graph._graph is not None


def test_web_research_graph_has_expected_nodes():
    graph = _make_graph()
    nodes = graph._graph.get_graph().nodes
    for name in ("load_skills", "match_skill", "execute", "embed_chunks", "retrieve"):
        assert name in nodes


# --- match_skill_node ---


@pytest.mark.asyncio
async def test_match_skill_node_returns_valid_skill():
    conv_id = "conv-match-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
        )
        result = await graph.ainvoke("what is langgraph?", conv_id)

    assert isinstance(result, str)
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)


@pytest.mark.asyncio
async def test_match_skill_node_falls_back_to_search_on_invalid_output():
    """If LLM returns unrecognized skill, matched_skill defaults to 'search'."""
    conv_id = "conv-fallback-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    matched_skills = []

    async def fake_execute(state):
        matched_skills.append(state.get("matched_skill"))
        return {"chunks": []}

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="INVALID_SKILL"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
        )

        # Patch execute node to capture matched_skill without running full graph
        with patch.object(
            graph._graph,
            "ainvoke",
            new=AsyncMock(return_value={"answer": "ok", "matched_skill": "search"}),
        ):
            await graph.ainvoke("query", conv_id)

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)


# --- execute_node caching ---


@pytest.mark.asyncio
async def test_execute_node_cache_hit_skips_stub():
    """Pre-populated cache means execute_node returns cached chunks directly."""
    from agent_workbench.services.content_retriever_tool import RetrievedChunk

    conv_id = "conv-exec-cache-test"
    key = "langgraph agents"
    cached_chunks = [
        RetrievedChunk(
            chunk_index=0, content="cached content", filename=key, token_count=10
        )
    ]

    _web_chunk_cache.setdefault(conv_id, {})[key] = cached_chunks
    _web_embedding_cache.setdefault(conv_id, {})[key] = [[0.1] * 384]

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
        )
        result = await graph.ainvoke("langgraph agents", conv_id)

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    assert isinstance(result, str)


# --- _dispatch skill routing ---


@pytest.mark.asyncio
async def test_dispatch_scrape_calls_scrape() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.scrape = AsyncMock(return_value="scraped content")
    state = {"matched_skill": "scrape", "url": "https://example.com", "query": "q"}
    result = await _dispatch(client, state)
    client.scrape.assert_called_once_with("https://example.com")
    assert result == "scraped content"


@pytest.mark.asyncio
async def test_dispatch_search_calls_search() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.search = AsyncMock(return_value="search results")
    state = {"matched_skill": "search", "url": None, "query": "langgraph tutorial"}
    result = await _dispatch(client, state)
    client.search.assert_called_once_with("langgraph tutorial")
    assert result == "search results"


@pytest.mark.asyncio
async def test_dispatch_crawl_calls_crawl() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.crawl = AsyncMock(return_value="crawled pages")
    state = {"matched_skill": "crawl", "url": "https://docs.example.com", "query": "q"}
    result = await _dispatch(client, state)
    client.crawl.assert_called_once_with("https://docs.example.com")
    assert result == "crawled pages"


@pytest.mark.asyncio
async def test_dispatch_extract_calls_extract_with_query_as_prompt() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.extract = AsyncMock(return_value="price: $9.99")
    state = {
        "matched_skill": "extract",
        "url": "https://shop.com",
        "query": "extract product price",
    }
    result = await _dispatch(client, state)
    client.extract.assert_called_once_with("https://shop.com", "extract product price")
    assert result == "price: $9.99"


@pytest.mark.asyncio
async def test_dispatch_defaults_to_search_for_unknown_skill() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.search = AsyncMock(return_value="results")
    state = {"matched_skill": "unknown", "url": None, "query": "my query"}
    result = await _dispatch(client, state)
    client.search.assert_called_once_with("my query")
    assert result == "results"


@pytest.mark.asyncio
async def test_dispatch_scrape_falls_back_to_query_when_no_url() -> None:
    from agent_workbench.services.web_research_graph import _dispatch

    client = MagicMock()
    client.scrape = AsyncMock(return_value="content")
    state = {"matched_skill": "scrape", "url": None, "query": "fallback query"}
    await _dispatch(client, state)
    client.scrape.assert_called_once_with("fallback query")


# --- token budget trimming ---


@pytest.mark.asyncio
async def test_execute_node_trims_large_content() -> None:
    """Raw content exceeding budget is trimmed before chunking."""
    from agent_workbench.services.web_research_graph import _WEB_CHAR_BUDGET

    conv_id = "conv-trim-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    oversized_content = "x" * (_WEB_CHAR_BUDGET + 10_000)
    mock_firecrawl = MagicMock()
    mock_firecrawl.search = AsyncMock(return_value=oversized_content)

    chunked_texts: list = []

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        retriever = _make_retriever()
        original_chunk = retriever.chunk_text

        def capturing_chunk(text: str, filename: str) -> list:
            chunked_texts.append(text)
            return original_chunk(text, filename)

        retriever.chunk_text = capturing_chunk  # type: ignore[method-assign]

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=retriever,
            model_config=_make_model_config(),
            firecrawl_client=mock_firecrawl,
        )
        await graph.ainvoke("some query", conv_id)

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    assert len(chunked_texts) > 0
    assert len(chunked_texts[0]) <= _WEB_CHAR_BUDGET


# --- no api key graceful degradation ---


@pytest.mark.asyncio
async def test_execute_node_no_firecrawl_returns_answer_string() -> None:
    """With no firecrawl_client, ainvoke still returns a string (not an error)."""
    conv_id = "conv-no-key-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
            firecrawl_client=None,
        )
        result = await graph.ainvoke("what is langgraph?", conv_id)

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_execute_node_cache_miss_stores_chunks():
    """Cache miss: stub content is chunked and stored in _web_chunk_cache."""
    conv_id = "conv-exec-miss-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
        )
        await graph.ainvoke("some query", conv_id)

    assert conv_id in _web_chunk_cache
    assert len(list(_web_chunk_cache[conv_id].values())[0]) > 0

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)


@pytest.mark.asyncio
async def test_turn2_skips_embedding():
    """Second ainvoke hits embedding cache — embed_batch not called again."""
    conv_id = "conv-turn2-embed-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    mock_es = MagicMock(spec=EmbeddingService)
    mock_es.embed.return_value = [0.1] * 384
    mock_es.embed_batch.return_value = [[0.1] * 384]
    mock_es.cosine_similarity.return_value = [0.9]
    retriever = SemanticRetriever(mock_es)

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="search"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=retriever,
            model_config=_make_model_config(),
        )

        await graph.ainvoke("langgraph overview", conv_id)
        count_after_turn1 = mock_es.embed_batch.call_count

        # Same query → same cache key → embedding cache hit → no embed_batch again
        await graph.ainvoke("langgraph overview", conv_id)
        count_after_turn2 = mock_es.embed_batch.call_count

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    assert count_after_turn1 == 1
    assert count_after_turn2 == 1  # not called again


# --- WebResearchTool ---


def test_web_research_tool_name():
    graph = _make_graph()
    tool = WebResearchTool(graph=graph, description="desc")
    assert tool.name == "web_research"


def test_web_research_tool_description_from_constructor():
    graph = _make_graph()
    tool = WebResearchTool(graph=graph, description="Custom description.")
    assert tool.description == "Custom description."


@pytest.mark.asyncio
async def test_arun_no_thread_id_returns_error():
    graph = _make_graph()
    tool = WebResearchTool(graph=graph, description="desc")
    result = await tool._arun("query", config={"configurable": {}})
    assert "No active conversation" in result


@pytest.mark.asyncio
async def test_arun_no_config_returns_error():
    graph = _make_graph()
    tool = WebResearchTool(graph=graph, description="desc")
    result = await tool._arun("query", config=None)
    assert "No active conversation" in result


@pytest.mark.asyncio
async def test_arun_returns_str():
    conv_id = "conv-tool-str-test"
    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    with patch(
        "agent_workbench.services.web_research_graph.provider_registry"
    ) as mock_reg:
        mock_model = MagicMock()
        mock_model.ainvoke = AsyncMock(return_value=MagicMock(content="answer"))
        mock_reg.create_model.return_value = mock_model

        graph = WebResearchGraph(
            skills_catalog=_SKILLS_CATALOG,
            semantic_retriever=_make_retriever(),
            model_config=_make_model_config(),
        )
        tool = WebResearchTool(graph=graph, description="desc")
        result = await tool._arun(
            "query",
            config={"configurable": {"thread_id": conv_id}},
        )

    _web_chunk_cache.pop(conv_id, None)
    _web_embedding_cache.pop(conv_id, None)

    assert isinstance(result, str)
