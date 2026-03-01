"""
Unit tests for Phase 4: cover_analysis_service and genre_defaults.
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from app.services.cover_analysis_service import (
    _get_full_text_summary,
    extract_thematic_material,
    synthesise_cover_brief,
    run_cover_analysis,
    GENRE_COVER_CONVENTIONS,
)
from app.services.genre_defaults import GENRE_DEFAULT_ACTIVATIONS, get_default_activations


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_chunk_analyses(n: int, with_narrative: bool = False):
    out = []
    for i in range(n):
        c = {"chunk_index": i, "visual_moment": f"Scene {i} summary text.", "dramatic_score": 0.5}
        if with_narrative:
            c["narrative_summary"] = f"Narrative for chunk {i}."
        out.append(c)
    return out


SAMPLE_CHUNK_ANALYSES = _make_chunk_analyses(5, with_narrative=True)

SAMPLE_THEMATIC = {
    "dominant_motifs": ["light", "shadow"],
    "symbolic_anchors": ["the tower"],
    "emotional_arc": "From fear to hope.",
    "recurring_imagery": ["forest", "river"],
    "central_tension": "Man vs nature.",
    "tone_words": ["dark", "hopeful"],
}


# ---------------------------------------------------------------------------
# _get_full_text_summary
# ---------------------------------------------------------------------------

def test_get_full_text_summary_caps_tokens():
    """200 chunk_analyses; assert output under 12000 tokens (tiktoken count)."""
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    except Exception:
        pytest.skip("tiktoken not available")
    chunk_analyses = _make_chunk_analyses(200, with_narrative=True)
    result = _get_full_text_summary(chunk_analyses)
    tokens = enc.encode(result)
    assert len(tokens) <= 12000, f"Expected <= 12000 tokens, got {len(tokens)}"


# ---------------------------------------------------------------------------
# extract_thematic_material
# ---------------------------------------------------------------------------

def test_extract_thematic_material_structure():
    with patch("app.services.cover_analysis_service._get_client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps({
            "dominant_motifs": ["a", "b"],
            "symbolic_anchors": ["x"],
            "emotional_arc": "Arc.",
            "recurring_imagery": ["i"],
            "central_tension": "Tension.",
            "tone_words": ["dark"],
        })
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = extract_thematic_material(SAMPLE_CHUNK_ANALYSES, "fantasy")
    assert "dominant_motifs" in result
    assert isinstance(result["symbolic_anchors"], list)


def test_synthesise_cover_brief_includes_all_fields():
    with patch("app.services.cover_analysis_service._get_client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock()]
        mock_resp.choices[0].message.content = json.dumps({
            "thematic_statement": "S",
            "emotional_promise": "E",
            "dominant_motifs": [],
            "symbolic_anchors": [],
            "cover_mood_keywords": [],
            "genre_conventions": "G",
            "genre_subversion_opportunity": "",
            "typography_direction": "T",
            "color_palette_direction": "C",
            "cover_t2i_prompt": "P",
            "cover_negative_prompt": "N",
            "cover_role_character_ids_hints": [],
            "cover_role_location_ids_hints": [],
            "cover_role_artefact_ids_hints": [],
        })
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = synthesise_cover_brief(SAMPLE_THEMATIC, "fantasy", "illustrated", [], [])

    required = [
        "thematic_statement", "emotional_promise", "cover_t2i_prompt",
        "typography_direction", "color_palette_direction", "cover_mood_keywords",
    ]
    for field in required:
        assert field in result, f"Missing field: {field}"


def test_genre_conventions_map_covers_known_genres():
    assert "fantasy" in GENRE_COVER_CONVENTIONS
    assert "thriller" in GENRE_COVER_CONVENTIONS


def test_run_cover_analysis_calls_both_stages():
    with patch("app.services.cover_analysis_service.extract_thematic_material") as s1:
        with patch("app.services.cover_analysis_service.synthesise_cover_brief") as s2:
            s1.return_value = SAMPLE_THEMATIC
            s2.return_value = {"thematic_statement": "test", "emotional_promise": "", "dominant_motifs": [], "symbolic_anchors": [], "cover_mood_keywords": [], "genre_conventions": "", "genre_subversion_opportunity": "", "typography_direction": "", "color_palette_direction": "", "cover_t2i_prompt": "", "cover_negative_prompt": "", "cover_role_character_ids_hints": [], "cover_role_location_ids_hints": [], "cover_role_artefact_ids_hints": []}
            run_cover_analysis(SAMPLE_CHUNK_ANALYSES, "fantasy", "illustrated", [], [])
    s1.assert_called_once()
    s2.assert_called_once()


# ---------------------------------------------------------------------------
# genre_defaults
# ---------------------------------------------------------------------------

def test_genre_defaults_full_book_always_all_four():
    assert get_default_activations("thriller", "full_book") == [
        "cover", "characters", "locations", "artefacts",
    ]
    assert get_default_activations("thriller", "full") == [
        "cover", "characters", "locations", "artefacts",
    ]


def test_genre_defaults_cover_only_thriller():
    assert get_default_activations("thriller", "cover_only") == ["cover"]


def test_genre_defaults_cover_only_fantasy():
    result = get_default_activations("fantasy", "cover_only")
    assert "characters" in result
    assert "locations" in result
