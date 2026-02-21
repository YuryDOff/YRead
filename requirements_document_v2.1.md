# Requirements Document: AI-Powered Book Illustration Platform
## "StoryForge AI - Illustrated Books Made Easy"

**Version:** 2.1  
**Date:** February 10, 2026 (updated Feb 19, 2026: Clean DB script; smart visual query algorithm and review-before-search step per plan; updated Feb 21, 2026: Visual Semantic Engine Steps 1–10 implemented; Steps 11–12 (Schemas + Routers + Frontend) implemented)  
**Project Type:** Web Application (SaaS)  
**Development Approach:** Vibe-coding with Cursor IDE  
**Primary Market:** Self-Publishing Authors (B2B)  
**Future Expansion:** Reading Platform (B2C - Phase 4)

---

## 1. Executive Summary

### 1.1 Vision

**Primary Vision (B2B - Phases 1-3):**
Empower self-publishing authors to create professionally illustrated books without the $5,000-$20,000 cost of traditional illustrators, enabling them to publish high-quality illustrated books on Amazon KDP.

**Future Vision (B2C - Phase 4):**
Build a reading platform where authors can publish their illustrated books and readers can discover and enjoy AI-enhanced reading experiences, creating a two-sided marketplace.

### 1.2 Market Opportunity

**B2B Market (Primary Focus):**
- **Total Addressable Market (TAM):** $900M - $1.2B globally
- **Serviceable Market:** 1.4 million books published annually on Amazon KDP
- **Target Segment:** 40% need illustrations (560,000 books/year)
- **Pain Point:** Professional illustration costs $5,000-$20,000 per book
- **Current Solutions:** Neolemon (23,000 users, $29/mo), expensive human illustrators

**B2C Market (Future Expansion):**
- **TAM:** $150-300M (estimated)
- **Target Segment:** Readers who want illustrated versions of books
- **Strategy:** Authors publish illustrated books on platform, readers subscribe to read
- **Revenue Model:** Subscription ($9.99/mo) or per-book purchase ($4.99)
- **Timing:** Phase 4 (Year 2), after B2B establishes content library

### 1.3 Competitive Positioning

**Primary Advantage: Manuscript Analysis Automation**
> "The first platform that reads your manuscript and automatically generates professional illustrations - no prompts, no design skills required."

**Competitive Landscape:**

| Competitor | Strengths | Weaknesses | Our Advantage |
|------------|-----------|------------|---------------|
| **Neolemon** | Character consistency, 23K users, $29/mo | Prompt-based (3-5 hrs/book), children's only | Manuscript analysis (15 min/book), all genres |
| **Recraft.ai** | Professional tools, high quality | Not book-specific, $50-200/mo, complex | Purpose-built for authors, $29/mo, simple |
| **Midjourney** | Best quality | Discord required, complex prompts, no book features | No technical skills needed, KDP-ready export |
| **Fiverr Artists** | Human creativity | $1,000-$5,000/book, weeks of turnaround | 10x cheaper, 100x faster, unlimited revisions |

**Key Differentiators:**
1. **Manuscript Analysis:** Upload manuscript → AI extracts characters, scenes automatically
2. **KDP Integration:** One-click export of print-ready PDFs (interior + cover)
3. **Reference Image Search:** AI-suggested, pre-cleared commercial images
4. **All Genres:** Children's, fantasy, sci-fi, romance, mystery (vs Neolemon's children's-only)
5. **Series Support:** Maintain character consistency across multi-book series

### 1.4 Business Model & Pricing

**SaaS Subscription Tiers:**

| Tier | Price | Target User | Features | Estimated Adoption |
|------|-------|-------------|----------|-------------------|
| **Free Trial** | $0 | Testing | 1 book, 10 illustrations, watermarked | 60% of signups |
| **Starter** | $19/mo | Hobbyists | 2 books/mo, 50 illus/book, KDP export | 20% of paid |
| **Creator** | $29/mo | Active authors | Unlimited books, all styles, cover gen | 60% of paid |
| **Professional** | $79/mo | Prolific authors | Batch processing, series tools, API | 20% of paid |

**Revenue Projections:**

| Metric | Year 1 | Year 2 | Year 3 |
|--------|--------|--------|--------|
| **Total Users** | 10,000 | 40,000 | 100,000 |
| **Paying Users** | 2,500 (25%) | 12,000 (30%) | 35,000 (35%) |
| **ARPU** | $35/mo | $40/mo | $45/mo |
| **MRR** | $87.5K | $480K | $1.58M |
| **ARR** | $1.05M | $5.76M | $18.9M |

**Cost Structure:**
- AI analysis: $0.50 per book (OpenAI GPT-4-mini for manuscript analysis)
- Image generation: $1.88 per book (125 images @ $0.015 each using Leonardo AI)
  - **Model Used:** Leonardo AI (primary recommendation for MVP)
  - **Pricing Details:**
    - Leonardo AI Maestro Plan: $48/month for 25,000 tokens
    - 1 image (1024x1536 resolution) ≈ 8 tokens
    - Effective cost: ~$0.015 per image
    - Typical 500-page book: ~125 illustrations (1 per 4 pages)
    - Cost calculation: 125 × $0.015 = $1.88/book
  - **Alternative Models (for comparison):**
    - Midjourney API: $0.05-0.08/image → $6.25-10.00/book (higher quality, premium tier)
    - Self-hosted Stable Diffusion: $0.01/image → $1.25/book (Phase 2+ infrastructure)
    - OpenAI DALL-E 3: $0.04/image → $5.00/book (good quality, expensive at scale)
  - **Why Leonardo AI:** Best cost/quality ratio, built-in character reference (no LoRA training needed), fast generation, multiple styles
- Cover generation: $0.12 (8 images for cover variations using Leonardo AI)
- Total COGS: ~$2.50 per book
- Gross margin: ~91% (after infrastructure costs)

### 1.5 MVP Scope (Phases 1-3: B2B Author Tools)

**Phase 1: MVP (Months 1-4)**
Single-author workflow from manuscript upload to KDP-ready export.

**Core Flow:**
1. Upload manuscript (.txt, .docx)
2. AI analyzes → extracts characters, locations, scenes
   
   **Best Practices for Reliable Scene Extraction:**
   - **Narrative Structure Analysis:** Identify key plot points using story structure frameworks
     - Opening Hook: First 5-10% of manuscript (sets tone, introduces protagonist)
     - Inciting Incident: 10-15% mark (problem/quest begins)
     - Rising Action Beats: Every 10-15% intervals (conflicts, revelations, setbacks)
     - Midpoint Twist: 40-50% mark (major revelation or reversal)
     - Climax: 80-90% mark (highest tension point)
     - Resolution: Final 5-10% (emotional payoff)
   
   - **Emotional Intensity Detection:** Score each chunk for visual/emotional impact
     - Action keywords: "ran," "fought," "crashed," "discovered," "screamed" → High score
     - Dialogue-heavy chunks with minimal action → Lower score
     - Sensory descriptions (visual, tactile, atmospheric) → Higher score
     - Internal monologue/reflection → Lower score
   
   - **Character Presence Weighting:** Prioritize scenes with main characters
     - Scenes with protagonist + antagonist together → Highest priority
     - Solo protagonist scenes → High priority
     - Supporting character only scenes → Medium priority
   
   - **Visual Density Assessment:** Identify highly descriptive passages
     - Paragraphs with 5+ visual adjectives → Highly illustratable
     - Setting descriptions (forests, castles, cities) → High priority
     - Abstract concepts or philosophy → Skip
   
   - **Pacing Consideration:** Balance illustration frequency with reading flow
     - Avoid clustering illustrations (minimum 3-4 pages between)
     - Prefer action/movement over static dialogue
     - Consider chapter breaks as natural illustration points
   
   - **Reader Interest Heuristics:** What keeps readers engaged
     - Character transformation moments (physical or emotional changes)
     - "Reveal" scenes (secrets, identities, hidden objects discovered)
     - Relationship dynamics (first meetings, conflicts, reconciliations)
     - Environmental spectacle (epic landscapes, magical phenomena)
     - Danger/suspense peaks (chases, confrontations, narrow escapes)
   
   **AI Prompting Strategy for Scene Extraction:**
   ```
   For each text chunk, analyze:
   1. Dramatic score (0.0-1.0): Action level + emotional intensity + visual richness
   2. Characters present: Which key characters appear in this chunk?
   3. Visual moment: What is the single most visual/memorable image?
   4. Reader engagement: Would readers remember this scene?
   5. Illustration priority: Should this scene be illustrated? (Yes/Maybe/No)
   
   Return scenes with dramatic_score > 0.6 as top candidates for illustration.
   ```
   
   **Validation:** Test extraction accuracy against manually selected scenes from 5 sample books. Target 70%+ match with human selections.

3. Review visual bible → approve reference images
4. Generate illustrations automatically (character consistency via Leonardo AI Character Reference)
5. Preview book layout
6. Export KDP package (interior.pdf + cover.pdf)

**Success Metric:** Author uploads manuscript and gets KDP-ready files in <30 minutes

**Out of Scope for MVP:**
- Batch processing (Phase 2)
- Series continuity (Phase 2)
- Reading platform (Phase 4)
- Mobile apps (Phase 5)

---

## 2. Market Analysis & User Personas

### 2.1 Target Market: Self-Publishing Authors

