"""
Unit tests for provider format_query() methods.
Pure logic tests — no external API calls.
"""
import pytest

try:
    from app.services.providers.pexels import PexelsProvider
    from app.services.providers.pixabay import PixabayProvider
    from app.services.providers.openverse import OpenverseProvider
    from app.services.providers.wikimedia import WikimediaProvider
    from app.services.providers.deviantart import DeviantArtProvider
    NEW_PROVIDERS_AVAILABLE = True
except ImportError:
    NEW_PROVIDERS_AVAILABLE = False

RAW_QUERY = "holographic AI construct cyberpunk neon sci-fi"


@pytest.mark.skipif(not NEW_PROVIDERS_AVAILABLE, reason="New provider files not yet implemented (Step 9)")
def test_pixabay_uses_plus_separator():
    p = PixabayProvider()
    formatted = p.format_query(RAW_QUERY)
    assert "+" in formatted, f"Pixabay query should use + separator: '{formatted}'"
    assert " AND " not in formatted


@pytest.mark.skipif(not NEW_PROVIDERS_AVAILABLE, reason="New provider files not yet implemented (Step 9)")
def test_openverse_produces_formal_description():
    p = OpenverseProvider()
    formatted = p.format_query(RAW_QUERY)
    assert len(formatted) > 0
    assert "+" not in formatted


@pytest.mark.skipif(not NEW_PROVIDERS_AVAILABLE, reason="New provider files not yet implemented (Step 9)")
def test_deviantart_wraps_with_site_filter():
    p = DeviantArtProvider()
    formatted = p.format_query(RAW_QUERY)
    assert "deviantart" in formatted.lower(), \
        f"DeviantArt provider should include site filter: '{formatted}'"


@pytest.mark.skipif(not NEW_PROVIDERS_AVAILABLE, reason="New provider files not yet implemented (Step 9)")
def test_all_providers_return_nonempty_query():
    providers = [PexelsProvider(), PixabayProvider(), OpenverseProvider(),
                 WikimediaProvider(), DeviantArtProvider()]
    for p in providers:
        result = p.format_query(RAW_QUERY)
        assert result and len(result.strip()) > 0, \
            f"{p.name}.format_query() returned empty string"
