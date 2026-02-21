# Development Roadmap 2.0: AI-Powered Book Illustration Platform
## "StoryForge AI - Cover Generation MVP → Full Illustration Platform"

**Version:** 2.0 (Strategic B2B Pivot)  
**Date:** February 12, 2026 (updated Feb 21, 2026: Visual Semantic Engine Steps 1–12 + Bugs/enhancements 7–14 implemented)  
**Development Approach:** Vibe-coding with Anthropic models via Cursor IDE  
**Strategic Focus:** Cover Generation MVP for rapid market validation  
**Target Market:** Self-publishing authors (B2B)

---

## 📊 Executive Summary

### Strategic Pivot: B2C → B2B
The original roadmap targeted **readers** (B2C) who wanted to read books with AI illustrations. Based on market research, we're pivoting to **self-publishing authors** (B2B) who need affordable illustration services for Amazon KDP publishing.

**Key Changes:**
- ❌ Reading interface (two-page spreads, page turns) → **Deferred to Phase 4**
- ✅ Cover generation (KDP-ready PDFs) → **New P0 feature**
- ✅ Direct manuscript upload → **Replaces Google Drive import**
- ✅ Leonardo AI integration → **Replaces generic image generation**
- ✅ KDP export (interior + cover PDFs) → **New core deliverable**

### MVP Strategy: Cover-First Validation
Rather than building the full illustration pipeline (125 images per book, 30+ minutes generation), we'll launch with **cover-only generation** to validate the market:

**Cover MVP Benefits:**
- ✅ Faster to market (2-3 weeks vs 6-8 weeks)
- ✅ Lower cost to test ($0.22/cover vs $2.50/book)
- ✅ Same workflow (upload → analysis → visual bible → generate)
- ✅ Validates core technology (AI analysis + Leonardo AI + ReportLab)
- ✅ Revenue generation ($10-20/cover or subscription)

**Success Metrics for MVP:**
- 50 authors generate covers
- 20+ covers used for KDP publishing
- 80%+ satisfaction with character consistency
- 70%+ satisfaction with cover quality
- 10+ paying customers ($200+ MRR)

**Then:** If validated, build full illustration pipeline (P1 roadmap)

---

## 🎯 Current Status Analysis (Feb 12, 2026; updated Feb 21, 2026)

### ✅ Completed Features (35% of B2B MVP)

**Visual Semantic Engine — Steps 1–12 (Feb 21, 2026):** Refactor per `visual pipeline refactoring_plan_v3.md` — **12 of 12 steps complete:**
- **Step 1 (DB Migration):** New tables `scenes`, `scene_characters`, `scene_locations`, `engine_ratings` created. New columns added to `characters` and `locations` (`ontology_json`, `entity_visual_tokens_json`), to `books` (`scene_count`, `known_adaptations_json`), to `illustrations` (`scene_id`, `prompt_used`). All migrations via `database._run_migrations()` — zero data loss, all new columns nullable.
- **Step 2 (CRUD Expansion):** Added `create_scene`, `get_scenes_by_book`, `get_scene`, `update_scene`, `delete_scenes_by_book`, `create_scene_character`, `create_scene_location`, `get_character_by_name`, `get_location_by_name`, `get_character`, `get_location`, `update_character_ontology`, `update_location_ontology`, `get_engine_ratings`, `update_engine_rating`. `clear_analysis_results()` extended to delete scenes on re-analysis.
- **Step 3 (Constants):** `app/services/ontology_constants.py` — 37-class `ENTITY_CLASSES` taxonomy, `ENTITY_PARENT` hierarchy (27 entries), `NON_HUMAN_CLASSES` set (30 classes).
- **Step 4 (Ontology Service):** `app/services/ontology_service.py` — `classify_entities_batch()` single batched LLM call; validates entity_class against closed enum; enforces `anti_human_override` logic; integrated into `run_full_analysis()` as step 2.5 (after consolidation); `ontology_json` persisted per entity. **9/9 unit tests passing.**
- **Step 5 (Entity Visual Token Builder):** `build_entity_visual_tokens_batch()` added to `ai_service.py` — single batched LLM call producing `{core_tokens, style_tokens, archetype_tokens, anti_tokens}` per entity; integrated as step 3 in `run_full_analysis()`; `entity_visual_tokens_json` saved to DB for each character/location. `_get_visual_tokens_for_entity()` in `search_service.py` updated: entity-level tokens take priority over chunk-based aggregation (chunk fallback unchanged). **14/14 unit tests passing.**
- **Step 6 (Scene Extractor):** `app/services/scene_extractor.py` — two-pass extraction: (A) deterministic sliding window (`group_chunks_into_candidate_scenes()`) scores windows by composite_score = dramatic×0.5 + density×0.3 + entities×0.2, applies non-maximum suppression; (B) `extract_scenes_llm()` single batched LLM call refining to exactly `scene_count` scenes with title, scene_type, chunk range, narrative_summary, visual_description, characters_present, primary_location, scene_prompt_draft. Entry point: `extract_scenes()`. Integrated as step 4 in `run_full_analysis()`; scenes + SceneCharacter + SceneLocation saved in `_run_analysis_background()`. **5/5 unit tests passing.**
- **Step 7 (Scene Visual Composer):** `app/services/scene_visual_composer.py` — `compose_scenes_batch()` single batched LLM call building `scene_visual_tokens` (core/style/composition/character/environment tokens) and `t2i_prompt_json` ({abstract, flux, sd}) per scene; enforces composition_tokens framing terms; respects `anti_human_override` for character_tokens; fallback helpers for LLM failures. Integrated as step 5 in `run_full_analysis()`; `scene_visual_tokens_json` and `t2i_prompt_json` saved to Scene in DB. **16/16 unit tests passing.**
- **Step 8 (T2I Provider Base):** `app/services/t2i_providers/` — `BaseT2IProvider` ABC with `T2IRequest` and `T2IResult` dataclasses; `AbstractProvider` (stub, no API, used for testing); `FluxProvider` skeleton (fal.ai / Replicate, checks `FAL_API_KEY` / `REPLICATE_API_KEY`); `SDProvider` skeleton (A1111 / ComfyUI, checks `SD_A1111_URL` / `SD_COMFYUI_URL`); `ALL_T2I_PROVIDERS` dict. `format_prompt()` extracts model-specific key from `t2i_prompt_json` with abstract fallback.
- **Step 9 (Search Provider Adapters):** `app/services/providers/` refactored to `BaseImageProvider` ABC with `is_available()`, `search()`, `format_query()`. Five new providers: **Pexels** (200 req/hour free, `PEXELS_API_KEY`), **Pixabay** (unlimited free, tags via `+`, `PIXABAY_API_KEY`), **Openverse** (free, no key, open-licensed), **Wikimedia Commons** (free, no key, historical/public domain), **DeviantArt** (via SerpAPI site filter, concept art/fantasy). `ALL_PROVIDERS` dict in `__init__.py`. **4/4 unit tests passing** (format_query logic verified without API calls).
- **Step 10 (Engine Selector + Query Diversification):** `app/services/engine_selector.py` — `ENGINE_AFFINITY` matrix (45+ entity×genre combinations), `select_engines()` with 4-tier fallback (exact match → parent class → generic style → hardcoded default) and engine ratings modifier (clamp [-5, +10]). `_build_queries_diversified()` in `search_service.py` — 4–6 semantically distinct queries per entity (ontology archetype, visual markers, canonical/analog, token combinations, adaptation queries for well-known books). Adaptation queries always forced to SerpAPI. `CONSOLIDATION_PROMPT` updated to extract `known_adaptations` for well-known books. `run_full_analysis()` accepts `is_well_known_book` parameter. **11/11 unit tests passing** (engine selector), **8/8 unit tests passing** (query diversification).

- **Step 11 (Schemas + Routers):** New Pydantic schemas `SceneResponse` (with JSON auto-deserialization and relationship-resolved `characters_present`/`primary_location`), `SceneUpdateRequest`, `EngineRatingUpdate`, `EngineRatingResponse`. New `app/routers/scenes.py` — GET, PATCH, POST generate-illustration (stub). Engine-ratings PATCH+GET added to `visual_bible.py` router. `proposed-search-queries` extended to include `scenes` array (selected only). All backwards-compatible (scene_count defaults to 10).
- **Step 12 (Frontend):** `api.ts` extended with Scene/EngineRating types and `getScenes()`, `updateScene()`, `rateEngine()` functions. `BookContext` + `StyleSelector` updated with `sceneCount` (3–20, default 10) passed to `analyzeBook()`. `AnalysisReviewPage` refactored to 3-tab layout (Characters | Locations | Scenes) with `SceneCard` — toggleable selection, editable prompt draft, persisted via PATCH. `ReviewSearchPage` (Search Queries step) extended with read-only Scenes section (SceneReviewCard: editable draft, read-only t2i abstract preview; no T2I model selector, no generate button). `VisualBibleReview` extended with ThumbsUp/ThumbsDown buttons under each thumbnail (grid + lightbox) calling `rateEngine()`.

**Bugs and enhancements 7–14 (Feb 21, 2026):** Implemented per plan `bugs_and_enhancements_7-13_a1abe484.plan.md`: (7) **Lightbox like/dislike feedback** — Review Search Result page fetches engine ratings on load; `VisualBibleReview` shows per-provider likes/dislikes counts and button labels "Good source (+1)" / "Poor source (+1)"; ratings refresh after each vote. (8) **Dashboard button** — WorkflowNav has a persistent "Dashboard" link to `/`. (9) **Key Parameters title** — StyleSelector heading changed from "Customize Your Experience" to "Key Parameters". (10) **Well-known book: Author + Title** — Backend `well_known_book_title` added to Book model and migration; StyleSelector shows two inputs (Author, Title of the book) when "This is a well-known published book" is checked; `book_info` in search_service uses `well_known_book_title` for query building. (11) **Similar book in Key Parameters** — "Is there another book like it?" moved from BookUpload to StyleSelector; `similar_book_title` persisted via analyze API and CRUD. (12) **manuscript-upload routes** — Routes and UI renamed from `create-book` to `manuscript-upload` (`/manuscript-upload`, `/books/:bookId/manuscript-upload`). (13) **Provider docs** — `.env.example` documents all provider keys (UNSPLASH_ACCESS_KEY, SERPAPI_KEY, PEXELS_API_KEY, PIXABAY_API_KEY; Openverse/Wikimedia no key). (14) **Settings page** — New route `/settings` and `SettingsPage`: Reference image search engines list from `GET /api/settings/providers` with checkboxes (default all available); selection persisted in localStorage (`yread_enabled_providers`); engine ratings section with book selector and table; POST search-references accepts optional `enabled_providers` and filters providers. Unit tests: `test_bugs_enhancements_7_13.py` (BookAnalyzeRequest, SearchReferencesRequest). Integration: `test_settings_and_analyze.py` (GET /api/settings/providers).

