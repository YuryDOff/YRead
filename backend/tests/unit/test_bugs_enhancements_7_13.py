"""
Unit tests for bugs/enhancements 7–14: settings providers, analyze schema, book fields.
"""
import pytest

from app.schemas import BookAnalyzeRequest, SearchReferencesRequest


# ---------------------------------------------------------------------------
# BookAnalyzeRequest: well_known_book_title, similar_book_title (items 10, 11)
# ---------------------------------------------------------------------------

def test_book_analyze_request_accepts_well_known_book_title_and_similar_book_title():
    req = BookAnalyzeRequest(
        style_category="fiction",
        well_known_book_title="A Study in Scarlet",
        similar_book_title="The Hound of the Baskervilles",
    )
    assert req.well_known_book_title == "A Study in Scarlet"
    assert req.similar_book_title == "The Hound of the Baskervilles"


def test_book_analyze_request_optional_well_known_and_similar_default_none():
    req = BookAnalyzeRequest(style_category="sci_fi")
    assert req.well_known_book_title is None
    assert req.similar_book_title is None


# ---------------------------------------------------------------------------
# SearchReferencesRequest: enabled_providers (item 14)
# ---------------------------------------------------------------------------

def test_search_references_request_accepts_enabled_providers():
    req = SearchReferencesRequest(
        main_only=True,
        enabled_providers=["unsplash", "serpapi"],
    )
    assert req.enabled_providers == ["unsplash", "serpapi"]


def test_search_references_request_enabled_providers_optional():
    req = SearchReferencesRequest(main_only=True)
    assert req.enabled_providers is None
