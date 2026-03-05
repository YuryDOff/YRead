# Noctua — Implementation Plan v3
## I2T Pipeline · Prompt Engineering Service · fal.ai T2I · Serper · TextStudio · Simple/Pro Tiers

**Supersedes:** `Noctua_Implementation_Plan_Merged.md`
**Status of prior phases:** Phases 1–7 complete (see status line per phase below).
**This document:** Phases 8–17, full Cursor Composer format.
**Target runtime:** Cursor Composer (Agent mode) — paste one phase block per session.
**Testing:** pytest (backend); Vitest + Playwright (frontend).

---

## Architecture Context (read before implementing)

The primary generation path is:

```
Reference image → POST /api/books/{id}/analyze-cover-reference
                → GPT-4o Vision (I2T)
                → style_template (CoverAnalysis.reference_style_template)
                        ↓
               PromptEngineeringService
               (style_template + primary entity visual_tokens + user instruction)
                        ↓
               PromptEngineeringResult (final_prompt, negative_prompt)
                        ↓
               FluxKontextProvider → fal.ai → generated image URL
                        ↓
               CoverConcept record → CoverStudioPage
                        ↓
               TextStudio (browser canvas) → KDP PNG export
```

Fallback path (no reference image / Simple tier):
```
genre + mood + character core_tokens → CoverPromptAssembler → final_prompt → FluxProvider
```

Copyright policy: third-party cover references → I2T text path ONLY. Image never passed as fal.ai conditioning input. Visual Bible entity references → direct image conditioning permitted.

---

## Tier Architecture

Both tiers run the **identical backend pipeline**. The split is frontend-only:

| | Simple | Pro |
|---|---|---|
| Workflow | Book Cover only | Full Book + Book Cover |
| Analysis | Single-pass (characters only) | Multi-pass (all 4 entity types) |
| Cover Brief Editor | Cover type + element selector only | Full two-panel prompt editor |
| Concepts per run | 3 | 6 |
| Moodboard | Cover tab only | All 4 tabs |
| Feature gate | `user.plan === 'simple'` | `user.plan === 'pro'` |

---

## Completed Phases Summary

- **Phase 1** ✅ Four-entity data model (Character, Location, Artefact, Scene).
- **Phase 2** ✅ Full CRUD layer for all entities.
- **Phase 3** ✅ Artefact analysis service + entity ontology classification.
- **Phase 4** ✅ Cover analysis service + genre defaults + thematic material extraction.
- **Phase 5** ✅ Analysis pipeline integration (background tasks, progress tracking).
- **Phase 6** ✅ Search extensions (Behance, Dribbble providers, entity search routing).
- **Phase 7** ✅ Bug fixes (BUG-1 is_main collision, BUG-2 scene display count), data model extensions (cover_type, color_palette_structured, primary_cover_*_id, is_selected_for_reference), VB entry endpoints, Cover Studio API, prompt registry + SettingsPage.
- **Phase 8a** ✅ Analysis engine branch (Simple vs Pro): Book.analysis_mode, BookCreate/BookResponse, POST /api/books, get_entity_types_for_mode in ai_service; _run_analysis_background filters entity_types by book.analysis_mode; 5 unit tests.
- **Phase 8b** ✅ I2T Analysis Service: I2TAnalysisResult and AnalyzeCoverReferenceRequest schemas; three columns on CoverAnalysis (reference_style_template, reference_style_notes, reference_image_url); i2t_analysis_service.run_i2t_analysis (GPT-4o Vision, cover/illustration); POST /api/books/{id}/analyze-cover-reference; unit tests (mock, empty on failure, mode routing, endpoint stores to DB).
- **Phase 9** ✅ Prompt Engineering Service + fal.ai FLUX + DALL-E: PromptEngineeringResult schema; prompt_engineering_service.run_prompt_merge (GPT-4o merge, heuristic compatibility, fallback); BaseCoverT2IProvider, T2IGenerationResult in base; FluxKontextProvider (fal-client), DalleProvider; get_cover_t2i_provider() in engine_selector; fal-client in requirements; FAL_API_KEY, COVER_T2I_PROVIDER in .env.example; 9 unit tests.
- **Phase 9b** ✅ Serper Search Provider: BaseSearchProvider and SearchResult in providers/base; serper_provider (blacklist, watermarked); get_supplementary_search_providers(entity_type) in engine_selector; SERPER_API_KEY in .env.example; 10 unit tests.
- **Phase 10** ✅ SetupPage + WorkflowNav + FeatureGate: AuthContext (user.plan), FeatureGate + UpgradeBanner, WorkflowNav dual-path (COVER_ONLY_STEPS / FULL_BOOK_STEPS), workflow selector in BookUpload, analysis_mode in manuscripts/upload, new routes (mood-board, cover-brief, studio/cover, studio/text, preview), stub pages MoodBoardPage/CoverStudioPage/TextStudioPage; Vitest + testing-library; 5 unit tests.
- **Phase 11** ✅ AnalysisReviewPage + CoverBriefEditor: tabs by book.analysis_mode (simple: Characters only; pro: Characters, Locations, Artefacts, Cover), is_main as read-only badge, is_selected_for_reference toggle and updateEntitySelections; CoverBriefEditor (Simple vs Pro layout, Panel A/B, localStorage noctua_panel_a_expanded, FeatureGate for negative prompt); 9 unit tests.
- **Phase 12** ✅ MoodBoardPage: tabs (Style Reference only for simple; Style Reference | Characters | Locations | Artefacts for pro), cover reference grid, upload, "Search for similar covers", "Analyse style" (explicit, not auto), StyleTemplateSummaryCard, error toast, Continue to Cover Brief; test-wrappers (analysisMode, defaultWrapper, wrapperWithSelectedImage); PATCH cover-analysis creates row if missing; 8 unit tests.
- **Phase 13** ✅ Cover generation wire-up: cover_prompt_assembler.py (CoverPromptAssembler.assemble fallback); illustrations generate uses _generate_concept_background (run_prompt_merge / CoverPromptAssembler, get_cover_t2i_provider, status generating→complete|failed); CoverStudioPage (poll cover-concepts, concept grid, Select, Regenerate, KDP note, Continue to Typography); TextStudioPage (canvas, title/author/font/color/size, export PNG 2560×1600, FeatureGate custom font); api getCoverConcepts, generateCoverConcepts, selectCoverConcept; 4 CoverStudio + 3 TextStudio unit tests.

---

## Session Grouping (new plan)

| Cursor Session | Phase | Rationale |
|---|---|---|
| 1 | 8a | Analysis engine branch (Simple vs Pro modes). Backend only. |
| 2 | 8b | I2T Analysis Service. Backend only. |
| 3 | 9 | Prompt Engineering Service + fal.ai FLUX provider + DALL-E provider. Backend only. |
| 4 | 9b | Serper provider. Backend only. Can run in parallel to sessions 1–3. |
| 5 | 10 | SetupPage refactor + WorkflowNav dual-path + FeatureGate. Frontend. |
| 6 | 11 | AnalysisReviewPage + CoverBriefEditor. Frontend. |
| 7 | 12 | MoodBoardPage. Frontend. |
| 8 | 13 | CoverStudioPage + TextStudioPage + wire generate endpoint. Frontend + backend wire-up. |
| 9 | 14 | E2E tests. Full attention on user-flow logic. |
| 10 | 15 | Visual identity + enhancement backlog doc. Independent branch. |
| 11 | 16 | Alpha deployment (Auth + PostgreSQL + Railway + user.plan field). Always last. |
| — | 17 | Illustration pipeline (FUTURE placeholder — no implementation scope). |

---

## Cursor Composer Session Prompt

Copy this prompt block in full at the start of every Cursor Composer session. Replace `[PASTE PHASE CONTENT HERE]` with the phase(s) for that session.

```
You are implementing a software project called Noctua by following a phased
<<<<<<< HEAD
implementation plan. The full plan is in `docs/implementation_plan.md`.
=======
implementation plan. The full plan is in `Project Planning/Noctua_implementation_plan_v3.md`.
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
The complete codebase documentation is in `docs/codebase_snapshot.md`.

════════════════════════════════════════
PROCESS — follow these steps in order. Do not skip any step.
════════════════════════════════════════

STEP 1 — READ BEFORE YOU WRITE
Before touching any file:
- Read the full phase content pasted below
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
c) If any test fails, fix the implementation (or the test if it is wrong)
   before moving to the next section
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

<<<<<<< HEAD
=======
STEP 8 - Mark the relevant section of Project Planning/Noctua_implementation_plan_v3.md as complete and include a short summary.  

>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
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

<<<<<<< HEAD
## Phase 8a — Analysis Engine Branch (Simple vs. Pro Modes)

**Dependency:** Phase 7 complete
=======
## Phase 8a — Analysis Engine Branch (Simple vs. Pro Modes) ✅ Complete

**Dependency:** Phase 7 complete  
**Status:** ✅ Complete

**Realization summary:** Added `analysis_mode` to Book model (Column, default "pro") and DB migration via `database._run_migrations()`. Introduced `BookCreate` schema and `analysis_mode` on `BookResponse`. New endpoint `POST /api/books` creates a book with optional `analysis_mode`; `crud.create_book` accepts `analysis_mode`. In `ai_service`: `get_entity_types_for_mode(analysis_mode, requested_types)` — simple → `["character"]`, pro → requested_types. In `_run_analysis_background`, entity_types are resolved via this function from `book.analysis_mode`, with "character" mapped to "characters" for the pipeline. Unit tests in `test_analysis_branch.py` (5 tests, all passing). No Alembic; used existing migration pattern.

>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `backend/app/models.py` — add `analysis_mode` field to Book
- `backend/app/schemas.py` — add `analysis_mode` to BookCreate, BookRead
- `backend/app/crud.py` — update create_book to accept analysis_mode
- `backend/app/routers/books.py` — accept analysis_mode in POST /api/books
- `backend/app/services/ai_service.py` — branch analysis based on analysis_mode
- `backend/tests/unit/test_analysis_branch.py` (new)

### 8a.1 Data Model

Add to `Book` model in `backend/app/models.py`:

```python
analysis_mode: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    default="pro",
    server_default="pro",
    comment="'simple' = Book Cover mode (characters only). 'pro' = Full Book (all entities)."
)
```

Add Alembic migration: `alembic revision --autogenerate -m "add_book_analysis_mode"`. Run `alembic upgrade head`.

### 8a.2 Schemas

Add to `BookCreate` and `BookRead` in `backend/app/schemas.py`:

```python
analysis_mode: Literal["simple", "pro"] = "pro"
```

### 8a.3 Router

In `backend/app/routers/books.py`, update `POST /api/books` to accept and persist `analysis_mode` from the request body. No other changes to existing endpoint logic.

### 8a.4 Analysis Service Branch

In `backend/app/services/ai_service.py`, wrap the entity extraction dispatch logic:

```python
def get_entity_types_for_mode(analysis_mode: str, requested_types: list[str]) -> list[str]:
    """
    Simple mode: extracts characters only, regardless of requested_types.
    Pro mode: extracts all requested_types (existing behaviour).
    """
    if analysis_mode == "simple":
        return ["character"]
    return requested_types
```

Call this function at the top of `run_analysis()` (or equivalent orchestration function) before dispatching to per-entity extractors. The rest of the pipeline is unchanged.

### 8a.5 Unit Tests

File: `backend/tests/unit/test_analysis_branch.py`

```python
import pytest
from app.services.ai_service import get_entity_types_for_mode

