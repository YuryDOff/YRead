"""AI analysis service using OpenAI GPT for book analysis."""
import json
import logging
import os
import time
import uuid
from typing import Callable, Optional

try:
    from langdetect import detect as _detect_lang, LangDetectException
except ImportError:
    _detect_lang = None
    LangDetectException = Exception  # type: ignore[misc, assignment]

from openai import OpenAI

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Scoring Constants & Keywords
# ---------------------------------------------------------------------------

ACTION_KEYWORDS = {
    "ran", "fought", "crashed", "discovered", "screamed",
    "exploded", "attacked", "collapsed", "revealed", "jumped",
    "rushed", "grabbed", "threw", "slammed", "burst"
}

VISUAL_ADJECTIVES = {
    "glowing", "dark", "towering", "ancient",
    "bright", "massive", "shimmering", "shadowy",
    "beautiful", "terrifying", "enormous", "tiny",
    "crimson", "golden", "silver", "emerald"
}

INTERNAL_MONOLOGUE_MARKERS = {"thought", "wondered", "remembered", "pondered", "considered"}

# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

_client: Optional[OpenAI] = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = OpenAI(api_key=api_key)
    return _client


# Model to use – gpt-4o-mini: 128K context, cheaper than gpt-3.5-turbo
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# ---------------------------------------------------------------------------
# Scoring & Analysis Functions
# ---------------------------------------------------------------------------

def calculate_dramatic_score(
    text: str,
    action_level: float,
    emotional_intensity: float,
    visual_richness: float,
) -> float:
    """
    Calculate dramatic score using multi-factor analysis.
    
    Args:
        text: The chunk text to analyze
        action_level: Action level from LLM (0.0-1.0)
        emotional_intensity: Emotional intensity from LLM (0.0-1.0)
        visual_richness: Visual richness from LLM (0.0-1.0)
    
    Returns:
        Dramatic score between 0.0 and 1.0
    """
    words = text.lower().split()
    
    # Calculate bonuses and penalties
    action_bonus = sum(1 for w in words if w in ACTION_KEYWORDS) * 0.2
    visual_bonus = sum(1 for w in words if w in VISUAL_ADJECTIVES) * 0.15
    monologue_penalty = sum(1 for w in words if w in INTERNAL_MONOLOGUE_MARKERS) * 0.05
    
    # Combine weighted factors
    score = (
        action_level * 0.4
        + emotional_intensity * 0.3
        + visual_richness * 0.3
        + action_bonus
        + visual_bonus
        - monologue_penalty
    )
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(score, 1.0))


def assess_visual_density(text: str) -> str:
    """
    Assess the visual density of text based on visual adjectives.
    
    Returns: "low", "medium", or "high"
    """
    words = text.split()
    if not words:
        return "low"
    
    count = sum(1 for w in words if w.lower() in VISUAL_ADJECTIVES)
    per_100 = (count / len(words)) * 100
    
    if per_100 >= 5:
        return "high"
    elif per_100 >= 2:
        return "medium"
    return "low"


def detect_narrative_position(chunk_index: int, total_chunks: int) -> str:
    """
    Detect narrative position based on chunk location in story.
    
    Returns: one of "opening_hook", "inciting_incident", "rising_action", 
             "midpoint", "climax", "resolution"
    """
    percent = chunk_index / max(total_chunks, 1)
    
    if percent <= 0.1:
        return "opening_hook"
    elif percent <= 0.15:
        return "inciting_incident"
    elif percent <= 0.5:
        return "rising_action"
    elif percent <= 0.7:
        return "midpoint"
    elif percent <= 0.9:
        return "climax"
    return "resolution"


def calculate_character_priority(characters_present: list[str], main_characters: list[dict]) -> float:
    """
    Calculate priority based on character presence.
    
    Returns: 1.0 (multiple main chars), 0.8 (one main char), or 0.5 (no main chars)
    """
    names = {c["name"] for c in main_characters if c.get("is_main")}
    present_set = set(characters_present)
    
    if len(names.intersection(present_set)) >= 2:
        return 1.0
    elif names.intersection(present_set):
        return 0.8
    return 0.5


