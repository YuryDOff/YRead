# Refactoring Plan v3: Semantic-to-Visual Translation Engine + Scene Narrative Layer

**Version:** 3.0  
**Changes from v2:**
- Search Queries screen: review & edit only — no T2I model selector, no generate button
- Full entity class taxonomy (30+ classes with parent hierarchy and tiered fallback)
- Provider list corrected: Flickr removed from free tier, DeviantArt via SerpAPI only
- Engine ratings (👍/👎 per book) — new DB table, feeds back into engine selection
- Well-known / adapted books: `known_adaptations` field + dedicated query strategy
- `engine_selector.py`: tiered fallback with `ENTITY_PARENT` mapping

**Out of scope (do not touch):** book upload (Create Book, except adding `scene_count`), Search Results display, Visual Bible approval.

---

## Updated Full Pipeline Architecture

```
[Create Book] → author, style_category, is_well_known, scene_count
        ↓
[POST /books/{id}/chunk]
        ↓
[POST /books/{id}/analyze]
        ↓
run_full_analysis():
  Step 1: Batch Analysis        → chunk_analyses (visual_layers, dramatic_score, ...)
  Step 2: Consolidation         → main_characters, main_locations, tone_and_style,
                                   known_adaptations (if well-known book)
  Step 2.5: Ontology Classifier → ontology_json per entity  (full 30+ class taxonomy)
  Step 3: Entity Token Builder  → entity_visual_tokens_json per entity
  Step 4: Scene Extractor       → N scenes (sliding window → LLM refinement)
  Step 5: Scene Visual Composer → scene_visual_tokens_json, t2i_prompt_json per scene
  Step 6: Save all to DB
        ↓
[Analysis Review]  Tabs: Characters | Locations | Scenes
  User: marks ★ is_main entities, reviews/toggles/edits scenes
  PUT /entity-selections
        ↓
[Search Queries]  ← REVIEW & EDIT ONLY (no model selector, no generate button)
  Characters: edit summary, edit search queries
  Locations:  edit summary, edit search queries
  Scenes:     read scene title + narrative_summary + scene_prompt_draft (editable)
              read t2i_prompt_json[abstract] (read-only, informational)
  POST /entity-summaries  (saves edits)
  POST /search-references (runs search with engine selection + engine ratings)
        ↓
[Search Results]  ← lightbox, thumbnails + provider badge
  User selects reference images
  👍/👎 per image → PATCH /books/{id}/engine-ratings → updates engine_ratings in DB
  Approve → selected_reference_urls saved
        ↓
[Visual Bible]
        ↓
[T2I Generation]  ← separate later step, after visual bible approved
  scene_prompt + reference images → POST /scenes/{id}/generate-illustration
  → T2IProvider.generate()
  → Illustration saved with scene_id
  → prompt_used shown in Preview screen
```

---

## Problem Diagnosis

| Problem | Root cause |
|---|---|
| LLM humanises non-human entities | `_character_suffix()` adds suffix only — no ontological enforcement in tokens |
| Queries too generic | Chunk-level token aggregation, not entity-level |
| `build_visual_tokens` at chunk level | Doesn't reflect consolidated entity characteristics |
| Single provider for everything | No engine selection logic |
| 1–3 similar queries | No semantic diversification |
| No narrative layer | No Scene model — only `visual_moment` string per chunk |
| T2I prompt built manually | No `scene_visual_composer`, no T2I provider abstraction |
| Well-known books not leveraged | No `known_adaptations` field, no adaptation-specific query strategy |

---

# PART I — Visual Semantic Engine

## Phase 1 — Visual Ontology Classifier

**File:** `app/services/ontology_service.py` (new)  
Called after `consolidate_results()`. One batched LLM call for all entities.

### 1.1 Full Entity Class Taxonomy

The `entity_class` field uses a closed enum of 30+ classes grouped by category.
This replaces the old 7-class list and covers all genres.

```python
# app/services/ontology_service.py

ENTITY_CLASSES = [
    # Human variants
    "human", "human_supernatural", "human_transformed", "human_enhanced",
    "clone", "human_hybrid",
    # Mechanical & Digital
    "android", "robot", "AI", "cyborg", "golem", "construct",
    # Divine & Cosmic
    "deity", "demigod", "angel", "demon", "cosmic_entity", "elemental",
    # Spirits & Undead
    "spirit", "ghost", "undead", "shade",
    # Fae & Mythical
    "fae", "mythical_beast", "folkloric", "trickster",
    # Animal-based
    "animal", "anthropomorphic_animal", "beast", "chimera", "shapeshifter",
    # Plant & Object
    "plant_being", "animated_object",
    # Alien & Unknown
    "alien", "alien_humanoid", "hivemind", "eldritch",
]

# Parent class hierarchy for tiered fallback in engine_selector
ENTITY_PARENT = {
    "human_supernatural": "human",
    "human_transformed":  "human",
    "human_enhanced":     "human",
    "clone":              "human",
    "human_hybrid":       "human_supernatural",
    "cyborg":             "android",
    "android":            "robot",
    "golem":              "construct",
    "animated_object":    "construct",
    "plant_being":        "construct",
    "ghost":              "spirit",
    "shade":              "spirit",
    "demigod":            "deity",
    "angel":              "deity",
    "demon":              "deity",
    "cosmic_entity":      "deity",
    "elemental":          "spirit",
    "fae":                "mythical_beast",
    "folkloric":          "mythical_beast",
    "trickster":          "mythical_beast",
    "beast":              "mythical_beast",
    "chimera":            "mythical_beast",
    "shapeshifter":       "mythical_beast",
    "anthropomorphic_animal": "animal",
    "alien_humanoid":     "alien",
    "hivemind":           "alien",
    "eldritch":           "cosmic_entity",
}

# Which classes require anti_human_override = true
NON_HUMAN_CLASSES = set(ENTITY_CLASSES) - {
    "human", "human_supernatural", "human_transformed",
    "human_enhanced", "clone", "human_hybrid",
    "demigod",  # demigods often have human visual form — keep human queries valid
}
```

### 1.2 Ontology Prompt

```python
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
- anti_human_override = true for all classes EXCEPT:
  human, human_supernatural, human_transformed, human_enhanced, clone, human_hybrid, demigod
- search_archetype is required when anti_human_override = true
- visual_markers must be concrete and visual, not abstract (e.g. "glowing red eyes", not "menacing")
- Choose the most specific class available
"""

def classify_entities_batch(entities: list[dict]) -> list[dict]:
    """
    Single LLM call for all entities (characters + locations).
    Input:  [{"name": ..., "description": ..., "visual_type": ...}]
    Output: [{"name": ..., "entity_class": ..., "materiality": ..., ...}]
    """
    ...
```

### 1.3 DB additions

```python
# In Character and Location models:
ontology_json = Column(Text, nullable=True)            # JSON: full ontology dict
entity_visual_tokens_json = Column(Text, nullable=True) # JSON: core/style/archetype/anti tokens
```

### 1.4 Integration

`run_full_analysis()` step 2.5, after consolidation, before entity token building.  
`_run_analysis_background()` in `books.py` saves `ontology_json` per entity.

### 1.5 Frontend (Analysis Review)

```tsx
// OntologyBadges component under each entity description
const OntologyBadges = ({ ontology }) => (
  <div className="flex flex-wrap gap-1 mt-2">
    <Badge variant="entity">{ontology.entity_class}</Badge>
    <Badge variant="material">{ontology.materiality}</Badge>
    <Badge variant="power">{ontology.power_status}</Badge>
    {ontology.visual_markers?.slice(0,3).map(m => (
      <Badge key={m} variant="marker">{m}</Badge>
    ))}
  </div>
);
```

---

## Phase 2 — Entity-Level Visual Token Builder

**Function:** `build_entity_visual_tokens(name, description, ontology)` in `ai_service.py`  
Built from consolidated description + ontology. Replaces chunk-level aggregation.

```python
ENTITY_VISUAL_TOKEN_PROMPT = """
Given a fictional entity's description and ontological classification,
generate structured visual tokens for image search.

Return ONLY valid JSON:
{
  "core_tokens": [...],        // 6: main visual characteristics
  "style_tokens": [...],       // 4: atmosphere, lighting, mood
  "archetype_tokens": [...],   // 3: entity archetype (required if anti_human_override=true)
  "anti_tokens": [...]         // 2–3: what to explicitly EXCLUDE from queries
}

If anti_human_override=true: core_tokens must NOT contain portrait/person/man/woman.
archetype_tokens must reflect entity_class.
anti_tokens capture humanising patterns to avoid.
"""
```

**Integration:** `_get_visual_tokens_for_entity()` in `search_service.py` —
priority: `entity_visual_tokens_json` (new) → fallback: chunk-based aggregation (existing, unchanged).

---

## Phase 3 — Search Engine Adapter Layer

### 3.1 Provider list (corrected)

```
app/services/providers/
    base.py          # BaseImageProvider (abstract)
    unsplash.py      # refactored to base — free, 50 req/hour
    serpapi.py       # refactored to base — 100 free searches, then paid
    pexels.py        # NEW — free, 200 req/hour, 20K/month; descriptive phrases
    openverse.py     # NEW — free, no key required; open-licensed content
    pixabay.py       # NEW — free, unlimited requests; tags via +; sci-fi/fantasy
    wikimedia.py     # NEW — free, no key; historical, real locations, public domain
    deviantart.py    # NEW — via SerpAPI (site:deviantart.com); concept art, fantasy
```

**Flickr: EXCLUDED from default providers.**
Flickr API key requires a Pro subscription ($82/year). Include as optional provider only
if user supplies their own `FLICKR_API_KEY`. Add note in `.env.example`.

**DeviantArt:** no official API. Implemented as a SerpAPI wrapper with
`engine=google_images&site=deviantart.com`. Requires `SERPAPI_KEY`.

### 3.2 BaseImageProvider