def test_simple_mode_returns_only_characters():
    result = get_entity_types_for_mode("simple", ["character", "location", "artefact"])
    assert result == ["character"]

def test_pro_mode_returns_all_requested():
    types = ["character", "location", "artefact", "scene"]
    result = get_entity_types_for_mode("pro", types)
    assert result == types

def test_simple_mode_ignores_requested_types():
    result = get_entity_types_for_mode("simple", ["artefact"])
    assert result == ["character"]

def test_default_mode_is_pro(client):
    r = client.post("/api/books", json={"title": "Test", "author": "Author"})
    assert r.status_code == 201
    assert r.json()["analysis_mode"] == "pro"

def test_simple_mode_persists(client):
    r = client.post("/api/books", json={
        "title": "Test", "author": "Author", "analysis_mode": "simple"
    })
    assert r.status_code == 201
    assert r.json()["analysis_mode"] == "simple"
```

**Success checklist:**
<<<<<<< HEAD
- [ ] `analysis_mode` field present on Book model and schema
- [ ] POST /api/books accepts `analysis_mode` without breaking existing callers (field is optional, defaults to 'pro')
- [ ] Simple mode restricts extraction to characters only
- [ ] All 5 unit tests passing

---

## Phase 8b — I2T Analysis Service (Image-to-Text Cover Style Extraction)

**Dependency:** Phase 8a complete
=======
- [x] `analysis_mode` field present on Book model and schema
- [x] POST /api/books accepts `analysis_mode` without breaking existing callers (field is optional, defaults to 'pro')
- [x] Simple mode restricts extraction to characters only
- [x] All 5 unit tests passing

---

## Phase 8b — I2T Analysis Service (Image-to-Text Cover Style Extraction) ✅ Complete

**Dependency:** Phase 8a complete
**Status:** ✅ Complete

**Realization summary:** I2TAnalysisResult and AnalyzeCoverReferenceRequest schemas; three columns on CoverAnalysis (reference_style_template, reference_style_notes, reference_image_url) with migrations; get_or_create_cover_analysis and update_cover_analysis in crud; i2t_analysis_service.run_i2t_analysis (GPT-4o Vision, cover/illustration modes); covers router POST analyze-cover-reference; unit tests (mock response, empty on failure, mode routing, endpoint stores to DB).

>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `backend/app/services/i2t_analysis_service.py` (new)
- `backend/app/schemas.py` — add `I2TAnalysisResult`
- `backend/app/models.py` — add 3 new fields to `CoverAnalysis`
- `backend/app/routers/covers.py` — add `POST /api/books/{book_id}/analyze-cover-reference`
- `backend/tests/unit/test_i2t_service.py` (new)

### 8b.1 Schema

Add to `backend/app/schemas.py`:

```python
class I2TAnalysisResult(BaseModel):
    style_template: str
    composition_notes: str
    color_palette_extracted: dict  # keys: dominant, accent, temperature, contrast
    style_tags: list[str]
    mood_keywords: list[str]
    lighting_description: str
```

### 8b.2 Data Model

Add three columns to `CoverAnalysis` in `backend/app/models.py`:

```python
reference_style_template: Mapped[str | None] = mapped_column(
    Text, nullable=True,
    comment="Full T2I prompt string extracted by GPT-4o Vision from reference cover"
)
reference_style_notes: Mapped[dict | None] = mapped_column(
    JSON, nullable=True,
    comment="Structured I2T result: color_palette, style_tags, mood_keywords, etc."
)
reference_image_url: Mapped[str | None] = mapped_column(
    String(2048), nullable=True,
    comment="URL of the reference cover image that was analysed"
)
```

Run Alembic migration after adding fields.

### 8b.3 I2T Service

Create `backend/app/services/i2t_analysis_service.py`:

```python
"""
i2t_analysis_service.py
------------------------
Reverse-engineers the visual style of a reference book cover image using
GPT-4o Vision. Produces a style_template string suitable for direct use
as a T2I prompt by the PromptEngineeringService.

Extraction modes:
  cover       — optimised for book cover composition vocabulary
  illustration — scene composition vocabulary (Phase 17, future)
"""
from __future__ import annotations

import logging
import os
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import I2TAnalysisResult

logger = logging.getLogger(__name__)

COVER_EXTRACTION_SYSTEM_PROMPT = """You are an expert at reverse-engineering the visual style
of book cover images for use in AI image generation. Analyse the provided cover image and
extract its style as a structured JSON object.

Focus ONLY on:
- Artistic style (illustration style, art movement, rendering technique)
- Composition (subject placement, foreground/midground/background layers, camera angle)
- Color palette (dominant colors, accent colors, temperature, contrast level)
- Lighting (type, direction, mood contribution)
- Atmosphere and mood keywords
- Decorative elements (borders, textures, overlays)
- Technical generation tags (8k, bokeh, etc.)

Do NOT extract:
- Specific character identities or names
- Trademarked elements
- Text content (title, author name)

Output ONLY valid JSON matching this schema:
{
  "style_template": "<single T2I prompt string, comma-separated descriptors>",
  "composition_notes": "<one sentence describing compositional structure>",
  "color_palette_extracted": {
    "dominant": "<primary color name>",
    "accent": "<accent color name>",
    "temperature": "warm | cool | neutral",
    "contrast": "high | medium | low"
  },
  "style_tags": ["<tag1>", "<tag2>"],
  "mood_keywords": ["<keyword1>", "<keyword2>"],
  "lighting_description": "<description of lighting>"
}"""

ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT = """You are an expert at analysing scene composition
in illustrated books. Analyse the provided image and extract its compositional style as JSON.
Focus on: scene depth, character-environment relationship, action staging, lighting mood,
color narrative role. Same JSON schema as cover extraction."""


async def run_i2t_analysis(
    image_url: str,
    mode: Literal["cover", "illustration"] = "cover",
) -> I2TAnalysisResult:
    """
    Calls GPT-4o Vision to extract style information from a reference image.

    Args:
        image_url: Publicly accessible URL of the reference image.
        mode: 'cover' uses cover composition vocabulary; 'illustration' uses scene vocabulary.

    Returns:
        I2TAnalysisResult with all fields populated.
        Returns an empty/default result if the Vision call fails — does NOT raise.
        Caller must handle the empty result gracefully (log, continue moodboard flow).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set — returning empty I2TAnalysisResult")
        return _empty_result()

    system_prompt = (
        COVER_EXTRACTION_SYSTEM_PROMPT
        if mode == "cover"
        else ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT
    )

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",   # Cost-efficient; use gpt-4o for highest accuracy
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": "high"},
                        },
                        {
                            "type": "text",
                            "text": "Analyse this book cover and extract its visual style as JSON.",
                        },
                    ],
                },
            ],
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        import json
        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)

        return I2TAnalysisResult(
            style_template=parsed.get("style_template", ""),
            composition_notes=parsed.get("composition_notes", ""),
            color_palette_extracted=parsed.get("color_palette_extracted", {}),
            style_tags=parsed.get("style_tags", []),
            mood_keywords=parsed.get("mood_keywords", []),
            lighting_description=parsed.get("lighting_description", ""),
        )

    except Exception as exc:
        logger.warning(f"I2T analysis failed for {image_url}: {exc}. Returning empty result.")
        return _empty_result()


def _empty_result() -> I2TAnalysisResult:
    return I2TAnalysisResult(
        style_template="",
        composition_notes="",
        color_palette_extracted={},
        style_tags=[],
        mood_keywords=[],
        lighting_description="",
    )
```

### 8b.4 Router Endpoint

Add to `backend/app/routers/covers.py`:

```python
@router.post("/{book_id}/analyze-cover-reference", response_model=I2TAnalysisResult)
async def analyze_cover_reference(
    book_id: int,
    body: AnalyzeCoverReferenceRequest,
    db: Session = Depends(get_db),
):
    """
    Runs GPT-4o Vision I2T analysis on a reference cover image.
    Stores result to CoverAnalysis DB record.
    Returns I2TAnalysisResult (all fields populated, or empty on Vision failure).
    """
    result = await run_i2t_analysis(image_url=body.image_url, mode=body.mode)

    cover_analysis = crud.get_or_create_cover_analysis(db, book_id)
    crud.update_cover_analysis(db, cover_analysis.id, {
        "reference_style_template": result.style_template,
        "reference_style_notes": {
            "composition_notes": result.composition_notes,
            "color_palette_extracted": result.color_palette_extracted,
            "style_tags": result.style_tags,
            "mood_keywords": result.mood_keywords,
            "lighting_description": result.lighting_description,
        },
        "reference_image_url": body.image_url,
    })
    return result
```

Add request schema to `schemas.py`:

```python
class AnalyzeCoverReferenceRequest(BaseModel):
    image_url: str
    mode: Literal["cover", "illustration"] = "cover"
```

### 8b.5 Unit Tests

File: `backend/tests/unit/test_i2t_service.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.services.i2t_analysis_service import run_i2t_analysis, _empty_result
from app.schemas import I2TAnalysisResult

MOCK_GPT_RESPONSE = {
    "style_template": "dark fantasy illustration, hooded figure, forest, art nouveau border, teal gold palette",
    "composition_notes": "Single foreground figure, centred, misty background",
    "color_palette_extracted": {"dominant": "teal", "accent": "gold", "temperature": "cool", "contrast": "high"},
    "style_tags": ["dark fantasy", "art nouveau", "cinematic"],
    "mood_keywords": ["mysterious", "atmospheric"],
    "lighting_description": "Moonlit from above, rim lighting on figure",
}

@pytest.mark.asyncio
@pytest.mark.skipif(not __import__("os").getenv("OPENAI_API_KEY"), reason="No API key")
async def test_run_i2t_analysis_returns_all_fields():
    result = await run_i2t_analysis("https://example.com/cover.jpg", mode="cover")
    assert isinstance(result, I2TAnalysisResult)
    assert result.style_template != ""
    assert isinstance(result.color_palette_extracted, dict)
    assert isinstance(result.style_tags, list)

@pytest.mark.asyncio
async def test_run_i2t_analysis_mock_response():
    import json
    mock_message = AsyncMock()
    mock_message.content = json.dumps(MOCK_GPT_RESPONSE)
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

        result = await run_i2t_analysis("https://example.com/cover.jpg")

    assert result.style_template == MOCK_GPT_RESPONSE["style_template"]
    assert result.color_palette_extracted["dominant"] == "teal"
    assert "dark fantasy" in result.style_tags

@pytest.mark.asyncio
async def test_run_i2t_analysis_returns_empty_on_vision_failure():
    with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Network error"))

        result = await run_i2t_analysis("https://example.com/cover.jpg")

    assert result.style_template == ""
    assert result.color_palette_extracted == {}
    assert result.style_tags == []

@pytest.mark.asyncio
async def test_mode_param_routes_to_correct_system_prompt():
    from app.services import i2t_analysis_service as svc
    with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        captured_messages = []

        async def capture_call(**kwargs):
            captured_messages.extend(kwargs.get("messages", []))
            raise Exception("stop early")

        mock_client.chat.completions.create = capture_call

        await run_i2t_analysis("https://example.com/img.jpg", mode="illustration")

    system_content = captured_messages[0]["content"]
    assert "scene composition" in system_content.lower()

def test_endpoint_stores_result_to_db(client, book_id):
    import json
    with patch("app.routers.covers.run_i2t_analysis") as mock_i2t:
        mock_i2t.return_value = I2TAnalysisResult(
            style_template="dark fantasy, teal gold",
            composition_notes="Single figure",
            color_palette_extracted={"dominant": "teal"},
            style_tags=["dark"],
            mood_keywords=["moody"],
            lighting_description="Rim light",
        )
        r = client.post(
            f"/api/books/{book_id}/analyze-cover-reference",
            json={"image_url": "https://example.com/cover.jpg", "mode": "cover"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["style_template"] == "dark fantasy, teal gold"
```

**Success checklist:**
<<<<<<< HEAD
- [ ] `I2TAnalysisResult` schema defined and importable
- [ ] 3 new columns on CoverAnalysis model + migration run
- [ ] `POST /api/books/{id}/analyze-cover-reference` endpoint live
- [ ] Empty result returned on Vision failure — no exception propagated
- [ ] Mode param selects correct extraction vocabulary
- [ ] All unit tests passing (mocked API calls)

---

## Phase 9 — Prompt Engineering Service + fal.ai FLUX Provider + DALL-E Provider

**Dependency:** Phase 8b complete
=======
- [x] `I2TAnalysisResult` schema defined and importable
- [x] 3 new columns on CoverAnalysis model + migration run
- [x] `POST /api/books/{id}/analyze-cover-reference` endpoint live
- [x] Empty result returned on Vision failure — no exception propagated
- [x] Mode param selects correct extraction vocabulary
- [x] All unit tests passing (mocked API calls)

**Phase 8b complete.** Implemented: I2TAnalysisResult and AnalyzeCoverReferenceRequest schemas; three new columns on CoverAnalysis (reference_style_template, reference_style_notes, reference_image_url) with migrations in database.py; get_or_create_cover_analysis and update_cover_analysis in crud; i2t_analysis_service.run_i2t_analysis (GPT-4o Vision, cover/illustration modes); covers router with POST analyze-cover-reference; unit tests (mock response, empty on failure, mode routing, endpoint stores to DB). Async tests run via asyncio.run (no pytest-asyncio).

---

## Phase 9 — Prompt Engineering Service + fal.ai FLUX Provider + DALL-E Provider ✅ Complete

**Dependency:** Phase 8b complete
**Status:** ✅ Complete

**Realization summary:** PromptEngineeringResult schema; prompt_engineering_service.run_prompt_merge (style_template + entity + user_instruction → GPT-4o merge, heuristic compatibility, fallback on failure); BaseCoverT2IProvider and T2IGenerationResult in t2i_providers/base; FluxKontextProvider (fal-client, TEXT/KONTEXT endpoints); DalleProvider (DALL-E 3 HD fallback); get_cover_t2i_provider() in engine_selector; fal-client>=0.10.0 in requirements; FAL_API_KEY, COVER_T2I_PROVIDER in .env.example; t2i_providers/__init__.py updated (no FluxProvider in ALL_T2I_PROVIDERS); 9 unit tests in test_prompt_engineering_service.py.

>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `backend/app/services/prompt_engineering_service.py` (new)
- `backend/app/services/t2i_providers/flux_provider.py` (replace stub)
- `backend/app/services/t2i_providers/dalle_provider.py` (replace stub)
- `backend/app/services/engine_selector.py` (add `get_cover_t2i_provider()`)
- `backend/app/schemas.py` (add `PromptEngineeringResult`)
- `backend/requirements.txt` (add `fal-client>=0.10.0`)
- `backend/.env.example` (add FAL_API_KEY, COVER_T2I_PROVIDER)
- `backend/tests/unit/test_prompt_engineering_service.py` (new)

### 9.1 PromptEngineeringResult Schema

Add to `backend/app/schemas.py`:

```python
from typing import Literal

class PromptEngineeringResult(BaseModel):
    final_prompt: str
    negative_prompt: str
    compatibility_status: Literal["COMPATIBLE", "WARNING", "INCOMPATIBLE"]
    compatibility_note: str
```

### 9.2 Prompt Engineering Service

Create `backend/app/services/prompt_engineering_service.py`:

```python
"""
prompt_engineering_service.py
------------------------------
Merges an I2T-extracted style_template with a book entity's visual tokens
to produce a final T2I prompt ready for fal.ai FLUX Kontext.

