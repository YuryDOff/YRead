"""
Unit tests for ontology_service.classify_entities_batch().
These tests make real LLM calls — mark slow/requires_api where appropriate.
"""
import pytest
from app.services.ontology_service import classify_entities_batch
from app.services.ontology_constants import ENTITY_CLASSES, NON_HUMAN_CLASSES


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_ontology_returns_valid_entity_class():
    """entity_class must always be from the closed enum."""
    entities = [{"name": "Robbie", "description": "A large clumsy robot with glowing red eyes", "visual_type": "AI"}]
    result = classify_entities_batch(entities)
    assert result[0]["entity_class"] in ENTITY_CLASSES


def test_ontology_non_human_sets_override():
    """AI/robot/alien entities must have anti_human_override=true."""
    entities = [
        {"name": "HAL 9000", "description": "A disembodied AI consciousness controlling a spaceship", "visual_type": "AI"},
        {"name": "Xenomorph", "description": "A biomechanical alien creature with acid blood", "visual_type": "alien"},
    ]
    results = classify_entities_batch(entities)
    for r in results:
        assert r["anti_human_override"] is True, f"{r['name']} should have anti_human_override=True"


def test_ontology_human_does_not_set_override():
    """Standard human characters must have anti_human_override=false."""
    entities = [{"name": "Susan Calvin", "description": "A frail woman in her seventies, roboticist", "visual_type": "woman"}]
    result = classify_entities_batch(entities)
    assert result[0]["anti_human_override"] is False


def test_ontology_visual_markers_count():
    """visual_markers must have 3-6 items."""
    entities = [{"name": "Gandalf", "description": "An old wizard with a grey beard and staff", "visual_type": "man"}]
    result = classify_entities_batch(entities)
    count = len(result[0]["visual_markers"])
    assert 3 <= count <= 6, f"Expected 3-6 visual markers, got {count}"


def test_ontology_search_archetype_present_for_non_human():
    """search_archetype must be non-null when anti_human_override=True."""
    entities = [{"name": "Robbie", "description": "A robot", "visual_type": "AI"}]
    result = classify_entities_batch(entities)
    if result[0]["anti_human_override"]:
        assert result[0]["search_archetype"] is not None


def test_ontology_fairy_tale_character():
    """Baba Yaga should be classified as folkloric, not human."""
    entities = [{"name": "Baba Yaga", "description": "A witch who lives in a hut on chicken legs in Russian folklore", "visual_type": "creature"}]
    result = classify_entities_batch(entities)
    assert result[0]["entity_class"] in {"folkloric", "fae", "mythical_beast", "human_supernatural"}
    assert result[0]["entity_class"] != "human"


def test_ontology_batch_preserves_order():
    """Output order must match input order."""
    entities = [
        {"name": "Alpha", "description": "A human detective", "visual_type": "man"},
        {"name": "Beta",  "description": "A robot assistant", "visual_type": "AI"},
    ]
    results = classify_entities_batch(entities)
    assert results[0]["name"] == "Alpha"
    assert results[1]["name"] == "Beta"


def test_ontology_empty_input():
    """Empty input must return empty list without error."""
    result = classify_entities_batch([])
    assert result == []


def test_ontology_entity_class_in_closed_enum_all():
    """All returned entity_class values must be from ENTITY_CLASSES."""
    entities = [
        {"name": "Dragon", "description": "A huge fire-breathing dragon", "visual_type": "creature"},
        {"name": "Jane", "description": "A young woman with brown hair", "visual_type": "woman"},
        {"name": "R2D2", "description": "A small spherical robot with blue and white panels", "visual_type": "AI"},
    ]
    results = classify_entities_batch(entities)
    for r in results:
        assert r["entity_class"] in ENTITY_CLASSES, f"Invalid entity_class: {r['entity_class']}"