```python
# app/services/providers/base.py
from abc import ABC, abstractmethod

class BaseImageProvider(ABC):
    name: str   # "unsplash", "pexels", etc.

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    async def search(self, query: str, content_type: str, count: int = 15) -> list[dict]: ...

    def format_query(self, raw_query: str) -> str:
        """Override per provider to adapt query format. Default: return as-is."""
        return raw_query
```

### 3.3 Query format per provider

| Provider | Query format | Best for |
|---|---|---|
| Unsplash | Natural phrases 3–6 words | Realistic human portraits, locations |
| Pexels | Descriptive phrases 5–8 words | Portraits, lifestyle, nature |
| Pixabay | Tags joined by `+` | Sci-fi, fantasy, concept illustrations |
| Openverse | Formal descriptions | Historical, archival, open-license |
| Wikimedia | Place/person names | Real locations, historical figures |
| SerpAPI | Standard query + negative terms | General fallback, fan-art |
| DeviantArt | Query + `site:deviantart.com` | Fantasy creatures, concept art |

---

## Phase 4 — Engine Selection Logic

**File:** `app/services/engine_selector.py` (new)

### 4.1 Affinity matrix (expanded for full taxonomy)

```python
ENGINE_AFFINITY = {
    # Human variants
    "human|fiction":               {"unsplash": 10, "pexels": 9},
    "human|romance":               {"unsplash": 10, "pexels": 9},
    "human|thriller":              {"unsplash": 9,  "pexels": 8, "serpapi": 6},
    "human|historical":            {"wikimedia": 10, "unsplash": 6},
    "human_supernatural|fantasy":  {"pixabay": 9, "deviantart": 8, "unsplash": 5},
    "human_enhanced|sci-fi":       {"pixabay": 9, "serpapi": 7},
    "human_hybrid|fantasy":        {"deviantart": 10, "pixabay": 8},
    # Mechanical & Digital
    "android|sci-fi":              {"pixabay": 10, "deviantart": 9, "serpapi": 7},
    "android|cyberpunk":           {"pixabay": 10, "deviantart": 10, "serpapi": 8},
    "robot|sci-fi":                {"pixabay": 10, "deviantart": 8, "serpapi": 7},
    "AI|sci-fi":                   {"pixabay": 9, "openverse": 7, "serpapi": 8},
    "AI|cyberpunk":                {"pixabay": 10, "deviantart": 9},
    "cyborg|sci-fi":               {"pixabay": 9, "deviantart": 9, "serpapi": 7},
    "construct|fantasy":           {"deviantart": 10, "pixabay": 8},
    "golem|fantasy":               {"deviantart": 10, "pixabay": 8},
    # Divine & Cosmic
    "deity|fantasy":               {"deviantart": 10, "pixabay": 9},
    "deity|mythology":             {"wikimedia": 8, "deviantart": 9, "pixabay": 8},
    "demigod|fantasy":             {"deviantart": 10, "pixabay": 9},
    "angel|fantasy":               {"deviantart": 9, "pixabay": 8, "unsplash": 5},
    "demon|fantasy":               {"deviantart": 10, "pixabay": 9},
    "cosmic_entity|sci-fi":        {"deviantart": 10, "pixabay": 8, "serpapi": 6},
    "elemental|fantasy":           {"deviantart": 9, "pixabay": 9, "unsplash": 4},
    # Spirits & Undead
    "spirit|fantasy":              {"deviantart": 9, "pixabay": 8},
    "spirit|folklore":             {"wikimedia": 7, "deviantart": 8, "pixabay": 7},
    "ghost|horror":                {"deviantart": 9, "pixabay": 8, "serpapi": 6},
    "undead|fantasy":              {"deviantart": 10, "pixabay": 9},
    "undead|horror":               {"deviantart": 9, "serpapi": 8},
    # Fae & Mythical
    "fae|fantasy":                 {"deviantart": 10, "pixabay": 9},
    "mythical_beast|fantasy":      {"deviantart": 10, "pixabay": 9},
    "folkloric|fantasy":           {"deviantart": 9, "pixabay": 8, "wikimedia": 5},
    "folkloric|folklore":          {"wikimedia": 8, "deviantart": 8, "pixabay": 7},
    "trickster|fantasy":           {"deviantart": 9, "pixabay": 8},
    # Animal-based
    "animal|fiction":              {"unsplash": 10, "pexels": 8},
    "animal|adventure":            {"unsplash": 9, "pixabay": 7},
    "anthropomorphic_animal|fantasy": {"deviantart": 10, "pixabay": 9},
    "beast|fantasy":               {"deviantart": 10, "pixabay": 9},
    "beast|horror":                {"deviantart": 9, "serpapi": 7},
    "chimera|fantasy":             {"deviantart": 10, "pixabay": 9},
    "shapeshifter|fantasy":        {"deviantart": 9, "pixabay": 8},
    # Alien & Unknown
    "alien|sci-fi":                {"deviantart": 10, "pixabay": 9, "serpapi": 7},
    "alien_humanoid|sci-fi":       {"deviantart": 9, "pixabay": 8, "serpapi": 7},
    "hivemind|sci-fi":             {"deviantart": 9, "pixabay": 8},
    "eldritch|horror":             {"deviantart": 10, "pixabay": 8, "serpapi": 6},
    # Locations
    "location|fiction":            {"unsplash": 10, "pexels": 8},
    "location|romance":            {"unsplash": 10, "pexels": 9},
    "location|sci-fi":             {"pixabay": 9, "unsplash": 7, "serpapi": 6},
    "location|cyberpunk":          {"pixabay": 10, "deviantart": 8, "serpapi": 7},
    "location|fantasy":            {"deviantart": 9, "pixabay": 8, "unsplash": 6},
    "location|horror":             {"pixabay": 8, "deviantart": 8, "serpapi": 6},
    "location|historical":         {"wikimedia": 10, "unsplash": 6},
    "location|folklore":           {"wikimedia": 8, "pixabay": 7, "unsplash": 5},
}
```

### 4.2 Tiered fallback

```python
def select_engines(
    entity_class: str,
    entity_type: str,
    style_category: str,
    available_providers: list[str],
    engine_ratings: dict,        # {provider: net_score} from DB for this book
    top_n: int = 2,
) -> list[str]:
    """
    Tiered lookup:
    1. Exact key: "entity_class|style_category"
    2. Parent class: ENTITY_PARENT[entity_class] + "|" + style_category
    3. Style-only fallback: "location|style" or generic human fallback
    4. Hardcoded default: unsplash + serpapi

    engine_ratings modifies scores:
    final_score = affinity_score * (1 + 0.1 * net_score)
    net_score = likes - dislikes for this provider on this book
    Cap net_score influence: clamp to [-5, +10] before applying
    """
    key = f"{entity_class}|{style_category}"
    if entity_type == "location":
        key = f"location|{style_category}"

    scores = (
        ENGINE_AFFINITY.get(key)
        or ENGINE_AFFINITY.get(f"{ENTITY_PARENT.get(entity_class, '')}|{style_category}")
        or ENGINE_AFFINITY.get(f"location|{style_category}" if entity_type == "location" else f"human|{style_category}")
        or {"unsplash": 7, "serpapi": 5}
    )

    # Apply engine rating modifier
    for provider, base_score in scores.items():
        net = engine_ratings.get(provider, 0)
        net_clamped = max(-5, min(10, net))
        scores[provider] = base_score * (1 + 0.1 * net_clamped)

    ranked = sorted(
        [(p, s) for p, s in scores.items() if p in available_providers],
        key=lambda x: x[1], reverse=True
    )
    return [p for p, _ in ranked[:top_n]]
```

### 4.3 Engine Ratings — DB table and API

**New model in `app/models.py`:**
```python
class EngineRating(Base):
    __tablename__ = "engine_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    provider = Column(String, nullable=False)   # "unsplash", "pixabay", etc.
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    @property
    def net_score(self) -> int:
        return self.likes - self.dislikes

    __table_args__ = (
        UniqueConstraint("book_id", "provider", name="uq_engine_rating"),
        Index("ix_engine_ratings_book_id", "book_id"),
    )
```

**New CRUD functions:**
```python
def get_engine_ratings(db, book_id) -> dict[str, int]:
    """Returns {provider: net_score} for the book."""

def update_engine_rating(db, book_id, provider, delta_likes, delta_dislikes) -> EngineRating:
    """Increments likes or dislikes. Creates row if not exists (upsert)."""
```

**New endpoint in `app/routers/visual_bible.py` (or new router):**
```
PATCH /books/{id}/engine-ratings
Body: { provider: str, action: "like" | "dislike" }
```

Called from Search Results lightbox when user clicks 👍/👎 under a thumbnail.

**Integration in `search_references_for_book()`:**
```python
ratings = crud.get_engine_ratings(db, book_id)   # {provider: net_score}
engines = select_engines(..., engine_ratings=ratings)
```

---

## Phase 5 — Query Diversification Engine

**Function:** `_build_queries_diversified()` in `search_service.py` — replaces `_build_queries()`.

Generates 4–5 semantically distinct queries:

```python
def _build_queries_diversified(
    entity_type: str,
    description: str,
    book_info: dict,                  # title, author, is_well_known, style_category,
                                      # known_adaptations (NEW)
    entity_visual_tokens: dict,       # from entity_visual_tokens_json
    ontology: dict,                   # from ontology_json
    *,
    visual_type: str = None,
    is_well_known_entity: bool = False,
    canonical_search_name: str = None,
    search_visual_analog: str = None,
) -> list[str]:
    """
    Query 1: Ontological archetype   — ontology.search_archetype + style_category
    Query 2: Visual markers          — top visual_markers + non-human suffix if applicable
    Query 3: Canonical / analog      — canonical_search_name or search_visual_analog
    Query 4: Core + archetype tokens — entity_visual_tokens core + archetype
    Query 5: Adaptation query        — if book has known_adaptations (see Phase 5.1)
    """
```

### 5.1 Well-known / adapted books strategy

When `book_info["is_well_known"] = True`, add additional query types:

```python
# In CONSOLIDATION_PROMPT, add field:
# "known_adaptations": ["1984 film 1984", "I Robot 2004 film", "BBC miniseries 2003"]
# Stored in visual_bible or as book field: known_adaptations_json

# Additional queries for well-known books:
if book_info.get("known_adaptations"):
    for adaptation in book_info["known_adaptations"][:2]:
        queries.append(f"{adaptation} {entity_type_label} still")
        # e.g. "I Robot 2004 film robot still"
        # These should be routed to SerpAPI (Google Images finds film stills)

if book_info.get("is_well_known"):
    # Illustration search
    queries.append(
        f"{book_info['title']} {book_info.get('author','')} book illustration".strip()
    )
```

**DB:** Add to `Book` model:
```python
known_adaptations_json = Column(Text, nullable=True)  # JSON array of adaptation strings
```

**CONSOLIDATION_PROMPT update:** Add instruction to populate `known_adaptations` when
`is_well_known_book = true`:
```
If is_well_known_book is true, list known film/TV/animation adaptations as:
"known_adaptations": ["Title Year format", ...]  // max 3, empty array if none
```

**Engine routing for adaptations:** Film stills queries → SerpAPI always (regardless of engine_ratings), because Google Images is the only provider that indexes film promotional material effectively. Other query types follow normal engine selection.

---

## Phase 6 — Schemas, Routers, Frontend (Part I — Entities)

- `app/schemas.py`: add `ontology: Optional[dict]`, `entity_visual_tokens: Optional[dict]` to `CharacterResponse` / `LocationResponse`
- `app/schemas.py`: extend `preferred_provider` enum: `"unsplash" | "serpapi" | "pexels" | "openverse" | "pixabay" | "wikimedia" | "deviantart" | "auto"`
- `app/routers/books.py`: GET /characters and GET /locations deserialise and include new fields
- Frontend, Search Queries: engine dropdown → `["Auto (recommended)", "Unsplash", "SerpAPI", "Pexels", "Pixabay", "Openverse", "Wikimedia", "DeviantArt"]`
- Frontend, Analysis Review: `OntologyBadges` component under each entity card

---

# PART II — Scene Narrative Layer

## Phase 7 — Scene Extractor

### 7.1 Data model

```
Chunk (technical unit)              Scene (narrative unit)
──────────────────────              ───────────────────────────────
id, book_id, chunk_index            id, book_id
text                                title
dramatic_score                      scene_type
visual_analysis_json                chunk_start_index
characters_present                  chunk_end_index          ← spans 3–7 chunks
locations_present                   characters: [id, ...]    ← FK via SceneCharacter
visual_layers                       locations: [id, ...]     ← FK via SceneLocation
                                    dramatic_score_avg
                                    visual_density
                                    scene_visual_tokens_json
                                    scene_prompt_draft       ← user-editable
                                    t2i_prompt_json          ← {abstract, flux, sd}
                                    narrative_position
                                    is_selected              ← user toggle
```

### 7.2 Extraction algorithm

**Step A — Sliding window (deterministic, no LLM):**

```python
def group_chunks_into_candidate_scenes(
    chunk_analyses: list[dict],
    scene_count: int,
    window_size: int = 5,
    step: int = 2,
) -> list[dict]:
    """
    For each window of window_size chunks:
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
    Return top (scene_count * 1.2) candidates for LLM refinement.
    """
```

**Step B — LLM Refinement (single batched call):**

```python
SCENE_EXTRACTION_PROMPT = """
Given N candidate scene windows from a novel, select and refine exactly {scene_count} scenes.

Prioritise scenes with:
- High dramatic tension or emotional peak
- Clear visual composition potential
- ≥ 2 entities present
- State change, conflict, revelation, or turning point
- Strong environmental context

For each selected scene return:
{
  "scene_id": 1,
  "title": "5–7 word evocative title",
  "scene_type": "climax|conflict|turning_point|revelation|emotional_peak|action|atmospheric",
  "chunk_start_index": 0,
  "chunk_end_index": 4,
  "narrative_summary": "2–3 sentences: what happens and why it matters",
  "visual_description": "detailed description of the KEY VISUAL MOMENT for illustration:
                         foreground, background, character positions, lighting, mood",
  "characters_present": ["name1", "name2"],
  "primary_location": "location name",
  "visual_intensity": 0.0–1.0,
  "illustration_priority": "high|medium|low",
  "scene_prompt_draft": "text-to-image ready prompt: visual style, character appearance,
                         environment, lighting, composition — for illustration generation"
}

Return ONLY valid JSON: {"scenes": [...]}
"""
```

### 7.3 New DB models

```python
class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title = Column(String, nullable=True)
    scene_type = Column(String, nullable=True)
    chunk_start_index = Column(Integer, nullable=False)
    chunk_end_index = Column(Integer, nullable=False)
    narrative_summary = Column(Text, nullable=True)
    visual_description = Column(Text, nullable=True)
    dramatic_score_avg = Column(Float, nullable=True)
    visual_intensity = Column(Float, nullable=True)
    illustration_priority = Column(String, nullable=True)
    narrative_position = Column(String, nullable=True)
    scene_prompt_draft = Column(Text, nullable=True)       # user-editable
    scene_visual_tokens_json = Column(Text, nullable=True)
    t2i_prompt_json = Column(Text, nullable=True)          # {abstract, flux, sd}
    is_selected = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="scenes")
    scene_characters = relationship("SceneCharacter", cascade="all, delete-orphan")
    scene_locations = relationship("SceneLocation", cascade="all, delete-orphan")
    illustrations = relationship("Illustration", back_populates="scene", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_scenes_book_id", "book_id"),)


class SceneCharacter(Base):
    __tablename__ = "scene_characters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)
    __table_args__ = (UniqueConstraint("scene_id", "character_id"),)


class SceneLocation(Base):
    __tablename__ = "scene_locations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    __table_args__ = (UniqueConstraint("scene_id", "location_id"),)
```

**Updates to existing models:**

```python
# Book: add
scene_count = Column(Integer, nullable=True, default=10)
known_adaptations_json = Column(Text, nullable=True)
scenes = relationship("Scene", back_populates="book", cascade="all, delete-orphan")

# Illustration: add scene_id, keep chunk_id nullable (table empty)
scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)
scene = relationship("Scene", back_populates="illustrations")
# chunk_id stays nullable — not removed, stays for back-compat
```

---

## Phase 8 — Scene Visual Composer

**File:** `app/services/scene_visual_composer.py` (new)

```python
SCENE_TOKEN_PROMPT = """
Given a scene's visual_description and the ontological profiles of characters present,
build structured visual tokens for this scene as a composition unit.

Return ONLY valid JSON:
{
  "core_tokens": [...],          // 6: key visual elements of the scene
  "style_tokens": [...],         // 4: atmosphere, lighting, mood
  "composition_tokens": [...],   // 3: camera angle, framing (e.g. "low angle", "wide shot")
  "character_tokens": [...],     // merged non-human visual markers from characters' ontologies
  "environment_tokens": [...]    // location-specific visual tokens
}

Apply anti_human_override: if any character has anti_human_override=true,
character_tokens must reflect their non-human nature, not default to human form.
"""

def build_scene_visual_tokens(
    scene: dict,
    character_ontologies: list[dict],
    location_visual_tokens: dict,
    style_category: str,
) -> dict: ...


def build_t2i_prompts(scene: dict, scene_visual_tokens: dict, style_category: str) -> dict:
    """
    Returns:
    {
      "abstract": "universal, model-agnostic description",
      "flux":     "FLUX-optimised — trigger words, LoRA hints, weight syntax",
      "sd":       "SD-optimised — emphasis via (), negative prompt hint"
    }
    abstract is always present. flux and sd are optional but built when possible.
    Adding a new T2I model later = add a new key to this dict. No DB migration needed.
    """
    ...
```

**Integration:** Step 5 of `run_full_analysis()`, after scene extraction.  
Scene visual tokens + t2i_prompt_json saved to DB in `_run_analysis_background()`.

---

## Phase 9 — T2I Provider Abstraction

**Files:**
```
app/services/t2i_providers/
    __init__.py             # ALL_T2I_PROVIDERS = {...}
    base.py                 # T2IRequest, T2IResult, BaseT2IProvider
    abstract_provider.py    # stub — returns prompt_used, no generation (for testing)
    flux_provider.py        # FLUX via fal.ai / Replicate — skeleton
    sd_provider.py          # Stable Diffusion via A1111 / ComfyUI — skeleton
```

```python
# base.py
@dataclass
class T2IRequest:
    prompt: str
    negative_prompt: str = ""
    reference_images: list[str] = None  # selected reference URLs from search
    width: int = 1024
    height: int = 1024

@dataclass
class T2IResult:
    image_url: str
    image_path: str
    provider: str
    prompt_used: str          # stored in Illustration, shown in Preview

class BaseT2IProvider(ABC):
    name: str

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def format_prompt(self, t2i_prompt_json: dict) -> str:
        """Extract model-specific prompt variant from t2i_prompt_json."""
        ...

    @abstractmethod
    async def generate(self, request: T2IRequest) -> T2IResult: ...
```

**Generation endpoint (stub for now):**
```
POST /books/{id}/scenes/{scene_id}/generate-illustration
Body: { t2i_provider, reference_character_url, reference_location_url }
→ background task → saves Illustration with scene_id and prompt_used
```

`prompt_used` is displayed in the **Preview screen** (existing screen, out of scope of this refactor, but the field is stored and available).

---

## Phase 10 — API Endpoints (Scene Layer)

### New router: `app/routers/scenes.py`

| Method | Path | Purpose |
|--------|------|---------|
| GET | /books/{id}/scenes | All scenes for book |
| PATCH | /books/{id}/scenes/{scene_id} | User edits: title, scene_prompt_draft, is_selected |
| POST | /books/{id}/scenes/{scene_id}/generate-illustration | Trigger T2I generation (later step) |
| GET | /books/{id}/scenes/{scene_id}/illustration | Generation status + result |