def build_visual_tokens(visual_layers: dict) -> dict:
    """
    Build structured visual tokens from visual layers.
    
    Args:
        visual_layers: Dict with subject, secondary, environment, materials, lighting, mood
    
    Returns:
        Dict with core_tokens, style_tokens, technical_tokens
    """
    core = []
    style = []
    technical = []
    
    # Core visual elements
    core.extend(visual_layers.get("subject", []))
    core.extend(visual_layers.get("secondary", []))
    core.extend(visual_layers.get("environment", []))
    core.extend(visual_layers.get("materials", []))
    
    # Style elements - add cinematic lighting first to ensure it's included
    style.append("cinematic lighting")
    style.extend(visual_layers.get("lighting", []))
    style.extend(visual_layers.get("mood", []))
    
    # Technical requirements
    technical.append("high detail")
    
    return {
        "core_tokens": core[:6],  # Limit to 6 most important
        "style_tokens": style[:5],  # Limit to 5 (cinematic lighting will be first)
        "technical_tokens": technical,
    }


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

def detect_manuscript_language(chunks: list[dict], sample_chars: int = 4000) -> str:
    """
    Detect the primary language of the manuscript from chunk text.
    Returns ISO 639-1 code (e.g. 'en', 'ru'). Defaults to 'en' on failure.
    """
    if not chunks:
        return "en"
    text_parts = []
    total = 0
    for ch in chunks:
        t = (ch.get("text") or "").strip()
        if t:
            text_parts.append(t)
            total += len(t)
            if total >= sample_chars:
                break
    sample = " ".join(text_parts)[:sample_chars]
    if not sample.strip():
        return "en"
    if _detect_lang is None:
        return "en"
    try:
        return _detect_lang(sample) or "en"
    except LangDetectException:
        return "en"


BATCH_ANALYSIS_PROMPT = """\
You are analyzing a book to extract visual and narrative elements for AI illustration generation.

LANGUAGE: Write ALL of the following in ENGLISH only (they are stored and used for image search and APIs): character physical_description, location visual_description and atmosphere, visual_moment, visual_layers (subject, secondary, environment, materials, lighting, mood). Keep character and location NAMES in the original language as they appear in the text.

Analyze the following text excerpts (chunks). For EACH chunk, provide:
1. Characters mentioned (name, physical description, personality, typical emotions)
2. Locations mentioned (name, visual description, atmosphere)
3. The most dramatic/visual moment (brief scene description)
4. Action level (0.0-1.0): How much physical action/movement occurs
5. Emotional intensity (0.0-1.0): How emotionally charged the scene is
6. Visual richness (0.0-1.0): How visually detailed and descriptive the text is
7. Illustration priority: "high", "medium", or "low" - how suitable for illustration
8. Which characters and locations appear in each chunk (by name)
9. Visual layers: structured breakdown of visual elements
10. Visual moment: one-sentence description of the key illustratable moment

Focus on VISUAL details: age, height, build, hair, eyes, skin, clothing for characters.
For locations: architecture, colors, lighting, weather, mood.

For visual_layers, extract:
- subject: main character(s) or object(s) in focus
- secondary: supporting elements or secondary characters
- environment: setting, background, location details
- materials: textures, surfaces, materials mentioned
- lighting: light sources, lighting conditions, atmosphere
- mood: emotional tone, atmosphere descriptors

Return ONLY valid JSON in this exact format:
{
  "characters": [
    {"name": "", "physical_description": "", "personality": "", "emotions": ["", ""]}
  ],
  "locations": [
    {"name": "", "visual_description": "", "atmosphere": ""}
  ],
  "chunk_analyses": [
    {
      "chunk_index": 0,
      "visual_moment": "Brief one-sentence description of key visual scene",
      "action_level": 0.0,
      "emotional_intensity": 0.0,
      "visual_richness": 0.0,
      "illustration_priority": "medium",
      "characters_present": ["name1", "name2"],
      "locations_present": ["name1"],
      "visual_layers": {
        "subject": ["main character or object"],
        "secondary": ["supporting elements"],
        "environment": ["setting details"],
        "materials": ["textures, surfaces"],
        "lighting": ["light conditions"],
        "mood": ["emotional atmosphere"]
      }
    }
  ]
}
"""