**Market Size:**
- 1.4M books self-published on Amazon KDP annually (US)
- 2M+ globally across all platforms
- 40% need illustrations (children's books, fantasy, sci-fi)
- Market growing 15% annually

**Pain Points (Validated from Author Community Research):**

| Pain Point | Current Solution | Cost | Time | Our Solution |
|------------|-----------------|------|------|--------------|
| Illustration costs | Professional artist | $5K-20K | 3-6 months | $29-79/mo subscription |
| Character consistency | Manual reference sheets | Included in above | Hours per book | Automatic LoRA training |
| Prompt engineering | Learn Midjourney/Discord | $10-30/mo + learning curve | 3-5 hours/book | Upload manuscript (15 min) |
| Finding references | Google/Shutterstock search | $50-200 | 1-3 hours | AI-suggested pre-cleared images |
| KDP formatting | Hire formatter or DIY | $100-300 | 2-4 hours | One-click export |
| Cover design | Hire designer | $300-800 | 1-2 weeks | AI-generated with templates |

**Author Communities (Where They Gather):**
- KBoards / Writer's Cafe (largest indie author forum)
- Reddit: r/selfpublish (100K+ members)
- Kindlepreneur (educational content + tools)
- Facebook Groups: Self-Publishing authors (20K+ members each)
- Twitter/X: #amwriting, #selfpub hashtags

### 2.2 User Personas (B2B - Authors)

#### Persona 1: "Sarah" - Children's Book Author
**Demographics:**
- Age: 35-50
- Background: Former teacher, stay-at-home parent, creative professional
- Publishing frequency: 2-4 books per year
- Income from books: $500-2,000/month

**Goals:**
- Create high-quality illustrated children's books
- Build recurring income through book sales
- Publish series with consistent characters
- Keep costs under $500 per book

**Pain Points:**
- Professional illustrators cost $9,000-$20,000 (unaffordable)
- Tried Midjourney but character consistency is impossible
- Spent 3-5 hours writing prompts for each book
- Not tech-savvy, finds Discord confusing

**Decision Criteria:**
- Character consistency (must match across 30+ pages)
- Easy to use (no technical skills required)
- Affordable ($200-300 per book max)
- Fast turnaround (publish monthly)

**What She'll Pay:** $29-79/mo (Creator or Professional tier)
**Lifetime Value:** $1,500-3,000 (3-5 year relationship, 10-20 books)

**Quote (from KBoards research):**
> "Illustration alone will end up being more than your budget. Your chances of making back money on it becomes very unlikely. I need an affordable solution."

---

#### Persona 2: "Marcus" - Fantasy Series Author
**Demographics:**
- Age: 28-45
- Background: Full-time author or side hustle
- Publishing frequency: 3-5 books per year (trilogy/series)
- Income from books: $2,000-8,000/month

**Goals:**
- Build epic fantasy worlds with visual consistency
- Publish book series (3-5 books) with recurring characters
- Create premium editions with interior illustrations
- Stand out in crowded fantasy market

**Pain Points:**
- Need maps, character art, world-building visuals
- Covers cost $300-500 each, adds up quickly
- Can't afford interior illustrations ($50-100 per image)
- Character appearance must stay consistent across 5-book series

**Decision Criteria:**
- Series continuity (same characters across books)
- Genre-specific styles (epic fantasy aesthetics)
- Batch processing (generate 5 books at once)
- Professional quality (rival traditionally published books)

**What He'll Pay:** $79/mo (Professional tier for batch processing)
**Lifetime Value:** $3,000-8,000 (4-6 year relationship, 15-30 books)

**Quote (from Medium research):**
> "Midjourney is heaven-sent for fantasy authors, but I still spend hours on prompts and struggle with consistency across my series."

---

#### Persona 3: "Jamie" - First-Time Author
**Demographics:**
- Age: 25-65 (wide range)
- Background: Aspiring author, side project
- Publishing frequency: 1-2 books per year (testing market)
- Income from books: $0-500/month (starting out)

**Goals:**
- Publish first book without massive investment
- Test market viability before committing more money
- Create professional-looking book on tight budget
- Learn self-publishing process

**Pain Points:**
- Can't afford $5,000+ for illustrations
- No design skills or artistic ability
- Overwhelmed by self-publishing complexity
- Doesn't know if book will sell

**Decision Criteria:**
- Low upfront cost (free trial essential)
- Easy to use (beginner-friendly)
- Professional output (doesn't look cheap)
- No long-term commitment (pay-per-book or cancel anytime)

**What They'll Pay:** $0 (free trial) → $19/mo (Starter tier if successful)
**Lifetime Value:** $200-800 (1-2 year relationship, 2-5 books)

**Quote (from KBoards research):**
> "I haven't made a lot from writing yet, so my budget is tiny. Is it realistic to get quality illustrations for under $200?"

---

### 2.3 B2C User Personas (Future - Phase 4)

#### Persona 4: "Elena" - Visual Reader (Future B2C)
**Demographics:**
- Age: 25-40
- Background: Professional, reads 20-30 books/year
- Spending on books: $20-50/month

**Goals:**
- Enhance reading experience with visuals
- Discover new illustrated books
- Support independent authors
- Nostalgic for childhood illustrated books

**What She'll Pay:** $9.99/mo reading subscription or $4.99 per book

**NOTE:** This persona is Phase 4 (Year 2) - not MVP focus

---

## 3. Functional Requirements (B2B - Author Tools)

### 3.1 Manuscript Upload & Processing

#### 3.1.1 Manuscript Upload (Revised from Google Drive Import)
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want to upload my manuscript file so that I can create an illustrated book.

**Acceptance Criteria:**
- Support file formats: .txt, .docx, .pdf (text-extractable)
- Drag-and-drop upload interface
- File size limit: 20MB for MVP (~4M words, 2000+ pages)
- Progress indicator during upload
- Extract plain text from uploaded files
- Validate that file contains readable text (not images-only PDF)
- Display book metadata form:
  - Book title (pre-filled from filename or first line)
  - Author name
  - Genre selection
  - **"Is there another book like it?"** (Yes/No toggle for reference image search optimization)
    - If **Yes**: User enters similar book title/author → Improves reference image search accuracy
    - If **No**: Uses genre-based descriptive searches only
    - **Note for B2C (Phase 4):** Caption would be "Is this a well-known published book?" (for reader-facing version)
  - Optional: Similar book title/author (appears if user selects "Yes" above)
- Confirmation message with word count and estimated page count

**Technical Specifications:**
- Frontend: React Dropzone component
- File storage: Server filesystem (temporary during processing)
- Text extraction:
  - .txt: Direct read
  - .docx: python-docx library
  - .pdf: PyPDF2 (text extraction, fails if scanned images)
- Validation: Minimum 1,000 words to qualify as "book"
- Security: Sanitize filename, validate MIME type, virus scan (optional)

**API Endpoint:**
```
POST /api/manuscripts/upload
Body: multipart/form-data with file
Response: {
  "manuscript_id": 123,
  "title": "Luna's Adventure",
  "word_count": 5420,
  "estimated_pages": 22,
  "status": "uploaded"
}
```

**Future Enhancement (Phase 2):**
- Google Drive integration (optional import source)
- Dropbox integration
- EPUB file support

**Rationale for Change:**
Direct upload is simpler, more flexible, and doesn't depend on external services. Authors have manuscripts in many formats and locations.

---

#### 3.1.2 Text Chunking
**Priority:** Must-Have (MVP)

**User Story:**
As a system, I need to chunk the book text intelligently so that I can analyze and generate contextual illustrations.

**Acceptance Criteria:**
- Text divided into overlapping chunks for AI analysis
- Chunk size: ~2000 tokens (~1500 words)
- Overlap: 200 tokens between chunks (maintains context)
- Chunk boundaries respect paragraph breaks when possible (no mid-sentence cuts)
- Metadata stored for each chunk:
  - chunk_id, position, word_count
  - start_page, end_page (estimated)
- **Post-analysis enrichment** (after AI analysis completes):
  - Characters present in chunk (references to character IDs)
  - Locations present in chunk (references to location IDs)
  - Dramatic score (0.0-1.0) for illustration prioritization
- Enable efficient querying: "Get all chunks featuring Character X"

**Technical Specifications:**
- Chunking algorithm:
  ```python
  def chunk_text(text, chunk_size=2000, overlap=200):
      tokens = text.split()  # Simple word tokenization
      chunks = []
      for i in range(0, len(tokens), chunk_size - overlap):
          chunk = tokens[i:i+chunk_size]
          # Find last sentence boundary in chunk
          chunk_text = ' '.join(chunk)
          chunks.append({
              'index': i,
              'text': chunk_text,
              'word_count': len(chunk),
              'start_page': i // 300,  # ~300 words/page
              'end_page': (i + len(chunk)) // 300
          })
      return chunks
  ```
- Store chunks in database with foreign key to manuscript
- Calculate total chunks: `total_chunks = (word_count / (chunk_size - overlap))`
- Estimated processing time: `total_chunks * 3 seconds` (for batch AI analysis)

**Database Schema:**
```sql
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_page INTEGER,
    end_page INTEGER,
    word_count INTEGER,
    dramatic_score REAL DEFAULT 0.0,  -- Set after AI analysis
    FOREIGN KEY (book_id) REFERENCES books(id),
    UNIQUE(book_id, chunk_index)
);

-- Junction tables for many-to-many relationships
CREATE TABLE chunk_characters (
    chunk_id INTEGER,
    character_id INTEGER,
    PRIMARY KEY (chunk_id, character_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

CREATE TABLE chunk_locations (
    chunk_id INTEGER,
    location_id INTEGER,
    PRIMARY KEY (chunk_id, location_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);
```

---

### 3.2 AI Analysis & Visual Bible Creation

#### 3.2.1 Book Analysis (Core Differentiator)
**Priority:** Must-Have (MVP) - **This is your killer feature**

**User Story:**
As an author, I want the AI to automatically analyze my manuscript and extract characters, locations, and key scenes so that I don't have to write prompts manually.

**Acceptance Criteria:**
- Analysis completed in batches to manage costs and API limits
- **Extracted information:**
  - **5 main characters** (name, physical description, personality traits, typical emotions)
  - **5 main locations** (name, detailed visual description, atmosphere)
  - **Overall tone and style** (genre, mood, narrative voice)
  - **Key dramatic moments per chunk** (for illustration placement)
  - **Character and location presence per chunk** (for metadata enrichment)
- Total cost per book: **≤$0.50 in AI tokens**
- Progress indicator shown to user during analysis ("Analyzing page 50 of 200...")
- Estimated time: 2-5 minutes for 500-page book
- **Chunk metadata updated** with character/location relationships
- **Idempotent re-analysis:** Running analysis on a previously analyzed book must first clear all prior results (characters, locations, visual bible, illustrations, chunk relationships, dramatic scores) before creating new ones. The book record and text chunks are preserved.

**Plan: Clean DB → Start Analysis (development).** To start analysis from a clean state (e.g. no existing books or analysis results), run a full database reset, then upload a manuscript and run analysis. See *Development: Full database reset* below.

**Technical Specifications:**

**Development: Full database reset.**  
A script clears all application data so you can run upload and analysis from scratch. From the project root:
```bash
cd backend && python scripts/reset_db.py
```
This removes all rows from books, chunks, characters, locations, visual_bible, illustrations, covers, kdp_exports, search_queries, and junction tables, in FK-safe order. Schema is preserved. After running, the app is ready for a fresh upload and analysis run.

**Batching Strategy:**
- Batch size: 10-15 chunks per GPT API call (stays within 128k context window)
- Number of batches: `total_chunks / batch_size`
- Cost per batch: ~$0.015-0.025 (using GPT-4-mini or GPT-3.5-turbo)

**AI Prompting Strategy (Three-Pass Analysis):**

**Pass 1: Batch Analysis (per 10-15 chunks)**
```
System Prompt:
You are an expert book analyst specializing in extracting visual information for illustration.

User Prompt:
Analyze the following book excerpts and extract:
1. Characters mentioned (name, physical description, personality, emotions)
2. Locations mentioned (name, visual description, atmosphere)
3. Most dramatic/visual moment in each chunk (for illustration)
4. Which characters/locations appear in which chunks

Return structured JSON.

[Insert 10-15 chunks here]

Expected Output Format:
{
  "characters": [
    {
      "name": "Luna",
      "physical_description": "8-year-old girl with long silver hair, bright green eyes, small frame",
      "personality": "Brave, curious, kind-hearted",
      "typical_emotions": "Wonder, determination, occasional fear"
    }
  ],
  "locations": [
    {
      "name": "Enchanted Forest",
      "visual_description": "Dense ancient forest with purple-glowing mushrooms, twisted oak trees, mist rolling through clearings",
      "atmosphere": "Mysterious, magical, slightly eerie"
    }
  ],
  "chunk_analysis": [
    {
      "chunk_index": 0,
      "dramatic_score": 0.7,  // 0.0 to 1.0
      "characters_present": ["Luna"],
      "locations_present": ["Enchanted Forest"],
      "visual_moment": "Luna discovers the glowing door behind the ancient oak tree"
    }
  ]
}
```

**Pass 2: Consolidation (after all batches complete)**
```
System Prompt:
You are an expert at consolidating character and location descriptions from multiple sources.

User Prompt:
I have analyzed a book in batches and found the following characters and locations mentioned across different sections. Consolidate these into the 5 MOST IMPORTANT characters and 5 MOST IMPORTANT locations, merging duplicate descriptions.

[Insert all characters from all batches]
[Insert all locations from all batches]

Criteria for "most important":
- Frequency of appearance (how many chunks they appear in)
- Narrative centrality (main protagonist, key antagonist, primary setting)
- Visual distinctiveness (unique, memorable appearance)

Return the top 5 of each with consolidated, detailed descriptions.
```

**Pass 3: Enrichment (update chunk metadata)**
```
For each chunk:
  - Update dramatic_score (from chunk_analysis)
  - Create chunk_characters entries (from characters_present)
  - Create chunk_locations entries (from locations_present)

This enables queries like:
  "SELECT chunks WHERE character_id = 1 ORDER BY dramatic_score DESC"
  → Get best scenes featuring Luna
```

**Cost Breakdown Example (500-page book):**
- Total chunks: ~166 (500 pages ÷ 3 pages per chunk)
- Batches: 12 batches (166 ÷ 14 chunks per batch)
- Cost per batch: $0.02 (GPT-4-mini)
- Pass 1 total: $0.24
- Pass 2 (consolidation): $0.05
- Pass 3 (enrichment): No cost (database updates)
- **Total: $0.29 (well under $0.50 budget)**

**Database Updates:**
```sql
-- Store extracted entities
INSERT INTO characters (book_id, name, physical_description, personality_traits, typical_emotions, is_main)
VALUES (?, ?, ?, ?, ?, TRUE);

INSERT INTO locations (book_id, name, visual_description, atmosphere, is_main)
VALUES (?, ?, ?, ?, TRUE);

-- Update chunk metadata
UPDATE chunks SET dramatic_score = ? WHERE id = ?;

INSERT INTO chunk_characters (chunk_id, character_id)
VALUES (?, ?);  -- Repeat for each character in chunk

INSERT INTO chunk_locations (chunk_id, location_id)
VALUES (?, ?);  -- Repeat for each location in chunk
```

**User Experience During Analysis:**
```
Loading Screen:
┌─────────────────────────────────────────┐
│  Analyzing Your Manuscript...           │
│                                         │
│  ███████████████░░░░░░░░░░░░  65%      │
│                                         │
│  ✓ Extracted 3 characters so far        │
│  ✓ Identified 2 key locations           │
│  ⧗ Finding dramatic moments...          │
│                                         │
│  Estimated time remaining: 1 minute     │
└─────────────────────────────────────────┘
```

**Error Handling:**
- If API call fails: Retry up to 3 times with exponential backoff
- If cost exceeds $0.50: Stop and notify user ("Book too complex for automatic analysis. Contact support for manual review.")
- If no characters found: Prompt user to manually enter at least 1 character
- If analysis fails entirely: Offer refund/credit and log for investigation

**Validation:**
- Character extraction accuracy: Test against 10 sample books, target 80%+ accuracy
- Scene detection relevance: User approval rate target 70%+
- Cost compliance: Monitor actual costs, adjust batch size if needed

**Competitive Advantage:**
This feature is **unique to your platform**. Neolemon requires authors to manually describe characters and write prompts for every scene (3-5 hours per book). Your automation reduces this to 15 minutes.

---

#### 3.2.2 Reference Image Search
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want the system to suggest reference images for my characters and locations so I don't have to spend hours searching stock photo sites.

**Acceptance Criteria:**
- For each **main character** (is_main = TRUE):
  - Search for **up to 10 reference images** showing diverse views/expressions
  - Images should capture the character's physical traits from AI analysis
- For each **main location** (is_main = TRUE):
  - Search for **up to 10 reference images** showing different angles/lighting
- **Main-only mode (default):** Only search for entities marked as main (typically 1 character + 1 location)
  - Conserves API quota
  - Non-main entities receive placeholder images
  - User can toggle to search all entities
- **Search queries use only visual references** (no entity name in query text):
  - Including character/location name in the query severely limits results; queries must be built from visual descriptors only (visual tokens from chunk analyses, or physical/visual description), plus optional book context for well-known books.
- **Smart visual query algorithm** (see below): character type (man/woman/animal/AI/alien), well-known entities (canonical_search_name), and fictional-entity synonyms (search_visual_analog) drive query formation.
- **Review step before search:** User can review and edit entity summaries and proposed search query lines (from GET proposed-search-queries) on a dedicated step (e.g. Review Search page); then run reference search with optional overrides (character_queries / location_queries) via POST search-references.
- Display up to 10 images per entity in a **grid** for user selection
- User selects **1 primary reference image** per character/location (e.g. via full-size preview and "Use for AI" action)
- **Book recognition logic** improves search accuracy:
  - If well-known book: Include book title and author in queries (no entity name)
  - If unknown/original: Use descriptive (visual) searches only
- **Entity-level well-known:** Characters/locations can be marked as well-known (e.g. Easter Island, Napoleon); their canonical_search_name is used in query_text.
- **All search queries logged** (query_text contains only visual terms) for debugging and quota management

**Technical Specifications:**

**Search Query Construction (visual references only — no entity name):**

Search query text must **not** include the character or location name, to avoid over-narrowing results. Only visual descriptors and optional book context are used.

```python
def build_search_query(entity_type, entity_name, description, book_info, visual_tokens):
    """
    Build search queries using only visual references (no entity name).
    query_text saved to search_query table contains only visual terms.
    """
    suffix = " portrait" if entity_type == "character" else " landscape"
    core = visual_tokens.get("core_tokens", [])[:4]
    style = visual_tokens.get("style_tokens", [])[:2]

    # Query 1: Visual tokens from chunk analyses, or description fallback (no name)
    if core or style:
        query1 = " ".join(core + style) + suffix
    else:
        short_desc = (description or "")[:80]
        query1 = (short_desc + suffix).strip() if short_desc else suffix.strip()

    # Query 2 (well-known book only): Book context only — title + author + "illustration" (no name)
    if book_info.get("is_well_known") and (book_info.get("title") or book_info.get("author")):
        query2 = " ".join(filter(None, [book_info.get("title"), book_info.get("author"), "illustration"]))
        return [query1, query2]
    return [query1]
```

- **Result:** Up to 10 images per entity (providers requested with higher count; dedupe/filter cap at 10).

**Smart visual query algorithm (entity type, well-known, fictional):**

- **Character type (visual_type):** For characters, the first discriminator in query_text is type: `man` | `woman` | `animal` | `AI` | `alien` | `creature` | null. The search suffix is derived from visual_type (e.g. " woman portrait", " animal wolf portrait", " alien humanoid"); if null, fallback " person portrait". This avoids mixing genders/species in results.
- **Well-known entities:** For both characters and locations, optional fields `is_well_known_entity` and `canonical_search_name` (e.g. "Easter Island", "Napoleon"). When set, one query is built starting with the canonical name plus portrait/landscape suffix so that query_text in search_queries reflects the real-world name.
- **Fictional entities:** Optional `search_visual_analog` holds short descriptive synonyms/keywords for image search (e.g. "tropical island ancient statues ocean"). For non–well-known entities, queries use this analog (or aggregated visual tokens from chunk analyses) as the basis for query_text instead of raw tokens only; portrait/landscape and character type suffixes still apply.
- **Aggregation:** Visual summaries can be aggregated across all chunks where the entity appears (visual layers, mood, lighting, etc.) to form a single visual summary and search terms; search_visual_analog or search_key_traits can be filled from this step.

**Review step before reference search:**

- The review step (e.g. `/review-search`) provides **three types of input per entity:** (1) AI summary (physical_description / visual_description), (2) reference image search query lines (proposed_queries), and (3) **text-to-image prompt** — a user-editable prompt for later text-to-image generation (see visual_pipeline_architecture §5). The prompt is stored on Character and Location as `text_to_image_prompt`.
- **Proposed queries API:** `GET /books/{book_id}/proposed-search-queries` returns, for main characters and main locations, a structure with: id, name, summary, and for characters visual_type, is_well_known_entity, canonical_search_name, and for both **proposed_queries** (array of query strings) and **text_to_image_prompt** (string). Query strings include the book’s **style** (style_category from Visual Bible) so that `search_queries.query_text` reflects the user’s style choice from the create-book page.
- **Saving edits:** `PATCH /books/{book_id}/entity-summaries` accepts a body with characters (id, physical_description, text_to_image_prompt, visual_type, is_well_known_entity, canonical_search_name, search_visual_analog, etc.) and locations (id, visual_description, text_to_image_prompt, …) to persist user-edited summaries and prompts.
- **Search options (on the Review Search page):** The user can choose per run: (1) **Search engine** — Unsplash, SerpAPI, or Default (from Home Settings); (2) **Search for** — Characters only, Locations only, or Both. These are sent as `preferred_provider` and `search_entity_types` on POST search-references. The **Search for** dropdown only shows options that match the entities on the page (main characters and main locations from Analysis Review): if the user selected only characters, the page shows only "Characters only"; if only locations, only "Locations only"; if both, all three options. When only one type exists, that option is selected by default and persisted to localStorage.
- **Search with user queries:** `POST /books/{book_id}/search-references` may accept optional `character_queries`, `location_queries`, **preferred_provider** (`"unsplash"` | `"serpapi"`), and **search_entity_types** (`"characters"` | `"locations"` | `"both"`) to restrict the run to one entity type; otherwise the backend uses Unsplash first with SerpAPI fallback and searches both types. Stored `search_queries.query_text` includes the book style for each run.
- **Flow:** After Analysis Review, user goes to the review step → edits summary, search query lines, and text-to-image prompt per entity → optionally sets Search engine and Search for → "Run reference search" → PATCH entity-summaries (including text_to_image_prompt), then POST search-references with character_queries, location_queries, preferred_provider, and search_entity_types. After a successful search, the user is redirected to **Review Search Result** (`/review-search-result`).
- **Saved search options:** The last chosen "Search engine" and "Search for" on the Review Search page are persisted in localStorage per book (`review_search_options_${bookId}`) and restored when the user reopens the page.

**Review Search Result (select and save reference images):**

- The **Review Search Result** page (`/review-search-result`) is where the user selects and saves reference images for the visual bible. It is separate from the **Visual Bible** step (`/visual-bible`), which is reserved for AI image generation and the final visual bible view. After "Run reference search", the page opens on the **Characters** tab if the user searched for characters or both, and on the **Locations** tab if they searched for locations only, so the first tab matches what was just searched.
- **Persisted reference pool:** Search results are stored in the `reference_images` table (per entity: character or location). Each new search **appends** new images to the pool (no overwrite); duplicate URLs per entity are not added. A **FIFO cap of 50 images per entity** is enforced (oldest by `created_at` removed when over the limit); images currently selected by the user are never evicted. Each image has a **source**: `unsplash`, `serpapi`, or `user`.
- **Loading references:** On opening Review Search Result, the frontend calls `GET /api/books/{book_id}/reference-results`, which returns `{ characters: { entityName: images[] }, locations: { entityName: images[] } }` with each image having `url`, `thumbnail`, `width`, `height`, and **source**. If the response is empty, the page falls back to context from the just-completed search.
- **Multiple selection:** The user can select **multiple** reference images per entity ("Select for visual bible" in the lightbox adds or toggles the image). Selections are saved on **Approve & Continue** via `POST /api/books/{book_id}/visual-bible/approve` with `character_selections` and `location_selections` as maps of entity id → **array of selected URLs**. The backend stores these in `selected_reference_urls` (JSON) and sets `reference_image_url` to the first selected URL for backward compatibility.
- **Source labels:** Each thumbnail on the page displays the source (Unsplash, SerpAPI, or User). User-uploaded images are supported via **Upload image** / "Add image" per entity (see below).
- **User reference upload:** `POST /api/books/{book_id}/reference-upload` (multipart: `file`, `entity_type`, `entity_id`) accepts image files (jpeg, png, webp), saves them under `static/reference_uploads/{book_id}/{entity_type}/`, and inserts a row in `reference_images` with `source = "user"`. The uploaded image appears in the same grid and can be selected for the visual bible. FIFO trim applies to the combined pool including user uploads.

**Workflow navigation:**

- A persistent **workflow navigation bar** (WorkflowNav) is shown on all author workflow pages: Create Book → Analysis Review → Search Queries → **Search Results** (review-search-result) → **Visual Bible** (visual-bible) → Preview. Users can jump to any stage from any other stage when a book is in context.
- Workflow routes include `/create-book`, `/analysis-review`, `/review-search`, `/review-search-result`, `/visual-bible`, `/preview`, wrapped in a shared **WorkflowLayout** that renders WorkflowNav above the current page content (Outlet). The dashboard (`/`) is outside this layout.
- From the **Home dashboard**, each book in "Your Recent Projects" has a menu (⋯) to open the book at a chosen stage (Preview, Analysis Review, Search Queries, Search Results, Visual Bible, Create Book). Clicking the card still opens the book in Preview. This allows resuming work at the right step without using browser back/forward.

**Steps 11–12 — API Schemas, Scenes Router, Frontend (Feb 21, 2026):**

**Backend (Step 11):**
- New Pydantic schemas: `SceneResponse` (with auto-deserialized `t2i_prompt_json`, `scene_visual_tokens`, `characters_present`, `primary_location` from SQLAlchemy relationships), `SceneUpdateRequest`, `EngineRatingUpdate`, `EngineRatingResponse`
- New router: `app/routers/scenes.py` — `GET /books/{id}/scenes`, `PATCH /books/{id}/scenes/{id}`, `POST /books/{id}/scenes/{id}/generate-illustration` (stub, 202)
- Engine ratings endpoints added to `visual_bible.py` router: `PATCH /books/{id}/engine-ratings`, `GET /books/{id}/engine-ratings`
- `GET /books/{id}/proposed-search-queries` now includes `scenes` key (selected scenes only)
- All schemas backwards-compatible: `BookAnalyzeRequest.scene_count` defaults to 10; no breaking changes to existing endpoints

**Frontend (Step 12):**
- `api.ts`: added `SceneResponse`, `EngineRatingUpdate`, `EngineRatingResponse`, `ProposedScene` interfaces; functions `getScenes()`, `updateScene()`, `rateEngine()`, `getEngineRatings()`; `analyzeBook()` now accepts optional `scene_count`
- `BookContext.tsx`: added `sceneCount` state (default 10) and `setSceneCount()` setter
- `StyleSelector.tsx`: added **Key Scenes to Extract** input (range 3–20, default 10); `scene_count` passed to `analyzeBook()`
- `AnalysisReviewPage.tsx`: refactored to three-tab layout — **Characters** | **Locations** | **Scenes**; Scenes tab shows `SceneCard` per scene with toggle (is_selected), badge (scene_type, illustration_priority), narrative_summary, characters/location chips, editable `scene_prompt_draft`; toggle and prompt changes persist immediately via `PATCH /books/{id}/scenes/{id}`
- `ReviewSearchPage.tsx` (Search Queries step): added **Scenes section** — review/edit only with `SceneReviewCard` showing title, scene_type, narrative_summary, editable `scene_prompt_draft` (debounced save), and read-only `t2i_prompt_json.abstract` preview panel; **no T2I model selector, no generate button** on this screen
- `VisualBibleReview.tsx` (Search Results step): added 👍/👎 rating buttons (ThumbsUp/ThumbsDown icons) under each thumbnail in the grid and in the lightbox; clicking calls `rateEngine()` with the image's `source` as provider; `user`-source images are excluded from rating (no point rating user uploads); ratings are fire-and-forget (no page reload)

**Test results (Steps 11–12):**
- 21/21 integration tests passing (`tests/integration/test_scene_api.py`)
- TypeScript: 0 compilation errors
- All existing 58/58 unit tests still passing

**Multi-Provider Engine Selection (Step 9–10, Feb 21, 2026):**

Seven image search providers are now implemented, each extending `BaseImageProvider` (`app/services/providers/`):

| Provider | Free tier | Best for | Key required |
|---|---|---|---|
| **Unsplash** | 50 req/hour | Realistic human portraits, real locations | `UNSPLASH_ACCESS_KEY` |
| **SerpAPI** | 100/month free | General fallback, film stills | `SERPAPI_KEY` |
| **Pexels** | 200 req/hour | Portraits, lifestyle, nature | `PEXELS_API_KEY` |
| **Pixabay** | Unlimited | Sci-fi, fantasy, concept art (tags via `+`) | `PIXABAY_API_KEY` |
| **Openverse** | Unlimited | Open-licensed, archival content | None |
| **Wikimedia** | Unlimited | Historical figures, real locations, public domain | None |
| **DeviantArt** | Via SerpAPI | Fantasy creatures, concept art, fan-art | `SERPAPI_KEY` |

**Engine Selection Logic (`engine_selector.py`):** Automatically selects the best 2 providers per entity based on:
1. `entity_class × style_category` affinity matrix (e.g. `android|sci-fi` → pixabay + deviantart)
2. Parent class fallback chain (ENTITY_PARENT hierarchy)
3. Per-book engine ratings (user 👍/👎 feedback from Search Results)
4. Hardcoded default: unsplash + serpapi

**Query Diversification (`_build_queries_diversified()`):** Generates 4–6 semantically distinct queries per entity using ontology archetype, visual markers, visual analog, token combinations, and adaptation-specific queries for well-known books. Adaptation queries (film/TV stills) always route through SerpAPI regardless of engine ratings.

**User settings and Settings page (Bugs/enhancements 7–14, Feb 21, 2026):**

- **Settings page** (`/settings`): Reachable from the dashboard (Settings icon). (1) **Reference image search engines** — List from `GET /api/settings/providers` (name, label, available per provider); checkboxes "Use this engine" with default = all available; selection persisted in localStorage (`yread_enabled_providers`) and sent as `enabled_providers` on `POST /books/{id}/search-references`. (2) **Engine ratings** — Book selector and table showing likes/dislikes per provider for the selected book (from `GET /books/{id}/engine-ratings`).
- **Well-known published book:** When "This is a well-known published book" is checked on Key Parameters, two fields are shown: **Author** and **Title of the book** (e.g. "A Study in Scarlet"). Backend stores `well_known_book_title` on Book; query building uses it for reference search. **Similar book** ("Is there another book like it?") is on the same Key Parameters step; `similar_book_title` is persisted via the analyze API.
- **Routes:** Upload/manuscript step uses paths `manuscript-upload` (e.g. `/manuscript-upload`, `/books/:bookId/manuscript-upload`). Key Parameters step heading is "Key Parameters". WorkflowNav includes a "Dashboard" link to `/`.
- **Lightbox feedback:** On Review Search Result, engine ratings are loaded and shown per provider (Likes/Dislikes counts); buttons labeled "Good source (+1)" / "Poor source (+1)"; ratings refresh after each vote.
- **API keys** (OpenAI, Unsplash, SerpAPI, Pexels, Pixabay, etc.) are documented in backend `.env.example`; Openverse and Wikimedia require no key.

**API Integration:**

**Primary: Unsplash API (Recommended for MVP)**
```python
import requests

UNSPLASH_ACCESS_KEY = os.getenv('UNSPLASH_ACCESS_KEY')

def search_unsplash(query, count=15):
    """
    Search Unsplash for pre-cleared, commercial-use images.
    Request more than 10 to allow for dedupe/filter; return up to 10 per entity.
    """
    url = "https://api.unsplash.com/search/photos"
    params = {
        'query': query,
        'per_page': count,
        'orientation': 'portrait' if 'character' in query else 'landscape'
    }
    headers = {
        'Authorization': f'Client-ID {UNSPLASH_ACCESS_KEY}'
    }
    
    response = requests.get(url, params=params, headers=headers)
    results = response.json()['results']
    
    return [{
        'url': img['urls']['regular'],
        'thumbnail': img['urls']['thumb'],
        'credit': f"Photo by {img['user']['name']} on Unsplash",
        'license': 'Unsplash License (free for commercial use)'
    } for img in results]
```

**Backup: SerpAPI (If Unsplash insufficient)**
```python
import serpapi

def search_serpapi(query, count=15):
    """
    Fallback to Google Image Search via SerpAPI.
    Request more than 10 to allow for dedupe/filter; return up to 10 per entity.
    """
    params = {
        'api_key': os.getenv('SERPAPI_KEY'),
        'engine': 'google_images',
        'q': query,
        'num': count,
        'safe': 'active',
        'tbs': 'isz:l'  # Large images only
    }
    
    search = serpapi.search(params)
    results = search['images_results']
    
    return [{
        'url': img['original'],
        'thumbnail': img['thumbnail'],
        'credit': img['source'],
        'license': 'Verify license before use'
    } for img in results[:count]]
```

**Main-Only Search Mode:**
```python
def search_references_for_book(book_id, search_all=False):
    """
    Search for reference images with main-only optimization
    
    Args:
        book_id: Book to search for
        search_all: If False, only search main entities (default)
    """
    book = get_book(book_id)
    
    if search_all:
        characters = get_characters(book_id)
        locations = get_locations(book_id)
    else:
        # Default: Only main entities
        characters = get_characters(book_id, is_main=True)
        locations = get_locations(book_id, is_main=True)
    
    queries_run = 0
    
    for character in characters:
        visual_tokens = get_visual_tokens_for_entity(book_id, character.id, 'character')
        queries = build_search_query('character', character.name,
                                     character.physical_description, book, visual_tokens)
        all_images = []
        for q in queries:
            all_images.extend(search_unsplash(q, count=15))
        images = filter_and_dedupe(all_images, max_results=10)
        save_reference_options(character.id, images)
        for q in queries:
            log_search_query(book_id, 'character', character.name, q, len(images))
        queries_run += len(queries)

    for location in locations:
        visual_tokens = get_visual_tokens_for_entity(book_id, location.id, 'location')
        queries = build_search_query('location', location.name,
                                    location.visual_description, book, visual_tokens)
        all_images = []
        for q in queries:
            all_images.extend(search_unsplash(q, count=15))
        images = filter_and_dedupe(all_images, max_results=10)
        save_reference_options(location.id, images)
        for q in queries:
            log_search_query(book_id, 'location', location.name, q, len(images))
        queries_run += len(queries)
    
    # For non-main entities, assign placeholder
    if not search_all:
        non_main_chars = get_characters(book_id, is_main=False)
        non_main_locs = get_locations(book_id, is_main=False)
        
        for entity in non_main_chars + non_main_locs:
            assign_placeholder_image(entity.id)
    
    return {
        'queries_run': queries_run,
        'cost': queries_run * 0.0 if using_unsplash else queries_run * 0.02
    }
```

**Search Query Logging:**
```sql
CREATE TABLE search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    entity_type TEXT,  -- 'character' or 'location'
    entity_name TEXT,
    query_text TEXT,
    result_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- API endpoint to view search history
GET /api/books/{book_id}/search-queries
Response: {
  "queries": [
    {
      "entity_type": "character",
      "entity_name": "Luna",
      "query": "Luna 8-year-old silver hair character illustration",
      "result_count": 3,
      "timestamp": "2026-02-10T14:30:00Z"
    }
  ]
}
```

**User Experience:**

**Step 1: Book Recognition**
```
┌─────────────────────────────────────────┐
│  Book Information                        │
│                                         │
│  Title: Luna's Adventure                │
│  Author: Jane Smith                     │
│                                         │
│  ○ Well-known published book            │
│  ● Original/unpublished work            │
│                                         │
│  [Next: Search References]              │
└─────────────────────────────────────────┘
```

**Step 2: Reference Selection (Main-Only Default)**
```
┌─────────────────────────────────────────┐
│  Select References for Main Entities    │
│                                         │
│  Main Character: Luna                   │
│  ┌─────┐ ┌─────┐ ┌─────┐               │
│  │ [1] │ │ [2] │ │ [3] │               │
│  └─────┘ └─────┘ └─────┘               │
│    ●       ○       ○                    │
│                                         │
│  Main Location: Enchanted Forest        │
│  ┌─────┐ ┌─────┐ ┌─────┐               │
│  │ [1] │ │ [2] │ │ [3] │               │
│  └─────┘ └─────┘ └─────┘               │
│    ○       ●       ○                    │
│                                         │
│  ☐ Search for all characters/locations │
│     (Uses more API quota)               │
│                                         │
│  [Approve & Continue]                   │
└─────────────────────────────────────────┘
```

**API Quota Management:**
- Unsplash Free Tier: 50 requests/hour (sufficient for most users)
- SerpAPI Free Tier: 100 searches/month (conserve with main-only mode)
- Main-only mode: ~2-5 searches per book
- All entities mode: ~10-30 searches per book

**Cost Analysis:**
- Unsplash: $0 (free tier adequate for MVP)
- SerpAPI: $0.02 per search (only if Unsplash insufficient)
- **Recommended: Start with Unsplash only, add SerpAPI in Phase 2 if needed**

**Competitive Advantage:**
Neolemon does **NOT** have integrated reference search. Authors must manually search Google/Shutterstock, download images, and upload them. Your integrated search saves 1-3 hours per book and eliminates copyright confusion.

C:\Users\dyv78\.cursor\plans\task_1.6_reference_image_search_v2_eb9050e0.plan.md



---

#### 3.2.3 Visual Bible Generation & Approval
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want to review and approve a visual style guide before illustrations are generated so I can ensure consistency and quality.

**Acceptance Criteria:**
- Visual bible includes:
  - Book title and author name
  - Selected illustration style (genre-specific template)
  - **For each main character:**
    - Name, physical description (from AI analysis)
    - Personality traits, typical emotions
    - **Up to 10 reference image options** in a grid
    - User clicks a thumbnail to view **full-size**; in the lightbox can choose **"Use for AI"** to set that image as the primary reference for generation
    - User selects 1 primary reference per character
    - **Edit description** (inline editing capability)
  - **For each main location:**
    - Name, visual description (from AI analysis)
    - Atmosphere and mood
    - **Up to 10 reference image options** in a grid
    - User clicks a thumbnail to view **full-size**; in the lightbox can choose **"Use for AI"** to set that image as the primary reference
    - User selects 1 primary reference per location
    - **Edit description** (inline editing capability)
  - Overall tone/mood description
  - Illustration frequency (user-selected)
  - Layout style (classic illustrated book)
- User can review entire visual bible in single view
- User can **approve** or **request regeneration** (re-run AI analysis)
- Upon approval, visual bible is **locked** for the book
- Locked visual bible stored as JSON for reference during generation

**Technical Specifications:**

**Visual Bible Data Structure:**
```json
{
  "book_id": 123,
  "book_title": "Luna's Adventure",
  "author_name": "Jane Smith",
  "style": {
    "category": "children_cartoon",
    "name": "Whimsical Children's Book",
    "description": "Bright, colorful, friendly cartoon style with soft edges and expressive characters"
  },
  "characters": [
    {
      "id": 1,
      "name": "Luna",
      "is_main": true,
      "physical_description": "8-year-old girl with long silver hair that shimmers in moonlight, bright green eyes, petite frame, wears a purple cloak with star patterns",
      "personality": "Brave, curious, kind-hearted, loves adventure",
      "typical_emotions": "Wonder, determination, occasional fear when facing danger",
      "reference_image_url": "https://images.unsplash.com/photo-xyz",
      "reference_credit": "Photo by John Doe on Unsplash",
      "user_edited": false
    }
  ],
  "locations": [
    {
      "id": 1,
      "name": "Enchanted Forest",
      "is_main": true,
      "visual_description": "Dense ancient forest with towering oak trees twisted into fantastical shapes, purple-glowing mushrooms lighting the pathways, perpetual mist rolling through clearings, shafts of moonlight filtering through canopy",
      "atmosphere": "Mysterious, magical, slightly eerie yet beautiful",
      "reference_image_url": "https://images.unsplash.com/photo-abc",
      "reference_credit": "Photo by Jane Photographer on Unsplash",
      "user_edited": false
    }
  ],
  "tone_description": "Whimsical fantasy adventure with elements of mystery and self-discovery. Suitable for ages 8-12.",
  "illustration_frequency": 4,  // One illustration every 4 pages
  "layout_style": "inline_classic",
  "approved_at": "2026-02-10T15:45:00Z",
  "version": 1
}
```

**User Interface Design:**

**Review Search Result screen** (selection of reference images; the **Visual Bible** step is a separate route for AI generation and final visual bible):
```
┌──────────────────────────────────────────────────────────────┐
│  Review Search Result: Luna's Adventure                      │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Style: Whimsical Children's Book                           │
│  Illustration Frequency: Every 4 pages                      │
│  Layout: Classic Illustrated Book                           │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Main Characters                                             │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Luna ⭐                                    [Edit]      │ │
│  │  ┌──────────┐                                          │ │
│  │  │          │  8-year-old girl with long silver hair  │ │
│  │  │  Image   │  that shimmers, bright green eyes...    │ │
│  │  │          │                                          │ │
│  │  └──────────┘  Personality: Brave, curious, kind      │ │
│  │                                                        │ │
│  │  Reference images (pool up to 50; source: Unsplash/SerpAPI/User) │
│  │  [img1][img2][img3][img4][img5]  [Select for visual bible] in modal │
│  │  [img6][img7][img8][img9][img10]  Multiple selection; Add image ↑  │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Supporting Character: Old Wizard          [Edit]      │ │
│  │  (Uses placeholder - not searched)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Main Locations                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Enchanted Forest ⭐                        [Edit]      │ │
│  │  ┌──────────┐                                          │ │
│  │  │          │  Dense ancient forest with towering     │ │
│  │  │  Image   │  oak trees, purple-glowing mushrooms... │ │
│  │  │          │                                          │ │
│  │  └──────────┘  Atmosphere: Mysterious, magical        │ │
│  │                                                        │ │
│  │  Reference images (pool up to 50; source: Unsplash/SerpAPI/User) │
│  │  [img1][img2][img3][img4][img5]  [Select for visual bible] in modal │
│  │  [img6][img7][img8][img9][img10]  Multiple selection; Add image ↑  │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│  Tone & Style                                                │
│  Whimsical fantasy adventure with mystery and self-         │
│  discovery. Ages 8-12.                              [Edit]  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  [Regenerate Analysis] [Approve & Generate Book]            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Inline Editing:**
- Click [Edit] button next to any description
- Text becomes editable textarea
- Save changes inline
- Mark field as `user_edited: true` in database
- User edits take precedence over AI-generated content

**API Endpoints:**
```
GET /api/books/{book_id}/visual-bible
Response: Visual bible JSON (see structure above)

PUT /api/books/{book_id}/visual-bible/character/{character_id}
Body: {
  "physical_description": "Updated description...",
  "reference_image_url": "https://..."
}
Response: Updated character object

GET /api/books/{book_id}/reference-results
Response: { characters: { entityName: [{ url, thumbnail, width?, height?, source }] }, locations: { ... } }
  (source: "unsplash" | "serpapi" | "user")

POST /api/books/{book_id}/reference-upload
Body: multipart form (file, entity_type, entity_id)
Response: { url, thumbnail, source: "user", id }

POST /api/books/{book_id}/visual-bible/approve
Body: { character_selections: { entityId: [urls] }, location_selections: { entityId: [urls] } }
Response: {
  "status": "approved",
  "approved_at": "2026-02-10T15:45:00Z",
  "next_step": "generate_illustrations"
}

POST /api/books/{book_id}/visual-bible/regenerate
Body: (empty - triggers re-analysis)
Response: {
  "status": "analyzing",
  "job_id": "abc-123"
}
```

**Approval Workflow:**
1. User reviews visual bible
2. User edits descriptions if needed
3. User selects reference images
4. User clicks "Approve & Generate Book"
5. System locks visual bible (cannot edit after approval)
6. System proceeds to illustration generation

**Re-generation Workflow:**
1. User clicks "Regenerate Analysis"
2. System shows confirmation: "This will delete existing visual bible and re-analyze the manuscript. Continue?"
3. If confirmed:
   - Delete all characters, locations, visual bible record
   - Delete all chunk enrichment data
   - Re-run AI analysis from scratch
   - Present new visual bible for approval
4. Note: Preserves book record and text chunks (don't re-chunk)

**Database Schema:**
```sql
CREATE TABLE visual_bible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE NOT NULL,
    style_category TEXT NOT NULL,  -- 'children_cartoon', 'fantasy_epic', etc.
    tone_description TEXT,
    illustration_frequency INTEGER DEFAULT 4,  -- Pages between illustrations
    layout_style TEXT DEFAULT 'inline_classic',
    visual_bible_json TEXT,  -- Full JSON blob (see structure above)
    approved_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

-- Update characters/locations tables
ALTER TABLE characters ADD COLUMN reference_image_url TEXT;
ALTER TABLE characters ADD COLUMN reference_credit TEXT;
ALTER TABLE characters ADD COLUMN user_edited BOOLEAN DEFAULT FALSE;

ALTER TABLE locations ADD COLUMN reference_image_url TEXT;
ALTER TABLE locations ADD COLUMN reference_credit TEXT;
ALTER TABLE locations ADD COLUMN user_edited BOOLEAN DEFAULT FALSE;
```

**Validation:**
- At least 1 main character required (enforce during approval)
- At least 1 main location recommended (warn if missing, allow proceed)
- All main entities must have reference images selected
- Description fields cannot be empty

**User Feedback:**
- After approval, show confirmation: "Visual bible approved! Generating your illustrated book now..."
- Estimated time to first illustrations: 5-10 minutes
- Progress updates during generation

**Competitive Advantage:**
This approval step gives authors control without complexity. Neolemon has character profiles, but your automatic extraction + easy editing is faster. Authors spend 2-3 minutes reviewing vs 30-60 minutes manually entering everything.

---

### 3.3 Illustration Generation

#### 3.3.1 Character Consistency via Leonardo AI Character Reference
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I need my characters to look consistent across all 30+ illustrations so readers recognize them throughout the book.

**Acceptance Criteria:**
- Character consistency: ≥85% (measured by visual similarity across illustrations)
- Use API-native character reference features (no custom model training required)
- Pass user-selected reference image to each generation
- Generation time: <30 seconds per image
- No training delay - instant generation after visual bible approval
- Cost per illustration: ~$0.015 (using Leonardo AI)

**Technical Specifications:**

**Leonardo AI Character Reference System:**

Leonardo AI provides built-in character consistency through their "Character Reference" feature, eliminating the need for custom LoRA training. This approach is:
- ✅ Faster to implement (1 week vs 4 weeks for LoRA pipeline)
- ✅ Lower cost ($0 GPU rental vs $2-6 per book)
- ✅ Simpler infrastructure (API calls only, no GPU orchestration)
- ✅ Instant results (no 2-4 hour training delay)
- ✅ Good quality (85-92% consistency, proven sufficient by Neolemon's 23K users)

**Implementation:**

```python
from leonardo_ai import Client
import os

# Initialize Leonardo AI client
leonardo = Client(api_key=os.getenv('LEONARDO_API_KEY'))

def generate_scene_illustration(scene, characters_present, visual_bible):
    """
    Generate illustration for a specific scene using Leonardo AI
    
    Args:
        scene: Scene object with description and chunk text
        characters_present: List of character objects in this scene
        visual_bible: Visual bible containing style preferences
    
    Returns:
        Generated image URL
    """
    
    # Build scene prompt from manuscript chunk + character descriptions
    prompt = build_scene_prompt(scene, characters_present, visual_bible)
    
    # Get main character reference image (if present in scene)
    main_character = get_main_character_in_scene(characters_present)
    character_reference = main_character.reference_image_url if main_character else None
    
    # Generate illustration with character reference
    response = leonardo.generate_image(
        prompt=prompt,
        character_reference_image=character_reference,  # API handles consistency
        model="leonardo-vision-xl",  # Or genre-specific model
        width=1024,
        height=1536,  # Portrait orientation for books
        num_images=1,
        guidance_scale=7.0,
        num_inference_steps=30
    )
    
    # Leonardo AI returns generation job ID
    job_id = response['generation_id']
    
    # Poll for completion (typically 15-30 seconds)
    image_url = wait_for_generation(job_id)
    
    return image_url

def build_scene_prompt(scene, characters_present, visual_bible):
    """
    Build detailed prompt from scene context
    """
    # Extract key visual moment from chunk
    visual_moment = scene.visual_moment or scene.chunk.text[:200]
    
    # Add character descriptions
    char_descriptions = []
    for char in characters_present:
        if char.is_main:
            # Main characters: Brief mention (reference image handles details)
            char_descriptions.append(f"{char.name}")
        else:
            # Supporting characters: Full description (no reference image)
            char_descriptions.append(f"{char.name}: {char.physical_description}")
    
    # Build prompt
    prompt = f"{visual_moment}. "
    
    if char_descriptions:
        prompt += f"Characters: {', '.join(char_descriptions)}. "
    
    # Add location context if present
    locations = get_chunk_locations(scene.chunk_id)
    if locations:
        loc_desc = [f"{loc.name}: {loc.visual_description}" for loc in locations if loc.is_main]
        if loc_desc:
            prompt += f"Setting: {', '.join(loc_desc)}. "
    
    # Add style directive from visual bible
    prompt += f"Style: {visual_bible['style']['description']}. "
    
    # Add genre-specific keywords
    genre_keywords = get_genre_keywords(visual_bible['style']['category'])
    prompt += f"{genre_keywords}"
    
    return prompt

def wait_for_generation(job_id, timeout=60):
    """
    Poll Leonardo AI API for generation completion
    """
    import time
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        status = leonardo.get_generation(job_id)
        
        if status['status'] == 'COMPLETE':
            return status['generated_images'][0]['url']
        elif status['status'] == 'FAILED':
            raise Exception(f"Generation failed: {status.get('error')}")
        
        time.sleep(3)  # Check every 3 seconds
    
    raise TimeoutError(f"Generation timed out after {timeout} seconds")
```

**Multi-Character Scene Handling:**

For scenes with multiple characters, Leonardo AI's character reference works best with the primary character. Supporting characters are described in the prompt.

```python
def handle_multi_character_scene(scene, characters):
    """
    Strategy for scenes with multiple characters
    """
    # Prioritize main character for reference image
    main_char = next((c for c in characters if c.is_main), None)
    
    if main_char:
        # Use main character reference
        reference_image = main_char.reference_image_url
        
        # Describe other characters in prompt
        other_chars = [c for c in characters if c.id != main_char.id]
        other_descriptions = [
            f"{c.name}: {c.physical_description}" 
            for c in other_chars
        ]
        
        prompt_addition = f"Also present: {', '.join(other_descriptions)}"
    else:
        # No main character in scene - describe all characters in prompt
        reference_image = None
        prompt_addition = ", ".join([
            f"{c.name}: {c.physical_description}" 
            for c in characters
        ])
    
    return reference_image, prompt_addition
```

**Leonardo AI Pricing:**

```python
# Leonardo AI token-based pricing
LEONARDO_PRICING = {
    'maestro_monthly': 48.00,  # $48/month
    'tokens_per_month': 25000,
    'tokens_per_image': 8,  # 1024x1536 image
    'images_per_month': 3125,  # 25000 / 8
    'cost_per_image': 0.015,  # $48 / 3125
}

def calculate_book_cost(num_illustrations):
    """
    Calculate Leonardo AI cost for book
    """
    return num_illustrations * LEONARDO_PRICING['cost_per_image']

# Example: 125 illustrations = 125 * $0.015 = $1.88
```

**Database Schema:**

No complex LoRA storage needed - just track API usage:

```sql
-- Simplified - no LoRA table needed
ALTER TABLE illustrations ADD COLUMN leonardo_job_id TEXT;
ALTER TABLE illustrations ADD COLUMN generation_time_seconds INTEGER;
ALTER TABLE illustrations ADD COLUMN tokens_used INTEGER DEFAULT 8;

-- Track API usage for billing
CREATE TABLE api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    service TEXT DEFAULT 'leonardo_ai',
    tokens_used INTEGER,
    cost_usd REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

**API Integration Workflow:**

```python
@app.post("/api/books/{book_id}/visual-bible/approve")
def approve_visual_bible(book_id: int):
    """
    When visual bible approved, start illustration generation immediately
    """
    vb = get_visual_bible(book_id)
    
    # Mark as approved
    vb.approved_at = datetime.now()
    save_visual_bible(vb)
    
    # Calculate illustration points
    illustration_points = calculate_illustration_points(book_id)
    
    # Create illustration jobs
    for point in illustration_points:
        create_illustration_job(
            book_id=book_id,
            chunk_id=point.chunk_id,
            page_number=point.page_number,
            status='pending'
        )
    
    # Start generation immediately (no training delay!)
    start_illustration_generation(book_id)
    
    return {
        "status": "approved",
        "illustration_jobs_created": len(illustration_points),
        "estimated_time": len(illustration_points) * 30,  # 30 sec per image
        "estimated_cost": len(illustration_points) * 0.015
    }
```

**Quality Assurance:**

```python
def validate_character_consistency(book_id):
    """
    Check character consistency across illustrations
    
    Uses image similarity detection to measure consistency
    """
    illustrations = get_illustrations(book_id, status='completed')
    main_char = get_main_character(book_id)
    
    # Get all illustrations featuring main character
    char_illustrations = [
        ill for ill in illustrations 
        if main_char.id in get_illustration_characters(ill.id)
    ]
    
    if len(char_illustrations) < 2:
        return 1.0  # Not enough data
    
    # Compare consecutive illustrations for visual similarity
    # (Use CLIP embeddings or similar)
    similarity_scores = []
    for i in range(len(char_illustrations) - 1):
        score = compare_character_appearance(
            char_illustrations[i].image_path,
            char_illustrations[i+1].image_path,
            focus_on='character'
        )
        similarity_scores.append(score)
    
    avg_consistency = sum(similarity_scores) / len(similarity_scores)
    
    return avg_consistency  # Target: ≥0.85 (85%)
```

**Regeneration for Quality Control:**

```python
@app.post("/api/illustrations/{illustration_id}/regenerate")
def regenerate_illustration(illustration_id: int, reason: str = None):
    """
    Allow authors to regenerate specific illustrations if unsatisfied
    """
    illustration = get_illustration(illustration_id)
    
    # Mark old version
    illustration.status = 'superseded'
    illustration.superseded_reason = reason
    save_illustration(illustration)
    
    # Create new generation job
    new_job = create_illustration_job(
        book_id=illustration.book_id,
        chunk_id=illustration.chunk_id,
        page_number=illustration.page_number,
        status='pending',
        parent_illustration_id=illustration_id
    )
    
    # Generate new version
    generate_illustration(new_job.id)
    
    return {"new_illustration_id": new_job.id}
```

**Competitive Advantage:**

This API-native approach provides:
- ✅ **85-92% consistency** (Neolemon proves this is sufficient for market)
- ✅ **Instant generation** (no training delay)
- ✅ **Lower costs** ($0 GPU rental)
- ✅ **Simpler architecture** (faster MVP, less maintenance)
- ✅ **Same differentiation** (manuscript analysis automation still unique)

**Future Enhancement (Phase 2): Custom LoRA Training**

If beta testing reveals users demand >95% consistency, we can add custom LoRA training as a **premium feature** ($79/mo Professional tier):

```
Phase 2 Premium Feature:
- "Studio Quality Character Training"
- Custom LoRA models for perfect consistency
- 4-6 hour training time (acceptable for premium users)
- Reusable across book series
- Market as competitive differentiator if needed

Decision criteria:
- >30% of beta users complain about consistency
- Competitive pressure (if others offer better)
- Premium tier demand validation
```

See Appendix 12.4 for detailed LoRA training implementation if needed in Phase 2.

---

#### 3.3.2 Smart Illustration Placement
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want illustrations placed at key narrative moments throughout the book based on my preferred frequency.

**Acceptance Criteria:**
- **First illustration on page 1** (always, sets visual tone)
- Subsequent illustrations every N pages (user configurable: 2, 4, 8, 12 pages)
- Within each N-page window, illustration placed at **most dramatic moment**
- Total illustrations calculated before generation: `(total_pages / N) + 1`
- Author can override AI placement (manual selection during preview)
- Illustration points marked in database for generation queue

**Technical Specifications:**

**Placement Algorithm:**
```python
def calculate_illustration_points(book_id):
    """
    Determine which chunks should get illustrations
    
    Returns list of chunk IDs to illustrate
    """
    book = get_book(book_id)
    vb = get_visual_bible(book_id)
    
    frequency = vb['illustration_frequency']  # e.g., 4 pages
    total_pages = book.total_pages
    
    # Calculate number of illustrations
    num_illustrations = (total_pages // frequency) + 1  # +1 for page 1
    
    # Chunk size is ~3 pages, so frequency in chunks:
    chunks_per_window = frequency // 3
    
    chunks = get_chunks(book_id)
    illustration_points = []
    
    # First illustration: Always page 1 (chunk 0)
    illustration_points.append(chunks[0].id)
    
    # Subsequent illustrations: Most dramatic chunk in each window
    for window_start in range(chunks_per_window, len(chunks), chunks_per_window):
        window_end = window_start + chunks_per_window
        window_chunks = chunks[window_start:window_end]
        
        # Select chunk with highest dramatic_score
        best_chunk = max(window_chunks, key=lambda c: c.dramatic_score)
        illustration_points.append(best_chunk.id)
    
    return illustration_points

# Example output for 100-page book with illustration every 4 pages:
# → 26 illustrations (100/4 + 1)
# → Chunk IDs: [0, 5, 9, 14, 18, 23, ...]
```

**Dramatic Score Calculation (from AI Analysis):**
```python
# During AI analysis, each chunk is scored 0.0 to 1.0
# Factors considered:
# - Action level (chase, fight, discovery)
# - Emotional intensity (fear, joy, sadness)
# - Visual density (descriptive language, sensory details)
# - Narrative importance (climax, turning point)

Example dramatic_scores:
Chunk 0: 0.6  # Opening scene - medium drama
Chunk 1: 0.3  # Exposition - low drama
Chunk 2: 0.9  # Luna discovers the glowing door - HIGH drama ← Illustrate this
Chunk 3: 0.4  # Dialogue scene - low drama
```

**Preview & Manual Override:**
```python
@app.get("/api/books/{book_id}/illustration-points")
def get_illustration_points(book_id: int):
    """
    Return proposed illustration points for author review
    """
    auto_points = calculate_illustration_points(book_id)
    
    return {
        "total_illustrations": len(auto_points),
        "frequency": get_visual_bible(book_id)['illustration_frequency'],
        "points": [
            {
                "chunk_id": chunk_id,
                "page": get_chunk(chunk_id).start_page,
                "excerpt": get_chunk(chunk_id).text[:200] + "...",
                "dramatic_score": get_chunk(chunk_id).dramatic_score,
                "ai_selected": True
            }
            for chunk_id in auto_points
        ]
    }

@app.post("/api/books/{book_id}/illustration-points/{chunk_id}/toggle")
def toggle_illustration_point(book_id: int, chunk_id: int):
    """
    Allow author to manually add/remove illustration points
    """
    # Toggle illustration flag for this chunk
    chunk = get_chunk(chunk_id)
    chunk.has_illustration = not chunk.has_illustration
    save_chunk(chunk)
    
    return {"chunk_id": chunk_id, "has_illustration": chunk.has_illustration}
```

**User Interface:**
```
┌──────────────────────────────────────────────────────────────┐
│  Illustration Placement Review                               │
├──────────────────────────────────────────────────────────────┤
│  Your 100-page book will have 26 illustrations              │
│  (One every 4 pages)                                         │
│                                                              │
│  Click any scene to add/remove illustration:                │
│                                                              │
│  ✓ Page 1: "Luna sat by the window, staring at the moon..." │
│  ○ Page 4: "Her mother called from downstairs..."           │
│  ✓ Page 8: "Luna discovered the glowing door behind..."     │
│  ○ Page 10: "She hesitated, her heart racing..."            │
│  ✓ Page 12: "Inside the door was a spiral staircase..."     │
│                                                              │
│  [Generate Illustrations]                                    │
└──────────────────────────────────────────────────────────────┘

✓ = Selected for illustration (blue highlight)
○ = Not selected (grey, clickable to add)
```

**Database Schema:**
```sql
-- Add to chunks table
ALTER TABLE chunks ADD COLUMN has_illustration BOOLEAN DEFAULT FALSE;
ALTER TABLE chunks ADD COLUMN illustration_override BOOLEAN DEFAULT FALSE;
  -- TRUE if author manually selected/deselected this chunk

-- Update during placement calculation
UPDATE chunks 
SET has_illustration = TRUE 
WHERE id IN (calculated_chunk_ids);
```

**Generation Queue:**
```python
def create_illustration_jobs(book_id):
    """
    Create illustration generation jobs for all selected chunks
    """
    chunks_to_illustrate = get_chunks(book_id, has_illustration=True)
    
    for i, chunk in enumerate(chunks_to_illustrate):
        create_illustration_record(
            book_id=book_id,
            chunk_id=chunk.id,
            page_number=chunk.start_page,
            priority=i,  # Generate in order (page 1 first)
            status='pending'
        )
    
    # Start generation queue
    start_illustration_generation(book_id)
```

**Competitive Advantage:**
This is smarter than random placement or manual-only selection. Neolemon leaves placement entirely to authors (they must decide every scene). Your AI assistance speeds up workflow while giving authors final control.

---

#### 3.3.3 Illustration Generation & Progressive Loading
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want to see my illustrated book quickly without waiting hours for all 100+ illustrations to generate.

**Acceptance Criteria:**
- **Initial batch:** Generate first 5 illustrations immediately (5-10 minutes)
- Author can preview book after first 5 complete
- **Background generation:** Remaining illustrations generate in background queue
- Progress indicator shows "Generating illustration 6 of 26..."
- Author can download partial book (with placeholders for pending illustrations)
- Final book ready when all illustrations complete

**Technical Specifications:**

**Generation Strategy:**

**Phase 1: Priority Generation (First 5)**
```python
@app.post("/api/books/{book_id}/generate-illustrations")
def start_illustration_generation(book_id: int):
    """
    Begin illustration generation process
    """
    # Get all illustration jobs
    jobs = get_illustration_jobs(book_id, status='pending')
    priority_jobs = jobs[:5]  # First 5
    background_jobs = jobs[5:]  # Remaining
    
    # Generate first 5 synchronously (user waits)
    for job in priority_jobs:
        generate_illustration(job.id)
        update_job_status(job.id, 'completed')
    
    # Queue remaining for background processing
    for job in background_jobs:
        queue_background_job(job.id)
    
    return {
        "status": "generating",
        "priority_complete": 5,
        "total": len(jobs),
        "estimated_time_remaining": len(background_jobs) * 30  # 30 sec per image
    }
```

**Phase 2: Background Queue Processing**
```python
def background_illustration_worker():
    """
    Worker process that generates illustrations in background
    """
    while True:
        job = get_next_illustration_job()
        
        if job:
            try:
                generate_illustration(job.id)
                update_job_status(job.id, 'completed')
                notify_author_if_complete(job.book_id)
            except Exception as e:
                update_job_status(job.id, 'failed')
                log_error(job.id, str(e))
        
        time.sleep(10)  # Check queue every 10 seconds

def generate_illustration(job_id):
    """
    Generate single illustration
    """
    job = get_illustration_job(job_id)
    chunk = get_chunk(job.chunk_id)
    vb = get_visual_bible(job.book_id)
    
    # Build scene description from chunk
    scene_description = chunk.text[:500]  # First 500 chars as context
    
    # Get characters/locations in this chunk
    characters = get_chunk_characters(chunk.id)
    locations = get_chunk_locations(chunk.id)
    
    # Build full prompt
    prompt = f"Scene: {scene_description}\n\n"
    
    if characters:
        char_desc = [c.physical_description for c in characters]
        prompt += f"Characters: {', '.join(char_desc)}\n\n"
    
    if locations:
        loc_desc = [l.visual_description for l in locations]
        prompt += f"Setting: {', '.join(loc_desc)}\n\n"
    
    prompt += f"Style: {vb['style']['description']}"
    
    # Generate with character LoRAs loaded
    lora_paths = [get_character_lora_path(c.id) for c in characters]
    image = generate_with_loras(prompt, lora_paths)
    
    # Save image
    filename = f"book_{job.book_id}_page_{job.page_number}.png"
    filepath = f"/data/illustrations/{job.book_id}/{filename}"
    image.save(filepath)
    
    # Update database
    update_illustration_job(job_id, {
        'image_path': filepath,
        'prompt': prompt,
        'status': 'completed',
        'generated_at': datetime.now()
    })
    
    return filepath
```

**Progress Tracking:**
```python
@app.get("/api/books/{book_id}/generation-progress")
def get_generation_progress(book_id: int):
    """
    Real-time progress for illustration generation
    """
    jobs = get_illustration_jobs(book_id)
    completed = [j for j in jobs if j.status == 'completed']
    pending = [j for j in jobs if j.status == 'pending']
    failed = [j for j in jobs if j.status == 'failed']
    
    return {
        "total": len(jobs),
        "completed": len(completed),
        "pending": len(pending),
        "failed": len(failed),
        "percent_complete": (len(completed) / len(jobs)) * 100,
        "estimated_time_remaining": len(pending) * 30,  # seconds
        "current_job": pending[0].page_number if pending else None
    }
```

**User Experience:**

**Step 1: Initial Generation (User Waits)**
```
┌──────────────────────────────────────────────────────────────┐
│  Generating Your Illustrated Book...                        │
│                                                              │
│  ████████████████░░░░░░░░░░░░░░░░░░░░░░  5 of 26 complete  │
│                                                              │
│  ✓ Page 1 illustration ready                                │
│  ✓ Page 4 illustration ready                                │
│  ✓ Page 8 illustration ready                                │
│  ✓ Page 12 illustration ready                               │
│  ✓ Page 16 illustration ready                               │
│  ⧗ Page 20 generating...                                    │
│                                                              │
│  Estimated time for first 5: 3 minutes                      │
│                                                              │
│  [Preview Book Now] (available after first 5)               │
└──────────────────────────────────────────────────────────────┘
```

**Step 2: Background Generation (User Can Preview)**
```
┌──────────────────────────────────────────────────────────────┐
│  Book Preview: Luna's Adventure                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Page 1 with illustration]                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Background generation in progress:                         │
│  12 of 26 illustrations complete                            │
│  Estimated time remaining: 7 minutes                        │
│                                                              │
│  [Download Partial Book] [Wait for Complete Book]           │
└──────────────────────────────────────────────────────────────┘
```

**Database Schema:**
```sql
CREATE TABLE illustrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    image_path TEXT,
    prompt TEXT,
    style TEXT,
    reference_images TEXT,  -- JSON array of reference URLs used
    status TEXT DEFAULT 'pending',  -- pending, generating, completed, failed
    priority INTEGER DEFAULT 999,  -- Lower = higher priority
    generated_at TIMESTAMP,
    error_message TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE INDEX idx_illustrations_status ON illustrations(book_id, status);
CREATE INDEX idx_illustrations_priority ON illustrations(book_id, priority, status);
```

**Error Handling:**
```python
# If generation fails (API error, timeout, etc.)
# Retry up to 3 times
# If still fails, use placeholder image

PLACEHOLDER_IMAGE_PATH = "/static/placeholder_illustration.png"

def generate_with_retry(job_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return generate_illustration(job_id)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                # Final failure, use placeholder
                log_error(job_id, f"Failed after {max_retries} attempts: {e}")
                use_placeholder(job_id)
                return PLACEHOLDER_IMAGE_PATH
```

**Cost Management:**
```python
# Track generation costs
generation_cost_per_image = 0.02  # GeminiGen pricing

@app.get("/api/books/{book_id}/generation-cost")
def get_generation_cost(book_id: int):
    jobs = get_illustration_jobs(book_id)
    total_cost = len(jobs) * generation_cost_per_image
    
    return {
        "total_illustrations": len(jobs),
        "cost_per_image": generation_cost_per_image,
        "total_cost": total_cost
    }

# Example: 26 illustrations × $0.02 = $0.52
```

**Competitive Advantage:**
Progressive loading is better UX than Neolemon's "wait for everything" approach. Authors can start reviewing their book immediately, reducing perceived wait time.

---

### 3.4 Cover Generation (NEW - Critical B2B Feature)

#### 3.4.1 Automated Cover Design
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want a professionally designed book cover so I have a complete publishing package without hiring a designer.

**Cover-Only Generation Option:**
Authors should be able to generate **only the cover** without creating interior illustrations for the manuscript. This workflow still requires visual bible creation (to extract main characters/locations for the cover visual) but skips the full illustration generation process.

**Use Cases for Cover-Only:**
- Authors who only need a cover design (already have interior illustrations or text-only book)
- Authors testing the platform before committing to full illustration package
- Authors on tight budgets prioritizing cover over interior illustrations
- Authors creating multiple cover variations to A/B test on Amazon KDP

**Acceptance Criteria:**
- Cover includes:
  - **Front cover:** Title, author name, key visual (main character or location)
  - **Back cover:** Book description/blurb, barcode placeholder, author bio (optional)
  - **Spine:** Title, author name (auto-sized based on page count)
- Genre-specific templates (fantasy, children's, romance, thriller, etc.)
- Spine width auto-calculated based on page count and paper type
- KDP-ready dimensions with bleed (0.125")
- Author can customize text, colors, layout
- Preview before finalizing
- **Cover-only workflow:**
  - Upload manuscript OR enter book details manually (title, page count, genre)
  - AI extracts main character/location for cover visual (or user provides description)
  - Generate visual bible with 1-2 main entities only
  - Generate cover (skip interior illustration generation)
  - Download cover.pdf immediately

**Technical Specifications:**

**Workflow Options:**

**Option 1: Full Book (Cover + Interior Illustrations)**
```
Upload manuscript → AI analysis → Visual bible → Generate illustrations → Generate cover → Export KDP package
```

**Option 2: Cover Only (NEW)**
```
Upload manuscript OR manual entry → Minimal AI analysis (extract 1 main character/location) → 
Visual bible (cover entities only) → Generate cover → Download cover.pdf
```

**Cover Generation Workflow:**

**Step 1: Calculate Spine Width**
```python
def calculate_spine_width(page_count, paper_type='white'):
    """
    KDP spine width formula
    
    Args:
        page_count: Total pages in book (must be even for paperback)
        paper_type: 'white' or 'cream'
    
    Returns:
        Spine width in inches
    """
    if paper_type == 'white':
        ppi = 0.0025  # Pages per inch for white paper
    else:  # cream
        ppi = 0.00252
    
    if page_count % 2 != 0:
        page_count += 1  # Round up to even number
    
    spine_width = page_count * ppi
    
    # KDP minimum spine width: 0.06" (24 pages min)
    return max(spine_width, 0.06)

# Example: 100-page book with white paper
# → spine_width = 100 * 0.0025 = 0.25 inches
```

**Step 2: Generate Cover Visual**
```python
def generate_cover_visual(book_id):
    """
    Create main cover image (front cover visual)
    """
    vb = get_visual_bible(book_id)
    book = get_book(book_id)
    
    # Use main character or main location as cover visual
    main_char = get_characters(book_id, is_main=True)[0]
    
    # Cover-specific prompt
    prompt = f"Book cover illustration for '{book.title}'. "
    prompt += f"Centered portrait of {main_char.physical_description}. "
    prompt += f"Style: {vb['style']['description']}. "
    prompt += f"Genre: {vb['style']['category']}. "
    prompt += "Professional book cover quality, eye-catching, marketable."
    
    # Generate at higher resolution for print
    image = generate_image(
        prompt=prompt,
        reference_image=main_char.reference_image_url,
        width=1600,
        height=2400,  # Standard book cover aspect ratio
        style='book_cover'
    )
    
    return image
```

**Step 3: Composite Full Cover (Using ReportLab/PIL)**
```python
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image, ImageDraw, ImageFont

def create_kdp_cover(book_id, output_path="cover.pdf"):
    """
    Create complete KDP cover with front, back, and spine
    """
    book = get_book(book_id)
    vb = get_visual_bible(book_id)
    
    # Dimensions
    TRIM_WIDTH = 8.5 * inch  # For 8.5x8.5 children's book
    TRIM_HEIGHT = 8.5 * inch
    BLEED = 0.125 * inch
    
    spine_width_inches = calculate_spine_width(book.total_pages)
    spine_width = spine_width_inches * inch
    
    # Total cover dimensions
    total_width = (2 * TRIM_WIDTH) + spine_width + (2 * BLEED)
    total_height = TRIM_HEIGHT + (2 * BLEED)
    
    # Create PDF canvas
    c = canvas.Canvas(output_path, pagesize=(total_width, total_height))
    
    # BACK COVER (left side)
    back_x = 0
    back_width = TRIM_WIDTH + BLEED
    
    # Background color
    c.setFillColorRGB(0.95, 0.95, 0.95)  # Light gray
    c.rect(back_x, 0, back_width, total_height, fill=1)
    
    # Book description
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica", 12)
    description = book.description or "A wonderful adventure awaits..."
    c.drawString(back_x + 0.5*inch, total_height - 1*inch, description[:50])
    
    # Barcode placeholder
    c.setFont("Helvetica", 10)
    c.drawString(back_x + 0.5*inch, 0.5*inch, "Barcode placement area")
    
    # SPINE (middle)
    spine_x = back_width
    
    # Spine background
    c.setFillColorRGB(0.1, 0.1, 0.1)  # Dark gray
    c.rect(spine_x, 0, spine_width, total_height, fill=1)
    
    # Spine text (rotated)
    c.saveState()
    c.translate(spine_x + (spine_width / 2), total_height / 2)
    c.rotate(90)
    c.setFillColorRGB(1, 1, 1)  # White text
    
    # Auto-size font based on spine width
    if spine_width_inches > 0.5:
        font_size = 14
    elif spine_width_inches > 0.3:
        font_size = 12
    else:
        font_size = 10
    
    c.setFont("Helvetica-Bold", font_size)
    spine_text = f"{book.title} - {book.author_name}"
    c.drawCentredString(0, 0, spine_text)
    c.restoreState()
    
    # FRONT COVER (right side)
    front_x = spine_x + spine_width
    front_width = TRIM_WIDTH + BLEED
    
    # Load generated cover visual
    cover_image_path = get_cover_visual_path(book_id)
    c.drawImage(
        cover_image_path,
        x=front_x,
        y=0,
        width=front_width,
        height=total_height,
        preserveAspectRatio=False
    )
    
    # Overlay title and author text on front cover
    c.saveState()
    
    # Title (top)
    c.setFillColorRGB(1, 1, 1)  # White text
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(
        front_x + (front_width / 2),
        total_height - 1.5*inch,
        book.title
    )
    
    # Author name (bottom)
    c.setFont("Helvetica", 18)
    c.drawCentredString(
        front_x + (front_width / 2),
        1*inch,
        f"by {book.author_name}"
    )
    
    c.restoreState()
    
    # Save PDF
    c.save()
    
    return output_path
```

**Genre-Specific Templates:**
```python
COVER_TEMPLATES = {
    'children_cartoon': {
        'front_bg_color': (255, 240, 200),  # Warm cream
        'title_color': (50, 100, 200),  # Bright blue
        'title_font': 'ComicSans-Bold',
        'spine_color': (255, 200, 100)
    },
    'fantasy_epic': {
        'front_bg_color': (20, 20, 40),  # Dark blue
        'title_color': (255, 215, 0),  # Gold
        'title_font': 'TimesNewRoman-Bold',
        'spine_color': (40, 20, 10)
    },
    'romance': {
        'front_bg_color': (255, 200, 220),  # Soft pink
        'title_color': (150, 50, 100),  # Deep rose
        'title_font': 'Garamond-Italic',
        'spine_color': (200, 150, 180)
    },
    # ... more templates
}
```

**User Customization:**
```python
@app.put("/api/books/{book_id}/cover")
def update_cover_design(book_id: int, cover_data: dict):
    """
    Allow author to customize cover text, colors, layout
    """
    allowed_fields = ['title', 'author_name', 'description', 
                      'title_color', 'template']
    
    cover_config = get_cover_config(book_id)
    
    for field in allowed_fields:
        if field in cover_data:
            cover_config[field] = cover_data[field]
    
    save_cover_config(book_id, cover_config)
    
    # Regenerate cover with new settings
    regenerate_cover(book_id)
    
    return {"status": "updated", "cover_url": get_cover_url(book_id)}
```

**Database Schema:**
```sql
CREATE TABLE covers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE NOT NULL,
    front_visual_path TEXT,  -- Generated cover image
    full_cover_path TEXT,  -- Complete PDF with spine
    template TEXT DEFAULT 'children_cartoon',
    title_override TEXT,  -- If different from book.title
    spine_width REAL,  -- Calculated in inches
    customizations TEXT,  -- JSON of color/font overrides
    generated_at TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

**API Endpoints:**
```
# Cover-only workflow (NEW)
POST /api/books/cover-only
Body: {
  "title": "Luna's Adventure",
  "author_name": "Jane Smith",
  "page_count": 100,
  "genre": "children_fantasy",
  "description": "A young girl discovers a magical door...",
  "main_character_description": "8-year-old girl with silver hair and green eyes",
  "OR": "manuscript_text": "...",  # Optional: provide manuscript for extraction
  "paper_type": "white",
  "trim_size": "8.5x8.5"
}
Response: {
  "book_id": 123,
  "status": "analyzing",
  "workflow": "cover_only",
  "next_step": "visual_bible_review"
}

# Standard cover generation (part of full workflow)
POST /api/books/{book_id}/cover/generate
Response: { "status": "generating", "estimated_time": 60 }

GET /api/books/{book_id}/cover
Response: {
  "front_visual_url": "/api/covers/123/front.png",
  "full_cover_url": "/api/covers/123/full.pdf",
  "spine_width": 0.25,
  "template": "children_cartoon"
}

PUT /api/books/{book_id}/cover
Body: { "title_color": "#FF6B9D", "template": "romance" }
Response: { "status": "updated" }
```

**Cover-Only Implementation Example:**

```python
@app.post("/api/books/cover-only")
def create_cover_only_book(data: CoverOnlyRequest):
    """
    Create book with cover-only workflow
    
    Minimal visual bible: Extract 1 main character/location for cover visual
    Skip interior illustration generation
    """
    
    # Create book record
    book = Book(
        title=data.title,
        author_name=data.author_name,
        total_pages=data.page_count,
        genre=data.genre,
        description=data.description,
        workflow_type='cover_only',  # Flag for cover-only
        status='analyzing'
    )
    save_book(book)
    
    # Extract main character for cover
    if data.manuscript_text:
        # Use AI to extract main character
        analysis = analyze_for_cover_only(data.manuscript_text, data.genre)
        main_character = analysis['main_character']
        main_location = analysis['main_location']
    else:
        # Use provided description
        main_character = Character(
            name="Main Character",
            physical_description=data.main_character_description,
            is_main=True
        )
        main_location = None
    
    # Create minimal visual bible (cover entities only)
    visual_bible = VisualBible(
        book_id=book.id,
        style_category=data.genre,
        workflow_type='cover_only'
    )
    
    # Save entities
    if main_character:
        save_character(book.id, main_character)
    if main_location:
        save_location(book.id, main_location)
    
    # Search reference images (just for cover entities)
    search_references_for_cover_only(book.id)
    
    book.status = 'visual_bible_review'
    save_book(book)
    
    return {
        "book_id": book.id,
        "status": "analyzing",
        "workflow": "cover_only",
        "next_step": "visual_bible_review"
    }
```

**Pricing for Cover-Only:**

```python
COVER_ONLY_PRICING = {
    'ai_analysis': 0.10,  # Minimal analysis (1-2 entities only)
    'reference_search': 0.00,  # Unsplash free tier
    'cover_generation': 0.12,  # 8 Leonardo AI images for variations
    'total': 0.22  # <$0.25 per cover
}

# Compared to full book: $2.50 (analysis + 125 illustrations + cover)
# Cover-only saves: $2.28 (91% savings)
```

**Use Case Example:**

Author has written a novel but only needs a cover (no interior illustrations). They:
1. Go to platform, select "Cover Only"
2. Enter book details: title, page count, description
3. Provide main character description or upload short excerpt
4. Review visual bible (1 character reference)
5. Approve and download cover.pdf
6. Total time: 10 minutes (vs 30+ minutes for full workflow)
7. Total cost: $0.22 (vs $2.50 for full book)

**Competitive Advantage:**
Neolemon does NOT include cover generation - authors must hire designers separately ($300-800). Your integrated cover generator completes the publishing package, making you a one-stop solution.

---

### 3.5 KDP Export (NEW - Critical B2B Feature)

#### 3.5.1 Print-Ready PDF Generation
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want to export my illustrated book as KDP-ready PDFs so I can upload directly to Amazon for publishing.

**Acceptance Criteria:**
- Generate **interior.pdf** (book content with illustrations)
  - Proper bleed: 0.125" on outer edges (right edge of odd pages, left edge of even pages)
  - Margins: 0.375" inside, 0.25" outside, 0.5" top/bottom
  - 300 DPI minimum for all images
  - Embedded fonts for compatibility
- Generate **cover.pdf** (full wrap cover with spine)
  - Includes front, back, spine
  - Spine width auto-calculated
  - Proper bleed on all edges
- Support standard trim sizes:
  - 8.5" x 8.5" (children's books - square)
  - 6" x 9" (fiction - standard novel)
  - 8" x 10" (illustrated fiction - larger format)
  - 8.5" x 11" (non-fiction, workbooks)
- One-click download of complete package
- Include upload instructions PDF

**Technical Specifications:**

**Interior PDF Generation (Using ReportLab):**
```python
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

def create_kdp_interior(book_id, trim_size=(8.5, 8.5), output_path="interior.pdf"):
    """
    Generate KDP-ready interior PDF
    
    Args:
        book_id: Book to export
        trim_size: (width, height) in inches
        output_path: Where to save PDF
    """
    book = get_book(book_id)
    chunks = get_chunks(book_id)
    illustrations = get_illustrations(book_id, status='completed')
    
    # Page dimensions
    trim_width, trim_height = trim_size
    page_width = trim_width * inch
    page_height = trim_height * inch
    
    # Create document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=(page_width, page_height),
        # Margins (different for left/right pages)
        leftMargin=0.375 * inch,  # Inside margin (binding side)
        rightMargin=0.25 * inch,  # Outside margin
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch
    )
    
    # Register custom fonts (avoid system font issues)
    try:
        pdfmetrics.registerFont(TTFont('Georgia', 'Georgia.ttf'))
        pdfmetrics.registerFont(TTFont('Georgia-Bold', 'Georgia-Bold.ttf'))
    except:
        # Fallback to standard fonts
        pass
    
    # Styles
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        'BookBody',
        parent=styles['Normal'],
        fontName='Georgia',
        fontSize=12,
        leading=16,  # Line spacing
        alignment=TA_JUSTIFY,
        firstLineIndent=0.25 * inch
    )
    
    # Build content
    story = []
    
    # Title page
    title_style = ParagraphStyle(
        'Title',
        fontSize=24,
        fontName='Georgia-Bold',
        alignment=1  # Center
    )
    story.append(Paragraph(book.title, title_style))
    story.append(Paragraph(f"by {book.author_name}", styles['Normal']))
    story.append(PageBreak())
    
    # Content pages
    for chunk in chunks:
        # Check if this chunk has an illustration
        chunk_illustration = next(
            (ill for ill in illustrations if ill.chunk_id == chunk.id),
            None
        )
        
        # Add illustration if present
        if chunk_illustration:
            # Full-width illustration
            img = Image(
                chunk_illustration.image_path,
                width=page_width - doc.leftMargin - doc.rightMargin,
                height=4 * inch  # Fixed height, aspect ratio maintained
            )
            story.append(img)
            story.append(Paragraph("<br/><br/>", body_style))  # Spacing
        
        # Add text
        paragraphs = chunk.text.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para, body_style))
    
    # Build PDF
    doc.build(story)
    
    return output_path
