# Noctua — Implementation Plan (Merged)
## T2I Module, Dual Workflow Paths, Cover Studio, Visual Identity, Alpha Deployment

**Phases 1–6:** Complete (four-entity model, CRUD, ontology, cover analysis, artefact analysis, search extensions).  
**This document:** Phases 7–16, starting from the current codebase state.  
**Target:** Cursor Composer (Agent mode) — each phase is a self-contained instruction block.  
**Testing:** pytest (backend); Vitest + Playwright (frontend).

> **Integration note:** Phases 7, 9, 10, 11, and 13 incorporate tasks from the T2I Gap Analysis (v2). Gap-derived additions are marked `[GAP]`. Original plan sections are unmarked. One new phase (Phase 9 — T2I Backend Services) has been inserted; all phases after it shift by one from the original numbering.

---

## How to Use This Document

Each phase has:
- **Scope** — exactly what changes
- **Files touched** — blast radius before starting
- **Implementation instructions** — precise enough for Cursor Composer
- **Unit test specs** — pytest signatures + assertions
- **Dependency** — which phase must be complete first

Run phases in order. Do not skip. Some phases modify files created in earlier phases.

---

## Session Grouping

| Session | Phases | Rationale                                                                                          |
| ------- | ------ | -------------------------------------------------------------------------------------------------- |
| 1       | 7      | Bug fixes + data model extensions + VB entries + Cover Studio API. All backend, overlapping files. |
| 2       | 8      | Frontend foundation. Must be stable before any component work.                                     |
| 3       | 9      | T2I backend services only. Pure Python, no frontend deps. Isolate for full attention.              |
| 4       | 10     | SetupPage + WorkflowNav. Additive frontend, shares routing context.                                |
| 5       | 11     | AnalysisReviewPage + Cover Brief Editor. Same page file.                                           |
| 6       | 12     | MoodBoardPage. Single new page.                                                                    |
| 7       | 13     | CoverStudio + TextStudio. Both new pages; CoverStudio now calls real T2I.                          |
| 8       | 14     | E2E tests only. Full attention on user-flow logic.                                                 |
| 9       | 15     | Visual identity. Independent — run any time after Session 2, optionally its own branch.            |
| 10      | 16     | Deployment. Touches every layer. Always last, always isolated.                                     |

---

## Cursor Composer Session Prompt

Copy this prompt in full at the start of every session. Replace the placeholder at the bottom with the phase content for that session.

```
You are implementing a software project called Noctua by following a phased
implementation plan. The full plan is in `docs/implementation_plan.md`.
The complete codebase documentation is in `docs/codebase_snapshot.md`.

════════════════════════════════════════
PROCESS — follow these steps in order. Do not skip any step.
════════════════════════════════════════

STEP 1 — READ BEFORE YOU WRITE
Before touching any file:
- Read the full phase content I have pasted below
- Read the relevant sections of `docs/codebase_snapshot.md` for every file
  you will modify — understand what already exists before adding to it
- Do not begin implementation until you have completed this reading

STEP 2 — DECLARE YOUR PLAN
Before writing any code, tell me:
- Every file you will CREATE (new files, with purpose)
- Every file you will MODIFY (existing files, with a specific summary of
  what changes — not "update as needed", but exactly what)
- Every assumption you are making that the phase does not explicitly resolve
- Any conflict you see between the phase instructions and the existing code

Then stop and wait for my explicit confirmation ("go ahead" or similar)
before writing a single line of implementation code.

STEP 3 — IMPLEMENT IN WRITTEN ORDER
Work through the phase sections in the order they are written.
Complete each section fully before moving to the next.
Do not skip ahead or reorder steps.

STEP 4 — MATCH EXISTING CONVENTIONS
Match the code style of the files you are modifying exactly:
- Python: match import ordering, type annotation style, docstring format,
  and error handling patterns visible in the existing service files
- TypeScript: match the component structure, hook patterns, and axios
  call conventions already present in api.ts and BookContext.tsx
- Tests: match the fixture approach, parametrize style, skip decorators,
  and assertion conventions of the existing test files

STEP 5 — WRITE AND RUN TESTS TOGETHER
For every section of implementation code you write:
a) Write the unit tests specified for that section in the phase
b) Run them immediately: `pytest path/to/test_file.py -v` (backend)
   or `npx vitest run path/to/test_file` (frontend)
c) If any test fails, fix the implementation (or the test if it is
   wrong) before moving to the next section
d) Paste the final test run output (pass/fail summary) in your response

Do not move to the next section until all tests for the current section
are passing.

STEP 6 — COMPLETE THE SESSION REPORT
When all phase sections are implemented and all tests are passing,
produce a session completion report in this exact format:

--- SESSION COMPLETE ---
Files created:
  - path/to/new_file.py — [one-line description]

Files modified:
  - path/to/existing_file.py — [one-line description of what changed]

Tests run:
  - backend/tests/unit/test_xyz.py — N passed, 0 failed

Deviations from plan:
  - [describe any deviation and why it was necessary, or "none"]

Known issues / follow-up needed:
  - [anything that needs attention in a future session, or "none"]

STEP 7 — UPDATE THE CODEBASE SNAPSHOT
After the session report, update `docs/codebase_snapshot.md` to reflect
everything that changed. Update only affected sections:
a) Section 2 (Database Schema): add new tables or columns
b) Section 3 (API Endpoints): add new endpoints, update status
c) Section 4 (Service Layer): add new service files or functions
d) Section 6 (Frontend Routing): add new routes
e) Section 7 (Frontend Components): add new components and pages
f) Section 11 (Known Stubs): remove implemented stubs; add new ones
g) Section 12 (Inter-Service Contracts): update changed data shapes

Do not rewrite sections that were not affected by this session.

════════════════════════════════════════
CONSTRAINTS — enforce without exception
════════════════════════════════════════

- Never modify files outside the "Files touched" list without flagging first
- Never delete existing functionality — extend, do not replace, unless the
  plan explicitly says to replace
- If the plan specifies a function signature, use it exactly
- If uncertain whether something conflicts with the existing codebase, stop
  and ask rather than guessing
- Do not add pip or npm packages beyond those specified without asking
- Do not run `git commit` or `git push`
- If a test requires an API key not in the environment, use the skip pattern:
  `pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="...")`

════════════════════════════════════════
CURRENT SESSION
════════════════════════════════════════

[PASTE PHASE CONTENT HERE]
```

---

## Phase 7 — Bug Fixes, Data Model Extensions, VB Entries & Cover Studio API
**Dependency:** Phases 1–6 complete  
**Files touched (backend):** `backend/app/models.py`, `backend/app/database.py`, `backend/app/schemas.py`, `backend/app/crud.py`, `backend/app/services/scene_extractor.py`, `backend/app/services/cover_analysis_service.py`, `backend/app/services/ai_service.py`, `backend/app/routers/visual_bible.py`, `backend/app/routers/illustrations.py`, `backend/app/routers/settings.py` (new), `backend/app/routers/books.py`, `backend/app/services/t2i_providers/abstract_provider.py`  
**Files touched (frontend):** `frontend/src/pages/AnalysisReviewPage.tsx`, `frontend/src/pages/ReviewSearchPage.tsx`, `frontend/src/pages/ReviewSearchResultPage.tsx`, `frontend/src/pages/SettingsPage.tsx`, `frontend/src/components/VisualBibleReview.tsx`, `frontend/src/services/api.ts`

This phase has eight sections. Complete them in order: bug fixes first (they underpin everything else), then data model additions, then the API endpoints, then frontend improvements.

---

### 7.0 Bug Fixes [GAP]

#### 7.0.1 Fix `is_main` collision — BUG-1

**Problem:** `is_main` is used simultaneously as a narrative importance flag (set by AI at analysis time) and as a UI selection flag (updated by the entity-selections endpoint when the user picks entities for reference search). When the user interacts with the UI, the AI-assigned narrative flag gets overwritten.

**Root cause:** `EntityMainFlag` in `EntitySelectionsRequest` writes to `is_main` directly.

**Fix — models.py:** Add `is_selected_for_reference` column to `characters` and `locations`:
```python
# In Character model:
is_selected_for_reference = Column(Integer, default=0)

# In Location model:
is_selected_for_reference = Column(Integer, default=0)
```

**Fix — database.py (_run_migrations):**
```python
_add_column_if_missing("characters", "is_selected_for_reference", "INTEGER DEFAULT 0")
_add_column_if_missing("locations", "is_selected_for_reference", "INTEGER DEFAULT 0")
```

**Fix — crud.py:** Add a new dedicated function; do NOT change `update_character` or `update_location` to write `is_main`:
```python
def update_entity_reference_selection(
    db: Session, entity_id: int, is_selected: int, entity_type: str
) -> None:
    """Writes only is_selected_for_reference. Never touches is_main."""
    if entity_type == "character":
        obj = db.query(Character).filter(Character.id == entity_id).first()
    else:
        obj = db.query(Location).filter(Location.id == entity_id).first()
    if obj:
        obj.is_selected_for_reference = is_selected
        db.commit()
```

**Fix — books.py router:** The `PUT /entity-selections` endpoint currently calls `crud.update_character(db, id, is_main=flag)` for each entity. Change it to call `crud.update_entity_reference_selection(db, id, flag, entity_type)` instead. `is_main` must never be written through this endpoint again.

**Fix — schemas.py:** Add `is_selected_for_reference: int = 0` to `CharacterResponse` and `LocationResponse`.

**Invariant to enforce:** `is_main` is set ONLY by `run_full_analysis` (ai_service) during the analyze background task. It is readonly everywhere else.

#### 7.0.2 Fix `scene_count` as display limit, not extraction limit — BUG-2

**Problem:** `{scene_count}` is substituted directly into `SCENE_EXTRACTION_PROMPT`, causing the LLM to extract exactly N scenes. At `scene_count=3`, only 3 scenes are persisted — a 48K-word novel gets 3 scenes forever.

**Fix — scene_extractor.py:**

Add an auto-calculation function:
```python
def _auto_scene_count(total_words: int) -> int:
    """
    One scene per ~3000 words. Min 5, max 30.
    Used for extraction; display count is a separate UI concern.
    """
    return max(5, min(30, total_words // 3000))
```

Remove `{scene_count}` from `SCENE_EXTRACTION_PROMPT`. Replace the instruction "select exactly {scene_count} scenes" with:
```
Select between {min_scenes} and {max_scenes} scenes. Prefer more scenes
over fewer — it is better to capture a minor moment than to omit a
significant one. The caller will filter by priority for display.
```

Update `extract_scenes_llm()` signature:
```python
def extract_scenes_llm(
    candidate_windows: list[dict],
    manuscript_lang: str = "en",
    total_words: int = 0,          # new param
    run_id: str = None,
) -> list[dict]:
    min_scenes = _auto_scene_count(total_words)
    max_scenes = min(min_scenes * 2, 30)
    # inject min_scenes and max_scenes into prompt, not a fixed count
```

**Fix — books.py router:** In `_run_analysis_background`, pass `total_words=book.total_words` when calling `extract_scenes_llm`. Remove the `scene_count` field from the analyze request's influence over extraction.

**Fix — models.py (books):** Add `scene_display_count` column (replaces the UX role of `scene_count`):
```python
scene_display_count = Column(Integer, default=10)
```
The old `scene_count` column is retained for backward compat but no longer drives extraction.

**Fix — database.py (_run_migrations):**
```python
_add_column_if_missing("books", "scene_display_count", "INTEGER DEFAULT 10")
```

**Fix — scenes.py router:** Extend `GET /scenes` with an optional query parameter:
```python
@router.get("/{book_id}/scenes")
async def get_scenes(
    book_id: int,
    show_all: bool = False,
    db: Session = Depends(get_db)
):
    scenes = _load_scenes_with_relations(db, book_id)
    if not show_all:
        book = crud.get_book(db, book_id)
        limit = book.scene_display_count or 10
        # Return top-N by dramatic importance
        scenes = scenes[:limit]
    return scenes
```

**Fix — frontend SetupPage.tsx:** Rename the "Number of scenes" input label to "Scenes to display" and clarify it controls display only, not extraction. Pass it to analyze as `scene_display_count` (not `scene_count`).

---

### 7.1 Data Model Extensions [GAP]

These columns are needed by Phase 9 (Prompt Assembler) and Phase 11 (Cover Brief Editor). Add them now so schemas are stable for frontend work in Phase 8.

#### 7.1.1 New columns — `cover_analysis` table