Primary mode (I2T path):
  Inputs:  style_template + primary_entity + user_instruction
  Process: Compatibility check → GPT-4o merge call → PromptEngineeringResult

Fallback mode (Simple tier / no reference image):
  Routes to CoverPromptAssembler using genre + mood + character core_tokens.
"""
from __future__ import annotations

import logging
import os
import json
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import PromptEngineeringResult

logger = logging.getLogger(__name__)

MERGE_SYSTEM_PROMPT = """You are the Noctua Prompt Engineering Service. Merge the provided
I2T style template with the replacement entity to produce a final T2I generation prompt.

RULES:
1. Preserve ALL atmospheric, color, lighting, and stylistic elements from the STYLE TEMPLATE.
2. Replace ONLY the primary subject with the REPLACEMENT ENTITY using its visual tokens.
3. Anti-tokens MUST appear in negative_prompt ONLY — never in the main prompt.
4. Compatibility check:
   COMPATIBLE: entity fits same compositional role (humanoid replacing humanoid).
   WARNING: entity type mismatch may cause awkward composition — explain the risk.
   INCOMPATIBLE: entity is irreconcilable with the composition.
5. Output ONLY valid JSON — no markdown.

OUTPUT SCHEMA:
{
  "final_prompt": "<merged T2I prompt>",
  "negative_prompt": "<comma-separated negative tokens>",
  "compatibility_status": "COMPATIBLE" | "WARNING" | "INCOMPATIBLE",
  "compatibility_note": "<1-2 sentences>"
}"""

# Fast heuristic compatibility check before making the LLM call.
# Saves a GPT call for obviously compatible or obviously incompatible pairings.
_HUMANOID_VISUAL_TYPES = {"humanoid", "anthropomorphic", "creature"}
_SPATIAL_VISUAL_TYPES = {"landscape", "cityscape", "interior", "architectural_ruin", "seascape"}

def _heuristic_compatibility(
    template_subject_class: str,
    entity_visual_type: str,
    entity_class: str,
) -> Literal["COMPATIBLE", "WARNING", "INCOMPATIBLE"] | None:
    """
    Returns a fast compatibility verdict if deterministic, else None (route to LLM).
    template_subject_class: 'humanoid' | 'object' | 'location' | 'abstract'
    """
    if template_subject_class == "humanoid":
        if entity_visual_type in _HUMANOID_VISUAL_TYPES:
            return "COMPATIBLE"
        if entity_visual_type in _SPATIAL_VISUAL_TYPES:
            return "WARNING"
    return None  # LLM decides


async def run_prompt_merge(
    style_template: str,
    entity: dict,
    user_instruction: str,
    template_subject_class: str = "humanoid",
) -> PromptEngineeringResult:
    """
    Merges style_template with the replacement entity.

    Args:
        style_template: Full T2I string from I2T analysis (CoverAnalysis.reference_style_template).
        entity: Dict with keys: name, entity_class, visual_type, core_tokens, style_tokens,
                archetype_tokens, anti_tokens. Matches entity visual_tokens_json structure.
        user_instruction: Author's natural-language instruction.
        template_subject_class: The compositional role of the original subject in the template.

    Returns:
        PromptEngineeringResult with all fields populated.
        On API failure: returns a safe fallback result (WARNING status, original template as prompt).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set — returning fallback PromptEngineeringResult")
        return _fallback_result(style_template)

    # Fast heuristic check first
    fast_status = _heuristic_compatibility(
        template_subject_class,
        entity.get("visual_type", ""),
        entity.get("entity_class", ""),
    )

    core_tokens = ", ".join(entity.get("core_tokens", []))
    style_tokens = ", ".join(entity.get("style_tokens", []))
    archetype_tokens = ", ".join(entity.get("archetype_tokens", []))
    anti_tokens = ", ".join(entity.get("anti_tokens", []))

    user_message = f"""=== STYLE TEMPLATE (from I2T analysis) ===
{style_template}

=== ENTITY TO REPLACE (existing primary subject) ===
Description: {template_subject_class} (primary foreground subject)

=== REPLACEMENT ENTITY ===
Name: {entity.get("name", "unnamed")}
Class: {entity.get("entity_class", "")}
Visual type: {entity.get("visual_type", "")}
Core tokens: {core_tokens}
Style tokens: {style_tokens}
Archetype tokens: {archetype_tokens}
Anti-tokens (negative prompt only): {anti_tokens}

=== USER INSTRUCTION ===
{user_instruction}

Produce the merged prompt. Return ONLY the JSON object."""

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": MERGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)

        result = PromptEngineeringResult(
            final_prompt=parsed["final_prompt"],
            negative_prompt=parsed["negative_prompt"],
            compatibility_status=parsed["compatibility_status"],
            compatibility_note=parsed["compatibility_note"],
        )

        # Override LLM status with heuristic if available (heuristic is more reliable)
        if fast_status is not None and fast_status != result.compatibility_status:
            logger.info(
                f"Heuristic overrides LLM compatibility: {result.compatibility_status} → {fast_status}"
            )
            result = result.model_copy(update={"compatibility_status": fast_status})

        return result

    except Exception as exc:
        logger.warning(f"Prompt merge LLM call failed: {exc}. Returning fallback.")
        return _fallback_result(style_template)


def _fallback_result(style_template: str) -> PromptEngineeringResult:
    return PromptEngineeringResult(
        final_prompt=style_template,
        negative_prompt="",
        compatibility_status="WARNING",
        compatibility_note="Prompt merge service unavailable. Using raw style template.",
    )
```

### 9.3 FLUX Kontext Provider (replace stub)

Replace `backend/app/services/t2i_providers/flux_provider.py` entirely:

```python
"""
flux_provider.py
-----------------
FLUX.1 Pro (text-only) and FLUX.1 Kontext Pro (image+text) via fal.ai.

FLUX Kontext is used when a moodboard reference URL is supplied — enabling
style transfer from Visual Bible entity reference images.

Install: pip install fal-client>=0.10.0
Requires: FAL_API_KEY environment variable.
"""
from __future__ import annotations

import logging
import os
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
    TEXT_ENDPOINT = "fal-ai/flux-pro/v1.1"
    KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"

    def __init__(self) -> None:
        api_key = os.getenv("FAL_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "FAL_API_KEY not set. Set it in .env before using FluxKontextProvider."
            )
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
        except ImportError as exc:
            raise RuntimeError("fal-client not installed. Run: pip install fal-client") from exc

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

        logger.info(
            f"FLUX generate — endpoint={endpoint}, "
            f"prompt_tokens={len(prompt.split())}, image_url={'yes' if image_url else 'no'}"
        )

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

### 9.4 DALL-E Provider (replace stub)

Replace `backend/app/services/t2i_providers/dalle_provider.py` entirely:

```python
"""
dalle_provider.py
------------------
DALL-E 3 HD via OpenAI API. Fallback when FAL_API_KEY is not set.
No image conditioning — image_url param is ignored with a warning.
"""
from __future__ import annotations

import logging
import os

from .base import BaseT2IProvider
from .flux_provider import T2IGenerationResult

logger = logging.getLogger(__name__)


class DalleProvider(BaseT2IProvider):
    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        negative_prompt: str | None = None,
        aspect_ratio: str = "2:3",
        **kwargs,
    ) -> T2IGenerationResult:
        from openai import AsyncOpenAI

        if image_url:
            logger.warning(
                "DalleProvider: image_url ignored — DALL-E 3 has no img2img. "
                "Use FluxKontextProvider for moodboard-conditioned generation."
            )

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="hd",
            n=1,
        )
        img = response.data[0]
        return T2IGenerationResult(
            url=img.url or "",
            model="dall-e-3-hd",
            prompt_used=img.revised_prompt or prompt,
            provider="dalle",
        )
```

