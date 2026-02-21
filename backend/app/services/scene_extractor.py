"""
Scene Extractor — Phase 6 of the Visual Semantic Engine.

Extracts narrative scenes from chunk analyses using a two-pass approach:
  Pass A: Deterministic sliding window (no LLM) — ranks candidate windows by composite score.
  Pass B: LLM refinement — selects and refines exactly scene_count scenes from candidates.
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

SCENE_EXTRACTION_PROMPT = """\
Given N candidate scene windows from a novel, select and refine exactly {scene_count} scenes.

LANGUAGE RULES (mandatory):
- The following fields are stored and used for image search and text-to-image APIs — write them ONLY in ENGLISH: title, narrative_summary, visual_description, scene_prompt_draft.
- If the manuscript is not in English (manuscript_lang is not "en"), also provide "title_display" and "narrative_summary_display" in the manuscript language, for user-facing display (same language as the source text). Omit title_display and narrative_summary_display when manuscript_lang is "en".

Prioritise scenes with:
- High dramatic tension or emotional peak
- Clear visual composition potential
- 2 or more entities present
- State change, conflict, revelation, or turning point
- Strong environmental context
- Good spread across different parts of the book (avoid clustering)

For each selected scene return:
{
  "scene_id": 1,
  "title": "5-7 word evocative title IN ENGLISH",
  "title_display": "optional: same title in manuscript language (omit if manuscript is English)",
  "scene_type": "climax|conflict|turning_point|revelation|emotional_peak|action|atmospheric",
  "chunk_start_index": 0,
  "chunk_end_index": 4,
  "narrative_summary": "2-3 sentences IN ENGLISH: what happens and why it matters",
  "narrative_summary_display": "optional: same summary in manuscript language (omit if manuscript is English)",
  "visual_description": "detailed description IN ENGLISH of the KEY VISUAL MOMENT for illustration: foreground, background, character positions, lighting, mood",
  "characters_present": ["name1", "name2"],
  "primary_location": "location name",
  "visual_intensity": 0.0,
  "illustration_priority": "high|medium|low",
  "scene_prompt_draft": "text-to-image ready prompt IN ENGLISH: visual style, character appearance, environment, lighting, composition"
}