Add to `CoverAnalysis` model:
```python
cover_type = Column(String, nullable=True)
# Values: "object_centered"|"character_centered"|"setting_centered"|"abstract"|"typography_centered"
# Set by cover_analysis_service; editable by user via PATCH /cover-analysis

color_palette_structured = Column(Text, nullable=True)
# JSON: {dominant: str, accent: str, temperature: str, contrast: str, saturation: str}
# Set by cover_analysis_service stage 2; editable by user

primary_cover_character_id = Column(Integer, nullable=True)   # FK by convention (not enforced)
primary_cover_location_id  = Column(Integer, nullable=True)
primary_cover_artefact_id  = Column(Integer, nullable=True)
# Single primary element for cover focal point — chosen by user, suggested by AI.
# Distinct from cover_role_character_ids (the old AI-suggested list, retained for reference).
```

**database.py (_run_migrations):**
```python
_add_column_if_missing("cover_analysis", "cover_type", "TEXT")
_add_column_if_missing("cover_analysis", "color_palette_structured", "TEXT")
_add_column_if_missing("cover_analysis", "primary_cover_character_id", "INTEGER")
_add_column_if_missing("cover_analysis", "primary_cover_location_id", "INTEGER")
_add_column_if_missing("cover_analysis", "primary_cover_artefact_id", "INTEGER")
```

#### 7.1.2 New columns — `books` table

```python
target_audience = Column(String, default="adult")
# Values: "children"|"ya"|"adult"|"literary"
# Modifies genre contract in cover generation
```

**database.py:**
```python
_add_column_if_missing("books", "target_audience", "TEXT DEFAULT 'adult'")
```

#### 7.1.3 Update schemas.py

Extend `CoverAnalysisResponse`:
```python
cover_type: str | None = None
color_palette_structured: dict | None = None   # deserialized from JSON
primary_cover_character_id: int | None = None
primary_cover_location_id: int | None = None
primary_cover_artefact_id: int | None = None
```

Extend `CoverAnalysisUpdateRequest` (all optional, user-editable):
```python
cover_type: str | None = None
color_palette_structured: dict | None = None
primary_cover_character_id: int | None = None
primary_cover_location_id: int | None = None
primary_cover_artefact_id: int | None = None
```

Extend `BookAnalyzeRequest`:
```python
target_audience: str = "adult"   # new field
```

Extend `BookResponse`:
```python
target_audience: str = "adult"
scene_display_count: int = 10
is_selected_for_reference: int = 0   # on CharacterResponse/LocationResponse
```

#### 7.1.4 Update cover_analysis_service.py — Stage 2 prompt

Extend `COVER_BRIEF_SYNTHESIS_PROMPT` to also generate:
- `cover_type` — chosen from: object_centered, character_centered, setting_centered, abstract, typography_centered. Selection logic: if symbolic_anchors non-empty → object_centered; fantasy/romance + strong protagonist → character_centered; literary/thriller → abstract; non_fiction → typography_centered; else → setting_centered.
- `color_palette_structured` — JSON object: `{dominant, accent, temperature, contrast, saturation}`.

Add the following to the prompt:
```
Also return:
- "cover_type": one of "object_centered"|"character_centered"|"setting_centered"|"abstract"|"typography_centered".
  Apply this logic: if symbolic_anchors is non-empty → "object_centered";
  if genre is fantasy/romance/ya and there is a dominant protagonist → "character_centered";
  if genre is literary_fiction/thriller/mystery → "abstract";
  if genre is non_fiction/biography → "typography_centered";
  otherwise → "setting_centered".
- "color_palette_structured": object with keys dominant (string), accent (string),
  temperature ("warm"|"cool"|"neutral"), contrast ("high"|"mid"|"low"),
  saturation ("saturated"|"desaturated"|"monochrome"|"mixed").
- "cover_role_primary_hint": single string — the ONE entity name (character, location, OR artefact)
  most suited as the primary focal element of the cover. Not a list.
```

Update `run_cover_analysis()` to write `cover_type`, `color_palette_structured`, and resolve `cover_role_primary_hint` to the appropriate primary_cover_*_id before calling `crud.create_or_update_cover_analysis`.

#### 7.1.5 Update crud.py

Extend `create_or_update_cover_analysis` to accept and persist the new fields.

Update `update_book` to accept `target_audience` and `scene_display_count`.

---

### 7.2 Visual Bible Entries Endpoints

Add to `backend/app/routers/visual_bible.py`:

```
GET  /api/books/{book_id}/visual-bible/entries
     Query: entity_type? entity_id?
     → list[VisualBibleEntryResponse]

POST /api/books/{book_id}/visual-bible/entries/generate
     Body: { entity_type, entity_id, angle_label, prompt? }
     → VisualBibleEntryResponse (202)
     Creates entry with status=pending; fires background T2I task (abstract_provider stub)

POST /api/books/{book_id}/visual-bible/entries/generate-all
     Body: { entity_type? }
     → { queued: int, entries: list[VisualBibleEntryResponse] }

PATCH /api/books/{book_id}/visual-bible/entries/{entry_id}
      Body: { is_approved?, image_path?, status? }
      → VisualBibleEntryResponse
```

**VB depth calculator** (helper in visual_bible.py or a utility module):
```python
def get_vb_angles(entity_type: str, visual_bible_depth: int, is_main: bool) -> list[str]:
    CHARACTER_ANGLES = ["front", "3/4 left", "3/4 right", "profile", "action pose", "close-up face"]
    LOCATION_ANGLES  = ["exterior wide", "interior", "atmospheric detail", "establishing shot"]
    ARTEFACT_ANGLES  = ["front", "back", "detail/open", "in-use context"]
    depth = visual_bible_depth or (6 if is_main else 3)
    if entity_type == "character":
        return CHARACTER_ANGLES[:depth]
    elif entity_type == "location":
        return LOCATION_ANGLES[:min(depth, 4)]
    elif entity_type == "artefact":
        return ARTEFACT_ANGLES[:min(depth, 4)]
    return []
```

The T2I background task calls `abstract_provider.generate()` — still a stub. The endpoint architecture is real; T2I is wired in Phase 9.

---

### 7.3 Cover Studio Endpoints

Add to `backend/app/routers/illustrations.py` (currently empty):

```
GET  /api/books/{book_id}/cover-concepts
     → list[CoverConceptResponse]

POST /api/books/{book_id}/cover-concepts/generate
     Body: {
         prompt?: str,
         negative_prompt?: str,
         style_variant?: str,   # photographic|illustrated|abstract|typographic
         concept_count?: int    # default 3
     }
     → { queued: int, concepts: list[CoverConceptResponse] }
     Creates concept_count CoverConcept rows with status=pending.
     Fires abstract_provider stub per concept (real T2I wired in Phase 9).

PATCH /api/books/{book_id}/cover-concepts/{concept_id}
      Body: { is_selected?, prompt_used?, style_variant? }
      → CoverConceptResponse

POST /api/books/{book_id}/cover-concepts/{concept_id}/select
     → StatusResponse
     Calls crud.set_selected_cover_concept; returns 200
```

**Important:** The `generate` endpoint should read `cover_analysis.cover_t2i_prompt` as the default prompt if no `prompt` override is supplied in the body. This ensures the AI-generated prompt is used by default, and the user can override it in Phase 13's Cover Studio UI.

---

### 7.4 Unit Tests — Phase 7

File: `backend/tests/unit/test_bugs_phase7.py`

```python
# BUG-1: is_main isolation
def test_update_entity_reference_selection_does_not_touch_is_main(db):
    book = crud.create_book(db, title="T", author="A")
    char = crud.create_character(db, book.id, "Hero", ...)
    # Simulate AI setting is_main
    crud.update_character(db, char.id, is_main=1)
    # Now user selects for reference
    crud.update_entity_reference_selection(db, char.id, 1, "character")
    refreshed = crud.get_character(db, char.id)
    assert refreshed.is_main == 1                     # unchanged
    assert refreshed.is_selected_for_reference == 1   # updated

def test_entity_selections_endpoint_does_not_write_is_main(client_with_book):
    client, book_id = client_with_book
    # Set is_main via analyze (mock)
    # Then call entity-selections
    r = client.put(f"/api/books/{book_id}/entity-selections",
                   json={"characters": [{"id": 1, "is_main": 0}], "locations": []})
    assert r.status_code == 200
    char_r = client.get(f"/api/books/{book_id}/characters").json()
    # is_main must remain as AI set it, not as entity-selections specified
    # (exact assertion depends on fixture setup)

# BUG-2: scene_count
def test_auto_scene_count_scales_with_words():
    assert _auto_scene_count(6000)  == 5    # min floor
    assert _auto_scene_count(15000) == 5    # 15000//3000 = 5
    assert _auto_scene_count(30000) == 10
    assert _auto_scene_count(90000) == 30   # max ceiling
    assert _auto_scene_count(200000) == 30  # max ceiling

def test_get_scenes_show_all_false_limits_to_display_count(client_with_scenes):
    client, book_id = client_with_scenes
    # Assume 15 scenes in DB, scene_display_count=5
    r = client.get(f"/api/books/{book_id}/scenes")
    assert len(r.json()) == 5

def test_get_scenes_show_all_true_returns_all(client_with_scenes):
    client, book_id = client_with_scenes
    r = client.get(f"/api/books/{book_id}/scenes?show_all=true")
    assert len(r.json()) > 5

# Data model
def test_cover_analysis_cover_type_field(db):
    book = crud.create_book(db, title="T", author="A")
    ca = crud.create_or_update_cover_analysis(db, book.id,
             cover_type="object_centered",
             color_palette_structured='{"dominant":"black","accent":"amber"}')
    assert ca.cover_type == "object_centered"

def test_cover_analysis_primary_ids(db):
    book = crud.create_book(db, title="T", author="A")
    ca = crud.create_or_update_cover_analysis(db, book.id,
             primary_cover_artefact_id=2)
    assert ca.primary_cover_artefact_id == 2
    assert ca.primary_cover_character_id is None

# VB entries
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
    assert r.json()["queued"] > 0

def test_generate_cover_concepts_creates_3(client_with_cover_analysis):
    client, book_id = client_with_cover_analysis
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate",
                    json={"concept_count": 3})
    assert r.status_code == 200
    assert r.json()["queued"] == 3

def test_cover_concept_generate_uses_cover_analysis_prompt(client_with_cover_analysis):
    client, book_id = client_with_cover_analysis
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate", json={})
    concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
    assert concepts[0]["prompt_used"]  # not None/empty

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

### 7.5 Backend: Per-Entity Full Description Field & Search Query Strategy

This section adds a `full_description` field to every entity type so that Google/SerpAPI searches can be driven by a rich natural-language sentence rather than compressed visual tokens. It also adds a per-book `search_query_strategy` preference that controls which query form is used per provider.

#### 7.5.1 Data model — new columns

**models.py:** Add `full_description` to Character, Location, Artefact, and CoverAnalysis:
```python
# Character, Location, Artefact:
full_description = Column(Text, nullable=True)
# A 1–2 sentence visual description generated by AI analysis.
# Example: "A tall woman in her 40s, sharp angular features, close-cropped silver hair,
# always dressed in charcoal grey tailored clothing, carrying a worn leather satchel."

# CoverAnalysis:
full_description = Column(Text, nullable=True)
# Full narrative description of the cover concept for use in search / generation prompts.
```

**models.py:** Add `search_query_strategy` to Book:
```python
search_query_strategy = Column(String, default="tokens")
# "tokens"   → use existing visual_tokens string for all engines (legacy behaviour)
# "adaptive" → route by provider type: sentences for Google-backed, tokens for tag-based
```

**database.py (_run_migrations):**
```python
_add_column_if_missing("characters", "full_description", "TEXT")
_add_column_if_missing("locations",  "full_description", "TEXT")
_add_column_if_missing("artefacts",  "full_description", "TEXT")
_add_column_if_missing("cover_analysis", "full_description", "TEXT")
_add_column_if_missing("books", "search_query_strategy", "TEXT DEFAULT 'tokens'")
```

**schemas.py:** Add `full_description: str | None = None` to `CharacterResponse`, `LocationResponse`, `ArtefactResponse`, `CoverAnalysisResponse`. Add to their respective update/patch request schemas as an optional field. Add `search_query_strategy: str = "tokens"` to `BookResponse` and `BookAnalyzeRequest`.

#### 7.5.2 AI service — generate `full_description` during analysis

**ai_service.py:** Extend the character, location, artefact, and cover extraction prompts to produce a `full_description` field. Append the following instruction to each entity extraction prompt:

```
Also return a "full_description" field: a single sentence (max 40 words) describing
the entity's visual appearance as if briefing a concept artist. Be concrete and specific.
Avoid metaphor. Focus on what is visible: physical traits, materials, colours, posture,
setting mood. This field will be used verbatim as a search query.
```

Parse and persist `full_description` when writing each entity to the database. If the LLM does not return it, set to `None` (do not error).

#### 7.5.3 Search service — adaptive query routing

In the search service layer (whichever module builds the query string passed to each provider), add the following routing logic. This must be called at query-build time, not at provider initialisation time.

**Provider classification:**

| Category | Providers | Best query format |
|----------|-----------|-------------------|
| `google_semantic` | `serpapi`, `behance` (via SerpAPI `site:`), `dribbble` (via SerpAPI `site:`) | `full_description` if available, else `visual_tokens` |
| `tag_based` | `unsplash`, `pexels`, `pixabay`, `openverse` | `visual_tokens` (2–5 keywords) |
| `catalogue` | `wikimedia` | `canonical_name` (entity name + optional 1–2 specificity terms) |
| `hybrid` | `flickr` | entity name + up to 3 style/mood tokens from `visual_tokens` |

**Query builder function — add to search service:**
```python
PROVIDER_CATEGORY = {
    "serpapi":    "google_semantic",
    "behance":    "google_semantic",
    "dribbble":   "google_semantic",
    "unsplash":   "tag_based",
    "pexels":     "tag_based",
    "pixabay":    "tag_based",
    "openverse":  "tag_based",
    "wikimedia":  "catalogue",
    "flickr":     "hybrid",
}