### 9.5 Engine Selector Extension

Add to `backend/app/services/engine_selector.py`:

```python
def get_cover_t2i_provider() -> "BaseT2IProvider":
    """
    Returns the best available T2I provider for cover generation.
    Preference: FluxKontextProvider (fal.ai) → DalleProvider (OpenAI fallback).
    """
    from app.services.t2i_providers.flux_provider import FluxKontextProvider
    from app.services.t2i_providers.dalle_provider import DalleProvider

    if os.getenv("FAL_API_KEY"):
        try:
            provider = FluxKontextProvider()
            logger.info("T2I provider: FluxKontextProvider (fal.ai)")
            return provider
        except EnvironmentError:
            pass

    logger.info("T2I provider: DalleProvider (OpenAI fallback)")
    return DalleProvider()
```

### 9.6 Environment Config

Add to `backend/.env.example`:
```bash
# T2I Generation
FAL_API_KEY=                      # Primary: FLUX Kontext via fal.ai
COVER_T2I_PROVIDER=flux_kontext   # "flux_kontext" | "dalle" (informational, auto-detected)
```

Add to `backend/requirements.txt`:
```
fal-client>=0.10.0
```

### 9.7 Unit Tests

File: `backend/tests/unit/test_prompt_engineering_service.py`

```python
import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.prompt_engineering_service import (
    run_prompt_merge, _heuristic_compatibility, _fallback_result
)
from app.schemas import PromptEngineeringResult

COMPATIBLE_ENTITY = {
    "name": "Seraphina Vale",
    "entity_class": "character",
    "visual_type": "humanoid",
    "core_tokens": ["red-haired woman", "emerald eyes", "scholar's robes"],
    "style_tokens": ["pre-Raphaelite", "ethereal"],
    "archetype_tokens": ["the seeker"],
    "anti_tokens": ["cartoonish", "modern clothing", "blonde"],
}

INCOMPATIBLE_ENTITY = {
    "name": "The Shattered Citadel",
    "entity_class": "location",
    "visual_type": "architectural_ruin",
    "core_tokens": ["crumbling towers", "gothic arches"],
    "style_tokens": ["brutalist"],
    "archetype_tokens": [],
    "anti_tokens": ["pristine"],
}

MOCK_COMPATIBLE_RESPONSE = json.dumps({
    "final_prompt": "dark fantasy, red-haired woman emerald eyes, misty forest, art nouveau border, teal gold palette",
    "negative_prompt": "cartoonish, modern clothing, blonde",
    "compatibility_status": "COMPATIBLE",
    "compatibility_note": "Humanoid entity fits the single foreground figure compositional role.",
})

MOCK_WARNING_RESPONSE = json.dumps({
    "final_prompt": "dark fantasy, crumbling towers gothic arches, misty forest, art nouveau border",
    "negative_prompt": "pristine",
    "compatibility_status": "WARNING",
    "compatibility_note": "A location entity replacing a humanoid figure may create an awkward composition.",
})

def _mock_gpt_response(content: str):
    mock_message = AsyncMock()
    mock_message.content = content
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    return mock_response


@pytest.mark.asyncio
async def test_compatible_merge_returns_correct_fields():
    with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_gpt_response(MOCK_COMPATIBLE_RESPONSE)
        )
        result = await run_prompt_merge(
            "dark fantasy, hooded figure, misty forest, art nouveau border, teal gold palette",
            COMPATIBLE_ENTITY,
            "Replace the hooded figure with my protagonist",
        )

    assert result.compatibility_status == "COMPATIBLE"
    assert "red-haired" in result.final_prompt.lower() or "seraphina" in result.final_prompt.lower()
    assert "cartoonish" in result.negative_prompt
    assert "modern clothing" in result.negative_prompt


@pytest.mark.asyncio
async def test_incompatible_entity_returns_warning():
    with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(
            return_value=_mock_gpt_response(MOCK_WARNING_RESPONSE)
        )
        result = await run_prompt_merge(
            "dark fantasy, hooded figure, misty forest",
            INCOMPATIBLE_ENTITY,
            "Replace figure with this citadel",
        )

    assert result.compatibility_status in ("WARNING", "INCOMPATIBLE")
    assert len(result.compatibility_note) > 20


def test_heuristic_compatible_humanoid_to_humanoid():
    assert _heuristic_compatibility("humanoid", "humanoid", "character") == "COMPATIBLE"


def test_heuristic_warning_humanoid_to_location():
    assert _heuristic_compatibility("humanoid", "landscape", "location") == "WARNING"


def test_heuristic_none_for_unknown():
    assert _heuristic_compatibility("humanoid", "mythical_beast", "creature") is None


@pytest.mark.asyncio
async def test_fallback_on_api_failure():
    with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
        mock_client = AsyncMock()
        mock_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))

        result = await run_prompt_merge(
            "dark fantasy, hooded figure, teal gold",
            COMPATIBLE_ENTITY,
            "Replace figure",
        )

    assert result.compatibility_status == "WARNING"
    assert "dark fantasy" in result.final_prompt  # raw template returned as fallback


def test_flux_provider_uses_kontext_endpoint_when_image_url_provided():
    # Test endpoint selection logic without real fal.ai call
    import os
    os.environ["FAL_API_KEY"] = "test_key"
    from app.services.t2i_providers.flux_provider import FluxKontextProvider
    provider = FluxKontextProvider()
    # TEXT_ENDPOINT used when no image_url, KONTEXT_ENDPOINT when image_url supplied
    assert provider.TEXT_ENDPOINT != provider.KONTEXT_ENDPOINT
    assert "kontext" in provider.KONTEXT_ENDPOINT


def test_engine_selector_returns_flux_when_fal_key_set(monkeypatch):
    monkeypatch.setenv("FAL_API_KEY", "test_key")
    from app.services.engine_selector import get_cover_t2i_provider
    from app.services.t2i_providers.flux_provider import FluxKontextProvider
    provider = get_cover_t2i_provider()
    assert isinstance(provider, FluxKontextProvider)


def test_engine_selector_returns_dalle_when_no_fal_key(monkeypatch):
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    from importlib import reload
    import app.services.engine_selector as es
    reload(es)
    from app.services.t2i_providers.dalle_provider import DalleProvider
    provider = es.get_cover_t2i_provider()
    assert isinstance(provider, DalleProvider)
```

**Success checklist:**
<<<<<<< HEAD
- [ ] `PromptEngineeringResult` schema importable
- [ ] `run_prompt_merge()` function signature matches spec exactly
- [ ] Anti-tokens always in negative prompt, never in main prompt
- [ ] COMPATIBLE / WARNING compatibility check working
- [ ] Fallback result returned on API failure (no exception propagated)
- [ ] FluxKontextProvider uses KONTEXT_ENDPOINT when image_url provided
- [ ] FluxKontextProvider uses TEXT_ENDPOINT when no image_url
- [ ] Engine selector returns Flux when FAL_API_KEY set, DALL-E otherwise
- [ ] All unit tests passing (no real API calls required)

---

## Phase 9b — Serper Search Provider

**Dependency:** Phase 7 complete (can run in parallel with Phases 8–9)
=======
- [x] `PromptEngineeringResult` schema importable
- [x] `run_prompt_merge()` function signature matches spec exactly
- [x] Anti-tokens always in negative prompt, never in main prompt
- [x] COMPATIBLE / WARNING compatibility check working
- [x] Fallback result returned on API failure (no exception propagated)
- [x] FluxKontextProvider uses KONTEXT_ENDPOINT when image_url provided
- [x] FluxKontextProvider uses TEXT_ENDPOINT when no image_url
- [x] Engine selector returns Flux when FAL_API_KEY set, DALL-E otherwise
- [x] All unit tests passing (no real API calls required)

---

## Phase 9b — Serper Search Provider ✅ Complete

**Dependency:** Phase 7 complete (can run in parallel with Phases 8–9)
**Status:** ✅ Complete

**Realization summary:** BaseSearchProvider and SearchResult added to providers/base.py; serper_provider.py (SerperProvider, hard blacklist, watermarked domains, POST google.serper.dev/images); get_supplementary_search_providers(entity_type) in engine_selector (Serper only for artefact/location); SERPER_API_KEY in .env.example; 10 unit tests in test_serper_provider.py (blacklist, watermark, is_available, search mock, engine selector routing).

>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `backend/app/services/providers/serper_provider.py` (new)
- `backend/app/services/engine_selector.py` (add Serper routing)
- `backend/.env.example` (add SERPER_API_KEY)
- `backend/tests/unit/test_serper_provider.py` (new)

### 9b.1 Serper Provider

Create `backend/app/services/providers/serper_provider.py`:

```python
"""
serper_provider.py
------------------
Google Search via Serper.dev API. Supplementary provider for artefact
and location reference image searches.

NOT used for book cover I2T searches (those target Goodreads/publisher
domains specifically — Serper's generic results are too noisy for style ref).

Domain policy:
  Hard blacklist (filtered entirely):
    lookaside.instagram.com, lookaside.fbsbx.com, craiyon.com,
    getimg.ai, ideogram.ai
  Soft flag (included with watermarked=True):
    shutterstock.com, dreamstime.com, gettyimages.com, istockphoto.com
"""
from __future__ import annotations

import logging
import os
from urllib.parse import urlparse

import httpx

from .base import BaseSearchProvider, SearchResult

logger = logging.getLogger(__name__)

_HARD_BLACKLIST = {
    "lookaside.instagram.com",
    "lookaside.fbsbx.com",
    "craiyon.com",
    "getimg.ai",
    "ideogram.ai",
}

_WATERMARK_DOMAINS = {
    "shutterstock.com",
    "dreamstime.com",
    "gettyimages.com",
    "istockphoto.com",
}


def _is_blacklisted(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith(f".{d}") for d in _HARD_BLACKLIST)
    except Exception:
        return False


def _is_watermarked(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        return any(host == d or host.endswith(f".{d}") for d in _WATERMARK_DOMAINS)
    except Exception:
        return False


class SerperProvider(BaseSearchProvider):
    """
    Serper.dev Google image search provider.
    Supplementary — used for artefact + location queries.
    """

    API_URL = "https://google.serper.dev/images"

    def is_available(self) -> bool:
        return bool(os.getenv("SERPER_API_KEY"))

    async def search(
        self,
        query: str,
        num: int = 10,
        **kwargs,
    ) -> list[SearchResult]:
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            logger.warning("SERPER_API_KEY not set — SerperProvider returning empty results")
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.API_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query, "num": num},
            )
            response.raise_for_status()
            data = response.json()

        results: list[SearchResult] = []
        for item in data.get("images", []):
            image_url = item.get("imageUrl", "")
            if not image_url:
                continue
            if _is_blacklisted(image_url):
                logger.debug(f"Blacklisted URL skipped: {image_url}")
                continue

            watermarked = _is_watermarked(image_url)
            results.append(
                SearchResult(
                    url=image_url,
                    title=item.get("title", ""),
                    source_url=item.get("link", ""),
                    provider="serper",
                    watermarked=watermarked,
                )
            )

        return results
```

### 9b.2 Engine Selector Routing

Add to `backend/app/services/engine_selector.py`:

```python
def get_supplementary_search_providers(entity_type: str) -> list:
    """
    Returns supplementary search providers for the given entity type.
    Serper is supplementary for artefact + location — not for book cover I2T search.
    """
    from app.services.providers.serper_provider import SerperProvider

    provider = SerperProvider()
    if not provider.is_available():
        return []

    if entity_type in ("artefact", "location"):
        return [provider]

    # Book cover searches: Serper too generic for style reference quality
    return []
```

### 9b.3 Unit Tests

File: `backend/tests/unit/test_serper_provider.py`

```python
import pytest
from app.services.providers.serper_provider import (
    SerperProvider, _is_blacklisted, _is_watermarked
)


def test_blacklisted_domains_rejected():
    assert _is_blacklisted("https://lookaside.instagram.com/image.jpg") is True
    assert _is_blacklisted("https://craiyon.com/output.png") is True
    assert _is_blacklisted("https://getimg.ai/gen/abc.png") is True
    assert _is_blacklisted("https://unsplash.com/photo.jpg") is False


def test_watermark_domains_flagged():
    assert _is_watermarked("https://shutterstock.com/photo-123.jpg") is True
    assert _is_watermarked("https://gettyimages.com/image.jpg") is True
    assert _is_watermarked("https://flickr.com/photo.jpg") is False


def test_is_available_false_without_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    assert SerperProvider().is_available() is False


def test_is_available_true_with_key(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    assert SerperProvider().is_available() is True


@pytest.mark.asyncio
async def test_returns_empty_without_key(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    results = await SerperProvider().search("dark fantasy art")
    assert results == []


@pytest.mark.asyncio
async def test_blacklisted_urls_filtered_from_results(monkeypatch, httpx_mock):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    httpx_mock.add_response(
        json={
            "images": [
                {"imageUrl": "https://craiyon.com/bad.png", "title": "Bad"},
                {"imageUrl": "https://unsplash.com/good.jpg", "title": "Good"},
            ]
        }
    )
    provider = SerperProvider()
    results = await provider.search("test query")
    assert len(results) == 1
    assert results[0].url == "https://unsplash.com/good.jpg"


@pytest.mark.asyncio
async def test_watermarked_flag_set_on_stock_photo_domains(monkeypatch, httpx_mock):
    monkeypatch.setenv("SERPER_API_KEY", "test_key")
    httpx_mock.add_response(
        json={
            "images": [
                {"imageUrl": "https://shutterstock.com/stock.jpg", "title": "Stock"},
            ]
        }
    )
    results = await SerperProvider().search("test query")
    assert results[0].watermarked is True
```

**Success checklist:**
<<<<<<< HEAD
- [ ] SerperProvider follows `BaseSearchProvider` interface
- [ ] Hard blacklist filters URLs before adding to results
- [ ] Watermarked flag set correctly for stock photo domains
- [ ] `is_available()` returns False gracefully when SERPER_API_KEY not set
- [ ] Engine selector returns Serper only for artefact/location entity types
- [ ] All unit tests passing

---

## Phase 10 — Frontend: SetupPage + WorkflowNav + FeatureGate

**Dependency:** Phase 9 complete (backend API stable before building frontend against it)
=======
- [x] SerperProvider follows `BaseSearchProvider` interface
- [x] Hard blacklist filters URLs before adding to results
- [x] Watermarked flag set correctly for stock photo domains
- [x] `is_available()` returns False gracefully when SERPER_API_KEY not set
- [x] Engine selector returns Serper only for artefact/location entity types
- [x] All unit tests passing

---

## Phase 10 — Frontend: SetupPage + WorkflowNav + FeatureGate ✅

**Dependency:** Phase 9 complete (backend API stable before building frontend against it)
**Status:** Complete. AuthContext, FeatureGate, WorkflowNav dual-path, workflow selector in BookUpload, analysis_mode in upload, new routes and stub pages, 5 frontend tests.
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `frontend/src/pages/SetupPage.tsx` (refactor)
- `frontend/src/pages/UploadPage.tsx` (add workflow mode selector)
- `frontend/src/components/WorkflowNav.tsx` (refactor — dual step set)
- `frontend/src/components/FeatureGate.tsx` (new)
- `frontend/src/context/AuthContext.tsx` (add user.plan field)
- `frontend/src/App.tsx` (add new routes)
- `frontend/src/tests/WorkflowNav.test.tsx` (new)
- `frontend/src/tests/FeatureGate.test.tsx` (new)

### 10.1 FeatureGate Component

Create `frontend/src/components/FeatureGate.tsx`:

```typescript
import { useAuth } from '@/context/AuthContext'

interface FeatureGateProps {
  plan: 'pro'
  fallback?: React.ReactNode
  children: React.ReactNode
}

/**
 * Gates children behind a plan tier check.
 * Reads user.plan from AuthContext — set by login response / JWT claim.
 *
 * Usage:
 *   <FeatureGate plan="pro" fallback={<UpgradeBanner feature="Advanced prompt editing" />}>
 *     <Panel A content />
 *   </FeatureGate>
 */
export function FeatureGate({ plan, fallback = null, children }: FeatureGateProps) {
  const { user } = useAuth()

  if (plan === 'pro' && user?.plan !== 'pro') {
    return <>{fallback}</>
  }

  return <>{children}</>
}

interface UpgradeBannerProps {
  feature: string
}

export function UpgradeBanner({ feature }: UpgradeBannerProps) {
  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
      <span className="font-medium">{feature}</span> is available on the Pro plan.{' '}
      <a href="/upgrade" className="underline">Upgrade</a>
    </div>
  )
}
```

### 10.2 WorkflowNav Dual-Path Steps

Refactor `frontend/src/components/WorkflowNav.tsx`:

```typescript
import { useBook } from '@/context/BookContext'
import { useLocation, useNavigate } from 'react-router-dom'

const COVER_ONLY_STEPS = [
  { label: 'Upload',       path: 'manuscript-upload' },
  { label: 'Characters',   path: 'analysis-review' },
  { label: 'Mood Board',   path: 'mood-board' },
  { label: 'Cover Brief',  path: 'cover-brief' },
  { label: 'Generate',     path: 'studio/cover' },
  { label: 'Typography',   path: 'studio/text' },
]

const FULL_BOOK_STEPS = [
  { label: 'Upload',       path: 'manuscript-upload' },
  { label: 'AI Analysis',  path: 'analysis-review' },
  { label: 'Mood Board',   path: 'mood-board' },
  { label: 'Cover Brief',  path: 'cover-brief' },
  { label: 'Generate',     path: 'studio/cover' },
  { label: 'Typography',   path: 'studio/text' },
  { label: 'Preview',      path: 'preview' },
]

export function WorkflowNav() {
  const { workflowType } = useBook()
  const location = useLocation()
  const navigate = useNavigate()
  const steps = workflowType === 'cover_only' ? COVER_ONLY_STEPS : FULL_BOOK_STEPS

  return (
    <nav aria-label="Workflow steps" className="flex items-center gap-2 px-6 py-3 border-b bg-white">
      {steps.map((step, index) => {
        const isActive = location.pathname.includes(step.path)
        const isComplete = false // TODO: derive from analysisProgress context
        return (
          <button
            key={step.path}
            onClick={() => navigate(step.path)}
            aria-current={isActive ? 'step' : undefined}
            className={[
              'flex items-center gap-1.5 rounded px-3 py-1.5 text-sm font-medium transition-colors',
              isActive ? 'bg-indigo-600 text-white' : 'text-gray-500 hover:text-gray-900',
              isComplete ? 'text-green-700' : '',
            ].join(' ')}
          >
            {isComplete && <span aria-hidden>✓</span>}
            <span>{step.label}</span>
          </button>
        )
      })}
    </nav>
  )
}
```

### 10.3 UploadPage — Workflow Mode Selector

Add to the upload form in `frontend/src/pages/UploadPage.tsx`:

```typescript
// Add after title/genre fields, before submit button:

const { user } = useAuth()
const isSimple = user?.plan !== 'pro'

// Workflow selector
<fieldset className="mt-4">
  <legend className="text-sm font-medium text-gray-700 mb-2">Workflow</legend>
  <div className="flex gap-4">
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="radio"
        name="analysis_mode"
        value="simple"
        checked={analysisMode === 'simple'}
        onChange={() => setAnalysisMode('simple')}
      />
      <span>Book Cover <span className="text-xs text-gray-400">(Fast)</span></span>
    </label>
    <label className={`flex items-center gap-2 ${isSimple ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}>
      <input
        type="radio"
        name="analysis_mode"
        value="pro"
        checked={analysisMode === 'pro'}
        onChange={() => !isSimple && setAnalysisMode('pro')}
        disabled={isSimple}
      />
      <span>Full Book</span>
      {isSimple && (
        <span className="text-xs text-amber-600 ml-1">(Pro only)</span>
      )}
    </label>
  </div>
</fieldset>
```

Pass `analysis_mode` to `createBook()` API call.

### 10.4 App.tsx Routes

Add to `frontend/src/App.tsx` routes:

```typescript
{ path: 'mood-board',    element: <MoodBoardPage /> },
{ path: 'cover-brief',   element: <AnalysisReviewPage /> },
{ path: 'studio/cover',  element: <CoverStudioPage /> },
{ path: 'studio/text',   element: <TextStudioPage /> },
{ path: 'preview',       element: <ReadingPage /> },
```

Retain existing routes (`review-search`, `visual-bible`) for backward compatibility.

### 10.5 Unit Tests

File: `frontend/src/tests/WorkflowNav.test.tsx`:
```typescript
import { render, screen } from '@testing-library/react'
import { WorkflowNav } from '@/components/WorkflowNav'

test('cover_only path shows Typography step not Preview', () => {
  // mock BookContext with workflowType: 'cover_only'
  render(<WorkflowNav />, { wrapper: makeContextWrapper({ workflowType: 'cover_only' }) })
  expect(screen.getByText('Typography')).toBeInTheDocument()
  expect(screen.queryByText('Preview')).not.toBeInTheDocument()
})

test('full_book path includes Preview step', () => {
  render(<WorkflowNav />, { wrapper: makeContextWrapper({ workflowType: 'full_book' }) })
  expect(screen.getByText('Preview')).toBeInTheDocument()
})
```

File: `frontend/src/tests/FeatureGate.test.tsx`:
```typescript
test('renders children for pro user', () => {
  render(<FeatureGate plan="pro"><span>Pro content</span></FeatureGate>, {
    wrapper: makeAuthWrapper({ plan: 'pro' })
  })
  expect(screen.getByText('Pro content')).toBeInTheDocument()
})

test('renders fallback for simple user', () => {
  render(
    <FeatureGate plan="pro" fallback={<span>Upgrade banner</span>}><span>Pro content</span></FeatureGate>,
    { wrapper: makeAuthWrapper({ plan: 'simple' }) }
  )
  expect(screen.getByText('Upgrade banner')).toBeInTheDocument()
  expect(screen.queryByText('Pro content')).not.toBeInTheDocument()
})