**Total: 58/58 unit tests passing** (plus 4 unit + 1 integration for bugs/enhancements) across test_engine_selector, test_query_diversification, test_provider_format_query, test_entity_token_builder, test_scene_extractor, test_scene_visual_composer. (8 test_ontology_service tests require live OPENAI_API_KEY — excluded from offline run.) **21/21 integration tests passing** in `tests/integration/test_scene_api.py` (Scene API + Engine Ratings contracts, no API key needed). **TypeScript: 0 errors.**

**Development workflow (Feb 19, 2026):** Plan *Clean DB → Start Analysis* implemented: script `backend/scripts/reset_db.py` for full database reset; database cleared and ready for fresh upload and analysis. See section *Development: Database reset and starting analysis* below.

**Workflow navigation (implemented):** Persistent stage navigation is in place: **WorkflowNav** component shows the six stages (Create Book, Analysis Review, Search Queries, **Search Results**, **Visual Bible**, Preview) on all workflow pages; **WorkflowLayout** wraps these routes and renders the nav bar above the current page. From the Home dashboard, users can open a book at any stage via the book card menu (⋯), in addition to opening in Preview by clicking the card.

**Reference search and review (implemented):** (1) **Style in query_text** — Each saved row in `search_queries` includes the book’s style (from Visual Bible style_category chosen on create-book) in `query_text`. (2) **Text-to-image prompt** — The Review Search page has three inputs per entity: AI summary, reference image search query lines, and an editable **text_to_image_prompt** (stored on Character/Location, for later T2I generation). (3) **Dual reference image providers** — Unsplash API (primary) and SerpAPI (fallback) are implemented; backend accepts optional **preferred_provider** (`unsplash` | `serpapi`) on POST search-references. (4) **User settings (HomePage)** — A Settings panel lets users choose AI analysis model, text-to-image model, and reference search provider (stored in localStorage); API keys are configured via backend `.env` (OPENAI_API_KEY, UNSPLASH_ACCESS_KEY, SEARCH_API_KEY / SERPAPI_KEY). (5) **Review Search page options** — On the Search Queries step the user can select the search engine for the run (Unsplash, SerpAPI, or Default from Settings) and whether to search **Characters only**, **Locations only**, or **Both**; `search_entity_types` is sent to POST search-references. (6) **Review Search Result refactor (Feb 2026):** The step where the user selects reference images is now the **Review Search Result** page (`/review-search-result`); the **Visual Bible** route (`/visual-bible`) is a separate stub for the next phase (AI generation and final visual bible). Search results are **persisted** in the `reference_images` table (append, FIFO cap 50 per entity); the user can select **multiple** references per entity ("Select for visual bible"); **GET reference-results** loads the pool; **POST reference-upload** allows uploading custom images per entity (source=user). The last chosen Search engine and Search for on the Review Search page are saved in localStorage per book and restored on reopen. (7) **Review Search UX consistency:** The "Search for" dropdown on the Review Search page only shows options that match the entities on the page (only characters selected on Analysis Review → "Characters only"; only locations → "Locations only"; both → all three). When only one type exists, that option is selected and persisted. After "Run reference search", the Review Search Result page opens on the Characters tab (if the user searched for characters or both) or the Locations tab (if they searched for locations only).

**Reusable from B2C Implementation:**

| Feature | Status | B2B Usefulness | Migration Effort |
|---------|--------|----------------|------------------|
| **Backend Foundation** | 100% | High | Low (minor updates) |
| - Database models | ✅ | Keep (add cover tables) | 2 hours |
| - Text chunking | ✅ | Keep (unchanged) | 0 hours |
| - AI analysis | ✅ | Keep (enhance with scene extraction) | 4 hours |
| - Reference search | ✅ | Keep (unchanged) | 0 hours |
| **Frontend Components** | 100% | Medium | Medium (rebrand) |
| - BookUpload | ✅ | Adapt for direct upload | 3 hours |
| - StyleSelector | ✅ | Keep (genre-specific) | 1 hour |
| - VisualBibleReview | ✅ | Keep (core workflow) | 2 hours |
| - LoadingScreen | ✅ | Keep (unchanged) | 0 hours |
| **State Management** | 100% | High | Low |
| - React Router | ✅ | Keep (update routes) | 1 hour |
| - BookContext | ✅ | Keep (rename variables) | 2 hours |
| **API Endpoints** | 100% | Medium | Medium |
| - Book import | ✅ | Replace with upload | 3 hours |
| - Analysis | ✅ | Enhance | 2 hours |
| - Visual bible | ✅ | Keep | 0 hours |

**Total Reusable Work:** ~30% of Cover MVP (saves 15-20 hours)

---

### ❌ Not Needed for B2B (Remove/Defer)

| B2C Feature | B2B Replacement | Action |
|-------------|-----------------|--------|
| Google Drive import | Direct file upload (.txt, .docx) | Replace in P0 |
| BookReader (two-page spread) | Simple preview (scrollable) | Defer to Phase 4 |
| Reading progress tracking | Not needed | Remove |
| Continue reading feature | Not needed | Remove |
| Page turn animations | Not needed | Remove |

**Effort Saved:** ~20 hours by not building reading interface

---

### 🚧 In Progress / Needs Update

| Feature | Current Status | Required for Cover MVP | Action |
|---------|---------------|----------------------|--------|
| Image Generation | 0% (not started) | Critical | Build with Leonardo AI (P0) |
| Integration & Polish | 50% (routing done) | Needed | Update branding, error handling (P0) |
| UI/UX Improvements | 33% (partial) | Needed | Complete for author workflow (P0) |

---

### 🆕 New Features Required for B2B

| Feature | Priority | Effort | Model |
|---------|----------|--------|-------|
| Direct file upload (.txt, .docx) | P0 | 4 hours | Haiku |
| Cover generation (ReportLab) | P0 | 8 hours | Sonnet |
| Leonardo AI integration | P0 | 6 hours | Sonnet |
| Cover-only workflow | P0 | 4 hours | Haiku |
| Simple preview mode | P0 | 3 hours | Haiku |
| KDP cover export | P0 | 3 hours | Haiku |
| Scene extraction (best practices) | P1 | 6 hours | Sonnet |
| Interior PDF generation | P1 | 12 hours | Sonnet |
| Full KDP export package | P1 | 4 hours | Haiku |

**Total New Work:** ~50 hours

---

## 🗺️ Development Roadmap

### Priority System

**P0 - Cover Generation MVP** (Weeks 1-3, ~50 hours)
- Core features needed to generate book covers
- Validates market demand
- Revenue generation capability

**P1 - Full Illustration Platform** (Weeks 4-8, ~60 hours)
- Complete interior illustration generation
- Full KDP publishing package
- Scales to full product

**P2 - Growth & Enhancement** (Months 3-6, ongoing)
- Batch processing
- Series support
- Premium features

**P3 - B2C Reading Platform** (Year 2, Phase 4)
- Two-sided marketplace
- Reading interface
- Social features

---

## 🎨 P0: Cover Generation MVP (Weeks 1-3)

**Goal:** Enable authors to generate professional book covers in <15 minutes  
**Success Metric:** 50 authors generate covers, 20+ publish on KDP, $200+ MRR  
**Timeline:** 3 weeks (50-60 hours)  
**Investment:** ~$100 Anthropic API + $48 Leonardo AI subscription

---

### Week 1: Foundation Migration & File Upload (16-20 hours)

#### Task 1.1: Project Rebranding & Setup (3 hours) - **Haiku**

**Objective:** Rebrand from "Reading Reinvented" to "StoryForge AI" (B2B positioning)

**Tasks:**
- Update project name, descriptions, metadata
- Change UI copy from reader to author perspective
- Update route names (/read → /preview, /setup → /create)
- Add author-focused messaging

**Cursor Prompt (Haiku):**
```
Rebrand this project for self-publishing authors:
- Change "Reading Reinvented" to "StoryForge AI"
- Update UI copy: "Read with illustrations" → "Create illustrated books for KDP"
- Update routes: /setup → /create-book, /reading → /preview
- Change BookContext to AuthorWorkflowContext
- Update homepage messaging to target authors, not readers
```

**Files to Update:**
- `frontend/index.html` (title)
- `frontend/src/App.jsx` (routing)
- `frontend/src/pages/*` (copy)
- `package.json` (project name)

**Model:** **Claude 3.5 Haiku** ($0.80/$4 per MTok)
- Simple find-replace, copy updates
- Estimated: 5,000 input tokens, 1,500 output tokens
- Cost: ~$0.01

**Validation:**
- [x] All UI references say "StoryForge AI"
- [x] Author-focused copy throughout
- [x] Routes updated correctly
- [x] Feature pills enhanced (4 items: Upload, AI Analysis, Custom illustrations, KDP-ready covers)
- [x] Frontend build successful with no errors

**Status: ✅ COMPLETED** (Feb 15, 2026)

---

#### Task 1.2: Database Schema Updates (2 hours) - **Haiku**

**Objective:** Add B2B-specific tables (covers, workflows, series support)

**Tasks:**
- Add `workflow_type` field to books table ('full' or 'cover_only')
- Create `covers` table
- Create `kdp_exports` table (for P1)
- Add `series` table structure (for P2)
- Remove `reading_progress` table

**Cursor Prompt (Haiku):**
```
Update database schema for B2B author workflow:

1. Add to books table:
   - workflow_type TEXT DEFAULT 'full' ('full' or 'cover_only')
   - is_well_known_book BOOLEAN DEFAULT FALSE
   - similar_book_title TEXT (for reference search optimization)

2. Create covers table:
   - id, book_id, front_visual_path, full_cover_path
   - template (genre), spine_width, customizations (JSON)
   - generated_at TIMESTAMP

3. Create kdp_exports table (for future):
   - id, book_id, trim_size, interior_pdf_path, cover_pdf_path
   - zip_file_path, exported_at, download_count

4. Remove reading_progress table (not needed for B2B)

Update models.py and create migration script.
```

