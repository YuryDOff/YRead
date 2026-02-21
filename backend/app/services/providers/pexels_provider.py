"""Pexels image search provider. Free, 200 req/hour, 20K/month. Best for portraits and lifestyle."""
import logging
import os

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")


class PexelsProvider(BaseImageProvider):
    """Image search via Pexels API. Free tier: 200 req/hour, 20K/month."""

    name = "pexels"

    def __init__(self):
        self.api_key = PEXELS_API_KEY

    def is_available(self) -> bool:
        return bool(self.api_key)

    def format_query(self, raw_query: str) -> str:
        """Pexels works best with descriptive phrases (5–8 words). Return as-is."""
        return raw_query

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        if not self.api_key:
            logger.warning("PEXELS_API_KEY not set; returning empty results")
            return []

        orientation = "portrait" if content_type == "character" else "landscape"
        params = {
            "query": query,
            "per_page": min(count, 80),
            "orientation": orientation,
        }
        headers = {"Authorization": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get("https://api.pexels.com/v1/search", params=params, headers=headers)
                if resp.status_code != 200:
                    logger.error("Pexels API returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("Pexels search failed: %s", e)
            return []

        results: list[dict] = []
        for photo in data.get("photos", [])[:count]:
            src = photo.get("src", {})
            results.append({
                "url": src.get("large") or src.get("original") or "",
                "thumbnail": src.get("small") or src.get("medium") or "",
                "width": photo.get("width", 0),
                "height": photo.get("height", 0),
                "credit": photo.get("photographer", "Pexels"),
                "license": "Pexels License (free for commercial use)",
                "provider": self.name,
            })
        return [r for r in results if r["url"]]