test('workflow selector renders Full Book disabled for simple user', () => {
  render(<UploadPage />, { wrapper: makeAuthWrapper({ plan: 'simple' }) })
  expect(screen.getByRole('radio', { name: /Full Book/i })).toBeDisabled()
})
```

**Success checklist:**
- [ ] FeatureGate renders children for pro, fallback for simple
- [ ] WorkflowNav renders correct step count per workflowType
- [ ] UploadPage workflow selector disables Full Book for simple users
- [ ] analysis_mode sent to API on book creation
- [ ] New routes registered in App.tsx
- [ ] All unit tests passing

---

<<<<<<< HEAD
## Phase 11 — Frontend: AnalysisReviewPage + CoverBriefEditor

**Dependency:** Phase 10 complete
=======
## Phase 11 — Frontend: AnalysisReviewPage + CoverBriefEditor ✅

**Dependency:** Phase 10 complete
**Status:** Complete. Tabs by analysis_mode, is_main badge + is_selected_for_reference toggle, CoverBriefEditor (Simple/Pro, Panel A/B, localStorage), 9 unit tests.
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)
**Files touched:**
- `frontend/src/pages/AnalysisReviewPage.tsx` (new — full implementation)
- `frontend/src/components/CoverBriefEditor.tsx` (new)
- `frontend/src/tests/AnalysisReviewPage.test.tsx` (new)
- `frontend/src/tests/CoverBriefEditor.test.tsx` (new)

### 11.1 AnalysisReviewPage

The page branches based on `book.analysis_mode` stored in BookContext:

```typescript
// Tab structure:
// Simple (Book Cover mode): Characters tab only
// Pro (Full Book mode): Characters | Locations | Artefacts | Cover tabs

// Per entity tab:
// - Entity cards with is_main badge (readonly — do not allow editing is_main here)
// - is_selected_for_reference toggle (calls PUT /api/books/{id}/entity-selections)
// - Visual token summary (core_tokens from entity_visual_tokens_json)
// - "Find references" link → navigates to MoodBoardPage with entity pre-selected

// Cover tab (Pro only):
// - Renders <CoverBriefEditor />

// On mount: fetch all active entity types, populate from BookContext or API
```

### 11.2 CoverBriefEditor

Create `frontend/src/components/CoverBriefEditor.tsx`:

```typescript
// SIMPLE TIER layout (analysis_mode === 'simple'):
//   - Cover type selector (dropdown: illustrated | photographic | typographic | abstract)
//   - Primary element selector (character select from extracted characters)
//   - Style reference thumbnail (if reference_image_url exists on CoverAnalysis)
//   - "Generate Cover" button → navigates to CoverStudioPage, triggers generation
//   - NO prompt panels visible

// PRO TIER layout (analysis_mode === 'pro'):
//   - Cover type selector (same as simple)
//   - Primary element selector (character | location | artefact — from extracted entities)
//   - Panel B — Merged Prompt (always visible, editable textarea)
//     * Populated from CoverAnalysis assembled_prompt (built by backend)
//     * User can edit freely — value sent as override to generate endpoint
//   - Panel A — I2T Style Template (collapsed by default)
//     * "Advanced ▾" toggle expands this panel
//     * Shows CoverAnalysis.reference_style_template (readonly — informational)
//     * Collapsible preference saved to localStorage key: 'noctua_panel_a_expanded'
//   - Negative prompt field (textarea, Pro only, FeatureGate-gated)
//   - "Generate Cover" button

// State:
//   coverType: string
//   primaryEntityId: number | null
//   mergedPromptOverride: string | null  // null = use backend assembled prompt
//   negativePromptOverride: string | null
//   panelAExpanded: boolean  // persisted to localStorage
```

### 11.3 Unit Tests

File: `frontend/src/tests/CoverBriefEditor.test.tsx`:

```typescript
test('simple tier hides prompt panels', () => {
  render(<CoverBriefEditor />, { wrapper: makeBookContextWrapper({ analysisMode: 'simple' }) })
  expect(screen.queryByText(/Advanced/i)).not.toBeInTheDocument()
  expect(screen.queryByLabelText(/Merged Prompt/i)).not.toBeInTheDocument()
})

test('pro tier shows Panel B always visible', () => {
  render(<CoverBriefEditor />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) })
  expect(screen.getByLabelText(/Merged Prompt/i)).toBeInTheDocument()
})

test('Advanced toggle expands Panel A', async () => {
  render(<CoverBriefEditor />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) })
  await userEvent.click(screen.getByText(/Advanced/i))
  expect(screen.getByText(/Style Template/i)).toBeInTheDocument()
})

test('panel A expansion state saved to localStorage', async () => {
  render(<CoverBriefEditor />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) })
  await userEvent.click(screen.getByText(/Advanced/i))
  expect(localStorage.getItem('noctua_panel_a_expanded')).toBe('true')
})

test('negative prompt field gated behind FeatureGate', () => {
  render(<CoverBriefEditor />, { wrapper: makeAuthWrapper({ plan: 'simple' }) })
  expect(screen.queryByLabelText(/Negative prompt/i)).not.toBeInTheDocument()
})
```

File: `frontend/src/tests/AnalysisReviewPage.test.tsx`:

```typescript
test('simple mode shows only Characters tab', () => {
  render(<AnalysisReviewPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'simple' }) })
  expect(screen.getByText('Characters')).toBeInTheDocument()
  expect(screen.queryByText('Locations')).not.toBeInTheDocument()
  expect(screen.queryByText('Artefacts')).not.toBeInTheDocument()
})

test('pro mode shows all four tabs', () => {
  render(<AnalysisReviewPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) })
  expect(screen.getByText('Characters')).toBeInTheDocument()
  expect(screen.getByText('Locations')).toBeInTheDocument()
  expect(screen.getByText('Artefacts')).toBeInTheDocument()
  expect(screen.getByText('Cover')).toBeInTheDocument()
})

test('is_main shown as badge, not editable', () => {
  render(<AnalysisReviewPage />, { wrapper: makeWithCharacters([{ name: 'Sera', is_main: true }]) })
  expect(screen.getByText('Main')).toBeInTheDocument()
  expect(screen.queryByRole('checkbox', { name: /Main character/i })).not.toBeInTheDocument()
})

test('is_selected_for_reference toggle calls entity-selections endpoint', async () => {
  const api = setupApiMock()
  render(<AnalysisReviewPage />, { wrapper: defaultWrapper() })
  await userEvent.click(screen.getByRole('switch', { name: /Use as reference/i }))
  expect(api.entitySelections).toHaveBeenCalled()
})
```

**Success checklist:**
- [ ] Simple tier: only Characters tab visible
- [ ] Pro tier: all four tabs visible
- [ ] `is_main` displayed as badge, never as editable toggle
- [ ] `is_selected_for_reference` toggle calls correct endpoint
- [ ] CoverBriefEditor panel A collapsed by default, localStorage persists state
- [ ] CoverBriefEditor Panel B always visible in Pro tier
- [ ] Negative prompt field hidden from Simple tier via FeatureGate
- [ ] All unit tests passing

---

<<<<<<< HEAD
## Phase 12 — Frontend: MoodBoardPage
=======
## Phase 12 — Frontend: MoodBoardPage ✅
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)

**Dependency:** Phase 11 complete
**Files touched:**
- `frontend/src/pages/MoodBoardPage.tsx` (new)
- `frontend/src/tests/MoodBoardPage.test.tsx` (new)

### 12.1 MoodBoardPage Structure

```typescript
// SIMPLE (Book Cover mode — analysis_mode === 'simple'):
//   Single "Style Reference" tab only
//
// PRO (Full Book mode — analysis_mode === 'pro'):
//   Four tabs: Style Reference | Characters | Locations | Artefacts

// STYLE REFERENCE TAB (both tiers):
//   - Image grid of uploaded/selected cover reference images
//   - "Upload cover reference" button → POST /api/books/{id}/reference-upload (type=cover)
//   - "Search for similar covers" link → opens Serper/Behance search (existing provider routing)
//   - "Analyse style" button (explicit trigger — NOT automatic):
//     * Visible only when at least one reference image is selected
//     * On click: POST /api/books/{id}/analyze-cover-reference with first selected image URL
//     * Loading state: spinner + "Extracting style..." message overlay on button
//     * On success: show StyleTemplateSummaryCard (see 12.2)
//     * On error: show dismissible error toast — "Style analysis failed. You can still continue."
//       Moodboard remains fully functional after error.
//   - IMPORTANT: Analyse style does NOT auto-trigger on image upload or select.

// CHARACTER / LOCATION / ARTEFACT TABS (Pro only):
//   Per entity type:
//   - Image grid grouped by entity name
//   - Select/deselect toggle on each card
//   - "Upload your own" button per entity section
//   - "Approve to Visual Bible" button → PUT /api/books/{id}/visual-bible/approve

// NAVIGATION:
//   "Continue to Cover Brief" button (bottom bar) → navigates to cover-brief route
```

### 12.2 StyleTemplateSummaryCard

After successful I2T analysis, render:

```typescript
// StyleTemplateSummaryCard:
//   - Genre chips: style_tags (list of pills)
//   - Mood keywords (list of pills, different colour)
//   - Color palette swatches: dominant + accent (small colored squares with label)
//   - Lighting description (one line of text)
//   - "View in Cover Brief editor" link → navigates to cover-brief, expands Panel A
//   - Card is dismissible (X button) — dismissal does not undo the I2T result in DB
```

### 12.3 Unit Tests

File: `frontend/src/tests/MoodBoardPage.test.tsx`:

```typescript
test('simple mode renders only Style Reference tab', () => {
  render(<MoodBoardPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'simple' }) })
  expect(screen.getByText('Style Reference')).toBeInTheDocument()
  expect(screen.queryByText('Characters')).not.toBeInTheDocument()
})

test('pro mode renders all four tabs', () => {
  render(<MoodBoardPage />, { wrapper: makeBookContextWrapper({ analysisMode: 'pro' }) })
  expect(screen.getByText('Style Reference')).toBeInTheDocument()
  expect(screen.getByText('Characters')).toBeInTheDocument()
  expect(screen.getByText('Locations')).toBeInTheDocument()
})

test('Analyse style button not visible without selected image', () => {
  render(<MoodBoardPage />, { wrapper: defaultWrapper() })
  expect(screen.queryByRole('button', { name: /Analyse style/i })).not.toBeInTheDocument()
})

test('Analyse style button visible when image selected', async () => {
  render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() })
  expect(screen.getByRole('button', { name: /Analyse style/i })).toBeInTheDocument()
})

test('clicking Analyse style calls analyze-cover-reference endpoint', async () => {
  const api = setupApiMock()
  render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() })
  await userEvent.click(screen.getByRole('button', { name: /Analyse style/i }))
  expect(api.analyzeCoverReference).toHaveBeenCalledOnce()
})

test('success state shows StyleTemplateSummaryCard', async () => {
  setupApiMock({ analyzeCoverReference: mockI2TSuccess })
  render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() })
  await userEvent.click(screen.getByRole('button', { name: /Analyse style/i }))
  await screen.findByText(/View in Cover Brief/i)
})

test('error state shows dismissible toast without blocking moodboard', async () => {
  setupApiMock({ analyzeCoverReference: mockI2TFailure })
  render(<MoodBoardPage />, { wrapper: wrapperWithSelectedImage() })
  await userEvent.click(screen.getByRole('button', { name: /Analyse style/i }))
  expect(await screen.findByText(/Style analysis failed/i)).toBeInTheDocument()
  // Moodboard tabs still functional
  expect(screen.getByRole('button', { name: /Continue to Cover Brief/i })).toBeEnabled()
})

