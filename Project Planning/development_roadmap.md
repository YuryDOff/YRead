# Development Roadmap: AI-Powered Book Reading Application
## "Reading Reinvented" - Implementation Guide for Cursor IDE

**Version:** 1.0 MVP  
**Date:** February 7, 2026  
**Last Updated:** February 7, 2026  
**Development Approach:** Vibe-coding with AI assistance  
**Estimated Total Time:** 40-60 hours (10-15 development sessions)

---

## 📊 Current Status Overview

### Completed Phases
- ✅ **Phase 1: Backend Foundation** (100% complete)
  - All backend services implemented: book import, chunking, AI analysis, reference search
  - Database models and CRUD operations functional
  - All API endpoints operational
- ✅ **Phase 2: Frontend Core UI** (100% complete)
  - All core UI components built: BookUpload, StyleSelector, VisualBibleReview, BookReader
  - React Router navigation implemented
  - BookContext for state management
- ✅ **Bug Fixes BF-1 to BF-4** (100% complete)
  - Idempotent re-analysis, continue reading, search optimization, analysis decoupling

### In Progress
- ⚠️ **Phase 3: Image Generation Integration** (0% - not started)
- ⚠️ **Phase 4: Integration & Polish** (50% - routing and state management done, needs error boundaries and polish)
- ⚠️ **BF-5: UI/UX Improvements** (33% - 2 of 6 items completed)

### Not Started
- ❌ **Phase 5: Deployment**
- ❌ **Phase 6: Documentation**

### 🔄 Strategic Pivot Planned
**B2B Author Platform**: A strategic pivot to target self-publishing authors (instead of readers) is planned. See `b2b_author_pivot_plan_94e78ef5.plan.md` for details. This roadmap reflects the **current B2C (reader-focused) implementation**.

---

## Overview

This roadmap provides a step-by-step implementation plan optimized for development using **Cursor IDE** with AI assistance. Each phase includes specific prompts you can use with Cursor's AI to accelerate development.

---

## Development Environment Setup

### Prerequisites Checklist
- [x] Cursor IDE installed and configured
- [x] Python 3.10+ installed
- [x] Node.js 18+ and npm installed
- [x] Git installed
- [x] API Keys obtained:
  - [x] OpenAI API key (for GPT analysis)
  - [x] GeminiGen API key (for image generation)
  - [x] SerpAPI key (for reference image search)

### Project Structure
```
reading-reinvented/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI application
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── database.py          # Database connection
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── book_service.py       # Book import & processing
│   │       ├── ai_service.py         # GPT analysis
│   │       ├── image_service.py      # Image generation
│   │       └── search_service.py     # Reference image search
│   ├── requirements.txt
│   ├── .env                     # Environment variables
│   └── alembic/                 # Database migrations (optional for MVP)
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── BookUpload.jsx
│   │   │   ├── StyleSelector.jsx
│   │   │   ├── VisualBibleReview.jsx
│   │   │   ├── BookReader.jsx
│   │   │   └── LoadingScreen.jsx
│   │   ├── pages/
│   │   │   ├── HomePage.jsx
│   │   │   ├── SetupPage.jsx
│   │   │   └── ReadingPage.jsx
│   │   ├── services/
│   │   │   └── api.js           # API client
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
└── README.md
```

---

## Phase 1: Backend Foundation (8-12 hours) ✅ COMPLETED

### 1.1 Project Initialization (1 hour) ✅

**Tasks:**
1. Create project directory structure
2. Initialize backend Python virtual environment
3. Initialize frontend with Vite + React
4. Set up version control (Git)

**Cursor Prompts:**
```
"Create a FastAPI backend project structure with the following:
- Main application file
- SQLAlchemy models for books, chunks, characters, locations, visual_bible, illustrations
- Database connection setup with SQLite
- Basic health check endpoint
Include requirements.txt with FastAPI, SQLAlchemy, pydantic, python-dotenv"

"Create a React + Vite frontend project with:
- Tailwind CSS configured
- Basic routing setup (react-router-dom)
- API client service using axios
- Component structure for BookUpload, StyleSelector, BookReader"
```

**Files to Create:**
- `backend/requirements.txt`
- `backend/.env.example`
- `backend/app/main.py`
- `backend/app/database.py`
- `frontend/package.json`
- `frontend/tailwind.config.js`

**Validation:**
- [x] Backend runs with `uvicorn app.main:app --reload`
- [x] Frontend runs with `npm run dev`
- [x] Health check endpoint returns 200

---

### 1.2 Database Models & Schema (2 hours) ✅

**Tasks:**
1. Define SQLAlchemy models matching requirements doc
2. Create database initialization script
3. Add CRUD utility functions

**Cursor Prompts:**
```
"Create SQLAlchemy models based on this schema:
[Paste the database schema from requirements doc section 4.1]
Include relationships, indexes, and timestamps. Use SQLite-compatible data types.

IMPORTANT: Add junction tables for many-to-many relationships:
- chunk_characters: links chunks to characters that appear in them
- chunk_locations: links chunks to locations that appear in them
These enable efficient querying like 'find all chunks with Character X' for illustration generation."

"Write a database initialization function that:
- Creates all tables
- Adds indexes for performance
- Includes sample seed data for testing
Put this in database.py"
```

**Files to Create:**
- `backend/app/models.py` (Books, Chunks, Characters, Locations, VisualBible, Illustrations, ReadingProgress, ChunkCharacters, ChunkLocations)
- `backend/app/crud.py` (Helper functions for database operations)

**Validation:**
- [x] Database file created in `backend/app.db`
- [x] All tables exist with correct schema
- [x] Can insert and query test data

---

### 1.3 Google Drive Import Service (2 hours) ✅

**Tasks:**
1. Implement Google Drive link parser
2. Download text file from shareable link
3. Save to local filesystem and database

**Cursor Prompts:**
```
"Create a book import service that:
1. Takes a Google Drive shareable link (format: https://drive.google.com/file/d/FILE_ID/view)
2. Converts it to direct download link
3. Downloads the file using requests library
4. Saves text content to database
5. Returns book_id and metadata (title, word count, estimated pages)
Handle errors: invalid link, file not found, network issues"

"Add an API endpoint POST /api/books/import that:
- Accepts google_drive_link in request body
- Calls the import service
- Returns book details or error
- Include rate limiting (1 request per 10 seconds)"
```

**Files to Create:**
- `backend/app/services/book_service.py`
- API endpoint in `backend/app/main.py`

