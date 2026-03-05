# Noctua — Session 2 Final Checkpoint
## ALL DECISIONS RESOLVED — Ready to Generate Implementation Plan

**Supersedes:** `Noctua_Session2_Checkpoint.md` (earlier draft from same session)
**Also read:** `Noctua_Context_Summary.md` (Session 1 decisions, all still in effect)

---

## HOW TO START THE NEXT SESSION

Paste this prompt:

> "I'm continuing work on the Noctua project (AI book cover and illustration platform).
> Read `Noctua_Session2_Final_Checkpoint.md` (uploaded) plus the project knowledge files
> (codebase_snapshot.md, frontend_code_snapshot.md, Noctua_Implementation_Plan_Merged.md).
> Also read `Noctua_Context_Summary.md` (uploaded) for Session 1 decisions.
> All planning decisions are fully resolved. Your job this session is to generate:
> 1. `scripts/test_prompt_engineering.py` — standalone prompt merge test script (spec in Section 4)
> 2. Full new Noctua Implementation Plan superseding Noctua_Implementation_Plan_Merged.md
> The plan spec is in Section 6. Use Cursor Composer format throughout.
> Do not ask clarifying questions — all decisions are locked."

---

## 1. Session 1 Decisions — All Still in Effect

Read `Noctua_Context_Summary.md` for full detail. Key items carried forward:

- I2T pivot confirmed. Primary path: reference image → GPT-4o Vision → style_template → Prompt Engineering Service → FLUX Kontext via fal.ai
- CoverPromptAssembler retained as fallback (no reference image path)
- Copyright policy: third-party cover refs → I2T text path ONLY. No direct image conditioning.
- fal.ai primary T2I: FLUX Kontext Pro ($0.04/image), FLUX Kontext Max ($0.08/image)
- TextStudio: browser-side canvas compositing, no backend round-trip
- Serper: supplementary provider with domain blacklist
- Phases 1–7 complete. New plan continues from Phase 8.

---

## 2. Session 2 Decisions — All Resolved

### D1 — Phase Numbering
Continue from Phase 8. Phases 1–7 marked complete with one-line status each.

### D2 — Frontend Build Order
Backend first (Phases 8–9), then frontend (Phases 10–12).

### D3 — I2T Trigger in Moodboard
Explicit **"Analyse style"** button. No auto-trigger.

### D4 — Illustration Pipeline
**Phase 16+ placeholder only.** Architecture note, no implementation scope.

### D5 — Cover Brief Editor Layout
**Two panels:**
- Panel B (merged prompt): always visible, always editable
- Panel A (I2T style template): collapsed by default, expandable via "Advanced" toggle
- Simple tier: both panels hidden — shows cover type + primary element selector only

### D6 — CLIP / Text Encoder
Deferred. Add to enhancement backlog in Phase 15 docs. LLM-based compatibility check sufficient for launch.

### D7 — Simple vs. Pro Tier Split *(finalised late Session 2)*

**Workflow selector on manuscript upload page:**
- Radio button: `Full Book` | `Book Cover`
- `Book Cover` mode = basis for **Simple subscription tier**
- In Simple subscription, `Book Cover` is the only available workflow
- `Full Book` mode = **Pro subscription tier** only

**AI Analysis Engine — branches into 2 versions:**

| | Simple Analysis | Pro Analysis |
|---|---|---|
| Trigger | Book Cover mode | Full Book mode |
| Pass count | Single pass | Multi-pass (existing pipeline) |
| Extracts | Key characters only | Characters + locations + artefacts + scenes |
| Cover brief inputs | Genre + mood + characters | Full entity ontology |
| Prompt Engineering | CoverPromptAssembler (character-aware) | I2T + Prompt Engineering Service (full merge) |

**Implementation note:** The Simple analysis is a regression to Noctua's earlier linear single-pass analysis, not new work. It is a refactor/branch of the existing pipeline, not a rewrite.

