# Noctua — Cover Flow Fix Plan
## Cursor Composer Sessions · 13 Fixes · 3 Sessions

**Status:** Ready for Cursor Composer implementation  
**Scope:** Cover-only (Simple tier) flow end-to-end  
**Dependencies:** Sessions must run in order A → B → C

---

## How to use this plan

Paste the **Cursor Composer Preamble** at the start of each session,
then paste the full session block below it.
Wait for Composer to declare its plan before confirming "go ahead".

---

## Cursor Composer Preamble (paste at top of EVERY session)

```
You are implementing fixes for a project called Noctua (AI book cover generation tool).
Read docs/codebase_snapshot.md and docs/frontend_code_snapshot.md before touching any file.

PROCESS — follow in order, no exceptions:

STEP 1 — READ BEFORE YOU WRITE
Read the full fix block below. Read the relevant sections of codebase_snapshot.md
for every file you will modify. Do not begin until reading is complete.

STEP 2 — DECLARE YOUR PLAN
Before writing code, tell me:
- Every file you will CREATE (with purpose)
- Every file you will MODIFY (with exact summary of what changes)
- Every assumption you are making
- Any conflict with existing code

Stop and wait for "go ahead" before writing implementation code.

STEP 3 — IMPLEMENT IN ORDER
Work through fixes in the order listed. Complete each fully before moving to the next.

STEP 4 — MATCH EXISTING CONVENTIONS
Match code style exactly: TypeScript component structure, hook patterns, axios conventions,
Python import ordering, type annotation style, error handling patterns.

STEP 5 — DO NOT BREAK EXISTING FUNCTIONALITY
Never delete existing code paths. The full_book / Pro path must remain fully intact.
All changes to shared components must be conditional on analysisMode or workflowType.

STEP 6 — SESSION REPORT
When done, produce:
--- SESSION COMPLETE ---
Files created: [list]
Files modified: [list with one-line description of what changed]
Deviations from plan: [describe or "none"]
Known issues: [describe or "none"]
```

---

## SESSION A — Backend Fixes
**Files touched:** `ai_service.py`, `i2t_analysis_service.py`, `backend/.env`
**Run first. No frontend changes in this session.**

---

### Fix A1 — I2T Prompt: COVER_EXTRACTION_SYSTEM_PROMPT

**File:** `backend/app/services/i2t_analysis_service.py`
**What:** Replace the entire `COVER_EXTRACTION_SYSTEM_PROMPT` string with the improved version below.
The current prompt instructs the model to "reverse-engineer visual style" — this produces academic
descriptions. The new prompt frames the task as writing a Stable Diffusion generation prompt,
which produces the comma-separated visual tokens the downstream pipeline needs.

**Replace this (lines ~10–41, the full COVER_EXTRACTION_SYSTEM_PROMPT triple-quoted string):**
```python
COVER_EXTRACTION_SYSTEM_PROMPT = """You are an expert at reverse-engineering the visual style
of book cover images for use in AI image generation. Analyse the provided cover image and
extract its style as a structured JSON object.
...
"""
```

**With this:**
```python
COVER_EXTRACTION_SYSTEM_PROMPT = """You are an expert at writing Stable Diffusion prompts
from reference images. Analyse the provided book cover image and describe it as a
Stable Diffusion generation prompt — the kind a professional concept artist would use
to recreate the same visual style, atmosphere, and composition.

Rules:
- DO NOT include any typography, text, titles, author names, or lettering in your output
- DO NOT include specific character identities, real names, or trademarked elements
- Focus ONLY on what makes this image visually reproducible: artistic style,
  composition, lighting, color, atmosphere, and rendering technique
- Use comma-separated descriptor tags in style_template — exactly as you would
  write a Stable Diffusion prompt (e.g. "dark fantasy illustration, hooded figure,
  misty forest, moonlit, Art Nouveau border, teal and gold palette, cinematic lighting,
  8k, bokeh background, dramatic upward angle")

Extract and return ONLY valid JSON matching this schema:
{
  "style_template": "<Stable Diffusion prompt string — comma-separated descriptors, no text/typography>",
  "composition_notes": "<one sentence: subject placement, foreground/background layers, camera angle>",
  "color_palette_extracted": {
    "dominant": "<primary color name or hex>",
    "accent": "<accent color name or hex>",
    "temperature": "warm | cool | neutral",
    "contrast": "high | medium | low"
  },
  "style_tags": ["<art style tag>", "<rendering technique>", "<art movement if applicable>"],
  "mood_keywords": ["<emotional tone>", "<atmosphere descriptor>"],
  "lighting_description": "<light source, direction, and mood contribution>"
}"""
```

