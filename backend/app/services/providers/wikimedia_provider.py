"""Wikimedia Commons image search provider. Free, no key. Historical figures and real locations."""
import logging

import httpx

from app.services.providers.base import BaseImageProvider

logger = logging.getLogger(__name__)

WIKIMEDIA_API_BASE = "https://commons.wikimedia.org/w/api.php"


class WikimediaProvider(BaseImageProvider):
    """Image search via Wikimedia Commons API. Free, no key. Best for historical/real-world content."""

    name = "wikimedia"

    def is_available(self) -> bool:
        return True  # No API key required

    def format_query(self, raw_query: str) -> str:
        """Wikimedia works best with proper names and place names. Return as-is."""
        return raw_query.strip()

    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        params = {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",
            "gsrlimit": min(count, 50),
            "prop": "imageinfo",
            "iiprop": "url|size|extmetadata",
            "iiurlwidth": 800,
            "format": "json",
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(WIKIMEDIA_API_BASE, params=params)
                if resp.status_code != 200:
                    logger.error("Wikimedia API returned %s for query: %s", resp.status_code, query)
                    return []
                data = resp.json()
        except Exception as e:
            logger.exception("Wikimedia search failed: %s", e)
            return []

        pages = data.get("query", {}).get("pages", {})
        results: list[dict] = []
        for page in pages.values():
            imageinfo = page.get("imageinfo", [{}])[0]
            url = imageinfo.get("thumburl") or imageinfo.get("url") or ""
            if not url:
                continue

            extmeta = imageinfo.get("extmetadata", {})
            artist = extmeta.get("Artist", {}).get("value", "Wikimedia Commons")
            # Strip HTML tags from artist field
            import re
            artist = re.sub(r"<[^>]+>", "", artist).strip() or "Wikimedia Commons"

            results.append({
                "url": url,
                "thumbnail": imageinfo.get("thumburl") or url,
                "width": imageinfo.get("thumbwidth") or imageinfo.get("width") or 0,
                "height": imageinfo.get("thumbheight") or imageinfo.get("height") or 0,
                "credit": artist,
                "license": extmeta.get("LicenseShortName", {}).get("value", "Public Domain / CC"),
                "provider": self.name,
            })
            if len(results) >= count:
                break
        return results
