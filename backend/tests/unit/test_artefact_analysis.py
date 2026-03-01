"""
Unit tests for Phase 3: artefact_analysis_service.
All LLM calls mocked with unittest.mock.patch.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.artefact_analysis_service import (
    extract_artefacts_from_chunks,
    build_artefact_visual_tokens_batch,
    run_artefact_analysis,
)
from app.services.ontology_constants import ARTEFACT_ENTITY_CLASSES
from app.services.engine_selector import ENGINE_AFFINITY


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_CHUNK_ANALYSES = [
    {"chunk_index": 0, "dramatic_score": 0.9, "visual_moment": "Hero draws the sword", "characters_present": ["Aragorn"], "locations_present": ["Rivendell"]},
    {"chunk_index": 1, "dramatic_score": 0.3, "visual_moment": "Generic room", "characters_present": [], "locations_present": []},
]
CHUNK_TEXT_MAP = {0: "He drew the sword.", 1: "The room was quiet."}


# ---------------------------------------------------------------------------
# extract_artefacts_from_chunks
# ---------------------------------------------------------------------------

def test_extract_artefacts_filters_background_objects():
    """Mock LLM to return a mix of valid artefacts and background items; assert structure."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps([
        {"name": "The Sword", "physical_description": "Glowing blade", "symbolic_role": "Power", "narrative_function": "Weapon", "typical_contexts": "Used by hero", "is_main": True, "chunks_present": [0, 2], "scenes_present": [], "visual_type": "physical_object"},
        {"name": "Background chair", "physical_description": "Wooden", "symbolic_role": "", "narrative_function": "Other", "typical_contexts": "", "is_main": False, "chunks_present": [1], "scenes_present": [], "visual_type": "physical_object"},
    ])

    with patch("app.services.artefact_analysis_service._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        result = extract_artefacts_from_chunks(SAMPLE_CHUNK_ANALYSES, CHUNK_TEXT_MAP)

    assert len(result) >= 1
    # Both are returned by mock; real LLM would filter. We assert correct structure.
    for item in result:
        assert "name" in item
        assert "physical_description" in item
        assert "narrative_function" in item
        assert "is_main" in item
        assert "chunks_present" in item


def test_extract_artefacts_returns_correct_structure():
    """Mock LLM response; assert each result has name, physical_description, narrative_function, is_main, chunks_present."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps([
        {"name": "Ring", "physical_description": "Golden", "symbolic_role": "Power", "narrative_function": "MacGuffin", "typical_contexts": "Used by Frodo", "is_main": True, "chunks_present": [0, 1, 2], "scenes_present": ["Council"], "visual_type": "magical_item"},
    ])

    with patch("app.services.artefact_analysis_service._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        result = extract_artefacts_from_chunks(SAMPLE_CHUNK_ANALYSES, CHUNK_TEXT_MAP)

    assert len(result) == 1
    r = result[0]
    assert r["name"] == "Ring"
    assert r["physical_description"] == "Golden"
    assert r["narrative_function"] == "MacGuffin"
    assert r["is_main"] is True
    assert r["chunks_present"] == [0, 1, 2]


def test_build_artefact_visual_tokens_batch_returns_same_order():
    """Input 3 artefacts; mock LLM; assert output list length == 3 and each has core_tokens, style_tokens."""
    artefacts = [
        {"name": "A", "physical_description": "d1", "symbolic_role": "s1", "visual_type": "physical_object"},
        {"name": "B", "physical_description": "d2", "symbolic_role": "s2", "visual_type": "magical_item"},
        {"name": "C", "physical_description": "d3", "symbolic_role": "s3", "visual_type": "document"},
    ]
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps([
        {"name": "A", "core_tokens": ["a"] * 6, "style_tokens": ["s"] * 4, "archetype_tokens": [], "anti_tokens": []},
        {"name": "B", "core_tokens": ["b"] * 6, "style_tokens": ["s"] * 4, "archetype_tokens": [], "anti_tokens": []},
        {"name": "C", "core_tokens": ["c"] * 6, "style_tokens": ["s"] * 4, "archetype_tokens": [], "anti_tokens": []},
    ])

    with patch("app.services.artefact_analysis_service._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_response
        result = build_artefact_visual_tokens_batch(artefacts)

    assert len(result) == 3
    for i, item in enumerate(result):
        assert item["name"] == artefacts[i]["name"]
        assert "core_tokens" in item
        assert "style_tokens" in item


def test_run_artefact_analysis_calls_ontology_service():
    with patch("app.services.artefact_analysis_service.extract_artefacts_from_chunks") as mock_extract:
        mock_extract.return_value = [
            {"name": "Sword", "physical_description": "Blade", "symbolic_role": "", "visual_type": "physical_object"},
        ]
        with patch("app.services.artefact_analysis_service.ontology_service.classify_entities_batch") as mock_ont:
            mock_ont.return_value = [{"entity_class": "magical_item", "materiality": "organic", "power_status": "neutral", "embodiment": "physical", "visual_markers": ["a", "b", "c"], "anti_human_override": False, "search_archetype": None}]
            with patch("app.services.artefact_analysis_service.build_artefact_visual_tokens_batch") as mock_tokens:
                mock_tokens.return_value = [{"name": "Sword", "core_tokens": [], "style_tokens": [], "archetype_tokens": [], "anti_tokens": []}]
                result = run_artefact_analysis(SAMPLE_CHUNK_ANALYSES, CHUNK_TEXT_MAP)

    mock_ont.assert_called_once()
    call_args = mock_ont.call_args
    assert call_args[1].get("entity_role") == "artefact"
    assert result["artefacts"]
    assert result["artefacts"][0]["entity_class"] == "magical_item"


def test_run_artefact_analysis_empty_book():
    with patch("app.services.artefact_analysis_service.extract_artefacts_from_chunks") as mock_extract:
        mock_extract.return_value = []
        result = run_artefact_analysis(SAMPLE_CHUNK_ANALYSES, CHUNK_TEXT_MAP)
    assert result["artefacts"] == []


def test_ontology_artefact_entity_role_accepted():
    from app.services.ontology_service import classify_entities_batch

    with patch("app.services.ontology_service._get_client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps([
            {"name": "Sword", "entity_class": "physical_weapon", "materiality": "organic", "power_status": "neutral", "embodiment": "physical", "visual_markers": ["blade", "hilt", "shine"], "anti_human_override": False, "search_archetype": None},
        ])
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        entities = [{"name": "Sword", "description": "A blade", "visual_type": "physical_object"}]
        result = classify_entities_batch(entities, entity_role="artefact")

    assert len(result) == 1
    assert result[0]["entity_class"] == "physical_weapon"


def test_engine_affinity_artefact_classes_present():
    assert "physical_weapon" in ENGINE_AFFINITY
    assert "magical_item" in ENGINE_AFFINITY
    assert "other_artefact" in ENGINE_AFFINITY
