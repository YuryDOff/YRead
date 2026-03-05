"""
Unit tests for Phase 9b: Serper search provider.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.providers.serper_provider import (
    SerperProvider,
    _is_blacklisted,
    _is_watermarked,
)


def test_blacklisted_domains_rejected():
    assert _is_blacklisted("https://lookaside.instagram.com/image.jpg") is True
    assert _is_blacklisted("https://craiyon.com/output.png") is True
    assert _is_blacklisted("https://getimg.ai/gen/abc.png") is True
    assert _is_blacklisted("https://unsplash.com/photo.jpg") is False


def test_watermark_domains_flagged():
    assert _is_watermarked("https://shutterstock.com/photo-123.jpg") is True
    assert _is_watermarked("https://gettyimages.com/image.jpg") is True
    assert _is_watermarked("https://flickr.com/photo.jpg") is False


def test_is_available_false_without_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    assert SerperProvider().is_available() is False


def test_is_available_true_with_key(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    assert SerperProvider().is_available() is True


def test_returns_empty_without_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    results = asyncio.run(SerperProvider().search("dark fantasy art"))
    assert results == []


def test_blacklisted_urls_filtered_from_results(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "images": [
            {"imageUrl": "https://craiyon.com/bad.png", "title": "Bad", "link": ""},
            {"imageUrl": "https://unsplash.com/good.jpg", "title": "Good", "link": ""},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    async def mock_post(*args, **kwargs):
        return mock_response

    with patch("app.services.providers.serper_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        results = asyncio.run(SerperProvider().search("test query"))

    assert len(results) == 1
    assert results[0].url == "https://unsplash.com/good.jpg"


def test_watermarked_flag_set_on_stock_photo_domains(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "images": [
            {"imageUrl": "https://shutterstock.com/stock.jpg", "title": "Stock", "link": ""},
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.services.providers.serper_provider.httpx.AsyncClient") as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)

        results = asyncio.run(SerperProvider().search("test query"))

    assert len(results) == 1
    assert results[0].watermarked is True


def test_get_supplementary_search_providers_returns_serper_for_artefact(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    from app.services.engine_selector import get_supplementary_search_providers
    providers = get_supplementary_search_providers("artefact")
    assert len(providers) == 1
    assert providers[0].__class__.__name__ == "SerperProvider"


def test_get_supplementary_search_providers_returns_serper_for_location(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    from app.services.engine_selector import get_supplementary_search_providers
    providers = get_supplementary_search_providers("location")
    assert len(providers) == 1


def test_get_supplementary_search_providers_returns_empty_for_character(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    from app.services.engine_selector import get_supplementary_search_providers
    providers = get_supplementary_search_providers("character")
    assert providers == []