**Do not change any other code in this file in this step.**

---

### Fix A2 — I2T Prompt: ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT

**File:** `backend/app/services/i2t_analysis_service.py`
**What:** Replace `ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT` with the improved version.
This prompt is used for Phase 17 (future illustration pipeline) but should be updated
now while we are in the file. Same SD-framing principle as A1.

**Replace the entire ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT string with:**
```python
ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT = """You are an expert at writing Stable Diffusion
prompts from illustrated book scenes. Analyse the provided image and describe it as a
Stable Diffusion generation prompt — the kind a professional concept artist would use
to recreate the same scene composition, atmosphere, and visual style.

Rules:
- DO NOT include any typography, text, captions, or lettering
- DO NOT include specific character names or trademarked elements
- Focus on: scene depth, character-environment relationship, action staging,
  lighting mood, color narrative role, compositional layers
- Use comma-separated descriptor tags in style_template — exactly as you would
  write a Stable Diffusion prompt (e.g. "fantasy illustration, young woman reading,
  candlelit library, warm amber glow, towering bookshelves, dust particles, detailed,
  painterly, cinematic composition, shallow depth of field")

Extract and return ONLY valid JSON matching this schema:
{
  "style_template": "<Stable Diffusion prompt string — comma-separated descriptors>",
  "composition_notes": "<one sentence: scene depth, subject placement, action staging>",
  "color_palette_extracted": {
    "dominant": "<primary color name or hex>",
    "accent": "<accent color name or hex>",
    "temperature": "warm | cool | neutral",
    "contrast": "high | medium | low"
  },
  "style_tags": ["<illustration style>", "<rendering technique>", "<art movement if applicable>"],
  "mood_keywords": ["<emotional tone>", "<narrative atmosphere>"],
  "lighting_description": "<light source, direction, and contribution to scene mood>"
}"""
```

---

### Fix A3 — Character extraction: lift 5-character cap for simple mode

**File:** `backend/app/services/ai_service.py`
**What:** In simple (cover_only) mode, the consolidation prompt caps characters at 5.
For cover generation, the author needs ALL characters to be extracted so they can choose
the right one for the cover. Add a simple-mode variant of the consolidation call.

**Step A3.1 — Add constant after existing MAX_MAIN_CHARACTERS:**
```python
MAX_MAIN_CHARACTERS = 5
MAX_MAIN_LOCATIONS = 5
# Simple mode: extract all characters (no cap) so author can select any for cover
MAX_MAIN_CHARACTERS_SIMPLE = 10
```

**Step A3.2 — Add CONSOLIDATION_PROMPT_SIMPLE after existing CONSOLIDATION_PROMPT:**

Copy the full existing `CONSOLIDATION_PROMPT` string into a new variable named
`CONSOLIDATION_PROMPT_SIMPLE`. In the new variable, change only these two lines:

Old text in prompt: `"1. Top 5 MAIN CHARACTERS (most frequently mentioned, most important to plot; pick consistently by mention frequency to reduce variance between re-runs)"`

New text: `"1. ALL MAIN CHARACTERS — extract every named character who appears more than once (no limit; cover generation requires the full cast). Mark the single most important protagonist as is_main: true, all others as is_main: false."`

All other content of the prompt remains identical.

**Step A3.3 — Update `consolidate_results()` to accept analysis_mode:**

Change signature:
```python
def consolidate_results(
    all_batch_results: list[dict],
    is_well_known_book: bool = False,
    run_id: Optional[str] = None,
    analysis_mode: str = "pro",   # ADD THIS PARAMETER
) -> dict:
```

Inside `consolidate_results()`, select which prompt to use:
```python
prompt = CONSOLIDATION_PROMPT_SIMPLE if analysis_mode == "simple" else CONSOLIDATION_PROMPT
```

Use `prompt` in the `messages` list instead of the hardcoded `CONSOLIDATION_PROMPT`.