### Updated endpoints

`POST /books/{id}/analyze` — add `scene_count: int = 10` to `BookAnalyzeRequest`.

`GET /books/{id}/proposed-search-queries` — add `scenes` array to response
(selected scenes only, with `scene_prompt_draft` and `t2i_prompt_json`).

`PATCH /books/{id}/engine-ratings` — new endpoint (add to `visual_bible.py` router or new router).

### New schemas

```python
class SceneResponse(BaseModel):
    id: int
    title: Optional[str]
    scene_type: Optional[str]
    chunk_start_index: int
    chunk_end_index: int
    narrative_summary: Optional[str]
    visual_description: Optional[str]
    scene_prompt_draft: Optional[str]           # user-editable
    t2i_prompt_json: Optional[dict]             # {abstract, flux, sd} — read-only on Search Queries
    scene_visual_tokens: Optional[dict]
    dramatic_score_avg: Optional[float]
    illustration_priority: Optional[str]
    narrative_position: Optional[str]
    is_selected: bool
    characters_present: list[str] = []
    primary_location: Optional[str]

class SceneUpdateRequest(BaseModel):
    title: Optional[str] = None
    scene_prompt_draft: Optional[str] = None    # user may edit the draft
    is_selected: Optional[bool] = None

class EngineRatingUpdate(BaseModel):
    provider: str
    action: Literal["like", "dislike"]

class BookAnalyzeRequest(BaseModel):            # updated
    style_category: str
    illustration_frequency: Optional[int] = None
    layout_style: Optional[str] = None
    is_well_known: bool = False
    author: Optional[str] = None
    scene_count: int = 10                       # NEW
```

---

## Phase 11 — Frontend

### Search Queries screen — REVIEW & EDIT ONLY

**What changes:**
- Remove T2I model selector dropdown
- Remove "Generate illustration" button from this screen
- Scenes section shows: title, narrative_summary, scene_prompt_draft (editable textarea), and t2i_prompt_json.abstract (read-only, labelled "AI-generated prompt preview")
- No model switching, no generate action

```tsx
// Scenes section in Search Queries — review only
const SceneQueryReview = ({ scene }) => (
  <div className="scene-review-card">
    <div className="scene-header">
      <span className="badge">{scene.scene_type}</span>
      <span className="badge">{scene.illustration_priority}</span>
    </div>
    <h3>{scene.title}</h3>
    <p className="text-sm text-muted">{scene.narrative_summary}</p>

    <label>Scene prompt draft</label>
    <textarea
      value={scene.scene_prompt_draft}
      onChange={e => onUpdateScene(scene.id, { scene_prompt_draft: e.target.value })}
    />

    <label>AI prompt preview (read-only)</label>
    <p className="prompt-preview">{scene.t2i_prompt_json?.abstract}</p>

    <div className="scene-entities text-sm text-muted">
      {scene.characters_present.join(", ")} · {scene.primary_location}
    </div>
  </div>
);
```

### Analysis Review — Scenes tab

```tsx
const SceneCard = ({ scene, onToggleSelected, onEditPrompt }) => (
  <div className={`scene-card ${scene.is_selected ? 'selected' : ''}`}>
    <div className="scene-header">
      <Toggle checked={scene.is_selected} onChange={() => onToggleSelected(scene.id)} />
      <span className="badge badge-type">{scene.scene_type}</span>
      <span className="badge badge-priority">{scene.illustration_priority}</span>
    </div>
    <h3>{scene.title}</h3>
    <p>{scene.narrative_summary}</p>
    <div className="scene-entities">
      {scene.characters_present.map(c => <Chip key={c}>{c}</Chip>)}
      {scene.primary_location && <Chip>{scene.primary_location}</Chip>}
    </div>
    <div className="scene-prompt">
      <label>Scene prompt draft</label>
      <textarea value={scene.scene_prompt_draft} onChange={...} />
    </div>
    <SceneTokenBadges tokens={scene.scene_visual_tokens} />
  </div>
);
```

### Search Results — engine rating buttons

```tsx
// Under each thumbnail in lightbox:
<div className="image-card">
  <img src={image.thumbnail} />
  <span className="provider-badge">{image.source}</span>
  <div className="rating-buttons">
    <button onClick={() => rateEngine(image.source, "like")}>👍</button>
    <button onClick={() => rateEngine(image.source, "dislike")}>👎</button>
  </div>
</div>

// rateEngine calls:
// PATCH /books/{bookId}/engine-ratings { provider: image.source, action: "like" | "dislike" }
```

### Create Book — scene_count field

```tsx
<label>Number of key scenes to extract</label>
<input type="number" min={3} max={20} defaultValue={10}
       onChange={e => setSceneCount(Number(e.target.value))} />
// Passed in analyzeBook() → BookAnalyzeRequest.scene_count
```

### `frontend/src/services/api.ts` additions

```typescript
interface SceneResponse {
  id: number;
  title: string;
  scene_type: string;
  narrative_summary: string;
  visual_description: string;
  scene_prompt_draft: string;
  t2i_prompt_json: { abstract: string; flux?: string; sd?: string };
  characters_present: string[];
  primary_location: string;
  is_selected: boolean;
  illustration_priority: string;
  scene_visual_tokens: object;
}

interface EngineRatingUpdate { provider: string; action: "like" | "dislike"; }

const getScenes = (bookId: number): Promise<SceneResponse[]>
const updateScene = (bookId: number, sceneId: number, data: Partial<SceneResponse>): Promise<SceneResponse>
const rateEngine = (bookId: number, update: EngineRatingUpdate): Promise<void>
```

---

## Execution Order for Cursor (Claude Opus)

Execute strictly in order. Each step depends on the previous.

### Step 1: DB Migration (35 min)
1. `app/models.py`: add `ontology_json`, `entity_visual_tokens_json` to `Character` and `Location`
2. `app/models.py`: add `scene_count`, `known_adaptations_json` to `Book`
3. `app/models.py`: add `Scene`, `SceneCharacter`, `SceneLocation`, `EngineRating` tables
4. `app/models.py`: update `Illustration` — add `scene_id` (nullable), keep `chunk_id` nullable
5. `app/models.py`: add all relationships (`Book.scenes`, `Scene.illustrations`, `Book.engine_ratings`)
6. `alembic revision --autogenerate -m "add_ontology_scene_engine_rating"` → review migration
7. `alembic upgrade head` — verify no data loss (all new columns nullable)

### Step 2: CRUD Expansion (25 min)
1. `app/crud.py`: `create_scene`, `get_scenes_by_book`, `get_scene`, `update_scene`, `delete_scenes_by_book`
2. `app/crud.py`: `create_scene_character`, `create_scene_location`
3. `app/crud.py`: `get_character_by_name`, `get_location_by_name`
4. `app/crud.py`: `update_character_ontology`, `update_location_ontology`
5. `app/crud.py`: `get_engine_ratings`, `update_engine_rating`
6. `app/crud.py`: add `delete_scenes_by_book` call inside existing `clear_analysis_results()`

### Step 3: Constants file (10 min)
1. Create `app/services/ontology_constants.py`:
   - `ENTITY_CLASSES` list
   - `ENTITY_PARENT` dict
   - `NON_HUMAN_CLASSES` set
2. This file is imported by both `ontology_service.py` and `engine_selector.py`

### Step 4: Ontology Service (45 min)
1. Create `app/services/ontology_service.py` with `ONTOLOGY_PROMPT` and `classify_entities_batch()`
2. Integrate into `ai_service.run_full_analysis()` as step 2.5 (after consolidation)
3. Update `_run_analysis_background()` in `books.py` to save `ontology_json` per entity

### Step 5: Entity Visual Token Builder (30 min)
1. Add `ENTITY_VISUAL_TOKEN_PROMPT` and `build_entity_visual_tokens()` to `ai_service.py`
2. Call for each main entity in `run_full_analysis()` as step 3
3. Update `_get_visual_tokens_for_entity()` in `search_service.py` — entity-level first, chunk fallback

### Step 6: Scene Extractor (60 min)
1. Create `app/services/scene_extractor.py`:
   - `group_chunks_into_candidate_scenes()` — deterministic sliding window
   - `extract_scenes_llm()` — LLM refinement with `SCENE_EXTRACTION_PROMPT`
   - `extract_scenes()` — entry point
2. Add `scene_count` parameter to `run_full_analysis()` and `BookAnalyzeRequest`
3. Integrate as step 4 of `run_full_analysis()`
4. Update `_run_analysis_background()` — save scenes + SceneCharacter + SceneLocation to DB

### Step 7: Scene Visual Composer (45 min)
1. Create `app/services/scene_visual_composer.py`:
   - `build_scene_visual_tokens()` — LLM call building token graph
   - `build_t2i_prompts()` — builds `{abstract, flux, sd}` dict
2. Integrate as step 5 of `run_full_analysis()` (after scene extraction)
3. Save `scene_visual_tokens_json` and `t2i_prompt_json` to Scene in DB

### Step 8: T2I Provider Base (25 min)
1. Create `app/services/t2i_providers/base.py` — `T2IRequest`, `T2IResult`, `BaseT2IProvider`
2. Create `app/services/t2i_providers/abstract_provider.py` — stub returning prompt only
3. Create `app/services/t2i_providers/flux_provider.py` — skeleton (is_available checks env var)
4. Create `app/services/t2i_providers/sd_provider.py` — skeleton
5. Create `app/services/t2i_providers/__init__.py` — `ALL_T2I_PROVIDERS`

### Step 9: Search Provider Adapters (60 min)
1. Create `app/services/providers/base.py` — `BaseImageProvider`
2. Refactor `unsplash.py`, `serpapi.py` to extend `BaseImageProvider`
3. Implement `pexels.py` (200 req/hour free), `openverse.py` (free), `pixabay.py` (free)
4. Implement `wikimedia.py` (free, no key), `deviantart.py` (via SerpAPI wrapper)
5. Update `app/services/providers/__init__.py` — `ALL_PROVIDERS` dict

