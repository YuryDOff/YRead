# LLM Analysis Prompts — Chunk & AI Analysis Branches

This document lists all prompts used for LLM-based analysis of manuscript chunks and related branches (characters, locations, artefacts, cover, scenes). Source: `backend/app/services/`.

---

## 1. Chunk batch analysis (characters + locations)

**Source:** `ai_service.py`  
**Constant:** `BATCH_ANALYSIS_PROMPT`  
**Used by:** `analyze_chunk_batch()`

```
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
```

---

## 2. Consolidation (main characters & locations)

**Source:** `ai_service.py`  
**Constant:** `CONSOLIDATION_PROMPT`  
**Used by:** `consolidate_results()`

```
Given these character and location extractions from multiple sections of a book, consolidate into:

LANGUAGE RULES (mandatory):
- Write ALL of the following in ENGLISH only (they are stored and used for image search and T2I): physical_description, personality_traits, visual_description, atmosphere, search_visual_analog.
- Keep "name" in the ORIGINAL language as in the manuscript (e.g. Russian names stay in Russian).
- For EVERY character and location set "canonical_search_name" in ENGLISH: for well-known entities use the standard English name (e.g. "Napoleon", "Sherlock Holmes", "Easter Island"); for others use English transliteration or translation of the name (e.g. "Ivan" → "Ivan", "Москва" → "Moscow") so that image search and APIs can use it. Never leave canonical_search_name null — always provide an English form.

1. Top 5 MAIN CHARACTERS (most frequently mentioned, most important to plot; pick consistently by mention frequency to reduce variance between re-runs)
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
```

---

## 3. Entity visual tokens (characters & locations)

**Source:** `ai_service.py`  
**Constant:** `ENTITY_VISUAL_TOKEN_PROMPT`  
**Used by:** `build_entity_visual_tokens_batch()`

```
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
```

---

## 4. Ontology classification (characters & locations)

**Source:** `ontology_service.py`  
**Constant:** `ONTOLOGY_PROMPT` (uses `ENTITY_CLASSES` from ontology_constants)  
**Used by:** `classify_entities_batch()` when entity_role is not "artefact"

```
You are classifying fictional entities for visual image search.

For each entity, select entity_class from EXACTLY this list:
human, human_supernatural, human_transformed, human_enhanced, clone, human_hybrid, android, robot, AI, cyborg, golem, construct, deity, demigod, angel, demon, cosmic_entity, elemental, spirit, ghost, undead, shade, fae, mythical_beast, folkloric, trickster, animal, anthropomorphic_animal, beast, chimera, shapeshifter, plant_being, animated_object, alien, alien_humanoid, hivemind, eldritch

Return ONLY valid JSON array, one object per entity:
[
  {
    "name": "entity name",
    "entity_class": "<one value from the list above>",
    "materiality": "organic|mechanical|holographic|energy-based|hybrid|immaterial",
    "power_status": "dominant|subordinate|assistant|childlike|corrupted|neutral",
    "embodiment": "physical|digital_avatar|disembodied|amorphous",
    "visual_markers": ["3 to 6 concrete visual markers"],
    "anti_human_override": true or false,
    "search_archetype": "short visual archetype phrase for non-human, or null"
  }
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
```

---

## 5. Ontology classification (artefacts)

**Source:** `ontology_service.py`  
**Constant:** `ONTOLOGY_ARTEFACT_PROMPT` (uses `ARTEFACT_ENTITY_CLASSES`)  
**Used by:** `classify_entities_batch(entity_role="artefact")`

```
You are classifying narrative artefacts (objects, items) for visual image search.

For each artefact, select entity_class from EXACTLY this list:
physical_weapon, magical_weapon, document_scroll, vessel_container, clothing_armour, instrument_device, vehicle, magical_item, natural_object, symbolic_token, other_artefact

Return ONLY valid JSON array, one object per entity:
[
  {
    "name": "artefact name",
    "entity_class": "<one value from the list above>",
    "materiality": "organic|mechanical|holographic|energy-based|hybrid|immaterial",
    "power_status": "dominant|subordinate|assistant|childlike|corrupted|neutral",
    "embodiment": "physical|digital_avatar|disembodied|amorphous",
    "visual_markers": ["3 to 6 concrete visual markers"],
    "anti_human_override": true or false,
    "search_archetype": "short visual archetype phrase for image search, or null"
  }
]

RULES:
- All output must be in ENGLISH.
- For artefacts, anti_human_override is typically false (objects are not human).
- visual_markers must be concrete and visual (e.g. "rusted blade", "glowing runes").
- visual_markers must have exactly 3 to 6 items.
- Output order MUST match input order exactly.
```

---

## 6. Artefact extraction from chunks

**Source:** `artefact_analysis_service.py`  
**Constant:** `ARTEFACT_EXTRACTION_PROMPT`  
**Used by:** `extract_artefacts_from_chunks()`