**Step A3.4 — Pass analysis_mode into consolidate_results from run_full_analysis:**

`run_full_analysis()` already receives `analysis_mode` implicitly via the caller.
Check the call site of `consolidate_results()` inside `run_full_analysis()` and add
the `analysis_mode` parameter. If `run_full_analysis` does not currently accept
`analysis_mode`, check the books router to see how analysis_mode is passed through.
Do NOT add a parameter to `run_full_analysis` if it is not already there — instead
read it from the book object that is available in the calling context.

**Success criteria for A3:**
- Simple mode analysis returns up to 10 characters
- Pro mode analysis still returns max 5 characters
- No change to location extraction in either mode
- Existing tests in `test_analysis_branch.py` still pass

---

### Fix A4 — Add FAL_API_KEY to .env

**File:** `backend/.env`
**What:** Add the FAL_API_KEY entry. This is required for FLUX Kontext cover generation.
Without this key, `flux_provider.py` fails silently and the DALL-E fallback runs
(which also needs OPENAI_API_KEY to be set).

**Add this line to backend/.env:**
```
FAL_API_KEY=your_fal_api_key_here
```

**Note for developer:** Get the key from https://fal.ai/dashboard → API Keys.
The DALL-E fallback (`dalle_provider.py`) will activate automatically if FAL_API_KEY
is absent but OPENAI_API_KEY is set. For production, FAL_API_KEY is preferred
(FLUX Kontext Pro at $0.04/image vs DALL-E 3 HD at $0.08/image).

**Also verify:** `OPENAI_API_KEY` is present in `.env` for I2T analysis and
PromptEngineeringService. If missing, add it.

**No code changes needed — .env only.**

---

### Session A Success Checklist
- [ ] `COVER_EXTRACTION_SYSTEM_PROMPT` contains "Stable Diffusion" in the model role definition
- [ ] `ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT` contains "Stable Diffusion" in the model role definition
- [ ] Both prompts contain the rule "DO NOT include any typography, text, titles"
- [ ] `CONSOLIDATION_PROMPT_SIMPLE` exists in ai_service.py
- [ ] `consolidate_results()` accepts `analysis_mode` parameter
- [ ] Simple mode consolidation uses CONSOLIDATION_PROMPT_SIMPLE
- [ ] `FAL_API_KEY` line present in backend/.env
- [ ] No existing tests broken

---

---

## SESSION B — Frontend Critical Path
**Files touched:** `SetupPage.tsx`, `App.tsx`, `CoverBriefEditor.tsx`,
`AnalysisReviewPage.tsx`, `pages/CoverBriefPage.tsx` (new), `services/api.ts`
**Run after Session A.**

---

### Fix B1 — genre never sent to analyzeBook

**File:** `frontend/src/pages/SetupPage.tsx`
**Function:** `handleUploadSuccess(book, metadata)`
**What:** `metadata.genre` is captured but never stored in BookContext.
`analyzeBook()` sends `genre: ctx.genre || undefined` — always undefined.

**Find this block in handleUploadSuccess:**
```typescript
if (metadata?.genre) {
  ctx.setStyleCategory(genreToStyleCategory(metadata.genre));
}
```

**Replace with:**
```typescript
if (metadata?.genre) {
  ctx.setStyleCategory(genreToStyleCategory(metadata.genre));
  ctx.setGenre(metadata.genre);  // ADD THIS LINE — stores raw genre for analyzeBook
}
```

**Verify:** `ctx.setGenre` exists in BookContext. If it does not exist, add it:
in `BookContext.tsx`, add `genre` to state and a `setGenre` setter following
the existing pattern for other string state fields.

**Test:** After fix, POST /api/books/{id}/analyze body must include `"genre": "Fantasy"`
(or whatever genre was selected). Verify in browser network tab.

---

### Fix B2 — Add reference_style_template to CoverAnalysisResponse type

**File:** `frontend/src/services/api.ts`
**What:** `CoverAnalysisResponse` interface uses `[key: string]: unknown` as a catch-all,
but `reference_style_template`, `reference_image_url`, and `reference_style_notes` are
not typed. This causes type-cast hacks in CoverBriefEditor. Add them as proper typed fields.

