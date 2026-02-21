"""Image search providers."""
from app.services.providers.base import BaseImageProvider
from app.services.providers.unsplash_provider import UnsplashProvider
from app.services.providers.serpapi_provider import SerpApiProvider
from app.services.providers.pexels_provider import PexelsProvider
from app.services.providers.pixabay_provider import PixabayProvider
from app.services.providers.openverse_provider import OpenverseProvider
from app.services.providers.wikimedia_provider import WikimediaProvider
from app.services.providers.deviantart_provider import DeviantArtProvider

ALL_PROVIDERS: dict[str, BaseImageProvider] = {
    "unsplash": UnsplashProvider(),
    "serpapi": SerpApiProvider(),
    "pexels": PexelsProvider(),
    "pixabay": PixabayProvider(),
    "openverse": OpenverseProvider(),
    "wikimedia": WikimediaProvider(),
    "deviantart": DeviantArtProvider(),
}

__all__ = [
    "BaseImageProvider",
    "UnsplashProvider",
    "SerpApiProvider",
    "PexelsProvider",
    "PixabayProvider",
    "OpenverseProvider",
    "WikimediaProvider",
    "DeviantArtProvider",
    "ALL_PROVIDERS",
]