```

**Bleed Handling for Interior:**
```python
# KDP bleed requirements:
# - Bleed only on OUTER edges (away from binding)
# - Odd pages (right-hand): bleed on right edge
# - Even pages (left-hand): bleed on left edge

def create_interior_with_bleed(book_id, trim_size=(8.5, 8.5)):
    """
    Create interior with proper bleed for print
    """
    BLEED = 0.125 * inch
    trim_width, trim_height = trim_size
    
    # Different page sizes for odd/even pages
    odd_page_size = (
        (trim_width * inch) + BLEED,  # Bleed on right
        (trim_height * inch) + (2 * BLEED)  # Top and bottom bleed
    )
    even_page_size = (
        (trim_width * inch) + BLEED,  # Bleed on left
        (trim_height * inch) + (2 * BLEED)
    )
    
    # Build PDF with alternating page sizes
    # (ReportLab doesn't easily support this, so we merge two PDFs)
    
    # Simpler approach for MVP: Use uniform bleed on all edges
    # KDP will trim correctly based on page position
    page_size = (
        (trim_width * inch) + (2 * BLEED),
        (trim_height * inch) + (2 * BLEED)
    )
    
    # ... rest of PDF generation
```

**Cover PDF Generation (Already covered in 3.4.1)**

**Complete KDP Package:**
```python
@app.post("/api/books/{book_id}/export-kdp")
def export_kdp_package(book_id: int, trim_size: str = "8.5x8.5"):
    """
    Generate complete KDP package
    
    Returns ZIP file containing:
    - interior.pdf
    - cover.pdf
    - upload_instructions.pdf
    - book_info.txt (metadata)
    """
    book = get_book(book_id)
    
    # Parse trim size
    width, height = map(float, trim_size.split('x'))
    
    # Create temp directory for this export
    export_dir = f"/tmp/kdp_export_{book_id}/"
    os.makedirs(export_dir, exist_ok=True)
    
    # Generate interior
    interior_path = create_kdp_interior(
        book_id,
        trim_size=(width, height),
        output_path=f"{export_dir}/interior.pdf"
    )
    
    # Generate cover
    cover_path = create_kdp_cover(
        book_id,
        output_path=f"{export_dir}/cover.pdf"
    )
    
    # Create upload instructions
    instructions_path = create_upload_instructions(
        book,
        trim_size=(width, height),
        output_path=f"{export_dir}/upload_instructions.pdf"
    )
    
    # Create metadata file
    with open(f"{export_dir}/book_info.txt", 'w') as f:
        f.write(f"Title: {book.title}\n")
        f.write(f"Author: {book.author_name}\n")
        f.write(f"Page Count: {book.total_pages}\n")
        f.write(f"Trim Size: {width}\" x {height}\"\n")
        f.write(f"Spine Width: {calculate_spine_width(book.total_pages)}\"\n")
    
    # ZIP everything
    zip_path = f"/tmp/kdp_package_{book_id}.zip"
    shutil.make_archive(zip_path.replace('.zip', ''), 'zip', export_dir)
    
    # Clean up temp directory
    shutil.rmtree(export_dir)
    
    return {
        "download_url": f"/api/downloads/{book_id}/kdp_package.zip",
        "files_included": ["interior.pdf", "cover.pdf", "upload_instructions.pdf", "book_info.txt"],
        "size_mb": os.path.getsize(zip_path) / (1024 * 1024)
    }
