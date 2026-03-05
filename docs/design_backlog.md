# Noctua — Design Backlog
> Living document. Do not delete entries — change status to Done when built.
> Add to project knowledge so Cursor Composer can reference during implementation.

---

## IDEA-001
**Status:** Planned (Phase 8b)
**Area:** Analysis Pipeline
**Summary:** Book-level author focus hint
**Detail:** Optional free-text field on the SetupPage that biases the entire analysis towards a specific theme or aspect the author wants to emphasise. Example: the book is a detective novel but the author wants Noctua to focus on its nostalgic undercurrent. The hint is injected into `extract_thematic_material()`, `synthesise_cover_brief()`, and `scene_extractor.extract_scenes()` prompts. Scenes and entities that match the hinted theme are weighted/surfaced more prominently.
**UX placement:** SetupPage, below genre selector. Optional text input labelled: *"What should Noctua focus on? (optional)"* with placeholder: *e.g. "nostalgic mood", "father-daughter relationship", "isolation theme"*
**Backend changes:**
- `books.author_focus_hint TEXT` — one migration line
- `AnalyzeRequest` schema: `author_focus_hint: str | None`
- `extract_thematic_material()` — inject hint into prompt
- `synthesise_cover_brief()` — inject hint into prompt
- `scene_extractor.extract_scenes()` — weight hint-matching scenes higher
**Phase target:** 8b (backend) + 10 (UI input on SetupPage)
**Dependencies:** Phase 8a complete
**Effort estimate:** Small

---

## IDEA-002
**Status:** Planned (Phase 11)
**Area:** Analysis Review UI
**Summary:** Entity-level refinement hint with inline token regeneration
**Detail:** On the AnalysisReviewPage, each entity card (Character, Location, Artefact) shows a small optional text input below the AI-generated description. Author can type a directive to steer token regeneration without triggering a full re-analysis. Example: character description reads *"Last generation of genetic clones, weaker and less resilient..."* — author types *"Emphasise physical frailty and genetic deterioration"* and clicks Regenerate. Only that entity's visual tokens are regenerated. The description text itself is preserved unless the author also edits it manually.
**UX pattern:** Inline annotation — input field + "Regenerate tokens ↺" button per entity card. Not a chat UI. Single-turn directive.
**UI sketch:**
```
┌─────────────────────────────────────────────────────┐
│ CLONE SEVEN                                          │
│ Last generation of genetic clones, weaker and       │
│ less resilient, appears less intelligent...          │
│                                                     │
│ ✏ Refine visual focus (optional):                   │
│ [Emphasise physical frailty and deterioration    ]  │
│                              [Regenerate tokens ↺]  │
└─────────────────────────────────────────────────────┘
```
**Applies to:** Characters, Locations, Artefacts (all four entity types equally)
**Backend changes:**
- `analyzeEntity` endpoint already exists — add optional `refinement_hint: str | None` param
- Pass hint into entity-specific analysis prompt as a directive prefix
**Phase target:** Phase 11 (AnalysisReviewPage frontend + minor backend endpoint param)
**Dependencies:** Phase 8a, existing `analyzeEntity` endpoint
**Effort estimate:** Small — existing re-analyse hook already present

---

## IDEA-003
**Status:** Backlog (Phase 14+)
**Area:** UX / Onboarding
**Summary:** Conversational summary screen post-analysis
**Detail:** After analysis completes, instead of routing directly to the Analysis Review tab wall, show a single "Noctua has read your book" summary screen. Noctua narrates what it found in a friendly voice, surfacing the top characters, primary location, notable artefacts, and overall tone. Ends with two clear CTAs: [Create a cover] [Extract scenes for illustrations]. "Review full analysis" is a secondary link. This is NOT a chat UI — it is a static summary screen assembled from existing entity DB data. No vectorisation or new backend work required.
**UX value:** Reduces cognitive load at the most complex step in the current flow. Makes the product feel intelligent rather than bureaucratic.
**Backend changes:** None — data already exists in entity DB post-analysis
**Frontend changes:** New `AnalysisSummaryPage.tsx` — single screen between SetupPage and AnalysisReviewPage
**Phase target:** Phase 14 or as a Phase 11 addition
**Dependencies:** Phase 11 (AnalysisReviewPage must exist as the destination)
**Effort estimate:** Small-Medium (frontend only)

---

## IDEA-004
**Status:** Backlog (Phase 15+)
**Area:** Semantic Search / Advanced Features
**Summary:** Chunk-level semantic search via pgvector (future)
**Detail:** Vectorise manuscript chunks using `text-embedding-3-small` and store as `chunks.embedding vector(1536)` with pgvector. Enables semantic queries like *"find the most visually dramatic scene with Elena in an outdoor setting"* without scanning all chunks via LLM. Only relevant if a "chat with your manuscript" or scene-level semantic search feature is built.
**Why not now:** Current pipeline reads every chunk exhaustively — vectorisation adds no speed or accuracy benefit to existing extraction. Bottleneck is OpenAI API latency, not DB reads.
**Cost when built:** ~$0.02 per 1M tokens via text-embedding-3-small — negligible for book-sized manuscripts.
**Phase target:** Phase 15+ / only if scene semantic search is scoped
**Dependencies:** pgvector on Railway, embedding budget approved
**Effort estimate:** Medium (new infra dependency)

---

## Tracking Notes

### How to add entries
- Increment ID sequentially (IDEA-005, IDEA-006...)
- Status lifecycle: `Backlog` → `Planned (Phase X)` → `In Progress` → `Done`
- When marking Done, add: `**Built in:** Phase X, commit/PR reference`

### How to use with Cursor Composer
At the start of a new implementation session, paste the relevant IDEA entries alongside the phase content. Cursor will treat them as additional scope context.
