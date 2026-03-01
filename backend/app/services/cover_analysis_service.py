"""
Cover Analysis Service — Phase 4.
Two-stage synthesis: thematic extraction then cover brief. Stateless; no DB.
Same lazy _client pattern as ai_service.
"""
import json
import logging
import os
from typing import Callable, Optional

try:
    import tiktoken
except ImportError:
    tiktoken = None  # type: ignore[assignment]

from openai import OpenAI

logger = logging.getLogger(__name__)

_client: Optional[OpenAI] = None

# Target max tokens for full-text summary (Stage 1 input)
COVER_SUMMARY_MAX_TOKENS = 12_000


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

GENRE_COVER_CONVENTIONS = {
    "fantasy": "Character-forward or world-building landscape; rich colour; ornate typography",
    "sci_fi": "Technological or cosmic imagery; cool palette; geometric or sans-serif type",
    "thriller": "Dark, high-contrast; single symbolic object or silhouette; bold sans type",
    "literary_fiction": "Abstract or atmospheric; muted palette; elegant serif",
    "romance": "Warm tones; intimate imagery; script typography",
    "mystery": "Single enigmatic object; shadow and light; restrained palette",
    "childrens": "Character-forward; bright palette; playful rounded typography",
    "historical_fiction": "Period-accurate imagery; aged textures; serif typography",
}


def _get_encoder():
    if tiktoken is None:
        return None
    try:
        return tiktoken.encoding_for_model("gpt-3.5-turbo")
    except Exception:
        return None