def build_search_query(
    entity_name: str,
    visual_tokens: str,
    full_description: str | None,
    provider: str,
    strategy: str,          # book.search_query_strategy: "tokens" | "adaptive"
) -> str:
    """
    Returns the search string to use for the given provider.
    If strategy == "tokens", always return visual_tokens (legacy behaviour).
    If strategy == "adaptive", route by provider category.
    """
    if strategy == "tokens" or not full_description:
        return visual_tokens

    category = PROVIDER_CATEGORY.get(provider, "tag_based")

    if category == "google_semantic":
        return full_description
    elif category == "catalogue":
        return entity_name          # let Wikimedia do exact title lookup
    elif category == "hybrid":
        # entity name + first 3 tokens
        tokens = visual_tokens.split()[:3]
        return f"{entity_name} {' '.join(tokens)}".strip()
    else:  # tag_based
        return visual_tokens
```

Call `build_search_query()` wherever the current code builds the query string for a provider, passing `book.search_query_strategy` and the entity's `full_description`.

**crud.py:** Update `update_character`, `update_location`, `update_artefact`, and `create_or_update_cover_analysis` to accept and persist `full_description`. Update `update_book` to accept `search_query_strategy`.

---

### Phase 7.6–7.8 scope proposal (to align with product)

**Рекомендуемый объём и порядок реализации** (согласовать с заказчиком перед стартом):

| Блок    | Содержание                                                                                    | Предложение                                                                                                                                                                                                                    |
| ------- | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **7.6** | Analysis Review — редактируемые карточки и вкладка Style                                      | **Включить.** Порядок: 7.6.4 (вкладка Style на AnalysisReviewPage) → 7.6.1 (карточки Characters/Locations/Artefacts) → 7.6.2 (Cover) → 7.6.3 (Scenes). Так вкладка Style появляется до переноса контента из VisualBibleReview. |
| **7.7** | Review Search — убрать T2I-поля, удаление вариантов Cover, панель движков, стратегия запросов | **Включить.** 7.7.1 (удалить T2I prompt inputs) → 7.7.2 (delete для Cover query variants) → 7.7.3 (Search Engines panel) → 7.7.4 (Query strategy toggle).                                                                      |
| **7.8** | VisualBibleReview — удалить вкладку Style                                                     | **Включить.** Делать после 7.6.4, чтобы контент Style уже жил на AnalysisReviewPage.                                                                                                                                           |

**Итоговый порядок фаз:** 7.6.4 → 7.6.1 → 7.6.2 → 7.6.3 → 7.7.1 → 7.7.2 → 7.7.3 → 7.7.4 → 7.8.

**Опционально:** если хочется минимизировать первый релиз 7.6–7.8, можно ограничиться 7.6.4 + 7.8 (перенос Style на Analysis Review и удаление с Review Result), отложив редактируемые карточки (7.6.1–7.6.3) и правки Review Search (7.7) на следующую итерацию.

*После согласования — пометить в плане выбранный вариант (полный 7.6–7.8 или сокращённый) и при необходимости вынести в отдельную подфазу «Phase 7.6–7.8 Frontend» в roadmap.*

---

### 7.6 Frontend: Analysis Review Page — Editable AI Results

**File:** `frontend/src/pages/AnalysisReviewPage.tsx`

Currently the page loads and displays AI analysis results as read-only. This section makes every field editable and saveable.

#### 7.6.1 Editable entity cards (Characters, Locations, Artefacts tabs)

Add an edit mode to each entity card. Pattern: each card gets an "Edit" button (pencil icon from Lucide). Clicking it switches the card into edit mode — all text fields become `<textarea>` or `<input>` elements. A "Save" button and a "Cancel" button appear. "Save" calls the appropriate PATCH endpoint; "Cancel" restores the previous values.

**Fields to make editable per entity type:**

Characters: `name`, `description`, `visual_description`, `full_description`, `role`, `personality_traits` (comma-separated string).

Locations: `name`, `description`, `visual_description`, `full_description`, `atmosphere`.

Artefacts: `name`, `description`, `visual_description`, `full_description`, `symbolic_role`.

**API calls:**
- Characters and Locations: use `api.patchEntitySummaries(bookId, { characters: [...] })` — this function already exists in `api.ts`. Extend `patchEntitySummaries` if needed to also accept individual artefact updates, or call a new `api.updateArtefact(bookId, artefactId, data)` for artefacts (add this function to `api.ts` if not present: `PATCH /api/books/{bookId}/artefacts/{artefactId}`).
- `full_description` is a new field; include it in the patch body.

**State management:** Store edits in local component state (`editingEntityId`, `editDraft`). Do not write to global `BookContext` until save succeeds.

**UX rules:**
- Only one entity card can be in edit mode at a time.
- On save success, update the local entity list in component state and exit edit mode.
- On save failure, show an inline error message on the card; remain in edit mode.
- `is_main` remains a read-only badge — it must never be rendered as an editable input.

#### 7.6.2 Editable Cover tab

The cover tab already loads `coverAnalysis` via `getCoverAnalysis`. Make the following fields editable inline, using the same edit/save/cancel pattern:

`thematic_statement`, `mood_keywords` (comma-separated), `visual_style_tags` (comma-separated), `cover_t2i_prompt`, `cover_type` (dropdown: object_centered / character_centered / setting_centered / abstract / typography_centered), `color_palette_structured` (rendered as individual sub-fields: dominant, accent, temperature, contrast, saturation), `full_description`.

**API call:** `api.updateCoverAnalysis(bookId, data)` — add this to `api.ts` if not present: `PATCH /api/books/{bookId}/cover-analysis` with a partial body.

#### 7.6.3 Editable Scenes tab

Scene fields `title`, `narrative_summary`, and `dramatic_importance` should be editable. `scene_prompt_draft` (the T2I prompt field) must be **removed entirely** from this tab — see section 7.7 below.

**API call:** existing `api.updateScene(bookId, sceneId, data)`.

#### 7.6.4 Style Summary tab — moved here from ReviewSearchResultPage

Add a new **"Style"** tab to `AnalysisReviewPage.tsx`. This tab displays the style summary that is currently shown in `VisualBibleReview` on `ReviewSearchResultPage`.

Content of the Style tab:
- `coverAnalysis.visual_style_tags` — display as tag chips; each chip editable in aggregate via the same edit/save pattern.
- `coverAnalysis.mood_keywords` — display as tag chips.
- `coverAnalysis.color_palette_structured` — rendered as labelled swatches (dominant, accent) + text labels (temperature, contrast, saturation). Editable.
- `coverAnalysis.thematic_statement` — displayed as a blockquote; editable.
- A "Save Style" button that calls `api.updateCoverAnalysis`.

The Style tab data is already available because `coverAnalysis` is fetched on mount.

**Tab order:** Characters | Locations | Artefacts | Scenes | Cover | Style

---

### 7.7 Frontend: Review Search Page — Improvements

**File:** `frontend/src/pages/ReviewSearchPage.tsx`

#### 7.7.1 Remove T2I prompt text boxes

Remove any `<textarea>` or `<input>` elements that contain or collect text-to-image generation prompts from `ReviewSearchPage.tsx`. These belong in `CoverStudioPage` and `TextStudioPage` (Phase 13). If T2I prompt data is currently displayed as read-only reference text (not a form field), it may be retained as a static display only — but form inputs for editing prompts must be removed.

#### 7.7.2 Add delete for Cover query variants

Currently Characters, Locations, and Artefacts entities on this page have a delete button (×) to remove a search query variant. The Cover section has 4 query variants but no delete. Apply the same delete pattern to cover query variants:

- Each cover query variant row gets a delete (×) button identical in style to those used for Characters/Locations/Artefacts.
- On delete: remove the variant from local state immediately (optimistic), then call the appropriate backend endpoint to persist the deletion if one exists; otherwise persist to the same localStorage key used by the cover query state (`review_search_options_${bookId}` or the relevant cover key).
- Minimum 1 variant must remain — disable the delete button when only one variant is left, matching the behaviour already in place for other entity types (confirm by reading the existing delete logic in the page).

#### 7.7.3 Move search engine selector here from Settings

Currently, enabled search providers are configured in `SettingsPage.tsx` and stored in `localStorage` under `ENABLED_PROVIDERS_STORAGE_KEY`. The user cannot change providers without leaving the workflow.

Add a **"Search Engines"** panel to `ReviewSearchPage.tsx`, positioned above the query list (collapsible, collapsed by default):

```typescript
// Read current enabled providers from localStorage via the existing
// ENABLED_PROVIDERS_STORAGE_KEY constant (imported from api.ts).
// Render each available provider as a toggle chip (enabled = filled, disabled = outline).
// On toggle: update localStorage immediately (same key, same format as SettingsPage).
// Label: "Search engines for this session" with a small info note:
// "Changes here apply to the current search only. Default engines are set in Settings."
```

Call `api.getProvidersStatus()` to get the list of available providers and their current status (this call is already made in SettingsPage — reuse the same API function). Render provider names as toggleable chips. Read initial state from `ENABLED_PROVIDERS_STORAGE_KEY` in localStorage. Write back to the same key on change. The existing `searchReferences` call already reads from this key, so no changes to the search execution logic are needed.

#### 7.7.4 Add search query strategy toggle

Add a **"Query strategy"** radio control to the Search Engines panel (alongside the provider toggles):

```
○ Compact keywords  (legacy — same tokens for all engines)
● Adaptive          (sentences for Google, keywords for tag-based engines)
```

Default: "Compact keywords" (preserves existing behaviour). Selection stored in `localStorage` under key `noctua_search_strategy_${bookId}`. On search execution, read this value and pass it to the backend as a `search_query_strategy` param in the `searchReferences` API call body, OR call `api.updateBook(bookId, { search_query_strategy: value })` before triggering search so the backend can read it from the book record. Use whichever approach matches how the backend reads strategy (see section 7.5.3 — the backend reads `book.search_query_strategy`). Therefore: call `api.updateBook` when the user changes the toggle, so the value is persisted to the book and the search service can read it.

---

### 7.8 Frontend: VisualBibleReview — Remove Style Tab

**File:** `frontend/src/components/VisualBibleReview.tsx`

Remove the **"Style"** tab from `VisualBibleReview`. This tab's content has been moved to `AnalysisReviewPage.tsx` (see section 7.6.4).

Steps:
1. Locate the style tab definition in `VisualBibleReview.tsx` (tab label `style` or `Style`).
2. Remove the tab button from the tab bar.
3. Remove the tab panel content block.
4. Remove any style-specific state, props, or data-fetching logic that was used exclusively by the style tab. Do not remove props or state shared with other tabs.
5. If `VisualBibleReview` accepts a `coverAnalysis` prop solely for the style tab, that prop can be made optional (`coverAnalysis?: CoverAnalysisResponse`) and the style tab references removed. Verify no other tab uses it before removing the prop.

---

### 7.9 Backend + Frontend: Editable LLM System Prompts in Settings

All LLM system prompts used for AI extraction and summarisation should be viewable and editable from the Settings screen. This prevents the need to redeploy to adjust prompt behaviour.

#### 7.9.1 Backend — prompt storage and API

**Prompt registry:** Create `backend/app/services/prompt_registry.py`. This module holds all system prompts as a Python dictionary (the source of truth for defaults), and provides functions to load overrides from the database.

```python
# prompt_registry.py