```

**Upload Instructions PDF:**
```python
def create_upload_instructions(book, trim_size, output_path):
    """
    Generate step-by-step KDP upload instructions
    """
    c = canvas.Canvas(output_path, pagesize=letter)
    
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, 10*inch, "How to Upload Your Book to Amazon KDP")
    
    c.setFont("Helvetica", 12)
    y = 9.5*inch
    
    instructions = [
        "1. Go to https://kdp.amazon.com and sign in",
        "2. Click 'Create' > 'Paperback'",
        "3. Enter book details:",
        f"   - Title: {book.title}",
        f"   - Author: {book.author_name}",
        "   - ISBN: Leave blank (KDP will assign free ISBN)",
        "4. Click 'Save and Continue'",
        "",
        "5. Upload your content:",
        "   - Manuscript: Upload 'interior.pdf'",
        f"   - Trim size: {trim_size[0]}\" x {trim_size[1]}\"",
        "   - Bleed: Yes (0.125\")",
        "   - Paper type: White or Cream",
        "   - Cover: Upload 'cover.pdf'",
        "6. Preview your book (KDP online previewer)",
        "7. Set pricing and publish!",
        "",
        f"Note: Your book has {book.total_pages} pages.",
        f"Recommended price: ${max(9.99, book.total_pages * 0.15):.2f}",
        "(Based on printing costs + reasonable profit margin)"
    ]
    
    for line in instructions:
        c.drawString(1*inch, y, line)
        y -= 0.25*inch
    
    c.save()
    return output_path
