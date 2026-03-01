# Noctua — Project Context Summary
## For Session Continuity — Paste at Start of New Conversation

**Purpose:** This document captures every architectural decision, research finding, and strategic pivot agreed in a prior Claude session. It is the single source of truth for continuing implementation plan work. The companion architecture diagram is `noctua_architecture.jsx` — a React component visualising all modules with build status, click-to-detail, and a module summary table.

---

## 1. What Noctua Is

Noctua (codebase name: YRead / StoryForge AI) is an AI-powered book production platform. Its current primary use case is **AI-assisted book cover generation**. Its long-term vision is **AI-illustrated reading experience** — producing chapter illustrations that give readers a new level of immersion.

The user journey at target state:
1. Author uploads manuscript
2. Noctua extracts characters, locations, artefacts, scenes with visual descriptions and ontology
3. Author reviews and selects main entities
4. Author finds reference images for entities (moodboard)
5. Author uploads or selects a cover they love → Noctua reverse-engineers its style
6. Author tells Noctua what to replace ("use this cover but replace the character with my protagonist")
7. Noctua merges the style template with book-specific entity descriptions → generates cover
8. Author adds typography in browser → downloads final cover PNG

---

## 2. Current Build State

**Phases 1–6: Complete** (backend only, partial frontend)
**Phase 7: Complete** (bug fixes, data model extensions, VB entries API, Cover Studio API stubs)

### What is fully built and working:
- Manuscript upload, chunking (.txt, .docx, .pdf)
- Multi-entity AI analysis pipeline (characters, locations, artefacts, cover brief) via GPT-4o-mini
- Ontology classification for all entity types
- Visual token generation (core, style, archetype, anti tokens per entity)
- Scene extraction with dramatic scoring
- Cover analysis service (two-stage: thematic extraction → cover brief)
- Multi-provider reference image search: Unsplash, SerpAPI, Pexels, Pixabay, Openverse, Wikimedia, DeviantArt, Behance, Dribbble
- Query diversification and engine selector (routes artefact/cover to art-heavy providers)
- Visual Bible approval and `selected_reference_urls` storage per entity
- Entity database (SQLite dev / PostgreSQL prod): Character, Location, Artefact, Scene, CoverAnalysis, VisualBibleEntry, CoverConcept models
- Analysis Review UI (four tabs: Characters / Locations / Artefacts / Cover) — partial Phase 7 gaps
- ReviewSearchPage and ReviewSearchResultPage with VisualBibleReview component
- All backend API endpoints through Phase 7

### What is stubbed / not yet built:
- T2I providers: `flux_provider.py`, `sd_provider.py`, `abstract_provider.py` — stubs only, no real API calls
- `illustrations.py` router — empty
- `webhook.py` router — empty
- MoodBoardPage — not yet built (stub exists as VisualBiblePage)
- CoverStudio page — not yet built
- TextStudio page — not yet built
- Frontend Phases 10–13 — not yet built
- Typography compositor — not yet built
- I2T Analysis Service — does not exist yet
- Prompt Engineering Service — does not exist yet
- Serper provider — does not exist yet

---

## 3. The Strategic Pivot — Why and What Changed

### The Discovery
Through manual experimentation, it was found that **prompts reverse-engineered from existing book covers via GPT-4o Vision (I2T), combined with manual element substitution, produce significantly better T2I results than Noctua's existing deterministic `CoverPromptAssembler`**.

Example workflow that was tested manually:
- Uploaded Barbara Erskine "The Story Spinner" cover to GPT-4o
- Asked: "Describe this as a Stable Diffusion prompt"
- Received: `Two golden feathers floating against a deep midnight purple background, delicate intricate quill detail, soft luminous glow, scattered gold dust particles, Art Nouveau influence, negative space composition...`
- Substituted feathers with book-specific artefact description → generated cover
- Result was demonstrably better than `CoverPromptAssembler` output

### The Pivot Decision
**The I2T + Prompt Engineering path becomes the PRIMARY cover generation flow.** The existing `CoverPromptAssembler` is retained as a fallback for users who don't supply a reference image.

This is an **additive** pivot — nothing built in Phases 1–7 is discarded. The entity extraction, visual tokens, and scene analysis all become *inputs* to the new Prompt Engineering Service rather than inputs to the assembler.