PROMPT_KEYS = {
    "character_extraction":   "System prompt for character extraction from manuscript",
    "location_extraction":    "System prompt for location extraction",
    "artefact_extraction":    "System prompt for artefact extraction",
    "scene_extraction":       "System prompt for scene extraction",
    "cover_brief_stage1":     "System prompt for cover analysis stage 1 (thematic)",
    "cover_brief_stage2":     "System prompt for cover analysis stage 2 (visual)",
    "full_description_gen":   "Instruction appended to extraction prompts to generate full_description",
}

# Default values: copy the current prompt strings verbatim from ai_service.py,
# scene_extractor.py, and cover_analysis_service.py into this dict at the matching keys.
PROMPT_DEFAULTS: dict[str, str] = {
    "character_extraction": "...",   # copy from ai_service.py
    # ... etc
}

def get_prompt(key: str, db) -> str:
    """Return DB override if present, else return PROMPT_DEFAULTS[key]."""
    override = crud.get_prompt_override(db, key)
    return override.value if override else PROMPT_DEFAULTS[key]

def list_prompts(db) -> list[dict]:
    """Return all keys with their current value (override or default) and description."""
    result = []
    for key, description in PROMPT_KEYS.items():
        value = get_prompt(key, db)
        is_overridden = crud.get_prompt_override(db, key) is not None
        result.append({"key": key, "description": description,
                        "value": value, "is_overridden": is_overridden})
    return result
```

**models.py:** Add a `PromptOverride` model:
```python
class PromptOverride(Base):
    __tablename__ = "prompt_overrides"
    id    = Column(Integer, primary_key=True)
    key   = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**database.py:** `Base.metadata.create_all(engine)` will create the table. No manual migration needed if this model is imported before `init_db()`.

**crud.py:** Add:
```python
def get_prompt_override(db, key: str) -> PromptOverride | None:
    return db.query(PromptOverride).filter(PromptOverride.key == key).first()

def set_prompt_override(db, key: str, value: str) -> PromptOverride:
    obj = get_prompt_override(db, key)
    if obj:
        obj.value = value
    else:
        obj = PromptOverride(key=key, value=value)
        db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

def reset_prompt_override(db, key: str) -> None:
    obj = get_prompt_override(db, key)
    if obj:
        db.delete(obj)
        db.commit()
```

**New router — `backend/app/routers/settings.py`:**
```
GET  /api/settings/prompts
     → list[{ key, description, value, is_overridden }]

PUT  /api/settings/prompts/{key}
     Body: { value: str }
     → { key, value, is_overridden: true }
     Validates key is in PROMPT_KEYS before saving.

DELETE /api/settings/prompts/{key}
       → StatusResponse
       Deletes override; reverts to default.
```

Register the router in `main.py`.

**ai_service.py, scene_extractor.py, cover_analysis_service.py:** Replace every hardcoded prompt string with a call to `prompt_registry.get_prompt(key, db)`. Pass `db` as a parameter to the functions that construct prompts, or load all prompts once at the start of an analysis run and pass them through.

#### 7.9.2 Frontend — prompt editor in SettingsPage

**File:** `frontend/src/pages/SettingsPage.tsx`

Add a new **"AI Prompts"** section below the existing provider settings.

**api.ts** — add:
```typescript
getPrompts(): Promise<PromptEntry[]>
// GET /api/settings/prompts

updatePrompt(key: string, value: string): Promise<PromptEntry>
// PUT /api/settings/prompts/{key}  body: { value }

resetPrompt(key: string): Promise<void>
// DELETE /api/settings/prompts/{key}
```

Where `PromptEntry = { key: string; description: string; value: string; is_overridden: boolean }`.

**SettingsPage UI — AI Prompts section:**

```
AI Prompts                              [Expand ▼]
────────────────────────────────────────────────
  ⚠ Editing prompts affects all future AI analysis runs.
    Changes take effect immediately. Reset to restore defaults.

  Character Extraction                  [Reset to default]
  System prompt for character extraction from manuscript
  ┌────────────────────────────────────────────────┐
  │ <editable textarea, full current value>        │
  └────────────────────────────────────────────────┘
                                          [Save]

  Location Extraction                   [Reset to default]
  ...

  (one block per PROMPT_KEYS entry)
```

Behaviour:
- Section collapsed by default (to avoid overwhelming the settings page).
- Load prompts on expand via `api.getPrompts()`.
- Each prompt block has a `<textarea>` (min 6 rows, monospace font) pre-filled with current value.
- "Save" button: calls `api.updatePrompt(key, newValue)`, shows inline success/error toast.
- "Reset to default" button: visible only when `is_overridden === true`. Calls `api.resetPrompt(key)`, reloads that block's value from the response.
- No auto-save — user must explicitly press Save per prompt.

#### 7.9.3 Unit tests — prompts

Add to `backend/tests/unit/test_bugs_phase7.py`:
```python
def test_get_prompt_returns_default_when_no_override(db):
    from app.services.prompt_registry import get_prompt, PROMPT_DEFAULTS
    value = get_prompt("character_extraction", db)
    assert value == PROMPT_DEFAULTS["character_extraction"]

def test_set_and_get_prompt_override(db):
    from app.services.prompt_registry import get_prompt
    crud.set_prompt_override(db, "character_extraction", "custom prompt text")
    value = get_prompt("character_extraction", db)
    assert value == "custom prompt text"

def test_reset_prompt_reverts_to_default(db):
    from app.services.prompt_registry import get_prompt, PROMPT_DEFAULTS
    crud.set_prompt_override(db, "character_extraction", "custom")
    crud.reset_prompt_override(db, "character_extraction")
    value = get_prompt("character_extraction", db)
    assert value == PROMPT_DEFAULTS["character_extraction"]

def test_prompts_api_get(client):
    r = client.get("/api/settings/prompts")
    assert r.status_code == 200
    keys = [p["key"] for p in r.json()]
    assert "character_extraction" in keys

def test_prompts_api_put(client):
    r = client.put("/api/settings/prompts/character_extraction",
                   json={"value": "new custom prompt"})
    assert r.status_code == 200
    assert r.json()["is_overridden"] is True

def test_prompts_api_put_invalid_key(client):
    r = client.put("/api/settings/prompts/nonexistent_key",
                   json={"value": "anything"})
    assert r.status_code == 422   # or 400

def test_prompts_api_delete(client):
    client.put("/api/settings/prompts/character_extraction",
               json={"value": "override"})
    r = client.delete("/api/settings/prompts/character_extraction")
    assert r.status_code == 200
    # Now get should return default
    prompts = client.get("/api/settings/prompts").json()
    p = next(p for p in prompts if p["key"] == "character_extraction")
    assert p["is_overridden"] is False
```

---

## Phase 8 — Frontend: Testing Bootstrap + BookContext + api.ts
**Dependency:** Phase 7  
**Files touched:** `frontend/package.json`, `frontend/vitest.config.ts` (new), `frontend/src/context/BookContext.tsx`, `frontend/src/services/api.ts`, `frontend/src/test/` (new directory)

### 8.1 Bootstrap Frontend Testing (Vitest + Playwright)

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

Add scripts: `"test": "vitest run"`, `"test:e2e": "playwright test"`.

Create `frontend/vitest.config.ts`:
```typescript
import { defineConfig } from 'vitest/config'
export default defineConfig({
  test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'], globals: true }
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

Create `frontend/src/test/mocks/server.ts` — MSW service worker mock server with handlers for all API endpoints returning fixture data (including all Phase 7 endpoints).

### 8.2 Extend `BookContext.tsx`

Add to context state:
```typescript
// Entities
artefacts: Artefact[]
setArtefacts: (a: Artefact[]) => void
coverAnalysis: CoverAnalysis | null
setCoverAnalysis: (c: CoverAnalysis | null) => void

// Workflow
workflowType: 'cover_only' | 'full_book'
setWorkflowType: (t: 'cover_only' | 'full_book') => void
activeEntityTypes: string[]
setActiveEntityTypes: (types: string[]) => void
genre: string
setGenre: (g: string) => void
targetAudience: string              // [GAP] new
setTargetAudience: (a: string) => void

// Analysis progress
analysisProgress: EntityProgress | null
setAnalysisProgress: (p: EntityProgress | null) => void

// Visual Bible
visualBibleEntries: VisualBibleEntry[]
setVisualBibleEntries: (e: VisualBibleEntry[]) => void

// Cover concepts
coverConcepts: CoverConcept[]
setCoverConcepts: (c: CoverConcept[]) => void
```

Add TypeScript interfaces matching all Phase 1 + Phase 7 schemas, including the new `cover_type`, `color_palette_structured`, `primary_cover_*_id`, and `is_selected_for_reference` fields.

### 8.3 Extend `api.ts`

Remove dead functions: `getProgress`, `updateProgress`.

Add:
```typescript
// Artefacts
getArtefacts(bookId: number): Promise<Artefact[]>
updateArtefact(bookId: number, artefactId: number, data: Partial<Artefact>): Promise<Artefact>

// Entity activations
updateEntityActivations(bookId: number, entityActivations: string[]): Promise<void>
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

// [GAP] Cover generation (Phase 9 endpoint — add stub call here, Phase 9 wires the backend)
generateCover(bookId: number, data?: GenerateCoverRequest): Promise<{status: string, job_id?: string}>

// Extended existing
searchReferences(bookId: number, params: SearchReferencesRequest): Promise<SearchReferencesResult>
getReferenceResults(bookId: number): Promise<ReferenceResultsResponse>
approveVisualBible(bookId: number, data: VisualBibleApproveRequest): Promise<void>
```

### 8.4 Unit Tests — Phase 8

File: `frontend/src/test/BookContext.test.tsx`
```typescript
describe('BookContext', () => {
  test('default workflowType is cover_only', () => { ... })
  test('activeEntityTypes defaults to ["cover"] for cover_only', () => { ... })
  test('setActiveEntityTypes updates context', () => { ... })
  test('targetAudience defaults to "adult"', () => { ... })    // [GAP]
  test('reset clears artefacts and coverAnalysis', () => { ... })
})
```

File: `frontend/src/test/api.test.ts`
```typescript
test('getArtefacts calls correct endpoint', async () => { ... })
test('getCoverAnalysis throws on 404', async () => { ... })
test('updateEntityActivations posts correct body', async () => { ... })
test('generateCover calls /generate-cover endpoint', async () => { ... })  // [GAP]
```

---

## Phase 9 — T2I Backend Services [GAP — New Phase]
**Dependency:** Phase 7  
**Files touched:** `backend/app/services/cover_visual_language.py` (new), `backend/app/services/cover_prompt_assembler.py` (new), `backend/app/services/t2i_providers/flux_provider.py`, `backend/app/services/t2i_providers/dalle_provider.py` (new), `backend/app/services/engine_selector.py`, `backend/app/routers/illustrations.py`, `backend/app/.env.example`, `backend/requirements.txt`

This phase wires the T2I generation stack end-to-end for cover generation. After this phase, `POST /cover-concepts/generate` produces real images (when `FAL_API_KEY` is set).

### 9.1 Cover Visual Language Maps

Create `backend/app/services/cover_visual_language.py`:

```python
"""
Static mapping tables that translate structured cover analysis parameters
into text-to-image prompt tokens. No LLM calls — pure deterministic lookup.
"""

MOOD_VISUAL_MARKERS: dict[str, list[str]] = {
    "dark":        ["dramatic shadows", "deep contrast", "low-key lighting"],
    "intense":     ["tight framing", "dynamic composition", "strong diagonals"],
    "foreboding":  ["stormy sky", "dark vignette", "isolated subject"],
    "mysterious":  ["partial concealment", "shadow and light interplay", "selective focus"],
    "reflective":  ["mirror surface", "still water reflection", "diffused soft light"],
    "chaotic":     ["fractured composition", "overlapping visual planes", "motion blur"],
    "tragic":      ["muted desaturated tones", "solitary figure", "heavy oppressive atmosphere"],
    "powerful":    ["monumental scale", "dramatic low angle", "strong silhouette"],
    "nostalgic":   ["faded warm tones", "film grain texture", "soft focus"],
    "hopeful":     ["dawn light rays", "open horizon", "upward leading lines"],
    "intimate":    ["close-up framing", "warm bokeh background", "gentle soft lighting"],
    "epic":        ["vast wide landscape", "tiny figure against immensity", "establishing shot"],
}

IMAGE_STYLE_MAP: dict[str, str] = {
    "fantasy":          "dark fantasy digital illustration, concept art, cinematic lighting",
    "dark_fantasy":     "dark fantasy digital painting, atmospheric concept art, painterly",
    "sci_fi":           "science fiction concept art, hard sci-fi aesthetic, crisp photorealistic",
    "literary_fiction": "atmospheric fine art, painterly impressionistic style, muted tones",
    "thriller":         "cinematic noir photography style, high contrast, dramatic shadows",
    "mystery":          "atmospheric illustration, chiaroscuro lighting, restrained palette",
    "romance":          "warm soft-focus illustration, intimate lighting, watercolor influence",
    "historical_fiction":"period oil painting style, aged warm tones, classical composition",
    "non_fiction":      "clean editorial photography, minimal graphic design",
    "childrens":        "bright children's book illustration, playful style, bold colors",
    "ya":               "dynamic YA cover illustration, vibrant, character-forward",
    "default":          "atmospheric digital illustration, cinematic lighting",
}