### Step 10: Engine Selector + Query Diversification (35 min)
1. Create `app/services/engine_selector.py`:
   - Import `ENTITY_PARENT` from `ontology_constants.py`
   - Full `ENGINE_AFFINITY` matrix
   - `select_engines()` with tiered fallback and ratings modifier
2. Add `_build_queries_diversified()` to `search_service.py` with adaptation query support
3. Replace all `_build_queries()` calls with `_build_queries_diversified()`
4. Integrate `select_engines()` and `get_engine_ratings()` in `search_references_for_book()`
5. Update `CONSOLIDATION_PROMPT` to extract `known_adaptations` for well-known books

### Step 11: Schemas + Routers (35 min)
1. `app/schemas.py`: add `SceneResponse`, `SceneUpdateRequest`, `EngineRatingUpdate`; update `BookAnalyzeRequest`; extend `CharacterResponse`/`LocationResponse`; extend provider enum
2. Create `app/routers/scenes.py`: GET, PATCH, POST generate-illustration (stub)
3. Register `scenes` router in `app/main.py`
4. Add engine-ratings endpoint to `app/routers/visual_bible.py` (or new router)
5. Update `app/routers/books.py`: accept `scene_count`, include ontology in entity responses
6. Update `app/routers/visual_bible.py`: include scenes in proposed-search-queries response

### Step 12: Frontend (50 min)
1. `api.ts`: add `SceneResponse`, `EngineRatingUpdate`; functions `getScenes()`, `updateScene()`, `rateEngine()`
2. Create Book: add `scene_count` field (default 10)
3. Analysis Review: add Scenes tab with `SceneCard` component
4. Search Queries: add Scenes section (review/edit only — no model selector, no generate button)
5. Search Results lightbox: add 👍/👎 buttons under each thumbnail, call `rateEngine()`

---

## Contracts (must not break)

| Contract | How protected |
|---|---|
| GET /characters, GET /locations | New fields added, all existing fields unchanged |
| POST /analyze | `scene_count` has default=10 — fully backwards compatible |
| Illustration.chunk_id | Kept nullable — table empty, zero risk |
| `_build_queries()` | Not deleted until step 10 completes and is verified |
| `_get_visual_tokens_from_chunks()` | Kept as fallback — entity-level is new priority |
| Book upload, Search Results display | Not touched |
| `clear_analysis_results()` | Extended with `delete_scenes_by_book` — re-analysis cleans scenes |
| `ENTITY_PARENT` fallback | Unknown entity_class always has a path to a valid affinity entry |

---

## Notes for Claude Opus

**On batching LLM calls:**
- `classify_entities_batch()` — all entities in one call
- `build_entity_visual_tokens()` — batch all main entities in one call (one JSON array in/out)
- `extract_scenes_llm()` — all candidates in one call
- `build_scene_visual_tokens()` — batch all scenes in one call

Do not make N individual calls per entity/scene. Batch everything.

**On progress_callback:**
Add stages: `"Classifying entities..."`, `"Building visual tokens..."`,
`"Extracting scenes..."`, `"Building scene prompts..."` so frontend progress bar reflects new steps.

**On `known_adaptations`:**
Film still queries must always route through SerpAPI regardless of engine_ratings,
because only Google Images reliably indexes film promotional material.
Wrap this as a special case in `_build_queries_diversified()`:
if query is an adaptation query → force provider = "serpapi", skip engine_selector.

**On Flickr:**
Do not implement `flickr.py` unless `FLICKR_API_KEY` is present in env.
Add to `.env.example`: `# FLICKR_API_KEY=  # Optional: requires Flickr Pro ($82/year)`.

**On `anti_tokens` in scene composition:**
If any character in the scene has `anti_human_override=true`, their `anti_tokens`
must propagate into `scene_visual_tokens.character_tokens` —
do not add humanising patterns even in scene-level composition.

**On engine ratings clamping:**
`net_score` influence is clamped to [-5, +10] before applying the multiplier.
This prevents a single enthusiastic user session from completely zeroing out a provider.
Minimum effective score after ratings = affinity_score * 0.5 (at net_score = -5).

---

# PART III — Success Criteria & Tests

## Definition of Done

A feature is considered complete when all three layers are satisfied:
1. **Functional** — the feature works end-to-end in the full pipeline
2. **Contract** — API contracts are not broken, existing data is not corrupted
3. **Quality** — measurable outcome metrics are met (see per-phase criteria below)

---

## Phase-by-Phase Success Criteria

### Phase 1 — Visual Ontology Classifier ✓ when:

- [ ] Every `main_character` and `main_location` after analysis has non-null `ontology_json`
- [ ] `entity_class` is always a value from `ENTITY_CLASSES` (never a free-form string)
- [ ] Characters with `visual_type = "AI"` receive `anti_human_override = true` in ≥ 95% of cases
- [ ] `visual_markers` contains 3–6 items (never 0, never > 6)
- [ ] `search_archetype` is non-null for all entities where `anti_human_override = true`
- [ ] Analysis Review shows ontology badges for all main entities without UI errors
- [ ] Re-running analysis clears and rebuilds ontology correctly (no stale data)

### Phase 2 — Entity Visual Token Builder ✓ when:

- [ ] All main entities have non-null `entity_visual_tokens_json` after analysis
- [ ] `_get_visual_tokens_for_entity()` returns entity-level tokens (not chunk aggregation) when field is populated
- [ ] For `anti_human_override = true` entities: `core_tokens` contains no values from `{"portrait", "person", "man", "woman", "face", "human"}`
- [ ] `anti_tokens` is non-empty for all non-human entities
- [ ] Chunk-based fallback still works correctly when `entity_visual_tokens_json` is null (old books)

### Phase 3 — Search Engine Adapter Layer ✓ when:

- [ ] All 6 new providers implement `BaseImageProvider` interface
- [ ] Each provider's `is_available()` returns `False` (not raises) when env var is missing
- [ ] Each provider's `format_query()` produces provider-appropriate format (verified by unit test)
- [ ] Pexels, Pixabay, Openverse each return ≥ 1 result for a standard test query
- [ ] Wikimedia returns results for a known historical figure/location query
- [ ] DeviantArt (via SerpAPI) returns results when `SERPAPI_KEY` is set
- [ ] No provider failure cascades and breaks the full search (all wrapped in try/except)

### Phase 4 — Engine Selection Logic ✓ when:

- [ ] `select_engines("AI", "character", "sci-fi", all_providers, {})` returns `["pixabay", "deviantart"]` or `["pixabay", "serpapi"]` (not `["unsplash"]`)
- [ ] `select_engines("human", "character", "fiction", all_providers, {})` returns `["unsplash", "pexels"]`
- [ ] `select_engines("folkloric", "character", "fantasy", all_providers, {})` returns providers matching `mythical_beast|fantasy` (parent fallback works)
- [ ] Unknown entity class (not in taxonomy) falls back gracefully without KeyError
- [ ] Engine ratings modifier: provider with net_score=+5 ranks higher than same provider with net_score=0
- [ ] Engine ratings modifier: provider with net_score=-5 does not disappear from results, only scores lower
- [ ] `engine_ratings` table is correctly updated by 👍/👎 actions and persisted across sessions

### Phase 5 — Query Diversification ✓ when:

- [ ] `_build_queries_diversified()` returns 4–5 queries for a standard character (not 1–2)
- [ ] All returned queries are semantically distinct (no two queries are substrings of each other)
- [ ] For `anti_human_override = true` entities: none of the 4–5 queries contain `{"man portrait", "woman portrait", "person portrait"}`
- [ ] For well-known books: at least one query is adaptation-specific and routed to SerpAPI
- [ ] For well-known books: at least one query targets book illustration
- [ ] `anti_tokens` from entity are applied as negative terms in SerpAPI queries (`-word`)

### Phase 6 — Schemas & Routers (Entities) ✓ when:

- [ ] GET /books/{id}/characters returns `ontology` and `entity_visual_tokens` fields
- [ ] GET /books/{id}/locations returns same new fields
- [ ] Old clients sending POST /analyze without `scene_count` still get 202 (default=10 applied)
- [ ] Old clients not sending new provider values in `preferred_provider` still work

### Phase 7 — Scene Extractor ✓ when:

- [ ] `run_full_analysis()` with `scene_count=5` produces exactly 5 scenes in DB
- [ ] Every scene has `chunk_start_index` and `chunk_end_index` covering 3–7 chunks
- [ ] Every scene has at least 1 entry in `scene_characters` or `scene_locations`
- [ ] `SceneCharacter` entries reference valid character IDs from the same book
- [ ] No two scenes have overlapping chunk ranges (non-maximum suppression working)
- [ ] Analysis Review Scenes tab displays all scenes without errors
- [ ] Re-running analysis with same `scene_count` produces a fresh set of scenes (old scenes deleted)
- [ ] Re-running analysis with `scene_count=3` produces exactly 3 scenes

### Phase 8 — Scene Visual Composer ✓ when:

- [ ] Every scene after analysis has non-null `scene_visual_tokens_json`
- [ ] Every scene has non-null `t2i_prompt_json` with at least `abstract` key
- [ ] `t2i_prompt_json.abstract` is ≥ 50 characters (not a stub or empty string)
- [ ] For scenes containing non-human characters: `scene_visual_tokens.character_tokens` does not default to human-portrait terms
- [ ] `composition_tokens` contains at least one camera/framing term (e.g. "wide shot", "close-up")

### Phase 9 — T2I Provider Base ✓ when:

- [ ] `abstract_provider` returns a `T2IResult` with `prompt_used` set and no external API call
- [ ] `flux_provider.is_available()` returns `False` when `FAL_API_KEY` / `REPLICATE_API_KEY` not set
- [ ] `format_prompt()` for flux returns `t2i_prompt_json["flux"]` when present, falls back to `abstract`
- [ ] `T2IRequest` with `reference_images=[]` does not crash any provider
- [ ] POST /scenes/{id}/generate-illustration returns 202 and creates Illustration row with `scene_id` set

