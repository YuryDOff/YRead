"""
Unit tests for Entity Visual Token Builder (Step 5).

Tests the pure-logic parts of build_entity_visual_tokens_batch() and fallback helpers
without LLM calls, plus validates the output schema contract via LLM mocking.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.ai_service import (
        build_entity_visual_tokens_batch,
        _entity_token_fallback,
        _build_entity_token_fallbacks,
    )
    ENTITY_TOKEN_BUILDER_AVAILABLE = True
except ImportError:
    ENTITY_TOKEN_BUILDER_AVAILABLE = False

skip_if_unavailable = pytest.mark.skipif(
    not ENTITY_TOKEN_BUILDER_AVAILABLE,
    reason="build_entity_visual_tokens_batch not yet implemented (Step 5)",
)


def _make_mock_openai_response(results: list[dict]):
    """Build a mock OpenAI chat completion response returning given JSON array."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(results)
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 200
    mock_response.usage.total_tokens = 300
    return mock_response


# ---------------------------------------------------------------------------
# Fallback helpers — no LLM, always runnable
# ---------------------------------------------------------------------------

def test_fallback_non_human_has_no_human_core_tokens():
    """Fallback for non-human entity must not produce human-portrait core tokens."""
    entity = {
        "name": "Robbie",
        "entity_class": "robot",
        "anti_human_override": True,
        "visual_markers": ["glowing red eyes", "cylindrical body", "metal plating"],
        "search_archetype": "boxy robot",
    }
    result = _entity_token_fallback(entity)
    HUMAN_TERMS = {"portrait", "person", "man", "woman", "face", "human"}
    for token in result["core_tokens"]:
        assert token.lower() not in HUMAN_TERMS, \
            f"Human term '{token}' in core_tokens for non-human fallback"


def test_fallback_human_produces_archetype_tokens_empty():
    """Fallback for human entity must have empty archetype_tokens."""
    entity = {
        "name": "Susan Calvin",
        "entity_class": "human",
        "anti_human_override": False,
        "visual_markers": ["sharp eyes", "grey hair", "formal suit"],
        "search_archetype": None,
    }
    result = _entity_token_fallback(entity)
    assert result["archetype_tokens"] == [], "Human entity should have empty archetype_tokens"
    assert result["anti_tokens"] == [], "Human entity should have empty anti_tokens"


def test_fallback_non_human_has_non_empty_archetype_tokens():
    """Fallback for non-human entity must have non-empty archetype_tokens."""
    entity = {
        "name": "HAL 9000",
        "entity_class": "AI",
        "anti_human_override": True,
        "visual_markers": ["glowing red camera eye", "disembodied voice"],
        "search_archetype": "disembodied AI camera eye",
    }
    result = _entity_token_fallback(entity)
    assert len(result["archetype_tokens"]) > 0, "Non-human entity should have archetype_tokens"


def test_fallback_output_has_required_keys():
    """Fallback output must always have all required keys."""
    entity = {"name": "Test", "entity_class": "human", "anti_human_override": False}
    result = _entity_token_fallback(entity)
    for key in ("name", "core_tokens", "style_tokens", "archetype_tokens", "anti_tokens"):
        assert key in result, f"Missing key '{key}' in fallback output"


def test_batch_fallback_preserves_count():
    """_build_entity_token_fallbacks must return same count as input."""
    entities = [
        {"name": "A", "entity_class": "human", "anti_human_override": False},
        {"name": "B", "entity_class": "robot", "anti_human_override": True, "visual_markers": []},
        {"name": "C", "entity_class": "alien", "anti_human_override": True, "visual_markers": []},
    ]
    results = _build_entity_token_fallbacks(entities)
    assert len(results) == 3, f"Expected 3 results, got {len(results)}"