**Files to Update:**
- `backend/app/models.py`
- `backend/app/database.py` (migration function)

**Model:** **Claude 3.5 Haiku**
- Simple schema updates
- Estimated: 4,000 input tokens, 1,200 output tokens
- Cost: ~$0.008

**Validation:**
- [x] New tables created successfully
- [x] Migration script runs without errors
- [x] Old data preserved

**Status: ✅ COMPLETED** (Feb 15, 2026)

---

#### Task 1.3: Direct File Upload (Replace Google Drive) (6 hours) - **Sonnet**

**Objective:** Replace Google Drive import with direct .txt/.docx/.pdf upload

**Tasks:**
- Create file upload endpoint (multipart/form-data)
- Support .txt, .docx, .pdf (text-extractable)
- Extract text from uploaded files
- Validate file size (max 20MB)
- Save manuscript and create book record

**Cursor Prompt (Sonnet):**
```
Create a robust file upload system for book manuscripts:

API Endpoint:
POST /api/manuscripts/upload (multipart/form-data)
- Accept files: .txt, .docx, .pdf
- Max size: 20MB
- Extract plain text from all formats
- Validate readable content (not scanned PDF images)

Implementation:
1. Use python-docx for .docx extraction
2. Use PyPDF2 for .pdf text extraction (fail gracefully if image-only)
3. Direct read for .txt
4. Save file temporarily during processing
5. Extract metadata: title (from filename or first line), word count, estimated pages
6. Create book record in database
7. Return book_id and metadata

Error Handling:
- Invalid file type → "Please upload .txt, .docx, or text PDF"
- File too large → "File exceeds 20MB limit"
- Scanned PDF → "PDF must contain extractable text, not images"
- Corrupted file → "Unable to read file. Please try again."

Include virus scan check (optional but good practice).
```

**Files to Create/Update:**
- `backend/app/services/upload_service.py` (new)
- `backend/app/main.py` (add endpoint)
- `frontend/src/components/BookUpload.jsx` (update UI)

**Model:** **Claude 3.5 Sonnet** ($3/$15 per MTok)
- Complex file handling, multiple formats
- Error handling logic
- Security considerations
- Estimated: 10,000 input tokens, 3,000 output tokens
- Cost: ~$0.075

**Validation:**
- [x] .txt files upload correctly
- [x] .docx files extract text properly
- [x] .pdf files work (text-based PDFs)
- [x] Error messages clear and helpful
- [x] File size validation works

**Status: ✅ COMPLETED** (Feb 15, 2026)

---

#### Task 1.4: Update BookUpload UI Component (4 hours) - **Haiku**

**Objective:** Replace Google Drive link input with drag-and-drop file upload

**Tasks:**
- Add drag-and-drop zone
- Show file preview (name, size, type)
- Add book metadata form (title, genre, page count estimate)
- Add "Is there another book like it?" field
- Show upload progress
- Display validation errors

**Cursor Prompt (Haiku):**
```
Update BookUpload.jsx for direct file upload:

Replace Google Drive link input with:
1. Drag-and-drop file zone (using react-dropzone)
   - Accept: .txt, .docx, .pdf
   - Max size: 20MB
   - Show upload progress
   
2. File preview card:
   - Filename
   - File size
   - File type icon
   - Remove button

3. Book metadata form (appears after file selected):
   - Title (pre-filled from filename)
   - Author name (required)
   - Genre dropdown (children's, fantasy, romance, thriller, etc.)
   - Page count (estimated from file size, editable)
   - "Is there another book like it?" toggle
     - If yes: Show "Similar book title" input field
   
4. Upload button (disabled until file + required fields filled)

Use Tailwind CSS for styling, match existing design system.
```

**Files to Update:**
- `frontend/src/components/BookUpload.jsx`

**Model:** **Claude 3.5 Haiku**
- UI component updates
- Form validation
- Estimated: 6,000 input tokens, 2,000 output tokens
- Cost: ~$0.012

**Validation:**
- [x] Drag-and-drop works smoothly
- [x] File validation prevents invalid types
- [x] Form pre-fills intelligently
- [x] Error states display correctly
- [x] Upload progress indicator implemented
- [x] Genre dropdown with comprehensive options
- [x] Similar book toggle field added

**Status: ✅ COMPLETED** (Feb 15, 2026)

---

#### Task 1.5: Enhanced AI Analysis with Scene Extraction (5 hours) - **Sonnet**

**Objective**

Transform the AI service from basic extraction into a scene intelligence engine that:
Identifies illustratable dramatic scenes
Scores them using multi-factor logic
Extracts structured VisualLayers
Generates VisualTokens for:
Reference image search using SerpApi or Unsplash API
Text-to-image models

**Tasks:**
Architecture Upgrade

Text Chunks
     ↓
LLM Analysis (Scene + Narrative + Emotional)
     ↓
Deterministic Post-Processing Layer
     ↓
Dramatic Scoring Engine
     ↓
Visual Layer Extraction
     ↓
Visual Token Builder
     ↓
Final JSON Output


**Cursor Prompt (Sonnet):**
```
🆕 ENHANCED OUTPUT SCHEMA

Update the GPT prompt to return:

{
  "characters": [...],
  "locations": [...],
  "chunk_analyses": [
    {
      "chunk_index": 0,
      "narrative_position": "opening_hook",
      "visual_moment": "Luna discovers the glowing door",
      "action_level": 0.6,
      "emotional_intensity": 0.7,
      "visual_richness": 0.8,
      "dramatic_score": 0.74,
      "characters_present": ["Luna"],
      "illustration_priority": "high",

      "visual_layers": {
        "subject": ["Luna"],
        "secondary": ["glowing door"],
        "environment": ["ancient stone corridor"],
        "materials": ["wet stone", "blue light"],
        "lighting": ["glowing", "volumetric beams"],
        "mood": ["mysterious", "tense"]
      },

      "visual_tokens": {
        "core_tokens": ["young woman explorer", "glowing portal", "ancient corridor"],
        "style_tokens": ["cinematic lighting", "dark fantasy"],
        "technical_tokens": ["35mm lens"]
      }
    }
  ]
}

🔧 REQUIRED CODE ENHANCEMENTS

Below is what must be added to ai_service.py.

1️⃣ Add Deterministic Scoring Engine

Add after imports:

ACTION_KEYWORDS = {
    "ran", "fought", "crashed", "discovered", "screamed",
    "exploded", "attacked", "collapsed", "revealed"
}

VISUAL_ADJECTIVES = {
    "glowing", "dark", "towering", "ancient",
    "bright", "massive", "shimmering", "shadowy"
}

INTERNAL_MONOLOGUE_MARKERS = {"thought", "wondered", "remembered"}

Dramatic Score Calculator
def calculate_dramatic_score(
    text: str,
    action_level: float,
    emotional_intensity: float,
    visual_richness: float,
) -> float:

    words = text.lower().split()

    action_bonus = sum(1 for w in words if w in ACTION_KEYWORDS) * 0.2
    visual_bonus = sum(1 for w in words if w in VISUAL_ADJECTIVES) * 0.15
    monologue_penalty = sum(1 for w in words if w in INTERNAL_MONOLOGUE_MARKERS) * 0.05

    score = (
        action_level * 0.4
        + emotional_intensity * 0.3
        + visual_richness * 0.3
        + action_bonus
        + visual_bonus
        - monologue_penalty
    )

    return max(0.0, min(score, 1.0))

2️⃣ Visual Density Assessment
def assess_visual_density(text: str) -> str:
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

3️⃣ Narrative Position Detection

Add helper:

def detect_narrative_position(chunk_index: int, total_chunks: int) -> str:
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

4️⃣ Character Presence Weighting
def calculate_character_priority(characters_present, main_characters):
    names = {c["name"] for c in main_characters if c.get("is_main")}
    if len(names.intersection(set(characters_present))) >= 2:
        return 1.0
    elif names.intersection(set(characters_present)):
        return 0.8
    return 0.5

5️⃣ Visual Layer Extraction (NEW)

Enhance GPT prompt to require:

For each chunk, extract visual_layers structured as:

{
  "subject": [],
  "secondary": [],
  "environment": [],
  "materials": [],
  "lighting": [],
  "mood": []
}

6️⃣ Visual Token Builder (NEW)

Add deterministic token builder:

def build_visual_tokens(visual_layers: dict) -> dict:
    core = []
    style = []
    technical = []

    core.extend(visual_layers.get("subject", []))
    core.extend(visual_layers.get("secondary", []))
    core.extend(visual_layers.get("environment", []))
    core.extend(visual_layers.get("materials", []))

    style.extend(visual_layers.get("lighting", []))
    style.extend(visual_layers.get("mood", []))

    style.append("cinematic lighting")
    technical.append("high detail")

    return {
        "core_tokens": core[:6],
        "style_tokens": style[:5],
        "technical_tokens": technical,
    }

7️⃣ Integrate into run_full_analysis()

After consolidation, iterate:

for chunk in consolidated["chunk_analyses"]:
    chunk["narrative_position"] = detect_narrative_position(
        chunk["chunk_index"], len(chunks)
    )

    density = assess_visual_density(
        next(c["text"] for c in chunks if c["chunk_index"] == chunk["chunk_index"])
    )
    chunk["visual_density"] = density

    chunk["dramatic_score"] = calculate_dramatic_score(
        text=...,
        action_level=chunk.get("action_level", 0.5),
        emotional_intensity=chunk.get("emotional_intensity", 0.5),
        visual_richness=chunk.get("visual_richness", 0.5),
    )

    if "visual_layers" in chunk:
        chunk["visual_tokens"] = build_visual_tokens(chunk["visual_layers"])

Validate: Test on 3 sample books, check 70%+ match with human-selected scenes.
```

**Files to Update:**
- `backend/app/services/ai_service.py`

**Model:** **Claude 3.5 Sonnet**
- Complex algorithmic logic
- Multi-factor scoring system
- Advanced prompt engineering
- Estimated: 12,000 input tokens, 4,000 output tokens
- Cost: ~$0.096

**Validation:**
- [x] Dramatic scores calculated for all chunks
- [x] Scores correlate with human judgment (test on sample)
- [x] Narrative positions detected correctly
- [x] Visual moments extracted accurately

**Status:** ✅ **COMPLETED**

