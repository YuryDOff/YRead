"""Unsplash image search provider."""
import logging
import os

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")


class UnsplashProvider(BaseImageProvider):
    """Image search via Unsplash API. Free, 50 req/hour. Best for realistic portraits and locations."""

    name = "unsplash"

    def __init__(self):
        self.access_key = UNSPLASH_ACCESS_KEY

    def is_available(self) -> bool:
        return bool(self.access_key)

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        if not self.access_key:
            logger.warning("UNSPLASH_ACCESS_KEY not set; returning empty results")
            return []

        orientation = "portrait" if content_type == "character" else "landscape"
        params = {
            "query": query,
            "per_page": count,
            "orientation": orientation,
        }
        headers = {"Authorization": f"Client-ID {self.access_key}"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    "https://api.unsplash.com/search/photos",
                    params=params,
                    headers=headers,
                )
                if resp.status_code != 200:
                    logger.error("Unsplash API returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("Unsplash search failed: %s", e)
            return []

        results: list[dict] = []
        for img in data.get("results", [])[:count]:
            urls = img.get("urls", {})
            user = img.get("user", {})
            results.append({
                "url": urls.get("regular") or urls.get("full") or "",
                "thumbnail": urls.get("thumb") or urls.get("small") or "",
                "width": img.get("width", 0),
                "height": img.get("height", 0),
                "credit": user.get("name", "Unsplash") or "Unsplash",
                "license": "Unsplash License (free for commercial use)",
                "provider": self.name,
            })
        return [r for r in results if r["url"]]
