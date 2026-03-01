# YRead — Implementation Plan
## Four-Entity Model, Dual Workflow Paths, Cover Studio

**Based on:** `docs/codebase_snapshot.md` + approved architecture spec  
**Target:** Cursor Composer (Agent mode) — each phase is a self-contained instruction block  
**Testing:** pytest (backend, existing conventions); Vitest + Playwright (frontend, to be bootstrapped)

---

## How to Use This Document

Each phase has:
- **Scope** — exactly what changes
- **Files touched** — so Cursor knows the blast radius before starting
- **Implementation instructions** — precise enough to give to Cursor Composer
- **Unit test specs** — written as pytest test signatures + assertions
- **Dependency** — which phase must be complete first

Run phases in order. Do not skip. Some phases modify files created in earlier phases.

---

## Phase 1 — Data Model Foundation
**Dependency:** None  
**Files touched:** `backend/app/models.py`, `backend/app/database.py`, `backend/app/schemas.py`

### 1.1 New and modified SQLAlchemy models

#### books table — add columns
Add to the `Book` model class and the `_run_migrations()` function:
- `entity_activations` TEXT nullable — JSON array of strings, e.g. `["cover", "characters"]`. Controls which entity types are active on a cover_only book. Full_book books always treat all four as active.
- `genre` TEXT nullable — user-selected genre string (e.g. "fantasy", "sci-fi", "thriller", "literary_fiction", "childrens"). Drives genre-aware defaults.

Existing `workflow_type` column already exists with default `"full"`. Add migration to add `"cover_only"` as a valid value alongside `"full"` (rename semantics: old `"full"` = new `"full_book"`; keep backward compatible by treating `"full"` as `"full_book"` in all logic).

#### New table: `artefacts`
```python
class Artefact(Base):
    __tablename__ = "artefacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    name = Column(String, nullable=False)
    physical_description = Column(Text, nullable=True)
    symbolic_role = Column(Text, nullable=True)        # What it represents thematically
    narrative_function = Column(String, nullable=True) # Tool|MacGuffin|Symbol|Weapon|Token
    typical_contexts = Column(Text, nullable=True)     # Which characters use it, which scenes
    is_main = Column(Integer, default=0)
    visual_type = Column(String, nullable=True)
    is_well_known_entity = Column(Integer, default=0)
    canonical_search_name = Column(String, nullable=True)
    search_visual_analog = Column(Text, nullable=True)
    text_to_image_prompt = Column(Text, nullable=True)
    ontology_json = Column(Text, nullable=True)
    entity_visual_tokens_json = Column(Text, nullable=True)
    reference_image_url = Column(Text, nullable=True)
    selected_reference_urls = Column(Text, nullable=True)  # JSON array of strings
    visual_bible_images = Column(Text, nullable=True)      # JSON array of image paths
    visual_bible_depth = Column(Integer, nullable=True)    # 2, 3, or 4 images

# Indexes
Index("ix_artefacts_book_id", Artefact.book_id)
```

#### New table: `chunk_artefacts`
```python
class ChunkArtefact(Base):
    __tablename__ = "chunk_artefacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    artefact_id = Column(Integer, ForeignKey("artefacts.id"), nullable=False)
    UniqueConstraint("chunk_id", "artefact_id", name="uq_chunk_artefact")

Index("ix_chunk_artefacts_chunk_id", ChunkArtefact.chunk_id)
Index("ix_chunk_artefacts_artefact_id", ChunkArtefact.artefact_id)
```

#### New table: `scene_artefacts`
```python
class SceneArtefact(Base):
    __tablename__ = "scene_artefacts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    artefact_id = Column(Integer, ForeignKey("artefacts.id"), nullable=False)
    UniqueConstraint("scene_id", "artefact_id", name="uq_scene_artefact")
```

#### New table: `cover_analysis`
```python
class CoverAnalysis(Base):
    __tablename__ = "cover_analysis"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False, unique=True)
    thematic_statement = Column(Text, nullable=True)
    emotional_promise = Column(Text, nullable=True)
    dominant_motifs = Column(Text, nullable=True)        # JSON array of strings
    symbolic_anchors = Column(Text, nullable=True)       # JSON array of strings (1-2)
    cover_mood_keywords = Column(Text, nullable=True)    # JSON array of strings (5-8)
    genre_conventions = Column(Text, nullable=True)
    genre_subversion_opportunity = Column(Text, nullable=True)
    typography_direction = Column(Text, nullable=True)
    color_palette_direction = Column(Text, nullable=True) # JSON {dominant, accent, background}
    cover_t2i_prompt = Column(Text, nullable=True)
    cover_negative_prompt = Column(Text, nullable=True)
    cover_role_character_ids = Column(Text, nullable=True) # JSON array of character ids
    cover_role_location_ids = Column(Text, nullable=True)  # JSON array of location ids
    cover_role_artefact_ids = Column(Text, nullable=True)  # JSON array of artefact ids
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Index("ix_cover_analysis_book_id", CoverAnalysis.book_id)
```

#### New table: `visual_bible_entries`
```python
class VisualBibleEntry(Base):
    __tablename__ = "visual_bible_entries"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # "character"|"location"|"artefact"
    entity_id = Column(Integer, nullable=False)   # id in respective table
    angle_label = Column(String, nullable=True)   # e.g. "front", "3/4 left", "in-use"
    prompt_used = Column(Text, nullable=True)
    image_path = Column(Text, nullable=True)
    status = Column(String, default="pending")    # pending|generating|complete|failed
    is_approved = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

Index("ix_vb_entries_book_entity", VisualBibleEntry.book_id, VisualBibleEntry.entity_type, VisualBibleEntry.entity_id)
```

#### New table: `cover_concepts`
```python
class CoverConcept(Base):
    __tablename__ = "cover_concepts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    concept_index = Column(Integer, nullable=False)  # 1, 2, 3
    prompt_used = Column(Text, nullable=True)
    negative_prompt = Column(Text, nullable=True)
    style_variant = Column(String, nullable=True)  # photographic|illustrated|abstract|typographic
    image_path = Column(Text, nullable=True)
    status = Column(String, default="pending")
    is_selected = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

Index("ix_cover_concepts_book_id", CoverConcept.book_id)
```

#### Add relationships to existing models
- `Book`: add relationships `artefacts`, `cover_analysis`, `visual_bible_entries`, `cover_concepts` (all with cascade delete-orphan).
- `Chunk`: add `chunk_artefacts` relationship.
- `Scene`: add `scene_artefacts` relationship.

#### characters and locations — add columns
- `cover_role` INTEGER DEFAULT 0 — AI-suggested flag: this entity is a candidate for the cover image
- `visual_bible_depth` INTEGER nullable — AI-suggested number of VB images (3–6)

### 1.2 Migrations (_run_migrations additions)
Add to `_run_migrations()` in `database.py`:
```python
# Phase 1: Four-entity model
_add_column_if_missing("books", "entity_activations", "TEXT")
_add_column_if_missing("books", "genre", "TEXT")
_add_column_if_missing("characters", "cover_role", "INTEGER DEFAULT 0")
_add_column_if_missing("characters", "visual_bible_depth", "INTEGER")
_add_column_if_missing("locations", "cover_role", "INTEGER DEFAULT 0")
_add_column_if_missing("locations", "visual_bible_depth", "INTEGER")
# New tables are created via Base.metadata.create_all() — add models to Base before this call
```

### 1.3 New Pydantic schemas (`schemas.py`)
Add:
- `ArtefactResponse` — mirrors Artefact model fields; include `selected_reference_urls` deserialized as `list[str]`.
- `CoverAnalysisResponse` — mirrors CoverAnalysis; JSON fields deserialized.
- `CoverAnalysisUpdateRequest` — all fields optional (user edits).
- `VisualBibleEntryResponse` — mirrors VisualBibleEntry.
- `CoverConceptResponse` — mirrors CoverConcept.
- `AnalysisProgressResponse` — `{ entity_type: str, status: "pending"|"running"|"complete"|"failed" }[]` — replaces the current simple dict.
- `BookAnalyzeRequest` — add `entity_types: list[str] = ["cover", "characters", "locations", "artefacts"]` and `genre: str = ""`.
- Update `BookResponse` to include `entity_activations: list[str]`, `genre: str`.

### 1.4 Unit tests — Phase 1
File: `backend/tests/unit/test_models_phase1.py`

```python
def test_artefact_model_fields():
    # Instantiate Artefact with all fields; assert field names and defaults

def test_cover_analysis_model_fields():
    # Instantiate CoverAnalysis; assert JSON fields are Text (will be serialized)

def test_visual_bible_entry_defaults():
    # Assert status defaults to "pending", is_approved to 0

def test_cover_concept_defaults():
    # Assert status "pending", is_selected 0

def test_book_entity_activations_nullable():
    # Book with no entity_activations is valid

def test_artefact_response_schema_deserializes_selected_urls():
    # ArtefactResponse with selected_reference_urls='["url1","url2"]'
    # Assert parsed to list[str]

def test_book_analyze_request_defaults():
    # BookAnalyzeRequest() — entity_types defaults to all four
```

