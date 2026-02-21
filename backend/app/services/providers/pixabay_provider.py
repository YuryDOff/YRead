"""Pixabay image search provider. Free, unlimited requests. Best for sci-fi, fantasy, concept art."""
import logging
import os

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")


class PixabayProvider(BaseImageProvider):
    """Image search via Pixabay API. Free, unlimited. Tags joined with '+' work best."""

    name = "pixabay"

    def __init__(self):
        self.api_key = PIXABAY_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    def format_query(self, raw_query: str) -> str:
        """Pixabay uses tags joined by '+'. Convert spaces/phrases to tag format."""
        words = raw_query.strip().split()
        # Keep phrases as individual tokens joined by +
        return "+".join(w for w in words if w)

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        if not self.api_key:
            logger.warning("PIXABAY_API_KEY not set; returning empty results")
            return []

        params = {
            "key": self.api_key,
            "q": query,
            "image_type": "all",
            "per_page": min(count, 200),
            "safesearch": "true",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get("https://pixabay.com/api/", params=params)
                if resp.status_code != 200:
                    logger.error("Pixabay API returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("Pixabay search failed: %s", e)
            return []

        results: list[dict] = []
        for hit in data.get("hits", [])[:count]:
            results.append({
                "url": hit.get("largeImageURL") or hit.get("webformatURL") or "",
                "thumbnail": hit.get("previewURL") or hit.get("webformatURL") or "",
                "width": hit.get("imageWidth", 0),
                "height": hit.get("imageHeight", 0),
                "credit": hit.get("user", "Pixabay"),
                "license": "Pixabay License (free for commercial use)",
                "provider": self.name,
            })
        return [r for r in results if r["url"]]