**Validation:**
- [x] Successfully downloads text file from Google Drive
- [x] Book saved to database with correct metadata
- [x] Error handling works for invalid links
- [x] Added file format validation (BF-5.3) - rejects non-.txt files with user-friendly error

---

### 1.4 Text Chunking Service (2 hours) ✅

**Tasks:**
1. Implement intelligent chunking algorithm
2. Calculate overlap between chunks
3. Store chunks in database with metadata

**Cursor Prompts:**
```
"Create a text chunking function that:
- Takes book text as input
- Splits into chunks of ~2000 tokens (~1500 words)
- Creates 200-token overlap between chunks
- Respects paragraph boundaries when possible
- Calculates chunk position (start/end page numbers, assuming 300 words per page)
- Returns list of chunk objects with: chunk_index, text, start_page, end_page, word_count
Use tiktoken library for token counting (GPT-3.5-turbo encoding)"

"Create database function to save chunks:
- Batch insert all chunks for a book
- Calculate total chunks and pages
- Update book status to 'chunked'
- Add transaction handling for atomicity"
```

**Files to Create:**
- Update `backend/app/services/book_service.py` with chunking logic

**Validation:**
- [x] 500-page book produces ~50-60 chunks
- [x] Overlaps are correct
- [x] Chunks stored in database with correct metadata
- [x] Page number calculations accurate

---

### 1.5 OpenAI Analysis Service (3 hours) ✅

**Tasks:**
1. Implement batch analysis with GPT API
2. Extract characters, locations, tone
3. Consolidate results
4. Stay within $0.50 budget

**Cursor Prompts:**
```
"Create an AI analysis service using OpenAI GPT-3.5-turbo that:

FIRST PASS (per batch of 10-15 chunks):
- Combines chunk text into single context
- Sends to GPT with this prompt structure:
  'Analyze this book excerpt and extract:
   1. All characters mentioned (name, physical description, personality)
   2. All locations mentioned (name, visual description, atmosphere)
   3. Most dramatic/visual moment in this section (for illustration)
   4. For each chunk in this batch, tag which characters and locations appear
   Return as JSON with structure: {characters: [], locations: [], dramatic_moments: [], chunk_tags: []}'
- Uses JSON mode for structured output
- Tracks token usage

SECOND PASS (consolidation):
- Takes all batch results
- Sends consolidation prompt to identify top 5 characters and 5 locations
- Generates overall tone and style summary

THIRD PASS (chunk enrichment):
- Updates each chunk record with character_ids and location_ids
- Creates relationships in chunk_characters and chunk_locations junction tables
- Enables efficient querying for illustration generation

Include cost tracking to ensure <$0.50 per book
Use streaming to show progress"

"Add progress tracking:
- Emit events for: 'batch_started', 'batch_completed', 'consolidation_started'
- Calculate and return estimated completion time
- Store results in database (characters, locations tables)"
```

**Files to Create:**
- `backend/app/services/ai_service.py`
- API endpoint `POST /api/books/{book_id}/analyze`

**Important GPT Prompts to Include:**

**Batch Analysis Prompt:**
```
You are analyzing a book to extract visual and narrative elements for AI illustration generation.

Extract from this text:

1. CHARACTERS (name, detailed physical description, personality traits, typical emotions)
   - Focus on visual details: age, height, build, hair, eyes, skin, clothing style
   - Note 2 typical emotional expressions for reference image search

2. LOCATIONS (name, detailed visual description, atmosphere, time of day)
   - Focus on visual details: architecture, colors, lighting, weather, mood
   - Describe as if setting up a photoshoot

3. DRAMATIC MOMENTS (brief scene description, why it's visually interesting)
   - Select 1-2 most visual/dramatic moments from this excerpt

Return ONLY valid JSON in this exact format:
{
  "characters": [{"name": "", "physical_description": "", "personality": "", "emotions": []}],
  "locations": [{"name": "", "visual_description": "", "atmosphere": ""}],
  "dramatic_moments": [{"scene_description": "", "visual_interest_reason": ""}]
}
```

**Consolidation Prompt:**
```
Given these character and location extractions from multiple sections of a book, consolidate into:

1. Top 5 MAIN CHARACTERS (most frequently mentioned, most important to plot)
   - Merge duplicate descriptions
   - Create comprehensive physical descriptions
   - Identify 2 most characteristic emotions for each

2. Top 5 MAIN LOCATIONS (most important to story)
   - Merge duplicate descriptions
   - Create comprehensive visual descriptions

3. OVERALL TONE & STYLE
   - Genre classification
   - Narrative mood
   - Visual style recommendation for illustrations

Return ONLY valid JSON in this format:
{
  "main_characters": [...],
  "main_locations": [...],
  "tone_and_style": {"genre": "", "mood": "", "visual_style": ""}
}
```

**Validation:**
- [x] Analysis completes within 5 minutes for 500-page book
- [x] Cost < $0.50 per book (log actual cost)
- [x] Extracts 5 characters and 5 locations
- [x] Dramatic moments identified per chunk
- [x] Results saved to database correctly
- [x] Upgraded to gpt-4o-mini (128K context) to handle large books
- [x] AI marks main character and main location with is_main flag

---

### 1.6 Reference Image Search Service (2 hours) ✅

**Tasks:**
1. Integrate Bing Image Search API (or SerpAPI)
2. Generate search queries from character/location descriptions
3. Return curated image results

**Cursor Prompts:**
```
"Create a reference image search service using Bing Image Search API that:

For each CHARACTER:
1. Check if book is marked as 'well-known' (from user input during setup)
2. If well-known, generate search queries including book title/author:
   - '{character_name} {book_title}'
   - '{description} {book_title} {author}'
   - '{character_name} illustration'
3. If not well-known, use generic queries:
   - '{description} person portrait'
   - '{description} character illustration'
4. Fetch 3-5 results per query
5. Filter: safe search ON, minimum 512x512px
6. Deduplicate similar images
7. Return top 2-3 most diverse images per character

For each LOCATION:
1. Similar approach with book context if available
2. Generate 2-3 search queries based on description
3. Fetch and filter results
4. Return top 2-3 images

Include error handling for API failures
Return image URLs with metadata (width, height, source)"

"Add caching to avoid duplicate searches:
- Store search results in database for 7 days
- Check cache before making API call
- Implement cache invalidation strategy"
```

**Files to Create:**
- `backend/app/services/search_service.py`
- API endpoint `GET /api/books/{book_id}/reference-images`

