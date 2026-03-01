"""
Artefact Analysis Service — Phase 3.
Extracts artefacts from chunk analyses, classifies via ontology, builds visual tokens.
Stateless; no DB access. Same structural patterns as ai_service (lazy _client, prompt constants).
"""
import json
import logging
import os
from typing import Callable, Optional

from openai import OpenAI

from app.services import ontology_service

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

# Top N chunk analyses by dramatic_score to keep token count bounded
ARTEFACT_SAMPLE_SIZE = 30

ARTEFACT_EXTRACTION_PROMPT = """You are extracting narrative artefacts from fiction for visual reference.

An artefact is an object that a character *acts upon or with* toward their goals.

RULES (apply strictly):
1. An artefact must be something a character uses, wields, seeks, or interacts with for a purpose — not background furniture.
2. Include only if the object appears in at least 2 chunks OR is described with unusual visual detail.
3. The object must have narrative weight (plot or symbolism). Exclude generic set-dressing.
4. A location is where a scene is set; an artefact is what a character uses. If ambiguous, classify as location, not artefact.
5. Return ONLY a valid JSON array of artefacts.

For each artefact return an object with these exact keys:
- name (string)
- physical_description (string)
- symbolic_role (string, brief)
- narrative_function (one of: "Tool", "MacGuffin", "Symbol", "Weapon", "Token", "Other")
- typical_contexts (string, e.g. "Used by [character] in [scene type] contexts")
- is_main (boolean: true if appears 3+ times or has strong symbolic role)
- chunks_present (array of chunk_index integers)
- scenes_present (array of short scene title hints, or empty)
- visual_type (one of: "physical_object", "magical_item", "document", "vehicle", "other")

Output MUST be a JSON array only. No markdown. Same order as input chunks where applicable."""


def extract_artefacts_from_chunks(
    chunk_analyses: list[dict],
    chunk_text_map: dict[int, str],
    manuscript_lang: str = "en",
    run_id: Optional[str] = None,
) -> list[dict]:
    """
    Single OpenAI call over a representative sample of chunk_analyses
    (top 30 by dramatic_score to keep token count bounded).

    Input chunk_analyses format: same as ai_service output (characters_present,
    locations_present, visual_moment, dramatic_score, etc.).

    Returns list of dicts with: name, physical_description, symbolic_role,
    narrative_function, typical_contexts, is_main, chunks_present, scenes_present, visual_type.
    """
    if not chunk_analyses:
        return []

    # Sample top by dramatic_score
    with_score = [
        (c.get("dramatic_score", 0.0) or 0.0, c)
        for c in chunk_analyses
    ]
    with_score.sort(key=lambda x: x[0], reverse=True)
    sample = [c for _, c in with_score[:ARTEFACT_SAMPLE_SIZE]]

    client = _get_client()
    user_content = json.dumps({"chunk_analyses": sample, "chunk_text_map": chunk_text_map}, ensure_ascii=False)

    logger.info("[artefact] extract_artefacts_from_chunks: %d sampled from %d", len(sample), len(chunk_analyses))

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ARTEFACT_EXTRACTION_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[artefact] LLM call failed: %s", e)
        return []

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        results = json.loads(raw)
        if not isinstance(results, list):
            return []
    except json.JSONDecodeError as e:
        logger.error("[artefact] Failed to parse response: %s | raw: %s", e, raw[:500])
        return []

    out = []
    for item in results:
        if not isinstance(item, dict):
            continue
        out.append({
            "name": item.get("name", ""),
            "physical_description": item.get("physical_description", ""),
            "symbolic_role": item.get("symbolic_role", ""),
            "narrative_function": item.get("narrative_function", "Other"),
            "typical_contexts": item.get("typical_contexts", ""),
            "is_main": bool(item.get("is_main", False)),
            "chunks_present": item.get("chunks_present", []) if isinstance(item.get("chunks_present"), list) else [],
            "scenes_present": item.get("scenes_present", []) if isinstance(item.get("scenes_present"), list) else [],
            "visual_type": item.get("visual_type", "other"),
        })
    return out


ARTEFACT_VISUAL_TOKEN_PROMPT = """You are generating structured visual search tokens for narrative artefacts (objects, items, vehicles).

LANGUAGE: All output must be in ENGLISH — used for image search and text-to-image APIs.

You will receive a JSON array of artefacts with: name, physical_description, symbolic_role, visual_type, entity_class (from ontology).

For each artefact produce visual tokens. Return a JSON array (same order as input):
[
  {
    "name": "artefact name",
    "core_tokens": ["token1", ...],
    "style_tokens": ["token1", ...],
    "archetype_tokens": ["token1", ...],
    "anti_tokens": ["token1", ...]
  }
]

Rules:
- core_tokens: exactly 6 main visual characteristics (shape, material, colour, size, condition)
- style_tokens: exactly 4 atmosphere/lighting/context descriptors
- archetype_tokens: exactly 3 archetype phrases for search (e.g. "medieval sword", "fantasy weapon")
- anti_tokens: 2-3 terms to EXCLUDE (e.g. "person", "portrait") or empty list
- Focus on the object, not people or places. Output order MUST match input order exactly."""


