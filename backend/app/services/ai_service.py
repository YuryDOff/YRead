"""AI analysis service using OpenAI GPT for book analysis."""
import json
import logging
import os
from typing import Optional

from openai import OpenAI

logger = logging.getLogger(__name__)

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


# Model to use – GPT-3.5-turbo keeps costs low
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

BATCH_ANALYSIS_PROMPT = """\
You are analyzing a book to extract visual and narrative elements for AI illustration generation.

Analyze the following text excerpts (chunks). For EACH chunk, provide:
1. Characters mentioned (name, physical description, personality, typical emotions)
2. Locations mentioned (name, visual description, atmosphere)
3. The most dramatic/visual moment (brief scene description)
4. A dramatic score from 0.0 to 1.0 (how visually interesting this chunk is)
5. Which characters and locations appear in each chunk (by name)

Focus on VISUAL details: age, height, build, hair, eyes, skin, clothing for characters.
For locations: architecture, colors, lighting, weather, mood.

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
      "dramatic_moment": "",
      "dramatic_score": 0.0,
      "characters_present": ["name1", "name2"],
      "locations_present": ["name1"]
    }
  ]
}
"""

CONSOLIDATION_PROMPT = """\
Given these character and location extractions from multiple sections of a book, consolidate into:

1. Top 5 MAIN CHARACTERS (most frequently mentioned, most important to plot)
   - Merge duplicate descriptions into comprehensive profiles
   - Create detailed physical descriptions
   - Identify 2 most characteristic emotions for each

2. Top 5 MAIN LOCATIONS (most important to story)
   - Merge duplicate descriptions
   - Create comprehensive visual descriptions

3. OVERALL TONE & STYLE
   - Genre classification
   - Narrative mood
   - Visual style recommendation for illustrations

Return ONLY valid JSON:
{
  "main_characters": [
    {
      "name": "",
      "physical_description": "",
      "personality_traits": "",
      "typical_emotions": ["", ""]
    }
  ],
  "main_locations": [
    {
      "name": "",
      "visual_description": "",
      "atmosphere": ""
    }
  ],
  "tone_and_style": {
    "genre": "",
    "mood": "",
    "visual_style": ""
  }
}
"""


# ---------------------------------------------------------------------------
# Batch analysis
# ---------------------------------------------------------------------------

def analyze_chunk_batch(chunks: list[dict]) -> dict:
    """
    Analyze a batch of chunks (10-15) via GPT.

    *chunks* is a list of dicts with keys: chunk_index, text.
    Returns parsed JSON with characters, locations, chunk_analyses.
    """
    client = _get_client()

    # Build the user message with numbered chunks
    parts: list[str] = []
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

def consolidate_results(all_batch_results: list[dict]) -> dict:
    """
    Take all batch results and consolidate characters/locations into
    top-5 lists plus overall tone.
    """
    client = _get_client()

    # Gather all characters & locations across batches
    all_chars: list[dict] = []
    all_locs: list[dict] = []
    for batch in all_batch_results:
        all_chars.extend(batch.get("characters", []))
        all_locs.extend(batch.get("locations", []))

    user_content = json.dumps(
        {"all_characters": all_chars, "all_locations": all_locs},
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

BATCH_SIZE = 10  # chunks per GPT call


def run_full_analysis(
    chunks: list[dict],
) -> dict:
    """
    Run the complete analysis pipeline:
      1) Batch analysis (groups of BATCH_SIZE)
      2) Consolidation
      3) Return combined result with per-chunk data

    *chunks* — list of dicts with at least {chunk_index, text}.

    Returns:
    {
        "main_characters": [...],
        "main_locations": [...],
        "tone_and_style": {...},
        "chunk_analyses": [...]    # merged from all batches
    }
    """
    all_batch_results: list[dict] = []
    all_chunk_analyses: list[dict] = []

    # 1. Batch analysis
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        logger.info(
            "Analyzing batch %d–%d of %d chunks",
            batch[0]["chunk_index"],
            batch[-1]["chunk_index"],
            len(chunks),
        )
        result = analyze_chunk_batch(batch)
        all_batch_results.append(result)
        all_chunk_analyses.extend(result.get("chunk_analyses", []))

    # 2. Consolidation
    logger.info("Consolidating results from %d batches", len(all_batch_results))
    consolidated = consolidate_results(all_batch_results)

    # 3. Merge
    consolidated["chunk_analyses"] = all_chunk_analyses
    return consolidated