---

## Phase 2 — CRUD Extensions
**Dependency:** Phase 1  
**Files touched:** `backend/app/crud.py`

### 2.1 New CRUD functions

Add the following functions. Follow the exact naming and signature conventions already in `crud.py` (db: Session parameter, return model or None):

```python
# Artefacts
def create_artefact(db, book_id, name, physical_description, symbolic_role,
                    narrative_function, typical_contexts, is_main=0) -> Artefact

def get_artefacts_by_book(db, book_id) -> list[Artefact]

def get_artefact(db, artefact_id) -> Optional[Artefact]

def update_artefact(db, artefact_id, **kwargs) -> Optional[Artefact]
    # Accept any subset of artefact fields; call setattr for each; commit

def update_artefact_ontology(db, artefact_id, ontology_json, entity_visual_tokens_json,
                              visual_type, canonical_search_name, search_visual_analog,
                              text_to_image_prompt) -> Optional[Artefact]

def link_chunk_artefact(db, chunk_id, artefact_id) -> None
    # Insert ChunkArtefact if not exists (catch IntegrityError)

def link_scene_artefact(db, scene_id, artefact_id) -> None

# Cover Analysis
def create_or_update_cover_analysis(db, book_id, **fields) -> CoverAnalysis
    # Upsert: get by book_id, create if not exists, update all provided fields

def get_cover_analysis(db, book_id) -> Optional[CoverAnalysis]

# Visual Bible Entries
def create_visual_bible_entry(db, book_id, entity_type, entity_id,
                               angle_label, prompt_used=None) -> VisualBibleEntry

def get_visual_bible_entries(db, book_id, entity_type=None,
                              entity_id=None) -> list[VisualBibleEntry]

def update_visual_bible_entry(db, entry_id, **kwargs) -> Optional[VisualBibleEntry]

# Cover Concepts
def create_cover_concept(db, book_id, concept_index, prompt_used,
                          negative_prompt, style_variant) -> CoverConcept

def get_cover_concepts(db, book_id) -> list[CoverConcept]

def update_cover_concept(db, concept_id, **kwargs) -> Optional[CoverConcept]

def set_selected_cover_concept(db, book_id, concept_id) -> None
    # Set is_selected=0 for all book concepts, then is_selected=1 for concept_id

# Book entity activations
def update_book_entity_activations(db, book_id, entity_activations: list[str]) -> Book

def get_active_entity_types(db, book_id) -> list[str]:
    # If workflow_type == "full_book" (or "full"): return all four
    # Else: parse entity_activations JSON; default to ["cover"] if null
```

### 2.2 Extend existing CRUD
- `get_reference_images_for_entity`: currently filters by `entity_type IN ("character", "location")`. Extend to also accept `"artefact"` and `"cover"`.
- `trim_reference_images_fifo`: same extension.
- `create_reference_image`: no change needed (entity_type is a free string).
- `update_book`: add `entity_activations` and `genre` to accepted kwargs.

### 2.3 Unit tests — Phase 2
File: `backend/tests/unit/test_crud_phase2.py`

Use an in-memory SQLite session fixture:
```python
@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
```

```python
def test_create_artefact_and_retrieve(db):
    book = crud.create_book(db, title="Test", author="A")
    a = crud.create_artefact(db, book.id, "Magic Sword", ...)
    result = crud.get_artefacts_by_book(db, book.id)
    assert len(result) == 1
    assert result[0].name == "Magic Sword"

def test_update_artefact_partial(db):
    # Create, update only symbolic_role; assert other fields unchanged

def test_create_or_update_cover_analysis_upsert(db):
    # Call twice with same book_id; assert only one row exists
    # Second call updates thematic_statement; assert updated

def test_get_active_entity_types_full_book(db):
    book = crud.create_book(db, ...); book.workflow_type = "full_book"; db.commit()
    assert crud.get_active_entity_types(db, book.id) == ["cover","characters","locations","artefacts"]

def test_get_active_entity_types_cover_only_default(db):
    book = crud.create_book(db, ...); book.workflow_type = "cover_only"; db.commit()
    assert crud.get_active_entity_types(db, book.id) == ["cover"]

def test_get_active_entity_types_cover_only_activated(db):
    book = crud.create_book(db, ...); book.workflow_type = "cover_only"
    crud.update_book_entity_activations(db, book.id, ["cover", "characters"]); db.commit()
    assert "characters" in crud.get_active_entity_types(db, book.id)

def test_set_selected_cover_concept_exclusive(db):
    book = crud.create_book(db, ...)
    c1 = crud.create_cover_concept(db, book.id, 1, "prompt1", "", "illustrated")
    c2 = crud.create_cover_concept(db, book.id, 2, "prompt2", "", "abstract")
    crud.set_selected_cover_concept(db, book.id, c2.id)
    assert crud.get_cover_concept(db, c1.id).is_selected == 0
    assert crud.get_cover_concept(db, c2.id).is_selected == 1

def test_link_chunk_artefact_idempotent(db):
    # Link same pair twice; assert no IntegrityError and only one row

def test_visual_bible_entry_filter_by_entity(db):
    # Create entries for character and artefact; filter by entity_type="artefact"
    # Assert only artefact entries returned
```

---

## Phase 3 — Artefact Analysis Service
**Dependency:** Phases 1, 2  
**Files touched:** `backend/app/services/artefact_analysis_service.py` (new), `backend/app/services/ontology_service.py`, `backend/app/services/ontology_constants.py`

### 3.1 New file: `artefact_analysis_service.py`

This service follows the same structural patterns as `ai_service.py`: lazy `_client`, module-level prompt constants, public functions returning dicts, no DB access.

**Prompt: ARTEFACT_EXTRACTION_PROMPT**  
System prompt that instructs GPT to extract artefacts from chunk analyses. Key filtering rules to include verbatim in the prompt:
1. An artefact is an object that a character *acts upon or with* toward their goals
2. Must appear in at least 2 chunks OR be described with unusual visual detail
3. Must have narrative weight (not background furniture)
4. A location is where a scene is set; an artefact is what a character uses. If ambiguous, classify as location.
5. Return JSON array.

**Functions:**

```python
def extract_artefacts_from_chunks(
    chunk_analyses: list[dict],
    chunk_text_map: dict[int, str],
    manuscript_lang: str = "en",
    run_id: str = None
) -> list[dict]:
    """
    Single OpenAI call over a representative sample of chunk_analyses
    (e.g. top 30 by dramatic_score to keep token count bounded).
    
    Input chunk_analyses format: same as ai_service output (with characters_present,
    locations_present, visual_moment etc.)
    
    Returns list of dicts:
    {
        name: str,
        physical_description: str,
        symbolic_role: str,
        narrative_function: "Tool"|"MacGuffin"|"Symbol"|"Weapon"|"Token"|"Other",
        typical_contexts: str,  # "Used by [character] in [scene type] contexts"
        is_main: bool,          # True if appears 3+ times or has strong symbolic role
        chunks_present: list[int],  # chunk_index list
        scenes_present: list[str],  # scene title hints
        visual_type: str,       # "physical_object"|"magical_item"|"document"|"vehicle"|"other"
    }
    """

def build_artefact_visual_tokens_batch(artefacts: list[dict]) -> list[dict]:
    """
    Same pattern as ai_service.build_entity_visual_tokens_batch but with
    artefact-specific prompt tuned for objects (not people/places).
    
    Input: [{name, physical_description, symbolic_role, visual_type, ...}]
    Output same order: [{name, core_tokens, style_tokens, archetype_tokens, anti_tokens}]
    """

def run_artefact_analysis(
    chunks: list[dict],
    chunk_text_map: dict[int, str],
    manuscript_lang: str = "en",
    progress_callback=None,
    run_id: str = None
) -> dict:
    """
    Full artefact pipeline:
    1. extract_artefacts_from_chunks
    2. ontology_service.classify_entities_batch (with entity_role="artefact")
    3. build_artefact_visual_tokens_batch
    
    Returns: {
        artefacts: list[dict],  # merged output with ontology and visual tokens
    }
    """
```

### 3.2 Extend `ontology_service.py`

The existing `classify_entities_batch` takes `{name, description, visual_type, entity_role?}`. Add `"artefact"` as a valid `entity_role`. Extend `ontology_constants.py`:

Add artefact-specific entity classes:
```python
ARTEFACT_ENTITY_CLASSES = [
    "physical_weapon", "magical_weapon", "document_scroll", "vessel_container",
    "clothing_armour", "instrument_device", "vehicle", "magical_item",
    "natural_object", "symbolic_token", "other_artefact"
]
```