Return ONLY valid JSON: {"scenes": [...]}
"""

# ---------------------------------------------------------------------------
# Visual density numeric mapping
# ---------------------------------------------------------------------------

_DENSITY_NUMERIC = {"low": 0.2, "medium": 0.6, "high": 1.0}

HIGH_DRAMA_POSITIONS = {"climax", "midpoint", "inciting_incident"}


def _density_numeric(density: str) -> float:
    return _DENSITY_NUMERIC.get(density.lower() if density else "low", 0.2)


# ---------------------------------------------------------------------------
# Pass A: Sliding window (deterministic, no LLM)
# ---------------------------------------------------------------------------


def group_chunks_into_candidate_scenes(
    chunk_analyses: list[dict],
    scene_count: int,
    window_size: int = 5,
    step: int = 2,
) -> list[dict]:
    """
    Deterministic sliding window over chunk_analyses.

    composite_score = avg(dramatic_score) * 0.5
                    + avg(visual_density_numeric) * 0.3
                    + entity_presence_bonus * 0.2

    entity_presence_bonus = min(1.0, unique_entities / 3)
    visual_density_numeric: low=0.2, medium=0.6, high=1.0

    Inclusion criteria (at least 2 of):
    - avg dramatic_score >= 0.6
    - visual_density == "high" in >= 2 chunks
    - unique characters_present >= 2
    - narrative_position in ("climax", "midpoint", "inciting_incident")

    Non-maximum suppression: overlapping windows (> 50%) → keep higher score only.
    Returns top (scene_count * 1.2) candidates (rounded up) for LLM refinement.
    """
    n = len(chunk_analyses)
    if n == 0:
        return []

    # Build a quick index by chunk_index (some may be missing or out-of-order)
    indexed = {ca.get("chunk_index", i): ca for i, ca in enumerate(chunk_analyses)}
    sorted_indices = sorted(indexed.keys())

    candidates: list[dict] = []

    for start_pos in range(0, len(sorted_indices), step):
        end_pos = min(start_pos + window_size - 1, len(sorted_indices) - 1)
        window_idx = sorted_indices[start_pos: end_pos + 1]
        window_chunks = [indexed[i] for i in window_idx]
        if not window_chunks:
            continue

        dramatic_scores = [float(c.get("dramatic_score", 0.0)) for c in window_chunks]
        densities = [_density_numeric(c.get("visual_density", "low")) for c in window_chunks]

        avg_dramatic = sum(dramatic_scores) / len(dramatic_scores)
        avg_density = sum(densities) / len(densities)

        unique_entities: set[str] = set()
        for c in window_chunks:
            unique_entities.update(c.get("characters_present", []))
            unique_entities.update(c.get("locations_present", []))
        entity_bonus = min(1.0, len(unique_entities) / 3)

        composite_score = avg_dramatic * 0.5 + avg_density * 0.3 + entity_bonus * 0.2

        # Inclusion criteria: at least 2 of 4 must be met
        crit_dramatic = avg_dramatic >= 0.6
        crit_density = sum(1 for c in window_chunks if c.get("visual_density") == "high") >= 2
        crit_entities = sum(len(c.get("characters_present", [])) for c in window_chunks) >= 2
        crit_position = any(
            c.get("narrative_position") in HIGH_DRAMA_POSITIONS for c in window_chunks
        )
        met = sum([crit_dramatic, crit_density, crit_entities, crit_position])

        if met < 2:
            continue

        candidates.append({
            "chunk_start": window_idx[0],
            "chunk_end": window_idx[-1],
            "composite_score": round(composite_score, 4),
            "avg_dramatic": round(avg_dramatic, 4),
            "avg_density": round(avg_density, 4),
            "unique_entities": sorted(unique_entities),
            "sample_chunks": window_chunks,
        })

    if not candidates:
        # Fallback: take all windows regardless of criteria, sorted by composite score
        for start_pos in range(0, len(sorted_indices), step):
            end_pos = min(start_pos + window_size - 1, len(sorted_indices) - 1)
            window_idx = sorted_indices[start_pos: end_pos + 1]
            window_chunks = [indexed[i] for i in window_idx]
            if not window_chunks:
                continue
            dramatic_scores = [float(c.get("dramatic_score", 0.0)) for c in window_chunks]
            densities = [_density_numeric(c.get("visual_density", "low")) for c in window_chunks]
            avg_dramatic = sum(dramatic_scores) / len(dramatic_scores)
            avg_density = sum(densities) / len(densities)
            unique_entities = set()
            for c in window_chunks:
                unique_entities.update(c.get("characters_present", []))
            entity_bonus = min(1.0, len(unique_entities) / 3)
            composite = avg_dramatic * 0.5 + avg_density * 0.3 + entity_bonus * 0.2
            candidates.append({
                "chunk_start": window_idx[0],
                "chunk_end": window_idx[-1],
                "composite_score": round(composite, 4),
                "avg_dramatic": round(avg_dramatic, 4),
                "avg_density": round(avg_density, 4),
                "unique_entities": sorted(unique_entities),
                "sample_chunks": window_chunks,
            })

    # Sort by composite score descending
    candidates.sort(key=lambda x: x["composite_score"], reverse=True)

    # Non-maximum suppression: remove windows that overlap > 50% with a higher-scored window
    kept: list[dict] = []
    for cand in candidates:
        s1, e1 = cand["chunk_start"], cand["chunk_end"]
        span1 = max(1, e1 - s1 + 1)
        suppress = False
        for k in kept:
            s2, e2 = k["chunk_start"], k["chunk_end"]
            overlap = max(0, min(e1, e2) - max(s1, s2) + 1)
            window_min = min(span1, max(1, e2 - s2 + 1))
            if overlap > window_min * 0.5:
                suppress = True
                break
        if not suppress:
            kept.append(cand)

    # Return top (scene_count * 1.2) rounded up
    import math
    target_count = max(scene_count, math.ceil(scene_count * 1.2))
    return kept[:target_count]


# ---------------------------------------------------------------------------
# Pass B: LLM refinement (single batched call)
# ---------------------------------------------------------------------------


def extract_scenes_llm(
    candidates: list[dict],
    scene_count: int,
    chunk_text_map: Optional[dict[int, str]] = None,
    manuscript_lang: str = "en",
    analysis_run_id: Optional[str] = None,
) -> list[dict]:
    """
    Single LLM call to select and refine exactly scene_count scenes from candidates.

    candidates: output of group_chunks_into_candidate_scenes()
    chunk_text_map: optional {chunk_index: text} for richer context
    manuscript_lang: ISO 639-1 code (e.g. "ru", "en"); when not "en", request title_display and narrative_summary_display.
    Returns: list of scene dicts matching SCENE_EXTRACTION_PROMPT schema.
    """
    if not candidates:
        return []

    client = _get_client()

    # Build concise candidate summaries for the LLM (avoid sending full text)
    candidate_summaries: list[dict] = []
    for i, cand in enumerate(candidates):
        summary: dict = {
            "candidate_id": i + 1,
            "chunk_start_index": cand["chunk_start"],
            "chunk_end_index": cand["chunk_end"],
            "composite_score": cand["composite_score"],
            "avg_dramatic_score": cand["avg_dramatic"],
            "entities_present": cand["unique_entities"][:10],
            "narrative_positions": list({
                c.get("narrative_position", "") for c in cand["sample_chunks"]
                if c.get("narrative_position")
            }),
        }
        # Include visual_moment snippets from the sample chunks
        moments = [
            c.get("visual_moment", "")
            for c in cand["sample_chunks"]
            if c.get("visual_moment")
        ]
        if moments:
            summary["visual_moments"] = moments[:3]
        # Include brief text excerpt if available
        if chunk_text_map:
            texts = []
            for idx in range(cand["chunk_start"], cand["chunk_end"] + 1):
                t = chunk_text_map.get(idx, "")
                if t:
                    texts.append(t[:200])
                if sum(len(t) for t in texts) > 800:
                    break
            if texts:
                summary["text_excerpt"] = " [...] ".join(texts)
        candidate_summaries.append(summary)

    prompt = SCENE_EXTRACTION_PROMPT.replace("{scene_count}", str(scene_count))
    user_content = json.dumps({
        "scene_count": scene_count,
        "manuscript_lang": manuscript_lang,
        "candidates": candidate_summaries,
        **({"analysis_run_id": analysis_run_id} if analysis_run_id else {}),
    }, ensure_ascii=False)

    logger.info(
        "[scene_extractor] extract_scenes_llm: %d candidates → %d scenes",
        len(candidates), scene_count,
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.3,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
        usage = response.usage
        logger.info(
            "[scene_extractor] tokens: prompt=%s completion=%s total=%s",
            usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    except Exception as e:
        logger.error("[scene_extractor] LLM call failed: %s", e)
        return _build_scene_fallbacks(candidates, scene_count)

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        parsed = json.loads(raw)
        scenes = parsed.get("scenes", []) if isinstance(parsed, dict) else parsed
        if not isinstance(scenes, list):
            raise ValueError("Expected scenes list")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[scene_extractor] Failed to parse LLM response: %s | raw: %s", e, raw[:500])
        return _build_scene_fallbacks(candidates, scene_count)

    # Validate and normalise each scene
    validated: list[dict] = []
    for scene in scenes:
        if not isinstance(scene, dict):
            continue
        chunk_start = scene.get("chunk_start_index", 0)
        chunk_end = scene.get("chunk_end_index", chunk_start)
        # Ensure span is within allowed range (3-7 chunks)
        span = chunk_end - chunk_start + 1
        if span < 3:
            chunk_end = chunk_start + 2
        elif span > 7:
            chunk_end = chunk_start + 6

        validated.append({
            "title": scene.get("title") or f"Scene {len(validated) + 1}",
            "title_display": scene.get("title_display") or None,
            "scene_type": scene.get("scene_type") or "atmospheric",
            "chunk_start_index": chunk_start,
            "chunk_end_index": chunk_end,
            "narrative_summary": scene.get("narrative_summary") or "",
            "narrative_summary_display": scene.get("narrative_summary_display") or None,
            "visual_description": scene.get("visual_description") or "",
            "characters_present": scene.get("characters_present") or [],
            "primary_location": scene.get("primary_location") or "",
            "visual_intensity": float(scene.get("visual_intensity") or 0.5),
            "illustration_priority": scene.get("illustration_priority") or "medium",
            "scene_prompt_draft": scene.get("scene_prompt_draft") or "",
        })

    # If LLM returned fewer scenes than requested, pad with fallbacks from candidates
    if len(validated) < scene_count:
        fallbacks = _build_scene_fallbacks(candidates, scene_count - len(validated))
        validated.extend(fallbacks)

    return validated[:scene_count]


def _build_scene_fallbacks(candidates: list[dict], count: int) -> list[dict]:
    """Build fallback scenes from candidates when LLM fails."""
    scenes: list[dict] = []
    for i, cand in enumerate(candidates[:count]):
        scenes.append({
            "title": f"Scene {i + 1}",
            "title_display": None,
            "scene_type": "atmospheric",
            "chunk_start_index": cand["chunk_start"],
            "chunk_end_index": cand["chunk_end"],
            "narrative_summary": "",
            "narrative_summary_display": None,
            "visual_description": "",
            "characters_present": cand.get("unique_entities", [])[:3],
            "primary_location": "",
            "visual_intensity": cand.get("composite_score", 0.5),
            "illustration_priority": "medium",
            "scene_prompt_draft": "",
        })
    return scenes


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def extract_scenes(
    chunk_analyses: list[dict],
    scene_count: int,
    chunk_text_map: Optional[dict[int, str]] = None,
    manuscript_lang: str = "en",
    analysis_run_id: Optional[str] = None,
) -> list[dict]:
    """
    Full two-pass scene extraction.

    Args:
        chunk_analyses: list of chunk analysis dicts (with dramatic_score, visual_density, etc.)
        scene_count: exact number of scenes to return
        chunk_text_map: optional {chunk_index: text} for richer LLM context
        manuscript_lang: ISO 639-1 code; when not "en", scenes get title_display and narrative_summary_display

    Returns:
        list of scene dicts with title, title_display, scene_type, chunk_start_index, chunk_end_index,
        narrative_summary, narrative_summary_display, visual_description, characters_present,
        primary_location, visual_intensity, illustration_priority, scene_prompt_draft.
    """
    if not chunk_analyses or scene_count <= 0:
        return []

    logger.info(
        "[scene_extractor] extract_scenes: %d chunks, scene_count=%d, manuscript_lang=%s",
        len(chunk_analyses), scene_count, manuscript_lang,
    )

    # Pass A: sliding window
    candidates = group_chunks_into_candidate_scenes(chunk_analyses, scene_count)
    logger.info("[scene_extractor] Pass A: %d candidates", len(candidates))

    if not candidates:
        return []

    # Pass B: LLM refinement
    scenes = extract_scenes_llm(
        candidates, scene_count, chunk_text_map=chunk_text_map,
        manuscript_lang=manuscript_lang, analysis_run_id=analysis_run_id,
    )
    logger.info("[scene_extractor] Pass B: %d scenes selected", len(scenes))

    return scenes