**Bing Search API Setup:**
- Sign up for free tier: https://www.microsoft.com/en-us/bing/apis/bing-image-search-api
- 1000 free searches/month
- Store API key in `.env`

**Validation:**
- [x] Returns 2-3 reference images per character
- [x] Returns 2-3 reference images per location
- [x] Uses book title/author (always included in queries, not just for well-known books)
- [x] Images are appropriate and diverse
- [x] Handles API failures gracefully
- [x] Search queries logged to search_queries table for review
- [x] Main-only search mode reduces API calls from ~20 to ~5
- [x] Placeholder images for non-main entities

---

## Phase 2: Frontend Core UI (8-10 hours) ✅ COMPLETED

### 2.1 Book Upload Component (2 hours) ✅

**Tasks:**
1. Create Google Drive link input form
2. Display upload progress
3. Show book metadata after import

**Cursor Prompts:**
```
"Create a React component BookUpload.jsx with:
- Input field for Google Drive link with validation (must match pattern)
- 'Import Book' button (disabled if invalid)
- Loading spinner during upload
- Success message showing: book title, word count, estimated pages
- Error message display with retry option
- Use Tailwind CSS for styling, make it clean and modern"

"Add form validation:
- Real-time URL validation
- Show helpful error messages
- Disable submit until valid
- Clear errors on input change"
```

**Files to Create:**
- `frontend/src/components/BookUpload.jsx`
- `frontend/src/services/api.js` (API client for backend)

**Validation:**
- [x] Form validates Google Drive URLs
- [x] Shows loading state during import
- [x] Displays book metadata on success
- [x] Handles errors gracefully
- [x] Displays detailed backend error messages to user

---

### 2.2 Style Selector Component (2 hours) ✅

**Tasks:**
1. Visual style picker UI
2. Illustration frequency slider
3. Layout style selection

**Cursor Prompts:**
```
"Create a StyleSelector.jsx component with:

0. BOOK RECOGNITION QUESTION (at top):
   - Toggle or radio: 'Is this a well-known published book?' (Yes/No)
   - If Yes: Optional text input for author name
   - Help text: 'This helps us find better reference images for characters and locations'
   - Store answer to pass to backend

1. VISUAL STYLE PICKER (radio cards):
   - Non-Fiction (realistic, documentary)
   - Fiction (versatile, balanced)
   - Romance (soft, dreamy)
   - Sci-Fi (futuristic, vibrant)
   - Fantasy (epic, painterly)
   - Fairy Tale (whimsical, storybook)
   - Classic Literature (vintage, engraving-style)
   Each card has icon, label, and description
   Selected card has border highlight

2. ILLUSTRATION FREQUENCY (slider):
   - Options: 1 per 2 pages, 1 per 4 pages, 1 per 8 pages, 1 per 12 pages
   - Display calculated total illustrations
   - Show preview: 'Your book will have ~X illustrations'

3. LAYOUT STYLE (toggle):
   - Inline Classic (traditional illustrated book)
   - Anime Panels (manga-style panels)
   - Visual preview of each style

Use Tailwind CSS. Make it visually appealing and intuitive."

"Add state management:
- Track selected style, frequency, layout
- Calculate total illustrations based on book page count
- Pass selections to parent component
- Include 'Analyze Book' button that proceeds to next step"
```

**Files to Create:**
- `frontend/src/components/StyleSelector.jsx`

**Validation:**
- [x] All style options selectable
- [x] Slider works smoothly
- [x] Total illustrations calculated correctly
- [x] Layout previews are clear
- [x] Settings passed to backend API
- [x] Book recognition question implemented
- [x] Main-only reference search toggle (default ON)

---

### 2.3 Loading/Wait Screens (1 hour) ⚠️ PARTIAL

**Tasks:**
1. Analysis progress screen
2. Generation progress screen
3. Progress animations

**Cursor Prompts:**
```
"Create LoadingScreen.jsx component that shows:
- Animated progress bar or spinner
- Dynamic status messages that change based on current task
- Estimated time remaining
- Cancel option (returns to previous screen)
- Beautiful, calming animation (use Tailwind CSS animations)

Support two modes:
1. ANALYSIS MODE - messages like:
   'Analyzing narrative structure...'
   'Identifying key characters...'
   'Mapping dramatic moments...'
   'Searching reference images...'

2. GENERATION MODE - messages like:
   'Generating your personalized illustrated book...'
   'Creating illustration 3 of 5...'
   'Bringing your book to life...'

Use smooth transitions between messages"
```

**Files to Create:**
- `frontend/src/components/LoadingScreen.jsx`

**Validation:**
- [x] Smooth animations
- [ ] Progress updates in real-time (needs WebSocket or polling)
- [ ] Cancel functionality works (not implemented yet)
- [ ] Estimated time is accurate (not implemented yet)

---

### 2.4 Visual Bible Review Component (3 hours) ✅

**Tasks:**
1. Display characters with reference images
2. Display locations with reference images
3. Enable selection and approval

**Cursor Prompts:**
```
"Create VisualBibleReview.jsx component with:

LAYOUT:
- Tabs for: Characters | Locations | Style Summary
- Clean, organized grid layout

CHARACTERS TAB:
- For each character:
  - Card with character name and description
  - Grid of 2-3 reference images (radio select)
  - Selected image has checkmark overlay
  - Inline edit button for description (optional for MVP)
- Visual feedback on selection
- Show count: '3 of 5 characters selected'

LOCATIONS TAB:
- Similar layout for locations
- 2-3 reference images per location
- Same selection mechanism

STYLE SUMMARY TAB:
- Display: genre, mood, visual style, tone
- Show selected illustration style and frequency
- Preview of first few illustration prompts (if available)

FOOTER:
- 'Approve & Generate Book' button
- Disabled until all characters and locations have selections
- Shows total selected: 'Ready: 5/5 characters, 5/5 locations'

Use Tailwind CSS for beautiful, modern design
Add hover effects and smooth transitions"

"Add image preview modal:
- Click image to view full size
- Navigation between reference images
- Close on overlay click or ESC key"
```

**Files to Create:**
- `frontend/src/components/VisualBibleReview.jsx`
- `frontend/src/components/ReferenceImageGrid.jsx`
- `frontend/src/components/CharacterCard.jsx`

**Validation:**
- [x] All reference images display correctly
- [x] Selection mechanism works smoothly
- [ ] Description editing functional (deferred)
- [x] Approval button enables only when ready
- [x] Data sent to backend correctly
- [x] Added Analysis Review Page (BF-4) - decoupled from reference search