```

**Validation Before Export:**
```python
@app.get("/api/books/{book_id}/export-validation")
def validate_export_readiness(book_id: int):
    """
    Check if book is ready for KDP export
    """
    book = get_book(book_id)
    illustrations = get_illustrations(book_id)
    cover = get_cover(book_id)
    
    issues = []
    
    # Check all illustrations generated
    pending = [i for i in illustrations if i.status != 'completed']
    if pending:
        issues.append(f"{len(pending)} illustrations still generating")
    
    # Check cover exists
    if not cover or not cover.full_cover_path:
        issues.append("Cover not generated")
    
    # Check minimum page count (KDP requires 24+ pages)
    if book.total_pages < 24:
        issues.append(f"Book too short ({book.total_pages} pages, need 24+)")
    
    # Check page count is even
    if book.total_pages % 2 != 0:
        issues.append("Page count must be even (will auto-add blank page)")
    
    # Check images are 300 DPI
    low_res_images = check_image_resolution(book_id)
    if low_res_images:
        issues.append(f"{len(low_res_images)} images below 300 DPI")
    
    return {
        "ready": len(issues) == 0,
        "issues": issues,
        "can_export_anyway": len(issues) <= 2  # Minor issues OK
    }
```

**User Experience:**

```
┌──────────────────────────────────────────────────────────────┐
│  Export for Amazon KDP                                       │
├──────────────────────────────────────────────────────────────┤
│  Book: Luna's Adventure                                      │
│  Pages: 100                                                  │
│  Illustrations: 26 of 26 complete ✓                          │
│  Cover: Ready ✓                                              │
│                                                              │
│  Select Trim Size:                                           │
│  ○ 6" x 9" (Standard Fiction)                               │
│  ● 8.5" x 8.5" (Children's Books - Square)                  │
│  ○ 8" x 10" (Large Format Illustrated)                      │
│  ○ 8.5" x 11" (Workbooks, Non-Fiction)                      │
│                                                              │
│  Estimated spine width: 0.25"                               │
│  Estimated printing cost: $3.20/copy                        │
│  Suggested retail price: $15.99                             │
│                                                              │
│  [Download KDP Package]                                     │
│                                                              │
│  What's included:                                            │
│  ✓ interior.pdf (100 pages, 300 DPI)                        │
│  ✓ cover.pdf (with spine)                                   │
│  ✓ upload_instructions.pdf                                  │
│  ✓ book_info.txt (metadata)                                 │
└──────────────────────────────────────────────────────────────┘
```

**Database Schema:**
```sql
CREATE TABLE kdp_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    trim_size TEXT NOT NULL,  -- "8.5x8.5"
    interior_pdf_path TEXT,
    cover_pdf_path TEXT,
    zip_file_path TEXT,
    exported_at TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

**Competitive Advantage:**
This is THE differentiator for B2B. Neolemon outputs individual images - authors must manually assemble them into a book and figure out KDP formatting themselves (3-5 hours of work). Your one-click KDP export saves authors an entire day of frustration and makes you the complete publishing solution.

---

### 3.6 Preview Mode (Replaces Reading Interface)

#### 3.6.1 Book Preview
**Priority:** Must-Have (MVP)

**User Story:**
As an author, I want to preview my illustrated book before exporting so I can check for errors or request changes.

**Acceptance Criteria:**
- Scrollable page-by-page preview
- Shows final layout (text + illustrations)
- Zoom functionality to check illustration quality
- Navigation controls (previous/next page, jump to page)
- Flag illustrations for regeneration
- Download preview PDF (low-res, for review only)

**Technical Specifications:**

**Simple Preview Interface:**
```html
<!-- Much simpler than full reading interface -->
<div class="book-preview">
  <div class="preview-controls">
    <button onclick="previousPage()">← Previous</button>
    <span>Page <input type="number" id="pageNum" value="1"> of 100</span>
    <button onclick="nextPage()">Next →</button>
    <button onclick="zoom()">🔍 Zoom</button>
  </div>
  
  <div class="preview-page">
    <!-- Current page content -->
    <img src="/api/books/123/preview-page/1" />
  </div>
  
  <div class="illustration-controls">
    <button onclick="flagIllustration()">⚠️ Flag for Regeneration</button>
  </div>
</div>
```

**Generates Preview Images on Demand:**
```python
@app.get("/api/books/{book_id}/preview-page/{page_number}")
def get_preview_page(book_id: int, page_number: int):
    """
    Render single page as image for preview
    """
    # Get page content (text chunk + illustration if present)
    page_data = get_page_data(book_id, page_number)
    
    # Render page as image (same layout as final PDF)
    page_image = render_page_preview(page_data)
    
    return StreamingResponse(
        io.BytesIO(page_image),
        media_type="image/png"
    )
```

**Much Simpler Than Full Reading Interface:**
- No two-page spreads
- No fancy animations
- No reading progress tracking
- Just: "Show me what my book looks like"

**Competitive Advantage:**
Simple preview is all authors need. Complex reading UI is wasted development time for B2B market.

---

## 4. Future Expansion: B2C Reading Platform (Phase 4)

**NOTE:** This section preserves your original B2C vision for future expansion.

### 4.1 Strategic Rationale for Phase 4

**Why Wait Until Phase 4?**
1. **B2B revenue funds B2C development** - Use author subscriptions to build reading platform
2. **Content library growth** - By Year 2, you'll have 10,000+ illustrated books from authors
3. **Two-sided marketplace** - Authors publish, readers discover, network effects
4. **Proven model** - Like Amazon (authors publish on KDP, readers buy on Kindle)

**B2C Business Model:**
- Authors can optionally publish their illustrated books to your reading platform
- Readers subscribe ($9.99/mo) or buy individual books ($4.99 each)
- Revenue share with authors: 70% to author, 30% to platform (match Amazon)

**Timeline:**
- Phase 1-3 (Year 1): B2B only (authors creating books)
- Phase 4 (Year 2): Launch reading platform
- Phase 5 (Year 3): Mobile apps, social features

### 4.2 Deferred B2C Features (From Original Document)

**These features are preserved for Phase 4 implementation:**

#### 4.2.1 Reading Interface
- Two-page spread layout (like an open book)
- Page turn animations
- Typography: Readable serif font
- Illustration display options (inline classic, anime panels)
- Smooth scrolling and responsive design
- Keyboard navigation

#### 4.2.2 Reading Progress & Controls
- Progress bar showing % completed
- Current page / Total pages indicator
- Previous/Next page buttons
- Jump to page
- Table of contents
- Bookmarks
- Resume where left off

#### 4.2.3 User Library
- Personal reading library
- Multiple books
- Reading history
- Favorites/collections
- Cross-device sync

#### 4.2.4 Discovery & Recommendation
- Browse illustrated books by genre
- Recommendations based on reading history
- Author pages
- Reviews and ratings

#### 4.2.5 Social Features
- Share favorite illustrations
- Reading groups
- Comments/discussions
- Author-reader interaction

**Implementation Priority for Phase 4:**
1. Basic reading interface (Month 13-14)
2. Library management (Month 15)
3. Discovery features (Month 16-17)
4. Social features (Month 18+)

**Estimated Phase 4 Investment:**
- Development time: 6 months
- Team: 2-3 engineers
- Cost: $200K-300K (funded by B2B revenue)

**Success Criteria for Phase 4 Launch:**
- 10,000+ illustrated books available (from authors)
- 5,000+ reader signups in first 3 months
- 15% conversion to paid ($9.99/mo or $4.99/book)
- $50K MRR from readers by Month 18

---

## 5. Data Models (Updated for B2B)

### 5.0 Visual Semantic Engine — Schema Extensions (Feb 21, 2026)

Added as part of Refactoring Plan v3 (`visual pipeline refactoring_plan_v3.md`), Steps 1–12 (complete):

#### New Tables

| Table | Purpose |
|---|---|
| `scenes` | Narrative units extracted from chunks; spans 3–7 chunks; user-toggleable; stores `scene_prompt_draft`, `t2i_prompt_json` |
| `scene_characters` | Scene ↔ Character junction |
| `scene_locations` | Scene ↔ Location junction |
| `engine_ratings` | Per-book provider feedback (likes/dislikes per provider); feeds back into engine selection |

#### New Columns on Existing Tables

| Table | Column | Type | Purpose |
|---|---|---|---|
| `characters` | `ontology_json` | TEXT (JSON) | Full ontology dict: entity_class, materiality, power_status, visual_markers, anti_human_override, search_archetype |
| `characters` | `entity_visual_tokens_json` | TEXT (JSON) | core/style/archetype/anti tokens for entity-level search query building |
| `locations` | `ontology_json` | TEXT (JSON) | Same ontology structure for locations |
| `locations` | `entity_visual_tokens_json` | TEXT (JSON) | Visual tokens for locations |
| `books` | `scene_count` | INTEGER DEFAULT 10 | Target number of scenes to extract per book |
| `books` | `known_adaptations_json` | TEXT (JSON) | Array of known film/TV adaptations for well-known books |
| `illustrations` | `scene_id` | INTEGER (nullable FK) | Links illustration to scene (replaces chunk_id when scenes are used) |
| `illustrations` | `prompt_used` | TEXT | Exact T2I prompt used for generation (shown in Preview screen) |

#### Entity Class Taxonomy (37 classes, `ontology_constants.py`)

The `entity_class` field uses a closed enum with tiered fallback hierarchy:
- **Human variants:** human, human_supernatural, human_transformed, human_enhanced, clone, human_hybrid
- **Mechanical & Digital:** android, robot, AI, cyborg, golem, construct
- **Divine & Cosmic:** deity, demigod, angel, demon, cosmic_entity, elemental
- **Spirits & Undead:** spirit, ghost, undead, shade
- **Fae & Mythical:** fae, mythical_beast, folkloric, trickster
- **Animal-based:** animal, anthropomorphic_animal, beast, chimera, shapeshifter
- **Plant & Object:** plant_being, animated_object
- **Alien & Unknown:** alien, alien_humanoid, hivemind, eldritch

`anti_human_override = true` for all non-human classes (30 of 37). When true, image search queries must not contain portrait/person/man/woman terms.

### 5.1 Database Schema

#### Books Table
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author_name TEXT NOT NULL,
    description TEXT,  -- For cover back text
    genre TEXT,  -- fantasy, children, romance, etc.
    is_well_known_book BOOLEAN DEFAULT FALSE,
    original_author TEXT,  -- For classic books being re-illustrated
    manuscript_file_path TEXT,
    total_words INTEGER,
    total_pages INTEGER,
    status TEXT DEFAULT 'uploaded',  -- uploaded, analyzing, ready, exporting, published
    user_id INTEGER,  -- For multi-user support (Phase 2)
    series_id INTEGER,  -- For series support (Phase 2)
    series_order INTEGER,  -- Book 1, 2, 3 in series
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (series_id) REFERENCES series(id)
);

CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_books_user ON books(user_id);
```

#### Users Table (Phase 2)
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    subscription_tier TEXT DEFAULT 'free',  -- free, starter, creator, professional
    subscription_status TEXT DEFAULT 'active',  -- active, cancelled, past_due
    subscription_started_at TIMESTAMP,
    stripe_customer_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Series Table (Phase 2)
```sql
CREATE TABLE series (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    user_id INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Chunks Table
```sql
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    start_page INTEGER,
    end_page INTEGER,
    word_count INTEGER,
    dramatic_score REAL DEFAULT 0.0,
    has_illustration BOOLEAN DEFAULT FALSE,
    illustration_override BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (book_id) REFERENCES books(id),
    UNIQUE(book_id, chunk_index)
);

CREATE INDEX idx_chunks_illustration ON chunks(book_id, has_illustration);
```

#### Characters Table
```sql
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    physical_description TEXT,
    personality_traits TEXT,
    typical_emotions TEXT,
    is_main BOOLEAN DEFAULT FALSE,
    reference_image_url TEXT,
    reference_credit TEXT,
    user_edited BOOLEAN DEFAULT FALSE,
    -- Smart visual query (Feb 2026)
    visual_type TEXT,              -- 'man'|'woman'|'animal'|'AI'|'alien'|'creature'|NULL
    is_well_known_entity INTEGER DEFAULT 0,
    canonical_search_name TEXT,
    search_visual_analog TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

CREATE INDEX idx_characters_main ON characters(book_id, is_main);
```

#### Locations Table
```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    visual_description TEXT,
    atmosphere TEXT,
    is_main BOOLEAN DEFAULT FALSE,
    reference_image_url TEXT,
    reference_credit TEXT,
    user_edited BOOLEAN DEFAULT FALSE,
    -- Smart visual query (Feb 2026)
    is_well_known_entity INTEGER DEFAULT 0,
    canonical_search_name TEXT,
    search_visual_analog TEXT,
    FOREIGN KEY (book_id) REFERENCES books(id)
);

CREATE INDEX idx_locations_main ON locations(book_id, is_main);
```

#### Chunk-Character Junction Table
```sql
CREATE TABLE chunk_characters (
    chunk_id INTEGER NOT NULL,
    character_id INTEGER NOT NULL,
    PRIMARY KEY (chunk_id, character_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);
```

#### Chunk-Location Junction Table
```sql
CREATE TABLE chunk_locations (
    chunk_id INTEGER NOT NULL,
    location_id INTEGER NOT NULL,
    PRIMARY KEY (chunk_id, location_id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);
```

#### Visual Bible Table
```sql
CREATE TABLE visual_bible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE NOT NULL,
    style_category TEXT NOT NULL,
    tone_description TEXT,
    illustration_frequency INTEGER DEFAULT 4,
    layout_style TEXT DEFAULT 'inline_classic',
    visual_bible_json TEXT,  -- Full JSON structure
    approved_at TIMESTAMP,
    version INTEGER DEFAULT 1,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Illustrations Table
```sql
CREATE TABLE illustrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    chunk_id INTEGER NOT NULL,
    page_number INTEGER NOT NULL,
    image_path TEXT,
    prompt TEXT,
    style TEXT,
    reference_images TEXT,  -- JSON array
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 999,
    generated_at TIMESTAMP,
    error_message TEXT,
    flagged_for_regeneration BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);