Add to `ENGINE_AFFINITY` in `ontology_constants.py` (used by `engine_selector.py`):
```python
# Artefact engine affinities
"physical_weapon": {"wikimedia": 1.4, "pexels": 1.2, "serpapi": 1.1},
"magical_item":    {"deviantart": 1.5, "serpapi": 1.3, "wikimedia": 1.1},
"document_scroll": {"wikimedia": 1.6, "pexels": 1.1},
"vehicle":         {"unsplash": 1.3, "pexels": 1.3, "wikimedia": 1.2},
"clothing_armour": {"wikimedia": 1.4, "deviantart": 1.3, "pexels": 1.1},
"instrument_device": {"unsplash": 1.3, "pexels": 1.2, "wikimedia": 1.2},
```

### 3.3 Unit tests — Phase 3
File: `backend/tests/unit/test_artefact_analysis.py`

```python
# All LLM calls mocked with unittest.mock.patch

def test_extract_artefacts_filters_background_objects():
    # Mock LLM to return a mix of valid artefacts and background items
    # Assert that items without narrative weight are excluded

def test_extract_artefacts_returns_correct_structure():
    # Mock LLM response; assert each result has name, physical_description,
    # narrative_function, is_main, chunks_present

def test_build_artefact_visual_tokens_batch_returns_same_order():
    # Input 3 artefacts; mock LLM; assert output list length == 3
    # Assert each has core_tokens, style_tokens

def test_run_artefact_analysis_calls_ontology_service():
    with patch("artefact_analysis_service.ontology_service.classify_entities_batch") as mock_ont:
        mock_ont.return_value = [{"entity_class": "magical_item", ...}]
        result = run_artefact_analysis(sample_chunks, {})
    mock_ont.assert_called_once()

def test_run_artefact_analysis_empty_book():
    # chunks list where no artefacts should be found
    # Assert result["artefacts"] == []

def test_ontology_artefact_entity_role_accepted():
    # classify_entities_batch with entity_role="artefact"
    # Assert no ValueError; valid entity_class returned

def test_engine_affinity_artefact_classes_present():
    from services.ontology_constants import ENGINE_AFFINITY
    assert "physical_weapon" in ENGINE_AFFINITY
    assert "magical_item" in ENGINE_AFFINITY
```

---

## Phase 4 — Cover Analysis Service
**Dependency:** Phases 1, 2  
**Files touched:** `backend/app/services/cover_analysis_service.py` (new)

### 4.1 New file: `cover_analysis_service.py`

Two-stage synthesis. Stateless (no DB). Follows same lazy `_client` pattern.

**Stage 1 prompt: COVER_THEMATIC_EXTRACTION_PROMPT**  
Full-manuscript thematic extraction. Instruct the model to identify:
- Dominant metaphors and recurring symbolic imagery
- The central emotional arc and promise
- Key motifs (objects, natural elements, concepts) that recur
- The central tension in one sentence

Input: concatenated chunk texts (or summarised chunks if >60k tokens — use the `narrative_summary` fields from scene_analyses as a proxy for long manuscripts).

**Stage 2 prompt: COVER_BRIEF_SYNTHESIS_PROMPT**  
Translate thematic extraction into structured cover design direction, incorporating genre conventions.

**Functions:**

```python
def _get_full_text_summary(chunk_analyses: list[dict]) -> str:
    """
    Build a summary suitable for full-book thematic reading.
    Concatenate narrative_summary fields from chunk_analyses (not raw text).
    Cap at ~12,000 tokens. If still too long, sample every Nth summary.
    """

def extract_thematic_material(
    chunk_analyses: list[dict],
    genre: str,
    run_id: str = None
) -> dict:
    """
    Stage 1 LLM call.
    Returns {
        dominant_motifs: list[str],
        symbolic_anchors: list[str],
        emotional_arc: str,
        recurring_imagery: list[str],
        central_tension: str,
        tone_words: list[str]
    }
    """

def synthesise_cover_brief(
    thematic_material: dict,
    genre: str,
    style_category: str,
    existing_characters: list[dict],  # [{name, is_main, cover_role_candidate}]
    existing_locations: list[dict],
    run_id: str = None
) -> dict:
    """
    Stage 2 LLM call.
    Returns full cover_analysis dict matching CoverAnalysis model fields:
    {
        thematic_statement, emotional_promise, dominant_motifs,
        symbolic_anchors, cover_mood_keywords, genre_conventions,
        genre_subversion_opportunity, typography_direction,
        color_palette_direction, cover_t2i_prompt, cover_negative_prompt,
        cover_role_character_ids_hints,  # names, not ids — caller resolves to ids
        cover_role_location_ids_hints,
        cover_role_artefact_ids_hints
    }
    """

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

def run_cover_analysis(
    chunk_analyses: list[dict],
    genre: str,
    style_category: str,
    existing_characters: list[dict],
    existing_locations: list[dict],
    progress_callback=None,
    run_id: str = None
) -> dict:
    """
    Orchestrates Stage 1 → Stage 2.
    Returns the cover_analysis dict ready for crud.create_or_update_cover_analysis.
    """
```

### 4.2 Genre-aware entity activation defaults

Add to a new `backend/app/services/genre_defaults.py`:
```python
GENRE_DEFAULT_ACTIVATIONS = {
    "fantasy":           ["cover", "characters", "locations", "artefacts"],
    "sci_fi":            ["cover", "characters", "locations"],
    "childrens":         ["cover", "characters"],
    "romance":           ["cover", "characters"],
    "thriller":          ["cover"],
    "mystery":           ["cover"],
    "literary_fiction":  ["cover"],
    "historical_fiction":["cover", "locations", "artefacts"],
    "default":           ["cover"],
}

def get_default_activations(genre: str, workflow_type: str) -> list[str]:
    if workflow_type in ("full_book", "full"):
        return ["cover", "characters", "locations", "artefacts"]
    return GENRE_DEFAULT_ACTIVATIONS.get(genre, GENRE_DEFAULT_ACTIVATIONS["default"])
```

### 4.3 Unit tests — Phase 4
File: `backend/tests/unit/test_cover_analysis.py`

```python
def test_get_full_text_summary_caps_tokens():
    # 200 chunk_analyses; assert output under 12000 tokens (tiktoken count)

def test_extract_thematic_material_structure(mock_openai):
    result = extract_thematic_material(sample_chunks, "fantasy")
    assert "dominant_motifs" in result
    assert isinstance(result["symbolic_anchors"], list)

def test_synthesise_cover_brief_includes_all_fields(mock_openai):
    result = synthesise_cover_brief(sample_thematic, "fantasy", "illustrated", [], [])
    required = ["thematic_statement", "emotional_promise", "cover_t2i_prompt",
                "typography_direction", "color_palette_direction", "cover_mood_keywords"]
    for field in required:
        assert field in result

def test_genre_conventions_map_covers_known_genres():
    assert "fantasy" in GENRE_COVER_CONVENTIONS
    assert "thriller" in GENRE_COVER_CONVENTIONS

def test_run_cover_analysis_calls_both_stages(mock_openai):
    with patch("cover_analysis_service.extract_thematic_material") as s1, \
         patch("cover_analysis_service.synthesise_cover_brief") as s2:
        s2.return_value = {"thematic_statement": "test", ...}
        run_cover_analysis(sample_chunks, "fantasy", "illustrated", [], [])
    s1.assert_called_once()
    s2.assert_called_once()

def test_genre_defaults_full_book_always_all_four():
    assert get_default_activations("thriller", "full_book") == \
        ["cover", "characters", "locations", "artefacts"]

def test_genre_defaults_cover_only_thriller():
    assert get_default_activations("thriller", "cover_only") == ["cover"]

def test_genre_defaults_cover_only_fantasy():
    result = get_default_activations("fantasy", "cover_only")
    assert "characters" in result and "locations" in result
```

---

## Phase 5 — Analysis Endpoint Extensions
**Dependency:** Phases 1–4  
**Files touched:** `backend/app/routers/books.py`, `backend/app/services/ai_service.py`

### 5.1 Extend `POST /api/books/{book_id}/analyze`

**Request body** (`BookAnalyzeRequest`) — add:
- `entity_types: list[str] = ["cover", "characters", "locations", "artefacts"]`
- `genre: str = ""`

**Background task `_run_analysis_background`** — refactor to:

```python
async def _run_analysis_background(book_id, req_dict, db_session_factory):
    """
    Runs entity analysis jobs based on entity_types in req_dict.
    Updates _analysis_progress per-entity.
    All jobs run concurrently (asyncio.gather or thread pool).
    
    For each requested entity_type:
    - "characters" + "locations": existing run_full_analysis path
      (but now also sets cover_role and visual_bible_depth on characters/locations)
    - "artefacts": artefact_analysis_service.run_artefact_analysis
      + crud operations to persist Artefacts, ChunkArtefacts, SceneArtefacts
    - "cover": cover_analysis_service.run_cover_analysis
      + crud.create_or_update_cover_analysis
    
    Updates book.entity_activations to include all successfully completed entity_types.
    Updates book.genre if provided in req_dict.
    """
```

**New `GET /api/books/{book_id}/analysis-progress`** response format — replace current simple `{current_chunk, total_chunks}` with:
```json
{
  "overall_status": "running"|"complete"|"failed"|"not_started",
  "entity_progress": {
    "characters": {"status": "complete", "current": 20, "total": 20},
    "locations":  {"status": "complete", "current": 20, "total": 20},
    "artefacts":  {"status": "running", "current": 8, "total": 20},
    "cover":      {"status": "pending", "current": 0, "total": 2}
  }
}
```

Extend in-memory `_analysis_progress` dict from `{book_id: {current, total}}` to:
```python
_analysis_progress: dict[int, dict] = {
    book_id: {
        "overall_status": str,
        "entity_progress": {
            entity_type: {"status": str, "current": int, "total": int}
        }
    }
}
```

### 5.2 New endpoint: `POST /api/books/{book_id}/analyze/entity`
For re-triggering a single entity type (e.g. user activates Artefacts mid-workflow):

```
POST /api/books/{book_id}/analyze/entity
Body: { entity_type: "artefacts" }
Response: 202 { status, message }
```

Fires same background logic as above but for a single entity type only. Preserves existing analysis results for other entity types.

### 5.3 New endpoints: Artefacts
Add to `books.py` router:

```
GET  /api/books/{book_id}/artefacts         → list[ArtefactResponse]
PUT  /api/books/{book_id}/artefacts/{id}    → ArtefactResponse  (user edits)
PUT  /api/books/{book_id}/entity-activations → StatusResponse
     Body: { entity_activations: list[str] }
```

### 5.4 New endpoints: Cover Analysis
Add to `visual_bible.py` router:

```
GET   /api/books/{book_id}/cover-analysis       → CoverAnalysisResponse (404 if not run)
PATCH /api/books/{book_id}/cover-analysis       → CoverAnalysisResponse (user edits all fields)
      Body: CoverAnalysisUpdateRequest (all fields optional)
```

### 5.5 Unit tests — Phase 5
File: `backend/tests/integration/test_analysis_phase5.py`

```python
@pytest.fixture(scope="module")
def client_with_book():
    # TestClient + upload + chunk; yield (client, book_id)

def test_analyze_with_entity_types_param(client_with_book):
    client, book_id = client_with_book
    r = client.post(f"/api/books/{book_id}/analyze",
                    json={"entity_types": ["cover"], "style_category": "illustrated"})
    assert r.status_code == 202

def test_analysis_progress_new_format(client_with_book):
    client, book_id = client_with_book
    # After analyze, poll progress
    r = client.get(f"/api/books/{book_id}/analysis-progress")
    assert r.status_code in (200, 404)  # 404 if not started
    if r.status_code == 200:
        data = r.json()
        assert "overall_status" in data
        assert "entity_progress" in data

def test_get_artefacts_empty_before_analysis(client_with_book):
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/artefacts")
    assert r.status_code == 200
    assert r.json() == []

def test_get_cover_analysis_404_before_analysis(client_with_book):
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/cover-analysis")
    assert r.status_code == 404

def test_patch_cover_analysis_updates_fields(client_with_book):
    # First create cover_analysis via crud directly in test setup
    client, book_id = client_with_book
    r = client.patch(f"/api/books/{book_id}/cover-analysis",
                     json={"thematic_statement": "A story about loss"})
    assert r.status_code == 200
    assert r.json()["thematic_statement"] == "A story about loss"

def test_update_entity_activations(client_with_book):
    client, book_id = client_with_book
    r = client.put(f"/api/books/{book_id}/entity-activations",
                   json={"entity_activations": ["cover", "characters"]})
    assert r.status_code == 200
    book_r = client.get(f"/api/books/{book_id}")
    assert "characters" in book_r.json()["entity_activations"]

def test_analyze_single_entity_endpoint(client_with_book):
    client, book_id = client_with_book
    r = client.post(f"/api/books/{book_id}/analyze/entity",
                    json={"entity_type": "artefacts"})
    assert r.status_code == 202
```

---

## Phase 6 — Search Service Extensions
**Dependency:** Phases 1–5  
**Files touched:** `backend/app/services/search_service.py`, `backend/app/services/engine_selector.py`, `backend/app/services/providers/` (new: `behance_provider.py`, `dribbble_provider.py`), `backend/app/routers/visual_bible.py`, `backend/app/.env.example`

### 6.1 New providers

**`behance_provider.py`**  
Uses SerpAPI with Behance-specific parameters (site search). Inherit from `BaseImageProvider`. Name: `"behance"`. `is_available()`: returns True if SERPAPI_KEY or SEARCH_API_KEY is set (same key as serpapi_provider). `search(query, content_type, count)`: calls SerpAPI with `q="{query} site:behance.net"` or equivalent SerpAPI tbm parameter. Returns normalized dicts with `provider="behance"`.

**`dribbble_provider.py`**  
Same pattern. Name: `"dribbble"`. SerpAPI query: `"{query} site:dribbble.com"`.

Add both to `ALL_PROVIDERS` list in `settings.py` router and to `engine_selector.py` affinity maps.

### 6.2 Add `"cover"` and `"artefact"` entity types to search_service

`search_references_for_book` currently handles `characters` and `locations`. Extend to also handle `artefacts` and `cover`:

```python
# Add to search_references_for_book signature:
search_entity_types: str = "all"  # "characters"|"locations"|"artefacts"|"cover"|"all"

# Add artefact search loop mirroring character/location loops:
# - Get artefacts from crud.get_artefacts_by_book
# - Build queries from entity tokens (same _build_queries_diversified logic)
# - Call _search_entity
# - Persist to reference_images with entity_type="artefact"

# Add cover search:
# - Get cover_analysis from crud.get_cover_analysis
# - Build cover-specific queries from symbolic_anchors + cover_mood_keywords + genre
# - Use cover-specific provider mix: behance, dribbble, unsplash (atmospheric)
# - Persist to reference_images with entity_type="cover", entity_id=cover_analysis.id
```

### 6.3 Extend `get_proposed_search_queries`

Return shape becomes:
```python
{
    "characters": [...],   # existing
    "locations": [...],    # existing
    "artefacts": [...],    # new — same shape as characters/locations
    "cover": {             # new — single object, not list
        "proposed_queries": list[str],  # derived from symbolic_anchors + mood_keywords
        "cover_analysis_summary": str,  # thematic_statement for display
    }
}
```

### 6.4 Extend `reference-results` endpoint and `visual-bible/approve`

`GET /api/books/{book_id}/reference-results` — extend response to include:
```json
{
  "characters": {...},
  "locations": {...},
  "artefacts": {"entity_name": [images]},
  "cover": {"cover": [images]}
}
```

`POST /api/books/{book_id}/visual-bible/approve` — extend `VisualBibleApproveRequest`:
```python
character_selections: dict[str, list[str]]
location_selections: dict[str, list[str]]
artefact_selections: dict[str, list[str]]   # new
cover_selections: list[str]                  # new — selected cover reference URLs
```

Update `reference-upload` endpoint to accept `entity_type = "artefact"|"cover"`.

### 6.5 Extend `engine_selector.py`

Add cover entity type handling:
```python
# Cover always uses behance + dribbble + unsplash as primary
# genre parameter used for query tuning, not provider selection
COVER_PROVIDERS = ["behance", "dribbble", "unsplash", "serpapi"]
```

In `select_engines`, when `entity_type == "cover"`, bypass affinity matrix and return `COVER_PROVIDERS` filtered by `available_providers`.

### 6.6 Unit tests — Phase 6
File: `backend/tests/unit/test_search_phase6.py`

```python
def test_behance_provider_available_with_serpapi_key(monkeypatch):
    monkeypatch.setenv("SERPAPI_KEY", "test_key")
    provider = BehanceProvider()
    assert provider.is_available() is True

def test_dribbble_provider_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)
    provider = DribbbleProvider()
    assert provider.is_available() is False

def test_select_engines_cover_returns_cover_providers():
    engines = select_engines("cover", "cover", "illustrated",
                             ["behance","dribbble","unsplash","pexels"],
                             engine_ratings=[])
    assert "behance" in engines or "dribbble" in engines

def test_select_engines_artefact_physical_weapon():
    engines = select_engines("physical_weapon", "artefact", "historical",
                             ["wikimedia","pexels","unsplash"], engine_ratings=[])
    assert "wikimedia" in engines

def test_get_proposed_search_queries_includes_artefacts(mock_db_with_artefacts):
    result = get_proposed_search_queries(1, mock_db_with_artefacts)
    assert "artefacts" in result
    assert "cover" in result

def test_search_references_for_book_artefact_entity_type(mock_db):
    # Mock all providers; set search_entity_types="artefacts"
    result = search_references_for_book(1, db=mock_db, search_entity_types="artefacts")
    assert "artefacts" in result
    assert "characters" not in result or result["characters"] == []
```