def test_batch_fallback_preserves_order():
    """_build_entity_token_fallbacks output order must match input order."""
    entities = [
        {"name": "Alpha", "entity_class": "human", "anti_human_override": False},
        {"name": "Beta", "entity_class": "robot", "anti_human_override": True, "visual_markers": []},
    ]
    results = _build_entity_token_fallbacks(entities)
    assert results[0]["name"] == "Alpha"
    assert results[1]["name"] == "Beta"


# ---------------------------------------------------------------------------
# Schema validation — test the output contract with mock data
# (simulate what build_entity_visual_tokens_batch should produce)
# ---------------------------------------------------------------------------

@skip_if_unavailable
def test_empty_input_returns_empty_list():
    result = build_entity_visual_tokens_batch([])
    assert result == [], "Empty input should return empty list"


@skip_if_unavailable
def test_output_count_matches_input():
    """Output length must equal input length (uses mock LLM)."""
    entities = [
        {"name": "Alice", "entity_class": "human", "anti_human_override": False,
         "visual_markers": [], "description": "A woman"},
        {"name": "Robot X", "entity_class": "robot", "anti_human_override": True,
         "visual_markers": ["red eyes", "metal body"], "description": "A robot"},
    ]
    mock_llm_output = [
        {"name": "Alice", "core_tokens": ["woman", "portrait", "detailed", "cinematic", "elegant", "realistic"],
         "style_tokens": ["soft lighting", "natural", "warm", "cinematic"],
         "archetype_tokens": [], "anti_tokens": []},
        {"name": "Robot X", "core_tokens": ["robot", "metal", "industrial", "red eyes", "cylindrical", "mechanical"],
         "style_tokens": ["dramatic lighting", "cold", "sci-fi", "neon"],
         "archetype_tokens": ["mechanical construct", "android", "robotic figure"],
         "anti_tokens": ["man portrait", "human face"]},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    assert len(results) == len(entities), \
        f"Expected {len(entities)} results, got {len(results)}"


@skip_if_unavailable
def test_output_order_matches_input():
    """Output order must match input order (uses mock LLM)."""
    entities = [
        {"name": "Alpha", "entity_class": "human", "anti_human_override": False,
         "visual_markers": [], "description": "human"},
        {"name": "Beta", "entity_class": "robot", "anti_human_override": True,
         "visual_markers": ["metal body"], "description": "robot"},
    ]
    mock_llm_output = [
        {"name": "Alpha", "core_tokens": ["figure", "a", "b", "c", "d", "e"],
         "style_tokens": ["s1", "s2", "s3", "s4"], "archetype_tokens": [], "anti_tokens": []},
        {"name": "Beta", "core_tokens": ["robot", "metal", "industrial", "red", "cold", "mechanical"],
         "style_tokens": ["neon", "dark", "dramatic", "sci-fi"],
         "archetype_tokens": ["mechanical construct", "android", "robotic"],
         "anti_tokens": ["man portrait", "human"]},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    assert results[0]["name"] == "Alpha", "First result should be Alpha"
    assert results[1]["name"] == "Beta", "Second result should be Beta"


@skip_if_unavailable
def test_all_outputs_have_required_keys():
    """Every result must have core_tokens, style_tokens, archetype_tokens, anti_tokens (uses mock LLM)."""
    entities = [
        {"name": "Test", "entity_class": "human", "anti_human_override": False,
         "visual_markers": [], "description": "A person"},
    ]
    mock_llm_output = [
        {"name": "Test", "core_tokens": ["a", "b", "c", "d", "e", "f"],
         "style_tokens": ["s1", "s2", "s3", "s4"], "archetype_tokens": [], "anti_tokens": []},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    for r in results:
        for key in ("core_tokens", "style_tokens", "archetype_tokens", "anti_tokens"):
            assert key in r, f"Missing key '{key}' in result: {r}"
        assert isinstance(r["core_tokens"], list)
        assert isinstance(r["style_tokens"], list)
        assert isinstance(r["archetype_tokens"], list)
        assert isinstance(r["anti_tokens"], list)


@skip_if_unavailable
def test_anti_human_entity_core_tokens_clean():
    """
    For anti_human_override=True entities: even if LLM returns human terms,
    the post-processing must strip them from core_tokens.
    """
    HUMAN_TERMS = {"portrait", "person", "man", "woman", "face", "human"}
    entities = [
        {
            "name": "Robbie",
            "description": "A large robot with glowing red eyes and cylindrical body",
            "entity_class": "robot",
            "anti_human_override": True,
            "visual_markers": ["glowing red eyes", "cylindrical body", "metallic surface"],
            "search_archetype": "boxy robot figure",
        }
    ]
    # Simulate LLM returning human terms (which should be stripped)
    mock_llm_output = [
        {"name": "Robbie",
         "core_tokens": ["glowing red eyes", "cylindrical body", "metallic surface", "man portrait", "human", "robot"],
         "style_tokens": ["dramatic", "neon", "cold", "sci-fi"],
         "archetype_tokens": ["mechanical construct", "android figure", "robotic body"],
         "anti_tokens": ["man portrait", "human face", "person"]},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    if results:
        for token in results[0].get("core_tokens", []):
            assert token.lower() not in HUMAN_TERMS, \
                f"Human term '{token}' found in core_tokens after anti_human filtering"


@skip_if_unavailable
def test_anti_human_entity_has_archetype_tokens():
    """For anti_human_override=True: archetype_tokens should be non-empty (uses mock LLM)."""
    entities = [
        {
            "name": "Xenomorph",
            "description": "Biomechanical alien creature with acid blood",
            "entity_class": "alien",
            "anti_human_override": True,
            "visual_markers": ["biomechanical form", "elongated head", "acid blood"],
            "search_archetype": "biomechanical alien creature",
        }
    ]
    mock_llm_output = [
        {"name": "Xenomorph",
         "core_tokens": ["biomechanical", "elongated", "alien", "dark", "menacing", "creature"],
         "style_tokens": ["horror", "dramatic", "atmospheric", "dark"],
         "archetype_tokens": ["biomechanical alien", "extraterrestrial creature", "xenomorph"],
         "anti_tokens": ["human face", "person portrait", "man"]},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    if results:
        archetype = results[0].get("archetype_tokens", [])
        assert len(archetype) > 0, "Non-human entity should have non-empty archetype_tokens"


@skip_if_unavailable
def test_human_entity_has_empty_anti_tokens():
    """For standard human entities: anti_tokens should be empty (uses mock LLM)."""
    entities = [
        {
            "name": "Susan Calvin",
            "description": "A frail woman in her seventies, roboticist",
            "entity_class": "human",
            "anti_human_override": False,
            "visual_markers": ["sharp eyes", "grey hair", "formal attire"],
            "search_archetype": None,
        }
    ]
    mock_llm_output = [
        {"name": "Susan Calvin",
         "core_tokens": ["elderly woman", "sharp eyes", "grey hair", "formal", "scientist", "portrait"],
         "style_tokens": ["cinematic", "natural lighting", "detailed", "realistic"],
         "archetype_tokens": [],
         "anti_tokens": []},
    ]
    mock_response = _make_mock_openai_response(mock_llm_output)
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.return_value = mock_response
        results = build_entity_visual_tokens_batch(entities)
    if results:
        anti = results[0].get("anti_tokens", [])
        assert anti == [], f"Human entity should have empty anti_tokens, got: {anti}"


@skip_if_unavailable
def test_llm_failure_falls_back_gracefully():
    """When LLM fails (raises RuntimeError), must fall back to defaults without raising."""
    entities = [
        {"name": "Test", "entity_class": "robot", "anti_human_override": True,
         "visual_markers": ["metal", "gears"], "description": "A robot"},
    ]
    with patch("app.services.ai_service._get_client") as mock_get_client:
        mock_get_client.return_value.chat.completions.create.side_effect = RuntimeError("API down")
        results = build_entity_visual_tokens_batch(entities)
    assert len(results) == 1, "Should return 1 fallback result"
    assert "core_tokens" in results[0]