**Implementation Summary:**
Added the following enhancements to `ai_service.py`:
1. **Scoring Constants**: ACTION_KEYWORDS, VISUAL_ADJECTIVES, INTERNAL_MONOLOGUE_MARKERS
2. **calculate_dramatic_score()**: Multi-factor scoring with keyword bonuses/penalties
3. **assess_visual_density()**: Classifies text as low/medium/high visual density
4. **detect_narrative_position()**: Maps chunk position to story structure (opening_hook, inciting_incident, rising_action, midpoint, climax, resolution)
5. **calculate_character_priority()**: Scores scenes based on main character presence
6. **build_visual_tokens()**: Extracts core_tokens, style_tokens, and technical_tokens from visual_layers
7. **Enhanced BATCH_ANALYSIS_PROMPT**: Now extracts action_level, emotional_intensity, visual_richness, visual_layers, and visual_moment
8. **Enhanced run_full_analysis()**: Post-processes all chunks with deterministic enhancements

C:\Users\dyv78\Desktop\DEV\YRead\TASK_1_5_IMPLEMENTATION.md


All tests passed successfully.

---
#### Task 1.6: Refactor and update the reference image search capability. 

**Objectives: make sure the referene image search capability which is already created, but not operational right now, is back alive. Update the reference image search capability to have a selection between SERPAPI and Unsplash API. 

**Feature: Reference Image Search v2 (MVP)**
*1. Overview*

Refactor existing search_service.py into a provider-based, book-aware, main-entity-optimized reference search system.
The new version must:
Use Unsplash as primary image provider
Use existing SerpAPI as fallback
Support main-only mode (default)
Integrate with AI_service-generated descriptions
Log all search queries
Return structured results for UI grid selection
Assign placeholders for non-main entities
Support well-known vs original book recognition

*2. Existing System Context*

Current file:
/mnt/data/search_service.py

Current capabilities:

SerpAPI async search
Query builders for characters and locations
Deduplication
DB logging via crud.create_search_query
Async httpx client
SQLAlchemy session support
Limitations:
No Unsplash integration
No main-only mode
No book recognition flag
No placeholder logic
No provider abstraction
No cost awareness
No structured entity result grouping

*3. Architectural Refactor*

3.1 Introduce Provider Abstraction

Create provider interface:

class ImageProvider(Protocol):
    async def search(self, query: str, entity_type: str, count: int = 3) -> list[dict]:
        ...


Implement:

UnsplashProvider

SerpApiProvider

Primary order:

Unsplash

SerpAPI (fallback only if insufficient results)

*4. Book Recognition Logic*

Add new input structure:

book_info = {
    "title": str,
    "author": str,
    "is_well_known": bool
}


If is_well_known == True:

Include book title and author in queries

If False:

Use descriptive search only

DO NOT include book title

*5. Query Construction (Replace Current Builders)*

Replace _build_character_queries and _build_location_queries with new queries build using the output of the AI_service {chunks_analysis}

Return max 3 queries.

*6. Provider Implementations*
6.1 UnsplashProvider (Primary)

Use async httpx (match existing architecture).

GET https://api.unsplash.com/search/photos


Headers:
Authorization: Client-ID {UNSPLASH_ACCESS_KEY}

Parameters:

query

per_page = count

orientation:

portrait if entity_type == "character"

landscape if entity_type == "location"

Return normalized format:

{
    "url": str,
    "thumbnail": str,
    "width": int,
    "height": int,
    "credit": str,
    "license": str,
    "provider": "unsplash"
}


License text:
"Unsplash License (free for commercial use)"

6.2 SerpApiProvider (Fallback)

Refactor existing _search_images_serpapi.

Normalize output to same schema as Unsplash:

{
    "url": original,
    "thumbnail": thumbnail,
    "width": width,
    "height": height,
    "credit": source,
    "license": "Verify license before use",
    "provider": "serpapi"
}

*7. Search Execution Flow*

New public API:

async def search_references_for_book(
    book_id: int,
    search_all: bool = False,
    db: Optional[Session] = None
) -> dict

7.1 Entity Fetch Logic

If search_all == False:

Fetch only is_main=True characters

Fetch only is_main=True locations

If True:

Fetch all

For non-main entities when search_all=False:

Assign placeholder

DO NOT call external APIs

*8. Entity-Level Search Logic*

For each entity:

Build queries

For each query:

Try Unsplash

If results < 2 → fallback to SerpAPI

Aggregate

Deduplicate

Filter min size 512

Limit to 3

Log every query via _save_query

*9. Placeholder Logic*

Add function:

def assign_placeholder(entity_id: int, entity_type: str)


Store default placeholder image in DB:

Character placeholder:
/static/placeholders/character.png

Location placeholder:
/static/placeholders/location.png

*10. Response Structure*

Return structured grouped result:

{
    "book_id": int,
    "mode": "main_only" | "all",
    "characters": [
        {
            "id": int,
            "name": str,
            "is_main": bool,
            "images": [ ... up to 3 ... ],
            "placeholder_assigned": bool
        }
    ],
    "locations": [
        {
            "id": int,
            "name": str,
            "is_main": bool,
            "images": [...],
            "placeholder_assigned": bool
        }
    ],
    "queries_run": int,
    "provider_usage": {
        "unsplash": int,
        "serpapi": int
    }
}

*11. Logging Requirements*

Each query must log:

book_id

entity_type

entity_name

query_text

result_count

provider_used

timestamp

Extend search_queries table:

Add column:

provider TEXT

*12. Deduplication Strategy*

Keep domain-based dedupe from existing _filter_and_dedupe.

Enhance:

Deduplicate by identical URL

Prefer Unsplash results over SerpAPI when duplicate domain

*13. Quota Optimization Rules*

Default mode = main_only

Stop querying after 3 good images found

Do not run fallback if Unsplash returns >= 3 valid images

Cap total queries per entity = 3

*14. UI Contract*

Front-end expects:

Grid display of 3 images per entity

Ability to mark 1 primary

Optional toggle for “Search all entities”

Query history endpoint:

GET /api/books/{book_id}/search-queries

*15. Integration with AI_service*

AI_service provides:

For characters:

name

physical_description

is_main

For locations:

name

visual_description

is_main

This feature must consume those fields directly.

No LLM calls in this service.

*16. Backwards Compatibility*

Remove:
search_all_references(characters, locations…)
Replace with:
search_references_for_book(book_id, search_all=False)

*17. Error Handling*

If Unsplash key missing → log warning → skip provider

If SerpAPI key missing → fallback unavailable

Service must never raise unhandled exceptions

Always return structured result

*18. Future Phase Hooks (Do NOT implement now)*

Caching results in Redis

Image scoring via CLIP similarity

Image style consistency scoring

VisualTokens extraction alignment

*19. Expected File Structure*

Refactor into:

search_service.py
providers/
    unsplash_provider.py
    serpapi_provider.py

*20. Claude Instruction Summary*

Claude must:
Refactor existing async code
Preserve SQLAlchemy integration
Introduce provider abstraction
Add Unsplash as primary
Implement main-only logic
Implement book recognition logic
Extend DB logging
Maintain async architecture
Return structured result format
Ensure deduplication and filtering
No synchronous requests
No blocking code

C:\Users\dyv78\.cursor\plans\task_1.6_reference_image_search_v2_eb9050e0.plan.md

**Status:** ✅ **COMPLETED** (Feb 15, 2026)

**Implementation Summary:**
- Provider architecture: `providers/base.py`, `unsplash_provider.py`, `serpapi_provider.py` — Unsplash primary, SerpAPI fallback (< 2 results)
- DB: `search_queries.provider`, `chunks.visual_analysis_json`; CRUD: `update_chunk_visual_analysis`, `create_search_query(provider)`
- `search_references_for_book(book_id, search_all)` — queries from `visual_tokens` (chunk_analyses) or description fallback; main-only mode; `assign_placeholder` for non-main
- Placeholders: `/static/placeholders/character.svg`, `location.svg`
- visual_bible router: no auto-select; response `{characters, locations, queries_run, provider_usage}`; compatible with VisualBibleReview
- Books router: saves `visual_layers`/`visual_tokens` to chunks during analyze

**Visual Bible Search & UI Improvements (Feb 2026):**
- **Search query formation:** `query_text` in `search_query` table now uses **only visual references** (no character/location name). Queries are built from `core_tokens` + `style_tokens` from chunk analyses, or description + suffix (" portrait" / " landscape"); for well-known books, second query is title + author + "illustration" only. This avoids over-narrowing and returns more images.
- **Image count:** Up to **10 images per entity** (was 3). Providers called with `count=15`; `_filter_and_dedupe(..., max_results=10)` applied. Same for characters and locations.
- **Visual Bible UI (`VisualBibleReview.tsx`):**
  - Reference images shown in a **grid** (e.g. 2–5 columns by breakpoint) to display up to 10 thumbnails per character/location.
  - **Lightbox:** Clicking a thumbnail opens a modal with full-size image. User can choose **"Use for AI"** to set that image as the primary reference for generation, or **"Close"** to cancel. Selected image is highlighted on the card (checkmark).

**Smart visual query algorithm and review step (Feb 2026)** — see plan `smart_visual_query_algorithm_and_review_a478f0a7.plan.md`:
- **Character type (visual_type):** DB fields on `Character`: `visual_type` (man/woman/animal/AI/alien/creature), `is_well_known_entity`, `canonical_search_name`, `search_visual_analog`. Same (except no visual_type) on `Location`. AI consolidation prompt extended to output these; books router persists them.
- **Query building:** `search_service._build_queries()` uses `_character_suffix(visual_type)` for character query suffix; for well-known entities adds a query from `canonical_search_name`; for fictional entities uses `search_visual_analog` or aggregated visual tokens. Well-known-book query uses "character" in query for characters to bias results toward people.
- **Proposed queries API:** `GET /books/{book_id}/proposed-search-queries` returns characters and locations with summary and `proposed_queries` (array of query strings) for the review UI.
- **Entity summaries update:** `PATCH /books/{book_id}/entity-summaries` accepts edited summaries and search-related fields (physical_description, visual_description, visual_type, is_well_known_entity, canonical_search_name, search_visual_analog).
- **Search with overrides:** `POST .../search-references` body may include `character_queries`, `location_queries`, `character_summaries`, `location_summaries`; when provided, backend uses them instead of building queries for those entities.
- **Frontend:** Analysis Review → "Prepare reference search" → **Review Search** page (`/review-search`) where user can edit summary and proposed query lines per entity, then "Run reference search" (saves entity-summaries and calls search-references with the edited queries).