### What the Pivot Adds
Two new central modules (see Section 5):
1. **I2T Analysis Service** — GPT-4o Vision extracts style template from reference image
2. **Prompt Engineering Service** — merges I2T style template with entity context from DB

---

## 4. Architecture Overview

The full architecture is visualised in **`noctua_architecture.jsx`** — a React component with:
- Click-any-module-for-details interaction
- Colour coding: green = built, orange = pivot/enhance, purple = new, blue = data store
- Six functional layers: Ingestion → Review → Reference Search → I2T+Prompt Engineering → Image Conditioning → Output
- Module summary table with phase assignments

### The Six Layers

**Layer 1 — Ingestion & Analysis** *(Built)*
Manuscript upload → chunking → AI analysis → entity database

**Layer 2 — Review & Entity Selection** *(Built, Phase 7 gaps)*
AnalysisReviewPage → is_main selections → Cover Brief Editor (primary element, cover type, colour palette)

**Layer 3 — Reference Image Search** *(Built + Pivot: add Serper)*
Multi-provider search → Moodboard & Reference Selector → Visual Bible DB
Pivot: cover tab in Moodboard now triggers I2T automatically when image selected

**Layer 4 — I2T Analysis & Prompt Engineering** *(New — Core)*
Reference image → I2T Service → style template → Prompt Engineering Service → (merges with entity context from DB) → final prompt → Cover Generation OR Illustration Generation

**Layer 5 — Image Conditioning** *(Visual Bible → T2I)*
Visual Bible approved reference images passed as FLUX Kontext image conditioning
Rules: artefact/character/location references → direct conditioning; cover references → I2T text path only (copyright)

**Layer 6 — Output & Finishing**
Cover Studio UI → Typography Compositor (TextStudio) → download PNG
Illustration Generation → Reading Page (future)

---

## 5. New Modules — Detailed Specifications

### 5.1 I2T Analysis Service
**File:** `backend/app/services/i2t_analysis_service.py` (new)
**What it does:** Takes an image URL or uploaded image, calls GPT-4o Vision, returns structured style description in T2I vocabulary.
**Modes:** `cover` (for book cover style extraction) | `illustration` (for illustration example extraction)
**Output fields:**
- `style_template` — full prompt string ready for T2I
- `composition_notes` — foreground/background/negative space description
- `color_palette_extracted` — dominant, accent, temperature, contrast
- `style_tags` — list: medium, art movement, rendering quality
- `mood_keywords` — list
- `lighting_description` — string

[[suggestions from OpenAI on I2T analysis service]] - use that to consider how to build the Analysis Service 