---

### 2.5 Book Reader Component (4 hours) ✅

**Tasks:**
1. Two-page spread layout
2. Page turning logic
3. Illustration rendering
4. Progress tracking

**Cursor Prompts:**
```
"Create BookReader.jsx component with:

LAYOUT (two-page spread):
- Left page and right page side-by-side
- Responsive to viewport size
- Book-like appearance (slight shadow, rounded corners, cream background)
- Page numbers in corners

TEXT RENDERING:
- Serif font (Georgia or similar)
- Max 65 characters per line
- Comfortable line height (1.6-1.8)
- Justified text alignment
- Hyphenation for clean edges

ILLUSTRATION PLACEMENT:
- Support two modes (based on user selection):
  1. INLINE CLASSIC: Full-width image within text flow
  2. ANIME PANELS: Bordered image boxes with text wrapping
- Image lazy loading
- Placeholder while loading
- Fallback for failed images

PAGE TURNING:
- Previous/Next buttons
- Keyboard navigation (arrow keys)
- Smooth page flip animation (CSS transform)
- Auto-scroll to top on page turn

NAVIGATION:
- Progress bar showing % completed
- 'Page X of Y' indicator
- Jump to page input
- Table of contents (if chapters detected)

Use Tailwind CSS for styling
Make it feel like reading a real book"

"Add reading progress tracking:
- Save current page to backend every 10 seconds
- Resume from last page on reload
- Show 'You left off on page X' message when reopening book"

"Implement illustration pre-loading:
- Track user reading speed (pages per minute)
- Request next 2-3 illustrations from backend when user is 2 illustrations away
- Show subtle loading indicator in corner if illustration not ready yet"
```

**Files to Create:**
- `frontend/src/components/BookReader.jsx`
- `frontend/src/components/PageSpread.jsx`
- `frontend/src/components/PageControls.jsx`

**Validation:**
- [x] Two-page layout displays correctly
- [x] Page turning is smooth
- [x] Illustrations render inline or as panels
- [x] Keyboard navigation works
- [x] Progress saving functional
- [ ] Reading speed tracking accurate (not implemented yet)
- [x] Can load book by URL parameter (BF-2)
- [x] Home screen "Continue Reading" section (BF-2)

---

## Phase 3: Image Generation Integration (6-8 hours) ❌ NOT STARTED

### 3.1 GeminiGen API Service (3 hours)

**Tasks:**
1. Implement GeminiGen API client
2. Handle single reference image limitation
3. Retry logic and error handling

**Cursor Prompts:**
```
"Create an image generation service for GeminiGen API that:

1. PROMPT CONSTRUCTION:
   - Takes scene description, character descriptions, location description
   - Combines into detailed generation prompt
   - Format: '{scene_description}. Character: {character_desc}. Setting: {location_desc}. Style: {user_style}'
   - Ensures prompt is clear and specific

2. API REQUEST:
   - Model: 'nano-banana'
   - Include ONE reference image (primary character or location)
   - Aspect ratio: 3:4 or 4:3 (book-appropriate)
   - Resolution: 1K (1024px)
   - Style parameter based on user selection

3. ERROR HANDLING:
   - 3 retry attempts with exponential backoff
   - Timeout: 60 seconds
   - Return placeholder image on final failure
   - Log errors for debugging

4. RESPONSE PROCESSING:
   - Save image to server filesystem (/static/illustrations/)
   - Store path in database
   - Return image URL

Include detailed logging for debugging
Handle rate limiting (if applicable)"

"Create placeholder image generator:
- Generate gray box with text 'Illustration Unavailable'
- Same aspect ratio as real illustrations
- Store as fallback.png in /static/"
```

**Files to Create:**
- `backend/app/services/image_service.py`
- Placeholder image: `backend/static/fallback.png`

**GeminiGen API Request Example:**
```python
import requests
import base64

def generate_illustration(prompt, reference_image_url, style, aspect_ratio="3:4"):
    """
    Generate illustration using GeminiGen Nano Banana API
    """
    # Download reference image and encode to base64
    ref_img_response = requests.get(reference_image_url)
    ref_img_base64 = base64.b64encode(ref_img_response.content).decode('utf-8')
    
    # Construct API request
    response = requests.post(
        "https://api.geminigen.ai/v1/generate",  # Verify actual endpoint
        headers={
            "Authorization": f"Bearer {GEMINIGEN_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "nano-banana",
            "prompt": prompt,
            "reference_image": ref_img_base64,  # or reference_image_url if supported
            "style": style,
            "aspect_ratio": aspect_ratio,
            "resolution": "1K"
        },
        timeout=60
    )
    
    # Handle response
    if response.status_code == 200:
        image_data = response.json()["image"]  # Adjust based on actual response structure
        # Save image to filesystem
        return save_image(image_data)
    else:
        raise Exception(f"Generation failed: {response.status_code}")
```

**Important Notes:**
- Verify GeminiGen API endpoint and authentication from their docs
- Test reference image format (URL vs base64)
- Confirm exact response structure
- Check rate limits and implement throttling if needed

**Validation:**
- [ ] Successfully generates images via API
- [ ] Reference images used correctly
- [ ] Retry logic works
- [ ] Placeholder used on failure
- [ ] Images saved to correct location
- [ ] Performance is acceptable (~30-60s per image)

---

### 3.2 Illustration Prompt Generation (2 hours)

**Tasks:**
1. Create prompts from visual bible + dramatic moments
2. Smart reference image selection
3. Consistency checks

**Cursor Prompts:**
```
"Create a prompt generation system that:

INPUT:
- Dramatic moment description (from AI analysis)
- Visual bible (characters, locations with references)
- User-selected style
- Chunk text (for additional context if needed)

PROMPT CONSTRUCTION:
1. Identify which characters appear in scene
2. Identify which location scene takes place in
3. Select primary reference image:
   - If 1 character: use character reference
   - If multiple characters: use main character reference
   - If no characters: use location reference
4. Build prompt with structure:
   '{scene_action}. {character_full_description}. {location_full_description}. {lighting_and_mood}. {style_keywords}.'
5. Keep total prompt <500 words for API efficiency

CONSISTENCY ENFORCEMENT:
- Always use same description for recurring characters
- Always use same description for recurring locations
- Maintain style keywords throughout book

STYLE KEYWORDS MAPPING:
- Non-Fiction: 'photorealistic, documentary style, natural lighting'
- Fiction: 'book illustration, detailed, balanced realism'
- Romance: 'soft focus, dreamy, pastel tones, romantic lighting'
- Sci-Fi: 'futuristic, vibrant colors, dramatic lighting, sci-fi aesthetic'
- Fantasy: 'epic fantasy, painterly, rich colors, dramatic composition'
- Fairy Tale: 'whimsical, storybook illustration, gentle colors'
- Classic: 'vintage engraving, cross-hatching, monochromatic, classic literature'

Return: {prompt: str, reference_image_url: str, characters: [], location: str}"

"Add prompt validation:
- Check prompt length
- Ensure required elements included
- Verify reference image URL is valid
- Log prompts for debugging/improvement"
```

