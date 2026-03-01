"""
Unit tests for Phase 1: data model foundation (models + schemas).
"""
import json
import pytest
from app.models import (
    Artefact,
    CoverAnalysis,
    VisualBibleEntry,
    CoverConcept,
    Book,
)
from app.schemas import (
    ArtefactResponse,
    CoverAnalysisResponse,
    BookAnalyzeRequest,
    BookResponse,
)


def test_artefact_model_fields():
    """Instantiate Artefact with all fields; assert field names and defaults."""
    a = Artefact(
        book_id=1,
        name="Magic Sword",
        physical_description="A glowing blade",
        symbolic_role="Power",
        narrative_function="Weapon",
        typical_contexts="Battle",
        is_main=1,
        visual_type="physical_object",
        is_well_known_entity=0,
        canonical_search_name="Excalibur",
        search_visual_analog="medieval sword",
        text_to_image_prompt="prompt",
        ontology_json="{}",
        entity_visual_tokens_json="{}",
        reference_image_url="http://example.com/img.png",
        selected_reference_urls='["u1","u2"]',
        visual_bible_images='["p1","p2"]',
        visual_bible_depth=3,
    )
    assert a.name == "Magic Sword"
    assert a.is_main == 1
    assert a.visual_bible_depth == 3
    assert a.physical_description == "A glowing blade"
    # Defaults when omitted (SQLAlchemy may set at persist time)
    a2 = Artefact(book_id=1, name="Ring")
    assert a2.is_main in (0, None)
    assert a2.is_well_known_entity in (0, None)


def test_cover_analysis_model_fields():
    """Instantiate CoverAnalysis; assert JSON fields are Text (will be serialized)."""
    c = CoverAnalysis(
        book_id=1,
        thematic_statement="A journey of redemption",
        emotional_promise="Hope",
        dominant_motifs='["light","shadow"]',
        symbolic_anchors='["tower","river"]',
        cover_mood_keywords='["dark","mysterious"]',
        genre_conventions="Fantasy",
        color_palette_direction='{"dominant":"blue","accent":"gold"}',
        cover_role_character_ids='[1,2]',
        cover_role_location_ids='[1]',
        cover_role_artefact_ids='[1]',
    )
    assert c.book_id == 1
    assert isinstance(c.dominant_motifs, str)
    assert json.loads(c.dominant_motifs) == ["light", "shadow"]
    assert isinstance(c.cover_role_character_ids, str)
    assert json.loads(c.cover_role_character_ids) == [1, 2]


def test_visual_bible_entry_defaults():
    """Assert status defaults to 'pending', is_approved to 0."""
    e = VisualBibleEntry(book_id=1, entity_type="character", entity_id=5)
    # Column default may be applied at persist time
    assert e.status in ("pending", None)
    assert e.is_approved in (0, None)
    assert VisualBibleEntry.status.default.arg == "pending"
    assert VisualBibleEntry.is_approved.default.arg == 0


def test_cover_concept_defaults():
    """Assert status 'pending', is_selected 0."""
    c = CoverConcept(book_id=1, concept_index=1)
    assert c.status in ("pending", None)
    assert c.is_selected in (0, None)
    assert CoverConcept.status.default.arg == "pending"
    assert CoverConcept.is_selected.default.arg == 0


def test_book_entity_activations_nullable():
    """Book with no entity_activations is valid."""
    b = Book(title="Test", author="A", workflow_type="cover_only")
    assert b.entity_activations is None
    assert b.genre is None


def test_artefact_response_schema_deserializes_selected_urls():
    """ArtefactResponse with selected_reference_urls='[\"url1\",\"url2\"]' -> list[str]."""
    class MockArtefact:
        pass

    m = MockArtefact()
    m.id = 1
    m.book_id = 1
    m.name = "Sword"
    m.physical_description = None
    m.symbolic_role = None
    m.narrative_function = None
    m.typical_contexts = None
    m.is_main = 0
    m.visual_type = None
    m.is_well_known_entity = 0
    m.canonical_search_name = None
    m.search_visual_analog = None
    m.text_to_image_prompt = None
    m.reference_image_url = None
    m.selected_reference_urls = '["url1", "url2"]'
    m.visual_bible_images = None
    m.visual_bible_depth = None

    resp = ArtefactResponse.model_validate(m)
    assert resp.selected_reference_urls == ["url1", "url2"]


def test_book_analyze_request_defaults():
    """BookAnalyzeRequest() — entity_types defaults to all four."""
    req = BookAnalyzeRequest(style_category="fiction")
    assert req.entity_types == ["cover", "characters", "locations", "artefacts"]
    assert req.genre == ""
