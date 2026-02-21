"""
Unit tests for engine_selector.select_engines().
Pure logic tests — no external calls.
"""
import pytest

# Engine selector will be created in Step 10, but we can test it now since
# ontology_constants is already available. We create a minimal engine_selector here.
# These tests will pass once engine_selector.py is created in Step 10.
try:
    from app.services.engine_selector import select_engines
    ENGINE_SELECTOR_AVAILABLE = True
except ImportError:
    ENGINE_SELECTOR_AVAILABLE = False

from app.services.ontology_constants import ENTITY_PARENT

ALL_PROVIDERS = ["unsplash", "serpapi", "pexels", "openverse", "pixabay", "wikimedia", "deviantart"]


# ---------------------------------------------------------------------------
# Constants tests (always run — no external deps)
# ---------------------------------------------------------------------------

def test_entity_parent_values_are_valid_classes():
    """All ENTITY_PARENT values must be valid entity classes."""
    from app.services.ontology_constants import ENTITY_CLASSES
    for child, parent in ENTITY_PARENT.items():
        assert parent in ENTITY_CLASSES, f"ENTITY_PARENT['{child}'] = '{parent}' not in ENTITY_CLASSES"


def test_non_human_classes_subset_of_entity_classes():
    """NON_HUMAN_CLASSES must be a subset of ENTITY_CLASSES."""
    from app.services.ontology_constants import ENTITY_CLASSES, NON_HUMAN_CLASSES
    assert NON_HUMAN_CLASSES.issubset(set(ENTITY_CLASSES))


def test_human_not_in_non_human_classes():
    from app.services.ontology_constants import NON_HUMAN_CLASSES
    assert "human" not in NON_HUMAN_CLASSES


# ---------------------------------------------------------------------------
# Engine selector tests (only run when engine_selector.py is available)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_ai_scifi_does_not_return_unsplash_first():
    """AI in sci-fi context should prefer pixabay/deviantart over unsplash."""
    result = select_engines("AI", "character", "sci-fi", ALL_PROVIDERS, {}, top_n=2)
    assert "unsplash" not in result, "Unsplash should not be selected for AI|sci-fi"


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_human_fiction_returns_unsplash():
    result = select_engines("human", "character", "fiction", ALL_PROVIDERS, {}, top_n=2)
    assert "unsplash" in result


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_historical_human_returns_wikimedia():
    result = select_engines("human", "character", "historical", ALL_PROVIDERS, {}, top_n=2)
    assert "wikimedia" in result


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_fantasy_creature_returns_deviantart():
    result = select_engines("mythical_beast", "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    assert "deviantart" in result


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_unknown_class_does_not_raise():
    """Completely unknown entity class must not raise an exception."""
    result = select_engines("unicorn_centaur_hybrid", "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    assert len(result) >= 1


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_result_only_contains_available_providers():
    limited = ["unsplash", "serpapi"]
    result = select_engines("AI", "character", "sci-fi", limited, {}, top_n=2)
    for p in result:
        assert p in limited


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_negative_rating_does_not_eliminate_provider():
    """A provider with bad ratings should still appear if it's the best available."""
    ratings = {"pixabay": -5, "deviantart": -5}
    limited = ["pixabay"]
    result = select_engines("AI", "character", "sci-fi", limited, ratings, top_n=1)
    assert result == ["pixabay"], "Only available provider must still be returned"


@pytest.mark.skipif(not ENGINE_SELECTOR_AVAILABLE, reason="engine_selector.py not yet implemented (Step 10)")
def test_rating_clamped_at_minus_5():
    """net_score below -5 should behave identically to -5 (clamping)."""
    result_minus5   = select_engines("human", "character", "fiction", ALL_PROVIDERS, {"unsplash": -5},   top_n=2)
    result_minus100 = select_engines("human", "character", "fiction", ALL_PROVIDERS, {"unsplash": -100}, top_n=2)
    assert result_minus5 == result_minus100