---

### Week 2: Leonardo AI Integration & Cover Generation (18-22 hours)

#### Task 2.1: Leonardo AI SDK Integration (6 hours) - **Sonnet**

**Objective:** Integrate Leonardo AI for character-consistent image generation

**Tasks:**
- Install Leonardo AI Python SDK
- Create Leonardo service wrapper
- Implement character reference feature
- Handle generation polling
- Implement retry logic and error handling

**Cursor Prompt (Sonnet):**
```
Create a Leonardo AI integration service for book cover and illustration generation:

Setup:
- Install: pip install leonardo-ai-sdk
- API key from environment variable
- Use Maestro plan ($48/mo, 25,000 tokens)

Service Implementation:

1. LeonardoService class with methods:
   - generate_image(prompt, character_reference, style, dimensions)
   - wait_for_generation(job_id, timeout=60)
   - download_image(url, save_path)

2. generate_image() should:
   - Call leonardo.generate_image() with:
     * prompt (scene description)
     * character_reference_image (URL from visual bible)
     * model="leonardo-vision-xl"
     * width, height (1024x1536 for covers)
     * num_images=1
   - Return generation job_id

3. wait_for_generation() should:
   - Poll every 3 seconds
   - Check status: PENDING → PROCESSING → COMPLETE
   - Handle FAILED status with error details
   - Timeout after 60 seconds
   - Return image URL when complete

4. Error Handling:
   - API rate limits → Exponential backoff
   - Invalid reference image → Clear error message
   - Generation timeout → Retry once, then fail gracefully
   - Quota exceeded → Alert user

5. Cost Tracking:
   - Log tokens used per generation (8 tokens per 1024x1536 image)
   - Track monthly quota usage
   - Alert when approaching limit

Return image URL and save to local storage.
```

**Files to Create:**
- `backend/app/services/leonardo_service.py`
- Update `backend/requirements.txt` with leonardo-ai-sdk

**Model:** **Claude 3.5 Sonnet**
- External API integration
- Async operations (polling)
- Complex error handling
- Estimated: 14,000 input tokens, 4,500 output tokens
- Cost: ~$0.110

**Validation:**
- [ ] Test image generation with reference image
- [ ] Character consistency visible across multiple generations
- [ ] Polling works correctly (no hanging)
- [ ] Error handling graceful
- [ ] Cost tracking accurate

---

#### Task 2.2: Cover Visual Generation (4 hours) - **Sonnet**

**Objective:** Generate front cover visual using main character or location

**Tasks:**
- Extract main character/location from visual bible
- Build cover-specific prompt
- Generate multiple variations (3-5 options)
- User selection interface
- Save selected visual

**Cursor Prompt (Sonnet):**
```
Create cover visual generation service:

Input:
- Visual bible (contains main character/location with reference image)
- Book metadata (title, genre, tone)

Process:
1. Identify primary visual element:
   - Prefer main character over location
   - If both exist, use character in setting

2. Build cover-optimized prompt:
   "Book cover illustration for '{title}'. 
   Centered {character description}. 
   Setting: {location description}.
   Style: {genre}-appropriate, professional book cover quality.
   Eye-catching, marketable, {tone} atmosphere.
   No text or titles in image."

3. Generate 3 variations:
   - Same prompt, different random seeds
   - All portrait orientation (1024x1536)
   - Save all options

4. Present to user:
   - Grid layout with 3 options
   - Radio button selection
   - Preview at cover size
   
5. Save selection:
   - Update covers table with front_visual_path
   - Delete unused variations

API Endpoint:
POST /api/books/{book_id}/cover/generate-visual
Response: {
  "variations": [
    {"id": 1, "url": "...", "thumbnail": "..."},
    {"id": 2, "url": "...", "thumbnail": "..."},
    {"id": 3, "url": "...", "thumbnail": "..."}
  ]
}

PUT /api/books/{book_id}/cover/select-visual
Body: {"variation_id": 2}
```

**Files to Create/Update:**
- `backend/app/services/cover_service.py` (new)
- `backend/app/main.py` (add endpoints)
- `frontend/src/components/CoverVisualSelector.jsx` (new)

**Model:** **Claude 3.5 Sonnet**
- Business logic for cover generation
- Multi-variation handling
- Prompt engineering for covers
- Estimated: 11,000 input tokens, 3,500 output tokens
- Cost: ~$0.086

**Validation:**
- [ ] 3 variations generated successfully
- [ ] Variations are distinct but thematically consistent
- [ ] User can select and save preference
- [ ] Selected visual saved correctly

---

#### Task 2.3: Cover PDF Generation with ReportLab (8 hours) - **Sonnet**

**Objective:** Generate KDP-ready cover PDF (front, back, spine)

**Tasks:**
- Calculate spine width from page count
- Create front cover with title, author, visual
- Create back cover with description, barcode placeholder
- Render spine with title and author
- Export as single PDF with proper dimensions and bleed

**Cursor Prompt (Sonnet):**
```
Create KDP-ready cover PDF generator using ReportLab:

Inputs:
- Book metadata (title, author, description, page count)
- Cover visual (front cover image)
- Trim size (default: 8.5" x 8.5" for children's books)
- Paper type (white or cream)

Implementation:

1. Spine Width Calculation:
   def calculate_spine_width(page_count, paper_type='white'):
       ppi = 0.0025 if paper_type == 'white' else 0.00252
       page_count = page_count + 1 if page_count % 2 else page_count  # Even pages
       spine_width = max(page_count * ppi, 0.06)  # KDP minimum 0.06"
       return spine_width

2. Cover Dimensions:
   - Trim width/height in inches
   - Bleed: 0.125" on all edges
   - Total width: (2 × trim_width) + spine_width + (2 × bleed)
   - Total height: trim_height + (2 × bleed)

3. Layout Sections:
   
   BACK COVER (left):
   - Background: Light gray or white
   - Book description (top half, 12pt font)
   - Barcode placeholder (bottom right, 2" x 1.2")
   - Author bio (optional, small text)
   
   SPINE (middle):
   - Background: Dark color or extracted from cover visual
   - Title + Author (rotated 90°, centered)
   - Font size auto-adjusted based on spine width:
     * >0.5" → 14pt
     * 0.3-0.5" → 12pt
     * <0.3" → 10pt
   
   FRONT COVER (right):
   - Cover visual (full bleed)
   - Title overlay (top, large bold font, white with shadow)
   - Author name (bottom, medium font, white with shadow)
   - Optional: Genre badge/icon

4. Genre-Specific Templates:
   CHILDREN_CARTOON:
     - Title: Comic Sans Bold, bright colors
     - Playful border
   FANTASY_EPIC:
     - Title: Serif bold, gold/metallic
     - Mystical effects
   ROMANCE:
     - Title: Script/Elegant, soft colors
     - Decorative flourishes

5. Output:
   - Save as cover.pdf
   - Embedded fonts (no external dependencies)
   - 300 DPI for print quality
   - Color space: CMYK for professional printing

API Endpoint:
POST /api/books/{book_id}/cover/generate-pdf
Body: {
  "trim_size": "8.5x8.5",
  "paper_type": "white",
  "template": "children_cartoon",
  "customizations": {
    "title_color": "#FFFFFF",
    "spine_color": "#333333"
  }
}

Response: {
  "cover_pdf_url": "/api/covers/123/cover.pdf",
  "spine_width": 0.25
}
```

**Files to Create:**
- `backend/app/services/cover_pdf_service.py` (new)
- Update `backend/requirements.txt` with reportlab

**Model:** **Claude 3.5 Sonnet**
- Complex PDF generation logic
- Mathematical calculations (spine, dimensions)
- Multi-section layout
- Typography and design rules
- Estimated: 16,000 input tokens, 5,000 output tokens
- Cost: ~$0.123

**Validation:**
- [ ] Spine width calculated correctly
- [ ] Cover renders with all elements
- [ ] PDF dimensions match KDP requirements
- [ ] Text readable and positioned correctly
- [ ] Upload to KDP succeeds

---

#### Task 2.4: Cover Customization UI (4 hours) - **Haiku**

**Objective:** Let authors customize cover colors, fonts, layout

**Tasks:**
- Create customization interface
- Color picker for title, spine, background
- Font selection dropdown
- Template selection (genre-based)
- Live preview updates
- Save customizations

**Cursor Prompt (Haiku):**
```
Create CoverCustomization.jsx component:

UI Layout:
1. Left Panel: Cover Preview
   - Show cover PDF preview (front, spine, back)
   - Update live as user changes settings
   - Zoom controls

2. Right Panel: Customization Options
   
   TEMPLATE:
   - Dropdown: Children's Cartoon, Fantasy Epic, Romance, Thriller, etc.
   - Each template has predefined color schemes
   
   COLORS:
   - Title Color (color picker)
   - Spine Color (color picker)
   - Background Color (back cover)
   
   TEXT:
   - Title Override (optional, defaults to book title)
   - Subtitle (optional)
   - Author Name Override (optional)
   
   LAYOUT:
   - Title Position: Top, Center, Bottom
   - Visual Size: Full Bleed, Inset
   
3. Action Buttons:
   - Reset to Template Defaults
   - Preview Changes
   - Save and Continue

State Management:
- Use React state for customizations
- Debounce preview updates (500ms)
- Save to backend on "Save and Continue"

API:
PUT /api/books/{book_id}/cover/customizations
Body: { customizations: {...} }
```

**Files to Create:**
- `frontend/src/components/CoverCustomization.jsx`

**Model:** **Claude 3.5 Haiku**
- UI component with forms
- State management
- Estimated: 7,000 input tokens, 2,500 output tokens
- Cost: ~$0.016

**Validation:**
- [ ] Color changes reflect in preview
- [ ] Template switching works
- [ ] Customizations save correctly
- [ ] Reset button restores defaults

---

### Week 3: Preview, Export & MVP Polish (16-18 hours)

#### Task 3.1: Simple Preview Mode (3 hours) - **Haiku**

**Objective:** Replace complex reading interface with simple scrollable preview

**Tasks:**
- Create simplified preview component
- Show cover + sample pages
- No page turns, just scroll
- Download preview PDF button