**Find the `CoverAnalysisResponse` interface. Add these fields:**
```typescript
export interface CoverAnalysisResponse {
  id?: number;
  // ... existing fields ...
  reference_style_template?: string | null;   // ADD
  reference_image_url?: string | null;         // ADD
  reference_style_notes?: Record<string, unknown> | null;  // ADD
  [key: string]: unknown;
}
```

Do not remove `[key: string]: unknown` — it is used for updateCoverAnalysis partial patch body.

---

### Fix B3 — Create CoverBriefPage (dedicated route component)

**File:** `frontend/src/pages/CoverBriefPage.tsx` (NEW FILE)
**What:** Currently `/cover-brief` maps to `AnalysisReviewPage` in App.tsx.
In simple mode `AnalysisReviewPage` shows only the Characters tab — no Cover tab —
making `CoverBriefEditor` completely inaccessible. Create a dedicated page.

**Create `frontend/src/pages/CoverBriefPage.tsx`:**

```typescript
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { useBook } from '../context/BookContext';
import {
  getCharacters,
  getLocations,
  getArtefacts,
  getCoverAnalysis,
  type Character,
  type Location,
  type Artefact,
  type CoverAnalysisResponse,
} from '../services/api';
import CoverBriefEditor from '../components/CoverBriefEditor';

export default function CoverBriefPage() {
  const navigate = useNavigate();
  const ctx = useBook();
  const [characters, setCharacters] = useState<Character[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [artefacts, setArtefacts] = useState<Artefact[]>([]);
  const [coverAnalysis, setCoverAnalysis] = useState<CoverAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const analysisMode =
    (ctx.book && (ctx.book as { analysis_mode?: string }).analysis_mode === 'simple')
      ? 'simple'
      : 'pro';

  useEffect(() => {
    if (!ctx.book) { navigate('/'); return; }
    (async () => {
      try {
        const [chars, locs, arts, cover] = await Promise.all([
          getCharacters(ctx.book!.id),
          getLocations(ctx.book!.id).catch(() => []),
          getArtefacts(ctx.book!.id).catch(() => []),
          getCoverAnalysis(ctx.book!.id).catch(() => null),
        ]);
        setCharacters(chars);
        setLocations(locs);
        setArtefacts(arts);
        setCoverAnalysis(cover);
      } finally {
        setLoading(false);
      }
    })();
  }, [ctx.book, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-paper-cream flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-golden" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper-cream px-4 py-10">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-1">
          <h1 className="font-display text-3xl font-semibold text-charcoal">Cover Brief</h1>
          <p className="font-body text-sm text-sepia">{ctx.book?.title}</p>
          <p className="font-ui text-xs text-sepia/70 max-w-md mx-auto">
            Select your cover type and primary character. Then generate your cover concepts.
          </p>
        </div>
        {ctx.book && (
          <CoverBriefEditor
            bookId={ctx.book.id}
            analysisMode={analysisMode}
            coverAnalysis={coverAnalysis}
            characters={characters}
            locations={locations}
            artefacts={artefacts}
          />
        )}
      </div>
    </div>
  );
}
```

---

### Fix B4 — Update App.tsx routing: /cover-brief → CoverBriefPage

**File:** `frontend/src/App.tsx`
**What:** Change the route mapping for `/cover-brief` to use the new `CoverBriefPage`.

**Step B4.1 — Add import at top of App.tsx:**
```typescript
import CoverBriefPage from './pages/CoverBriefPage';
```

**Step B4.2 — Find the route for cover-brief:**
```typescript
{ path: 'cover-brief', element: <AnalysisReviewPage /> }
```

**Replace with:**
```typescript
{ path: 'cover-brief', element: <CoverBriefPage /> }
```

Do NOT remove the `/analysis-review` route — it must stay as `AnalysisReviewPage`.
Only the `cover-brief` path changes.

---

### Fix B5 — CoverBriefEditor: wire Generate Cover to actual API call

**File:** `frontend/src/components/CoverBriefEditor.tsx`
**What:** `handleGenerate()` currently only calls `navigate()`. It must call
`generateCoverConcepts()` first, then navigate. This is the root cause of
"Generate Cover does nothing".

**Step B5.1 — Add import:**
```typescript
import { generateCoverConcepts } from '../services/api';
```