---

## Phase 7 — Visual Bible Entries Endpoints and Cover Studio
**Dependency:** Phases 1, 2, 6  
**Files touched:** `backend/app/routers/visual_bible.py`, `backend/app/routers/illustrations.py` (currently empty stub), `backend/app/services/t2i_providers/`

### 7.1 Visual Bible Entries endpoints (add to `visual_bible.py`)

```
GET  /api/books/{book_id}/visual-bible/entries
     Query: entity_type? entity_id?
     → list[VisualBibleEntryResponse]

POST /api/books/{book_id}/visual-bible/entries/generate
     Body: { entity_type, entity_id, angle_label, prompt? }
     → VisualBibleEntryResponse (202 — background T2I)
     Creates entry with status=pending; fires background T2I task (stub for now)

POST /api/books/{book_id}/visual-bible/entries/generate-all
     Body: { entity_type? }  # optional filter; default all active entities
     → { queued: int, entries: list[VisualBibleEntryResponse] }
     Creates all entries for all entities based on visual_bible_depth; queues T2I

PATCH /api/books/{book_id}/visual-bible/entries/{entry_id}
      Body: { is_approved?, image_path?, status? }
      → VisualBibleEntryResponse
```

The T2I generation background task in `generate` and `generate-all` calls `t2i_providers/abstract_provider.py` which is still a stub — this is acceptable for now. The endpoint architecture is real; the T2I call is the stub.

**VB depth calculator** (add as helper function in `visual_bible.py` router or a utility module):
```python
def get_vb_angles(entity_type: str, visual_bible_depth: int, is_main: bool) -> list[str]:
    """Returns ordered list of angle labels based on entity type and depth."""
    CHARACTER_ANGLES = ["front", "3/4 left", "3/4 right", "profile", "action pose", "close-up face"]
    LOCATION_ANGLES = ["exterior wide", "interior", "atmospheric detail", "establishing shot"]
    ARTEFACT_ANGLES = ["front", "back", "detail/open", "in-use context"]
    
    depth = visual_bible_depth or (6 if is_main else 3)
    if entity_type == "character":
        return CHARACTER_ANGLES[:depth]
    elif entity_type == "location":
        return LOCATION_ANGLES[:min(depth, 4)]
    elif entity_type == "artefact":
        return ARTEFACT_ANGLES[:min(depth, 4)]
    return []
```

### 7.2 Cover Studio endpoints (add to `illustrations.py` — currently empty)

```
GET  /api/books/{book_id}/cover-concepts
     → list[CoverConceptResponse]

POST /api/books/{book_id}/cover-concepts/generate
     Body: {
         prompt?: str,          # override auto prompt from cover_analysis
         negative_prompt?: str,
         style_variant?: str,   # photographic|illustrated|abstract|typographic
         concept_count?: int    # default 3
     }
     → { queued: int, concepts: list[CoverConceptResponse] }
     Creates concept_count entries with status=pending; fires T2I stub per concept

PATCH /api/books/{book_id}/cover-concepts/{concept_id}
      Body: { is_selected?, prompt_used?, style_variant? }
      → CoverConceptResponse

POST /api/books/{book_id}/cover-concepts/{concept_id}/select
     → StatusResponse
     Calls crud.set_selected_cover_concept; returns 200
```

### 7.3 Unit tests — Phase 7
File: `backend/tests/integration/test_visual_bible_phase7.py`

```python
def test_get_vb_angles_character_main():
    angles = get_vb_angles("character", 6, is_main=True)
    assert len(angles) == 6
    assert "front" in angles

def test_get_vb_angles_artefact_secondary():
    angles = get_vb_angles("artefact", 2, is_main=False)
    assert len(angles) == 2

def test_generate_vb_entries_creates_correct_count(client_with_analysis):
    client, book_id = client_with_analysis
    r = client.post(f"/api/books/{book_id}/visual-bible/entries/generate-all")
    assert r.status_code == 200
    data = r.json()
    assert data["queued"] > 0

def test_get_vb_entries_filter_by_entity_type(client_with_entries):
    client, book_id = client_with_entries
    r = client.get(f"/api/books/{book_id}/visual-bible/entries?entity_type=artefact")
    assert all(e["entity_type"] == "artefact" for e in r.json())

def test_patch_vb_entry_approve(client_with_entries):
    client, book_id = client_with_entries
    entries = client.get(f"/api/books/{book_id}/visual-bible/entries").json()
    entry_id = entries[0]["id"]
    r = client.patch(f"/api/books/{book_id}/visual-bible/entries/{entry_id}",
                     json={"is_approved": 1})
    assert r.json()["is_approved"] == 1

def test_generate_cover_concepts_creates_3(client_with_cover_analysis):
    client, book_id = client_with_cover_analysis
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate",
                    json={"concept_count": 3})
    assert r.status_code == 200
    assert r.json()["queued"] == 3

def test_select_cover_concept_exclusive(client_with_concepts):
    client, book_id = client_with_concepts
    concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
    c1_id, c2_id = concepts[0]["id"], concepts[1]["id"]
    client.post(f"/api/books/{book_id}/cover-concepts/{c1_id}/select")
    client.post(f"/api/books/{book_id}/cover-concepts/{c2_id}/select")
    r = client.get(f"/api/books/{book_id}/cover-concepts")
    selected = [c for c in r.json() if c["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["id"] == c2_id
```

---

## Phase 8 — Frontend: Bootstrap Testing + BookContext Extensions
**Dependency:** Phases 1–7 (backend must be stable)  
**Files touched:** `frontend/package.json`, `frontend/vitest.config.ts` (new), `frontend/src/context/BookContext.tsx`, `frontend/src/services/api.ts`

### 8.1 Bootstrap frontend testing (Vitest + Playwright)

Add to `package.json` devDependencies:
```json
"vitest": "^1.6.0",
"@testing-library/react": "^16.0.0",
"@testing-library/user-event": "^14.5.0",
"@vitejs/plugin-react": "^4.3.0",
"jsdom": "^24.0.0",
"@playwright/test": "^1.44.0",
"msw": "^2.3.0"
```

Add `test` and `test:e2e` scripts to package.json.

Create `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  }
})
```

Create `frontend/src/test/setup.ts`:
```typescript
import '@testing-library/jest-dom'
import { server } from './mocks/server'
beforeAll(() => server.listen())
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
```

Create `frontend/src/test/mocks/server.ts` — MSW service worker mock server with handlers for all API endpoints returning fixture data.

### 8.2 Extend `BookContext.tsx`

Add to context state:
```typescript
// New entity state
artefacts: Artefact[]
setArtefacts: (a: Artefact[]) => void
coverAnalysis: CoverAnalysis | null
setCoverAnalysis: (c: CoverAnalysis | null) => void

// Path and activation
workflowType: 'cover_only' | 'full_book'
setWorkflowType: (t: 'cover_only' | 'full_book') => void
activeEntityTypes: string[]     // ["cover", "characters", ...]
setActiveEntityTypes: (types: string[]) => void
genre: string
setGenre: (g: string) => void

// Analysis progress (new per-entity format)
analysisProgress: EntityProgress | null   // EntityProgress shape matches Phase 5 API
setAnalysisProgress: (p: EntityProgress | null) => void

// Visual bible entries
visualBibleEntries: VisualBibleEntry[]
setVisualBibleEntries: (e: VisualBibleEntry[]) => void

// Cover concepts
coverConcepts: CoverConcept[]
setCoverConcepts: (c: CoverConcept[]) => void
```

Add TypeScript interfaces matching all new schemas from Phase 1 schemas.py.

### 8.3 Extend `api.ts`

Add the following functions following existing axios conventions:

```typescript
// Artefacts
getArtefacts(bookId: number): Promise<Artefact[]>
updateArtefact(bookId: number, artefactId: number, data: Partial<Artefact>): Promise<Artefact>

// Entity activations
updateEntityActivations(bookId: number, entityActivations: string[]): Promise<void>

// Analysis — per-entity trigger
analyzeEntity(bookId: number, entityType: string): Promise<void>

// Cover analysis
getCoverAnalysis(bookId: number): Promise<CoverAnalysis>
updateCoverAnalysis(bookId: number, data: Partial<CoverAnalysis>): Promise<CoverAnalysis>

// Visual bible entries
getVisualBibleEntries(bookId: number, entityType?: string): Promise<VisualBibleEntry[]>
generateVisualBibleEntry(bookId: number, data: GenerateEntryRequest): Promise<VisualBibleEntry>
generateAllVisualBibleEntries(bookId: number, entityType?: string): Promise<GenerateAllResult>
updateVisualBibleEntry(bookId: number, entryId: number, data: Partial<VisualBibleEntry>): Promise<VisualBibleEntry>

// Cover concepts
getCoverConcepts(bookId: number): Promise<CoverConcept[]>
generateCoverConcepts(bookId: number, data: GenerateConceptsRequest): Promise<GenerateConceptsResult>
updateCoverConcept(bookId: number, conceptId: number, data: Partial<CoverConcept>): Promise<CoverConcept>
selectCoverConcept(bookId: number, conceptId: number): Promise<void>

// Extended existing
searchReferences(bookId: number, params: SearchReferencesRequest): Promise<SearchReferencesResult>
// extend SearchReferencesRequest: search_entity_types includes "artefacts"|"cover"
getReferenceResults(bookId: number): Promise<ReferenceResultsResponse>
// extend ReferenceResultsResponse to include artefacts and cover keys
approveVisualBible(bookId: number, data: VisualBibleApproveRequest): Promise<void>
// extend to include artefact_selections and cover_selections
```

Remove dead functions: `getProgress`, `updateProgress` (they have no backend; flagged as stubs in snapshot).

### 8.4 Frontend unit tests — Phase 8
File: `frontend/src/test/BookContext.test.tsx`

```typescript
describe('BookContext', () => {
  test('default workflowType is cover_only', () => {
    // render provider; assert context value
  })

  test('activeEntityTypes defaults to ["cover"] for cover_only', () => {})

  test('setActiveEntityTypes updates context', () => {
    // act: call setActiveEntityTypes(["cover", "characters"])
    // assert: activeEntityTypes contains both
  })

  test('reset clears artefacts and coverAnalysis', () => {})
})
```

File: `frontend/src/test/api.test.ts`

```typescript
describe('api', () => {
  test('getArtefacts calls correct endpoint', async () => {
    server.use(http.get('/api/books/1/artefacts', () => HttpResponse.json([])))
    const result = await getArtefacts(1)
    expect(result).toEqual([])
  })

  test('getCoverAnalysis throws on 404', async () => {
    server.use(http.get('/api/books/1/cover-analysis', () => new HttpResponse(null, {status: 404})))
    await expect(getCoverAnalysis(1)).rejects.toThrow()
  })

  test('updateEntityActivations posts correct body', async () => {
    let body: unknown
    server.use(http.put('/api/books/1/entity-activations', async ({request}) => {
      body = await request.json()
      return HttpResponse.json({status: 'ok'})
    }))
    await updateEntityActivations(1, ["cover", "characters"])
    expect(body).toEqual({entity_activations: ["cover", "characters"]})
  })
})
```

---

## Phase 9 — Frontend: SetupPage + WorkflowNav
**Dependency:** Phase 8  
**Files touched:** `frontend/src/pages/SetupPage.tsx`, `frontend/src/components/WorkflowNav.tsx`, `frontend/src/App.tsx`

### 9.1 SetupPage — add workflow path selection

Below the existing style/genre selectors, add a clearly labelled choice:

```typescript
// New UI section: "What do you want to create?"
// Two radio cards:
// [Book Cover]  — "Generate a KDP-ready cover. Fastest path."
// [Full Book]   — "Cover + interior illustrations + reading view."
// 
// On selection: setWorkflowType(value); setGenre(selectedGenre)
// On genre change: call getDefaultActivations(genre, workflowType) from genre_defaults
// and setActiveEntityTypes(defaults) — this is a frontend-side utility function
// mirroring the backend genre_defaults.py logic

// Add genre selector to the form (currently style_category exists but no genre field)
// Map genre → default entity activations on the frontend:
const GENRE_DEFAULT_ACTIVATIONS: Record<string, string[]> = {
  fantasy: ["cover", "characters", "locations", "artefacts"],
  sci_fi: ["cover", "characters", "locations"],
  childrens: ["cover", "characters"],
  // ... mirror backend genre_defaults.py
}
```

Update the `BookAnalyzeRequest` sent to the backend to include `entity_types` and `genre`.

### 9.2 WorkflowNav — dual path support

The current `WorkflowNav` has hardcoded step links. Refactor to derive steps from `workflowType` and `activeEntityTypes` from context:

```typescript
// Cover-Only steps:
const COVER_ONLY_STEPS = [
  { label: "Upload",      path: "manuscript-upload" },
  { label: "AI Analysis", path: "analysis-review" },
  { label: "Mood Board",  path: "mood-board" },
  { label: "Cover Studio",path: "studio/cover" },
  { label: "Preview",     path: "preview" },
]

// Full Book steps:
const FULL_BOOK_STEPS = [
  { label: "Upload",        path: "manuscript-upload" },
  { label: "AI Analysis",   path: "analysis-review" },
  { label: "Mood Board",    path: "mood-board" },
  { label: "Visual Bible",  path: "visual-bible" },
  { label: "Studio",        path: "studio" },
  { label: "Preview",       path: "preview" },
]

// Each step also shows a per-entity completion indicator using analysisProgress from context
```

### 9.3 App.tsx routing — add new routes

```typescript
// Add to books/:bookId routes:
{ path: "mood-board",         element: <MoodBoardPage /> }
{ path: "studio",             element: <StudioPage /> }
{ path: "studio/cover",       element: <CoverStudioPage /> }
{ path: "studio/text",        element: <TextStudioPage /> }

// Keep existing routes for backward compatibility:
// review-search, review-search-result, visual-bible remain but WorkflowNav
// no longer links to review-search (it's now a panel inside mood-board)
```

### 9.4 Frontend unit tests — Phase 9
File: `frontend/src/test/WorkflowNav.test.tsx`

```typescript
describe('WorkflowNav', () => {
  test('renders cover_only steps when workflowType is cover_only', () => {
    renderWithContext(<WorkflowNav />, { workflowType: 'cover_only' })
    expect(screen.getByText('Cover Studio')).toBeInTheDocument()
    expect(screen.queryByText('Visual Bible')).not.toBeInTheDocument()
  })

  test('renders full_book steps when workflowType is full_book', () => {
    renderWithContext(<WorkflowNav />, { workflowType: 'full_book' })
    expect(screen.getByText('Visual Bible')).toBeInTheDocument()
    expect(screen.getByText('Studio')).toBeInTheDocument()
  })
})
```

File: `frontend/src/test/SetupPage.test.tsx`

```typescript
test('selecting fantasy genre activates characters and locations', async () => {
  render(<SetupPage />)
  await userEvent.selectOptions(screen.getByLabelText(/genre/i), 'fantasy')
  // Check that the context setActiveEntityTypes was called with fantasy defaults
})

test('selecting full_book workflow shows all entity type toggles', async () => {
  render(<SetupPage />)
  await userEvent.click(screen.getByLabelText(/full book/i))
  expect(screen.getByText(/artefacts/i)).toBeInTheDocument()
})
```

---

## Phase 10 — Frontend: AnalysisReviewPage Refactor
**Dependency:** Phase 9  
**Files touched:** `frontend/src/pages/AnalysisReviewPage.tsx`

### 10.1 Four-tab structure

Refactor `AnalysisReviewPage` from its current flat entity tables into a tabbed interface:

```typescript
// Tabs: Cover | Characters | Locations | Artefacts
// 
// Tab visibility:
// - Cover: always visible (always active)
// - Characters/Locations/Artefacts: visible always, but show activation toggle
//   if entity type is not in activeEntityTypes (cover_only path)
//   Full book path: all active and populated

// Cover tab contents:
// - Display CoverAnalysis fields in editable form:
//   thematic_statement (textarea), emotional_promise (textarea),
//   dominant_motifs (tag list, editable), symbolic_anchors (tag list),
//   cover_mood_keywords (tag list), typography_direction (text),
//   color_palette_direction (3 colour pickers or text),
//   genre_conventions (readonly, informational), cover_t2i_prompt (textarea),
//   cover_negative_prompt (textarea)
// - "Entities on cover" section: checkboxes over characters/locations/artefacts
//   to set cover_role flag
// - Save button → PATCH /cover-analysis

// Characters tab: existing UI (entity table, is_main toggles, visual tokens)
// Locations tab: same
// Artefacts tab: new — same pattern as characters/locations
//   Fields: name, physical_description, symbolic_role, narrative_function,
//           typical_contexts, is_main toggle

// Per-tab progress indicator using analysisProgress from context
// If entity not yet analysed: show "Run analysis for [Entity]" button
//   → calls api.analyzeEntity(bookId, entityType)

// Remove scenes tab from this page (scenes are for internal use; 
// not user-facing in the revised UX)
```