test('Analyse style does NOT auto-trigger on image upload', async () => {
  const api = setupApiMock()
  render(<MoodBoardPage />, { wrapper: defaultWrapper() })
  await userEvent.upload(screen.getByTestId('cover-upload-input'), mockFile)
  expect(api.analyzeCoverReference).not.toHaveBeenCalled()
})
```

**Success checklist:**
- [ ] Simple mode: only Style Reference tab visible
- [ ] Pro mode: all four tabs visible
- [ ] "Analyse style" button requires explicit click — never auto-triggered
- [ ] Button only appears after at least one image is selected/uploaded
- [ ] Loading state shown during I2T call
- [ ] StyleTemplateSummaryCard shown on success
- [ ] Error toast shown on failure — moodboard still usable
- [ ] All unit tests passing

---

<<<<<<< HEAD
## Phase 13 — Cover Generation Endpoint Wire-Up + CoverStudioPage + TextStudioPage
=======
## Phase 13 — Cover Generation Endpoint Wire-Up + CoverStudioPage + TextStudioPage ✅
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)

**Dependency:** Phase 12 complete + Phase 9 complete (both must be done)
**Files touched:**
- `backend/app/routers/covers.py` (wire POST /api/books/{id}/covers/generate to real services)
- `frontend/src/pages/CoverStudioPage.tsx` (new)
- `frontend/src/pages/TextStudioPage.tsx` (new)
- `frontend/src/tests/CoverStudioPage.test.tsx` (new)
- `frontend/src/tests/TextStudioPage.test.tsx` (new)

### 13.1 Backend — Wire Generate Endpoint

In `backend/app/routers/covers.py`, update the `POST /api/books/{book_id}/covers/generate` handler (currently a stub) to call the real pipeline:

```python
@router.post("/{book_id}/covers/generate", response_model=CoverConceptRead, status_code=202)
async def generate_cover(
    book_id: int,
    body: CoverGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Starts async cover generation. Returns a CoverConcept record with status='generating'.
    Client polls GET /covers/{concept_id} until status changes.

    Pipeline:
    1. If CoverAnalysis.reference_style_template exists → PromptEngineeringService merge
    2. Else → CoverPromptAssembler fallback (genre + character tokens)
    3. Call get_cover_t2i_provider().generate(final_prompt, image_url=entity_ref_url)
    4. Save result URL to CoverConcept.generated_image_url, set status='complete'
    """
    cover_analysis = crud.get_or_create_cover_analysis(db, book_id)
    concept = crud.create_cover_concept(db, book_id, status="generating")

    background_tasks.add_task(
        _generate_concept_background,
        book_id=book_id,
        concept_id=concept.id,
        cover_analysis_id=cover_analysis.id,
        body=body,
        db_session_factory=get_db_session_factory(),
    )

    return concept


async def _generate_concept_background(
    book_id: int,
    concept_id: int,
    cover_analysis_id: int,
    body: CoverGenerateRequest,
    db_session_factory,
):
    from app.services.prompt_engineering_service import run_prompt_merge
    from app.services.cover_prompt_assembler import CoverPromptAssembler
    from app.services.engine_selector import get_cover_t2i_provider

    async with db_session_factory() as db:
        cover_analysis = crud.get_cover_analysis(db, cover_analysis_id)
        primary_entity = _resolve_primary_entity(db, cover_analysis)

        if cover_analysis.reference_style_template and primary_entity:
            # Primary path: I2T → PromptEngineeringService
            pe_result = await run_prompt_merge(
                style_template=cover_analysis.reference_style_template,
                entity=primary_entity,
                user_instruction=body.user_instruction or "Replace the main subject with this entity.",
            )
            final_prompt = pe_result.final_prompt
            negative_prompt = pe_result.negative_prompt
        else:
            # Fallback path: CoverPromptAssembler
            assembler = CoverPromptAssembler()
            book = crud.get_book(db, book_id)
            asm_result = assembler.assemble(
                genre=book.genre or "fantasy",
                cover_type=cover_analysis.cover_type or "illustrated",
                primary_entity_tokens=_get_primary_entity_tokens(db, cover_analysis),
            )
            final_prompt = asm_result.prompt
            negative_prompt = asm_result.negative_prompt

        # Get entity reference image URL for FLUX Kontext conditioning
        ref_image_url = _get_entity_reference_url(db, cover_analysis)

        provider = get_cover_t2i_provider()
        try:
            gen_result = await provider.generate(
                prompt=final_prompt,
                image_url=ref_image_url,
                negative_prompt=negative_prompt or None,
            )
            crud.update_cover_concept(db, concept_id, {
                "generated_image_url": gen_result.url,
                "prompt_used": final_prompt,
                "negative_prompt_used": negative_prompt,
                "status": "complete",
                "provider_used": gen_result.provider,
            })
        except Exception as exc:
            logger.error(f"Cover generation failed for concept {concept_id}: {exc}")
            crud.update_cover_concept(db, concept_id, {"status": "failed", "error": str(exc)})
```

### 13.2 CoverStudioPage

Create `frontend/src/pages/CoverStudioPage.tsx`:

```typescript
// On mount:
// 1. Check if a pending generate request should be fired (from CoverBriefEditor state)
// 2. If yes: POST /api/books/{id}/covers/generate with user_instruction from CoverBriefEditor
// 3. Poll GET /api/books/{id}/cover-concepts every 3s until all concepts have status != 'generating'

// Layout:
// - Generation status bar: "Generating N concepts..." with spinner
// - Concept grid: shows cover concept cards as they complete
// - Each card: generated image thumbnail + "Select" button + params_log accordion (Pro only)
// - Max concepts: 3 (Simple) | 6 (Pro) — enforced by backend, front-end shows count
// - "Regenerate" button: posts new generation request (re-polls)
// - "Continue to Typography" button (enabled when at least 1 concept selected)
//   → navigates to studio/text with selected concept in context

// KDP note (visible in UI):
// - "Final cover will be exported at 2560×1600px, 300dpi, with 0.125" bleed — KDP compatible"
// - Display this note above the concept grid
```

### 13.3 TextStudioPage

Create `frontend/src/pages/TextStudioPage.tsx`:

```typescript
// Pure browser-side canvas compositing. No backend calls for typography.

// Layout:
// - Canvas element: shows selected cover concept image as background
// - Text overlay controls (sidebar):
//   - Title text input + font selector (genre-appropriate presets)
//   - Author name text input + font selector
//   - Text color picker
//   - Text size slider
// - Drag-to-reposition: text elements draggable on canvas (pointer events)
// - Smart placement hint: detect negative space at top of image → suggest title placement there
// - Font library:
//   - Simple tier: genre presets (5 curated options per genre)
//   - Pro tier: full library + "Upload custom font" (FeatureGate-gated)
// - Export button:
//   - Flatten canvas to PNG via canvas.toBlob()
//   - Trigger browser download: "noctua-cover-{title}.png"
//   - Export dimensions: 2560×1600 (KDP). Display this spec visibly above export button:
//     "Export: 2560×1600px · 300dpi · 0.125" bleed · KDP compatible"
```

**Note on KDP spec:** Before implementation, verify current KDP cover spec at:
https://kdp.amazon.com/en_US/help/topic/G200645690
The plan specifies 2560×1600 at 300dpi with 0.125" bleed — confirm this is current before coding the export function.

### 13.4 Unit Tests

```typescript
// CoverStudioPage.test.tsx
test('shows KDP spec note above concept grid', () => {
  render(<CoverStudioPage />)
  expect(screen.getByText(/2560×1600/i)).toBeInTheDocument()
})

test('Continue button disabled until concept selected', () => {
  render(<CoverStudioPage />, { wrapper: withNoConceptSelected() })
  expect(screen.getByRole('button', { name: /Continue to Typography/i })).toBeDisabled()
})

test('Continue button enabled after concept selected', () => {
  render(<CoverStudioPage />, { wrapper: withConceptSelected() })
  expect(screen.getByRole('button', { name: /Continue to Typography/i })).toBeEnabled()
})

test('Simple tier shows max 3 concept slots', () => {
  render(<CoverStudioPage />, { wrapper: makeAuthWrapper({ plan: 'simple' }) })
  expect(screen.getAllByTestId('concept-slot').length).toBeLessThanOrEqual(3)
})

// TextStudioPage.test.tsx
test('renders canvas element', () => {
  render(<TextStudioPage />)
  expect(document.querySelector('canvas')).toBeInTheDocument()
})

test('export button shows KDP spec', () => {
  render(<TextStudioPage />)
  expect(screen.getByText(/KDP compatible/i)).toBeInTheDocument()
})

test('custom font upload gated behind FeatureGate', () => {
  render(<TextStudioPage />, { wrapper: makeAuthWrapper({ plan: 'simple' }) })
  expect(screen.queryByText(/Upload custom font/i)).not.toBeInTheDocument()
})
```

**Success checklist:**
- [ ] `POST /api/books/{id}/covers/generate` calls PromptEngineeringService when style_template exists
- [ ] Fallback to CoverPromptAssembler when no style_template
- [ ] CoverConcept record status transitions: generating → complete | failed
- [ ] CoverStudioPage polls until all concepts have non-generating status
- [ ] KDP spec note visible in both CoverStudioPage and TextStudioPage
- [ ] TextStudioPage export uses canvas.toBlob() — no backend round-trip
- [ ] Custom font upload gated behind FeatureGate (Pro only)
- [ ] All unit tests passing

---

<<<<<<< HEAD
## Phase 14 — Frontend E2E Tests
=======
## Phase 14 — Frontend E2E Tests ✅ COMPLETE
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)

**Dependency:** Phases 10–13 complete
**Files touched:**
- `frontend/playwright.config.ts` (new)
- `frontend/e2e/cover_only_path.spec.ts` (new)
- `frontend/e2e/full_book_path.spec.ts` (new)
- `backend/tests/e2e/test_e2e_i2t_pipeline.py` (new)

### 14.1 Playwright Config

Create `frontend/playwright.config.ts`:

```typescript
import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: !process.env.CI,
  },
})
```

### 14.2 Cover-Only Path E2E

File: `frontend/e2e/cover_only_path.spec.ts`:

```typescript
import { test, expect } from '@playwright/test'

test.describe('Cover-Only Path (Simple Tier)', () => {
  test('upload → analysis → moodboard → cover brief → generate', async ({ page }) => {
    await page.goto('/')
    await page.click('text=New Book')
    await page.setInputFiles('input[type=file]', 'e2e/fixtures/short_story.txt')
    await page.fill('input[name=title]', 'The Ember Crown')
    await page.selectOption('select[name=genre]', 'fantasy')
    await page.check('input[value=simple]')  // Book Cover workflow
    await page.click('text=Continue')

    // Should land on analysis review — only Characters tab
    await expect(page.locator('[role=tab][name=Characters]')).toBeVisible()
    await expect(page.locator('[role=tab][name=Locations]')).not.toBeVisible()

    // Navigate to Moodboard
    await page.click('text=Mood Board')
    await expect(page.locator('[role=tab][name="Style Reference"]')).toBeVisible()

    // Upload cover reference
    await page.setInputFiles('[data-testid=cover-upload-input]', 'e2e/fixtures/sample_cover.jpg')
    await expect(page.getByRole('button', { name: /Analyse style/i })).toBeVisible()

    // Navigate to Cover Brief (skip I2T for speed in E2E)
    await page.click('text=Continue to Cover Brief')
    await expect(page.locator('[data-testid=cover-type-selector]')).toBeVisible()
    await expect(page.locator('[data-testid=prompt-panel-b]')).not.toBeVisible() // Simple hides panels

    // Trigger generation
    await page.click('text=Generate Cover')
    await expect(page.locator('text=Generating')).toBeVisible()
    await expect(page.locator('[data-testid=concept-card]')).toBeVisible({ timeout: 60000 })
  })
})
```

### 14.3 Backend E2E — I2T Pipeline

File: `backend/tests/e2e/test_e2e_i2t_pipeline.py`:

```python
import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY"
)


def test_full_i2t_pipeline(client, book_id):
    """End-to-end: reference image → I2T → prompt merge → CoverConcept."""
    # 1. Run I2T analysis
    r = client.post(
        f"/api/books/{book_id}/analyze-cover-reference",
        json={
            "image_url": "https://covers.openlibrary.org/b/id/8224689-L.jpg",
            "mode": "cover",
        }
    )
    assert r.status_code == 200
    i2t = r.json()
    assert i2t["style_template"] != ""

    # 2. Verify CoverAnalysis updated
    r2 = client.get(f"/api/books/{book_id}/cover-analysis")
    assert r2.json()["reference_style_template"] == i2t["style_template"]

    # 3. Trigger generation (uses I2T result automatically)
    r3 = client.post(
        f"/api/books/{book_id}/covers/generate",
        json={"user_instruction": "Keep the atmospheric style, use the main character"},
    )
    assert r3.status_code == 202
    concept_id = r3.json()["id"]
    assert r3.json()["status"] == "generating"

    # 4. Poll until complete (skip in CI if no FAL_API_KEY)
    if not os.getenv("FAL_API_KEY"):
        pytest.skip("FAL_API_KEY not set — skipping generation poll")

    import time
    for _ in range(30):
        r4 = client.get(f"/api/cover-concepts/{concept_id}")
        if r4.json()["status"] in ("complete", "failed"):
            break
        time.sleep(2)

    assert r4.json()["status"] == "complete"
    assert r4.json()["generated_image_url"].startswith("https://")
```

**Success checklist:**
<<<<<<< HEAD
- [ ] Cover-only E2E passes end-to-end (may stub generation step in CI)
- [ ] Backend E2E validates I2T → CoverAnalysis storage → generation trigger
- [ ] All Playwright tests pass locally with `npx playwright test`
- [ ] Backend E2E tests skip gracefully when API keys not set
=======
- [x] Cover-only E2E passes end-to-end (may stub generation step in CI)
- [x] Backend E2E validates I2T → CoverAnalysis storage → generation trigger
- [x] All Playwright tests pass locally with `npx playwright test`
- [x] Backend E2E tests skip gracefully when API keys not set

**Done:** Playwright config, `cover_only_path.spec.ts`, `full_book_path.spec.ts`, fixtures; backend `test_e2e_i2t_pipeline.py` (skipif no OPENAI_API_KEY/FAL_API_KEY). `CoverAnalysisResponse` extended with `reference_style_template`, `reference_style_notes`, `reference_image_url`. Tab/aria and data-testid added for E2E selectors.
>>>>>>> 9137d41 (NoctuaV1: cover studio, I2T pipeline, Dalle/Serper, e2e tests, planning docs)

---

## Phase 15 — Visual Identity + Enhancement Backlog

**Dependency:** Phase 8a complete (can run on separate branch any time after that)
**Files touched:**
- `frontend/src/styles/` — design tokens, Tailwind config extensions
- `frontend/src/components/ui/` — shared UI primitives (Button, Card, Badge, Toast)
- `docs/enhancement_backlog.md` (new)

### 15.1 Design Tokens

Extend Tailwind config with Noctua brand tokens:

```javascript
// tailwind.config.js additions
theme: {
  extend: {
    colors: {
      noctua: {
        900: '#0d0d1a',   // Deep midnight — primary background
        800: '#1a1a2e',   // Card background
        700: '#252540',   // Border, divider
        500: '#6366f1',   // Indigo primary action
        300: '#a5b4fc',   // Indigo light — hover state
        gold: '#f59e0b',  // Accent — badges, highlights
      }
    },
    fontFamily: {
      display: ['Playfair Display', 'serif'],
      body: ['Inter', 'sans-serif'],
    }
  }
}
```

### 15.2 Shared UI Components

Create in `frontend/src/components/ui/`:
- `Button.tsx` — primary / secondary / ghost variants, loading state
- `Card.tsx` — base card with optional hover elevation
- `Badge.tsx` — pill badges (genre, mood, entity type)
- `Toast.tsx` — dismissible success / error / info toasts
- `Spinner.tsx` — loading indicator

All components must use Noctua design tokens and match the dark-panel visual identity.

### 15.3 Enhancement Backlog

Create `docs/enhancement_backlog.md`:

```markdown
# Noctua — Enhancement Backlog

Items deferred from implementation plan. Add to future planning sessions in priority order.

## AI / Generation

- **CLIP text encoder** for compatibility pre-check in PromptEngineeringService
  (replaces heuristic check with vector similarity). Deferred: D6.
- **CLIP image embedding** for style tag validation (catches GPT-4o Vision hallucinations).
  Would run post-I2T to verify style_tags against actual image embedding.
- **Leonardo.ai secondary T2I provider** (`leonardo_provider.py`). Use for Phoenix/PhotoReal
  aesthetic alternatives. Already planned architecture; add when fal.ai pipeline is stable.
- **LoRA training** for character visual consistency in illustration pipeline.
  Replicate or Leonardo Enterprise. Prerequisite for Phase 17.
- **Direct image conditioning** opt-in for user-owned covers (premium future feature).
  Currently blocked by copyright policy (third-party covers → I2T text path only).

## Cover Studio

- **Style intensity slider** (Pro tier): parameter controlling how strongly the style_template
  influences the merge vs. entity tokens. Maps to FLUX guidance_scale.
- **Composition lock toggle** (Pro tier): locks the compositional structure from style_template
  (foreground/background layers, camera angle) even when entity is incompatible.
- **Variation controls** (Pro tier): seed control, style_strength, num_inference_steps.
- **3D mockup preview**: after TextStudio export, show cover on 3D book mockup.
  Library: three.js or CSS 3D transform. User can screenshot for marketing.

## Typography (TextStudio)

- **Smart font pairing**: after user selects title font, suggest complementary author name font.
- **Spine text** for print books: side text overlay panel (requires expanded canvas).
- **Series branding**: lock font + color choice across multiple books in a series.

## Platform

- **API access** for Pro+ / developer tier: generate covers programmatically.
- **Community gallery**: opt-in sharing of generated covers with genre tag for discovery.
  Requires moderation layer before launch.
- **Collaborative review**: share a cover draft link with editor/agent for comment.

## Infrastructure

- **CDN caching** for generated images (currently direct fal.ai URLs — not permanent).
- **Stripe billing integration** (currently user.plan is a static DB field).
- **Usage tracking**: images generated per month per user (enforce tier limits).
```

**Success checklist:**
- [ ] Tailwind tokens added and applied to at least WorkflowNav and CoverBriefEditor
- [ ] 5 shared UI primitives created and used in at least one existing component
- [ ] `docs/enhancement_backlog.md` created with full item list
- [ ] No regressions in existing component tests

---

## Phase 16 — Alpha Deployment (Auth + PostgreSQL + Railway)

**Dependency:** Phase 15 complete. Always the final phase.
**Files touched:** All layers — treat this phase as a dedicated deployment session.

### 16.1 Auth Layer

This phase carries forward the existing Phase 16 from `Noctua_Implementation_Plan_Merged.md` verbatim, with the following additions:

Add to `User` model (`backend/app/models.py`):

```python
plan: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    default="simple",
    server_default="simple",
    comment="'simple' | 'pro'. Controls frontend FeatureGate."
)
```

Add Alembic migration for `user.plan` field.

Include `plan` in JWT token payload and user context response so the frontend `FeatureGate` component has access without an additional API call.

### 16.2 Remainder of Phase 16

Carry forward verbatim from `Noctua_Implementation_Plan_Merged.md` Phase 16:
- PostgreSQL database migration from SQLite
- Railway.app deployment configuration
- Environment variable management (Railway secrets)
- Health check endpoint
- Production CORS configuration
- Launch readiness checklist

**Carry forward launch readiness checklist** from old plan Phase 16 verbatim, and add:

```
- [ ] user.plan field migrated in PostgreSQL
- [ ] Plan field present in JWT response (verified with /api/auth/me)
- [ ] FeatureGate tested with real pro and simple users in staging
- [ ] fal.ai spend limit set (Railway env: FAL_API_KEY + billing cap confirmed)
- [ ] Serper API key set in Railway secrets
- [ ] KDP spec verified against current KDP documentation before TextStudio export function ships
```

---

## Phase 17 — Illustration Pipeline (Future Placeholder)

⏳ **FUTURE — Not in current implementation scope.**

Do not implement. Add this section to the plan as an architecture reference for the next planning session.

**Architecture note:**
- Same I2T → Prompt Engineering path as cover pipeline
- I2T mode: `illustration` (scene composition vocabulary)
- Entity conditioning: character + location reference images via FLUX Kontext
- LoRA training required for per-book character consistency (Leonardo.ai Enterprise or Replicate)
- Output: `IllustrationConcept` DB record, per-chapter
- User journey: Reading Page shows illustrations inline with chapter text
- Trigger for planning session: when cover pipeline is live, stable, and has ≥10 real user covers generated

---

## Dependency Graph

```
Phase 7  ✅ (Bugs + Model + VB API + Cover Studio API)
    │
    ├──► Phase 8a (Analysis Engine Branch — Simple/Pro)
    │         │
    │         ├──► Phase 8b (I2T Analysis Service)
    │         │         │
    │         │         └──► Phase 9  (Prompt Engineering Service + FLUX + DALL-E)
    │         │                   │
    │         │         ┌─────────┘
    │         │         │
    │         └──► Phase 10 (SetupPage + WorkflowNav + FeatureGate) ◄── Phase 9 also needed
    │                   │
    │                   └──► Phase 11 (AnalysisReviewPage + CoverBriefEditor)
    │                              │
    │                              └──► Phase 12 (MoodBoardPage)
    │                                        │
    │                                        └──► Phase 13 (CoverStudio + TextStudio) ◄── Phase 9
    │                                                  │
    │                                                  └──► Phase 14 (E2E Tests)
    │                                                             │
    ├──► Phase 9b (Serper Provider) ──── any time after Phase 7   │
    │                                                             │
    └──► Phase 15 (Visual Identity) ─── any time after Phase 8a   │
                                                                   └──► Phase 16 (Deployment)
```

Phase 9b (Serper) can begin immediately after Phase 7 — no dependency on I2T or Prompt Engineering.
Phase 15 (Visual Identity) is fully independent — run on a separate branch after Phase 8a is stable.
Phase 9 must complete before Phase 13 (CoverStudio needs real T2I).
Phase 16 always runs last.

---

## Environment Variables Reference

```bash
# OpenAI (required for I2T + PromptEngineeringService)
OPENAI_API_KEY=

# fal.ai (required for FLUX Kontext primary T2I)
FAL_API_KEY=

# Provider selection (auto-detected — informational only)
COVER_T2I_PROVIDER=flux_kontext  # "flux_kontext" | "dalle"

# Serper (supplementary image search)
SERPER_API_KEY=

# Existing variables (carry forward from prior phases)
DATABASE_URL=
SECRET_KEY=
UNSPLASH_ACCESS_KEY=
BEHANCE_API_KEY=

# Spend monitoring (set before Phase 16 deployment)
# OpenAI and fal.ai spend alerts must be configured in their respective dashboards
```

---

*Document version: v3.0 — Supersedes Noctua_Implementation_Plan_Merged.md*
*Last updated: Session 3 planning output*
*Next session checkpoint: generate Noctua_Session3_Checkpoint.md after Phase 8a completes*