**Files to Create:**
- Update `backend/app/services/image_service.py` with prompt generation

**Example Generated Prompt:**
```
"A tense confrontation in a dimly lit Victorian study. 
Character: A tall, slender woman in her early 30s with long auburn hair, 
piercing green eyes, and pale skin, wearing a dark green velvet dress, 
expression showing determination and anger. 
Setting: A mahogany-paneled study with floor-to-ceiling bookshelves, 
a large oak desk, flickering candlelight, shadows in corners, 
atmosphere of secrecy and tension. 
Style: vintage engraving, cross-hatching, monochromatic, classic literature illustration."
```

**Validation:**
- [ ] Prompts are detailed and specific
- [ ] Correct reference images selected
- [ ] Style keywords applied consistently
- [ ] Character/location descriptions reused correctly
- [ ] Prompts are appropriate length

---

### 3.3 Batch Generation & Queue Management (3 hours)

**Tasks:**
1. Initial batch generation (first 5 illustrations)
2. Progressive generation based on reading speed
3. Queue system for pending generations

**Cursor Prompts:**
```
"Create an illustration generation queue system:

INITIAL BATCH:
- Generate first 5 illustrations when user clicks 'Read'
- Run in background (async)
- Update frontend with progress: 'Generating illustration 1 of 5...'
- Allow user to start reading after first 2 complete

PROGRESSIVE GENERATION:
- Track user reading progress (current page)
- Calculate when user will reach next illustration
- Formula: time_to_next_illustration = (pages_to_next_illus / reading_speed_pages_per_min)
- Start generation when time_to_next_illustration < 5 minutes
- Always keep 2-3 illustrations ahead of reader

QUEUE MANAGEMENT:
- Max queue size: 3 pending generations
- FIFO processing (first in, first out)
- If queue full, skip and warn
- Mark illustrations as: 'pending', 'generating', 'completed', 'failed'

CONCURRENCY:
- Single generation at a time (to avoid rate limits)
- Use background task queue (Celery or similar, or simple threading for MVP)

READING SPEED TRACKING:
- Track page turn timestamps
- Calculate rolling average of last 10 page turns
- Default: 1 page per minute
- Store in session"

"Add API endpoints:
- POST /api/books/{book_id}/generate-initial (trigger first 5)
- POST /api/books/{book_id}/queue-next (trigger next illustration)
- GET /api/books/{book_id}/illustration-status (check queue status)
- WebSocket endpoint for real-time progress updates (optional)"
```

**Files to Create:**
- `backend/app/services/queue_service.py`
- Background task handler (simple threading or Celery)
- WebSocket handler (optional but recommended)

**Validation:**
- [ ] Initial 5 illustrations generated successfully
- [ ] User can start reading after 2 ready
- [ ] Progressive generation triggers correctly
- [ ] Queue doesn't overflow
- [ ] Reading speed calculation accurate
- [ ] No blocking during generation

---

## Bug Fixes & Improvements (applied during development)

### BF-1: Idempotent Re-Analysis ✅ COMPLETED

**Problem:** Running `POST /api/books/{book_id}/analyze` on an already-analyzed book duplicated characters, locations and other analysis artefacts in the database.

**Solution:**
- Added `clear_analysis_results(db, book_id)` function to `backend/app/crud.py`.
- The function deletes: `chunk_characters`, `chunk_locations`, `characters`, `locations`, `visual_bible`, `illustrations`, and resets `dramatic_score` to `NULL` on all chunks. The book record and its text chunks are preserved.
- `analyze_book` endpoint in `backend/app/routers/books.py` now calls `clear_analysis_results` before starting a new analysis.

### BF-2: Continue Reading from Home Screen ✅ COMPLETED

**Problem:** There was no way to resume reading a previously analyzed book. The only path to the reading experience led through the full Visual Bible generation flow.

**Solution:**
- `HomePage.tsx` now fetches the list of books on mount and displays a "Continue Reading" section for books with status `ready` or `reading`.
- Clicking a book card sets it in `BookContext` and navigates to `/read`.
- `ReadingPage.tsx` supports loading a book by `bookId` URL parameter (for direct links / page refresh).
- `App.tsx` adds route `/read/:bookId` alongside `/read`.
- `api.ts` exports a new `listBooks()` function.

### BF-3: Reference Image Search Optimization ✅ COMPLETED

**Problem:** Character names were not included in search queries for non-well-known books. Search queries were not logged. Every SerpAPI run searched for all 5 characters and 5 locations (~20-30 API calls), quickly exhausting the free tier.

**Solution:**

1. **Character names always in queries.** `_build_character_queries` and `_build_location_queries` in `search_service.py` now always include the entity name, even for non-well-known books.

2. **Search query audit log.** New `SearchQuery` model (`search_queries` table) stores every SerpAPI query with: book_id, entity_type, entity_name, query_text, results_count, created_at. New endpoint `GET /api/books/{book_id}/search-queries` to review them. Queries are cleared on re-analysis via `clear_analysis_results`.

3. **AI flags main character & location.** `CONSOLIDATION_PROMPT` in `ai_service.py` now asks GPT to mark exactly one character and one location as `is_main: true`. New `is_main` column on `Character` and `Location` models (with SQLite ALTER TABLE migration).

4. **Main-only search mode.** New "Limit reference search to main character & location only" checkbox in `StyleSelector` (default ON). `POST /api/books/{book_id}/search-references` accepts `{ "main_only": true }` body. When enabled, only `is_main=1` entities are searched via SerpAPI; the rest get a static placeholder SVG (`/static/placeholder_reference.svg`). Reduces API calls from ~20-30 to ~5.

5. **Placeholder image.** Static SVG at `backend/static/placeholder_reference.svg` served via FastAPI StaticFiles.