**Cursor Prompt (Haiku):**
```
Create SimpleBookPreview.jsx component:

Replace BookReader.jsx with simpler preview for authors:

Layout:
1. Cover Preview:
   - Show generated cover (front, spine visible)
   - Full width display
   
2. Sample Pages Preview:
   - Scrollable view (not two-page spread)
   - Show page 1 (always has illustration)
   - Show 2-3 more sample pages with text
   - Note: "Preview mode - full book will have illustrations every 4 pages"
   
3. Controls:
   - Download Preview PDF (low-res, watermarked)
   - Back to Edit
   - Generate Final Cover (if satisfied)
   
No animations, page turns, or reading progress.
Keep it simple and fast.

API Endpoints:
GET /api/books/{book_id}/preview-cover-image
GET /api/books/{book_id}/preview-pdf (watermarked, cover only)
```

**Files to Create/Update:**
- `frontend/src/components/SimpleBookPreview.jsx`
- Replace `BookReader.jsx` usage in routes

**Model:** **Claude 3.5 Haiku**
- Simple UI component
- Estimated: 5,000 input tokens, 1,800 output tokens
- Cost: ~$0.011

**Validation:**
- [ ] Cover displays correctly
- [ ] Preview is clear and professional
- [ ] Download button works
- [ ] Navigation intuitive

---

#### Task 3.2: Cover Export & Download (3 hours) - **Haiku**

**Objective:** Package cover PDF for download with upload instructions

**Tasks:**
- Create download endpoint
- Generate cover.pdf
- Create upload instructions PDF
- Package as ZIP (optional) or direct download
- Track download count

**Cursor Prompt (Haiku):**
```
Create cover export and download system:

1. Export Endpoint:
POST /api/books/{book_id}/export-cover
- Generate final cover.pdf (no watermark)
- Create upload_instructions.pdf with KDP steps
- Save export record in database
- Return download URLs

2. Upload Instructions PDF:
Create simple 1-page PDF with:
- Title: "How to Upload Your Cover to Amazon KDP"
- Steps:
  1. Go to kdp.amazon.com
  2. Create new paperback or upload to existing book
  3. In "Cover" section, select "Upload a cover you already have"
  4. Upload this cover.pdf file
  5. KDP will validate dimensions and bleed
  6. Preview and publish
- Your book details (title, spine width, trim size)

3. Download Tracking:
- Increment download_count in kdp_exports table
- Log timestamp

4. Frontend Download Button:
- "Download Cover Package"
- Shows: "Includes cover.pdf + upload instructions"
- One-click download

API:
GET /api/downloads/{book_id}/cover.pdf
GET /api/downloads/{book_id}/instructions.pdf
```

**Files to Create/Update:**
- `backend/app/services/export_service.py` (new)
- `frontend/src/components/DownloadCover.jsx` (new)

**Model:** **Claude 3.5 Haiku**
- File generation and download logic
- Estimated: 4,500 input tokens, 1,500 output tokens
- Cost: ~$0.010

**Validation:**
- [ ] Cover downloads correctly
- [ ] Instructions PDF clear and helpful
- [ ] Download count increments
- [ ] Files not corrupted

---

#### Task 3.3: Cover-Only Workflow Implementation (4 hours) - **Haiku**

**Objective:** Add option to generate cover without full manuscript analysis

**Tasks:**
- Add "Cover Only" mode selection
- Minimal analysis (extract 1-2 main entities)
- Skip interior illustration setup
- Direct to cover generation

**Cursor Prompt (Haiku):**
```
Implement cover-only workflow for authors who just need a cover:

Entry Point:
- BookUpload.jsx: Add toggle "What do you need?"
  ○ Full illustrated book
  ○ Cover only (faster, cheaper)

Cover-Only Path:
1. File upload (same as before) OR manual entry
2. Book metadata form (title, author, genre, page count)
3. Main character/location description:
   - If uploaded manuscript: Extract 1 main character from AI analysis
   - If manual: Text field "Describe your main character" (200 char limit)
4. Reference image selection (1 image only)
5. Generate cover visual
6. Customize cover
7. Download

API Endpoint:
POST /api/books/cover-only
Body: {
  "title": "...",
  "author_name": "...",
  "page_count": 100,
  "genre": "children_fantasy",
  "main_character_description": "8-year-old girl with silver hair",
  "paper_type": "white",
  "trim_size": "8.5x8.5"
}

Response: {
  "book_id": 123,
  "workflow": "cover_only",
  "next_step": "/cover-visual-selection"
}

Frontend: Update routing to handle cover_only workflow
Backend: Minimal AI analysis (1 entity extraction instead of full analysis)
```

**Files to Update:**
- `frontend/src/components/BookUpload.jsx` (add toggle)
- `backend/app/services/book_service.py` (add cover_only mode)
- `backend/app/main.py` (add cover-only endpoint)

**Model:** **Claude 3.5 Haiku**
- Workflow logic, conditional routing
- Estimated: 6,000 input tokens, 2,000 output tokens
- Cost: ~$0.013

**Validation:**
- [ ] Cover-only mode skips unnecessary steps
- [ ] Manual character description works
- [ ] Faster workflow (< 10 minutes total)
- [ ] Cost reduced ($0.22 vs $2.50)

---

#### Task 3.4: Error Handling & User Feedback (2 hours) - **Haiku**

**Objective:** Improve error messages and loading states

**Tasks:**
- Add error boundaries in React
- User-friendly error messages
- Loading states with progress
- Toast notifications for success/error
- Retry mechanisms

**Cursor Prompt (Haiku):**
```
Improve error handling and user feedback across the app:

1. React Error Boundary:
   - Catch component errors
   - Show friendly "Something went wrong" page
   - Log error to console (future: send to monitoring)

2. API Error Handling:
   - Network errors: "Unable to connect. Check your internet."
   - 400 errors: Show specific validation messages
   - 500 errors: "Server error. Please try again."
   - Timeout errors: "Request took too long. Retrying..."

3. Loading States:
   - File upload: Progress bar with percentage
   - AI analysis: "Analyzing your book... (Step 1 of 3)"
   - Image generation: "Generating cover visual... (~30 seconds)"
   - PDF generation: "Creating your cover PDF..."

4. Success Notifications:
   - Toast messages for successful operations
   - "Cover generated successfully!"
   - "Download ready!"

5. Retry Mechanisms:
   - Failed image generation → "Retry" button
   - Failed analysis → "Re-analyze" button
   - Show retry count (max 3 attempts)

Use react-hot-toast for notifications.
```

**Files to Update:**
- `frontend/src/App.jsx` (error boundary)
- `frontend/src/services/api.js` (error handling)
- All components (loading states)

**Model:** **Claude 3.5 Haiku**
- UI/UX improvements
- Estimated: 5,500 input tokens, 2,000 output tokens
- Cost: ~$0.012

**Validation:**
- [ ] Errors display helpful messages
- [ ] Loading states clear and informative
- [ ] Retry buttons work correctly
- [ ] User never confused about what's happening

---

#### Task 3.5: Author Dashboard (4 hours) - **Haiku**

**Objective:** Simple dashboard to manage multiple book covers

**Tasks:**
- List all user's books
- Show status (analyzing, ready, exported)
- Create new book button
- View/edit existing books
- Delete books

**Cursor Prompt (Haiku):**
```
Create AuthorDashboard.jsx component:

Layout:
1. Header:
   - "My Book Covers"
   - "Create New Cover" button (prominent)
   
2. Books Grid:
   - Card for each book:
     * Cover thumbnail (if generated)
     * Book title
     * Status badge: "Draft", "Cover Ready", "Exported"
     * Last updated timestamp
     * Actions: View, Edit, Delete
   
3. Empty State:
   - "No covers yet!"
   - "Create your first book cover to get started"
   - Large "Create New Cover" button

4. Filters (optional):
   - All, Draft, Ready, Exported
   - Sort by: Newest, Oldest, Title

API Endpoints:
GET /api/books (list all books for user)
DELETE /api/books/{book_id}

Route: Make this the homepage after login
```

**Files to Create:**
- `frontend/src/components/AuthorDashboard.jsx`
- Update routes to make this homepage

**Model:** **Claude 3.5 Haiku**
- CRUD UI component
- Estimated: 6,000 input tokens, 2,200 output tokens
- Cost: ~$0.013

**Validation:**
- [ ] All books display correctly
- [ ] Create button navigates to upload
- [ ] Edit/delete work correctly
- [ ] Status badges accurate

---

#### Task 3.6: Branding & UI Polish (2 hours) - **Haiku**

**Objective:** Professional branding and consistent design

**Tasks:**
- Create logo placeholder
- Consistent color scheme
- Typography refinement
- Landing page updates
- Footer with links

**Cursor Prompt (Haiku):**
```
Polish the UI for professional author-facing platform:

1. Color Scheme (B2B SaaS style):
   - Primary: Deep blue (#1E40AF)
   - Secondary: Warm orange (#F97316) 
   - Success: Green (#10B981)
   - Background: Light gray (#F9FAFB)
   - Text: Dark gray (#1F2937)

2. Typography:
   - Headings: Inter, bold
   - Body: Inter, regular
   - Monospace (code): Fira Code

3. Logo:
   - Text logo: "StoryForge AI"
   - Icon: Book with sparkles/AI symbol
   - Placeholder SVG for now

4. Landing Page Updates:
   - Hero: "Create Professional Book Covers in Minutes"
   - Value props: "Save $500 on cover design", "KDP-ready PDFs", "Character consistency"
   - CTA: "Create Your First Cover Free"

5. Footer:
   - Links: About, Pricing, Help, Contact
   - Social: Twitter, Email
   - Copyright notice

Apply consistently across all pages.
Update Tailwind config with custom colors.
```

**Files to Update:**
- `frontend/tailwind.config.js` (color scheme)
- `frontend/src/pages/HomePage.jsx` (landing page)
- `frontend/src/components/Header.jsx` (logo, nav)
- `frontend/src/components/Footer.jsx` (new)

**Model:** **Claude 3.5 Haiku**
- UI styling and branding
- Estimated: 4,000 input tokens, 1,500 output tokens
- Cost: ~$0.009

**Validation:**
- [ ] Consistent colors throughout
- [ ] Typography readable and professional
- [ ] Landing page compelling
- [ ] Brand identity clear

---

## 📊 P0 Cost Summary

### Development Costs (Cover MVP)