### 10.2 Frontend unit tests — Phase 10
File: `frontend/src/test/AnalysisReviewPage.test.tsx`

```typescript
test('shows Cover tab by default', () => {
  renderWithMockData(<AnalysisReviewPage />)
  expect(screen.getByRole('tab', {name: /cover/i})).toHaveAttribute('aria-selected', 'true')
})

test('cover tab renders thematic_statement field', () => {
  renderWithMockData(<AnalysisReviewPage />, {coverAnalysis: mockCoverAnalysis})
  expect(screen.getByLabelText(/thematic statement/i)).toBeInTheDocument()
})

test('inactive entity tab shows activation toggle', () => {
  renderWithMockData(<AnalysisReviewPage />, {
    workflowType: 'cover_only',
    activeEntityTypes: ['cover']
  })
  fireEvent.click(screen.getByRole('tab', {name: /artefacts/i}))
  expect(screen.getByText(/activate artefacts/i)).toBeInTheDocument()
})

test('clicking activate entity calls analyzeEntity', async () => {
  const spy = vi.spyOn(api, 'analyzeEntity').mockResolvedValue(undefined)
  renderWithMockData(<AnalysisReviewPage />, {workflowType: 'cover_only', activeEntityTypes: ['cover']})
  fireEvent.click(screen.getByRole('tab', {name: /characters/i}))
  await userEvent.click(screen.getByText(/activate characters/i))
  expect(spy).toHaveBeenCalledWith(expect.any(Number), 'characters')
})

test('artefacts tab renders artefact list', () => {
  renderWithMockData(<AnalysisReviewPage />, {artefacts: [mockArtefact]})
  fireEvent.click(screen.getByRole('tab', {name: /artefacts/i}))
  expect(screen.getByText(mockArtefact.name)).toBeInTheDocument()
})
```

---

## Phase 11 — Frontend: MoodBoardPage
**Dependency:** Phase 10  
**Files touched:** `frontend/src/pages/MoodBoardPage.tsx` (new), `frontend/src/App.tsx`

### 11.1 New `MoodBoardPage.tsx`

This replaces the workflow function of `ReviewSearchPage` + `ReviewSearchResultPage`. Those pages remain in the codebase (their routes still resolve) but the WorkflowNav no longer links to them.

**Structure:**
```typescript
// Tabs: Cover | Characters | Locations | Artefacts
// Only active entity types render populated tabs; inactive tabs show activation CTA

// Per-tab layout:
// TOP: Collapsible "Search Queries" panel
//   - Shows proposed queries for this entity type from GET /proposed-search-queries
//   - Each query is an editable text input
//   - "Re-run search for [Entity Type]" button (calls searchReferences with entity type filter)
//   - Provider selector (which providers to use for this tab's entity type)
//
// MAIN: Image grid per entity
//   - Group by entity name (character name, location name, etc.)
//   - Each group: horizontal scroll of reference image cards
//   - Image card: thumbnail, source badge, select checkbox
//   - Selected images highlighted; count badge on entity name
//   - "Upload your own" button per entity → calls reference-upload
//
// BOTTOM: "Save Mood Board" button
//   - Calls POST /visual-bible/approve with all current selections
//   - Navigates to next step

// Cover tab specifics:
//   - No "per entity" grouping — single pool of cover reference images
//   - Image sources include behance/dribbble badges
//   - Atmospheric photography, design reference thumbnails

// On mount:
//   - GET /reference-results (loads existing selections)
//   - If no results: auto-trigger GET /proposed-search-queries
//     then show "Run Search" CTA per tab (don't auto-run)
```

### 11.2 Frontend unit tests — Phase 11
File: `frontend/src/test/MoodBoardPage.test.tsx`

```typescript
test('renders four tabs', () => {
  render(<MoodBoardPage />)
  expect(screen.getByRole('tab', {name: /cover/i})).toBeInTheDocument()
  expect(screen.getByRole('tab', {name: /characters/i})).toBeInTheDocument()
  expect(screen.getByRole('tab', {name: /locations/i})).toBeInTheDocument()
  expect(screen.getByRole('tab', {name: /artefacts/i})).toBeInTheDocument()
})

test('search queries panel is collapsed by default', () => {
  render(<MoodBoardPage />)
  expect(screen.queryByRole('textbox', {name: /query/i})).not.toBeVisible()
})

test('expanding search queries panel shows editable queries', async () => {
  renderWithMocks(<MoodBoardPage />, {proposedQueries: mockQueries})
  await userEvent.click(screen.getByText(/search queries/i))
  expect(screen.getByDisplayValue(mockQueries.cover.proposed_queries[0])).toBeInTheDocument()
})

test('selecting image highlights it', async () => {
  renderWithMocks(<MoodBoardPage />, {referenceResults: mockResults})
  const img = screen.getAllByRole('img')[0]
  await userEvent.click(img)
  expect(img.closest('[data-selected]')).toHaveAttribute('data-selected', 'true')
})

test('save mood board calls approveVisualBible', async () => {
  const spy = vi.spyOn(api, 'approveVisualBible').mockResolvedValue(undefined)
  renderWithMocks(<MoodBoardPage />, {referenceResults: mockResults})
  await userEvent.click(screen.getByText(/save mood board/i))
  expect(spy).toHaveBeenCalledOnce()
})
```

---

## Phase 12 — Frontend: CoverStudioPage + TextStudioPage
**Dependency:** Phase 11  
**Files touched:** `frontend/src/pages/CoverStudioPage.tsx` (new), `frontend/src/pages/TextStudioPage.tsx` (new)

### 12.1 `CoverStudioPage.tsx`

```typescript
// Layout:
// LEFT: Generation controls (1/3 width)
//   - Prompt editor (pre-filled from coverAnalysis.cover_t2i_prompt)
//   - Negative prompt editor
//   - Style variant selector: illustrated | photographic | abstract | typographic
//   - Concept count: 1–3 (default 3)
//   - "Generate Covers" button → POST /cover-concepts/generate
//
// RIGHT: Concept gallery (2/3 width)
//   - 1–3 concept cards side by side
//   - Each card: image (placeholder/spinner while generating), status badge
//   - "Select" button per card → POST /cover-concepts/{id}/select
//   - Selected card gets visual highlight
//   - "Generate Variants" button on selected card (re-generates with same prompt + variation)
//
// BOTTOM: "Export to KDP" button (only enabled when one concept is selected)
//   → navigates to /preview

// Poll GET /cover-concepts every 3s while any concept status == "generating"
```

### 12.2 `TextStudioPage.tsx` (Full Book only)

```typescript
// Layout:
// LEFT: Scene list (1/3 width)
//   - List of is_selected=true scenes sorted by illustration_priority
//   - Click scene to load in right panel
//   - Status indicator per scene (no illustration / pending / complete)
//
// RIGHT: Scene editor (2/3 width)
//   - Scene title + narrative_summary (readonly)
//   - Characters, locations, artefacts in this scene (readonly chips)
//   - Prompt editor (pre-filled from scene.scene_prompt_draft + VB conditioning)
//   - "Generate Illustration" button → POST /scenes/{id}/generate-illustration
//   - Illustration preview (placeholder/result image)

// Note: T2I is still a stub backend-side; this page builds the full UI
// but generation returns the stub 202 response
```

### 12.3 Frontend unit tests — Phase 12
File: `frontend/src/test/CoverStudioPage.test.tsx`

```typescript
test('generate button calls generateCoverConcepts', async () => {
  const spy = vi.spyOn(api, 'generateCoverConcepts').mockResolvedValue({queued: 3, concepts: []})
  render(<CoverStudioPage />)
  await userEvent.click(screen.getByText(/generate covers/i))
  expect(spy).toHaveBeenCalledWith(expect.any(Number), expect.objectContaining({concept_count: 3}))
})

test('export button disabled when no concept selected', () => {
  renderWithMocks(<CoverStudioPage />, {coverConcepts: mockConceptsNoneSelected})
  expect(screen.getByText(/export to kdp/i)).toBeDisabled()
})

test('export button enabled when concept is selected', () => {
  renderWithMocks(<CoverStudioPage />, {coverConcepts: mockConceptsOneSelected})
  expect(screen.getByText(/export to kdp/i)).not.toBeDisabled()
})

test('selecting concept calls selectCoverConcept', async () => {
  const spy = vi.spyOn(api, 'selectCoverConcept').mockResolvedValue(undefined)
  renderWithMocks(<CoverStudioPage />, {coverConcepts: mockConcepts})
  await userEvent.click(screen.getAllByText(/select/i)[0])
  expect(spy).toHaveBeenCalledOnce()
})
```