ENTITY_VISUAL_TOKEN_PROMPT = """\
You are generating structured visual search tokens for fictional entities (characters and locations).

LANGUAGE: All output tokens must be in ENGLISH (core_tokens, style_tokens, archetype_tokens, anti_tokens) — they are used for image search and text-to-image APIs.

You will receive a JSON array of entities, each with: name, description, entity_class, anti_human_override, visual_markers, search_archetype.

For each entity, produce visual tokens for image search. Return a JSON array (same order as input):
[
  {
    "name": "entity name",
    "core_tokens": ["token1", ...],
    "style_tokens": ["token1", ...],
    "archetype_tokens": ["token1", ...],
    "anti_tokens": ["token1", ...]
  }
]

Rules:
- core_tokens: exactly 6 main visual characteristics (concrete, searchable)
- style_tokens: exactly 4 atmosphere/lighting/mood descriptors
- archetype_tokens: exactly 3 archetype phrases (REQUIRED when anti_human_override=true; empty list when false)
- anti_tokens: 2-3 terms to EXCLUDE from queries (empty for human entities)
- If anti_human_override=true: core_tokens must NOT contain "portrait", "person", "man", "woman", "face", "human"
- archetype_tokens must reflect entity_class (e.g. "android" → "mechanical construct", "metallic humanoid", "robotic figure")
- anti_tokens for non-human: capture humanising patterns to avoid (e.g. "man portrait", "human face", "person")
- Output order MUST match input order exactly
"""