CREATE INDEX idx_illustrations_status ON illustrations(book_id, status);
CREATE INDEX idx_illustrations_priority ON illustrations(book_id, priority, status);
```

#### Character LoRAs Table
```sql
CREATE TABLE character_loras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    character_id INTEGER UNIQUE NOT NULL,
    lora_file_path TEXT NOT NULL,
    training_images_count INTEGER DEFAULT 20,
    trained_at TIMESTAMP,
    training_cost REAL,
    status TEXT DEFAULT 'pending',
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

#### Covers Table
```sql
CREATE TABLE covers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE NOT NULL,
    front_visual_path TEXT,
    full_cover_path TEXT,
    template TEXT DEFAULT 'children_cartoon',
    title_override TEXT,
    spine_width REAL,
    customizations TEXT,  -- JSON
    generated_at TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### KDP Exports Table
```sql
CREATE TABLE kdp_exports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    trim_size TEXT NOT NULL,
    interior_pdf_path TEXT,
    cover_pdf_path TEXT,
    zip_file_path TEXT,
    exported_at TIMESTAMP,
    download_count INTEGER DEFAULT 0,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Search Queries Table
```sql
CREATE TABLE search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    query_text TEXT NOT NULL,
    result_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

### 5.2 API Endpoints (Updated for B2B)

#### Authentication (Phase 2)
- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

#### Book Management
- `POST /api/manuscripts/upload` - Upload .txt/.docx file
- `GET /api/books` - List user's books
- `GET /api/books/{book_id}` - Book details
- `DELETE /api/books/{book_id}` - Delete book
- `PUT /api/books/{book_id}` - Update book metadata

#### AI Analysis
- `POST /api/books/{book_id}/analyze` - Trigger AI analysis
- `GET /api/books/{book_id}/analysis-progress` - Check progress
- `POST /api/books/{book_id}/regenerate-analysis` - Re-analyze if unsatisfied

#### Visual Bible
- `GET /api/books/{book_id}/visual-bible` - Get visual bible
- `PUT /api/books/{book_id}/visual-bible/character/{id}` - Update character
- `PUT /api/books/{book_id}/visual-bible/location/{id}` - Update location
- `POST /api/books/{book_id}/visual-bible/approve` - Approve and proceed
- `GET /api/books/{book_id}/search-queries` - View search history

#### Reference images – proposed queries and review
- `GET /api/books/{book_id}/proposed-search-queries` - Returns proposed queries per main character/location **and `scenes` array** (selected scenes only with `scene_prompt_draft` and `t2i_prompt_json`); query strings include book style.
- `PATCH /api/books/{book_id}/entity-summaries` - Save user-edited summaries, text_to_image_prompt, and search-related fields (visual_type, canonical_search_name, search_visual_analog, etc.)
- `POST /api/books/{book_id}/search-references` - Run reference search; body may include optional `character_queries`, `location_queries`, `preferred_provider` ("unsplash" | "serpapi"), `search_entity_types` ("characters" | "locations" | "both"), and `enabled_providers` (list of provider names from Settings; if omitted, all available providers are used).

#### Scenes (Step 11 — Feb 21, 2026)
- `GET /api/books/{book_id}/scenes` - All scenes for book, ordered by chunk_start_index; returns `SceneResponse[]` including `characters_present`, `primary_location`, `t2i_prompt_json`, `is_selected`
- `PATCH /api/books/{book_id}/scenes/{scene_id}` - Update scene fields: `title`, `scene_prompt_draft`, `is_selected`
- `POST /api/books/{book_id}/scenes/{scene_id}/generate-illustration` - Trigger T2I generation (stub, returns 202; full implementation is post-visual-bible step)

#### Settings (Bugs/enhancements 13–14 — Feb 21, 2026)
- `GET /api/settings/providers` - Returns `{providers: [{name, label, available}]}` for reference image search engines (used by Settings page checkboxes).

#### Engine Ratings (Step 11 — Feb 21, 2026)
- `PATCH /api/books/{book_id}/engine-ratings` - Record like/dislike for a search provider; body: `{provider, action: "like"|"dislike"}`; upserts row in `engine_ratings`
- `GET /api/books/{book_id}/engine-ratings` - Returns all engine rating rows for book: `[{provider, likes, dislikes, net_score}]`

#### Reference Images
- `GET /api/books/{book_id}/reference-images` - Get all references
- `POST /api/books/{book_id}/reference-images/search` - Trigger search
- `PUT /api/characters/{id}/reference` - Select reference image
- `PUT /api/locations/{id}/reference` - Select reference image

#### Illustrations
- `POST /api/books/{book_id}/generate-illustrations` - Start generation
- `GET /api/books/{book_id}/illustrations` - List all illustrations
- `GET /api/books/{book_id}/generation-progress` - Real-time progress
- `POST /api/illustrations/{id}/regenerate` - Regenerate single illustration
- `POST /api/illustrations/{id}/flag` - Flag for regeneration

#### Cover
- `POST /api/books/{book_id}/cover/generate` - Generate cover
- `GET /api/books/{book_id}/cover` - Get cover details
- `PUT /api/books/{book_id}/cover` - Update cover customizations
- `GET /api/covers/{book_id}/preview` - Preview cover image

#### KDP Export
- `GET /api/books/{book_id}/export-validation` - Check readiness
- `POST /api/books/{book_id}/export-kdp` - Generate KDP package
- `GET /api/downloads/{book_id}/kdp_package.zip` - Download package

#### Preview
- `GET /api/books/{book_id}/preview-page/{page}` - Preview page image
- `GET /api/books/{book_id}/preview-pdf` - Low-res preview PDF

#### Subscription (Phase 2)
- `GET /api/subscription` - Current subscription info
- `POST /api/subscription/upgrade` - Upgrade tier
- `POST /api/subscription/cancel` - Cancel subscription
- `POST /api/subscription/webhooks` - Stripe webhooks

---

## 6. Non-Functional Requirements

### 6.1 Performance

**MVP Targets:**
- Manuscript upload: <30 seconds for 500-page book
- AI analysis: <5 minutes per book (within $0.50 budget)
- LoRA training: 2-4 hours (background, author doesn't wait)
- Initial illustration batch (5 images): <10 minutes
- Full illustration generation: <30 minutes total (background)
- KDP export: <60 seconds
- Page preview: <2 seconds per page

**Phase 2 Targets (Scale):**
- Support 100 concurrent users
- Process 1,000 books/day
- 99.9% uptime

### 6.2 Scalability

**MVP (Single Server):**
- 10 concurrent authors
- 100 books total
- 1TB storage (books + illustrations)
- SQLite database

**Phase 2 (Cloud Scale):**
- 1,000 concurrent authors
- 10,000 books total
- PostgreSQL database (RDS)
- S3 storage for images
- Load balanced backend
- GPU cluster for generation (Runpod.io)

### 6.3 Cost Constraints (Per Book)

**MVP Cost Breakdown:**
- AI analysis: $0.50
- LoRA training: $2.00 (2 characters @ $1.00 each via cloud GPU)
- Illustration generation: $2.50 (125 images @ $0.02 each)
- Cover generation: $0.05
- Reference image search: $0.00 (Unsplash free)
- **Total per book: ~$5.00**

**At $29/mo Creator tier:**
- Break-even: 1 book per 6 months ($5 cost / $29 = 17% of monthly fee)
- Target: Authors create 2-3 books/year (profitable at scale)

**Cost Optimization Strategies:**
- Cache LoRAs for series (reuse character models)
- Batch processing (lower GPU costs)
- Progressive generation (spread costs over time)

### 6.4 Browser Compatibility

**Supported Browsers:**
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

**Responsive Design:**
- Desktop: 1024px+ width (primary)
- Tablet: 768px+ (Phase 2)
- Mobile: Phase 5

### 6.5 Security

**MVP Security:**
- HTTPS in production (free via Let's Encrypt)
- API keys stored in environment variables (never in code)
- File upload validation (type, size, virus scan)
- Rate limiting on expensive operations (AI analysis, generation)
- User content isolated (no cross-user access)

**Phase 2 Security (Multi-User):**
- Password hashing (bcrypt)
- JWT authentication
- Role-based access control
- Payment security (Stripe integration)
- GDPR compliance (data export, deletion)

---

## 7. Success Criteria

### 7.1 MVP Success (Phase 1 - Months 1-4)

**Market Validation:**
- [ ] 50 beta authors complete full workflow (upload → KDP export)
- [ ] 30+ books actually published on Amazon KDP
- [ ] 80%+ approval rating on character consistency
- [ ] 70%+ approval rating on scene selection accuracy
- [ ] User feedback: "Saved me 3-5 hours per book"

**Functional Success:**
- [ ] Author uploads manuscript in <30 seconds
- [ ] AI analysis completes in <5 minutes
- [ ] Character extraction accuracy: 80%+ (vs author review)
- [ ] Scene detection relevance: 70%+ (author approval rate)
- [ ] All 26 illustrations generated in <30 minutes
- [ ] KDP package exports correctly 100% of time
- [ ] Spine width calculations accurate to 0.01"
- [ ] Cover design meets author satisfaction (4+ stars average)

**Quality Success:**
- [ ] Character consistency across 30+ illustrations
- [ ] Illustrations match genre expectations
- [ ] KDP files pass Amazon's ingestion validation with no errors
- [ ] No major bugs in demo workflow
- [ ] Support response time <24 hours

**Business Success:**
- [ ] 25% conversion from free trial to paid
- [ ] 100 paying customers within 3 months ($3K MRR)
- [ ] <$50 CAC (customer acquisition cost)
- [ ] <$5 COGS per book
- [ ] 6-month retention: >70%
- [ ] Average 2.5 books created per user
- [ ] Net Promoter Score (NPS): 50+

### 7.2 Growth Success (Phase 2 - Months 5-8)

**Scale Milestones:**
- [ ] 1,000 paying customers ($30K MRR)
- [ ] 3,000+ books published on KDP via platform
- [ ] <$30 CAC (improving with word-of-mouth)
- [ ] 75% 6-month retention
- [ ] 40% of users create 3+ books (repeat usage)

### 7.3 Expansion Success (Phase 3 - Months 9-12)

**Market Leadership:**
- [ ] 5,000 paying customers ($150K MRR)
- [ ] 10,000+ books published
- [ ] #1 result for "AI book illustration" on Google
- [ ] Featured in Kindlepreneur, KBoards (community recognition)
- [ ] 80% market share in children's book AI illustration

### 7.4 Platform Success (Phase 4 - Year 2)

**B2C Launch:**
- [ ] 10,000+ illustrated books in reading library
- [ ] 5,000+ reader signups
- [ ] $50K MRR from readers
- [ ] Two-sided marketplace functioning (authors publish, readers discover)

---

## 8. Roadmap (Updated with B2B Focus)

### Phase 1: MVP Launch (Months 1-4) - "Ship to First Authors"

**Goal:** 100 authors create and publish books on KDP

**Features:**
1. ✅ Manuscript upload (.txt, .docx)
2. ✅ AI analysis (characters, locations, scenes)
3. ✅ Reference image search (Unsplash)
4. ✅ Visual bible approval
5. ✅ Character consistency (LoRA training)
6. ✅ Illustration generation
7. ✅ Cover generation
8. ✅ KDP export (interior + cover PDFs)
9. ✅ Preview mode
10. ✅ Basic user accounts (email/password)

**Pricing:**
- Free trial: 1 book (watermarked)
- Creator: $29/mo (unlimited books)

**Success Metric:**
- 30 books published on KDP
- $3K MRR
- 80% satisfaction score

**Timeline:** 16 weeks

---

### Phase 2: Growth Features (Months 5-8) - "Scale to 1,000 Authors"

**Goal:** 1,000 paying authors, $30K MRR

**Features:**
1. ✅ Genre-specific templates (10+ genres)
2. ✅ Advanced character consistency
3. ✅ Batch processing (3 books at once)
4. ✅ Series continuity (character library across books)
5. ✅ Author dashboard (manage multiple books)
6. ✅ Community gallery (showcase books)
7. ✅ Stripe integration (subscription management)
8. ✅ Email marketing (onboarding, tips)

**Pricing:**
- Starter: $19/mo (2 books/mo)
- Creator: $29/mo (unlimited)
- Professional: $79/mo (batch + series)

**Success Metric:**
- $30K MRR
- 70% 6-month retention
- 3 books per user average

**Timeline:** 16 weeks

---

### Phase 3: Market Leadership (Months 9-12) - "Dominate Children's Books"

**Goal:** 5,000 authors, $150K MRR, market leader

**Features:**
1. ✅ 50+ genre templates
2. ✅ Advanced cover customization
3. ✅ API access (power users, integrations)
4. ✅ Publisher partnerships (white-label for small presses)
5. ✅ International support (Spanish, French books)
6. ✅ Mobile-optimized interface
7. ✅ Referral program (20% commission)
8. ✅ Author success resources (blog, tutorials)

**Success Metric:**
- $150K MRR
- Market leader in children's book AI illustration
- Featured by Amazon, Kindlepreneur

**Timeline:** 16 weeks

---

### Phase 4: B2C Reading Platform (Year 2) - "Two-Sided Marketplace"

**Goal:** Build reading platform where authors publish, readers discover

**Features (Deferred from Original B2C Vision):**
1. ✅ Reading interface (two-page spreads, animations)
2. ✅ User reading library
3. ✅ Discovery (browse, search, recommendations)
4. ✅ Purchase/subscription for readers ($9.99/mo)
5. ✅ Author revenue share (70/30 split)
6. ✅ Reviews and ratings
7. ✅ Social features (sharing, reading groups)

**Revenue Model:**
- B2B: $150K MRR from authors
- B2C: $50K MRR from readers (target)
- Total: $200K MRR ($2.4M ARR)

**Success Metric:**
- 10,000 books in library
- 5,000 readers
- $50K MRR from B2C

**Timeline:** 24 weeks

---

### Phase 5: Mobile & Global (Year 3) - "Everywhere, Everyone"

**Features:**
1. Native iOS app
2. Native Android app
3. Offline reading
4. 10+ languages supported
5. Global payment methods
6. International author communities

**Goal:** $1M MRR, 50,000 authors, 100,000 readers

---

## 9. Risks & Mitigation (Updated for B2B)

### 9.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Character consistency fails** | Critical | Medium | Use proven kohya_ss, extensive testing, fallback to Neolemon-style workflow if needed |
| **AI analysis costs exceed $0.50** | High | Low | Strict batching, token monitoring, use GPT-3.5-turbo, kill switch at $0.75 |
| **LoRA training too expensive** | Medium | Medium | Use cloud GPUs (Runpod) instead of buying hardware, optimize training epochs |
| **KDP validation fails** | Critical | Low | Test with real KDP submissions, follow official specs exactly, beta testing |
| **Image generation quality poor** | High | Low | Use high-quality models, human QA review, regeneration options |

### 9.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Neolemon improves & adds manuscript analysis** | Critical | Medium | Move fast, ship MVP in 4 months, build loyal community, differentiate on KDP integration |
| **Amazon bans AI-illustrated books** | Critical | Very Low | Unlikely (Amazon allows AI content), position as "AI-assisted", emphasize human creativity |
| **Authors don't want to pay $29/mo** | High | Low | Proven by Neolemon's success, validate in beta, offer pay-per-book alternative |
| **Not enough authors need illustrations** | Medium | Very Low | 560K books/year need illustrations (validated), children's books alone is huge market |
| **Stripe/payment issues** | Medium | Low | Use reliable payment processor, have backup (PayPal), follow Stripe best practices |

### 9.3 User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Authors overwhelmed by complexity** | High | Medium | Simple UI, onboarding wizard, video tutorials, excellent support |
| **Character consistency disappoints** | Critical | Medium | Set realistic expectations, show examples, allow regeneration, match Neolemon quality |
| **KDP export doesn't work** | Critical | Low | Extensive testing, validate with actual KDP uploads, clear instructions |
| **Wait times too long (>30 min)** | Medium | Medium | Progressive loading, background processing, set expectations, show progress |

---

## 10. Assumptions & Dependencies

### 10.1 Assumptions

**Market Assumptions:**
- Self-publishing authors are willing to pay $29-79/mo for illustration tools
- Manuscript analysis automation is valued more than manual prompt control
- Authors prioritize speed and cost over perfection
- KDP remains dominant platform for self-publishing
- Demand for illustrated adult books continues growing

**Technical Assumptions:**
- GeminiGen API remains available and affordable (~$0.02/image)
- OpenAI API pricing stays stable (GPT-4-mini at <$0.50/book analysis)
- Cloud GPU services (Runpod) remain accessible at <$0.50/hour
- Character consistency via LoRA training is achievable with 20 images
- ReportLab can generate KDP-compliant PDFs

**User Assumptions:**
- Authors have manuscripts in .txt or .docx format
- Authors can upload files (not overwhelmingly technical)
- Authors have stable internet connection
- Authors are comfortable with AI-generated art (ethically)
- Authors will spend 30 minutes reviewing visual bible

### 10.2 External Dependencies

**AI Services:**
- **OpenAI API** (GPT-4-mini): Text analysis, character/location extraction
- **GeminiGen API**: Image generation
- **Unsplash API**: Free reference image search (backup: SerpAPI)

**Infrastructure:**
- **Vercel or Netlify**: Frontend hosting (free tier adequate for MVP)
- **Render.com or Railway**: Backend hosting (free tier for beta)
- **Runpod.io or Vast.ai**: Cloud GPU for LoRA training

**Payment Processing:**
- **Stripe**: Subscription billing (Phase 2)

**Third-Party Libraries:**
- **ReportLab**: PDF generation
- **python-docx**: DOCX text extraction
- **kohya_ss**: LoRA training (self-hosted)
- **Stable Diffusion XL**: Base image generation model

### 10.3 Internal Dependencies

**Development Tools:**
- Cursor IDE for vibe-coding
- Python 3.10+ environment
- Node.js 18+ for frontend
- Git for version control
- GitHub for repository

**Team (MVP):**
- 1 founder/developer (you)
- 0 additional hires for MVP (solo founder approach)
- Phase 2: Hire 1 engineer (after $10K MRR)
- Phase 3: Grow to 3-person team (after $50K MRR)

---

## 11. Market Validation Evidence

### 11.1 Competitor Validation

**Neolemon (Primary Validation):**
- 23,000 active users (proven demand)
- $29/month pricing (proven willingness to pay)
- 60% are Amazon KDP publishers (validated target market)
- Children's books only (leaves 60% of market open)
- Prompt-based workflow (3-5 hours/book proves pain point exists)

**Market Size Validation:**
- 1.4M books published annually on KDP (Amazon reports)
- 40% need illustrations = 560,000 books/year
- Growing 15% annually (self-publishing trend)

### 11.2 Author Community Validation

**Pain Points Validated (from KBoards, r/selfpublish research):**

**Quote 1 (Cost):**
> "Illustration alone will end up being more than your budget. Your chances of making back money on it becomes very unlikely." - KBoards user

**Quote 2 (Time):**
> "I spent 3-5 hours writing prompts for every scene using Midjourney. Character consistency was impossible." - Medium author blog

**Quote 3 (Quality Need):**
> "For every 1 very high quality kids' book, there are 10 roughly made ones that are still decent to good, and there are 200 poor quality ones." - KBoards user

**Quote 4 (Neolemon Alternative):**
> "Neolemon has changed the game for me... currently working on a project that I've been wanting to create for the past 4 years but couldn't because other software wasn't producing consistent characters." - Neolemon testimonial

### 11.3 Differentiation Validation

**Your Advantages (Validated Gaps):**

1. **Manuscript Analysis:**
   - Neolemon: Authors manually write prompts (validated pain point)
   - You: Automatic extraction (saves 3-5 hours, unique feature)

2. **KDP Integration:**
   - Neolemon: Outputs individual images (authors must assemble)
   - You: One-click KDP export (complete solution)

3. **Reference Search:**
   - Neolemon: Authors search Google/Shutterstock manually (1-3 hours)
   - You: AI-suggested pre-cleared images (unique feature)

4. **All Genres:**
   - Neolemon: Children's cartoon only
   - You: Fantasy, romance, mystery, sci-fi, etc.

---

## 12. Appendices

### 12.1 Technical Implementation Resources

**GitHub Repositories to Use:**

**Leonardo AI Integration:**
- Official SDK: `pip install leonardo-ai-sdk`
- Documentation: https://docs.leonardo.ai/
- Character Reference feature for consistency

**PDF Generation:**
- ReportLab: `pip install reportlab`
- Documentation: https://docs.reportlab.com/
- Complete KDP formatting examples provided

**Document Processing:**
- python-docx: `pip install python-docx`
- PyPDF2: `pip install pypdf`

**Image Processing:**
- Pillow: `pip install pillow`
- For resizing, format conversion

**LoRA Training (Phase 2 Only - If Needed):**
- `bmaltais/kohya_ss` - Complete LoRA training pipeline
- Installation: `git clone https://github.com/bmaltais/kohya_ss.git`
- See Appendix 12.4 for implementation guide

