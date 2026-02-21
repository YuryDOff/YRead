"""
Unit tests for _build_queries_diversified() in search_service.py.
Pure logic tests — no external API calls, no DB.
"""
import pytest
from app.services.search_service import _build_queries_diversified

BOOK_INFO_SCIFI = {
    "title": "I, Robot",
    "author": "Isaac Asimov",
    "is_well_known": True,
    "style_category": "sci-fi",
    "known_adaptations": ["I Robot 2004 film"],
}
BOOK_INFO_FICTION = {
    "title": "A Novel",
    "author": "Author",
    "is_well_known": False,
    "style_category": "fiction",
    "known_adaptations": [],
}

ONTOLOGY_AI = {
    "entity_class": "android",
    "anti_human_override": True,
    "search_archetype": "boxy robot with glowing red eyes",
    "visual_markers": ["glowing red eyes", "parallelepiped shape", "metallic surface"],
}
ONTOLOGY_HUMAN = {
    "entity_class": "human",
    "anti_human_override": False,
    "search_archetype": None,
    "visual_markers": ["sharp eyes", "grey hair"],
}

TOKENS_AI = {
    "core_tokens": ["robot", "metal", "industrial"],
    "style_tokens": ["dramatic lighting"],
    "archetype_tokens": ["mechanical construct", "android"],
    "anti_tokens": ["man portrait", "person"],
}
TOKENS_HUMAN = {
    "core_tokens": ["elderly woman", "sharp eyes"],
    "style_tokens": ["cinematic"],
    "archetype_tokens": [],
    "anti_tokens": [],
}


def test_returns_multiple_queries():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert len(queries) >= 4, f"Expected ≥4 queries, got {len(queries)}: {queries}"


def test_no_human_terms_for_anti_human_entity():
    forbidden = {"man portrait", "woman portrait", "person portrait", "human portrait"}
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    for q in queries:
        for term in forbidden:
            assert term not in q.lower(), f"Human term '{term}' found in query for anti_human entity: '{q}'"


def test_all_queries_distinct():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert len(queries) == len(set(queries)), f"Duplicate queries found: {queries}"


def test_style_category_in_at_least_one_query():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert any("sci-fi" in q.lower() for q in queries), f"style_category not in any query: {queries}"


def test_well_known_book_includes_adaptation_query():
    queries = _build_queries_diversified("character", "robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert any("2004" in q or "film" in q for q in queries), \
        f"No adaptation query found for well-known book: {queries}"


def test_no_adaptation_query_for_unknown_book():
    queries = _build_queries_diversified("character", "detective", BOOK_INFO_FICTION, TOKENS_HUMAN, ONTOLOGY_HUMAN)
    assert not any("film" in q or "2004" in q for q in queries)


def test_human_character_returns_portrait_suffix():
    queries = _build_queries_diversified("character", "woman roboticist", BOOK_INFO_FICTION, TOKENS_HUMAN, ONTOLOGY_HUMAN)
    assert any("portrait" in q.lower() for q in queries), \
        f"Human character queries should include portrait: {queries}"


def test_location_query_contains_no_portrait():
    queries = _build_queries_diversified("location", "sprawling industrial complex", BOOK_INFO_SCIFI,
                                         TOKENS_AI, ONTOLOGY_AI)
    assert not any("portrait" in q.lower() for q in queries)