**Step B5.2 — Add generating state:**
```typescript
const [generating, setGenerating] = useState(false);
const [generateError, setGenerateError] = useState<string | null>(null);
```

**Step B5.3 — Replace handleGenerate:**
```typescript
async function handleGenerate() {
  if (!bookId) return;
  setGenerating(true);
  setGenerateError(null);
  try {
    const conceptCount = isSimple ? 3 : 6;
    // Build user_instruction from coverType + primaryEntityKey
    const primaryLabel = primaryOptions.find((o) => o.key === primaryEntityKey)?.name ?? '';
    const instruction = [
      coverType ? `Cover type: ${coverType}` : '',
      primaryLabel ? `Primary element: ${primaryLabel}` : '',
    ].filter(Boolean).join('. ');

    await generateCoverConcepts(bookId, {
      concept_count: conceptCount,
      user_instruction: instruction || undefined,
    });
    navigate(`/books/${bookId}/studio/cover`);
  } catch (err) {
    console.error('Cover generation failed', err);
    setGenerateError('Cover generation failed. Please try again.');
    setGenerating(false);
  }
}
```

**Step B5.4 — Update the Generate button JSX:**
```typescript
<button
  type="button"
  onClick={handleGenerate}
  disabled={generating}
  className="px-6 py-2.5 rounded-lg font-ui font-semibold text-paper-cream
             bg-midnight hover:bg-midnight/90 transition-colors
             disabled:opacity-50 disabled:cursor-not-allowed"
>
  {generating ? (
    <span className="flex items-center gap-2">
      <Loader2 size={16} className="animate-spin" />
      Generating…
    </span>
  ) : (
    'Generate Cover'
  )}
</button>
{generateError && (
  <p className="font-ui text-xs text-red-600 mt-2">{generateError}</p>
)}
```

Add `Loader2` to the existing lucide-react import in CoverBriefEditor.tsx.

---

### Fix B6 — AnalysisReviewPage: fix CTA for simple/cover_only path

**File:** `frontend/src/pages/AnalysisReviewPage.tsx`
**What:** The bottom "Prepare reference search" button navigates to `/review-search`
for ALL modes. For `cover_only` / `simple`, the correct next step is `/mood-board`.

**Find the actions section at the bottom of the return JSX (~line 477–508).
Specifically this button:**
```typescript
<button
  onClick={handlePrepareSearch}
  disabled={searching || (selectedCharCount === 0 && ...)}
  ...
>
  ...
  Prepare reference search ({selectedCharCount + ...} entities)
</button>
```

**Replace `handlePrepareSearch` with a mode-aware version:**

First, add a new handler above the existing `handlePrepareSearch`:
```typescript
async function handleContinueMoodBoard() {
  if (!ctx.book) return;
  setSearching(true);
  try {
    // Save is_main selections before navigating
    await updateEntitySelections(ctx.book.id, {
      characters: characters.map((c) => ({
        id: c.id,
        is_main: !!charMainFlags[c.id],
      })),
      locations: [],
      artefacts: [],
    });
    navigate(`/books/${ctx.book.id}/mood-board`);
  } catch (err) {
    console.error('Failed to save selections', err);
    alert('Failed to save. Please try again.');
  } finally {
    setSearching(false);
  }
}
```

Then replace the primary CTA button to be mode-aware:
```typescript
{analysisMode === 'simple' ? (
  <button
    onClick={handleContinueMoodBoard}
    disabled={searching}
    className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg
               font-ui font-semibold text-paper-cream bg-midnight
               hover:bg-midnight/90 disabled:opacity-40 disabled:cursor-not-allowed
               transition-colors shadow cursor-pointer"
  >
    {searching ? (
      <><Loader2 size={18} className="animate-spin" />Saving…</>
    ) : (
      'Continue to Mood Board'
    )}
  </button>
) : (
  <button
    onClick={handlePrepareSearch}
    disabled={searching || (selectedCharCount === 0 && selectedLocCount === 0 && selectedArtefactCount === 0)}
    className="flex-1 flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg
               font-ui font-semibold text-paper-cream bg-midnight
               hover:bg-midnight/90 disabled:opacity-40 disabled:cursor-not-allowed
               transition-colors shadow cursor-pointer"
  >
    {searching ? (
      <><Loader2 size={18} className="animate-spin" />Saving…</>
    ) : (
      <><Search size={18} />Prepare reference search ({selectedCharCount + selectedLocCount + selectedArtefactCount} entities)</>
    )}
  </button>
)}
```

