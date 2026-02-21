"""
Scene Visual Composer — Phase 7 of the Visual Semantic Engine.

Builds structured visual tokens and T2I prompts for each scene in a single batched LLM call.
Respects anti_human_override for non-human characters: their character_tokens must not
default to human-portrait terms.
"""
import json
import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

SCENE_TOKEN_PROMPT = """\
You are building visual composition tokens and text-to-image (T2I) prompts for book illustration scenes.

LANGUAGE: All output must be in ENGLISH (scene_visual_tokens, t2i_prompt_json.abstract, .flux, .sd) — they are stored and used for image search and T2I APIs.

You will receive a JSON array of scenes, each with: title, visual_description, characters_present,
primary_location, scene_type, and character_ontologies (entity_class, anti_human_override, visual_markers).

For EACH scene, produce visual tokens and T2I prompts. Return a JSON array (same order as input):
[
  {
    "scene_id": <same as input scene_id>,
    "scene_visual_tokens": {
      "core_tokens": ["..."],        // 6 key visual elements of the scene
      "style_tokens": ["..."],       // 4 atmosphere/lighting/mood descriptors
      "composition_tokens": ["..."], // 3 camera angle / framing terms (e.g. "wide shot", "low angle", "close-up")
      "character_tokens": ["..."],   // visual markers from characters present (respect anti_human_override)
      "environment_tokens": ["..."]  // location-specific visual tokens
    },
    "t2i_prompt_json": {
      "abstract": "universal, model-agnostic prompt: 60-200 chars, contains visual keywords, style, composition",
      "flux": "FLUX-optimised: trigger words, emphasis syntax, weight hints",
      "sd": "SD-optimised: emphasis via (), negative prompt hint in --neg format"
    }
  }
]

CRITICAL RULES:
- composition_tokens MUST contain at least one camera/framing term: wide shot, close-up, medium shot,
  establishing shot, over-the-shoulder, low angle, bird's eye view, Dutch angle, tracking shot
- If any character has anti_human_override=true: character_tokens must reflect NON-HUMAN nature
  (use visual_markers and entity_class, NOT "person", "man", "woman", "portrait", "face", "human")
- abstract prompt must be >= 50 characters and visually specific (not a stub)
- t2i_prompt_json.abstract must describe: subject(s), environment, lighting, mood, composition
- Output order MUST match input order exactly
"""


def build_scene_visual_tokens(
    scene: dict,
    character_ontologies: list[dict],
    style_category: str,
) -> dict:
    """
    Build visual tokens for a single scene. Used internally by compose_scenes_batch().
    character_ontologies: list of {name, entity_class, anti_human_override, visual_markers, search_archetype}
    Returns: {"core_tokens": [...], "style_tokens": [...], "composition_tokens": [...],
              "character_tokens": [...], "environment_tokens": [...]}
    """
    # Collect relevant character ontologies for characters in this scene
    chars_present = set(n.lower() for n in (scene.get("characters_present") or []))
    relevant_ontologies = [
        o for o in character_ontologies
        if o.get("name", "").lower() in chars_present
    ]
    scene_input = {
        "scene_id": scene.get("_idx", 1),
        "title": scene.get("title", ""),
        "visual_description": scene.get("visual_description", ""),
        "characters_present": scene.get("characters_present", []),
        "primary_location": scene.get("primary_location", ""),
        "scene_type": scene.get("scene_type", "atmospheric"),
        "character_ontologies": relevant_ontologies,
        "style_category": style_category,
    }
    result = compose_scenes_batch([scene], character_ontologies, style_category)
    if result and result[0].get("scene_visual_tokens"):
        return result[0]["scene_visual_tokens"]
    return {}


