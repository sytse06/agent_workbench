"""Unit tests for FirecrawlClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_workbench.services.firecrawl_client import FirecrawlClient


def _make_response(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def _make_client() -> FirecrawlClient:
    with patch("agent_workbench.services.firecrawl_client.httpx.AsyncClient"):
        return FirecrawlClient(api_key="test-key")


# --- scrape ---


@pytest.mark.asyncio
async def test_scrape_posts_to_correct_endpoint() -> None:
    client = _make_client()
    mock_resp = _make_response({"data": {"markdown": "# Hello"}})
    client._client.post = AsyncMock(return_value=mock_resp)

    result = await client.scrape("https://example.com")

    client._client.post.assert_called_once_with(
        "/scrape", json={"url": "https://example.com", "formats": ["markdown"]}
    )
    assert result == "# Hello"


@pytest.mark.asyncio
async def test_scrape_returns_empty_string_on_missing_markdown() -> None:
    client = _make_client()
    client._client.post = AsyncMock(return_value=_make_response({"data": {}}))
    result = await client.scrape("https://example.com")
    assert result == ""


# --- search ---


@pytest.mark.asyncio
async def test_search_posts_query_and_limit() -> None:
    client = _make_client()
    mock_resp = _make_response(
        {
            "data": [
                {
                    "url": "https://a.com",
                    "title": "A",
                    "markdown": "content A",
                }
            ]
        }
    )
    client._client.post = AsyncMock(return_value=mock_resp)

    result = await client.search("langgraph tutorial", limit=3)

    client._client.post.assert_called_once_with(
        "/search", json={"query": "langgraph tutorial", "limit": 3}
    )
    assert "content A" in result
    assert "https://a.com" in result


@pytest.mark.asyncio
async def test_search_concatenates_multiple_results() -> None:
    client = _make_client()
    client._client.post = AsyncMock(
        return_value=_make_response(
            {
                "data": [
                    {"url": "https://a.com", "title": "A", "markdown": "body A"},
                    {"url": "https://b.com", "title": "B", "markdown": "body B"},
                ]
            }
        )
    )
    result = await client.search("query")
    assert "body A" in result
    assert "body B" in result
    assert "---" in result


@pytest.mark.asyncio
async def test_search_skips_items_without_markdown() -> None:
    client = _make_client()
    client._client.post = AsyncMock(
        return_value=_make_response(
            {"data": [{"url": "https://a.com", "title": "A", "markdown": ""}]}
        )
    )
    result = await client.search("query")
    assert result == ""


# --- crawl ---


@pytest.mark.asyncio
async def test_crawl_starts_job_and_polls_until_complete() -> None:
    client = _make_client()
    client._client.post = AsyncMock(
        return_value=_make_response({"id": "job-123", "success": True})
    )
    client._client.get = AsyncMock(
        return_value=_make_response(
            {
                "status": "completed",
                "data": [{"markdown": "page 1"}, {"markdown": "page 2"}],
            }
        )
    )

    sleep_patch = patch(
        "agent_workbench.services.firecrawl_client.asyncio.sleep", new=AsyncMock()
    )
    with sleep_patch:
        result = await client.crawl("https://docs.example.com")

    client._client.post.assert_called_once_with(
        "/crawl",
        json={"url": "https://docs.example.com", "maxDepth": 2, "limit": 10},
    )
    client._client.get.assert_called_once_with("/crawl/job-123")
    assert "page 1" in result
    assert "page 2" in result


@pytest.mark.asyncio
async def test_crawl_returns_empty_on_failed_status() -> None:
    client = _make_client()
    client._client.post = AsyncMock(return_value=_make_response({"id": "job-456"}))
    client._client.get = AsyncMock(return_value=_make_response({"status": "failed"}))
    sleep_patch = patch(
        "agent_workbench.services.firecrawl_client.asyncio.sleep", new=AsyncMock()
    )
    with sleep_patch:
        result = await client.crawl("https://example.com")
    assert result == ""


@pytest.mark.asyncio
async def test_crawl_returns_empty_when_no_job_id() -> None:
    client = _make_client()
    client._client.post = AsyncMock(return_value=_make_response({}))
    result = await client.crawl("https://example.com")
    assert result == ""


# --- extract ---


@pytest.mark.asyncio
async def test_extract_posts_url_and_prompt() -> None:
    client = _make_client()
    client._client.post = AsyncMock(
        return_value=_make_response({"data": {"price": "$9.99", "name": "Widget"}})
    )

    result = await client.extract("https://shop.com/item", "Extract price and name")

    client._client.post.assert_called_once_with(
        "/extract",
        json={"urls": ["https://shop.com/item"], "prompt": "Extract price and name"},
    )
    assert "price" in result
    assert "$9.99" in result


@pytest.mark.asyncio
async def test_extract_handles_non_dict_response() -> None:
    client = _make_client()
    client._client.post = AsyncMock(
        return_value=_make_response({"data": "raw string result"})
    )
    result = await client.extract("https://example.com", "prompt")
    assert result == "raw string result"


# --- aclose ---


@pytest.mark.asyncio
async def test_aclose_calls_httpx_client_aclose() -> None:
    client = _make_client()
    client._client.aclose = AsyncMock()
    await client.aclose()
    client._client.aclose.assert_called_once()
