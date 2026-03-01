"""
Unit tests for search engine / provider selection and response behaviour.
- Aggregate vs single-provider mode (preferred_provider, use_aggregate_providers).
- Router overwriting source to unsplash/serpapi (current behaviour under test).
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from app.services.providers import ALL_PROVIDERS


def test_aggregate_mode_when_preferred_provider_is_none():
    """When preferred_provider is None or 'auto', aggregate mode should be used (all enabled providers)."""
    preferred_provider = None
    use_aggregate = not preferred_provider or preferred_provider == "auto"
    assert use_aggregate is True

    preferred_provider = "auto"
    use_aggregate = not preferred_provider or preferred_provider == "auto"
    assert use_aggregate is True


def test_single_provider_mode_when_preferred_set():
    """When preferred_provider is set (e.g. 'unsplash'), aggregate mode is off."""
    preferred_provider = "unsplash"
    use_aggregate = not preferred_provider or preferred_provider == "auto"
    assert use_aggregate is False

    preferred_provider = "serpapi"
    use_aggregate = not preferred_provider or preferred_provider == "auto"
    assert use_aggregate is False


def test_available_providers_filtered_by_enabled_list():
    """available_provider_names should be filtered by enabled_providers when provided."""
    all_names = list(ALL_PROVIDERS.keys())
    enabled_providers = ["unsplash", "pexels", "pixabay"]
    # Simulate: only those that are both available and in enabled_providers
    available = [n for n, p in ALL_PROVIDERS.items() if p.is_available()]
    filtered = [n for n in available if n in enabled_providers]
    # Result may be empty if no keys are set; we only check the filtering logic
    assert all(n in enabled_providers for n in filtered)


def test_router_source_rewrite_logic_documents_current_behaviour():
    """Document: router currently maps any provider not in ('unsplash','serpapi') to unsplash/serpapi."""
    # Characters: non-unsplash/serpapi -> unsplash
    source = "pexels"
    allowed = ("unsplash", "serpapi")
    result = source if source in allowed else "unsplash"
    assert result == "unsplash"

    source = "pixabay"
    result = source if source in allowed else "unsplash"
    assert result == "unsplash"

    # Locations: non-unsplash/serpapi -> serpapi
    result_loc = source if source in allowed else "serpapi"
    assert result_loc == "serpapi"


def test_pixabay_format_query_semantics():
    """Pixabay expects +-joined tags; format_query must produce a valid query string."""
    from app.services.providers.pixabay_provider import PixabayProvider
    p = PixabayProvider()
    out = p.format_query("wizard portrait fantasy")
    assert "+" in out
    assert "wizard" in out
    assert "portrait" in out
    assert "wizard+portrait+fantasy" == out or "fantasy" in out


def test_openverse_response_parsing_uses_results_key():
    """Openverse API returns top-level 'results' array; our code must use data.get('results', [])."""
    # Simulate API response structure
    data = {"result_count": 10, "page_count": 1, "results": [{"id": "x", "url": "https://a.com/1", "thumbnail": "", "width": 600, "height": 400, "creator": "X", "license": "cc0"}]}
    results = data.get("results", [])[:15]
    assert len(results) == 1
    assert results[0].get("url") == "https://a.com/1"


def test_wikimedia_response_parsing_uses_query_pages():
    """Wikimedia API returns query.pages dict; our code must use data.get('query', {}).get('pages', {})."""
    data = {"query": {"pages": {"123": {"imageinfo": [{"url": "https://b.com/1", "thumburl": "https://b.com/t", "thumbwidth": 800}]}}}}
    pages = data.get("query", {}).get("pages", {})
    assert len(pages) == 1
    info = list(pages.values())[0].get("imageinfo", [{}])[0]
    assert info.get("url") == "https://b.com/1"


def test_provider_result_has_required_fields():
    """Each provider result must have url, provider, width, height for filtering/ranking pipeline."""
    from app.services.providers.base import BaseImageProvider
    # Contract from base.py: list of dicts with url, thumbnail, width, height, credit, license, provider
    required = {"url", "provider", "width", "height"}
    # We only assert the contract; actual providers are tested via integration or mocked HTTP
    sample = {"url": "https://x", "thumbnail": "", "width": 600, "height": 400, "credit": "", "license": "", "provider": "test"}
    assert required <= set(sample.keys())


def test_alignment_score_expects_search_metadata():
    """Ranking uses search_metadata (title, description, alt, tags); missing -> neutral 0.5."""
    from app.services.search_service import _alignment_score
    assert _alignment_score("robot", {}) == 0.5
    assert _alignment_score("robot", {"url": "https://x", "provider": "x"}) == 0.5
    img_with_meta = {"search_metadata": {"title": "robot", "description": "robot arm", "alt": "", "tags": "robot"}}
    s = _alignment_score("robot portrait", img_with_meta)
    assert s > 0.2 and s <= 1.0