def build_artefact_visual_tokens_batch(artefacts: list[dict]) -> list[dict]:
    """
    Same pattern as ai_service.build_entity_visual_tokens_batch but with
    artefact-specific prompt for objects (not people/places).

    Input: [{name, physical_description, symbolic_role, visual_type, entity_class?, ...}]
    Output same order: [{name, core_tokens, style_tokens, archetype_tokens, anti_tokens}]
    """
    if not artefacts:
        return []

    client = _get_client()
    user_content = json.dumps(artefacts, ensure_ascii=False)

    logger.info("[artefact] build_artefact_visual_tokens_batch: %d artefacts", len(artefacts))

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ARTEFACT_VISUAL_TOKEN_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[artefact] LLM call failed: %s", e)
        return _artefact_token_fallbacks(artefacts)

    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        results = json.loads(raw)
        if not isinstance(results, list):
            return _artefact_token_fallbacks(artefacts)
    except json.JSONDecodeError:
        return _artefact_token_fallbacks(artefacts)

    validated = []
    for i, item in enumerate(results):
        if not isinstance(item, dict):
            validated.append(_artefact_token_fallback(artefacts[i] if i < len(artefacts) else {}))
            continue
        validated.append({
            "name": item.get("name", artefacts[i].get("name", "") if i < len(artefacts) else ""),
            "core_tokens": (item.get("core_tokens") or [])[:6],
            "style_tokens": (item.get("style_tokens") or [])[:4],
            "archetype_tokens": (item.get("archetype_tokens") or [])[:3],
            "anti_tokens": (item.get("anti_tokens") or [])[:3],
        })

    while len(validated) < len(artefacts):
        idx = len(validated)
        validated.append(_artefact_token_fallback(artefacts[idx] if idx < len(artefacts) else {}))

    return validated[: len(artefacts)]


def _artefact_token_fallback(artefact: dict) -> dict:
    return {
        "name": artefact.get("name", ""),
        "core_tokens": ["object", "detailed", "high contrast", "dramatic lighting", "textured", "clear"],
        "style_tokens": ["atmospheric", "moody", "cinematic", "focused"],
        "archetype_tokens": [],
        "anti_tokens": [],
    }


def _artefact_token_fallbacks(artefacts: list[dict]) -> list[dict]:
    return [_artefact_token_fallback(a) for a in artefacts]


def run_artefact_analysis(
    chunks: list[dict],
    chunk_text_map: dict[int, str],
    manuscript_lang: str = "en",
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    run_id: Optional[str] = None,
) -> dict:
    """
    Full artefact pipeline:
    1. extract_artefacts_from_chunks (chunk_analyses from chunks or caller passes chunk_analyses)
    2. ontology_service.classify_entities_batch with entity_role="artefact"
    3. build_artefact_visual_tokens_batch

    chunks: list of chunk dicts; must include or be convertible to chunk_analyses format
    (chunk_index, dramatic_score, characters_present, locations_present, visual_moment, etc.).

    Returns: { artefacts: list[dict] } with merged ontology and visual tokens.
    """
    chunk_analyses = chunks
    if not chunk_analyses:
        return {"artefacts": []}

    if progress_callback:
        progress_callback("artefacts", 0, 3)

    artefacts = extract_artefacts_from_chunks(
        chunk_analyses, chunk_text_map, manuscript_lang=manuscript_lang, run_id=run_id
    )

    if progress_callback:
        progress_callback("artefacts", 1, 3)

    if not artefacts:
        return {"artefacts": []}

    ontology_input = [
        {
            "name": a["name"],
            "description": a.get("physical_description", "") or a.get("symbolic_role", ""),
            "visual_type": a.get("visual_type", "other"),
            "entity_role": "artefact",
        }
        for a in artefacts
    ]
    ontology_results = ontology_service.classify_entities_batch(ontology_input, entity_role="artefact")

    for i, art in enumerate(artefacts):
        if i < len(ontology_results):
            o = ontology_results[i]
            art["entity_class"] = o.get("entity_class", "other_artefact")
            art["materiality"] = o.get("materiality", "organic")
            art["power_status"] = o.get("power_status", "neutral")
            art["embodiment"] = o.get("embodiment", "physical")
            art["visual_markers"] = o.get("visual_markers", [])[:6]
            art["anti_human_override"] = o.get("anti_human_override", False)
            art["search_archetype"] = o.get("search_archetype")

    if progress_callback:
        progress_callback("artefacts", 2, 3)

    token_results = build_artefact_visual_tokens_batch(artefacts)

    for i, art in enumerate(artefacts):
        if i < len(token_results):
            t = token_results[i]
            art["core_tokens"] = t.get("core_tokens", [])
            art["style_tokens"] = t.get("style_tokens", [])
            art["archetype_tokens"] = t.get("archetype_tokens", [])
            art["anti_tokens"] = t.get("anti_tokens", [])

    return {"artefacts": artefacts}