```
You are extracting narrative artefacts from fiction for visual reference.

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

Output MUST be a JSON array only. No markdown. Same order as input chunks where applicable.
```

---

## 7. Artefact visual tokens

**Source:** `artefact_analysis_service.py`  
**Constant:** `ARTEFACT_VISUAL_TOKEN_PROMPT`  
**Used by:** `build_artefact_visual_tokens_batch()`

```
You are generating structured visual search tokens for narrative artefacts (objects, items, vehicles).

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
- Focus on the object, not people or places. Output order MUST match input order exactly.
```

---

## 8. Cover — thematic extraction (stage 1)

**Source:** `cover_analysis_service.py`  
**Constant:** `COVER_THEMATIC_EXTRACTION_PROMPT`  
**Used by:** `extract_thematic_material()`

```
You are analyzing a work of fiction to extract thematic material for cover design.

From the provided text (chunk summaries from the manuscript), identify:

1. dominant_motifs — list of 4–8 key recurring motifs (objects, natural elements, concepts)
2. symbolic_anchors — 1–2 central symbolic images that could anchor the cover
3. emotional_arc — one paragraph on the central emotional journey
4. recurring_imagery — list of 4–8 recurring visual images
5. central_tension — the central tension in one sentence
6. tone_words — list of 5–10 mood/tone words

Return ONLY valid JSON with these exact keys (all arrays of strings except emotional_arc and central_tension which are strings).
```

---

## 9. Cover — brief synthesis (stage 2)

**Source:** `cover_analysis_service.py`  
**Constant:** `COVER_BRIEF_SYNTHESIS_PROMPT`  
**Used by:** `synthesise_cover_brief()`

```
You are synthesizing a cover design brief from thematic material.

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

Use the provided genre conventions. Character/location/artefact hints are names only; caller will resolve to ids.
```

---

## 10. Cover — genre conventions (input to stage 2)

**Source:** `cover_analysis_service.py`  
**Constant:** `GENRE_COVER_CONVENTIONS`

| Genre | Convention |
|-------|------------|
| fantasy | Character-forward or world-building landscape; rich colour; ornate typography |
| sci_fi | Technological or cosmic imagery; cool palette; geometric or sans-serif type |
| thriller | Dark, high-contrast; single symbolic object or silhouette; bold sans type |
| literary_fiction | Abstract or atmospheric; muted palette; elegant serif |
| romance | Warm tones; intimate imagery; script typography |
| mystery | Single enigmatic object; shadow and light; restrained palette |
| childrens | Character-forward; bright palette; playful rounded typography |
| historical_fiction | Period-accurate imagery; aged textures; serif typography |

---

## 11. Scene extraction

**Source:** `scene_extractor.py`  
**Constant:** `SCENE_EXTRACTION_PROMPT` (placeholder `{scene_count}` replaced at runtime)  
**Used by:** `extract_scenes_llm()`

```
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
```

---

## 12. Scene visual tokens & T2I prompts

**Source:** `scene_visual_composer.py`  
**Constant:** `SCENE_TOKEN_PROMPT`  
**Used by:** `compose_scenes_batch()`

```
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
```

---

## Summary

| # | Branch | Source file | Constant | Purpose |
|---|--------|-------------|----------|---------|
| 1 | Chunks | ai_service.py | BATCH_ANALYSIS_PROMPT | Per-chunk characters, locations, visual_moment, scores |
| 2 | Chunks | ai_service.py | CONSOLIDATION_PROMPT | Merge to top 5 characters, top 5 locations, tone |
| 3 | Characters/Locations | ai_service.py | ENTITY_VISUAL_TOKEN_PROMPT | Visual search tokens per entity |
| 4 | Characters/Locations | ontology_service.py | ONTOLOGY_PROMPT | entity_class, visual_markers, search_archetype |
| 5 | Artefacts | ontology_service.py | ONTOLOGY_ARTEFACT_PROMPT | entity_class for artefacts |
| 6 | Artefacts | artefact_analysis_service.py | ARTEFACT_EXTRACTION_PROMPT | Extract artefacts from chunk sample |
| 7 | Artefacts | artefact_analysis_service.py | ARTEFACT_VISUAL_TOKEN_PROMPT | Visual tokens for artefacts |
| 8 | Cover | cover_analysis_service.py | COVER_THEMATIC_EXTRACTION_PROMPT | Stage 1: thematic material |
| 9 | Cover | cover_analysis_service.py | COVER_BRIEF_SYNTHESIS_PROMPT | Stage 2: cover brief JSON |
| 10 | Cover | cover_analysis_service.py | GENRE_COVER_CONVENTIONS | Genre hints for stage 2 |
| 11 | Scenes | scene_extractor.py | SCENE_EXTRACTION_PROMPT | Select/refine N scenes from candidates |
| 12 | Scenes | scene_visual_composer.py | SCENE_TOKEN_PROMPT | Scene visual tokens + T2I prompts |