def build_t2i_prompts(
    scene: dict,
    scene_visual_tokens: dict,
    style_category: str,
) -> dict:
    """
    Build T2I prompts from scene visual tokens.
    Returns {"abstract": "...", "flux": "...", "sd": "..."}
    """
    core = scene_visual_tokens.get("core_tokens", [])
    style = scene_visual_tokens.get("style_tokens", [])
    composition = scene_visual_tokens.get("composition_tokens", [])
    character = scene_visual_tokens.get("character_tokens", [])
    environment = scene_visual_tokens.get("environment_tokens", [])
    prompt_draft = scene.get("scene_prompt_draft", "")

    all_tokens = core + character + environment + style + composition
    token_str = ", ".join(t for t in all_tokens[:12] if t)

    abstract = prompt_draft or f"{token_str} — {style_category} illustration"
    if len(abstract) < 50 and token_str:
        abstract = f"{abstract}, {', '.join(style[:2])}"

    flux = f"{abstract}, high detail, 8k, cinematic"
    sd_neg = "blurry, low quality, watermark, text, duplicate, cropped"
    sd = f"({abstract}:1.2), masterpiece, best quality --neg {sd_neg}"

    return {"abstract": abstract[:400], "flux": flux[:400], "sd": sd[:400]}


def compose_scenes_batch(
    scenes: list[dict],
    character_ontologies: list[dict],
    style_category: str,
) -> list[dict]:
    """
    Single batched LLM call to build visual tokens and T2I prompts for all scenes.

    scenes: list of scene dicts (output of extract_scenes_llm)
    character_ontologies: list of {name, entity_class, anti_human_override, visual_markers, search_archetype}
    style_category: genre string (e.g. "sci-fi", "fantasy", "fiction")

    Adds to each scene dict: "scene_visual_tokens" and "t2i_prompt_json".
    Returns updated scenes list (same order).
    """
    if not scenes:
        return []

    client = _get_client()

    # Build input for LLM — include relevant character ontologies per scene
    scene_inputs: list[dict] = []
    for i, scene in enumerate(scenes):
        chars_present = set(n.lower() for n in (scene.get("characters_present") or []))
        relevant_ontologies = [
            {
                "name": o.get("name", ""),
                "entity_class": o.get("entity_class", "human"),
                "anti_human_override": o.get("anti_human_override", False),
                "visual_markers": (o.get("visual_markers") or [])[:4],
                "search_archetype": o.get("search_archetype"),
            }
            for o in character_ontologies
            if o.get("name", "").lower() in chars_present
        ]
        scene_inputs.append({
            "scene_id": i + 1,
            "title": scene.get("title", ""),
            "visual_description": (scene.get("visual_description") or "")[:500],
            "scene_prompt_draft": (scene.get("scene_prompt_draft") or "")[:300],
            "characters_present": scene.get("characters_present", []),
            "primary_location": scene.get("primary_location", ""),
            "scene_type": scene.get("scene_type", "atmospheric"),
            "character_ontologies": relevant_ontologies,
            "style_category": style_category,
        })

    user_content = json.dumps(scene_inputs, ensure_ascii=False)
    logger.info("[scene_composer] compose_scenes_batch: %d scenes", len(scenes))

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SCENE_TOKEN_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=6000,
        )
        raw = response.choices[0].message.content.strip()
        usage = response.usage
        logger.info(
            "[scene_composer] tokens: prompt=%s completion=%s total=%s",
            usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    except Exception as e:
        logger.error("[scene_composer] LLM call failed: %s", e)
        return _apply_scene_fallbacks(scenes, character_ontologies, style_category)

    # Strip markdown code fences
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        results = json.loads(raw)
        if not isinstance(results, list):
            raise ValueError("Expected JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[scene_composer] Failed to parse response: %s | raw: %s", e, raw[:500])
        return _apply_scene_fallbacks(scenes, character_ontologies, style_category)

    # Merge results back into scenes
    result_by_id = {r.get("scene_id"): r for r in results if isinstance(r, dict)}

    updated_scenes: list[dict] = []
    for i, scene in enumerate(scenes):
        scene_copy = dict(scene)
        result = result_by_id.get(i + 1, {})

        svt = result.get("scene_visual_tokens", {})
        t2i = result.get("t2i_prompt_json", {})

        # Validate composition_tokens — must have at least one framing term
        FRAMING_TERMS = {
            "wide shot", "close-up", "medium shot", "establishing shot",
            "over-the-shoulder", "low angle", "bird's eye view", "dutch angle",
            "tracking shot", "wide angle", "panoramic"
        }
        comp_tokens = svt.get("composition_tokens", [])
        if not any(t.lower() in FRAMING_TERMS for t in comp_tokens):
            comp_tokens = ["wide shot"] + comp_tokens
        svt["composition_tokens"] = comp_tokens[:3]

        # Validate abstract T2I prompt length
        abstract = t2i.get("abstract", "")
        if not abstract or len(abstract) < 50:
            fallback = _build_fallback_t2i(scene_copy, svt, style_category)
            t2i = fallback if not abstract or len(abstract) < 50 else t2i

        scene_copy["scene_visual_tokens"] = svt
        scene_copy["t2i_prompt_json"] = t2i
        updated_scenes.append(scene_copy)

    # Pad if LLM returned fewer results
    while len(updated_scenes) < len(scenes):
        idx = len(updated_scenes)
        scene_copy = dict(scenes[idx])
        svt = _build_fallback_svt(scenes[idx], character_ontologies, style_category)
        t2i = _build_fallback_t2i(scenes[idx], svt, style_category)
        scene_copy["scene_visual_tokens"] = svt
        scene_copy["t2i_prompt_json"] = t2i
        updated_scenes.append(scene_copy)

    return updated_scenes


def _build_fallback_svt(scene: dict, character_ontologies: list[dict], style_category: str) -> dict:
    """Build fallback scene_visual_tokens when LLM fails."""
    chars_present = set(n.lower() for n in (scene.get("characters_present") or []))
    char_tokens: list[str] = []
    for o in character_ontologies:
        if o.get("name", "").lower() not in chars_present:
            continue
        if o.get("anti_human_override"):
            char_tokens.extend((o.get("visual_markers") or [])[:2])
        else:
            char_tokens.extend((o.get("visual_markers") or [])[:2])

    return {
        "core_tokens": [scene.get("scene_type", "scene"), style_category, "dramatic", "detailed", "cinematic", "high contrast"],
        "style_tokens": ["cinematic lighting", "dramatic atmosphere", "high detail", "moody"],
        "composition_tokens": ["wide shot", "establishing shot", "medium shot"],
        "character_tokens": char_tokens[:4] or ["figure", "silhouette"],
        "environment_tokens": [scene.get("primary_location", "environment"), "atmospheric", "detailed"],
    }


def _build_fallback_t2i(scene: dict, svt: dict, style_category: str) -> dict:
    """Build fallback T2I prompts from scene data."""
    title = scene.get("title", "")
    scene_type = scene.get("scene_type", "atmospheric")
    location = scene.get("primary_location", "")
    prompt_draft = scene.get("scene_prompt_draft", "")
    core = svt.get("core_tokens", [])
    comp = svt.get("composition_tokens", ["wide shot"])

    if prompt_draft and len(prompt_draft) >= 50:
        abstract = prompt_draft[:300]
    else:
        parts = [title, f"{scene_type} scene"]
        if location:
            parts.append(f"in {location}")
        if core:
            parts.append(", ".join(core[:4]))
        if comp:
            parts.append(comp[0])
        parts.append(style_category)
        abstract = ", ".join(p for p in parts if p)

    flux = f"{abstract}, high detail, 8k, dramatic lighting"
    sd = f"({abstract}:1.2), masterpiece, best quality --neg blurry, low quality, watermark"

    return {"abstract": abstract[:400], "flux": flux[:400], "sd": sd[:400]}


def _apply_scene_fallbacks(
    scenes: list[dict],
    character_ontologies: list[dict],
    style_category: str,
) -> list[dict]:
    """Apply fallback visual tokens and T2I prompts to all scenes."""
    updated = []
    for scene in scenes:
        scene_copy = dict(scene)
        svt = _build_fallback_svt(scene, character_ontologies, style_category)
        t2i = _build_fallback_t2i(scene, svt, style_category)
        scene_copy["scene_visual_tokens"] = svt
        scene_copy["t2i_prompt_json"] = t2i
        updated.append(scene_copy)
    return updated