### Phase 10 — API Endpoints (Scenes) ✓ when:

- [ ] GET /books/{id}/scenes returns all scenes with correct `characters_present` and `primary_location`
- [ ] PATCH /books/{id}/scenes/{id} with `{"is_selected": false}` persists correctly
- [ ] PATCH /books/{id}/scenes/{id} with `{"scene_prompt_draft": "..."}` persists correctly
- [ ] GET /books/{id}/proposed-search-queries includes `scenes` array with only `is_selected=true` scenes
- [ ] PATCH /books/{id}/engine-ratings correctly increments `likes` or `dislikes` counter
- [ ] PATCH /books/{id}/engine-ratings is idempotent for the same provider (does not duplicate rows)

### Phase 11 — Frontend ✓ when:

- [ ] Analysis Review: Scenes tab loads and displays scene cards without console errors
- [ ] Analysis Review: toggling `is_selected` on a scene sends correct PATCH and updates UI
- [ ] Analysis Review: editing `scene_prompt_draft` debounces and saves via PATCH
- [ ] Search Queries: Scenes section shows only `is_selected=true` scenes
- [ ] Search Queries: no T2I model selector, no generate button visible on this screen
- [ ] Search Queries: `t2i_prompt_json.abstract` field is read-only (textarea disabled or plain text)
- [ ] Search Results: 👍/👎 buttons visible under each thumbnail
- [ ] Search Results: clicking 👍 calls `rateEngine()`, no page reload required
- [ ] Create Book: `scene_count` field accepts values 3–20, defaults to 10

---

## Test Suite Structure

```
tests/
    unit/
        test_ontology_service.py
        test_entity_token_builder.py
        test_engine_selector.py
        test_query_diversification.py
        test_scene_extractor.py
        test_scene_visual_composer.py
        test_provider_format_query.py
    integration/
        test_full_analysis_pipeline.py
        test_search_references.py
        test_scene_api.py
        test_engine_ratings.py
    fixtures/
        sample_chunks_scifi.json       # I, Robot — for non-human entity tests
        sample_chunks_fantasy.json     # for folkloric/mythical entity tests
        sample_chunks_historical.json  # for human|historical tests
        sample_chunks_fairy_tale.json  # for anthropomorphic_animal, fae, folkloric
        expected_ontologies.json       # ground truth ontology for fixture characters
```

---

## Unit Tests

### `tests/unit/test_ontology_service.py`

```python
import pytest
from app.services.ontology_service import classify_entities_batch
from app.services.ontology_constants import ENTITY_CLASSES, NON_HUMAN_CLASSES

# --- Schema validation ---

def test_ontology_returns_valid_entity_class():
    """entity_class must always be from the closed enum."""
    entities = [{"name": "Robbie", "description": "A large clumsy robot with glowing red eyes", "visual_type": "AI"}]
    result = classify_entities_batch(entities)
    assert result[0]["entity_class"] in ENTITY_CLASSES

def test_ontology_non_human_sets_override():
    """AI/robot/alien entities must have anti_human_override=true."""
    entities = [
        {"name": "HAL 9000", "description": "A disembodied AI consciousness controlling a spaceship", "visual_type": "AI"},
        {"name": "Xenomorph", "description": "A biomechanical alien creature with acid blood", "visual_type": "alien"},
    ]
    results = classify_entities_batch(entities)
    for r in results:
        assert r["anti_human_override"] is True, f"{r['name']} should have anti_human_override=True"

def test_ontology_human_does_not_set_override():
    """Standard human characters must have anti_human_override=false."""
    entities = [{"name": "Susan Calvin", "description": "A frail woman in her seventies, roboticist", "visual_type": "woman"}]
    result = classify_entities_batch(entities)
    assert result[0]["anti_human_override"] is False

def test_ontology_visual_markers_count():
    """visual_markers must have 3–6 items."""
    entities = [{"name": "Gandalf", "description": "An old wizard with a grey beard and staff", "visual_type": "man"}]
    result = classify_entities_batch(entities)
    count = len(result[0]["visual_markers"])
    assert 3 <= count <= 6, f"Expected 3–6 visual markers, got {count}"

def test_ontology_search_archetype_present_for_non_human():
    """search_archetype must be non-null when anti_human_override=True."""
    entities = [{"name": "Robbie", "description": "A robot", "visual_type": "AI"}]
    result = classify_entities_batch(entities)
    if result[0]["anti_human_override"]:
        assert result[0]["search_archetype"] is not None

def test_ontology_fairy_tale_character():
    """Baba Yaga should be classified as folkloric, not human."""
    entities = [{"name": "Baba Yaga", "description": "A witch who lives in a hut on chicken legs in Russian folklore", "visual_type": "creature"}]
    result = classify_entities_batch(entities)
    assert result[0]["entity_class"] in {"folkloric", "fae", "mythical_beast", "human_supernatural"}
    # Must NOT be "human"
    assert result[0]["entity_class"] != "human"

def test_ontology_batch_preserves_order():
    """Output order must match input order."""
    entities = [
        {"name": "Alpha", "description": "A human detective", "visual_type": "man"},
        {"name": "Beta",  "description": "A robot assistant", "visual_type": "AI"},
    ]
    results = classify_entities_batch(entities)
    assert results[0]["name"] == "Alpha"
    assert results[1]["name"] == "Beta"
```

### `tests/unit/test_engine_selector.py`

```python
import pytest
from app.services.engine_selector import select_engines
from app.services.ontology_constants import ENTITY_PARENT

ALL_PROVIDERS = ["unsplash", "serpapi", "pexels", "openverse", "pixabay", "wikimedia", "deviantart"]

# --- Core routing ---

def test_ai_scifi_does_not_return_unsplash_first():
    """AI in sci-fi context should prefer pixabay/deviantart over unsplash."""
    result = select_engines("AI", "character", "sci-fi", ALL_PROVIDERS, {}, top_n=2)
    assert "unsplash" not in result, "Unsplash should not be selected for AI|sci-fi"

def test_human_fiction_returns_unsplash():
    result = select_engines("human", "character", "fiction", ALL_PROVIDERS, {}, top_n=2)
    assert "unsplash" in result

def test_historical_human_returns_wikimedia():
    result = select_engines("human", "character", "historical", ALL_PROVIDERS, {}, top_n=2)
    assert "wikimedia" in result

def test_fantasy_creature_returns_deviantart():
    result = select_engines("mythical_beast", "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    assert "deviantart" in result

# --- Parent class fallback ---

def test_demigod_falls_back_to_deity():
    """demigod not in matrix → should fall back to deity affinity."""
    result_demigod = select_engines("demigod", "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    result_deity   = select_engines("deity",   "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    assert set(result_demigod) == set(result_deity), "demigod should resolve same as deity"

def test_ghost_falls_back_to_spirit():
    result_ghost  = select_engines("ghost",  "character", "horror", ALL_PROVIDERS, {}, top_n=2)
    result_spirit = select_engines("spirit", "character", "horror", ALL_PROVIDERS, {}, top_n=2)
    assert set(result_ghost) == set(result_spirit)

def test_unknown_class_does_not_raise():
    """Completely unknown entity class must not raise an exception."""
    result = select_engines("unicorn_centaur_hybrid", "character", "fantasy", ALL_PROVIDERS, {}, top_n=2)
    assert len(result) >= 1  # Must return something

def test_result_only_contains_available_providers():
    limited = ["unsplash", "serpapi"]
    result = select_engines("AI", "character", "sci-fi", limited, {}, top_n=2)
    for p in result:
        assert p in limited

# --- Engine ratings modifier ---

def test_positive_rating_boosts_provider():
    ratings_neutral  = {}
    ratings_positive = {"pixabay": 5}
    result_neutral  = select_engines("AI", "character", "sci-fi", ALL_PROVIDERS, ratings_neutral,  top_n=3)
    result_positive = select_engines("AI", "character", "sci-fi", ALL_PROVIDERS, ratings_positive, top_n=3)
    # pixabay should rank at least as high with positive rating
    if "pixabay" in result_positive and "pixabay" in result_neutral:
        assert result_positive.index("pixabay") <= result_neutral.index("pixabay")

def test_negative_rating_does_not_eliminate_provider():
    """A provider with bad ratings should still appear if it's the best available."""
    ratings = {"pixabay": -5, "deviantart": -5}
    limited = ["pixabay"]
    result = select_engines("AI", "character", "sci-fi", limited, ratings, top_n=1)
    assert result == ["pixabay"], "Only available provider must still be returned"

def test_rating_clamped_at_minus_5():
    """net_score below -5 should behave identically to -5 (clamping)."""
    result_minus5   = select_engines("human", "character", "fiction", ALL_PROVIDERS, {"unsplash": -5},  top_n=2)
    result_minus100 = select_engines("human", "character", "fiction", ALL_PROVIDERS, {"unsplash": -100}, top_n=2)
    assert result_minus5 == result_minus100
```

### `tests/unit/test_query_diversification.py`

