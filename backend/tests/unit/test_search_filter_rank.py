"""
Unit tests for alignment score and _filter_dedupe_and_rank in search_service.py.
Covers: alignment_score, dedupe by URL (keep max score), min_size filter, max 50 per entity.
"""
import pytest
from app.services.search_service import (
    _alignment_score,
    _filter_dedupe_and_rank,
    MAX_REFERENCE_IMAGES_PER_ENTITY,
)


def test_alignment_score_empty_metadata_returns_neutral():
    assert _alignment_score("robot portrait", {}) == 0.5
    assert _alignment_score("robot portrait", {"url": "https://x.y/z"}) == 0.5
    assert _alignment_score("robot", {"search_metadata": None}) == 0.5


def test_alignment_score_token_overlap():
    img = {"search_metadata": {"title": "", "description": "robot in factory", "alt": "", "tags": "robot industrial"}}
    s = _alignment_score("robot portrait", img)
    assert s > 0.2  # some overlap (e.g. "robot") yields score above no-overlap
    assert s <= 1.0


def test_alignment_score_no_overlap_low():
    img = {"search_metadata": {"title": "sunset", "description": "beach", "alt": "", "tags": "nature"}}
    s = _alignment_score("robot portrait", img)
    assert s <= 0.5


def test_filter_dedupe_and_rank_dedupes_by_url_keeps_higher_score():
    base = {"width": 600, "height": 600}
    img1 = {**base, "url": "https://a.com/1", "query_text": "robot", "search_metadata": {"title": "robot", "description": "robot", "alt": "", "tags": ""}}
    img2 = {**base, "url": "https://a.com/1", "query_text": "sunset", "search_metadata": {"title": "sunset", "description": "", "alt": "", "tags": ""}}
    # Same URL: one has query "robot" matching "robot" in metadata → higher score
    result = _filter_dedupe_and_rank([img1, img2], min_size=100, max_results=10)
    assert len(result) == 1
    assert result[0]["url"] == "https://a.com/1"
    assert result[0].get("relevance_score", 0) >= 0.2


def test_filter_dedupe_and_rank_sorts_by_score_desc():
    base = {"width": 600, "height": 600}
    low = {**base, "url": "https://a.com/low", "query_text": "x", "search_metadata": {"title": "other", "description": "", "alt": "", "tags": ""}}
    high = {**base, "url": "https://a.com/high", "query_text": "robot", "search_metadata": {"title": "robot", "description": "robot", "alt": "", "tags": "robot"}}
    result = _filter_dedupe_and_rank([low, high], min_size=100, max_results=10)
    assert len(result) == 2
    assert result[0]["relevance_score"] >= result[1]["relevance_score"]


def test_filter_dedupe_and_rank_respects_max_results():
    images = [
        {"url": f"https://a.com/{i}", "width": 600, "height": 600, "query_text": "q", "search_metadata": {"title": "", "description": "", "alt": "", "tags": ""}}
        for i in range(60)
    ]
    result = _filter_dedupe_and_rank(images, min_size=100, max_results=50)
    assert len(result) == 50


def test_filter_dedupe_and_rank_filters_min_size():
    small = {"url": "https://a.com/s", "width": 100, "height": 100, "query_text": "q", "search_metadata": {}}
    big = {"url": "https://a.com/b", "width": 600, "height": 600, "query_text": "q", "search_metadata": {}}
    result = _filter_dedupe_and_rank([small, big], min_size=512, max_results=10)
    assert len(result) == 1
    assert result[0]["url"] == "https://a.com/b"


def test_max_reference_images_constant():
    assert MAX_REFERENCE_IMAGES_PER_ENTITY == 50
