"""Abstract base class for image search providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Normalised result from supplementary search (e.g. Serper)."""
    url: str
    title: str = ""
    source_url: str = ""
    provider: str = ""
    watermarked: bool = False


class BaseSearchProvider(ABC):
    """Abstract base for supplementary image search (Serper, etc.)."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the provider is configured and ready to use."""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        num: int = 10,
        **kwargs,
    ) -> list[SearchResult]:
        """Search for images; returns list of SearchResult."""
        ...


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
            List of normalised dicts: {url, thumbnail, width, height, credit, license, provider}.
            Optional for relevance scoring: search_metadata (dict with title, description, alt, tags)
            or top-level title, description, alt, tags (all optional).
        """
        ...

    def format_query(self, raw_query: str) -> str:
        """Override per provider to adapt query format. Default: return as-is."""
        return raw_query