def build_entity_visual_tokens_batch(entities: list[dict]) -> list[dict]:
    """
    Single batched LLM call to build visual tokens for all main entities.

    Input: [{"name": ..., "description": ..., "entity_class": ..., "anti_human_override": ...,
             "visual_markers": [...], "search_archetype": ...}]
    Output: [{"name": ..., "core_tokens": [...], "style_tokens": [...], "archetype_tokens": [...], "anti_tokens": [...]}]

    Output order matches input order. Falls back gracefully on parse errors.
    """
    if not entities:
        return []

    client = _get_client()
    user_content = json.dumps(entities, ensure_ascii=False)

    logger.info("[entity_tokens] build_entity_visual_tokens_batch: %d entities", len(entities))

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ENTITY_VISUAL_TOKEN_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
        raw = response.choices[0].message.content.strip()
        usage = response.usage
        logger.info(
            "[entity_tokens] tokens: prompt=%s completion=%s total=%s",
            usage.prompt_tokens, usage.completion_tokens, usage.total_tokens,
        )
    except Exception as e:
        logger.error("[entity_tokens] LLM call failed: %s", e)
        return _build_entity_token_fallbacks(entities)

    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        results = json.loads(raw)
        if not isinstance(results, list):
            raise ValueError("Expected JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        logger.error("[entity_tokens] Failed to parse response: %s | raw: %s", e, raw[:500])
        return _build_entity_token_fallbacks(entities)

    # Validate and normalise each result
    validated: list[dict] = []
    for i, item in enumerate(results):
        if not isinstance(item, dict):
            validated.append(_entity_token_fallback(entities[i] if i < len(entities) else {}))
            continue

        anti_override = entities[i].get("anti_human_override", False) if i < len(entities) else False

        # Enforce: no human terms in core_tokens when anti_human_override=True
        HUMAN_TERMS = {"portrait", "person", "man", "woman", "face", "human"}
        core = [t for t in item.get("core_tokens", []) if t.lower() not in HUMAN_TERMS] if anti_override else item.get("core_tokens", [])
        # Pad if too few after filter
        while len(core) < 6 and item.get("archetype_tokens"):
            filler = item["archetype_tokens"][len(core) % max(1, len(item["archetype_tokens"]))]
            if filler not in core:
                core.append(filler)
            else:
                break

        validated.append({
            "name": item.get("name", entities[i].get("name", "") if i < len(entities) else ""),
            "core_tokens": core[:6],
            "style_tokens": item.get("style_tokens", [])[:4],
            "archetype_tokens": item.get("archetype_tokens", [])[:3],
            "anti_tokens": item.get("anti_tokens", [])[:3],
        })

    # Pad with fallbacks if LLM returned fewer items
    while len(validated) < len(entities):
        idx = len(validated)
        validated.append(_entity_token_fallback(entities[idx] if idx < len(entities) else {}))

    return validated[:len(entities)]


def _entity_token_fallback(entity: dict) -> dict:
    """Return safe default visual tokens when LLM fails for an entity."""
    anti_override = entity.get("anti_human_override", False)
    entity_class = entity.get("entity_class", "human")
    markers = entity.get("visual_markers", [])

    if anti_override:
        core = (markers[:3] if markers else [entity_class, "detailed", "dramatic lighting"])
        core = core + ["high contrast", "cinematic", "concept art"][: max(0, 6 - len(core))]
        archetype = [entity_class.replace("_", " "), "non-human form", "fantastical figure"]
        anti = ["man portrait", "human face"]
    else:
        core = (markers[:3] if markers else ["detailed figure", "dramatic lighting", "cinematic"])
        core = core + ["portrait", "realistic", "high detail"][: max(0, 6 - len(core))]
        archetype = []
        anti = []

    return {
        "name": entity.get("name", ""),
        "core_tokens": core[:6],
        "style_tokens": ["cinematic lighting", "high detail", "dramatic", "atmospheric"],
        "archetype_tokens": archetype[:3],
        "anti_tokens": anti,
    }


def _build_entity_token_fallbacks(entities: list[dict]) -> list[dict]:
    return [_entity_token_fallback(e) for e in entities]


CONSOLIDATION_PROMPT = """\
Given these character and location extractions from multiple sections of a book, consolidate into:

LANGUAGE RULES (mandatory):
- Write ALL of the following in ENGLISH only (they are stored and used for image search and T2I): physical_description, personality_traits, visual_description, atmosphere, search_visual_analog.
- Keep "name" in the ORIGINAL language as in the manuscript (e.g. Russian names stay in Russian).
- For EVERY character and location set "canonical_search_name" in ENGLISH: for well-known entities use the standard English name (e.g. "Napoleon", "Sherlock Holmes", "Easter Island"); for others use English transliteration or translation of the name (e.g. "Ivan" → "Ivan", "Москва" → "Moscow") so that image search and APIs can use it. Never leave canonical_search_name null — always provide an English form.

1. Top 5 MAIN CHARACTERS (most frequently mentioned, most important to plot)
   - Merge duplicate descriptions into comprehensive profiles
   - Create detailed physical descriptions (in English)
   - Identify 2 most characteristic emotions for each
   - Mark EXACTLY ONE character as "is_main": true — the single most important protagonist
   - All other characters must have "is_main": false
   - For each character set "visual_type" to exactly one of: "man", "woman", "animal", "AI", "alien", "creature" (based on physical description and context)
   - If the character is a real or well-known person/entity (historical, celebrity, famous fictional with established look), set "is_well_known_entity": true and "canonical_search_name" to the standard English name for image search (e.g. "Napoleon", "Sherlock Holmes"); otherwise "is_well_known_entity": false and "canonical_search_name" to English transliteration/translation of the name
   - For fictional characters with is_well_known_entity false, set "search_visual_analog" to a short phrase of real-world visual keywords in English (e.g. "young woman red hair green eyes medieval dress")

2. Top 5 MAIN LOCATIONS (most important to story)
   - Merge duplicate descriptions; write all in English
   - Create comprehensive visual descriptions (in English)
   - Mark EXACTLY ONE location as "is_main": true — the single most important/frequent location
   - All other locations must have "is_main": false
   - If the location is real or well-known (e.g. Easter Island, Paris, Mount Everest), set "is_well_known_entity": true and "canonical_search_name" to the standard English name; otherwise "is_well_known_entity": false and "canonical_search_name" to English transliteration/translation of the location name
   - For fictional locations with is_well_known_entity false, set "search_visual_analog" to real-world visual keywords in English (e.g. "tropical island ancient stone statues ocean cliffs")

3. OVERALL TONE & STYLE
   - Genre classification
   - Narrative mood
   - Visual style recommendation for illustrations

4. KNOWN ADAPTATIONS (only when is_well_known_book = true)
   - List known film/TV/animation adaptations as: "Title Year format"  (max 3, empty array if none)
   - Examples: "I Robot 2004 film", "BBC miniseries 2003", "Disney animation 1991"

Return ONLY valid JSON:
{
  "main_characters": [
    {
      "name": "",
      "physical_description": "",
      "personality_traits": "",
      "typical_emotions": ["", ""],
      "is_main": false,
      "visual_type": "woman",
      "is_well_known_entity": false,
      "canonical_search_name": "English name or transliteration",
      "search_visual_analog": ""
    }
  ],
  "main_locations": [
    {
      "name": "",
      "visual_description": "",
      "atmosphere": "",
      "is_main": false,
      "is_well_known_entity": false,
      "canonical_search_name": "English name or transliteration",
      "search_visual_analog": ""
    }
  ],
  "tone_and_style": {
    "genre": "",
    "mood": "",
    "visual_style": ""
  },
  "known_adaptations": []
}
"""


# ---------------------------------------------------------------------------
# Batch analysis
# ---------------------------------------------------------------------------

def analyze_chunk_batch(chunks: list[dict], run_id: Optional[str] = None) -> dict:
    """
    Analyze a batch of chunks (10-15) via GPT.

    *chunks* is a list of dicts with keys: chunk_index, text.
    *run_id*: optional unique id for this analysis run; appended to the prompt to reduce
    OpenAI server-side cache hits when re-analyzing the same manuscript (same prompt would
    otherwise return identical or near-identical responses).
    Returns parsed JSON with characters, locations, chunk_analyses.
    """
    logger.info("analyze_chunk_batch: batch size=%s, calling OpenAI", len(chunks))
    client = _get_client()

    # Build the user message with numbered chunks
    parts: list[str] = []
    if run_id:
        parts.append(f"[Analysis run: {run_id}]")
    for ch in chunks:
        parts.append(f"--- CHUNK {ch['chunk_index']} ---\n{ch['text']}")
    user_content = "\n\n".join(parts)

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": BATCH_ANALYSIS_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    result_text = response.choices[0].message.content
    usage = response.usage
    logger.info(
        "Batch analysis: prompt_tokens=%s completion_tokens=%s total=%s",
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
    )

    try:
        return json.loads(result_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse batch analysis JSON: %s", result_text[:500])
        return {"characters": [], "locations": [], "chunk_analyses": []}


# ---------------------------------------------------------------------------
# Consolidation
# ---------------------------------------------------------------------------

def consolidate_results(
    all_batch_results: list[dict],
    is_well_known_book: bool = False,
    run_id: Optional[str] = None,
) -> dict:
    """
    Take all batch results and consolidate characters/locations into
    top-5 lists plus overall tone.

    When is_well_known_book=True, the prompt instructs the model to also
    populate known_adaptations (film/TV/animation adaptations list).
    *run_id*: optional unique id for this run; appended to the prompt to reduce cache hits.
    """
    client = _get_client()

    # Gather all characters & locations across batches
    all_chars: list[dict] = []
    all_locs: list[dict] = []
    for batch in all_batch_results:
        all_chars.extend(batch.get("characters", []))
        all_locs.extend(batch.get("locations", []))

    user_content = json.dumps(
        {
            "all_characters": all_chars,
            "all_locations": all_locs,
            "is_well_known_book": is_well_known_book,
            **({"analysis_run_id": run_id} if run_id else {}),
        },
        ensure_ascii=False,
    )

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": CONSOLIDATION_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.3,
        max_tokens=4096,
    )

    usage = response.usage
    logger.info(
        "Consolidation: prompt_tokens=%s completion_tokens=%s total=%s",
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
    )

    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        logger.error("Failed to parse consolidation JSON")
        return {"main_characters": [], "main_locations": [], "tone_and_style": {}}


# ---------------------------------------------------------------------------
# Full analysis pipeline
# ---------------------------------------------------------------------------

BATCH_SIZE = 10  # chunks per GPT call; fewer round-trips = faster total analysis


def run_full_analysis(
    chunks: list[dict],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    scene_count: int = 10,
    is_well_known_book: bool = False,
    analysis_run_id: Optional[str] = None,
) -> dict:
    """
    Run the complete analysis pipeline:
      1) Batch analysis (groups of BATCH_SIZE)
      2) Consolidation
      2.5) Ontology Classifier — classify all entities
      3) Post-process chunks with dramatic scoring, narrative positions, visual tokens
      4) Return combined result with per-chunk data

    *chunks* — list of dicts with at least {chunk_index, text}.

    *analysis_run_id* — optional unique id for this run. When set, it is included in
    prompts so that re-analyzing the same manuscript produces different prompts and
    avoids OpenAI server-side cache hits (otherwise identical prompts can return
    identical or near-identical summaries). If None, a new UUID is generated per run.

    Returns:
    {
        "main_characters": [...],   # each includes "ontology" dict
        "main_locations":  [...],   # each includes "ontology" dict
        "tone_and_style":  {...},
        "chunk_analyses":  [...]
    }
    """
    from app.services.ontology_service import classify_entities_batch

    run_id = analysis_run_id or str(uuid.uuid4())
    logger.info("[analyze] run_full_analysis: analysis_run_id=%s", run_id)

    all_batch_results: list[dict] = []
    all_chunk_analyses: list[dict] = []

    chunk_text_map = {ch["chunk_index"]: ch["text"] for ch in chunks}
    manuscript_lang = detect_manuscript_language(chunks)
    logger.info("[analyze] detected manuscript language: %s", manuscript_lang)

    # 1. Batch analysis
    t_start = time.perf_counter()
    num_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
    logger.info(
        "[analyze] run_full_analysis: starting batch loop, total chunks=%s, BATCH_SIZE=%s, num_batches=%s",
        len(chunks), BATCH_SIZE, num_batches,
    )
    for i in range(0, len(chunks), BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        t_batch = time.perf_counter()
        batch = chunks[i: i + BATCH_SIZE]
        logger.info(
            "[analyze] Batch %d/%d (chunk_index %d\u2013%d of %d)...",
            batch_num, num_batches,
            batch[0]["chunk_index"],
            batch[-1]["chunk_index"],
            len(chunks),
        )
        result = analyze_chunk_batch(batch, run_id=run_id)
        all_batch_results.append(result)
        all_chunk_analyses.extend(result.get("chunk_analyses", []))
        if progress_callback:
            try:
                chunks_processed = i + len(batch)
                progress_callback(chunks_processed, len(chunks))
            except Exception:
                pass
        logger.info("[analyze] Batch %d/%d done in %.1fs", batch_num, num_batches, time.perf_counter() - t_batch)

    # 2. Consolidation
    t_cons = time.perf_counter()
    logger.info("[analyze] Consolidating results from %d batches...", len(all_batch_results))
    if progress_callback:
        try:
            progress_callback(len(chunks), len(chunks))
        except Exception:
            pass
    consolidated = consolidate_results(
        all_batch_results, is_well_known_book=is_well_known_book, run_id=run_id
    )
    logger.info("[analyze] Consolidation done in %.1fs", time.perf_counter() - t_cons)

    # 2.5. Ontology Classifier — single batched LLM call for all entities
    t_onto = time.perf_counter()
    logger.info("[analyze] Classifying entities ontology...")
    main_characters = consolidated.get("main_characters", [])
    main_locations = consolidated.get("main_locations", [])

    entities_for_ontology: list[dict] = []
    for ch in main_characters:
        entities_for_ontology.append({
            "name": ch.get("name", ""),
            "description": ch.get("physical_description", ""),
            "visual_type": ch.get("visual_type", ""),
            "entity_role": "character",
        })
    for loc in main_locations:
        entities_for_ontology.append({
            "name": loc.get("name", ""),
            "description": loc.get("visual_description", ""),
            "visual_type": "location",
            "entity_role": "location",
        })

    ontology_results: list[dict] = []
    if entities_for_ontology:
        try:
            ontology_results = classify_entities_batch(entities_for_ontology)
        except Exception as e:
            logger.error("[analyze] Ontology classification failed: %s", e)
            ontology_results = []

    # Attach ontology back to each character / location
    onto_map: dict[str, dict] = {}
    for o in ontology_results:
        if isinstance(o, dict) and o.get("name"):
            onto_map[o["name"].lower()] = o

    for ch in main_characters:
        key = ch.get("name", "").lower()
        ch["ontology"] = onto_map.get(key, {})

    for loc in main_locations:
        key = loc.get("name", "").lower()
        loc["ontology"] = onto_map.get(key, {})

    logger.info("[analyze] Ontology done in %.1fs", time.perf_counter() - t_onto)

    # 3. Entity-level visual token builder — single batched LLM call
    if progress_callback:
        try:
            progress_callback(len(chunks), len(chunks))
        except Exception:
            pass
    t_tokens = time.perf_counter()
    logger.info("[analyze] Building entity visual tokens...")

    entities_for_tokens: list[dict] = []
    for ch in main_characters:
        onto = ch.get("ontology") or {}
        entities_for_tokens.append({
            "name": ch.get("name", ""),
            "description": ch.get("physical_description", ""),
            "entity_class": onto.get("entity_class", "human"),
            "anti_human_override": onto.get("anti_human_override", False),
            "visual_markers": onto.get("visual_markers", []),
            "search_archetype": onto.get("search_archetype"),
        })
    for loc in main_locations:
        onto = loc.get("ontology") or {}
        entities_for_tokens.append({
            "name": loc.get("name", ""),
            "description": loc.get("visual_description", ""),
            "entity_class": onto.get("entity_class", "construct"),
            "anti_human_override": False,
            "visual_markers": onto.get("visual_markers", []),
            "search_archetype": None,
        })

    token_results: list[dict] = []
    if entities_for_tokens:
        try:
            token_results = build_entity_visual_tokens_batch(entities_for_tokens)
        except Exception as e:
            logger.error("[analyze] Entity token building failed: %s", e)
            token_results = []

    # Attach visual tokens back to each character / location
    token_map: dict[str, dict] = {}
    for t in token_results:
        if isinstance(t, dict) and t.get("name"):
            token_map[t["name"].lower()] = t

    for ch in main_characters:
        key = ch.get("name", "").lower()
        ch["entity_visual_tokens"] = token_map.get(key, {})

    for loc in main_locations:
        key = loc.get("name", "").lower()
        loc["entity_visual_tokens"] = token_map.get(key, {})

    logger.info("[analyze] Entity visual tokens done in %.1fs", time.perf_counter() - t_tokens)

    # 3b. Post-process chunks with deterministic enhancements
    total_chunks = len(chunks)

    for chunk_analysis in all_chunk_analyses:
        chunk_idx = chunk_analysis.get("chunk_index", 0)
        chunk_text = chunk_text_map.get(chunk_idx, "")

        chunk_analysis["narrative_position"] = detect_narrative_position(chunk_idx, total_chunks)
        chunk_analysis["visual_density"] = assess_visual_density(chunk_text)
        chunk_analysis["dramatic_score"] = calculate_dramatic_score(
            text=chunk_text,
            action_level=chunk_analysis.get("action_level", 0.5),
            emotional_intensity=chunk_analysis.get("emotional_intensity", 0.5),
            visual_richness=chunk_analysis.get("visual_richness", 0.5),
        )
        characters_present = chunk_analysis.get("characters_present", [])
        chunk_analysis["character_priority"] = calculate_character_priority(
            characters_present, main_characters
        )
        if "visual_layers" in chunk_analysis:
            chunk_analysis["visual_tokens"] = build_visual_tokens(chunk_analysis["visual_layers"])

    # 4. Scene extraction — sliding window + LLM refinement
    if progress_callback:
        try:
            progress_callback(len(chunks), len(chunks))
        except Exception:
            pass
    t_scenes = time.perf_counter()
    logger.info("[analyze] Extracting scenes (scene_count=%d)...", scene_count)

    scenes: list[dict] = []
    if scene_count > 0 and all_chunk_analyses:
        try:
            from app.services.scene_extractor import extract_scenes
            scenes = extract_scenes(
                all_chunk_analyses,
                scene_count=scene_count,
                chunk_text_map=chunk_text_map,
                manuscript_lang=manuscript_lang,
                analysis_run_id=run_id,
            )
        except Exception as e:
            logger.error("[analyze] Scene extraction failed: %s", e)
            scenes = []

    logger.info("[analyze] Scene extraction done in %.1fs: %d scenes", time.perf_counter() - t_scenes, len(scenes))

    # 5. Scene visual composer — build visual tokens + T2I prompts per scene
    if progress_callback:
        try:
            progress_callback(len(chunks), len(chunks))
        except Exception:
            pass
    t_composer = time.perf_counter()
    logger.info("[analyze] Building scene visual tokens and T2I prompts...")

    if scenes:
        try:
            from app.services.scene_visual_composer import compose_scenes_batch
            tone_and_style = consolidated.get("tone_and_style", {})
            style_cat = tone_and_style.get("genre", "fiction")
            character_ontologies = [
                {
                    "name": ch.get("name", ""),
                    "entity_class": (ch.get("ontology") or {}).get("entity_class", "human"),
                    "anti_human_override": (ch.get("ontology") or {}).get("anti_human_override", False),
                    "visual_markers": (ch.get("ontology") or {}).get("visual_markers", []),
                    "search_archetype": (ch.get("ontology") or {}).get("search_archetype"),
                }
                for ch in main_characters
            ]
            scenes = compose_scenes_batch(scenes, character_ontologies, style_cat)
        except Exception as e:
            logger.error("[analyze] Scene visual composition failed: %s", e)

    logger.info("[analyze] Scene composition done in %.1fs", time.perf_counter() - t_composer)

    # Final merge and return
    consolidated["chunk_analyses"] = all_chunk_analyses
    consolidated["main_characters"] = main_characters
    consolidated["main_locations"] = main_locations
    consolidated["scenes"] = scenes

    logger.info(
        "[analyze] Analysis complete in %.1fs: %d chunks, %d main characters, %d main locations",
        time.perf_counter() - t_start,
        len(all_chunk_analyses),
        len(main_characters),
        len(main_locations),
    )

    return consolidated
