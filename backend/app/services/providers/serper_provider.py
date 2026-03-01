"""Serper.dev image search provider."""
import os
import httpx

from app.services.providers.base import BaseImageProvider


class SerperProvider(BaseImageProvider):
    name = "serper"

    def is_available(self) -> bool:
        return bool(os.getenv("SERPER_API_KEY"))

    async def search(self, query: str, content_type: str, count: int = 15) -> list[dict]:
        key = os.getenv("SERPER_API_KEY", "")
        if not key:
            return []
        headers = {"X-API-KEY": key, "Content-Type": "application/json"}
        payload = {"q": query, "num": max(1, min(20, count))}
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post("https://google.serper.dev/images", headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        out = []
        for it in data.get("images", [])[:count]:
            out.append({
                "url": it.get("imageUrl") or it.get("link") or "",
                "thumbnail": it.get("thumbnailUrl") or "",
                "width": it.get("imageWidth"),
                "height": it.get("imageHeight"),
                "credit": it.get("source") or "",
                "license": "unknown",
                "provider": self.name,
                "title": it.get("title") or "",
            })
        return [x for x in out if x.get("url")]
