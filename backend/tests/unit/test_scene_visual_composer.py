"""
Unit tests for Scene Visual Composer (Step 7).

Tests the pure-logic parts of compose_scenes_batch() and fallback helpers.
LLM-dependent tests use unittest.mock to avoid requiring an API key.
"""
import json
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.scene_visual_composer import (
        _build_fallback_svt,
        _build_fallback_t2i,
        _apply_scene_fallbacks,
        compose_scenes_batch,
    )
    COMPOSER_AVAILABLE = True
except ImportError:
    COMPOSER_AVAILABLE = False

skip_if_unavailable = pytest.mark.skipif(
    not COMPOSER_AVAILABLE,
    reason="scene_visual_composer.py not yet implemented (Step 7)",
)


def _make_mock_scene_composer_response(results: list[dict]):
    """Build a mock OpenAI response for scene composer."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = json.dumps(results)
    mock_response.usage.prompt_tokens = 200
    mock_response.usage.completion_tokens = 400
    mock_response.usage.total_tokens = 600
    return mock_response


def _make_llm_output_for_scenes(scenes: list[dict]) -> list[dict]:
    """Build valid mock LLM output for a list of scenes."""
    output = []
    for i, scene in enumerate(scenes):
        has_non_human = any(
            o.get("anti_human_override", False)
            for o in [ROBOT_CHAR_ONTOLOGY]
            if o.get("name", "").lower() in {n.lower() for n in scene.get("characters_present", [])}
        )
        char_tokens = (
            ["glowing red eyes", "cylindrical body", "metallic surface", "robot figure"]
            if has_non_human else ["figure", "portrait subject", "detailed"]
        )
        output.append({
            "scene_id": i + 1,
            "scene_visual_tokens": {
                "core_tokens": ["dramatic", "atmospheric", "detailed", "cinematic", "vivid", "high contrast"],
                "style_tokens": ["cinematic lighting", "dramatic shadows", "moody", "atmospheric"],
                "composition_tokens": ["wide shot", "establishing shot", "medium shot"],
                "character_tokens": char_tokens,
                "environment_tokens": [scene.get("primary_location", "environment"), "detailed", "atmospheric"],
            },
            "t2i_prompt_json": {
                "abstract": f"A dramatic {scene.get('scene_type', 'atmospheric')} scene in {scene.get('primary_location', 'a location')}, wide shot, cinematic lighting, high detail illustration, {', '.join(char_tokens[:2])}",
                "flux": f"A dramatic scene, high detail, 8k, cinematic, {scene.get('title', '')}",
                "sd": f"(dramatic scene:1.2), masterpiece --neg blurry, low quality",
            },
        })
    return output

# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

HUMAN_CHAR_ONTOLOGY = {
    "name": "Susan Calvin",
    "entity_class": "human",
    "anti_human_override": False,
    "visual_markers": ["sharp eyes", "grey hair", "formal attire"],
    "search_archetype": None,
}

ROBOT_CHAR_ONTOLOGY = {
    "name": "Robbie",
    "entity_class": "robot",
    "anti_human_override": True,
    "visual_markers": ["glowing red eyes", "cylindrical body", "metallic surface"],
    "search_archetype": "boxy robot figure",
}

SAMPLE_SCENE = {
    "title": "The Lab Confrontation",
    "scene_type": "conflict",
    "chunk_start_index": 5,
    "chunk_end_index": 9,
    "narrative_summary": "Susan confronts Robbie in the laboratory.",
    "visual_description": "A tense standoff between a woman and a large robot in a dimly lit lab.",
    "characters_present": ["Susan Calvin", "Robbie"],
    "primary_location": "Laboratory",
    "visual_intensity": 0.8,
    "illustration_priority": "high",
    "scene_prompt_draft": "Dimly lit laboratory, tense confrontation, dramatic shadows.",
}

SCENE_NO_HUMANS = {
    "title": "Robot Uprising",
    "scene_type": "climax",
    "chunk_start_index": 15,
    "chunk_end_index": 19,
    "narrative_summary": "Robots take control of the facility.",
    "visual_description": "Rows of robots march through a metallic corridor under red alarm lights.",
    "characters_present": ["Robbie"],
    "primary_location": "Factory Floor",
    "visual_intensity": 0.9,
    "illustration_priority": "high",
    "scene_prompt_draft": "Metallic corridor, red alarm lights, rows of robots marching.",
}


# ---------------------------------------------------------------------------
# Fallback SVT — pure logic, no LLM
# ---------------------------------------------------------------------------

@skip_if_unavailable
def test_fallback_svt_has_required_keys():
    """Fallback SVT must have all required token keys."""
    svt = _build_fallback_svt(SAMPLE_SCENE, [HUMAN_CHAR_ONTOLOGY], "fiction")
    for key in ("core_tokens", "style_tokens", "composition_tokens", "character_tokens", "environment_tokens"):
        assert key in svt, f"Missing key '{key}' in fallback SVT"


@skip_if_unavailable
def test_fallback_svt_composition_has_framing_term():
    """Fallback SVT composition_tokens must contain at least one framing term."""
    FRAMING_TERMS = {
        "wide shot", "close-up", "medium shot", "establishing shot",
        "over-the-shoulder", "low angle", "bird's eye view", "dutch angle",
        "tracking shot", "wide angle"
    }
    svt = _build_fallback_svt(SAMPLE_SCENE, [HUMAN_CHAR_ONTOLOGY], "fiction")
    comp = svt.get("composition_tokens", [])
    assert any(t.lower() in FRAMING_TERMS for t in comp), \
        f"No framing term in composition_tokens: {comp}"


@skip_if_unavailable
def test_fallback_svt_non_human_character_tokens_use_markers():
    """For a scene with a non-human character, character_tokens should use visual_markers."""
    svt = _build_fallback_svt(SCENE_NO_HUMANS, [ROBOT_CHAR_ONTOLOGY], "sci-fi")
    char_tokens = svt.get("character_tokens", [])
    # Should include at least one of Robbie's visual markers
    robbie_markers = {"glowing red eyes", "cylindrical body", "metallic surface"}
    has_marker = any(t.lower() in robbie_markers for t in char_tokens)
    assert has_marker, f"Non-human character markers not in character_tokens: {char_tokens}"


# ---------------------------------------------------------------------------
# Fallback T2I — pure logic, no LLM
# ---------------------------------------------------------------------------

@skip_if_unavailable
def test_fallback_t2i_has_required_keys():
    """Fallback T2I must have abstract, flux, sd keys."""
    svt = _build_fallback_svt(SAMPLE_SCENE, [HUMAN_CHAR_ONTOLOGY], "fiction")
    t2i = _build_fallback_t2i(SAMPLE_SCENE, svt, "fiction")
    for key in ("abstract", "flux", "sd"):
        assert key in t2i, f"Missing key '{key}' in fallback T2I"


@skip_if_unavailable
def test_fallback_t2i_abstract_min_length():
    """T2I abstract must be at least 50 characters."""
    svt = _build_fallback_svt(SAMPLE_SCENE, [HUMAN_CHAR_ONTOLOGY], "fiction")
    t2i = _build_fallback_t2i(SAMPLE_SCENE, svt, "fiction")
    abstract = t2i.get("abstract", "")
    assert len(abstract) >= 50, \
        f"T2I abstract too short ({len(abstract)} chars): '{abstract}'"


@skip_if_unavailable
def test_fallback_t2i_uses_scene_prompt_draft_when_available():
    """If scene_prompt_draft is >= 50 chars, T2I abstract should use it."""
    scene_with_draft = dict(SAMPLE_SCENE)
    long_draft = "A dimly lit laboratory with towering metal shelves, a tense confrontation between a scientist and a large industrial robot under flickering fluorescent lights"
    scene_with_draft["scene_prompt_draft"] = long_draft
    svt = _build_fallback_svt(scene_with_draft, [HUMAN_CHAR_ONTOLOGY], "sci-fi")
    t2i = _build_fallback_t2i(scene_with_draft, svt, "sci-fi")
    assert long_draft[:50] in t2i["abstract"], \
        "Abstract should use the scene_prompt_draft when it's long enough"


# ---------------------------------------------------------------------------
# _apply_scene_fallbacks — pure logic, no LLM
# ---------------------------------------------------------------------------

@skip_if_unavailable
def test_apply_fallbacks_adds_visual_tokens_field():
    """_apply_scene_fallbacks must add scene_visual_tokens to all scenes."""
    scenes = [SAMPLE_SCENE, SCENE_NO_HUMANS]
    result = _apply_scene_fallbacks(scenes, [HUMAN_CHAR_ONTOLOGY, ROBOT_CHAR_ONTOLOGY], "sci-fi")
    for scene in result:
        assert "scene_visual_tokens" in scene, "scene_visual_tokens missing after fallback"
        assert "t2i_prompt_json" in scene, "t2i_prompt_json missing after fallback"


@skip_if_unavailable
def test_apply_fallbacks_preserves_original_fields():
    """_apply_scene_fallbacks must not remove existing scene fields."""
    scenes = [dict(SAMPLE_SCENE)]
    result = _apply_scene_fallbacks(scenes, [HUMAN_CHAR_ONTOLOGY], "fiction")
    for field in ("title", "scene_type", "chunk_start_index", "chunk_end_index",
                  "narrative_summary", "scene_prompt_draft"):
        assert field in result[0], f"Field '{field}' was removed by apply_fallbacks"


@skip_if_unavailable
def test_apply_fallbacks_count_preserved():
    """Output count must equal input count."""
    scenes = [SAMPLE_SCENE, SCENE_NO_HUMANS]
    result = _apply_scene_fallbacks(scenes, [ROBOT_CHAR_ONTOLOGY], "sci-fi")
    assert len(result) == 2, f"Expected 2 results, got {len(result)}"


# ---------------------------------------------------------------------------
# compose_scenes_batch schema validation (with potential LLM call)
# ---------------------------------------------------------------------------

@skip_if_unavailable
def test_compose_batch_empty_input_returns_empty():
    result = compose_scenes_batch([], [], "fiction")
    assert result == [], "Empty input should return empty list"


@skip_if_unavailable
def test_compose_batch_preserves_count():
    """Output length must equal input length (uses mock LLM)."""
    scenes = [SAMPLE_SCENE, SCENE_NO_HUMANS]
    mock_output = _make_llm_output_for_scenes(scenes)
    mock_resp = _make_mock_scene_composer_response(mock_output)
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY, ROBOT_CHAR_ONTOLOGY], "sci-fi")
    assert len(result) == 2, f"Expected 2 results, got {len(result)}"


@skip_if_unavailable
def test_compose_batch_all_scenes_have_visual_tokens():
    """Every output scene must have scene_visual_tokens with required sub-keys (uses mock LLM)."""
    scenes = [SAMPLE_SCENE]
    mock_output = _make_llm_output_for_scenes(scenes)
    mock_resp = _make_mock_scene_composer_response(mock_output)
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY, ROBOT_CHAR_ONTOLOGY], "sci-fi")
    for scene in result:
        svt = scene.get("scene_visual_tokens", {})
        assert svt, f"scene_visual_tokens missing or empty for scene: {scene.get('title')}"
        for key in ("core_tokens", "style_tokens", "composition_tokens"):
            assert key in svt, f"Missing '{key}' in scene_visual_tokens"


@skip_if_unavailable
def test_compose_batch_all_scenes_have_t2i_prompt():
    """Every output scene must have t2i_prompt_json with 'abstract' >= 50 chars (uses mock LLM)."""
    scenes = [SAMPLE_SCENE]
    mock_output = _make_llm_output_for_scenes(scenes)
    mock_resp = _make_mock_scene_composer_response(mock_output)
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY], "fiction")
    for scene in result:
        t2i = scene.get("t2i_prompt_json", {})
        assert t2i, f"t2i_prompt_json missing for scene: {scene.get('title')}"
        assert "abstract" in t2i, f"'abstract' key missing in t2i_prompt_json"
        assert len(t2i["abstract"]) >= 50, \
            f"T2I abstract too short ({len(t2i['abstract'])} chars)"


@skip_if_unavailable
def test_compose_batch_composition_has_framing_term():
    """Every scene's composition_tokens must contain at least one framing term (uses mock LLM)."""
    FRAMING_TERMS = {
        "wide shot", "close-up", "medium shot", "establishing shot",
        "over-the-shoulder", "low angle", "bird's eye view", "dutch angle",
        "tracking shot", "wide angle", "panoramic"
    }
    scenes = [SAMPLE_SCENE, SCENE_NO_HUMANS]
    mock_output = _make_llm_output_for_scenes(scenes)
    mock_resp = _make_mock_scene_composer_response(mock_output)
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY, ROBOT_CHAR_ONTOLOGY], "sci-fi")
    for scene in result:
        comp = scene.get("scene_visual_tokens", {}).get("composition_tokens", [])
        has_framing = any(t.lower() in FRAMING_TERMS for t in comp)
        assert has_framing, \
            f"No framing term in composition_tokens for scene '{scene.get('title')}': {comp}"


