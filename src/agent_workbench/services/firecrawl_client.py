"""FirecrawlClient — async httpx wrapper for the Firecrawl REST API.

Supports all four skills defined in SKILLS.md:
  scrape  → POST /scrape
  search  → POST /search
  crawl   → POST /crawl (async job, polled via GET /crawl/{id})
  extract → POST /extract

All methods return plain markdown/text for the retrieval pipeline.
"""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

_CRAWL_POLL_INTERVAL = 2.0  # seconds between crawl status polls
_CRAWL_TIMEOUT = 120.0  # max seconds to wait for a crawl job


class FirecrawlClient:
    BASE_URL = "https://api.firecrawl.dev/v1"

    def __init__(self, api_key: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    async def scrape(self, url: str) -> str:
        """Scrape a single URL and return its markdown content."""
        logger.info("FirecrawlClient.scrape: %s", url)
        resp = await self._client.post(
            "/scrape", json={"url": url, "formats": ["markdown"]}
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data.get("data", {}).get("markdown", "") or "")

    async def search(self, query: str, limit: int = 5) -> str:
        """Search the web and return concatenated markdown from top results."""
        logger.info("FirecrawlClient.search: %r limit=%d", query, limit)
        resp = await self._client.post("/search", json={"query": query, "limit": limit})
        resp.raise_for_status()
        data = resp.json()
        results = data.get("data", []) or []
        parts = []
        for item in results:
            url = item.get("url", "")
            title = item.get("title", "")
            md = item.get("markdown", "") or item.get("content", "") or ""
            if md:
                parts.append(f"## [{title}]({url})\n\n{md}")
        return "\n\n---\n\n".join(parts)

    async def crawl(self, url: str, max_depth: int = 2, limit: int = 10) -> str:
        """Crawl a site and return concatenated markdown from all pages.

        Firecrawl crawl is async — starts a job, polls until complete.
        """
        logger.info(
            "FirecrawlClient.crawl: %s depth=%d limit=%d", url, max_depth, limit
        )
        resp = await self._client.post(
            "/crawl",
            json={"url": url, "maxDepth": max_depth, "limit": limit},
        )
        resp.raise_for_status()
        job_id = resp.json().get("id", "")
        if not job_id:
            logger.warning("FirecrawlClient.crawl: no job id returned")
            return ""

        elapsed = 0.0
        while elapsed < _CRAWL_TIMEOUT:
            await asyncio.sleep(_CRAWL_POLL_INTERVAL)
            elapsed += _CRAWL_POLL_INTERVAL
            status_resp = await self._client.get(f"/crawl/{job_id}")
            status_resp.raise_for_status()
            status_data = status_resp.json()
            status = status_data.get("status", "")
            if status == "completed":
                pages = status_data.get("data", []) or []
                parts = [p.get("markdown", "") for p in pages if p.get("markdown")]
                logger.info(
                    "FirecrawlClient.crawl job %s: completed, %d pages",
                    job_id,
                    len(parts),
                )
                return "\n\n---\n\n".join(parts)
            if status in ("failed", "cancelled"):
                logger.warning("FirecrawlClient.crawl job %s: %s", job_id, status)
                return ""
            logger.debug(
                "FirecrawlClient.crawl job %s: %s (%.0fs)", job_id, status, elapsed
            )

        logger.warning(
            "FirecrawlClient.crawl job %s timed out after %.0fs", job_id, _CRAWL_TIMEOUT
        )
        return ""

    async def extract(self, url: str, prompt: str) -> str:
        """Extract structured data from a URL using a natural-language prompt."""
        logger.info("FirecrawlClient.extract: %s prompt=%r", url, prompt[:80])
        resp = await self._client.post(
            "/extract", json={"urls": [url], "prompt": prompt}
        )
        resp.raise_for_status()
        data = resp.json()
        extracted = data.get("data", {})
        if isinstance(extracted, dict):
            return "\n".join(f"**{k}**: {v}" for k, v in extracted.items())
        return str(extracted)

    async def aclose(self) -> None:
        await self._client.aclose()
