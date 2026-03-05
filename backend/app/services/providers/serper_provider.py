"""
serper_provider.py
------------------
Google Search via Serper.dev API. Supplementary provider for artefact
and location reference image searches.

NOT used for book cover I2T searches (those target Goodreads/publisher
domains specifically — Serper's generic results are too noisy for style ref).

Domain policy:
  Hard blacklist (filtered entirely):
    lookaside.instagram.com, lookaside.fbsbx.com, craiyon.com,
    getimg.ai, ideogram.ai
  Soft flag (included with watermarked=True):
    shutterstock.com, dreamstime.com, gettyimages.com, istockphoto.com
"""
from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

from .base import BaseSearchProvider, SearchResult

logger = logging.getLogger(__name__)

_HARD_BLACKLIST = {
    "lookaside.instagram.com",
    "lookaside.fbsbx.com",
    "craiyon.com",
    "getimg.ai",
    "ideogram.ai",
}

_WATERMARK_DOMAINS = {
    "shutterstock.com",
    "dreamstime.com",
    "gettyimages.com",
    "istockphoto.com",
}


def _is_blacklisted(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith(f".{d}") for d in _HARD_BLACKLIST)
    except Exception:
        return False


def _is_watermarked(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith(f".{d}") for d in _WATERMARK_DOMAINS)
    except Exception:
        return False


class SerperProvider(BaseSearchProvider):
    """
    Serper.dev Google image search provider.
    Supplementary — used for artefact + location queries.
    """

    API_URL = "https://google.serper.dev/images"

    def is_available(self) -> bool:
        return bool(os.getenv("SERPER_API_KEY"))

    async def search(
        self,
        query: str,
        num: int = 10,
        **kwargs,
    ) -> list[SearchResult]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            logger.warning("SERPER_API_KEY not set — SerperProvider returning empty results")
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.API_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num},
            )
            response.raise_for_status()
            data = response.json()

        results: list[SearchResult] = []
        for item in data.get("images", []):
            image_url = item.get("imageUrl", "")
            if not image_url:
                continue
            if _is_blacklisted(image_url):
                logger.debug("Blacklisted URL skipped: %s", image_url)
                continue

            watermarked = _is_watermarked(image_url)
            results.append(
                SearchResult(
                    url=image_url,
                    title=item.get("title", ""),
                    source_url=item.get("link", ""),
                    provider="serper",
                    watermarked=watermarked,
                )
            )

        return results