COVER_TYPE_COMPOSITION: dict[str, str] = {
    "object_centered":    "centered object composition, subject isolated against atmospheric background",
    "character_centered": "character portrait composition, subject fills two-thirds of frame",
    "setting_centered":   "wide establishing shot, environment as protagonist, immersive landscape",
    "abstract":           "abstract atmospheric composition, mood through color and texture",
    "typography_centered":"bold typographic design, minimal imagery, maximum negative space for title",
}

GENRE_NEGATIVE_TOKENS: dict[str, list[str]] = {
    "fantasy":          ["photorealistic modern setting", "contemporary clothing", "office environment"],
    "dark_fantasy":     ["bright cheerful colors", "smiling faces", "pastoral scenes"],
    "thriller":         ["bright cheerful colors", "smiling faces", "pastoral idyllic scenery"],
    "literary_fiction": ["cartoon style", "action scene", "saturated primary colors"],
    "romance":          ["dark horror elements", "violence", "cold industrial setting"],
    "mystery":          ["bright sunshine", "crowd scenes", "cheerful expressions"],
    "sci_fi":           ["medieval setting", "nature only", "no technology"],
}

UNIVERSAL_NEGATIVE_TOKENS = [
    "text overlay", "watermark", "signature", "blurry", "low quality",
    "jpeg artifacts", "poorly drawn", "deformed", "extra limbs",
]
```

### 9.2 Cover Prompt Assembler

Create `backend/app/services/cover_prompt_assembler.py`:

```python
from dataclasses import dataclass, field
from typing import Optional
from .cover_visual_language import (
    MOOD_VISUAL_MARKERS, IMAGE_STYLE_MAP,
    COVER_TYPE_COMPOSITION, GENRE_NEGATIVE_TOKENS, UNIVERSAL_NEGATIVE_TOKENS,
)

@dataclass
class CoverPromptResult:
    prompt: str
    negative_prompt: str
    token_count: int
    params_log: dict = field(default_factory=dict)

@dataclass
class ColorParams:
    dominant: str = ""
    accent: str = ""
    temperature: str = ""   # "warm"|"cool"|"neutral"
    contrast: str = ""      # "high"|"mid"|"low"
    saturation: str = ""

class CoverPromptAssembler:
    """
    Deterministically assembles a T2I prompt from structured cover analysis
    parameters. Does not call any LLM. Target output: 120–150 tokens.

    Assembly order (each section is a prompt segment separated by commas):
    1. Image style medium  — most influential token for T2I models
    2. Composition type    — from cover_type
    3. Primary element     — core_tokens of the user-selected entity
    4. Mood visual markers — translated from cover_mood_keywords
    5. Color grading       — from color_palette_structured
    6. Reference style     — if moodboard reference hint is available
    7. Typography space    — always appended for cover format
    """

    MAX_TOKENS = 150

    def assemble(
        self,
        cover_type: str,
        genre: str,
        cover_mood_keywords: list[str],
        primary_element_tokens: list[str],   # core_tokens of selected entity
        color_params: Optional[ColorParams] = None,
        reference_style_hint: Optional[str] = None,
        existing_negative_prompt: Optional[str] = None,
    ) -> CoverPromptResult:

        parts = []
        log = {}

        # 1. Image style
        style = IMAGE_STYLE_MAP.get(genre, IMAGE_STYLE_MAP["default"])
        parts.append(style)
        log["image_style"] = style

        # 2. Composition
        composition = COVER_TYPE_COMPOSITION.get(
            cover_type, COVER_TYPE_COMPOSITION["object_centered"]
        )
        parts.append(composition)
        log["composition"] = composition

        # 3. Primary element (top 4 tokens — beyond 4 adds noise)
        if primary_element_tokens:
            primary_desc = ", ".join(primary_element_tokens[:4])
            parts.append(primary_desc)
            log["primary_tokens"] = primary_element_tokens[:4]

        # 4. Mood → visual markers (1 marker per mood keyword, top 3 moods)
        mood_markers = []
        for kw in cover_mood_keywords[:3]:
            markers = MOOD_VISUAL_MARKERS.get(kw.lower(), [])
            if markers:
                mood_markers.append(markers[0])
        if mood_markers:
            parts.append(", ".join(mood_markers))
        log["mood_markers"] = mood_markers

        # 5. Color grading
        if color_params and color_params.dominant:
            color_seg = f"{color_params.dominant} color palette"
            if color_params.accent:
                color_seg += f", {color_params.accent} accent"
            if color_params.contrast:
                color_seg += f", {color_params.contrast} contrast"
            parts.append(color_seg)
            log["color"] = vars(color_params)

        # 6. Reference style hint
        if reference_style_hint:
            parts.append(reference_style_hint)
            log["reference_hint"] = reference_style_hint

        # 7. Always leave space for typography
        parts.append("space at top for title text, book cover format")

        prompt = ", ".join(p for p in parts if p.strip())

        # Negative prompt
        neg_parts = []
        if existing_negative_prompt:
            neg_parts.append(existing_negative_prompt)
        genre_neg = ", ".join(GENRE_NEGATIVE_TOKENS.get(genre, []))
        if genre_neg:
            neg_parts.append(genre_neg)
        neg_parts.append(", ".join(UNIVERSAL_NEGATIVE_TOKENS))
        negative_prompt = ", ".join(p for p in neg_parts if p.strip())

        return CoverPromptResult(
            prompt=prompt,
            negative_prompt=negative_prompt,
            token_count=len(prompt.split()),
            params_log=log,
        )
```

### 9.3 FLUX.1 Kontext Provider

Replace the stub in `backend/app/services/t2i_providers/flux_provider.py`:

```python
import os
import logging
from dataclasses import dataclass
from .base import BaseT2IProvider

logger = logging.getLogger(__name__)

@dataclass
class T2IGenerationResult:
    url: str
    width: int | None = None
    height: int | None = None
    model: str = ""
    prompt_used: str = ""
    provider: str = ""

class FluxKontextProvider(BaseT2IProvider):
    """
    FLUX.1 Pro (text-only) and FLUX.1 Kontext Pro (image+text) via fal.ai.
    Kontext is used when a moodboard reference URL is supplied — it performs
    style transfer from the reference image, which directly serves the
    moodboard → generation pipeline.

    Requires: FAL_API_KEY environment variable.
    Install: pip install fal-client
    """

    TEXT_ENDPOINT    = "fal-ai/flux-pro/v1.1"
    KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"

    def __init__(self):
        api_key = os.getenv("FAL_API_KEY")
        if not api_key:
            raise EnvironmentError("FAL_API_KEY not set")
        os.environ["FAL_KEY"] = api_key

    def is_available(self) -> bool:
        return bool(os.getenv("FAL_API_KEY"))

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        negative_prompt: str | None = None,
        aspect_ratio: str = "2:3",
        num_inference_steps: int = 28,
        guidance_scale: float = 3.5,
    ) -> T2IGenerationResult:
        try:
            import fal_client
        except ImportError:
            raise RuntimeError("fal-client not installed. Run: pip install fal-client")

        endpoint = self.KONTEXT_ENDPOINT if image_url else self.TEXT_ENDPOINT
        args: dict = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }
        if image_url:
            args["image_url"] = image_url
        if negative_prompt:
            args["negative_prompt"] = negative_prompt

        logger.info(f"FLUX generate via {endpoint}, prompt length={len(prompt.split())} tokens")
        result = await fal_client.run_async(endpoint, arguments=args)
        image_data = result["images"][0]

        return T2IGenerationResult(
            url=image_data["url"],
            width=image_data.get("width"),
            height=image_data.get("height"),
            model=endpoint,
            prompt_used=prompt,
            provider="flux_kontext" if image_url else "flux_pro",
        )
```

### 9.4 DALL-E Provider (Fallback)

Create `backend/app/services/t2i_providers/dalle_provider.py`:

```python
import os
import logging
from .base import BaseT2IProvider
from .flux_provider import T2IGenerationResult

logger = logging.getLogger(__name__)

class DalleProvider(BaseT2IProvider):
    """
    DALL-E 3 HD via OpenAI API. Fallback when FAL_API_KEY is not set.
    Best for: complex prompts with many constraints, reliable prompt adherence.
    Limitation: no image-to-image / style reference input.
    """

    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,  # ignored — DALL-E 3 does not support img2img
        negative_prompt: str | None = None,
        aspect_ratio: str = "2:3",
        **kwargs,
    ) -> T2IGenerationResult:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if image_url:
            logger.warning("DalleProvider: image_url ignored (DALL-E 3 has no img2img). "
                           "Use FluxKontextProvider for moodboard-conditioned generation.")

        # DALL-E closest portrait size
        size = "1024x1792"

        logger.info(f"DALL-E 3 generate, prompt length={len(prompt.split())} tokens")
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="hd",
            n=1,
        )
        img = response.data[0]
        return T2IGenerationResult(
            url=img.url,
            model="dall-e-3-hd",
            prompt_used=img.revised_prompt or prompt,
            provider="dalle",
        )
```

### 9.5 Engine Selector — T2I Extensions

Extend `backend/app/services/engine_selector.py`:

```python
def get_cover_t2i_provider() -> "BaseT2IProvider":
    """
    Returns the best available T2I provider for cover generation.
    Priority: FLUX Kontext (supports moodboard reference) > DALL-E 3.
    Raises ProviderNotConfiguredError if neither is available.
    """
    from .t2i_providers.flux_provider import FluxKontextProvider
    from .t2i_providers.dalle_provider import DalleProvider

    preferred = os.getenv("COVER_T2I_PROVIDER", "flux_kontext")

    if preferred == "flux_kontext" and os.getenv("FAL_API_KEY"):
        return FluxKontextProvider()
    if os.getenv("OPENAI_API_KEY"):
        return DalleProvider()
    raise ProviderNotConfiguredError(
        "No T2I provider available. Set FAL_API_KEY (recommended) or OPENAI_API_KEY."
    )
```

### 9.6 Cover Generation — Wire Real T2I

Update `backend/app/routers/illustrations.py` — the `POST /cover-concepts/generate` background task:

```python
async def _generate_concept_background(
    book_id: int, concept_id: int, prompt: str,
    negative_prompt: str, reference_url: str | None,
    db_session_factory,
):
    """
    Called per concept. Replaces the abstract_provider stub with real T2I.
    Uses: CoverPromptAssembler → get_cover_t2i_provider → persist result.
    """
    db = db_session_factory()
    try:
        crud.update_cover_concept(db, concept_id, status="generating")

        # Get primary element tokens for assembler
        cover_analysis = crud.get_cover_analysis(db, book_id)
        primary_tokens = _resolve_primary_element_tokens(cover_analysis, db)

        # Build structured prompt via assembler
        assembler = CoverPromptAssembler()
        color_params = _parse_color_params(cover_analysis.color_palette_structured)
        prompt_result = assembler.assemble(
            cover_type=cover_analysis.cover_type or "object_centered",
            genre=cover_analysis.book.genre or "default",
            cover_mood_keywords=json.loads(cover_analysis.cover_mood_keywords or "[]"),
            primary_element_tokens=primary_tokens,
            color_params=color_params,
            existing_negative_prompt=cover_analysis.cover_negative_prompt,
        )

        # Use prompt override if explicitly provided by user
        final_prompt = prompt if prompt else prompt_result.prompt
        final_neg = negative_prompt if negative_prompt else prompt_result.negative_prompt

        # Generate
        provider = get_cover_t2i_provider()
        result = await provider.generate(
            prompt=final_prompt,
            image_url=reference_url,
            negative_prompt=final_neg,
            aspect_ratio="2:3",
        )

        crud.update_cover_concept(db, concept_id,
                                  status="complete",
                                  image_path=result.url,
                                  prompt_used=final_prompt)
    except Exception as e:
        logger.error(f"Cover concept generation failed: {e}")
        crud.update_cover_concept(db, concept_id, status="failed")
    finally:
        db.close()