| Task Category | Hours | Model | Estimated Cost |
|---------------|-------|-------|----------------|
| **Week 1: Foundation** | 20 | 60% Haiku, 40% Sonnet | $30 |
| - Rebranding | 3 | Haiku | $3 |
| - Schema updates | 2 | Haiku | $2 |
| - File upload | 6 | Sonnet | $8 |
| - Upload UI | 4 | Haiku | $4 |
| - Enhanced analysis | 5 | Sonnet | $8 |
| **Week 2: Leonardo & Cover** | 22 | 70% Sonnet, 30% Haiku | $50 |
| - Leonardo integration | 6 | Sonnet | $12 |
| - Cover visual generation | 4 | Sonnet | $8 |
| - PDF generation | 8 | Sonnet | $18 |
| - Customization UI | 4 | Haiku | $4 |
| **Week 3: Polish & Export** | 18 | 70% Haiku, 30% Sonnet | $20 |
| - Preview mode | 3 | Haiku | $3 |
| - Export system | 3 | Haiku | $3 |
| - Cover-only workflow | 4 | Haiku | $4 |
| - Error handling | 2 | Haiku | $2 |
| - Dashboard | 4 | Haiku | $4 |
| - Branding polish | 2 | Haiku | $2 |
| **TOTAL** | **60 hours** | | **$100** |

**Additional Costs:**
- Cursor Pro: $20/month
- Leonardo AI Maestro: $48/month (test with 50 covers)
- OpenAI API: $25 (testing 50 books)
- **Total MVP Investment: ~$193**

### Per-Cover Operational Cost

| Item | Cost | Notes |
|------|------|-------|
| AI analysis (minimal) | $0.10 | Just main character extraction |
| Leonardo AI (cover visual) | $0.12 | 8 tokens × $0.015 |
| PDF generation | $0.00 | ReportLab (local) |
| **Total** | **$0.22** | 91% cheaper than full book ($2.50) |

---

## 🎯 MVP Success Metrics

### Technical Validation (Week 3)
- [ ] Cover generated in <15 minutes (target: 10 minutes)
- [ ] PDF passes KDP validation 100% of time
- [ ] Character consistency ≥85% (visual inspection)
- [ ] System handles 10 concurrent users
- [ ] Error rate <5%

### Market Validation (Months 1-2)
- [ ] 50 authors create covers
- [ ] 20+ covers used for actual KDP publishing
- [ ] 80%+ satisfaction (survey)
- [ ] 70%+ would recommend
- [ ] 10+ paying customers ($200+ MRR)

### Go/No-Go Decision
After 50 covers generated:
- **GO** (build P1 full illustrations): If ≥40 authors satisfied + ≥10 paid
- **NO-GO** (pivot/stop): If <30 authors satisfied or $0 revenue

---

## 🚀 P1: Full Illustration Platform (Weeks 4-8, if MVP validates)

**Objective:** Build complete illustrated book generation with KDP export

**Only proceed if Cover MVP shows:**
- Strong demand (≥40/50 satisfied)
- Revenue potential (≥$200 MRR)
- Technical validation (PDFs work on KDP)

---

### P1 Feature List (Priority Order)

| Feature | Effort | Model | Purpose |
|---------|--------|-------|---------|
| **Smart Illustration Placement** | 6h | Sonnet | Dramatic scene detection |
| **Batch Illustration Generation** | 8h | Sonnet | Generate 125 images/book |
| **Progressive Loading** | 4h | Haiku | Generate first 5, queue rest |
| **Interior PDF Generation** | 12h | Sonnet | ReportLab with bleed/margins |
| **Full KDP Export Package** | 4h | Haiku | interior.pdf + cover.pdf + instructions |
| **Illustration Regeneration** | 3h | Haiku | Retry failed/unsatisfactory images |
| **Series Character Library** | 6h | Sonnet | Reuse characters across books |
| **Genre Templates** | 4h | Haiku | 10+ genre-specific styles |
| **Author Review/Approval** | 5h | Haiku | Flag illustrations, request changes |
| **Pricing/Subscription** | 8h | Sonnet | Stripe integration, tiers |

**Total P1 Effort:** 60 hours (4-5 weeks)  
**Total P1 Cost:** ~$120 Anthropic + $48 Leonardo + development time

---

### P1.1: Smart Illustration Placement (6 hours) - **Sonnet**

**Objective:** Implement dramatic score-based illustration placement

**Already have:** Dramatic scores from enhanced analysis (P0 Task 1.5)

**Tasks:**
- Calculate illustration points based on frequency (every N pages)
- Select chunks with highest dramatic scores in each window
- Allow manual override
- Save illustration points to database

**Cursor Prompt (Sonnet):**
```
Implement smart illustration placement algorithm:

Input:
- book_id
- illustration_frequency (user-selected: 2, 4, 8, or 12 pages)
- All chunks with dramatic_scores

Algorithm:
1. Calculate number of illustrations:
   num_illustrations = (total_pages / frequency) + 1  # +1 for page 1

2. Always illustrate page 1 (chunk 0)

3. Divide remaining chunks into windows:
   window_size = frequency / 3  # Convert pages to chunks (~3 pages per chunk)
   
4. For each window:
   - Select chunk with highest dramatic_score
   - Mark as illustration point
   
5. Handle edge cases:
   - Minimum 3 pages between illustrations
   - Prefer chapter breaks (detect "Chapter" in text)
   - Skip chunks with dramatic_score < 0.3 (too boring)

6. Save to database:
   UPDATE chunks SET has_illustration = TRUE WHERE id IN (selected_ids)

7. Return illustration plan:
   {
     "total_illustrations": 26,
     "points": [
       {"chunk_id": 0, "page": 1, "score": 0.8, "excerpt": "..."},
       {"chunk_id": 5, "page": 15, "score": 0.9, "excerpt": "..."}
     ]
   }

API Endpoint:
POST /api/books/{book_id}/calculate-illustration-points
Body: {"frequency": 4}

Allow manual override:
PUT /api/books/{book_id}/illustration-points/toggle
Body: {"chunk_id": 10}
```

**Model:** **Claude 3.5 Sonnet** (algorithm complexity)  
**Cost:** ~$0.08

---

### P1.2: Batch Illustration Generation (8 hours) - **Sonnet**

**Objective:** Generate all illustrations for a book efficiently

**Tasks:**
- Priority generation (first 5 immediately)
- Background queue for remaining
- Progress tracking
- Error handling and retries

**Cursor Prompt (Sonnet):**
```
Create batch illustration generation system:

Workflow:
1. Get all chunks marked has_illustration = TRUE
2. Generate first 5 immediately (user waits)
   - Show real-time progress
   - Estimated time: 2-3 minutes
3. Queue remaining illustrations for background processing
4. Allow user to preview book with first 5
5. Background worker generates remaining

Implementation:

Priority Generation:
for chunk in priority_chunks[:5]:
    scene_description = chunk.visual_moment
    characters = get_chunk_characters(chunk.id)
    locations = get_chunk_locations(chunk.id)
    
    prompt = build_scene_prompt(scene_description, characters, locations, visual_bible)
    
    image = leonardo.generate_image(
        prompt=prompt,
        character_reference=get_main_character_reference(characters),
        width=1024,
        height=1536
    )
    
    save_illustration(chunk.id, image)

Background Queue:
- Use simple job queue (or Celery if scaling)
- Process 1 image at a time (avoid rate limits)
- 30 seconds between generations
- Retry failed generations 3 times
- Notify user when complete (email or in-app)

Progress Tracking:
GET /api/books/{book_id}/generation-progress
Response: {
  "total": 125,
  "completed": 47,
  "failed": 2,
  "pending": 76,
  "percent": 38,
  "estimated_time_remaining": 2340  // seconds
}

Error Handling:
- Leonardo API failure → Retry with exponential backoff
- Quota exceeded → Pause queue, alert user
- Timeout → Skip and mark as failed, continue
- All failed → Alert user, offer manual regeneration
```

**Model:** **Claude 3.5 Sonnet** (complex async logic)  
**Cost:** ~$0.12

---

### P1.3: Interior PDF Generation (12 hours) - **Sonnet**

**Objective:** Create KDP-ready interior PDF with text + illustrations

**Tasks:**
- ReportLab layout with proper margins and bleed
- Embed fonts for compatibility
- Place illustrations at correct pages
- Handle page breaks intelligently
- 300 DPI quality

**Cursor Prompt (Sonnet):**
```
Create KDP interior PDF generator using ReportLab:

Requirements:
- Trim size: Support 6x9", 8.5x8.5", 8x10", 8.5x11"
- Bleed: 0.125" on OUTER edges only (right for odd pages, left for even)
- Margins: 0.375" inside (binding), 0.25" outside, 0.5" top/bottom
- Font: Embedded Georgia (serif) for book text
- Images: 300 DPI minimum, placed at illustration points

Layout Logic:

1. Title Page:
   - Book title (24pt, centered)
   - Author name (16pt, centered below title)
   - Blank page after title

2. Content Pages:
   - Chunk text in justified paragraphs
   - First line indent: 0.25"
   - Line spacing: 1.5
   - When chunk has_illustration = TRUE:
     * Insert full-width image above text
     * Image height: 4" (maintain aspect ratio)
     * Caption (optional): "Illustration X of Y"

3. Page Numbering:
   - Start from page 1 (after title)
   - Bottom center
   - Small font (10pt)

4. Bleed Handling:
   - Odd pages (right-hand): Add bleed on right edge
   - Even pages (left-hand): Add bleed on left edge
   - Top/bottom bleed on all pages

Implementation:
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register embedded font
pdfmetrics.registerFont(TTFont('Georgia', 'Georgia.ttf'))

def create_kdp_interior(book_id, trim_size=(8.5, 8.5)):
    doc = SimpleDocTemplate(...)
    story = []
    
    # Title page
    story.append(Paragraph(book.title, title_style))
    story.append(PageBreak())
    
    # Content
    for chunk in chunks:
        if chunk.has_illustration:
            # Add illustration
            ill = get_illustration(chunk.id)
            img = Image(ill.image_path, width=..., height=4*inch)
            story.append(img)
        
        # Add text
        for paragraph in chunk.text.split('\n\n'):
            story.append(Paragraph(paragraph, body_style))
    
    doc.build(story)

API Endpoint:
POST /api/books/{book_id}/generate-interior-pdf
Body: {"trim_size": "8.5x8.5"}
Response: {"interior_pdf_url": "/api/exports/123/interior.pdf"}
```