@skip_if_unavailable
def test_compose_batch_llm_failure_falls_back_gracefully():
    """When LLM fails, compose_scenes_batch must return scenes with fallback tokens (no raise)."""
    scenes = [SAMPLE_SCENE, SCENE_NO_HUMANS]
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.side_effect = RuntimeError("API down")
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY, ROBOT_CHAR_ONTOLOGY], "sci-fi")
    assert len(result) == 2, "Should return 2 fallback results"
    for scene in result:
        assert "scene_visual_tokens" in scene
        assert "t2i_prompt_json" in scene


@skip_if_unavailable
def test_compose_batch_preserves_original_scene_fields():
    """compose_scenes_batch must not remove original scene fields."""
    scenes = [SAMPLE_SCENE]
    mock_output = _make_llm_output_for_scenes(scenes)
    mock_resp = _make_mock_scene_composer_response(mock_output)
    with patch("app.services.scene_visual_composer._get_client") as mock_client:
        mock_client.return_value.chat.completions.create.return_value = mock_resp
        result = compose_scenes_batch(scenes, [HUMAN_CHAR_ONTOLOGY], "fiction")
    for field in ("title", "scene_type", "chunk_start_index", "chunk_end_index",
                  "narrative_summary", "scene_prompt_draft"):
        assert field in result[0], f"Field '{field}' was removed by compose_scenes_batch"