**Phase placement:** Analysis engine branch refactor goes into **Phase 8** — it must exist before I2T service (Phase 9) since both downstream services consume entity data. Phase 8 therefore has two parallel scopes:
  - 8a: Analysis Engine branch (Simple vs. Pro modes)
  - 8b: I2T Analysis Service (builds on top of Phase 8a entity data)

### D8 — QuickCover Mode (supersedes earlier 'QuickCoverPage' suggestion)
No separate QuickCoverPage. Instead:
- Workflow selector radio on upload page handles the routing
- Book Cover mode IS the quick/simple path
- Characters extracted by Simple Analysis feed directly into CoverPromptAssembler fallback path
- No new backend work beyond the analysis branch already specified in D7
- Phase: handled within Phase 8a + Phase 11 frontend (workflow selector UI)

### D9 — Pricing Model Confirmed
Subscription tiers. Simple = lower monthly fee, Pro = higher monthly fee.
- Simple tier: Book Cover mode only, Simple Analysis, 3 concepts/run, limited moodboard slots, genre font presets
- Pro tier: Full Book + Book Cover mode, Pro Analysis, 6 concepts/run, unlimited moodboard, full font library + custom upload
- Exact price points TBD (suggested range: Simple $12–18/mo, Pro $29–39/mo — based on competitive analysis)
- Architecture: `user.plan` field ('simple' | 'pro') on User model. Feature gate in frontend. Phase 16.

---

## 3. Competitive Analysis Findings (Session 2)

### Bookbrush
- ~100K registered accounts (total, not paid). Bootstrapped. ~12 person team.
- Estimated ARR: $400K–$900K (estimated, not confirmed — based on account count and conversion assumptions)
- Template-first tool. No AI image generation. No manuscript awareness.
- Strong community (conferences, YouTube, partnerships with Draft2Digital etc.) — this is their moat, not the product quality
- Pricing: Free / Plus $8.25/mo / Gold $12.25/mo / Platinum $20.50/mo

### CoverDesignAI
- Closest direct AI competitor. Accepts reference image for style matching (direct conditioning, not I2T).
- No manuscript upload. Author must manually describe characters and scenes.
- No public revenue, funding, or team size data. Likely solo/2-person project, sub-$100K ARR.
- Fastest path to first cover (~10 min) — poses a first-impression challenge for Noctua onboarding

### GetCovers
- NOT an AI tool. Human designer service. Explicitly no AI without author permission.
- $150–600+ per cover, 3–7 days turnaround.
- Best benchmark for Pro tier pricing justification.

### Key Strategic Conclusions
1. Bookbrush's moat is community/distribution, not product — Noctua needs a distribution strategy
2. CoverDesignAI's lack of traction despite reasonable product suggests discovery is the hard problem
3. Noctua's structural moat: manuscript → entity ontology → I2T style extraction → entity merge. No competitor does this chain.
4. CoverDesignAI's 10-min first cover is a demo risk for Noctua — mitigated by Book Cover mode (D8)

---

## 4. Prompt Engineering Test Script — Specification

**File:** `scripts/test_prompt_engineering.py`

**Purpose:** Standalone validation of I2T → entity merge logic before building the full service.

**What it must do:**
1. Hardcoded I2T `style_template` string (example below)
2. Hardcoded entity dict (character with visual_tokens)
3. Hardcoded user instruction string
4. Build three-section GPT-4o prompt: STYLE TEMPLATE / ENTITY TO REPLACE / REPLACEMENT ENTITY + INSTRUCTION
5. Call GPT-4o, print: merged T2I prompt, negative prompt, compatibility assessment
6. Second call with incompatible entity to test compatibility warning path

