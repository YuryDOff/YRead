"""Abstract base class for image search providers."""
from abc import ABC, abstractmethod


class BaseImageProvider(ABC):
    name: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready to use."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        content_type: str,
        count: int = 15,
    ) -> list[dict]:
        """
        Search for images.

        Args:
            query: Search query string (may be pre-formatted by format_query)
            content_type: "character" or "location"
            count: Max results to return

        Returns:
            List of normalised dicts: {url, thumbnail, width, height, credit, license, provider}
        """
        ...

    def format_query(self, raw_query: str) -> str:
        """Override per provider to adapt query format. Default: return as-is."""
        return raw_query