def _resolve_primary_element_tokens(cover_analysis, db) -> list[str]:
    """
    Returns core_tokens of the user-selected primary element.
    Priority: primary_cover_artefact_id > primary_cover_character_id > primary_cover_location_id.
    Falls back to symbolic_anchors if no primary is set.
    """
    if cover_analysis.primary_cover_artefact_id:
        artefact = crud.get_artefact(db, cover_analysis.primary_cover_artefact_id)
        if artefact and artefact.entity_visual_tokens_json:
            return json.loads(artefact.entity_visual_tokens_json).get("core_tokens", [])
    if cover_analysis.primary_cover_character_id:
        char = crud.get_character(db, cover_analysis.primary_cover_character_id)
        if char and char.entity_visual_tokens_json:
            return json.loads(char.entity_visual_tokens_json).get("core_tokens", [])
    if cover_analysis.primary_cover_location_id:
        loc = crud.get_location(db, cover_analysis.primary_cover_location_id)
        if loc and loc.entity_visual_tokens_json:
            return json.loads(loc.entity_visual_tokens_json).get("core_tokens", [])
    # Fallback
    return json.loads(cover_analysis.symbolic_anchors or "[]")
```

Also update `POST /cover-concepts/generate` to pass the first cover reference URL:
```python
# In the endpoint handler, before firing background task:
cover_refs = crud.get_selected_reference_urls(db, book_id, "cover")
reference_url = cover_refs[0] if cover_refs else None
# Pass reference_url to _generate_concept_background
```

### 9.7 Update .env.example and requirements.txt

Add to `backend/.env.example`:
```bash
# T2I Generation
FAL_API_KEY=                     # Primary: FLUX Kontext via fal.ai
COVER_T2I_PROVIDER=flux_kontext  # "flux_kontext" | "dalle"
```

Add to `backend/requirements.txt`:
```
fal-client>=0.10.0
```

### 9.8 Unit Tests — Phase 9

File: `backend/tests/unit/test_cover_prompt_assembler.py`

```python
from services.cover_prompt_assembler import CoverPromptAssembler, ColorParams
from services.cover_visual_language import IMAGE_STYLE_MAP, MOOD_VISUAL_MARKERS

def test_assembler_starts_with_image_style():
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="fantasy",
        cover_mood_keywords=["dark"], primary_element_tokens=["glowing boulder"]
    )
    assert result.prompt.startswith("dark fantasy digital illustration")

def test_assembler_includes_composition():
    result = CoverPromptAssembler().assemble(
        cover_type="character_centered", genre="romance",
        cover_mood_keywords=[], primary_element_tokens=[]
    )
    assert "character portrait" in result.prompt

def test_assembler_translates_mood_to_visual_markers():
    result = CoverPromptAssembler().assemble(
        cover_type="abstract", genre="thriller",
        cover_mood_keywords=["foreboding", "intense"],
        primary_element_tokens=[]
    )
    assert any(m in result.prompt for m in MOOD_VISUAL_MARKERS["foreboding"])

def test_assembler_includes_color_params():
    cp = ColorParams(dominant="deep black", accent="amber", contrast="high")
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="dark_fantasy",
        cover_mood_keywords=[], primary_element_tokens=[], color_params=cp
    )
    assert "deep black" in result.prompt
    assert "amber" in result.prompt

def test_assembler_uses_top_4_primary_tokens_only():
    tokens = ["a", "b", "c", "d", "e", "f"]
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="fantasy",
        cover_mood_keywords=[], primary_element_tokens=tokens
    )
    assert "e" not in result.prompt  # 5th token excluded
    assert "f" not in result.prompt

def test_assembler_always_appends_typography_space():
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="mystery",
        cover_mood_keywords=[], primary_element_tokens=[]
    )
    assert "space at top for title" in result.prompt

def test_assembler_negative_includes_genre_tokens():
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="thriller",
        cover_mood_keywords=[], primary_element_tokens=[]
    )
    assert "bright cheerful colors" in result.negative_prompt

def test_assembler_negative_always_includes_universal_tokens():
    result = CoverPromptAssembler().assemble(
        cover_type="abstract", genre="literary_fiction",
        cover_mood_keywords=[], primary_element_tokens=[]
    )
    assert "watermark" in result.negative_prompt

def test_assembler_token_count_under_limit():
    result = CoverPromptAssembler().assemble(
        cover_type="object_centered", genre="fantasy",
        cover_mood_keywords=["dark", "intense", "foreboding", "epic", "powerful"],
        primary_element_tokens=["glowing boulder", "pinkish moss", "sinister glow", "large natural rock"],
        color_params=ColorParams("deep blue black", "amber glow", "cool", "high", "desaturated"),
        reference_style_hint="painterly atmospheric",
    )
    assert result.token_count <= 150

def test_visual_language_maps_cover_all_genres():
    assert "fantasy" in IMAGE_STYLE_MAP
    assert "thriller" in IMAGE_STYLE_MAP
    assert "literary_fiction" in IMAGE_STYLE_MAP
    assert len(MOOD_VISUAL_MARKERS) >= 8

@pytest.mark.skipif(not os.getenv("FAL_API_KEY"), reason="requires FAL_API_KEY")
async def test_flux_provider_generates_image():
    from t2i_providers.flux_provider import FluxKontextProvider
    provider = FluxKontextProvider()
    result = await provider.generate(
        prompt="dark fantasy illustration, glowing boulder, concept art, 2:3 ratio",
        aspect_ratio="2:3",
    )
    assert result.url.startswith("http")
    assert result.provider == "flux_pro"

@pytest.mark.skipif(not os.getenv("FAL_API_KEY"), reason="requires FAL_API_KEY")
async def test_flux_kontext_with_reference():
    from t2i_providers.flux_provider import FluxKontextProvider
    provider = FluxKontextProvider()
    result = await provider.generate(
        prompt="dark fantasy illustration, glowing boulder",
        image_url="https://images.unsplash.com/photo-example",  # any valid image
    )
    assert result.provider == "flux_kontext"

def test_get_cover_t2i_provider_returns_flux_when_key_set(monkeypatch):
    monkeypatch.setenv("FAL_API_KEY", "test")
    from services.engine_selector import get_cover_t2i_provider
    from t2i_providers.flux_provider import FluxKontextProvider
    assert isinstance(get_cover_t2i_provider(), FluxKontextProvider)

def test_get_cover_t2i_provider_falls_back_to_dalle(monkeypatch):
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    from services.engine_selector import get_cover_t2i_provider
    from t2i_providers.dalle_provider import DalleProvider
    assert isinstance(get_cover_t2i_provider(), DalleProvider)
```

---

## Phase 10 — Frontend: SetupPage + WorkflowNav
**Dependency:** Phase 8  
**Files touched:** `frontend/src/pages/SetupPage.tsx`, `frontend/src/components/WorkflowNav.tsx`, `frontend/src/App.tsx`

### 10.1 SetupPage — Workflow Path + Genre + Target Audience

Below the existing style/genre selectors, add:

```typescript
// 1. Workflow path selector
// Two radio cards:
// [Book Cover]  — "Generate a KDP-ready cover. Fastest path."
// [Full Book]   — "Cover + interior illustrations + reading view."
// On selection: setWorkflowType(value)

// 2. Genre selector (already exists, but must now drive entity activation defaults)
// On genre change: setGenre(value); setActiveEntityTypes(getDefaultActivations(genre, workflowType))
const GENRE_DEFAULT_ACTIVATIONS: Record<string, string[]> = {
  fantasy:          ["cover", "characters", "locations", "artefacts"],
  sci_fi:           ["cover", "characters", "locations"],
  childrens:        ["cover", "characters"],
  romance:          ["cover", "characters"],
  thriller:         ["cover"],
  mystery:          ["cover"],
  literary_fiction: ["cover"],
  historical_fiction:["cover", "locations", "artefacts"],
  default:          ["cover"],
}

// 3. [GAP] Target audience selector
// Dropdown: "Children" | "Young Adult" | "Adult" | "Literary/Academic"
// Values: "children" | "ya" | "adult" | "literary"
// On selection: setTargetAudience(value)
// Note: For "Full Book" workflow, display all four entity types regardless of genre

// 4. [GAP] is_well_known_book checkbox
// "This is a well-known published book"
// When checked: show text input "Original title (English)" — well_known_book_title
// Passed in analyze request as is_well_known and well_known_book_title

// 5. Update analyzeBook() call to send:
// entity_types, genre, target_audience, is_well_known, well_known_book_title
```

### 10.2 WorkflowNav — Dual Path Support

Derive steps from `workflowType` and `activeEntityTypes` from context:

```typescript
const COVER_ONLY_STEPS = [
  { label: "Upload",       path: "manuscript-upload" },
  { label: "AI Analysis",  path: "analysis-review" },
  { label: "Mood Board",   path: "mood-board" },
  { label: "Cover Studio", path: "studio/cover" },
  { label: "Preview",      path: "preview" },
]

const FULL_BOOK_STEPS = [
  { label: "Upload",       path: "manuscript-upload" },
  { label: "AI Analysis",  path: "analysis-review" },
  { label: "Mood Board",   path: "mood-board" },
  { label: "Visual Bible", path: "visual-bible" },
  { label: "Studio",       path: "studio" },
  { label: "Preview",      path: "preview" },
]
// Each step shows a per-entity completion indicator from analysisProgress context
```

### 10.3 App.tsx — New Routes

```typescript
{ path: "mood-board",    element: <MoodBoardPage /> }
{ path: "studio",        element: <StudioPage /> }
{ path: "studio/cover",  element: <CoverStudioPage /> }
{ path: "studio/text",   element: <TextStudioPage /> }
// Existing routes (review-search, visual-bible) retained for backward compat
```

### 10.4 Unit Tests — Phase 10

```typescript
// WorkflowNav.test.tsx
test('cover_only path shows Cover Studio, not Visual Bible', () => { ... })
test('full_book path shows Visual Bible and Studio', () => { ... })

// SetupPage.test.tsx
test('selecting fantasy genre activates characters and locations', async () => { ... })
test('selecting full_book workflow always activates all four types', async () => { ... })
test('target audience dropdown present with adult as default', () => { ... })   // [GAP]
test('is_well_known checkbox shows title input when checked', async () => { ... }) // [GAP]
test('analyzeBook includes genre, target_audience, entity_types', async () => { ... }) // [GAP]
```

---

## Phase 11 — Frontend: AnalysisReviewPage + Cover Brief Editor
**Dependency:** Phase 10  
**Files touched:** `frontend/src/pages/AnalysisReviewPage.tsx`

### 11.1 Four-Tab Structure

Refactor `AnalysisReviewPage` into a tabbed interface:

```typescript
// Tabs: Cover | Characters | Locations | Artefacts
// Cover: always visible. Others: visible but show activation CTA if not in activeEntityTypes.

// Cover tab:
// - Readonly fields: thematic_statement, emotional_promise (display only; editable in Cover Brief Editor below)
// - Dominant motifs (tag list), symbolic_anchors (tag list), cover_mood_keywords (tag list)
// - genre_conventions (readonly info banner)
// - cover_t2i_prompt (textarea, editable) — this is the RAW LLM prompt, shown for transparency
// - cover_negative_prompt (textarea)
// - Save button → PATCH /cover-analysis
// - [GAP] Cover Brief Editor section (see 11.2 below)

// Characters tab: existing entity table (is_main readonly badge, is_selected_for_reference toggle)
// [GAP] Important: "is_main" shown as readonly badge ("AI-identified protagonist").
// "Select for reference search" toggle writes is_selected_for_reference, not is_main.

// Locations tab: same as characters
// Artefacts tab: new — name, physical_description, symbolic_role, narrative_function, is_main toggle