**Example inputs:**
```python
style_template = """dark atmospheric fantasy illustration, hooded cloaked figure standing
in misty forest, moonlit background, Art Nouveau decorative border, deep teal and gold
color palette, highly detailed, cinematic lighting, f/2.8 bokeh background, 8k render
quality, dramatic upward angle, negative space at top for title"""

entity = {
    "name": "Seraphina Vale",
    "entity_class": "character",
    "visual_type": "humanoid",
    "core_tokens": ["red-haired woman", "emerald eyes", "scholar's robes", "ink-stained hands"],
    "style_tokens": ["pre-Raphaelite", "ethereal", "bookish"],
    "archetype_tokens": ["the seeker", "reluctant hero"],
    "anti_tokens": ["cartoonish", "modern clothing", "blonde"]
}

user_instruction = "Replace the hooded figure with my protagonist, keeping the forest atmosphere"
```

**Success criteria:**
- Output retains: forest, Art Nouveau border, teal/gold palette, moonlit atmosphere
- Output replaces: hooded figure → Seraphina Vale with her visual tokens
- Anti-tokens appear in negative prompt
- Compatibility: COMPATIBLE (same compositional role — single foreground figure)
- Second test (cityscape location replacing a character): returns WARNING with explanation

---

## 5. Enhancement Backlog (Do Not Implement — Document Only)

Add these to `docs/enhancement_backlog.md` in Phase 15:

- **CLIP text encoder** for compatibility pre-check in Prompt Engineering Service (replaces heuristic)
- **CLIP image embedding** for style tag validation (catches GPT-4o Vision hallucinations)
- **Leonardo.ai** secondary T2I provider (`leonardo_provider.py`)
- **LoRA training** for character consistency (illustration pipeline prerequisite)
- **Direct image conditioning** opt-in for user-owned covers (premium future feature)
- **3D mockup** preview after TextStudio export
- **Pro tier variation controls**: style intensity slider, composition lock
- **API access** for Pro+ / developer tier

---

## 6. New Implementation Plan — Full Specification

### Format
Cursor Composer format exactly as in `Noctua_Implementation_Plan_Merged.md`:
- Phase header with dependency
- Files touched list
- Numbered instruction sections with code blocks
- Unit test section at end of each phase
- Success criteria checklist

### Phase Map

---

**PHASES 1–7 — COMPLETE**
Mark each with one-line status. No implementation content needed.

- Phase 1: Manuscript ingestion (upload, chunking, .txt/.docx/.pdf) ✅
- Phase 2: Entity AI analysis pipeline (GPT-4o-mini, characters/locations/artefacts/scenes) ✅
- Phase 3: Visual token generation per entity (core/style/archetype/anti tokens) ✅
- Phase 4: Scene extraction with dramatic scoring ✅
- Phase 5: Multi-provider reference image search (Unsplash, SerpAPI, Pexels, Pixabay, Openverse, Wikimedia, DeviantArt, Behance, Dribbble) ✅
- Phase 6: Visual Bible approval + selected_reference_urls storage ✅
- Phase 7: Bug fixes, data model extensions, VB entries API, Cover Studio API stubs ✅

---

**Phase 8a — Analysis Engine Branch (Simple vs. Pro)**

Dependency: Phase 7 complete
Files touched:
- `backend/app/services/analysis_service.py` (refactor)
- `backend/app/services/simple_analysis_service.py` (new)
- `backend/app/routers/analysis.py` (modify: add mode param)
- `backend/app/models.py` (add: `analysis_mode` field on Book: 'simple' | 'pro')
- `backend/app/schemas.py` (add: AnalysisMode enum)

Scope:
- Add `analysis_mode: AnalysisMode` field to Book model (default: 'pro')
- `simple_analysis_service.py`: single-pass GPT-4o-mini call. Extracts key characters only (name, description, visual tokens). No locations, artefacts, scenes.
- `analysis_service.py`: renamed to `pro_analysis_service.py` OR keep filename and add mode branch at entry point
- Router: `POST /api/books/{book_id}/analyze` accepts `mode: 'simple' | 'pro'` param (default: 'pro'). Routes to appropriate service.
- Engine selector: `get_analysis_service(mode)` returns SimpleAnalysisService or ProAnalysisService