**Files changed:** `models.py`, `database.py`, `crud.py`, `schemas.py`, `ai_service.py`, `search_service.py`, `routers/books.py`, `routers/visual_bible.py`, `BookContext.tsx`, `StyleSelector.tsx`, `api.ts`, `SetupPage.tsx`.

---

### Delete Book from Library ✅ COMPLETED

**Feature:** Added ability to delete book and all associated data from the library.

**Solution:**
- `DELETE /api/books/{book_id}` endpoint in `routers/books.py`
- `delete_book()` function in `crud.py` removes:
  - All database records: characters, locations, visual_bible, illustrations, reading_progress, search_queries, chunk relationships, chunks
  - Generated illustration files from disk (using `os.remove`)
  - **Preserves:** Original text file on disk (`book.file_path`) and Google Drive link
- Frontend: Delete button with styled confirmation dialog (from BF-5.2)

**Files changed:** `crud.py`, `routers/books.py`, `api.ts`, `HomePage.tsx`

### BF-4: Decouple Analysis from Reference Search + Improve Queries ✅ COMPLETED

**Problem:** AI analysis and reference image search were tightly coupled — `SetupPage.handleAnalyze()` called `analyzeBook()` then immediately `searchReferences()`. Users could not review AI-identified characters/locations or change the "main" selection before search consumed SerpAPI quota. Search queries for non-well-known books did not include book title or author, producing generic results.

**Solution:**

1. **New Analysis Review Page.** After AI analysis completes, `SetupPage` navigates to `/analysis-review` instead of calling `searchReferences()`. New `AnalysisReviewPage.tsx` fetches characters and locations, displays them as interactive cards with star-toggle for `is_main` flag. User can select/deselect any entities for reference search. Also fixed "Start Reading a New Book" button to call `ctx.reset()` before navigating to `/setup` (prevents stale state from previous book).

2. **Batch entity selection endpoint.** New `PUT /api/books/{book_id}/entity-selections` accepts `{ characters: [{id, is_main}], locations: [{id, is_main}] }` to persist user's choices before triggering search. New `EntityMainFlag` and `EntitySelectionsRequest` schemas.

3. **Search queries always include book context.** `_build_character_queries()` and `_build_location_queries()` no longer branch on `is_well_known`. Query 1 always includes `{name} {book_title} {author} illustration`. Query 2 is a description-based fallback. The `is_well_known` parameter was removed from search service functions.

4. **Author passed to location queries.** `search_location_references()` and `search_all_references()` now accept and pass `author` to `_build_location_queries()`.

5. **Bug fix.** Removed stale debug instrumentation from `crud.py`, `books.py`, and `HomePage.tsx`. Fixed silent catch in `handleDelete` to show alert on failure.

**Files changed:** `schemas.py`, `routers/books.py`, `routers/visual_bible.py`, `services/search_service.py`, `crud.py`, `SetupPage.tsx`, `AnalysisReviewPage.tsx` (new), `App.tsx`, `api.ts`, `HomePage.tsx`, `requirements_document.md`.

---

### BF-5: UI/UX Improvements ⚠️ PARTIAL (2/6 completed)

#### BF-5.1: Некорректный рендеринг текста на Reading Page ❌ PENDING
**Problem:** Text displayed incorrectly (line breaks ignored, encoding issues with special characters like © and apostrophes) on the reading page.
**Status:** Not implemented yet
**Affected:** `ReadingPage.tsx`, `book_service.py`

#### BF-5.2: Стилизованный диалог подтверждения удаления ✅ COMPLETED
**Problem:** Basic `window.confirm()` dialog for book deletion doesn't match application design.
**Solution:** Replaced with custom styled `Dialog` component from `@headlessui/react` in `HomePage.tsx`.
**Files changed:** `HomePage.tsx`

#### BF-5.3: Сообщение об ошибке при некорректном формате файла ✅ COMPLETED
**Problem:** No user-friendly error when importing non-.txt files from Google Drive.
**Solution:** Added Content-Type validation in `book_service.py`; displays specific error message in `BookUpload.tsx`.
**Files changed:** `book_service.py`, `BookUpload.tsx`

#### BF-5.4: Lightbox для референсных изображений ❌ PENDING
**Problem:** Reference image thumbnails too small on Visual Bible page, no full-size view option.
**Status:** Not implemented yet
**Affected:** `VisualBiblePage.tsx`

#### BF-5.5: Проверка дубликатов при импорте книг ❌ PENDING
**Problem:** Importing the same Google Drive link creates duplicate book entries without warning.
**Status:** Not implemented yet
**Affected:** `routers/books.py`, `crud.py`

#### BF-5.6: Кнопка повторного анализа книги ❌ PENDING
**Problem:** No option to re-run AI analysis and generation for already analyzed books.
**Status:** Not implemented yet
**Affected:** `HomePage.tsx`, backend re-analysis flow

---

## Phase 4: Integration & Polish (4-6 hours) ⚠️ PARTIAL

### 4.1 End-to-End Workflow Integration (2 hours)

**Tasks:**
1. Connect all components
2. State management across pages
3. Navigation flow

**Cursor Prompts:**
```
"Create a React Router setup with these pages:

1. HOME PAGE (/):
   - Welcome message
   - 'Start Reading' button → /setup

2. SETUP PAGE (/setup):
   - Render BookUpload component
   - On success → StyleSelector component
   - On style submission → trigger analysis → LoadingScreen
   - After analysis → /visual-bible

3. VISUAL BIBLE PAGE (/visual-bible):
   - Render VisualBibleReview component
   - On approval → trigger initial generation → LoadingScreen
   - After generation → /read

4. READING PAGE (/read):
   - Render BookReader component
   - Full-screen reading experience
   - 'Exit' button returns to home

Use React Context for global state:
- Current book
- Visual bible data
- Reading progress

Include route guards:
- Redirect to /setup if no book loaded
- Redirect to /visual-bible if analysis not complete
- Redirect to /read only if illustrations ready"

"Add error boundary components:
- Catch and display errors gracefully
- 'Report Issue' button
- Automatic retry option
- Fallback UI that doesn't break the experience"
```

**Files to Create:**
- `frontend/src/App.jsx` (routing)
- `frontend/src/context/BookContext.jsx` (state management)
- `frontend/src/pages/HomePage.jsx`
- `frontend/src/pages/SetupPage.jsx`
- `frontend/src/pages/VisualBiblePage.jsx`
- `frontend/src/pages/ReadingPage.jsx`