def _get_full_text_summary(chunk_analyses: list[dict]) -> str:
    """
    Build a summary suitable for full-book thematic reading.
    Uses narrative_summary or visual_moment per chunk. Cap at ~12,000 tokens.
    If over limit, sample every Nth summary.
    """
    parts = []
    for c in chunk_analyses:
        text = c.get("narrative_summary") or c.get("visual_moment") or ""
        if isinstance(text, str) and text.strip():
            parts.append(text.strip())

    if not parts:
        return ""

    concatenated = "\n\n".join(parts)
    enc = _get_encoder()
    if enc is None:
        if len(concatenated) > 45000:
            return "\n\n".join(parts[:: max(1, len(parts) // 50)])
        return concatenated

    tokens = enc.encode(concatenated)
    if len(tokens) <= COVER_SUMMARY_MAX_TOKENS:
        return concatenated

    # Over limit: sample every Nth part to get under cap
    step = max(1, (len(parts) * COVER_SUMMARY_MAX_TOKENS) // len(tokens))
    sampled = parts[::step]
    while sampled and len(enc.encode("\n\n".join(sampled))) > COVER_SUMMARY_MAX_TOKENS:
        step += 1
        sampled = parts[::step]
    return "\n\n".join(sampled) if sampled else "\n\n".join(parts[:1])


COVER_THEMATIC_EXTRACTION_PROMPT = """You are analyzing a work of fiction to extract thematic material for cover design.

From the provided text (chunk summaries from the manuscript), identify:

1. dominant_motifs — list of 4–8 key recurring motifs (objects, natural elements, concepts)
2. symbolic_anchors — 1–2 central symbolic images that could anchor the cover
3. emotional_arc — one paragraph on the central emotional journey
4. recurring_imagery — list of 4–8 recurring visual images
5. central_tension — the central tension in one sentence
6. tone_words — list of 5–10 mood/tone words

Return ONLY valid JSON with these exact keys (all arrays of strings except emotional_arc and central_tension which are strings)."""


COVER_BRIEF_SYNTHESIS_PROMPT = """You are synthesizing a cover design brief from thematic material.

Given thematic extraction and genre conventions, produce a structured cover brief.

Return ONLY valid JSON with these exact keys:
- thematic_statement (string)
- emotional_promise (string)
- dominant_motifs (array of strings)
- symbolic_anchors (array of strings)
- cover_mood_keywords (array of 5–8 strings)
- genre_conventions (string)
- genre_subversion_opportunity (string)
- typography_direction (string)
- color_palette_direction (string)
- cover_t2i_prompt (string: full text-to-image prompt for cover)
- cover_negative_prompt (string: what to avoid)
- cover_role_character_ids_hints (array of character names suggested for cover)
- cover_role_location_ids_hints (array of location names suggested for cover)
- cover_role_artefact_ids_hints (array of artefact names suggested for cover)
- cover_type (string: one of "object_centered"|"character_centered"|"setting_centered"|"abstract"|"typography_centered". Apply: if symbolic_anchors non-empty → "object_centered"; if genre is fantasy/romance/ya and dominant protagonist → "character_centered"; if genre is literary_fiction/thriller/mystery → "abstract"; if genre is non_fiction/biography → "typography_centered"; otherwise → "setting_centered".)
- color_palette_structured (object with keys: dominant (string), accent (string), temperature ("warm"|"cool"|"neutral"), contrast ("high"|"mid"|"low"), saturation ("saturated"|"desaturated"|"monochrome"|"mixed"))
- cover_role_primary_hint (string: the ONE entity name—character, location, OR artefact—most suited as the primary focal element of the cover; not a list)

Use the provided genre conventions. Character/location/artefact hints are names only; caller will resolve to ids."""


def extract_thematic_material(
    chunk_analyses: list[dict],
    genre: str,
    run_id: Optional[str] = None,
) -> dict:
    """
    Stage 1 LLM call.
    Returns {
        dominant_motifs, symbolic_anchors, emotional_arc, recurring_imagery,
        central_tension, tone_words
    }
    """
    summary = _get_full_text_summary(chunk_analyses)
    if not summary.strip():
        return {
            "dominant_motifs": [],
            "symbolic_anchors": [],
            "emotional_arc": "",
            "recurring_imagery": [],
            "central_tension": "",
            "tone_words": [],
        }

    client = _get_client()
    user_content = f"Genre: {genre}\n\nText:\n{summary[:120000]}"

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COVER_THEMATIC_EXTRACTION_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[cover_analysis] Stage 1 LLM failed: %s", e)
        return {
            "dominant_motifs": [],
            "symbolic_anchors": [],
            "emotional_arc": "",
            "recurring_imagery": [],
            "central_tension": "",
            "tone_words": [],
        }

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[cover_analysis] Stage 1 parse failed: %s", e)
        return {
            "dominant_motifs": [],
            "symbolic_anchors": [],
            "emotional_arc": "",
            "recurring_imagery": [],
            "central_tension": "",
            "tone_words": [],
        }

    return {
        "dominant_motifs": data.get("dominant_motifs", []) if isinstance(data.get("dominant_motifs"), list) else [],
        "symbolic_anchors": data.get("symbolic_anchors", []) if isinstance(data.get("symbolic_anchors"), list) else [],
        "emotional_arc": str(data.get("emotional_arc", "")),
        "recurring_imagery": data.get("recurring_imagery", []) if isinstance(data.get("recurring_imagery"), list) else [],
        "central_tension": str(data.get("central_tension", "")),
        "tone_words": data.get("tone_words", []) if isinstance(data.get("tone_words"), list) else [],
    }


def synthesise_cover_brief(
    thematic_material: dict,
    genre: str,
    style_category: str,
    existing_characters: list[dict],
    existing_locations: list[dict],
    run_id: Optional[str] = None,
) -> dict:
    """
    Stage 2 LLM call.
    Returns full cover_analysis dict matching CoverAnalysis model fields, with
    cover_role_*_ids_hints as names (caller resolves to ids).
    """
    conventions = GENRE_COVER_CONVENTIONS.get(genre, "Atmospheric; clear typography; genre-appropriate imagery.")
    user_content = json.dumps({
        "thematic_material": thematic_material,
        "genre": genre,
        "style_category": style_category,
        "genre_conventions_hint": conventions,
        "existing_characters": [{"name": c.get("name"), "is_main": c.get("is_main"), "cover_role_candidate": c.get("cover_role")} for c in existing_characters],
        "existing_locations": [{"name": l.get("name"), "is_main": l.get("is_main"), "cover_role_candidate": l.get("cover_role")} for l in existing_locations],
    }, ensure_ascii=False)

    client = _get_client()
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": COVER_BRIEF_SYNTHESIS_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=2048,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[cover_analysis] Stage 2 LLM failed: %s", e)
        return _default_cover_brief(thematic_material, genre)

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("Expected JSON object")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[cover_analysis] Stage 2 parse failed: %s", e)
        return _default_cover_brief(thematic_material, genre)

    color_structured = data.get("color_palette_structured")
    if not isinstance(color_structured, dict):
        color_structured = None
    return {
        "thematic_statement": str(data.get("thematic_statement", "")),
        "emotional_promise": str(data.get("emotional_promise", "")),
        "dominant_motifs": data.get("dominant_motifs", []),
        "symbolic_anchors": data.get("symbolic_anchors", []),
        "cover_mood_keywords": data.get("cover_mood_keywords", []),
        "genre_conventions": str(data.get("genre_conventions", "")),
        "genre_subversion_opportunity": str(data.get("genre_subversion_opportunity", "")),
        "typography_direction": str(data.get("typography_direction", "")),
        "color_palette_direction": str(data.get("color_palette_direction", "")),
        "cover_t2i_prompt": str(data.get("cover_t2i_prompt", "")),
        "cover_negative_prompt": str(data.get("cover_negative_prompt", "")),
        "cover_role_character_ids_hints": data.get("cover_role_character_ids_hints", []) if isinstance(data.get("cover_role_character_ids_hints"), list) else [],
        "cover_role_location_ids_hints": data.get("cover_role_location_ids_hints", []) if isinstance(data.get("cover_role_location_ids_hints"), list) else [],
        "cover_role_artefact_ids_hints": data.get("cover_role_artefact_ids_hints", []) if isinstance(data.get("cover_role_artefact_ids_hints"), list) else [],
        "cover_type": str(data.get("cover_type", "")).strip() or None,
        "color_palette_structured": color_structured,
        "cover_role_primary_hint": str(data.get("cover_role_primary_hint", "")).strip() or None,
    }


def _default_cover_brief(thematic_material: dict, genre: str) -> dict:
    return {
        "thematic_statement": thematic_material.get("central_tension", ""),
        "emotional_promise": thematic_material.get("emotional_arc", ""),
        "dominant_motifs": thematic_material.get("dominant_motifs", []),
        "symbolic_anchors": thematic_material.get("symbolic_anchors", []),
        "cover_mood_keywords": thematic_material.get("tone_words", [])[:8],
        "genre_conventions": GENRE_COVER_CONVENTIONS.get(genre, ""),
        "genre_subversion_opportunity": "",
        "typography_direction": "Clear, genre-appropriate",
        "color_palette_direction": "Atmospheric",
        "cover_t2i_prompt": "",
        "cover_negative_prompt": "",
        "cover_role_character_ids_hints": [],
        "cover_role_location_ids_hints": [],
        "cover_role_artefact_ids_hints": [],
        "cover_type": "setting_centered",
        "color_palette_structured": None,
        "cover_role_primary_hint": None,
    }


def run_cover_analysis(
    chunk_analyses: list[dict],
    genre: str,
    style_category: str,
    existing_characters: list[dict],
    existing_locations: list[dict],
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    run_id: Optional[str] = None,
) -> dict:
    """
    Orchestrates Stage 1 → Stage 2.
    Returns the cover_analysis dict ready for crud.create_or_update_cover_analysis.
    """
    if progress_callback:
        progress_callback("cover", 0, 2)
    thematic = extract_thematic_material(chunk_analyses, genre, run_id=run_id)
    if progress_callback:
        progress_callback("cover", 1, 2)
    brief = synthesise_cover_brief(
        thematic, genre, style_category,
        existing_characters, existing_locations,
        run_id=run_id,
    )
    return brief