```python
import pytest
from app.services.search_service import _build_queries_diversified

BOOK_INFO_SCIFI = {"title": "I, Robot", "author": "Isaac Asimov", "is_well_known": True,
                   "style_category": "sci-fi", "known_adaptations": ["I Robot 2004 film"]}
BOOK_INFO_FICTION = {"title": "A Novel", "author": "Author", "is_well_known": False,
                     "style_category": "fiction", "known_adaptations": []}

ONTOLOGY_AI = {"entity_class": "android", "anti_human_override": True,
               "search_archetype": "boxy robot with glowing red eyes",
               "visual_markers": ["glowing red eyes", "parallelepiped shape", "metallic surface"]}
ONTOLOGY_HUMAN = {"entity_class": "human", "anti_human_override": False,
                  "search_archetype": None, "visual_markers": ["sharp eyes", "grey hair"]}

TOKENS_AI = {"core_tokens": ["robot", "metal", "industrial"], "style_tokens": ["dramatic lighting"],
             "archetype_tokens": ["mechanical construct", "android"], "anti_tokens": ["man portrait", "person"]}
TOKENS_HUMAN = {"core_tokens": ["elderly woman", "sharp eyes"], "style_tokens": ["cinematic"],
                "archetype_tokens": [], "anti_tokens": []}

def test_returns_multiple_queries():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert len(queries) >= 4, f"Expected ≥4 queries, got {len(queries)}: {queries}"

def test_no_human_terms_for_anti_human_entity():
    forbidden = {"man portrait", "woman portrait", "person portrait", "human portrait"}
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    for q in queries:
        for term in forbidden:
            assert term not in q.lower(), f"Human term '{term}' found in query for anti_human entity: '{q}'"

def test_all_queries_distinct():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert len(queries) == len(set(queries)), f"Duplicate queries found: {queries}"

def test_style_category_in_at_least_one_query():
    queries = _build_queries_diversified("character", "large robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert any("sci-fi" in q.lower() for q in queries), f"style_category not in any query: {queries}"

def test_well_known_book_includes_adaptation_query():
    queries = _build_queries_diversified("character", "robot", BOOK_INFO_SCIFI, TOKENS_AI, ONTOLOGY_AI)
    assert any("2004" in q or "film" in q for q in queries), \
        f"No adaptation query found for well-known book: {queries}"

def test_no_adaptation_query_for_unknown_book():
    queries = _build_queries_diversified("character", "detective", BOOK_INFO_FICTION, TOKENS_HUMAN, ONTOLOGY_HUMAN)
    assert not any("film" in q or "2004" in q for q in queries)

def test_human_character_returns_portrait_suffix():
    queries = _build_queries_diversified("character", "woman roboticist", BOOK_INFO_FICTION, TOKENS_HUMAN, ONTOLOGY_HUMAN)
    assert any("portrait" in q.lower() for q in queries), \
        f"Human character queries should include portrait: {queries}"

def test_location_query_contains_no_portrait():
    queries = _build_queries_diversified("location", "sprawling industrial complex", BOOK_INFO_SCIFI,
                                         TOKENS_AI, ONTOLOGY_AI)
    assert not any("portrait" in q.lower() for q in queries)
```

### `tests/unit/test_scene_extractor.py`

```python
import pytest
from app.services.scene_extractor import group_chunks_into_candidate_scenes

def make_chunk(idx, dramatic, density, chars, narrative_pos="rising_action"):
    return {
        "chunk_index": idx,
        "dramatic_score": dramatic,
        "visual_density": density,
        "characters_present": chars,
        "locations_present": ["Lab"],
        "narrative_position": narrative_pos,
    }

# Build a 20-chunk test corpus
CHUNKS_20 = (
    [make_chunk(i, 0.3, "low", ["Alice"]) for i in range(5)] +
    [make_chunk(i, 0.8, "high", ["Alice", "Bob"], "climax") for i in range(5, 10)] +
    [make_chunk(i, 0.4, "medium", ["Alice"]) for i in range(10, 15)] +
    [make_chunk(i, 0.9, "high", ["Alice", "Bob", "Carol"], "climax") for i in range(15, 20)]
)

def test_returns_correct_scene_count():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=3)
    # Should return scene_count * 1.2 = ~4 candidates (buffer for LLM)
    assert len(candidates) >= 3

def test_high_drama_chunks_selected_over_low():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=2)
    # All candidates should overlap with high-drama regions (chunks 5–9 and 15–19)
    for c in candidates:
        assert c["composite_score"] > 0.3, f"Low-drama window selected: {c}"

def test_no_overlapping_windows():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=4)
    ranges = [(c["chunk_start"], c["chunk_end"]) for c in candidates]
    for i, (s1, e1) in enumerate(ranges):
        for j, (s2, e2) in enumerate(ranges):
            if i == j:
                continue
            overlap = min(e1, e2) - max(s1, s2)
            window_min = min(e1 - s1, e2 - s2)
            assert overlap <= window_min * 0.5, \
                f"Windows {i} and {j} overlap too much: {s1}–{e1} vs {s2}–{e2}"

def test_each_window_covers_3_to_7_chunks():
    candidates = group_chunks_into_candidate_scenes(CHUNKS_20, scene_count=3)
    for c in candidates:
        span = c["chunk_end"] - c["chunk_start"] + 1
        assert 3 <= span <= 7, f"Window span {span} out of range 3–7"

def test_single_chunk_corpus_does_not_crash():
    single = [make_chunk(0, 0.9, "high", ["Alice", "Bob"])]
    result = group_chunks_into_candidate_scenes(single, scene_count=2)
    # Should return 0 or 1 candidates without raising
    assert isinstance(result, list)
```

### `tests/unit/test_provider_format_query.py`

```python
import pytest
from app.services.providers.pexels import PexelsProvider
from app.services.providers.pixabay import PixabayProvider
from app.services.providers.openverse import OpenverseProvider
from app.services.providers.wikimedia import WikimediaProvider
from app.services.providers.deviantart import DeviantArtProvider

RAW_QUERY = "holographic AI construct cyberpunk neon sci-fi"

def test_pixabay_uses_plus_separator():
    p = PixabayProvider()
    formatted = p.format_query(RAW_QUERY)
    assert "+" in formatted, f"Pixabay query should use + separator: '{formatted}'"
    assert " AND " not in formatted

def test_openverse_produces_formal_description():
    p = OpenverseProvider()
    formatted = p.format_query(RAW_QUERY)
    # Should be a clean phrase, no special characters
    assert len(formatted) > 0
    assert "+" not in formatted

def test_deviantart_wraps_with_site_filter():
    # DeviantArt queries are handled by SerpAPI with site filter
    p = DeviantArtProvider()
    formatted = p.format_query(RAW_QUERY)
    assert "deviantart" in formatted.lower(), \
        f"DeviantArt provider should include site filter: '{formatted}'"

def test_all_providers_return_nonempty_query():
    providers = [PexelsProvider(), PixabayProvider(), OpenverseProvider(),
                 WikimediaProvider(), DeviantArtProvider()]
    for p in providers:
        result = p.format_query(RAW_QUERY)
        assert result and len(result.strip()) > 0, \
            f"{p.name}.format_query() returned empty string"
```

---

## Integration Tests

### `tests/integration/test_full_analysis_pipeline.py`

```python
"""
Integration test: runs full run_full_analysis() against fixture chunks.
Uses real OpenAI calls (mark as slow / require API key).
"""
import json
import pytest
from app.services.ai_service import run_full_analysis
from app.services.ontology_constants import ENTITY_CLASSES

# Fixture: 15 chunks from I, Robot (pre-saved as JSON)
@pytest.fixture
def scifi_chunks():
    with open("tests/fixtures/sample_chunks_scifi.json") as f:
        return json.load(f)

@pytest.mark.slow
@pytest.mark.requires_api
def test_pipeline_produces_characters_with_ontology(scifi_chunks):
    result = run_full_analysis(scifi_chunks, scene_count=3)

    chars = result.get("main_characters", [])
    assert len(chars) >= 1, "Should find at least one character"

    for c in chars:
        assert "ontology" in c, f"Character {c['name']} missing ontology"
        assert c["ontology"]["entity_class"] in ENTITY_CLASSES
        assert "entity_visual_tokens" in c
        assert len(c["entity_visual_tokens"].get("core_tokens", [])) > 0

def test_robbie_robot_classified_as_non_human(scifi_chunks):
    """Robbie (I, Robot) must not be classified as human."""
    result = run_full_analysis(scifi_chunks, scene_count=3)
    chars = result.get("main_characters", [])
    robbie = next((c for c in chars if "robbie" in c["name"].lower()), None)
    if robbie:
        assert robbie["ontology"]["anti_human_override"] is True
        assert robbie["ontology"]["entity_class"] != "human"

@pytest.mark.slow
@pytest.mark.requires_api
def test_pipeline_produces_correct_scene_count(scifi_chunks):
    result = run_full_analysis(scifi_chunks, scene_count=3)
    scenes = result.get("scenes", [])
    assert len(scenes) == 3, f"Expected 3 scenes, got {len(scenes)}"

def test_scenes_have_required_fields(scifi_chunks):
    result = run_full_analysis(scifi_chunks, scene_count=3)
    for scene in result.get("scenes", []):
        assert scene.get("title"), f"Scene missing title: {scene}"
        assert scene.get("scene_prompt_draft"), f"Scene missing prompt: {scene}"
        assert "abstract" in scene.get("t2i_prompt_json", {}), \
            f"Scene missing abstract T2I prompt: {scene}"
        span = scene["chunk_end_index"] - scene["chunk_start_index"] + 1
        assert 3 <= span <= 7, f"Scene span {span} out of expected range"

@pytest.mark.slow
@pytest.mark.requires_api
def test_fairy_tale_characters_classified_correctly():
    """fairy_tale fixture: anthropomorphic animals and folkloric entities."""
    with open("tests/fixtures/sample_chunks_fairy_tale.json") as f:
        chunks = json.load(f)
    result = run_full_analysis(chunks, scene_count=2)
    for c in result.get("main_characters", []):
        assert c["ontology"]["entity_class"] in ENTITY_CLASSES
        # Fairy tale characters should NOT default to "human" unless truly human
        # (test is intentionally loose — just checks schema validity)
```

### `tests/integration/test_search_references.py`