---

## Phase 13 — Frontend: Preview Unified Mode + E2E Tests
**Dependency:** Phases 9–12  
**Files touched:** `frontend/src/pages/ReadingPage.tsx`, `frontend/playwright.config.ts` (new), `frontend/e2e/` (new)

### 13.1 Preview + Reading mode unification

`ReadingPage.tsx` currently serves as Preview. Add reading mode:
```typescript
// Read ?mode= query param from URL
// mode=reading: hide WorkflowNav chrome, hide edit controls, show clean text+illustrations
// mode=preview (default): show WorkflowNav, show inline illustration edit controls

// Add toggle button: "Reading View" / "Edit View"
// Button toggles ?mode=reading param on the URL

// Add export actions (shown only in preview mode):
// - Cover-Only path: "Export Cover (KDP)" → POST /api/books/{id}/cover-concepts/{id}/export (stub)
// - Full Book path: "Export Full Book (KDP)" → stub endpoint
```

### 13.2 E2E Test setup

Create `frontend/playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
})
```

### 13.3 E2E Tests
File: `frontend/e2e/cover_only_path.spec.ts`

```typescript
test.describe('Cover-Only Path', () => {
  test('complete cover-only flow from upload to concept generation', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Book')
    
    // Upload step
    await page.setInputFiles('input[type=file]', 'e2e/fixtures/short_story.txt')
    await page.fill('input[name=title]', 'Test Book')
    await page.selectOption('select[name=genre]', 'thriller')
    await page.click('text=Cover Only')
    await page.click('text=Continue')
    
    // Assert WorkflowNav shows Cover-Only steps
    await expect(page.locator('text=Cover Studio')).toBeVisible()
    await expect(page.locator('text=Visual Bible')).not.toBeVisible()
    
    // Analysis step — Cover tab only (thriller default)
    await page.click('text=Run Analysis')
    await expect(page.locator('[data-testid=cover-tab-complete]')).toBeVisible({timeout: 30000})
    
    // Assert Characters tab shows activation CTA (not active by default for thriller)
    await page.click('text=Characters')
    await expect(page.locator('text=Activate Characters')).toBeVisible()
    
    // Cover tab has thematic_statement populated
    await page.click('text=Cover')
    await expect(page.locator('[name=thematic_statement]')).not.toBeEmpty()
    
    // Mood Board step
    await page.click('text=Mood Board')
    await expect(page.locator('text=Run Search')).toBeVisible()
    
    // Cover Studio step
    await page.click('text=Cover Studio')
    await expect(page.locator('text=Generate Covers')).toBeVisible()
    await page.click('text=Generate Covers')
    // 3 concept placeholders appear
    await expect(page.locator('[data-testid=concept-card]')).toHaveCount(3)
  })

  test('activating characters mid-flow triggers analysis', async ({ page }) => {
    // Navigate to analysis review on a cover_only book
    // Click Characters tab → Activate Characters
    // Assert analyzeEntity API call was made
    // Assert characters tab populates
  })
})
```

File: `frontend/e2e/full_book_path.spec.ts`

```typescript
test.describe('Full Book Path', () => {
  test('full book path shows all four entity tabs active', async ({ page }) => {
    await page.goto('/')
    // upload + select Full Book
    await page.click('text=Full Book')
    await page.click('text=Continue')
    
    // All four tabs in Analysis Review are active (no activation CTA)
    await page.click('text=Run Analysis')
    await expect(page.locator('[data-testid=analysis-progress-characters]')).toBeVisible({timeout: 60000})
    
    await page.click('text=Artefacts')
    await expect(page.locator('text=Activate Artefacts')).not.toBeVisible()
  })

  test('mood board shows all four tabs with search results', async ({ page }) => {
    // ...
  })

  test('visual bible page is in the nav for full_book', async ({ page }) => {
    // ...
  })

  test('preview mode toggle hides workflow chrome', async ({ page }) => {
    await page.goto('/books/1/preview')
    await page.click('text=Reading View')
    await expect(page.locator('[data-testid=workflow-nav]')).not.toBeVisible()
    await page.click('text=Edit View')
    await expect(page.locator('[data-testid=workflow-nav]')).toBeVisible()
  })
})
```

---

## Backend E2E Tests — Extend Existing Pipeline

File: `backend/tests/e2e/test_e2e_four_entity_pipeline.py`

```python
@pytest.fixture(scope="module")
def full_pipeline_client():
    # TestClient + upload + chunk; yield (client, book_id)

def test_cover_only_workflow_type(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.patch(f"/api/books/{book_id}", json={"workflow_type": "cover_only"})
    assert r.status_code == 200

def test_analyze_cover_only_entity_types(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.post(f"/api/books/{book_id}/analyze",
                    json={"entity_types": ["cover"], "style_category": "illustrated",
                          "genre": "thriller"})
    assert r.status_code == 202

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="requires OpenAI key")
def test_cover_analysis_populated_after_analyze(full_pipeline_client):
    client, book_id = full_pipeline_client
    # Poll until complete
    for _ in range(60):
        time.sleep(2)
        prog = client.get(f"/api/books/{book_id}/analysis-progress").json()
        if prog.get("entity_progress", {}).get("cover", {}).get("status") == "complete":
            break
    r = client.get(f"/api/books/{book_id}/cover-analysis")
    assert r.status_code == 200
    assert r.json()["thematic_statement"]

def test_artefact_analysis_trigger(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.post(f"/api/books/{book_id}/analyze/entity",
                    json={"entity_type": "artefacts"})
    assert r.status_code == 202

def test_reference_results_include_artefacts(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.get(f"/api/books/{book_id}/reference-results")
    data = r.json()
    assert "artefacts" in data
    assert "cover" in data

def test_visual_bible_approve_with_artefact_selections(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.post(f"/api/books/{book_id}/visual-bible/approve",
                    json={
                        "character_selections": {},
                        "location_selections": {},
                        "artefact_selections": {},
                        "cover_selections": []
                    })
    assert r.status_code == 200

def test_cover_concepts_generate_three(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate",
                    json={"concept_count": 3})
    assert r.status_code == 200
    assert r.json()["queued"] == 3

def test_select_cover_concept_exclusive(full_pipeline_client):
    client, book_id = full_pipeline_client
    concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
    if len(concepts) >= 2:
        c1, c2 = concepts[0]["id"], concepts[1]["id"]
        client.post(f"/api/books/{book_id}/cover-concepts/{c1}/select")
        client.post(f"/api/books/{book_id}/cover-concepts/{c2}/select")
        updated = client.get(f"/api/books/{book_id}/cover-concepts").json()
        selected = [c for c in updated if c["is_selected"]]
        assert len(selected) == 1
        assert selected[0]["id"] == c2
```

---

## Dependency Graph Summary

```
Phase 1 (Models/DB) ──► Phase 2 (CRUD) ──► Phase 3 (Artefact Service)
                    └──►               └──► Phase 4 (Cover Service)
                                       └──► Phase 5 (Endpoints)
                                             └──► Phase 6 (Search)
                                                   └──► Phase 7 (VB Entries + Cover Studio endpoints)
                                                         └──► Phase 8 (Frontend Foundation)
                                                               └──► Phase 9 (Setup + Nav)
                                                                     └──► Phase 10 (Analysis Page)
                                                                           └──► Phase 11 (Mood Board)
                                                                                 └──► Phase 12 (Studio Pages)
                                                                                       └──► Phase 13 (E2E)
```

Phases 3 and 4 can run in parallel (both depend on Phases 1+2 only).  
Phases 5, 6, 7 are strictly sequential.  
Frontend phases 8–13 can begin once backend Phase 7 is stable (API contracts are fixed).

---

## Critical Pre-Conditions Before Starting Phase 1

1. **Back up `app.db`** before any migration changes. The `_run_migrations()` function uses `ALTER TABLE ADD COLUMN` which is non-destructive, but new tables created via `Base.metadata.create_all()` require all models to be imported before `init_db()` is called.

2. **Run existing tests** (`pytest backend/tests/`) and confirm all pass before starting. Use test results as your baseline.

3. **Confirm `workflow_type` semantics**: the existing default value is `"full"`. Throughout all new code, treat `"full"` and `"full_book"` as equivalent (add a helper `is_full_book(workflow_type: str) -> bool` that returns True for both).

4. **Confirm T2I provider choice** before starting Phase 7. The Visual Bible entry generation and Cover Concept generation endpoints in Phase 7 fire T2I tasks. If T2I remains a stub (abstract_provider), Phase 7 still works correctly — the endpoints create records with `status=pending` and the generation silently produces no image. The UI should handle `image_path=None` gracefully with a placeholder.

5. **Remove dead frontend API functions**: before Phase 8, remove `getProgress` and `updateProgress` from `api.ts` to prevent confusion.