**Model:** **Claude 3.5 Sonnet** (complex PDF generation)  
**Cost:** ~$0.15

---

### P1.4: Full KDP Export Package (4 hours) - **Haiku**

**Objective:** Package interior.pdf + cover.pdf + instructions.pdf as ZIP

**Cursor Prompt (Haiku):**
```
Create complete KDP export package:

1. Generate interior.pdf (from P1.3)
2. Get cover.pdf (from P0)
3. Create detailed upload_instructions.pdf:
   - Step-by-step KDP upload guide
   - Book specifications (trim size, page count, spine width)
   - Interior + cover upload instructions
   - Preview checklist
   - Pricing calculator
4. Create metadata.txt:
   - Book title, author, ISBN (if applicable)
   - Page count, trim size, paper type
   - Print cost estimate
5. ZIP all files together
6. Return download link

API:
POST /api/books/{book_id}/export-kdp-package
Body: {"trim_size": "8.5x8.5"}

Response: {
  "download_url": "/api/downloads/123/kdp_package.zip",
  "files": [
    "interior.pdf",
    "cover.pdf",
    "upload_instructions.pdf",
    "book_info.txt"
  ],
  "size_mb": 45.2
}
```

**Model:** **Claude 3.5 Haiku** (packaging logic)  
**Cost:** ~$0.02

---

## 🔄 P2: Growth & Enhancement Features (Months 3-6)

**Only build after P1 validates full product:**
- 100+ books generated
- $1K+ MRR
- <20% churn rate

### P2 Feature Roadmap

| Feature | Effort | Business Value |
|---------|--------|----------------|
| Batch Processing (5 books at once) | 12h | Professional tier upsell |
| Series Character Library | 10h | Retain series authors (high LTV) |
| API Access | 16h | Enterprise tier ($200/mo) |
| Advanced Cover Templates | 8h | Differentiation |
| Multi-language Support | 20h | International expansion |
| White-label for Publishers | 24h | B2B2B revenue |
| Analytics Dashboard | 6h | User insights |

---

## 📋 Model Assignment Guidelines

### When to Use Claude 3.5 Haiku ($0.80/$4 per MTok)

**Characteristics:**
- Simple CRUD operations
- UI components with clear requirements
- Form validation
- Styling and layout
- Configuration files
- Straightforward refactoring

**Examples:**
- "Create a file upload form with validation"
- "Update the color scheme to blue and orange"
- "Add a download button to this component"
- "Rename variables from reader to author"

**Cost:** ~$0.01 per typical task

---

### When to Use Claude 3.5 Sonnet ($3/$15 per MTok)

**Characteristics:**
- Complex business logic
- External API integrations
- Multi-step algorithms
- Error handling with retries
- Mathematical calculations
- Database schema design
- Async/concurrent operations
- Security-critical code

**Examples:**
- "Integrate Leonardo AI with polling and error handling"
- "Calculate spine width and generate PDF with bleed"
- "Implement dramatic score algorithm with multi-factor weighting"
- "Create batch generation queue with retry logic"

**Cost:** ~$0.10 per typical task

---

### Decision Tree

```
Is this task...

┌─ Simple UI update? → Haiku
├─ External API integration? → Sonnet
├─ Complex algorithm? → Sonnet
├─ Form/validation? → Haiku
├─ Database CRUD? → Haiku
├─ PDF generation? → Sonnet
├─ Error handling with retries? → Sonnet
├─ Styling/branding? → Haiku
└─ Multi-step workflow? → Sonnet
```

---

## 🎯 Development Best Practices

### Cursor IDE Workflow

**1. Context Loading:**
Always start prompts with relevant context:
```
"Given that we're using Leonardo AI for image generation and storing 
results in the illustrations table, create a service that..."
```

**2. Incremental Development:**
```
Session 1: Basic functionality
Session 2: Error handling
Session 3: Polish and edge cases
```

**3. Testing Prompts:**
```
"Generate 3 test cases for this function:
1. Happy path
2. Edge case (empty input)
3. Error case (API failure)"
```

**4. Code Review Prompts:**
```
"Review this code for:
- Security vulnerabilities
- Performance issues
- Best practices violations
- Missing error handling"
```

---

### Version Control Strategy

**Branch Structure:**
```
main (production)
├── develop (staging)
│   ├── feature/cover-generation
│   ├── feature/leonardo-integration
│   └── fix/upload-validation
```

**Commit Messages:**
```
feat(cover): Add spine width calculation
fix(upload): Validate file extensions correctly
refactor(api): Extract Leonardo service to separate file
docs(readme): Update installation instructions
```

**Before Each Development Session:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

**After Completing a Task:**
```bash
git add .
git commit -m "feat(feature): Description"
git push origin feature/your-feature-name
# Create PR to develop
```

---

## 📊 Progress Tracking

### Weekly Checklist

**Week 1:**
- [ ] Project rebranded to StoryForge AI
- [ ] Database schema updated
- [ ] Direct file upload working
- [ ] AI analysis enhanced with scene extraction
- [ ] Author dashboard functional

**Week 2:**
- [ ] Leonardo AI integrated
- [ ] Cover visual generation working
- [ ] Cover PDF generator functional
- [ ] Customization UI complete
- [ ] First end-to-end cover generated

**Week 3:**
- [ ] Preview mode built
- [ ] Export and download working
- [ ] Cover-only workflow functional
- [ ] Error handling polished
- [ ] 10 test covers generated successfully

**Go-Live:**
- [ ] Documentation complete
- [ ] Landing page live
- [ ] Payment system ready (optional for MVP)
- [ ] First 5 beta users onboarded

---

## 💰 Pricing Strategy (for MVP)

### Free Tier (Market Validation)
- 3 free covers (watermarked)
- Full feature access
- Learn the product

### Paid Tiers (After 50 users)
- **Pay-Per-Cover:** $10-20 per cover (no subscription)
- **Starter:** $19/mo (3 covers/month)
- **Creator:** $29/mo (10 covers/month) ← Target tier

---

## 🚀 Launch Strategy

### Soft Launch (Week 4)
1. Share with 10 author friends
2. Get feedback, fix bugs
3. Testimonials

### Beta Launch (Week 5-6)
1. Reddit: r/selfpublish, r/writing
2. Twitter: #selfpub, #amwriting, #KDP
3. Author Facebook groups
4. Goal: 50 cover generations

### Public Launch (Week 7-8)
1. Product Hunt
2. Hacker News
3. Kindlepreneur guest post
4. KBoards promotion
5. Goal: 200 signups, 10 paying customers

---

## 📈 Success Metrics Dashboard

Track weekly:
```
┌─────────────────────────────────────────┐
│  STORYFORGE AI - WEEK 3 METRICS        │
├─────────────────────────────────────────┤
│  👥 Total Signups: 47                   │
│  📕 Covers Generated: 38                │
│  ✅ Covers Published (KDP): 12          │
│  💰 Revenue: $95                        │
│  ⭐ Satisfaction: 4.2/5.0               │
│  🔄 Return Rate: 28%                    │
└─────────────────────────────────────────┘

GO/NO-GO Decision:
✅ Generated ≥40 covers
✅ Published ≥10 covers
❌ Revenue <$200 (target: $200)
⚠️  DECISION: Need 2 more paying customers
```

---

## 🎓 Learning Resources

### ReportLab (PDF Generation)
- Docs: https://docs.reportlab.com/
- KDP Specs: https://kdp.amazon.com/en_US/help/topic/G201834180

### Leonardo AI
- Docs: https://docs.leonardo.ai/
- Python SDK: https://github.com/leonardo-ai/leonardo-python-sdk

### Amazon KDP
- Publishing Guide: https://kdp.amazon.com/en_US/help/topic/G200645680
- Cover Creator Specs: https://kdp.amazon.com/en_US/cover-templates

---

## 🗄️ Development: Database reset and starting analysis

**Plan: Clean DB → Start Analysis**

To start analysis from a clean state (no existing books or analysis results):

1. **Reset the database** (clears all books, chunks, characters, locations, visual bible, illustrations, covers, exports, and related data):
   ```bash
   cd backend && python scripts/reset_db.py
   ```
2. **Start (or restart) the backend** so the app uses the cleared DB.
3. **Upload a manuscript** and run analysis from the UI (or via API) as usual.

The script is in `backend/scripts/reset_db.py`. It deletes rows in FK-safe order and leaves the schema intact. For per-book re-analysis without wiping the whole DB, the API uses `crud.clear_analysis_results(book_id)` before re-running analysis (idempotent re-analysis).

---

## 🐛 Troubleshooting Common Issues

### Leonardo AI Issues

**Issue:** Rate limit errors  
**Solution:** 
```python
# Add exponential backoff
import time

def generate_with_retry(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return leonardo.generate_image(prompt)
        except RateLimitError:
            wait = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(wait)
    raise Exception("Max retries exceeded")
```

**Issue:** Character consistency poor  
**Solution:**
- Ensure reference image is clear and high-quality
- Increase character reference weight in prompt
- Use character description in prompt along with reference

---

### ReportLab Issues

**Issue:** Fonts not embedded  
**Solution:**
```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register font from file
pdfmetrics.registerFont(TTFont('Georgia', 'Georgia.ttf'))

# Use in style
style = ParagraphStyle('Body', fontName='Georgia')
```

**Issue:** Images not displaying in PDF  
**Solution:**
- Ensure image paths are absolute
- Verify images are 300 DPI minimum
- Check image format (PNG, JPEG supported)

---

## 📝 Next Steps After MVP

**If MVP Succeeds (≥40 covers, ≥$200 MRR):**
1. ✅ Build P1 (Full Illustration Platform)
2. ✅ Optimize costs (negotiate Leonardo bulk pricing)
3. ✅ Add payment processing (Stripe)
4. ✅ Hire VA for customer support
5. ✅ Scale marketing (ads, content)

**If MVP Fails (<30 covers, $0 revenue):**
1. ❌ Pivot to different market segment
2. ❌ Or: Build B2C reading platform instead
3. ❌ Or: Offer service-based illustration (manual)

---

**Good luck building StoryForge AI! 🚀📚✨**

**Remember:**
- Start with Cover MVP (validate market first)
- Use Haiku for simple tasks, Sonnet for complex
- Ship fast, iterate based on feedback
- Authors need speed and affordability, not perfection
- Your competitive advantage is automation (vs Neolemon's manual workflow)

---

**END OF DEVELOPMENT ROADMAP 2.0**