Tests:
- Simple analysis returns only Character entities, no Location/Artefact/Scene records created
- Pro analysis returns all entity types (existing test coverage)
- Router correctly routes by mode param
- Book.analysis_mode field persists correctly
- Simple analysis completes in single LLM pass (assert call_count == 1)

---

**Phase 8b — I2T Analysis Service (Backend)**

Dependency: Phase 8a complete
Files touched:
- `backend/app/services/i2t_analysis_service.py` (new)
- `backend/app/routers/covers.py` (add endpoint)
- `backend/app/models.py` (add fields to CoverAnalysis)
- `backend/app/schemas.py` (add I2TAnalysisResult schema)

Scope:
- New file: `i2t_analysis_service.py`
- Model: GPT-4o-mini for covers (~$0.0004/image). GPT-4o full as opt-in if mini proves insufficient.
- Extraction modes: `cover` | `illustration`
- Output schema (Pydantic `I2TAnalysisResult`):
  - `style_template: str` — full T2I prompt string
  - `composition_notes: str`
  - `color_palette_extracted: dict` (dominant, accent, temperature, contrast)
  - `style_tags: list[str]`
  - `mood_keywords: list[str]`
  - `lighting_description: str`
- New DB fields on CoverAnalysis:
  - `reference_style_template TEXT`
  - `reference_style_notes JSON`
  - `reference_image_url TEXT`
- New endpoint: `POST /api/books/{book_id}/analyze-cover-reference`
  - Body: `{ image_url: str, mode: 'cover' | 'illustration' }`
  - Stores result to CoverAnalysis fields
  - Returns I2TAnalysisResult
- Error handling: if Vision call fails, return empty I2TAnalysisResult, do NOT block moodboard flow

Tests:
- Mock GPT-4o Vision response → assert all I2TAnalysisResult fields populated
- Assert DB fields updated on CoverAnalysis record
- Assert graceful empty result returned on Vision API error (no exception propagated)
- Assert mode param correctly sets extraction vocabulary (cover vs. illustration prompt differs)

Also in Phase 8b: generate `scripts/test_prompt_engineering.py` per Section 4 spec above.

---

**Phase 9 — Prompt Engineering Service + fal.ai T2I Provider (Backend)**

Dependency: Phase 8b complete
Files touched:
- `backend/app/services/prompt_engineering_service.py` (new)
- `backend/app/services/t2i_providers/flux_provider.py` (replace stub)
- `backend/app/services/t2i_providers/dalle_provider.py` (replace stub)
- `backend/app/services/engine_selector.py` (extend: add get_cover_t2i_provider())
- `backend/app/schemas.py` (add PromptEngineeringResult schema)

Scope — Prompt Engineering Service:
- Two modes: `cover` | `illustration`
- Cover mode inputs: `style_template` (from I2T), `primary_entity` (from DB), `user_instruction` (natural language)
- Compatibility pre-check: use entity `visual_type` + `entity_class` ontology fields for fast heuristic before LLM call
- LLM merge call: three-section GPT-4o prompt (STYLE TEMPLATE / ENTITY TO REPLACE / REPLACEMENT + INSTRUCTION)
- Output schema `PromptEngineeringResult`:
  - `final_prompt: str`
  - `negative_prompt: str`
  - `compatibility_status: Literal['COMPATIBLE', 'WARNING', 'INCOMPATIBLE']`
  - `compatibility_note: str`
- Fallback path: if no style_template (Simple tier / no reference image), route to CoverPromptAssembler
  - Simple tier fallback inputs: genre + mood + character core_tokens only

