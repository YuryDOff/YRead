"""
Ontology Classifier Service — Phase 1 of the Visual Semantic Engine.

Classifies all entities (characters + locations) in a single batched LLM call,
assigning entity_class from the closed 30+ class taxonomy, plus materiality,
power_status, embodiment, visual_markers, anti_human_override, and search_archetype.
"""
import json
import logging
import os
from typing import Optional

from openai import OpenAI

from app.services.ontology_constants import ENTITY_CLASSES, NON_HUMAN_CLASSES

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

ONTOLOGY_PROMPT = f"""
You are classifying fictional entities for visual image search.

For each entity, select entity_class from EXACTLY this list:
{", ".join(ENTITY_CLASSES)}

Return ONLY valid JSON array, one object per entity:
[
  {{
    "name": "entity name",
    "entity_class": "<one value from the list above>",
    "materiality": "organic|mechanical|holographic|energy-based|hybrid|immaterial",
    "power_status": "dominant|subordinate|assistant|childlike|corrupted|neutral",
    "embodiment": "physical|digital_avatar|disembodied|amorphous",
    "visual_markers": ["3 to 6 concrete visual markers"],
    "anti_human_override": true or false,
    "search_archetype": "short visual archetype phrase for non-human, or null"
  }}
]

RULES:
- All output must be in ENGLISH: visual_markers and search_archetype are used for image search and text-to-image APIs.
- anti_human_override = true for all classes EXCEPT:
  human, human_supernatural, human_transformed, human_enhanced, clone, human_hybrid, demigod
- search_archetype is required (non-null) when anti_human_override = true
- visual_markers must be concrete and visual, not abstract (e.g. "glowing red eyes", not "menacing")
- visual_markers must have exactly 3 to 6 items
- Choose the most specific class available
- Output order MUST match input order exactly
- Locations that are places/settings: use entity_class "construct" for built structures,
  or keep as the most relevant class; set anti_human_override = false for locations
"""


def classify_entities_batch(entities: list[dict]) -> list[dict]:
    """
    Single LLM call for all entities (characters + locations).

    Input:  [{"name": ..., "description": ..., "visual_type": ...}]
    Output: [{"name": ..., "entity_class": ..., "materiality": ..., ...}]

    Output order matches input order. Falls back gracefully on parse errors.
    """
    if not entities:
        return []

    client = _get_client()

    user_content = json.dumps(entities, ensure_ascii=False)

    logger.info("[ontology] classify_entities_batch: %d entities", len(entities))

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ONTOLOGY_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
        usage = response.usage
        logger.info(
            "[ontology] tokens: prompt=%s completion=%s total=%s",
            usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    except Exception as e:
        logger.error("[ontology] LLM call failed: %s", e)
        return _build_fallback_results(entities)

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        results = json.loads(raw)
        if not isinstance(results, list):
            raise ValueError("Expected JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[ontology] Failed to parse response: %s | raw: %s", e, raw[:500])
        return _build_fallback_results(entities)

    # Validate and normalise each result
    validated = []
    for i, item in enumerate(results):
        if not isinstance(item, dict):
            validated.append(_fallback_for_entity(entities[i] if i < len(entities) else {}))
            continue

        entity_class = item.get("entity_class", "human")
        if entity_class not in ENTITY_CLASSES:
            logger.warning("[ontology] Unknown entity_class '%s', defaulting to 'human'", entity_class)
            entity_class = "human"
            item["entity_class"] = entity_class

        # Enforce anti_human_override logic
        expected_override = entity_class in NON_HUMAN_CLASSES
        item["anti_human_override"] = expected_override

        # Ensure search_archetype present when override=True
        if expected_override and not item.get("search_archetype"):
            item["search_archetype"] = entity_class.replace("_", " ")

        # Ensure visual_markers count is 3-6
        markers = item.get("visual_markers", [])
        if not isinstance(markers, list):
            markers = []
        if len(markers) < 3:
            markers.extend(["detailed", "high contrast", "dramatic lighting"][: 3 - len(markers)])
        item["visual_markers"] = markers[:6]

        validated.append(item)

    # If LLM returned fewer items than entities (truncated), pad with fallbacks
    while len(validated) < len(entities):
        idx = len(validated)
        validated.append(_fallback_for_entity(entities[idx] if idx < len(entities) else {}))

    return validated[:len(entities)]


def _fallback_for_entity(entity: dict) -> dict:
    """Return a safe default ontology dict for an entity when LLM fails."""
    visual_type = (entity.get("visual_type") or "").lower()
    if visual_type in ("ai", "robot", "android", "alien", "creature"):
        entity_class = "robot" if visual_type in ("ai", "robot", "android") else "alien"
        anti_override = True
    else:
        entity_class = "human"
        anti_override = False

    return {
        "name": entity.get("name", ""),
        "entity_class": entity_class,
        "materiality": "organic" if not anti_override else "mechanical",
        "power_status": "neutral",
        "embodiment": "physical",
        "visual_markers": ["detailed figure", "dramatic lighting", "high contrast"],
        "anti_human_override": anti_override,
        "search_archetype": entity_class.replace("_", " ") if anti_override else None,
    }


def _build_fallback_results(entities: list[dict]) -> list[dict]:
    return [_fallback_for_entity(e) for e in entities]
