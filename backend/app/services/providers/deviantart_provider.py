"""DeviantArt image search provider (via SerpAPI site:deviantart.com). Concept art and fantasy."""
import logging
import os

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")
SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")


class DeviantArtProvider(BaseImageProvider):
    """
    DeviantArt via SerpAPI Google Images with site:deviantart.com filter.
    No official DeviantArt API — uses Google Images to index fan art and concept art.
    Requires SERPAPI_KEY.
    """

    name = "deviantart"

    def __init__(self):
        self.api_key = SERPAPI_KEY or SEARCH_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    def format_query(self, raw_query: str) -> str:
        """Append site:deviantart.com filter for SerpAPI queries."""
        base = raw_query.strip()
        if "deviantart" not in base.lower():
            return f"{base} site:deviantart.com"
        return base

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        if not self.api_key:
            logger.warning("SERPAPI_KEY not set; DeviantArt provider unavailable")
            return []

        params = {
            "engine": "google_images",
            "q": query,
            "api_key": self.api_key,
            "safe": "active",
            "num": count,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get("https://serpapi.com/search.json", params=params)
                if resp.status_code != 200:
                    logger.error("DeviantArt/SerpAPI returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("DeviantArt/SerpAPI search failed: %s", e)
            return []

        results: list[dict] = []
        for img in data.get("images_results", [])[:count]:
            original = img.get("original", "")
            if not original:
                continue
            results.append({
                "url": original,
                "thumbnail": img.get("thumbnail", ""),
                "width": img.get("original_width", 0),
                "height": img.get("original_height", 0),
                "credit": img.get("source", "DeviantArt"),
                "license": "Verify license before use (fan art)",
                "provider": self.name,
            })
        return results