**Validation:**
- [x] Can navigate through entire workflow
- [x] State persists across pages
- [x] Route guards work correctly
- [ ] Error boundaries catch errors (not implemented yet)
- [x] No broken UI states
- [x] BookContext implemented with reset functionality

---

### 4.2 UI/UX Polish (2 hours)

**Tasks:**
1. Responsive design
2. Loading states
3. Error messages
4. Animations

**Cursor Prompts:**
```
"Polish the UI with:

1. LOADING STATES everywhere:
   - Skeleton loaders for content
   - Spinner or pulse animations
   - Disable buttons while loading
   - Show 'X% complete' where applicable

2. ERROR HANDLING UX:
   - Toast notifications for non-critical errors
   - Modal for critical errors
   - Clear error messages (avoid technical jargon)
   - 'Try Again' buttons
   - Contact support option

3. ANIMATIONS:
   - Smooth page transitions (fade in/out)
   - Button hover effects
   - Card hover lift effect
   - Progress bar animations
   - Page flip animation in reader
   - All animations <300ms for snappiness

4. ACCESSIBILITY:
   - ARIA labels on interactive elements
   - Keyboard navigation support
   - Focus indicators
   - Alt text on images
   - Color contrast compliance (WCAG AA)

5. RESPONSIVE DESIGN:
   - Desktop-first for MVP (1024px+)
   - Mobile message: 'Please use desktop for best experience'
   - Tablet support if time permits

Use Tailwind CSS utilities and custom CSS where needed"

"Add user feedback:
- Toast notifications for success/errors
- Confirmation modals for destructive actions
- Progress indicators everywhere
- Hover tooltips for additional info
- 'Help' icons with explanations"
```

**Files to Create:**
- `frontend/src/components/Toast.jsx`
- `frontend/src/components/Modal.jsx`
- `frontend/src/components/Skeleton.jsx`
- Custom CSS animations

**Validation:**
- [ ] All interactive elements have loading states
- [ ] Errors displayed clearly with recovery options
- [ ] Animations are smooth and pleasant
- [ ] Keyboard navigation works
- [ ] Accessible to screen readers

---

### 4.3 Testing & Bug Fixes (2 hours)

**Tasks:**
1. Manual testing of complete flow
2. Bug fixes
3. Performance optimization

**Testing Checklist:**
- [ ] Import book from Google Drive (various file sizes)
- [ ] Style selection and calculation accuracy
- [ ] AI analysis completes successfully
- [ ] Reference images load correctly
- [ ] Visual bible selections save properly
- [ ] Initial illustrations generate
- [ ] Can start reading
- [ ] Page turning is smooth
- [ ] Illustrations display inline correctly
- [ ] Reading progress saves and resumes
- [ ] Progressive generation triggers
- [ ] Error states handled gracefully
- [ ] No console errors
- [ ] Performance is acceptable (no lag)

**Common Issues to Check:**
- CORS errors (backend/frontend communication)
- Image loading failures (URLs, CORS, paths)
- Database locking (SQLite concurrent writes)
- API rate limits (OpenAI, GeminiGen)
- Memory leaks (React component cleanup)
- Large file uploads timing out
- Slow database queries (add indexes)

**Performance Optimization:**
```
"Optimize performance:
- Add indexes to database on frequently queried columns
- Implement image lazy loading
- Compress images before storing
- Use React.memo for expensive components
- Debounce API calls
- Add database query caching
- Minimize re-renders in React
- Use production builds for testing"
```

**Validation:**
- [ ] No critical bugs
- [ ] Performance acceptable (smooth reading)
- [ ] Error handling robust
- [ ] Edge cases handled

---

## Phase 5: Deployment (2-3 hours) ❌ NOT STARTED

### 5.1 Backend Deployment

**Recommended Platform:** Render.com (Free Tier)

**Steps:**
1. Create `render.yaml` config
2. Set environment variables
3. Deploy backend service

**Cursor Prompts:**
```
"Create deployment configuration for Render.com:

1. Create render.yaml with:
   - Web service for FastAPI backend
   - Environment: Python 3.10
   - Build command: pip install -r requirements.txt
   - Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
   - Health check path: /health

2. Create Dockerfile (alternative):
   - Python 3.10 base image
   - Copy requirements and install
   - Copy application code
   - Expose port 8000
   - CMD to run uvicorn

3. Update .env for production:
   - Database path
   - API keys (use environment variables)
   - CORS allowed origins (frontend URL)
   - Log level

4. Add production dependencies to requirements.txt:
   - gunicorn or uvicorn[standard]
   - python-dotenv
   - All existing dependencies"
```

**Files to Create:**
- `backend/render.yaml`
- `backend/Dockerfile` (optional)
- `backend/.env.production`

**Render.com Setup:**
1. Sign up at https://render.com
2. Connect GitHub repository
3. Create new Web Service
4. Select backend directory
5. Add environment variables (API keys)
6. Deploy

**Validation:**
- [ ] Backend deployed successfully
- [ ] Health check endpoint returns 200
- [ ] API endpoints accessible via HTTPS
- [ ] Database persists correctly
- [ ] Environment variables loaded

---

### 5.2 Frontend Deployment

**Recommended Platform:** Vercel (Free Tier)

**Steps:**
1. Update API URLs for production
2. Build production bundle
3. Deploy to Vercel

**Cursor Prompts:**
```
"Prepare frontend for production deployment:

1. Update API client to use environment variables:
   - Create .env.production with VITE_API_URL
   - Update api.js to read from import.meta.env.VITE_API_URL
   - Fallback to localhost for development

2. Optimize build:
   - Enable production mode
   - Minify assets
   - Tree-shake unused code
   - Compress images

3. Create vercel.json config:
   - Rewrites for SPA routing
   - Headers for caching
   - Environment variable references

4. Update CORS in backend:
   - Allow Vercel frontend domain
   - Update allowed origins in main.py"
```

**Files to Create:**
- `frontend/.env.production`
- `frontend/vercel.json`

**Vercel Setup:**
1. Sign up at https://vercel.com
2. Import GitHub repository
3. Select frontend directory
4. Add environment variable: `VITE_API_URL=https://your-backend.onrender.com`
5. Deploy

**Validation:**
- [ ] Frontend deployed successfully
- [ ] API calls work (CORS configured)
- [ ] All pages load correctly
- [ ] Images display properly
- [ ] No 404 errors on refresh

---

### 5.3 Database & Storage Setup

**For MVP (Simple Approach):**
- SQLite database stored on Render.com persistent disk
- Illustrations stored in `/static` folder on server