Keep `handlePrepareSearch` unchanged — it is still needed for pro/full_book path.

---

### Fix B7 — Skip StyleSelector for cover_only path

**File:** `frontend/src/pages/SetupPage.tsx`
**What:** After upload, `simple` mode users see `StyleSelector` with irrelevant
illustration fields (frequency, layout, scene count). For cover_only, go directly
to analysis.

**In `handleUploadSuccess`, after setting all context values, add:**
```typescript
// For simple/cover_only: skip StyleSelector, go directly to analysis
if (book.analysis_mode === 'simple') {
  // Set defaults for fields StyleSelector would normally collect
  ctx.setEntityTypes(['cover', 'characters']);
  ctx.setSceneCount(0);
  // Trigger analysis immediately
  setStep('analyzing');
  handleAnalyze();
  return;
}
// Pro path: show StyleSelector as before
setStep('style');
```

**Important:** `handleAnalyze` must be callable without `formValues` (it already
accepts optional `formValues?: { sceneCount: number }`). Verify this before implementing.

**Do not change the `step === 'style'` rendering block** — it must stay for pro path.

---

### Session B Success Checklist
- [ ] `ctx.setGenre(metadata.genre)` called in handleUploadSuccess
- [ ] `CoverAnalysisResponse` has typed `reference_style_template` field
- [ ] `/books/:id/cover-brief` route renders `CoverBriefPage` (not AnalysisReviewPage)
- [ ] CoverBriefPage loads coverAnalysis, characters, renders CoverBriefEditor
- [ ] "Generate Cover" calls `generateCoverConcepts()` before navigating
- [ ] "Generate Cover" shows loading state and error state
- [ ] AnalysisReviewPage simple mode shows "Continue to Mood Board" CTA → /mood-board
- [ ] AnalysisReviewPage pro mode still shows "Prepare reference search" CTA → /review-search
- [ ] Simple mode upload skips StyleSelector → goes directly to analyzing
- [ ] Pro mode upload still shows StyleSelector

---

---

## SESSION C — UI Polish & Data Fixes
**Files touched:** `AnalysisReviewPage.tsx`, `MoodBoardPage.tsx`,
multiple files for rename, `api.ts`
**Run after Session B.**

---

### Fix C1 — Character card: UX improvements

**File:** `frontend/src/pages/AnalysisReviewPage.tsx`
**Component:** `CharacterCard`

**C1.1 — Translate Russian strings to English:**

Find and replace all Russian UI labels in CharacterCard (and LocationCard if they appear there too):
- `"Онтология и визуальные данные"` → `"Visual Data"`
- `"Тип:"` → `"Type:"`
- `"Эмоции:"` → `"Emotions:"`
- `"Стиль:"` → `"Style tokens:"`
- `"Архетип:"` → `"Archetype:"`
- `"Аналог для поиска:"` → `"Search analog:"`

**C1.2 — Add Main/Secondary icon:**

In the CharacterCard view mode, replace the text "Main" badge with an icon + label:
```typescript
// Replace:
<span className="mt-0.5 flex-shrink-0 px-2 py-0.5 rounded text-xs font-ui font-medium bg-golden/20 text-golden">Main</span>

// With:
<span className="mt-0.5 flex-shrink-0 flex items-center gap-1 px-2 py-0.5 rounded text-xs font-ui font-medium bg-golden/20 text-golden">
  <Star size={12} fill="currentColor" />
  Main
</span>
```

For secondary characters (is_main = false), add a subtle secondary indicator:
```typescript
{!isMain && (
  <span className="mt-0.5 flex-shrink-0 flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-ui text-sepia/60 bg-sepia/5">
    <User size={11} />
    Secondary
  </span>
)}
```

Add `User` to lucide-react imports (it may not be imported yet — check first).

**C1.3 — Add visual token editing in edit mode:**