// Per-tab: progress indicator from analysisProgress; "Run Analysis" button if entity not yet run
```

### 11.2 Cover Brief Editor [GAP]

This is a new section within the Cover tab. It allows the user to make the key creative decisions about the cover, with AI recommendations clearly labelled as suggestions.

```typescript
// CoverBriefEditor component (inside Cover tab):
//
// Section: "Cover Type"
// Selector: Object-Centered | Character-Centered | Setting-Centered | Abstract | Typography
// Pre-filled from cover_analysis.cover_type (AI suggestion)
// Label: "AI suggests: [cover_type]" with ability to accept or override
// On change → PATCH /cover-analysis { cover_type }
//
// Section: "Primary Element" (shown after cover_type is set)
// Depends on cover_type:
//   - Object-Centered: dropdown of artefacts, each showing name + physical_description snippet
//   - Character-Centered: dropdown of characters, each showing name + physical_description snippet
//   - Setting-Centered: dropdown of locations, each showing name + atmosphere snippet
//   - Abstract / Typography-Centered: no primary element needed (hidden)
// AI highlights recommended candidate (cover_analysis.primary_cover_*_id suggestion)
// User selects exactly ONE primary element
// On change → PATCH /cover-analysis { primary_cover_artefact_id | primary_cover_character_id | primary_cover_location_id }
//
// Section: "Style Reference (Moodboard)"
// Shows current cover reference images (cover_selections from visual-bible/approve)
// "Upload style reference" button → POST /reference-upload (entity_type=cover)
// Note: "This image will be used as a style reference for cover generation via FLUX Kontext"
//
// Section: "Assembled Prompt Preview" (readonly, auto-updates)
// Calls api.previewCoverPrompt(bookId) → GET endpoint that runs assembler and returns prompt
// Shows the deterministic assembled prompt (not the raw LLM prompt)
// Allows user to understand what will be sent to the T2I model
// [This preview endpoint can be added as GET /cover-concepts/preview-prompt in illustrations.py]
```

**New backend endpoint for prompt preview:**
```
GET /api/books/{book_id}/cover-concepts/preview-prompt
→ { prompt: str, negative_prompt: str, params_log: dict }
Runs CoverPromptAssembler with current cover_analysis data and primary element.
No T2I call made. Used by the UI to show the user what will be generated.
```

### 11.3 Unit Tests — Phase 11

```typescript
// AnalysisReviewPage.test.tsx
test('shows Cover tab by default', () => { ... })
test('cover tab renders thematic_statement', () => { ... })
test('inactive entity tab shows activation CTA', () => { ... })
test('is_main shown as readonly badge, not editable toggle', () => { ... })   // [GAP]
test('is_selected_for_reference toggle updates without touching is_main', () => { ... }) // [GAP]
test('cover type selector pre-fills from AI suggestion', () => { ... })          // [GAP]
test('primary element list changes based on cover_type selection', () => { ... }) // [GAP]
test('assembled prompt preview shown when cover_type and primary set', () => { ... }) // [GAP]
test('artefacts tab renders artefact list', () => { ... })
```

---

## Phase 12 — Frontend: MoodBoardPage
**Dependency:** Phase 11  
**Files touched:** `frontend/src/pages/MoodBoardPage.tsx` (new), `frontend/src/App.tsx`

### 12.1 New `MoodBoardPage.tsx`

Replaces the workflow role of `ReviewSearchPage` + `ReviewSearchResultPage`. Those pages remain in the codebase but WorkflowNav no longer links to them.

```typescript
// Tabs: Cover | Characters | Locations | Artefacts
// Only active entity types render populated tabs.

// Per-tab layout:
// TOP: Collapsible "Search Queries" panel
//   - Editable query inputs from GET /proposed-search-queries
//   - "Re-run search" button per entity type
//   - Provider selector for this tab's entity type
//
// MAIN: Image grid
//   - Grouped by entity name
//   - Image cards: thumbnail, source badge (behance/dribbble for cover), select checkbox
//   - "Upload your own" button → POST /reference-upload
//
// BOTTOM: "Save Mood Board" → POST /visual-bible/approve → navigate to next step