Scope — FLUX Kontext Provider:
- Replace stub in `flux_provider.py` with real fal.ai calls
- TEXT_ENDPOINT: `fal-ai/flux-pro/v1.1`
- KONTEXT_ENDPOINT: `fal-ai/flux-pro/kontext`
- Requires: FAL_API_KEY env var, `pip install fal-client`
- `is_available()`: returns bool(os.getenv("FAL_API_KEY"))
- `generate(prompt, image_url=None, negative_prompt=None, aspect_ratio="2:3", ...)`: uses KONTEXT_ENDPOINT if image_url provided, TEXT_ENDPOINT otherwise

Scope — DALL-E Provider:
- Replace stub with real OpenAI DALL-E 3 HD call
- image_url param ignored (log warning)
- Size: 1024×1792

Scope — Engine Selector:
- `get_cover_t2i_provider()`: returns FluxKontextProvider if FAL_API_KEY set, else DalleProvider

Tests:
- Mock GPT-4o merge call → assert PromptEngineeringResult fields populated
- Compatibility WARNING returned for incompatible entity pair (location replacing character)
- FluxKontextProvider selected when FAL_API_KEY env var set
- DalleProvider selected when FAL_API_KEY not set
- KONTEXT_ENDPOINT used when image_url supplied to FluxKontextProvider
- TEXT_ENDPOINT used when no image_url
- CoverPromptAssembler fallback triggered when style_template is None

---

**Phase 9b — Serper Provider (Backend)**

Dependency: Phase 7 complete (can run parallel to 8–9)
Files touched:
- `backend/app/services/providers/serper_provider.py` (new)
- `backend/app/services/engine_selector.py` (add Serper routing rules)
- `backend/.env.example` (add SERPER_API_KEY)

Scope:
- Follows existing `base.py` provider interface exactly
- Hard blacklist (filter out entirely): `lookaside.instagram.com`, `lookaside.fbsbx.com`, `craiyon.com`, `getimg.ai`, `ideogram.ai`
- Soft flag (return but set `watermarked: True`): `shutterstock.com`, `dreamstime.com`, `gettyimages.com`, `istockphoto.com`
- Engine selector routing:
  - Serper = supplementary for artefact + location searches
  - NOT primary for book cover I2T searches
  - Book cover queries: target goodreads.com, publisher sites — not generic style terms

Tests:
- Blacklisted domain URLs filtered from results
- Watermarked flag set on stock photo domain results
- Provider follows base interface contract (duck-type check)
- SERPER_API_KEY not set → is_available() returns False gracefully

---

**Phase 10 — SetupPage / WorkflowNav / Workflow Selector Frontend**

Dependency: Phase 9 complete
Files touched:
- `frontend/src/pages/SetupPage.tsx` (refactor)
- `frontend/src/components/WorkflowNav.tsx` (refactor)
- `frontend/src/pages/UploadPage.tsx` (add workflow selector)
- `backend/app/routers/books.py` (add workflow_mode to book creation)

Scope:
- UploadPage: add radio button selector — `Full Book` (Pro) | `Book Cover` (Simple)
  - Simple tier users: only `Book Cover` option available (Full Book radio disabled + tooltip: "Upgrade to Pro")
  - Selection stored as `book.analysis_mode` ('simple' | 'pro') on book create/update
- SetupPage: book setup wizard (title, genre, author name) — connects to existing POST /api/books
- WorkflowNav visual update: step indicators with 48×32px illustrations, full color if active, 30% opacity inactive, checkmark overlay on completed steps
- WorkflowNav steps differ by mode:
  - Book Cover mode: Upload → Characters → Moodboard → Cover Brief → Generate → TextStudio
  - Full Book mode: Upload → Analysis → Characters → Locations → Artefacts → Moodboard → Cover Brief → Generate → TextStudio

Tests:
- Workflow selector renders both options for Pro user
- Simple tier user sees Full Book option disabled
- Book Cover selection → book.analysis_mode = 'simple' on save
- WorkflowNav renders correct step count per mode
- Completed steps show checkmark overlay

---

**Phase 11 — AnalysisReviewPage + Cover Brief Editor Frontend**