In the CharacterCard edit mode block (where `isEditing && onSave && onCancel`),
after the existing personality_traits input, add:
```typescript
<label className="block font-ui text-xs text-sepia">Core tokens (comma-separated)</label>
<input
  value={draft.core_tokens ?? (character.entity_visual_tokens?.core_tokens ?? []).join(', ')}
  onChange={(e) => onDraftChange?.('core_tokens', e.target.value)}
  className="w-full px-2 py-1 rounded border border-sepia/20 text-sm font-ui"
  placeholder="e.g. red-haired woman, emerald eyes, scholar's robes"
/>
<label className="block font-ui text-xs text-sepia">Style tokens (comma-separated)</label>
<input
  value={draft.style_tokens ?? (character.entity_visual_tokens?.style_tokens ?? []).join(', ')}
  onChange={(e) => onDraftChange?.('style_tokens', e.target.value)}
  className="w-full px-2 py-1 rounded border border-sepia/20 text-sm font-ui"
  placeholder="e.g. pre-Raphaelite, ethereal, painterly"
/>
```

In the `onSave` handler in `AnalysisReviewPage` (the call to `patchEntitySummaries`),
pass the token fields if present in `data`:
```typescript
await patchEntitySummaries(ctx.book.id, {
  characters: [{ 
    id: c.id, 
    ...data,
    // Convert comma strings back to arrays if present
    core_tokens: data.core_tokens 
      ? data.core_tokens.split(',').map((s: string) => s.trim()).filter(Boolean) 
      : undefined,
    style_tokens: data.style_tokens 
      ? data.style_tokens.split(',').map((s: string) => s.trim()).filter(Boolean) 
      : undefined,
  }],
  locations: [],
});
```