**Steps:**
1. Configure persistent disk on Render.com
2. Update file paths in code
3. Test write/read operations

**Cursor Prompts:**
```
"Update file paths for production:

1. Database:
   - Use environment variable for DB path
   - Default: /data/app.db (Render persistent disk)
   - Ensure directory exists before creating DB

2. Image Storage:
   - Create /static/illustrations directory
   - Serve via FastAPI StaticFiles
   - Update paths in image_service.py

3. Environment Detection:
   - Check if RENDER=true environment variable
   - Use different paths for local vs production
   - Add logging for debugging"
```

**render.yaml addition:**
```yaml
services:
  - type: web
    name: reading-reinvented-backend
    env: python
    disk:
      name: data
      mountPath: /data
      sizeGB: 1
```

**Validation:**
- [ ] Database persists across deployments
- [ ] Images save and load correctly
- [ ] Paths work in production
- [ ] No permission errors

---

## Phase 6: Documentation & Handoff (1-2 hours) ⚠️ PARTIAL

### 6.1 User Documentation

**Create:**
1. README.md with setup instructions
2. User guide (how to use the app)
3. Troubleshooting guide

**Cursor Prompts:**
```
"Create a comprehensive README.md with:

1. PROJECT OVERVIEW
   - Description
   - Features
   - Screenshots

2. SETUP INSTRUCTIONS
   - Prerequisites
   - Installation steps (backend and frontend)
   - Environment variables
   - Database initialization
   - Running locally

3. DEPLOYMENT
   - Backend deployment (Render.com)
   - Frontend deployment (Vercel)
   - Environment configuration

4. USAGE GUIDE
   - How to import a book
   - How to set up visual bible
   - How to read with illustrations

5. TROUBLESHOOTING
   - Common errors and solutions
   - API rate limits
   - Image generation failures

6. FUTURE IMPROVEMENTS
   - Roadmap items
   - Known limitations

Use clear formatting with code blocks and links"
```

---

## Development Tips for Cursor IDE

### Effective Prompting Strategies

**1. Be Specific:**
```
❌ "Create a book reader"
✅ "Create a BookReader.jsx component with two-page spread layout, 
serif font, page turning buttons, and progress bar. Use Tailwind CSS."
```

**2. Provide Context:**
```
"Given that we're using FastAPI and SQLAlchemy, create a service 
that chunks book text into 2000-token segments with 200-token overlap."
```

**3. Request Complete Files:**
```
"Create a complete file backend/app/services/book_service.py with:
- Import book from Google Drive function
- Text chunking function
- Database save function
- Error handling
Include all imports and docstrings."
```

**4. Iterate Incrementally:**
```
First: "Create basic book upload form"
Then: "Add validation for Google Drive URLs"
Then: "Add loading spinner during upload"
Then: "Add error handling with retry"
```

**5. Ask for Explanations:**
```
"Explain the chunking algorithm you just created and why you 
chose those specific token counts."
```

### Cursor Shortcuts & Features

- **Cmd/Ctrl + K**: Inline code generation
- **Cmd/Ctrl + L**: Chat with AI about selected code
- **Cmd/Ctrl + I**: Generate based on comment
- **Tab**: Accept AI suggestion

### Debugging with Cursor

```
"This function is throwing an error: [paste error]. 
Here's the code: [paste code]. 
What's wrong and how do I fix it?"
```

---

## Cost Estimates

### Development Costs (MVP)
- OpenAI API (testing): ~$5-10
- GeminiGen API (testing): ~$5-10
- Bing Search API: Free tier (1000 searches)
- Hosting: Free tiers (Render + Vercel)

**Total Development Cost:** ~$10-20

### Per-Book Operational Costs
- Analysis: $0.50
- Images (125 @ $0.02): $2.50
- Search: Free

**Total Per Book:** ~$3.00

---

## Timeline Estimate

**Assuming 4-hour focused development sessions:**

| Phase | Hours | Sessions | Days (at 1 session/day) |
|-------|-------|----------|-------------------------|
| Backend Foundation | 8-12 | 2-3 | 2-3 days |
| Frontend Core UI | 8-10 | 2-3 | 2-3 days |
| Image Generation | 6-8 | 2 | 2 days |
| Integration & Polish | 4-6 | 1-2 | 1-2 days |
| Deployment | 2-3 | 1 | 1 day |
| Documentation | 1-2 | 1 | 1 day |
| **TOTAL** | **40-60** | **10-15** | **10-15 days** |

**Accelerated Timeline (Full-Time):** 5-7 days  
**Part-Time (2 sessions/week):** 5-8 weeks

---

## Success Milestones

### Week 1 Milestone
- [ ] Book import working
- [ ] Text chunking functional
- [ ] AI analysis completes
- [ ] Basic UI components created

### Week 2 Milestone
- [ ] Reference image search working
- [ ] Visual bible review functional
- [ ] Image generation integrated
- [ ] Reading interface operational

### Week 3 Milestone
- [ ] Complete workflow functional end-to-end
- [ ] UI polished
- [ ] Deployed to production
- [ ] Documentation complete

---

## Troubleshooting Common Issues

### Backend Issues

**Issue:** Database locked error
**Solution:** 
```python
# Add to database.py
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30}
)
```

**Issue:** CORS errors
**Solution:**
```python
# In main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-frontend.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Issue:** OpenAI rate limits
**Solution:**
- Add exponential backoff
- Use gpt-3.5-turbo (higher rate limit)
- Implement request queuing

### Frontend Issues

**Issue:** Images not loading
**Solution:**
- Check CORS headers on backend
- Verify image URLs are correct
- Use proxy in development: `vite.config.js`
```javascript
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
}
```

**Issue:** State not persisting
**Solution:**
- Use React Context properly
- Check dependencies in useEffect
- Use localStorage for persistence if needed

---

## Next Steps After MVP

1. **User Testing:** Get feedback from 5-10 users
2. **Analytics:** Add usage tracking to understand behavior
3. **Performance:** Profile and optimize slow operations
4. **Features:** Implement Phase 2 roadmap items
5. **Monetization:** Consider subscription model or pay-per-book

---

**Good luck with your development! This roadmap should guide you through building a functional MVP. Remember to:**
- Commit code frequently to Git
- Test each component before moving to the next
- Use Cursor's AI assistance liberally
- Don't aim for perfection in MVP—focus on functionality
- Have fun building something innovative!

---

**END OF DEVELOPMENT ROADMAP**