Dependency: Phase 10 complete
Files touched:
- `frontend/src/pages/AnalysisReviewPage.tsx` (new)
- `frontend/src/components/CoverBriefEditor.tsx` (new)
- `frontend/src/components/FeatureGate.tsx` (new — plan-based gate component)

Scope — AnalysisReviewPage:
- Book Cover mode: single tab (Characters only) + `is_main` toggles
- Full Book mode: four tabs (Characters / Locations / Artefacts / Cover) + `is_main` toggles
- Tabs hidden/shown based on `book.analysis_mode`
- Connects to existing entity endpoints

Scope — CoverBriefEditor:
- **Simple tier** (Book Cover mode): Cover type selector + Primary element selector (character only) + Style reference thumbnail + "Generate" button. No prompt panels.
- **Pro tier** (Full Book mode): Full two-panel layout:
  - Panel B (merged prompt): always visible, editable textarea
  - Panel A (I2T style template): collapsed by default, expandable via "Advanced" toggle
  - Negative prompt field (Pro only)

Scope — FeatureGate component:
- `<FeatureGate plan="pro" fallback={<UpgradeBanner />}>...</FeatureGate>`
- Reads `user.plan` from AuthContext
- Used to gate: Panel A Advanced toggle, negative prompt field, Full Book workflow selector option, locations/artefacts tabs

Tests:
- Simple tier Cover Brief Editor renders without prompt panels
- Pro tier renders both panels, Advanced toggle expands Panel A
- FeatureGate renders children for Pro user
- FeatureGate renders fallback for Simple user
- AnalysisReviewPage shows only Characters tab for Book Cover mode
- AnalysisReviewPage shows all four tabs for Full Book mode

---

**Phase 12 — MoodBoardPage Frontend**

Dependency: Phase 11 complete
Files touched:
- `frontend/src/pages/MoodBoardPage.tsx` (new — replaces VisualBiblePage stub)

Scope:
- Book Cover mode (Simple): single "Covers" tab only — upload/select cover reference + "Analyse style" button
- Full Book mode (Pro): four tabs — Characters / Locations / Artefacts / Covers
- Covers tab in both modes:
  - Display uploaded/selected cover reference images
  - "Analyse style" button (explicit trigger — fires POST /api/books/{id}/analyze-cover-reference)
  - Loading state during I2T call (dismissible)
  - Success state: style template summary card (genre chips, mood keywords, color palette swatches)
  - Summary card links to Cover Brief Editor Panel A
  - Error state: graceful fallback message, moodboard still usable
- Character/Location/Artefact tabs (Pro only): reference image grid, select/deselect, upload own image, approve to Visual Bible

Tests:
- Book Cover mode renders only Covers tab
- Full Book mode renders all four tabs
- "Analyse style" button calls correct endpoint
- Loading state shown during I2T call
- Success state shows style template summary card
- Error state shows fallback message without blocking moodboard
- Approving image adds to Visual Bible (existing endpoint)

---

**Phase 13 — Cover Generation Endpoint + Cover Studio Page**

Dependency: Phase 12 complete
Files touched:
- `backend/app/routers/covers.py` (wire POST /api/books/{id}/covers/generate to real services)
- `frontend/src/pages/CoverStudioPage.tsx` (new)

Scope — Backend:
- Wire generate endpoint to PromptEngineeringService + T2IProvider (FluxKontext or DALL-E fallback)
- concept_count: 3 for Simple tier, 6 for Pro tier (read from user.plan)
- Store results as CoverConcept records with status, image URL, prompt used

Scope — Frontend CoverStudioPage:
- Generated concept grid (3 or 6 cards)
- Select preferred concept → proceed to TextStudio
- Regenerate button (costs 1 credit)
- Show prompt used (Pro tier only — behind FeatureGate)

Tests:
- Generate endpoint calls PromptEngineeringService then T2IProvider in correct order
- concept_count respects user.plan (3 vs 6)
- CoverConcept records created in DB with correct status
- CoverStudioPage renders concept grid
- Pro user sees prompt used on concept card