// Cover tab: single pool (no per-entity grouping), behance/dribbble badges prominent
// On mount: GET /reference-results → if empty, show GET /proposed-search-queries + "Run Search" CTA
```

### 12.2 Unit Tests — Phase 12

```typescript
test('renders four tabs', () => { ... })
test('search queries panel collapsed by default', () => { ... })
test('expanding panel shows editable queries', async () => { ... })
test('selecting image highlights it', async () => { ... })
test('save mood board calls approveVisualBible', async () => { ... })
```

---

## Phase 13 — Frontend: CoverStudioPage + TextStudioPage
**Dependency:** Phase 12 (MoodBoardPage, which completes the moodboard reference selection)  
**Files touched:** `frontend/src/pages/CoverStudioPage.tsx` (new), `frontend/src/pages/TextStudioPage.tsx` (new)

### 13.1 `CoverStudioPage.tsx`

The cover studio now connects to real T2I (Phase 9). The UI reflects that.

```typescript
// Layout:
// LEFT: Generation controls (1/3 width)
//   - Assembled Prompt display (readonly, from GET /cover-concepts/preview-prompt)
//     with "Edit raw prompt" toggle to override with manual text
//   - Negative prompt editor (pre-filled from cover_analysis)
//   - Style variant selector: illustrated | photographic | abstract | typographic
//   - Concept count: 1–3 (default 3)
//   - Moodboard reference thumbnail (if cover references exist from Phase 12)
//     with label: "Style conditioned from your moodboard" [GAP]
//   - "Generate Covers" button → POST /cover-concepts/generate
//     (now triggers real T2I via FluxKontextProvider; shows spinner)
//
// RIGHT: Concept gallery (2/3 width)
//   - 1–3 concept cards
//   - Status: pending spinner | generating animation | complete image
//   - Poll GET /cover-concepts every 3s while any status == "generating"
//   - "Select" button per card → POST /cover-concepts/{id}/select
//   - Selected card: highlighted border, checkmark
//   - "Regenerate" button on selected card
//   - params_log accordion per card (shows what tokens went into the prompt) [GAP]
//
// BOTTOM: "Export to KDP" (enabled only when one concept selected)
```

### 13.2 `TextStudioPage.tsx` (Full Book only)

```typescript
// LEFT: Scene list (sorted by illustration_priority high→low)
//   - Status indicator per scene
//   - Click → load in right panel
//
// RIGHT: Scene editor
//   - Scene title + narrative_summary (readonly)
//   - Characters, locations, artefacts in scene (readonly chips)
//   - Prompt editor (pre-filled from scene.t2i_prompt_json.abstract)
//   - "Generate Illustration" → POST /scenes/{id}/generate-illustration
//     (T2I stub backend-side; page handles the 202 gracefully with "Queued" state)
//   - Illustration preview (image or placeholder)
```

### 13.3 Unit Tests — Phase 13

```typescript
// CoverStudioPage.test.tsx
test('assembled prompt pre-fills from API', async () => { ... })         // [GAP]
test('moodboard reference thumbnail shown when cover refs exist', () => { ... }) // [GAP]
test('generate calls generateCoverConcepts with correct body', async () => { ... })
test('concepts poll every 3s while generating', async () => {
  vi.useFakeTimers()
  // assert polling occurs
})
test('export disabled when no concept selected', () => { ... })
test('export enabled when concept selected', () => { ... })
test('params_log accordion visible on concept card', () => { ... })     // [GAP]
test('selecting concept calls selectCoverConcept', async () => { ... })
```

---

## Phase 14 — Frontend: Preview + E2E Tests
**Dependency:** Phases 10–13  
**Files touched:** `frontend/src/pages/ReadingPage.tsx`, `frontend/playwright.config.ts` (new), `frontend/e2e/` (new), `backend/tests/e2e/test_e2e_four_entity_pipeline.py`

### 14.1 Preview + Reading Mode Unification

```typescript
// Read ?mode= from URL
// mode=reading: hide WorkflowNav, hide edit controls, clean text+illustrations
// mode=preview (default): show WorkflowNav, inline edit controls
// Toggle button: "Reading View" / "Edit View"
// Export actions (preview mode only):
// - Cover-Only: "Export Cover (KDP)" → POST /cover-concepts/{id}/export (stub)
// - Full Book: "Export Full Book (KDP)" → stub
```

### 14.2 E2E Test Setup

Create `frontend/playwright.config.ts`:
```typescript
import { defineConfig } from '@playwright/test'
export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://localhost:5173', trace: 'on-first-retry' },
  webServer: { command: 'npm run dev', port: 5173, reuseExistingServer: !process.env.CI },
})
```

### 14.3 Frontend E2E Tests

File: `frontend/e2e/cover_only_path.spec.ts`

```typescript
test.describe('Cover-Only Path', () => {
  test('upload → analysis → cover brief editor → mood board → cover studio', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Book')
    await page.setInputFiles('input[type=file]', 'e2e/fixtures/short_story.txt')
    await page.fill('input[name=title]', 'Test Book')
    await page.selectOption('select[name=genre]', 'thriller')
    await page.click('text=Cover Only')
    await page.click('text=Continue')

    await expect(page.locator('text=Cover Studio')).toBeVisible()
    await expect(page.locator('text=Visual Bible')).not.toBeVisible()

    await page.click('text=Run Analysis')
    await expect(page.locator('[data-testid=cover-tab-complete]')).toBeVisible({timeout: 30000})

    // Cover Brief Editor
    await page.click('text=Cover')
    await expect(page.locator('[data-testid=cover-type-selector]')).toBeVisible()  // [GAP]
    await expect(page.locator('[data-testid=assembled-prompt-preview]')).toBeVisible() // [GAP]

    // Characters inactive for thriller
    await page.click('text=Characters')
    await expect(page.locator('text=Activate Characters')).toBeVisible()

    // Mood Board
    await page.click('text=Mood Board')
    await expect(page.locator('text=Run Search')).toBeVisible()

    // Cover Studio
    await page.click('text=Cover Studio')
    await expect(page.locator('text=Generate Covers')).toBeVisible()
    await page.click('text=Generate Covers')
    await expect(page.locator('[data-testid=concept-card]')).toHaveCount(3)
  })

  test('activating characters mid-flow triggers entity analysis', async ({ page }) => { ... })
  test('is_main badge is readonly in entity tabs', async ({ page }) => { ... })  // [GAP]
})
```

File: `frontend/e2e/full_book_path.spec.ts`

```typescript
test.describe('Full Book Path', () => {
  test('all four entity tabs are active for full_book', async ({ page }) => { ... })
  test('scene display shows top N, show-all button reveals more', async ({ page }) => { ... }) // [GAP]
  test('preview mode toggle hides workflow chrome', async ({ page }) => { ... })
})
```

### 14.4 Backend E2E Tests

File: `backend/tests/e2e/test_e2e_four_entity_pipeline.py` — extend existing file:

```python
def test_cover_type_set_after_analysis(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.get(f"/api/books/{book_id}/cover-analysis")
    if r.status_code == 200:
        assert r.json().get("cover_type") is not None      # [GAP]

def test_color_palette_structured_after_analysis(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.get(f"/api/books/{book_id}/cover-analysis")
    if r.status_code == 200:
        cp = r.json().get("color_palette_structured")
        if cp:
            assert "dominant" in cp                         # [GAP]

def test_is_main_unchanged_after_entity_selections(full_pipeline_client):
    client, book_id = full_pipeline_client
    chars_before = {c["id"]: c["is_main"] for c in
                    client.get(f"/api/books/{book_id}/characters").json()}
    # Simulate entity-selections update
    client.put(f"/api/books/{book_id}/entity-selections",
               json={"characters": [{"id": k, "is_main": 0} for k in chars_before],
                     "locations": []})
    chars_after = {c["id"]: c["is_main"] for c in
                   client.get(f"/api/books/{book_id}/characters").json()}
    assert chars_before == chars_after                      # [GAP: BUG-1 fix verified]

def test_scenes_count_above_3_for_standard_manuscript(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.get(f"/api/books/{book_id}/scenes?show_all=true")
    assert len(r.json()) >= 5                               # [GAP: BUG-2 fix verified]

@pytest.mark.skipif(not os.getenv("FAL_API_KEY"), reason="requires FAL_API_KEY")
def test_cover_concept_generates_real_image(full_pipeline_client):
    client, book_id = full_pipeline_client
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate",
                    json={"concept_count": 1})
    assert r.status_code == 200
    concept_id = r.json()["concepts"][0]["id"]
    # Poll until complete
    for _ in range(30):
        import time; time.sleep(3)
        concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
        c = next((c for c in concepts if c["id"] == concept_id), None)
        if c and c["status"] == "complete":
            assert c["image_path"].startswith("http")       # [GAP: real T2I]
            break
    else:
        pytest.fail("Cover concept did not complete within 90 seconds")
```

---

## Phase 15 — Visual Identity (Noctua Branding)
**Dependency:** None (fully independent — run any time after Phase 8, optionally on its own branch)  
**Files touched:** `frontend/src/components/ChapterHeader.tsx` (new), `frontend/src/components/NoctuaIllustration.tsx` (new), `frontend/src/data/chapters.ts` (new), `frontend/public/illustrations/` (new directory), `frontend/index.html`, `frontend/src/index.css`, `frontend/src/App.tsx`, `frontend/src/components/WorkflowNav.tsx`

### 15.1 SVG Illustration Assets

All SVGs in `frontend/public/illustrations/`. Files in `public/` are served at `/illustrations/filename.svg` without import statements.

Required files and their scenes:
```
noctua-dashboard.svg   — The Study: persona at lamp-lit desk, owl by window
noctua-upload.svg      — Ch.1: owl flies in carrying manuscript
noctua-analysis.svg    — Ch.2: glowing map unfurling, characters appearing
noctua-review.svg      — Ch.3: persona at cork board, pinning notes
noctua-moodboard.svg   — Ch.4: persona stepping back from image wall, owl on shoulder
noctua-visualbible.svg — Ch.5: shadowy figures stepping out of open book
noctua-coverstudio.svg — Ch.6: persona facing glowing blank canvas, brush raised
noctua-preview.svg     — Ch.7: floating open book, pages turning, owl resting on it
noctua-export.svg      — Ch.8: owl flying out of window with finished book
```

Production checklist: viewBox `0 0 600 400`; strokes use `currentColor`; amber `#c9a84c` as fill on specific elements only; transparent background; no embedded text; under 30KB per file.

If illustrations are not ready: create placeholder SVGs (simple owl silhouette + filename label). Zero code changes needed when final assets arrive.

### 15.2 Typography — Google Fonts

Add to `frontend/index.html` `<head>`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;1,400;1,600&display=swap" rel="stylesheet">
```

Add to `frontend/src/index.css`:
```css
:root {
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans:  'Inter', system-ui, sans-serif;
  --color-ink:  #1a1a2e;
  --color-amber: #c9a84c;
  --color-ink-secondary: #4a4a6a;
}
.noctua-chapter-number { font-family: var(--font-serif); font-style: italic; font-size: 0.875rem; color: var(--color-amber); letter-spacing: 0.05em; }
.noctua-chapter-title  { font-family: var(--font-serif); font-weight: 600; font-size: 1.5rem; line-height: 1.2; color: var(--color-ink); }
.noctua-instruction    { font-family: var(--font-sans); font-size: 0.9375rem; line-height: 1.6; color: var(--color-ink-secondary); }
.noctua-wordmark       { font-family: var(--font-serif); font-variant: small-caps; letter-spacing: 0.12em; font-weight: 600; color: var(--color-ink); }
```

### 15.3 Chapter Metadata

Create `frontend/src/data/chapters.ts`:
```typescript
export interface ChapterMeta { number: string; title: string; instruction: string; illustration: string; }

export const CHAPTERS: Record<string, ChapterMeta> = {
  '/': { number: '', title: 'The Study', instruction: 'Your manuscripts wait here...', illustration: 'noctua-dashboard.svg' },
  'manuscript-upload': { number: 'One', title: 'The Manuscript Arrives', instruction: 'Hand over your manuscript...', illustration: 'noctua-upload.svg' },
  'analysis-review': { number: 'Two', title: 'The Oracle Reads', instruction: 'The Oracle has mapped your manuscript...', illustration: 'noctua-review.svg' },
  'mood-board': { number: 'Three', title: 'The Vision Takes Shape', instruction: 'Choose your visual references...', illustration: 'noctua-moodboard.svg' },
  'visual-bible': { number: 'Four', title: 'The Characters Awaken', instruction: 'Your entities take consistent visual form...', illustration: 'noctua-visualbible.svg' },
  'studio/cover': { number: 'Five', title: 'The Cover Reveals Itself', instruction: 'Generate multiple cover concepts...', illustration: 'noctua-coverstudio.svg' },
  'studio': { number: 'Five', title: 'The Illustrations Are Born', instruction: 'Scene by scene, your manuscript finds its visual voice...', illustration: 'noctua-coverstudio.svg' },
  'preview': { number: 'Six', title: 'The Book Breathes', instruction: 'See your illustrated manuscript for the first time...', illustration: 'noctua-preview.svg' },
}

export function getChapterForPath(pathname: string): ChapterMeta | null {
  if (CHAPTERS[pathname]) return CHAPTERS[pathname]
  if (pathname.includes('studio/cover')) return CHAPTERS['studio/cover']
  if (pathname.includes('studio')) return CHAPTERS['studio']
  const segment = pathname.split('/').filter(Boolean).pop() ?? ''
  return CHAPTERS[segment] ?? null
}
```

### 15.4 NoctuaIllustration Component

Create `frontend/src/components/NoctuaIllustration.tsx`:
```typescript
export function NoctuaIllustration({ filename, alt, className }: Props) {
  return (
    <img src={`/illustrations/${filename}`} alt={alt} className={className}
      width={300} height={200} style={{ objectFit: 'contain' }}
      onError={(e) => { (e.target as HTMLImageElement).style.display = 'none' }} />
  )
}
```

### 15.5 ChapterHeader Component

Create `frontend/src/components/ChapterHeader.tsx` — collapsible header with chapter number, title, instruction, and illustration. Collapse preference persisted to `localStorage` under key `noctua_chapter_header_collapsed`. Default: expanded. Resets to expanded on first visit to a new page if no preference saved yet.

Add `<ChapterHeader />` once in `WorkflowLayout.tsx` just above `<Outlet />` — renders on every workflow page automatically.

For `HomePage.tsx` (outside WorkflowLayout) add `<ChapterHeader />` manually at page top.

### 15.6 WorkflowNav Visual Update

Each step indicator shows:
- Small illustration (48×32px): full color if active, 30% opacity otherwise
- Checkmark overlay on completed steps
- Chapter number label below (abbreviated when inactive)

### 15.7 App Renaming

Replace all occurrences of "YRead", "StoryForge AI", "StoryForge" with "Noctua":
- `frontend/index.html`: `<title>Noctua</title>`
- `frontend/src/App.tsx`: app name constants
- `backend/app/main.py`: `FastAPI(title="Noctua API")`
- `package.json`: `"name": "noctua-frontend"`
- `docs/codebase_snapshot.md`: header line

### 15.8 Unit Tests — Phase 15

```typescript
// ChapterHeader.test.tsx
test('renders correct title for upload route', () => { ... })
test('renders instruction sentence', () => { ... })
test('expanded by default when no localStorage preference', () => { ... })
test('collapses on Hide click and persists to localStorage', async () => { ... })
test('respects collapsed preference on remount', () => { ... })
test('returns null for unknown route', () => { ... })
test('illustration img has correct src', () => { ... })
test('illustration onError hides image gracefully', async () => { ... })

// getChapterForPath
test('resolves root path to The Study', () => { ... })
test('resolves nested workflow path by last segment', () => { ... })
test('resolves studio/cover nested path', () => { ... })
test('returns null for unknown path', () => { ... })
```

---

## Phase 16 — Alpha Deployment
**Dependency:** All prior phases stable; Phase 15 complete  
**Files touched:** `backend/app/models.py`, `backend/app/database.py`, `backend/app/routers/auth.py` (new), `backend/app/services/storage_service.py` (new), `backend/app/services/auth_service.py` (new), `backend/app/main.py`, `backend/app/routers/books.py`, `backend/.env.example`, `backend/requirements.txt`, `frontend/src/pages/LoginPage.tsx` (new), `frontend/src/context/AuthContext.tsx` (new), `frontend/src/components/ErrorBoundary.tsx` (new), `frontend/src/services/api.ts`, `railway.toml` (project root)

### 16.1 Database: Alembic + PostgreSQL

Install: `pip install alembic psycopg2-binary`

Initialize: `cd backend && alembic init alembic`

Configure `alembic/env.py` to use `DATABASE_URL` env var and import all models.

Generate initial migration from current model state:
```bash
alembic revision --autogenerate -m "initial_schema"
alembic revision --autogenerate -m "phase7_bug_fixes_and_t2i_fields"
alembic revision --autogenerate -m "add_users_and_book_ownership"
```

Replace `init_db()` in `main.py` with `alembic upgrade head` as a startup step or pre-deploy command.

Local Postgres testing via `docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:16
    environment: { POSTGRES_DB: noctua, POSTGRES_USER: noctua, POSTGRES_PASSWORD: noctua }
    ports: ["5432:5432"]
```

### 16.2 File Storage: storage_service.py

Create `backend/app/services/storage_service.py` — thin abstraction: `local` backend (filesystem) for dev, `s3` backend (boto3, compatible with Cloudflare R2) for production.

```python
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local")  # "local" | "s3"

def upload_file(file_content: bytes, key: str, content_type: str = "application/octet-stream") -> str:
    """Returns public URL of uploaded file. key e.g. 'uploads/book_42/manuscript.pdf'"""

def delete_file(key: str) -> None: ...
```

Update all file-write calls in `upload_service.py`, `visual_bible.py` reference-upload, and `illustrations.py` to use `storage_service.upload_file()`.

### 16.3 Authentication: Magic Link

Install: `pip install fastapi-users[sqlalchemy] fastapi-users-db-sqlalchemy python-jose[cryptography]`

Add `User` model (fastapi-users UUID-based base).  
Add `user_id UUID FK nullable` to `Book` (nullable for backward compat with existing books).  
Create `auth.py` router: `POST /auth/request-login-link`, `GET /auth/verify`, `POST /auth/logout`, `GET /auth/me`.  
Add optional auth dependency to book endpoints — unauthenticated requests see only books with `user_id IS NULL`.

### 16.4 CORS and Environment

Replace dev CORS with `ALLOWED_ORIGINS` env var. Frontend `api.ts`: use `VITE_API_BASE_URL` env var; add `withCredentials: true`.

### 16.5 Startup Recovery

```python
@app.on_event("startup")
async def recover_stuck_analyses():
    stuck = db.query(Book).filter(Book.status == "analyzing").all()
    for book in stuck: book.status = "imported"
    if stuck: db.commit()
```

### 16.6 Frontend Error Boundary

Create `frontend/src/components/ErrorBoundary.tsx` — class component wrapping root app. On error: show Noctua illustration, error ID, "Return to the Study" button. Wrap in `main.tsx`.

### 16.7 Railway Deployment

Create `railway.toml` at project root — two services: `noctua-api` (FastAPI, `alembic upgrade head && uvicorn ...`) and `noctua-frontend` (Vite build + serve).

### 16.8 Updated .env.example

```bash
# Core
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=postgresql://noctua:noctua@localhost:5432/noctua

# T2I Generation
FAL_API_KEY=                    # Primary: FLUX Kontext via fal.ai
COVER_T2I_PROVIDER=flux_kontext # "flux_kontext" | "dalle"

# Auth
SECRET=
EMAIL_FROM=noctua@yourdomain.com
SMTP_HOST=smtp.resend.com
SMTP_PORT=587
SMTP_USER=resend
SMTP_PASSWORD=

# File storage
STORAGE_BACKEND=local
S3_BUCKET=noctua-assets
S3_ENDPOINT_URL=
S3_PUBLIC_BASE_URL=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# CORS
ALLOWED_ORIGINS=http://localhost:5173

# Image search providers
UNSPLASH_ACCESS_KEY=
SERPAPI_KEY=
SEARCH_API_KEY=
PEXELS_API_KEY=
PIXABAY_API_KEY=
OPENVERSE_CLIENT_ID=
OPENVERSE_CLIENT_SECRET=
OPENVERSE_ACCESS_TOKEN=
```

### 16.9 Alpha Readiness Checklist

**Security**
- [ ] `.env` not committed; `SECRET` is randomly generated; `ALLOWED_ORIGINS` is production URL only

**Data**
- [ ] Postgres provisioned; `alembic upgrade head` runs clean on production database
- [ ] `STORAGE_BACKEND=s3` configured with valid credentials

**Functionality**
- [ ] Magic link email delivers correctly
- [ ] Full analysis pipeline completes on test manuscript in production
- [ ] T2I generates an image with `FAL_API_KEY` set in production
- [ ] File upload persists after server restart (confirms cloud storage)
- [ ] Stuck analysis recovery runs on startup

**Resilience**
- [ ] Error boundary renders when API returns 500
- [ ] Frontend shows loading states during analysis and T2I generation

**Cost controls**
- [ ] `MAX_MANUSCRIPT_WORDS` env var set (e.g. 120000)
- [ ] OpenAI spend alert configured
- [ ] fal.ai rate limits understood and billing cap set

---

## Dependency Graph

```
Phase 7  (Bugs + Model + VB API + Cover Studio API)
    │
    ├──► Phase 8  (Frontend Foundation)
    │         │
    │         ├──► Phase 9  (T2I Backend Services) ─────────────────────────────┐
    │         │                                                                   │
    │         └──► Phase 10 (SetupPage + WorkflowNav)                           │
    │                   │                                                         │
    │                   └──► Phase 11 (AnalysisReview + Cover Brief Editor)      │
    │                              │                                              │
    │                              └──► Phase 12 (MoodBoardPage)                 │
    │                                        │                                   │
    │                                        └──► Phase 13 (CoverStudio ◄────────┘
    │                                                  + TextStudio)
    │                                                       │
    │                                                       └──► Phase 14 (E2E)
    │                                                                  │
    └──► Phase 15 (Visual Identity) ◄─── any time after Phase 8       │
                                                                       └──► Phase 16 (Deployment)
```

Phases 9 and 10 can begin in parallel after Phase 8 is complete (they share no files). Phase 13 must wait for both Phase 9 (real T2I) and Phase 12 (moodboard reference completed by user flow).

Phase 15 (Visual Identity) is fully independent of the T2I stack — it can run on a separate branch any time after Phase 8 is stable.

Phase 16 always runs last.