**Cost:** ~$0.0004/image (GPT-4o-mini, low detail) — negligible. Use GPT-4o-mini for covers (style extraction doesn't need high detail). Use GPT-4o full only if mini proves insufficient.

**Trigger points:**
- When user selects/uploads a cover reference in the Moodboard cover tab
- When user uploads an illustration example (future illustration pipeline)
- On-demand via `POST /api/books/{book_id}/analyze-cover-references`

**Storage:** Result stored in `cover_analysis.reference_style_template` (new field) and `cover_analysis.reference_style_notes` (new field).

### 5.2 Prompt Engineering Service
**File:** `backend/app/services/prompt_engineering_service.py` (new)
**What it does:** Merges I2T-derived style template with entity-specific context from the database. Handles natural language substitution instructions from users.

**Two modes:**
1. **Cover mode** — replaces a style template element with a character/location/artefact from the book. Input: style_template + primary entity description + user instruction (e.g. "replace the character with the main protagonist")
2. **Illustration mode** — replaces style template subject with scene description + entity visual tokens

**Core logic:**
- Sends three-section prompt to GPT-4o: STYLE TEMPLATE + ENTITY TO REPLACE + REPLACEMENT ENTITY + INSTRUCTION
- Runs compatibility validation step first: checks if replacement entity is compositionally compatible with template (e.g. a full landscape can't replace a small foreground object)
- If incompatibility: returns warning to user and either adapts composition or asks user to choose a different template
- Uses entity ontology data (entity_class, materiality, visual_type) from DB to predict compatibility before LLM call — fast pre-check

**Relationship to CoverPromptAssembler:**
- I2T path: `reference image → I2T Service → Prompt Engineering Service → final prompt` (primary)
- Fallback path: `cover_analysis data → CoverPromptAssembler → final prompt` (no reference image)

**User-facing UX:** "Assembled Prompt Preview" in Cover Brief Editor shows the merged prompt before generation. User can edit it.

---

## 6. Serper Integration Decision

### Test Results Summary (from `serper_test_raw.json` and `serper_test_report.txt`)
- 12/12 queries succeeded
- Average quality score: 4.33/8.0
- Average response time: 1.95s
- Characters: 5.23 (Good) — but inflated by unusable Instagram crawler URLs
- Locations: 4.23 (OK)
- Artefacts: 4.07 (OK) — DeviantArt and Pinterest results are genuinely good
- Book Covers: 3.80 (OK) — returns gallery pages, not individual clean covers

### Decision: Add as Supplementary Provider
**File:** `backend/app/services/providers/serper_provider.py` (new)
**Interface:** Follows existing `base.py` provider interface exactly
**Cost:** ~$0.001/query vs SerpAPI's ~$0.005 — 5x cheaper
**Registration:** 2,500 free queries available at serper.dev (no credit card)

### Required Filters (implement in serper_provider.py):
**Hard blacklist — never return these domains:**
- `lookaside.instagram.com` — Instagram SEO crawler URLs, non-functional for image display
- `lookaside.fbsbx.com` — Facebook crawler URLs, same problem
- `craiyon.com`, `getimg.ai`, `ideogram.ai` — AI-generated images (circular conditioning)

**Soft flag — return but mark as watermarked (not for T2I conditioning):**
- `shutterstock.com`, `dreamstime.com`, `gettyimages.com`, `istockphoto.com`

**Routing rules in engine_selector.py:**
- Use Serper as supplementary for: artefact searches, location searches
- Do NOT use Serper as primary for: book cover I2T searches (needs dedicated query strategy)
- Book cover search queries need different format: target goodreads.com, publisher sites, specific genre databases rather than generic style terms

---

## 7. T2I Provider Decision

### Decision: fal.ai as Primary, Leonardo as Secondary

**fal.ai (Primary)**
- FLUX Kontext Pro: $0.04/image
- FLUX Kontext Max: $0.08/image
- Native image URL conditioning input — perfect for Visual Bible pipeline
- Python SDK, WebSocket async callbacks — fits Noctua's background task architecture
- Existing `flux_provider.py` stub already targets fal.ai
- 99.99% uptime SLA
- No LoRA training at standard tier (enterprise only)

**Leonardo.ai (Secondary / Future)**
- Use for: accessing Leonardo proprietary models (Phoenix, PhotoReal) as alternative aesthetics
- Use for: LoRA training when illustration pipeline needs per-book style consistency
- FLUX Kontext on Leonardo costs more (token markup) — don't use for FLUX, use fal.ai direct
- Already have credits there — use for manual testing and prompt research
- `leonardo_provider.py` to be added following same abstract base interface

**GeminiGen.ai / Nano Banana Pro (Not for Noctua backend)**
- $0.134/image vs $0.04 — 3x cost penalty
- No reliable image conditioning
- Consumer wrapper, unstable API
- Use existing tokens for personal cover experimentation only
- Nano Banana's text rendering is better than FLUX but irrelevant since typography is handled separately in TextStudio

### Provider Architecture
The abstract provider base (`t2i_providers/base.py`) already supports multiple providers. Implementation:
- `flux_provider.py` → fal.ai (primary, implement in new Phase 9)
- `dalle_provider.py` → OpenAI DALL-E (already planned as fallback)
- `leonardo_provider.py` → Leonardo API (add as future secondary)
- `abstract_provider.py` → stub (keep for testing without API keys)

---

## 8. Typography / TextStudio Decision

**Approach: Browser-side compositing (Option B)**
- After FLUX generates cover image, user goes to TextStudio
- Browser canvas renders generated image + title/author text overlay
- User selects from curated genre-appropriate font library
- Drag-to-reposition text elements
- Smart placement: detect negative space zones in generated image and suggest placement
- Export: flatten to PNG, download button
- No backend round-trip for typography — pure frontend canvas

**Complexity:** ~3–4 days of frontend work
**Phase:** Phase 13 (TextStudio component, already planned)

---

## 9. Copyright Handling for Cover References

**Policy decision:**
- Cover reference images from third parties → **I2T text path only** (never passed as direct FLUX Kontext conditioning)
- Only the *extracted text prompt* is used downstream, not the image itself
- Style elements in extracted text (dark background, golden objects, Art Nouveau) are not copyrightable expressions
- If user uploads their OWN cover or has rights → offer image conditioning as explicit opt-in (premium future feature)
- Artefact/character/location references from Visual Bible → direct image conditioning is fine (user selected/owns or licensed)

**User-facing framing:** "Use this cover as a style reference" → always routes through I2T
**Never:** Direct image-to-image conditioning of third-party book covers

---

## 10. Outstanding Decisions Before Implementation Plan

The following were still being considered when this session ended. Raise and resolve these at the start of the next session before writing the plan:

1. **Phase numbering reset or continuation?** The old plan goes Phase 7–16. Does the new plan restart numbering from 8 (continuing from Phase 7 complete) or renumber everything cleanly?

*Noctua Product manager says: use the previous plan, keep the phases 1-7 as they are, update the rest, renumbering from phase 8*

2. **Frontend phases 10, 11, 12 — build status clarification needed.** The architecture diagram noted that the module summary table conflated "backend functionality exists" with "frontend page is built." Phases 10 (SetupPage/WorkflowNav refactor), 11 (AnalysisReviewPage + Cover Brief Editor), 12 (MoodBoardPage) are all NOT yet built on the frontend. These need to be clearly scoped in the new plan.

3. **Where exactly does I2T trigger in the user flow?** Two options discussed: (a) triggers automatically when user selects/uploads any image in the cover tab of Moodboard, or (b) explicit "Analyse style" button. Decision needed for Phase 12 scope.

4. **Illustration pipeline scope in the new plan.** Should the new implementation plan include a future-scoped illustration generation phase as a placeholder, or leave it entirely out and add it in a later planning session?

5. **Cover Brief Editor — how much control to expose?** Currently planned as: cover type selector + primary element selector + assembled prompt preview (editable). Does the I2T pivot change what's shown here? User should probably see the I2T style template separately from the entity substitution result.

---

## 11. Key Files to Reference in New Session

- `noctua_architecture.jsx` — full architecture diagram (React, interactive, click for details)
- `docs/codebase_snapshot.md` — current backend state (phases 1–7)
- `docs/frontend_code_snapshot.md` — current frontend state
- `Noctua_Implementation_Plan_Merged.md` — old plan (phases 7–16, now to be superseded)
- `serper_test_raw.json` — full Serper test results
- `serper_test_report.txt` — human-readable Serper test report
- `test_serper.py` — Serper test script (for reference when writing serper_provider.py)

---

## 12. Prompt for New Session

Paste this at the start of a new Claude conversation after uploading this document and `noctua_architecture.jsx`:

---

*"I'm continuing work on the Noctua project (AI book cover and illustration platform). The attached context summary document captures all architectural decisions, research findings, and strategic pivots from a prior session. The `noctua_architecture.jsx` file is the companion architecture diagram — please read both before responding.*

*The project documentation is in my project knowledge (codebase_snapshot.md, frontend_code_snapshot.md, Noctua_Implementation_Plan_Merged.md).*

*I need you to:*
*1. Confirm you have absorbed the context summary*
*2. Suggest to user to generate the script to test the prompt engineering-i.e. merging the reverse engineered I2T prompt with the Noctua entities prompt*
*3. Ask me to resolve the 5 outstanding decisions listed in Section 10*
	1. Ask user if he wants to explore the text encoder/CLIP functionality and its use in Noctua
*3. Then generate the new Noctua Implementation Plan that supersedes Noctua_Implementation_Plan_Merged.md*
*4. Guide user to define the 'simple' and 'pro' versions of Noctua app - to not overexpose the key component engines, such as prompt buiding pipeline. Essentially, idea to explore if 'simple' version allows user less control and 'pro' version allows user more control. Can pricing be associated with that?*
*5. Guide user by asking questions to create a competitive analysis of Noctua vs. 'content factories in N8N' or manual creation of book cover by going through the steps that Noctua automates in its pipeline. Identify other ways to execute the user journey of cover creation and analyse Noctua's strong and weak sides against it. Purpose of this is to hone Noctua's positioning*

*The new plan must: reflect Phases 1–7 as complete, incorporate the I2T pipeline, Prompt Engineering Service, Serper provider, fal.ai T2I integration, and TextStudio typography module. Keep the Cursor Composer format (scope, files touched, instructions, tests, dependency) that the existing plan uses."*
