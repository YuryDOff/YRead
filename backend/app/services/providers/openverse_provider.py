"""Openverse image search provider. Free, no key required. Open-licensed content."""
import logging

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

OPENVERSE_API_BASE = "https://api.openverse.org/v1"


class OpenverseProvider(BaseImageProvider):
    """Image search via Openverse API. Free, no key required. Primarily open-licensed content."""

    name = "openverse"

    def is_available(self) -> bool:
        return True  # No API key required

    def format_query(self, raw_query: str) -> str:
        """Openverse handles formal descriptions well. Return clean phrase, no special chars."""
        # Strip special characters that may confuse the API
        cleaned = raw_query.replace("+", " ").strip()
        return cleaned

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        params = {
            "q": query,
            "page_size": min(count, 500),
            "license_type": "all",
            "mature": "false",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(f"{OPENVERSE_API_BASE}/images/", params=params)
                if resp.status_code != 200:
                    logger.error("Openverse API returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("Openverse search failed: %s", e)
            return []

        results: list[dict] = []
        for item in data.get("results", [])[:count]:
            results.append({
                "url": item.get("url") or "",
                "thumbnail": item.get("thumbnail") or item.get("url") or "",
                "width": item.get("width") or 0,
                "height": item.get("height") or 0,
                "credit": item.get("creator") or item.get("source") or "Openverse",
                "license": item.get("license_url") or item.get("license") or "Open license",
                "provider": self.name,
            })
        return [r for r in results if r["url"]]