### 12.2 Cost Breakdown Examples

**Example 1: 32-Page Children's Book (Using Leonardo AI)**

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| AI analysis | 1 book | $0.30 | $0.30 |
| Reference searches | 2 (main char + location) | $0.00 | $0.00 |
| **Leonardo AI illustrations** | **8 images** | **$0.015 each** | **$0.12** |
| Cover generation (Leonardo AI) | 1 cover | $0.12 | $0.12 |
| **TOTAL** | | | **$0.54** |

**At $29/mo Creator tier:** Highly profitable (98% margin)

---

**Example 2: 300-Page Fantasy Novel (Using Leonardo AI)**

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| AI analysis | 1 book | $0.50 | $0.50 |
| Reference searches | 5 (3 chars + 2 locations) | $0.00 | $0.00 |
| **Leonardo AI illustrations** | **75 images (every 4 pages)** | **$0.015 each** | **$1.13** |
| Cover generation (Leonardo AI) | 1 cover | $0.12 | $0.12 |
| **TOTAL** | | | **$1.75** |

**At $29/mo Creator tier:** Still profitable (94% margin, authors create 2-3 books/year)

---

**Example 3: 5-Book Series (Batch Processing - Phase 2)**

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| AI analysis | 5 books | $0.40 each | $2.00 |
| **Leonardo AI illustrations** | **250 images total** | **$0.015 each** | **$3.75** |
| Covers (Leonardo AI) | 5 covers | $0.12 each | $0.60 |
| **TOTAL** | | | **$6.35** |

**At $79/mo Professional tier:**
- Cost per book: $1.27
- Very profitable for series authors (98% margin)

**Note:** Phase 2 may add optional LoRA training for perfect character consistency across series (+$3.00 for 3 shared characters if author opts in)

---

### 12.3 Glossary (Updated for B2B)

**B2B Terms:**
- **KDP (Kindle Direct Publishing):** Amazon's self-publishing platform where authors upload books
- **Trim Size:** Dimensions of final printed book (e.g., 6"x9", 8.5"x8.5")
- **Bleed:** Extra 0.125" beyond trim size for printing (prevents white edges)
- **Spine Width:** Thickness of book spine, calculated from page count
- **Interior PDF:** Content pages of book (text + illustrations)
- **Cover PDF:** Full wrap cover (front, back, spine combined)

**AI Terms:**
- **LoRA (Low-Rank Adaptation):** Technique for training AI to generate consistent characters
- **Visual Bible:** Style guide with approved character/location references
- **Dramatic Score:** AI-assigned rating (0.0-1.0) of how visually interesting a scene is
- **Chunking:** Dividing book text into segments for AI analysis
- **Reference Image:** Photo used to guide AI illustration generation

**Platform Terms:**
- **Manuscript Analysis:** Automatic extraction of characters, locations, scenes from uploaded book
- **Character Consistency:** Ability to generate same character across 30+ illustrations
- **Progressive Loading:** Generating illustrations in batches (priority first, rest in background)
- **Main-Only Search:** Searching reference images only for main characters/locations to save API quota
- **Leonardo AI:** Image generation API service with built-in character reference feature
- **LoRA (Low-Rank Adaptation):** Advanced technique for training AI models to generate perfectly consistent characters (Phase 2 feature)

---

### 12.4 Phase 2: Custom LoRA Training Implementation (Optional Premium Feature)

**When to Implement:**
- Only after MVP validation shows demand for >95% character consistency
- Positioned as premium feature ($79/mo Professional tier)
- For series authors needing perfect consistency across 5+ books

**Implementation Overview:**

If beta testing reveals that Leonardo AI's 85-92% consistency is insufficient for a significant segment of users (>30% complaints), implement custom LoRA training as an optional premium upgrade.

**Technical Stack:**
- **kohya_ss:** Open-source LoRA training pipeline
- **Cloud GPU:** Runpod.io or Vast.ai ($0.30-0.50/hour)
- **Training time:** 2-4 hours per character
- **Cost:** $2-6 per book (2-3 main characters)

**Quick Implementation Guide:**

```python
# 1. Generate training dataset (20 images per character)
def generate_character_training_images(character, reference_image):
    poses = ['front view', 'side profile', '3/4 view']
    expressions = ['smiling', 'serious', 'surprised']
    
    training_images = []
    for pose in poses:
        for expression in expressions:
            img = leonardo.generate_image(
                prompt=f"{character.physical_description}, {pose}, {expression}",
                character_reference_image=reference_image
            )
            training_images.append(img)
    
    return training_images

# 2. Train LoRA using kohya_ss
def train_lora(character_id, training_images):
    # Save images to training directory
    save_training_data(character_id, training_images)
    
    # Submit to cloud GPU
    job = runpod.submit_training_job(
        images_path=f"/data/training/{character_id}/",
        config={
            "model": "stable-diffusion-xl-base-1.0",
            "epochs": 30,
            "learning_rate": 3e-5
        }
    )
    
    return job.id

# 3. Use trained LoRA for perfect consistency
def generate_with_lora(scene, character_lora_path):
    pipe = StableDiffusionXLPipeline.from_pretrained("sdxl-base-1.0")
    pipe.load_lora_weights(character_lora_path)
    
    image = pipe(scene.prompt).images[0]
    return image
```

**Pricing Model for LoRA Training:**
- Free/Creator tier: Leonardo AI only (85-92% consistency)
- Professional tier ($79/mo): Option to enable LoRA training
  - First book in series: 2-4 hour delay for training
  - Subsequent books: Instant (reuse trained LoRAs)
  - Perfect for 5+ book series

**Marketing Position:**
- "Studio Quality Character Training"
- "Perfect Consistency for Series Authors"
- "Industry-Leading 99% Character Match"

**See full implementation in `/docs/lora-training-guide.md` if Phase 2 is greenlit**

---

**END OF REQUIREMENTS DOCUMENT v2.1**

---

## Summary of Major Changes from v2.0 to v2.1

### Updated (Simplified Implementation):
1. ✅ **Leonardo AI character consistency** (replaced custom LoRA training for MVP)
   - Faster implementation (1 week vs 4 weeks)
   - Lower cost ($0 GPU rental vs $2-6 per book)
   - Good quality (85-92% consistency vs 95-99% with LoRA)
   - Deferred LoRA to Phase 2 as optional premium feature
2. ✅ **Image generation cost model explained** (Leonardo AI: $0.015/image vs previous generic $0.02)
   - Maestro plan: $48/mo for 25,000 tokens (3,125 images)
   - Effective cost per book reduced: $1.88 vs $2.50
3. ✅ **Scene extraction best practices** added to manuscript analysis section
   - Narrative structure analysis (story beats, plot points)
   - Emotional intensity detection
   - Visual density assessment
   - Reader engagement heuristics
4. ✅ **Book recognition question** updated for B2B context
   - "Is there another book like it?" (vs "Is this a well-known published book?")
   - Helps optimize reference image search
   - B2C alternative noted for Phase 4
5. ✅ **Cover-only generation workflow** added
   - Authors can generate just covers without full illustrations
   - Minimal visual bible (1-2 entities)
   - Cost: $0.22 vs $2.50 for full book (91% savings)
   - Use case: Cover design service separate from illustration service

### Summary of Changes from v1.0 to v2.0 (Original B2C → B2B Pivot):
[Previous v2.0 summary remains unchanged]

### Added (Critical B2B Features):
1. ✅ **Manuscript upload** (direct file upload, replacing Google Drive dependency)
2. ✅ **Cover generation** (complete KDP publishing package)
3. ✅ **KDP export** (one-click print-ready PDFs with bleed/spine)
4. ✅ **Market analysis** (competitive positioning, user personas, pricing strategy)
5. ✅ **Leonardo AI character consistency** (API-native, deferred custom LoRA to Phase 2)
6. ✅ **Reference image search** (AI-suggested, pre-cleared commercial images)
7. ✅ **Series support** (database schema for multi-book series - Phase 2)
8. ✅ **Subscription tiers** (free, $19, $29, $79 pricing validated by Neolemon)
9. ✅ **Author personas** (Sarah, Marcus, Jamie - validated from research)
10. ✅ **Competitive analysis** (Neolemon, Recraft.ai, positioning strategy)

### Removed (Wrong Focus for B2B):
1. ❌ Google Drive import (replaced with direct upload)
2. ❌ Two-page spread reading interface (replaced with simple preview)
3. ❌ Page turn animations (unnecessary for authors)
4. ❌ Reading progress tracking (authors preview, not read)
5. ❌ Anime panel layouts (niche, adds complexity)

### Deferred to Phase 4 (B2C Reading Platform):
1. ⏸️ Full reading interface (preserved for future marketplace)
2. ⏸️ User reading library (when readers join platform)
3. ⏸️ Social sharing (reading groups, comments)
4. ⏸️ Discovery features (browse, recommendations)

### Key Strategic Shifts:
- **Target User:** Readers → Authors
- **Use Case:** Reading enhancement → Book creation & publishing
- **Output:** Reading experience → KDP-ready PDFs
- **Revenue Model:** Unclear → Proven SaaS subscription ($29/mo)
- **Market Size:** Unknown → $900M-$1.2B TAM (validated)
- **Competition:** None → Beatable (Neolemon lacks manuscript analysis)
- **Timeline:** 6 months → 4 months (removed reading UI complexity)

### Preserved Strengths:
- ✅ Manuscript analysis (your killer differentiator)
- ✅ Visual bible concept (author control)
- ✅ Smart illustration placement (dramatic moment detection)
- ✅ Character/location extraction (well-designed)
- ✅ Technical architecture (solid foundation)

**Result:** Faster to build, bigger validated market, clearer revenue path, stronger competitive positioning.