**Verify:** `patchEntitySummaries` backend endpoint accepts `core_tokens` and
`style_tokens` fields for characters. Check the backend schema — if not supported,
note it as a known issue in the session report (don't block on it).

**C1.4 — Clarify the "0" tab badge:**

Add `title` attribute to the tab count badge:
```typescript
<span
  title="Characters selected for reference image search"
  className={`text-xs px-1.5 py-0.5 rounded-full ${...}`}
>
  {count}
</span>
```

---

### Fix C2 — MoodBoard: fix uploaded cover disappearing + filter to selected only

**File:** `frontend/src/pages/MoodBoardPage.tsx`
**What:** Two related issues:
(a) Uploaded cover image disappears when user returns to Mood Board
(b) All cover search results shown instead of only selected ones

**C2.1 — Filter cover images to selected only:**

Find the line where `setCoverImages` is called after `getCoverImages(refs)`:
```typescript
const cover = getCoverImages(refs);
setCoverImages(cover);
```

Replace with a filter that only shows selected covers:
```typescript
const cover = getCoverImages(refs);
// Only show covers that were explicitly selected or uploaded
const selectedCovers = cover.filter(
  (img) => (img as ReferenceImageItem & { is_selected_for_reference?: number }).is_selected_for_reference === 1
    || (img as ReferenceImageItem & { source?: string }).source === 'upload'
);
setCoverImages(selectedCovers.length > 0 ? selectedCovers : cover);
```

Note: if `ReferenceImageItem` does not have `is_selected_for_reference` field,
check the type in api.ts and add it. The fallback `cover` ensures the grid
never shows completely empty when no selections have been made yet.

**C2.2 — Refresh cover images after upload:**

The upload handler `handleUploadCoverRef` already calls `getReferenceResults` and
`getCoverImages` after upload. Verify it also refreshes with the same filter from C2.1.
If the upload returns the image in the refs result, the filter should handle it.
If not (image is missing from reference-results after upload), add the uploaded image
directly to state as a fallback:

```typescript
async function handleUploadCoverRef(file: File) {
  if (!id || coverAnalysisId == null) return;
  setUploading(true);
  try {
    const uploaded = await uploadReferenceImage(id, 'cover', coverAnalysisId, file);
    // Refresh from server
    const refs = await getReferenceResults(id);
    const cover = getCoverImages(refs);
    // Apply selection filter; if uploaded image not in refs, prepend it directly
    const filtered = cover.filter(
      (img) => (img as any).is_selected_for_reference === 1 || (img as any).source === 'upload'
    );
    if (filtered.length === 0 && uploaded?.url) {
      // Server did not return the uploaded image yet — show it directly from upload response
      setCoverImages([uploaded, ...cover.slice(0, 2)]);
    } else {
      setCoverImages(filtered.length > 0 ? filtered : cover);
    }
    ctx.setReferenceImages(refs);
  } catch {
    setErrorToast('Upload failed. Please try again.');
  } finally {
    setUploading(false);
  }
}
```

---

### Fix C3 — Rename YRead/StoryForge → Noctua throughout codebase

**Files touched:**
- `frontend/index.html`
- `frontend/package.json`
- `frontend/src/App.tsx` (page title, meta)
- `frontend/src/services/api.ts` (localStorage key)
- `backend/app/main.py` (FastAPI app title)
- `docs/codebase_snapshot.md` (header line)
- `docs/frontend_code_snapshot.md` (header line)

**Replacements:**

| Find | Replace |
|------|---------|
| `YRead` | `Noctua` |
| `StoryForge AI` | `Noctua` |
| `StoryForge` | `Noctua` |
| `yread_enabled_providers` (in api.ts ENABLED_PROVIDERS_STORAGE_KEY) | `noctua_enabled_providers` |
| `yread_user_plan` (if in AuthContext localStorage key) | `noctua_user_plan` (already done per AuthContext.tsx code) |

**In index.html:** Update `<title>` and any `<meta>` description tags.
**In package.json:** Update `"name"` field if it contains yread or storyforge.
**In main.py:** Update `FastAPI(title="...")` parameter.

**Important:** Do NOT change the localStorage key `noctua_user_plan` in AuthContext.tsx
— it already uses `noctua_user_plan` (confirmed in code review). Only change the
`yread_enabled_providers` key in api.ts.

---

### Session C Success Checklist
- [ ] CharacterCard shows "Main" with Star icon, "Secondary" with User icon
- [ ] CharacterCard edit mode has core_tokens and style_tokens inputs
- [ ] All Russian strings replaced with English in CharacterCard
- [ ] Tab count badge has tooltip text
- [ ] Mood Board shows only selected cover images (not full search results)
- [ ] Uploaded cover image persists on return to Mood Board
- [ ] No occurrence of "YRead" or "StoryForge" in HTML, JSON, or Python source files
- [ ] `ENABLED_PROVIDERS_STORAGE_KEY` = `'noctua_enabled_providers'` in api.ts

---

---

## Fix Priority Reference (for triage if sessions are split)

| Fix | Session | Priority | Blocks | Description |
|-----|---------|----------|--------|-------------|
| A1 | A | P1 | cover quality | I2T prompt: Stable Diffusion framing for cover |
| A2 | A | P2 | future | I2T prompt: Stable Diffusion framing for illustrations |
| A3 | A | P2 | char selection | Lift 5-character cap in simple mode |
| A4 | A | **P0** | ALL generation | Add FAL_API_KEY to .env |
| B1 | B | P1 | cover quality | genre sent to analyzeBook |
| B2 | B | P3 | type safety | CoverAnalysisResponse typed fields |
| B3 | B | P1 | CoverBriefEditor access | New CoverBriefPage.tsx |
| B4 | B | P1 | CoverBriefEditor access | App.tsx routing fix |
| B5 | B | **P0** | generation | Generate Cover calls API |
| B6 | B | P1 | navigation | Analysis review CTA simple path |
| B7 | B | P2 | UX | Skip StyleSelector for simple |
| C1 | C | P2 | UX | Character card improvements |
| C2 | C | P2 | UX | MoodBoard cover filter |
| C3 | C | P3 | brand | Rename to Noctua |

**P0 = must fix for any cover to generate**
**P1 = must fix for correct user flow**
**P2 = important UX improvement**
**P3 = polish / housekeeping**

---

## Notes for developer before starting

1. **FAL_API_KEY first** — without it no cover generation works regardless of code fixes.
   Get key from https://fal.ai/dashboard before running Session B tests.

2. **Session order matters** — Session B Fix B5 (Generate button) will fail end-to-end
   without A4 (FAL key). But the code change itself can be done in any order.

3. **Test the cover path end-to-end after Session B** before starting Session C.
   The critical path is: Upload → Analysis Review → Mood Board → Cover Brief → Generate → Studio.

4. **Do not run Sessions concurrently** — they modify overlapping files.

5. **Context window warning:** If this plan is pasted into a single Cursor session,
   it may exceed context limits. Use one session block per Cursor Composer conversation.