---

**Phase 14 — TextStudio (Typography Compositor)**

Dependency: Phase 13 complete
Files touched:
- `frontend/src/pages/TextStudioPage.tsx` (new)
- `frontend/src/components/TextStudio/CanvasCompositor.tsx` (new)
- `frontend/src/components/TextStudio/FontLibrary.ts` (new — curated font data)

Scope:
- Browser canvas: render generated cover image + title/author text overlay
- KDP bleed-safe output: **verify KDP spec before implementation** — target 2560×1600 (6"×9" at 300dpi with 0.125" bleed). Confirm against current KDP guidelines.
- Simple tier: 3 font choices per genre preset, drag-to-reposition, no placement suggestions, no custom upload
- Pro tier: full font library (~20+ fonts), smart placement suggestions (detect negative space zones), custom font upload (.ttf/.otf)
- Export: flatten canvas to PNG, trigger download
- Communicate KDP-safe dimensions explicitly in UI (trust signal vs. Bookbrush)

Tests:
- Canvas renders image + text overlay
- Drag gesture repositions text element
- Export produces PNG blob at correct dimensions
- Simple tier shows only 3 fonts per genre
- Pro tier shows full library + upload button
- Smart placement suggestions only shown for Pro tier

---

**Phase 15 — App Rename + ChapterHeader + Enhancement Backlog**

Dependency: Phase 14 complete
Files touched: `frontend/index.html`, `frontend/src/App.tsx`, `backend/app/main.py`, `package.json`, `docs/codebase_snapshot.md`, `frontend/src/components/ChapterHeader.tsx` (new), `docs/enhancement_backlog.md` (new)

Scope:
- Replace all "YRead" / "StoryForge AI" / "StoryForge" → "Noctua" throughout codebase
- ChapterHeader component: shows chapter title + instruction sentence per workflow step. Collapsible. Preference persisted to localStorage.
- WorkflowNav final polish
- Create `docs/enhancement_backlog.md` with full list from Section 5 of this checkpoint

---

**Phase 16 — Alpha Deployment (Auth + PostgreSQL + Railway)**

Dependency: Phase 15 complete
Files touched: same as existing Phase 16 in Noctua_Implementation_Plan_Merged.md — carry forward verbatim with one addition:

- Add `user.plan: Literal['simple', 'pro']` field (default: 'simple') to User model
- Add plan field to auth token / user context so frontend FeatureGate has access without extra API call
- Alembic migration for user.plan field

---

**Phase 17 — Illustration Pipeline (Future Placeholder)**

⏳ FUTURE — Not in current implementation scope.

Architecture note only:
- Same I2T → Prompt Engineering path as cover pipeline
- I2T mode: `illustration` (scene composition vocabulary)
- Entity conditioning: character + location reference images via FLUX Kontext
- LoRA training required for per-book character consistency (Leonardo.ai enterprise or Replicate)
- Output: IllustrationConcept record, per-chapter
- User journey: Reading Page shows illustrations inline with chapter text
- Add to separate planning session when cover pipeline is live and validated.

---

## 7. Files to Upload to Next Session

Required:
- This file: `Noctua_Session2_Final_Checkpoint.md`
- `Noctua_Context_Summary.md` (Session 1 — still needed for full context)

Project knowledge (already loaded — no upload needed):
- `codebase_snapshot.md`
- `frontend_code_snapshot.md`
- `Noctua_Implementation_Plan_Merged.md`

---

## 8. What the Next Session Generates (in order)

1. `scripts/test_prompt_engineering.py` — per Section 4 spec
2. Full new Implementation Plan document in Cursor Composer format — per Section 6 spec
   - Phases 1–7: one-line complete status each
   - Phases 8a through 17: full Cursor Composer detail
3. (Optional) Updated `Noctua_Session2_Checkpoint.md` → `Noctua_Session3_Checkpoint.md` if planning continues