```python
"""
Integration tests for search pipeline with new engine selection.
Some tests require live API keys — marked accordingly.
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.search_service import search_references_for_book

@pytest.mark.asyncio
async def test_search_uses_pixabay_for_android_scifi(db_session, book_android_scifi):
    """
    Given a book with an android character in sci-fi style,
    search should use pixabay (not unsplash) as primary provider.
    """
    calls = []

    async def mock_search(query, content_type, count):
        calls.append({"provider": "pixabay", "query": query})
        return [{"url": "http://pixabay.com/test.jpg", "width": 800, "height": 600, "source": "pixabay"}]

    with patch("app.services.providers.pixabay.PixabayProvider.search", mock_search):
        await search_references_for_book(book_android_scifi.id, db=db_session)

    assert any(c["provider"] == "pixabay" for c in calls), \
        "Pixabay should be called for android|sci-fi entity"

@pytest.mark.asyncio
async def test_anti_human_entity_queries_dont_contain_portrait(db_session, book_android_scifi):
    """All search queries for anti_human_override=True entities must not contain portrait."""
    captured_queries = []

    async def mock_search(query, content_type, count):
        captured_queries.append(query)
        return []

    with patch("app.services.providers.pixabay.PixabayProvider.search", mock_search), \
         patch("app.services.providers.serpapi.SerpApiProvider.search", mock_search):
        await search_references_for_book(book_android_scifi.id, db=db_session)

    for q in captured_queries:
        assert "portrait" not in q.lower(), \
            f"Portrait term found in query for non-human entity: '{q}'"

@pytest.mark.asyncio
async def test_engine_ratings_influence_provider_selection(db_session, book_fiction):
    """
    After setting negative ratings for unsplash, pexels should be selected instead.
    """
    from app.crud import update_engine_rating
    update_engine_rating(db_session, book_fiction.id, "unsplash", delta_likes=0, delta_dislikes=5)

    selected_providers = []
    async def mock_search(query, content_type, count):
        return []

    with patch("app.services.providers.pexels.PexelsProvider.search",
               side_effect=lambda q, ct, c: (selected_providers.append("pexels"), [])[1]):
        await search_references_for_book(book_fiction.id, db=db_session)

    assert "pexels" in selected_providers, \
        "Pexels should be elevated after unsplash gets negative ratings"
```

### `tests/integration/test_scene_api.py`

```python
"""API-level integration tests for Scene endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_scenes_returns_list(auth_headers, analyzed_book_id):
    response = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_scenes_each_has_required_fields(auth_headers, analyzed_book_id):
    response = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers)
    for scene in response.json():
        assert "id" in scene
        assert "title" in scene
        assert "scene_type" in scene
        assert "chunk_start_index" in scene
        assert "chunk_end_index" in scene
        assert "scene_prompt_draft" in scene
        assert "t2i_prompt_json" in scene
        assert "abstract" in scene["t2i_prompt_json"]
        assert "is_selected" in scene

def test_patch_scene_is_selected(auth_headers, analyzed_book_id):
    scenes = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers).json()
    scene_id = scenes[0]["id"]

    response = client.patch(
        f"/books/{analyzed_book_id}/scenes/{scene_id}",
        json={"is_selected": False},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["is_selected"] is False

    # Verify persistence
    updated = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers).json()
    updated_scene = next(s for s in updated if s["id"] == scene_id)
    assert updated_scene["is_selected"] is False

def test_patch_scene_prompt_draft(auth_headers, analyzed_book_id):
    scenes = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers).json()
    scene_id = scenes[0]["id"]
    new_prompt = "A tense confrontation in a dimly lit laboratory, wide angle shot"

    response = client.patch(
        f"/books/{analyzed_book_id}/scenes/{scene_id}",
        json={"scene_prompt_draft": new_prompt},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["scene_prompt_draft"] == new_prompt

def test_proposed_queries_includes_selected_scenes_only(auth_headers, analyzed_book_id):
    scenes = client.get(f"/books/{analyzed_book_id}/scenes", headers=auth_headers).json()

    # Deselect all scenes
    for scene in scenes:
        client.patch(f"/books/{analyzed_book_id}/scenes/{scene['id']}",
                     json={"is_selected": False}, headers=auth_headers)

    # Select one
    selected_id = scenes[0]["id"]
    client.patch(f"/books/{analyzed_book_id}/scenes/{selected_id}",
                 json={"is_selected": True}, headers=auth_headers)

    response = client.get(f"/books/{analyzed_book_id}/proposed-search-queries", headers=auth_headers)
    assert response.status_code == 200
    returned_scene_ids = [s["id"] for s in response.json().get("scenes", [])]
    assert selected_id in returned_scene_ids
    assert all(sid == selected_id for sid in returned_scene_ids)
```

### `tests/integration/test_engine_ratings.py`

```python
def test_engine_rating_like_increments_likes(auth_headers, analyzed_book_id):
    response = client.patch(
        f"/books/{analyzed_book_id}/engine-ratings",
        json={"provider": "pixabay", "action": "like"},
        headers=auth_headers
    )
    assert response.status_code == 200

    # Call twice more
    client.patch(f"/books/{analyzed_book_id}/engine-ratings",
                 json={"provider": "pixabay", "action": "like"}, headers=auth_headers)

    # Verify net_score
    response = client.get(f"/books/{analyzed_book_id}/engine-ratings", headers=auth_headers)
    ratings = {r["provider"]: r for r in response.json()}
    assert ratings["pixabay"]["likes"] >= 2
    assert ratings["pixabay"]["net_score"] >= 2

def test_engine_rating_dislike_decrements(auth_headers, analyzed_book_id):
    client.patch(f"/books/{analyzed_book_id}/engine-ratings",
                 json={"provider": "unsplash", "action": "dislike"}, headers=auth_headers)
    response = client.get(f"/books/{analyzed_book_id}/engine-ratings", headers=auth_headers)
    ratings = {r["provider"]: r for r in response.json()}
    assert ratings["unsplash"]["dislikes"] >= 1
    assert ratings["unsplash"]["net_score"] < 0

def test_engine_ratings_do_not_affect_other_books(auth_headers, analyzed_book_id, other_book_id):
    client.patch(f"/books/{analyzed_book_id}/engine-ratings",
                 json={"provider": "pixabay", "action": "like"}, headers=auth_headers)
    response = client.get(f"/books/{other_book_id}/engine-ratings", headers=auth_headers)
    ratings = {r["provider"]: r for r in response.json()}
    # other_book should have zero pixabay likes
    assert ratings.get("pixabay", {}).get("likes", 0) == 0

def test_rating_upsert_no_duplicate_rows(db_session, analyzed_book_id):
    from app.crud import update_engine_rating, get_engine_ratings
    update_engine_rating(db_session, analyzed_book_id, "pixabay", delta_likes=1, delta_dislikes=0)
    update_engine_rating(db_session, analyzed_book_id, "pixabay", delta_likes=1, delta_dislikes=0)
    ratings = get_engine_ratings(db_session, analyzed_book_id)
    # Should be one row, not two
    assert isinstance(ratings.get("pixabay"), int)
```

---

## Quality Metrics (Non-Automated)

These are manual review criteria to assess the *quality* of results,
not just correctness of code. Review after implementing each phase on real book data.

### After Phase 1 — Ontology Quality Check

Using "I, Robot" (Asimov) as test book:

| Character | Expected `entity_class` | Expected `anti_human_override` |
|---|---|---|
| Robbie | `android` or `robot` | `true` |
| Susan Calvin | `human` | `false` |
| Gregory Powell | `human` | `false` |
| NS-2 robots (Nestor) | `android` | `true` |

Pass if ≥ 3/4 are correct.

Using a fairy tale (e.g. "The Frog Prince"):

| Character | Expected `entity_class` |
|---|---|
| The Frog Prince | `human_transformed` or `shapeshifter` |
| The Princess | `human` |
| The Witch | `human_supernatural` or `folkloric` |

Pass if ≥ 2/3 are correct.

### After Phase 4 + 5 — Query Quality Spot-Check

For each of these entity + genre combinations, manually inspect the 4–5 generated queries
and confirm none contain humanising terms for non-human entities:

| Entity | Genre | Anti-humanising check |
|---|---|---|
| Robbie (robot) | sci-fi | No "man", "woman", "portrait" in any query |
| Dragon | fantasy | No "person", "portrait" in any query |
| Baba Yaga | folklore | Queries should suggest folkloric visual, not just "old woman" |
| George Weston | fiction | "portrait" or "man" should appear in at least one query |

### After Phase 7 — Scene Quality Check

For a 200-page novel with `scene_count=5`, manually verify:

- [ ] At least 3 of 5 scenes correspond to actual narrative peaks (not filler dialogue)
- [ ] All 5 scenes span different parts of the book (none clustered in one chapter)
- [ ] `scene_prompt_draft` describes a visually illustratable moment (not "they talked")
- [ ] `t2i_prompt_json.abstract` is 60–200 characters and contains visual keywords

### After Phase 8 — T2I Prompt Quality Check

For a scene containing a non-human character (e.g. Robbie the robot in a lab):

- [ ] `abstract` prompt does not describe a human figure where there should be a robot
- [ ] `composition_tokens` contains a camera angle or framing term
- [ ] The prompt would produce an on-genre image if submitted to a T2I model

---

## Test Fixtures — What to Prepare

```
tests/fixtures/
    sample_chunks_scifi.json        # 15 chunks from I, Robot — for Android/AI entity tests
    sample_chunks_fantasy.json      # 15 chunks with mythical, fae, creature entities
    sample_chunks_historical.json   # 15 chunks set in real historical period
    sample_chunks_fairy_tale.json   # 10 chunks with shapeshifter, folkloric, animal entities
    expected_ontologies.json        # Ground truth: {character_name: {entity_class, anti_human_override}}
    expected_scene_count.json       # {fixture: min_scenes_expected, max_scenes_expected}
```

Fixtures should be real text excerpts (or synthetic but realistic), pre-chunked to match
the `{chunk_index, text}` format expected by `run_full_analysis()`.

**Recommended source texts (public domain):**
- I, Robot (Asimov) — for sci-fi/android tests
- Grimm's Fairy Tales — for folkloric/shapeshifter/anthropomorphic_animal tests
- A Tale of Two Cities (Dickens) — for human|historical tests
- A Princess of Mars (Burroughs) — for alien_humanoid tests

