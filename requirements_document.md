# Requirements Document: AI-Powered Book Reading Application
## "Reading Reinvented"

**Version:** 1.0 MVP  
**Date:** February 7, 2026  
**Project Type:** Web Application  
**Development Approach:** Vibe-coding with Cursor IDE

---

## 1. Executive Summary

### 1.1 Vision
Create a revolutionary web-based reading experience that enriches books with AI-generated illustrations, transforming traditional reading into an immersive visual journey.

### 1.2 Unique Selling Proposition (USP)
"Reading Reinvented" - An AI-powered application that dynamically generates contextual illustrations for books using advanced image generation technology, creating a personalized visual narrative experience.

### 1.3 Target MVP Scope
Single-book experience with automated visual bible creation and dynamic illustration generation during reading.

---

## 2. Technical Architecture

### 2.1 Technology Stack

#### Frontend
- **Framework:** React (recommended) or Vue.js
- **Styling:** Tailwind CSS for rapid UI development
- **Build Tool:** Vite or Next.js (for easier deployment)
- **State Management:** React Context API or Zustand (lightweight)

#### Backend
- **Language:** Python 3.10+
- **Framework:** FastAPI or Flask
- **API Communication:** RESTful API architecture

#### Database
- **Type:** SQLite (file-based, perfect for MVP)
- **ORM:** SQLAlchemy (Python)

#### AI Services
- **Text Analysis:** OpenAI GPT-3.5-turbo or GPT-4-mini (low-cost, high context window ~128k tokens)
- **Image Generation:** GeminiGen API (Nano Banana model)
- **Web Search:** Bing Search API (free tier) or SerpAPI (free tier)

#### Hosting & Deployment
- **Frontend:** Vercel, Netlify, or GitHub Pages (free tier)
- **Backend:** Render.com, Railway.app, or PythonAnywhere (free tier)
- **Storage:** Local filesystem for MVP (server-side storage)

### 2.2 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     USER INTERFACE (React)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Book Upload  │  │ Visual Bible │  │  Book Reader │      │
│  │   Screen     │  │   Approval   │  │    Screen    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND API (FastAPI/Python)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Book Import │  │  AI Analysis │  │ Illustration │      │
│  │   Service    │  │   Service    │  │  Generator   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATABASE (SQLite)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │    Books     │  │    Chunks    │  │ Illustrations│      │
│  │  Characters  │  │   Locations  │  │ Visual Bible │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   OpenAI     │  │  GeminiGen   │  │ Web Search   │      │
│  │     GPT      │  │     API      │  │     API      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Functional Requirements

### 3.1 Book Import & Processing

#### 3.1.1 Google Drive Import
**Priority:** Must-Have

**User Story:**
As a user, I want to import my book from Google Drive so that I can read it with AI-generated illustrations.

**Acceptance Criteria:**
- User can paste a shareable Google Drive link
- System validates the link format
- System downloads .txt file from Google Drive
- Book title extracted from filename or first line
- Confirmation message displayed upon successful import
- Error handling for invalid links or unsupported file types

**Technical Specifications:**
- Support Google Drive shareable links (format: `https://drive.google.com/file/d/FILE_ID/view`)
- Convert shareable link to direct download link
- File size limit: 10MB for MVP (approximately 2M words)
- Supported format: Plain text (.txt) only

#### 3.1.2 Text Chunking
**Priority:** Must-Have

**User Story:**
As a system, I need to chunk the book text intelligently so that I can analyze and generate contextual illustrations.

**Acceptance Criteria:**
- Text divided into overlapping chunks
- Chunk size: ~2000 tokens (~1500 words)
- Overlap: 200 tokens between chunks
- Chunk boundaries respect paragraph breaks when possible
- Metadata stored: chunk_id, position, word_count
- **Chunk metadata enriched after AI analysis with:**
  - Characters present in chunk (references to character IDs)
  - Locations present in chunk (references to location IDs)
  - Dramatic score (0.0-1.0) for illustration prioritization

**Technical Specifications:**
- Use sliding window approach with overlap
- Store chunks in database with references to parent book
- Calculate total chunks and estimated reading time
- Tag chunks with page numbers (estimated ~300 words per page)
- After AI analysis, update chunks with character/location relationships
- Enable efficient querying: "Get all chunks featuring Character X"

### 3.2 AI Analysis & Visual Bible Creation

#### 3.2.1 Book Analysis
**Priority:** Must-Have

**User Story:**
As a system, I need to analyze the entire book to extract key characters, locations, tone, and dramatic moments for illustration.

**Acceptance Criteria:**
- Analysis completed in batches to manage costs
- Extracted information:
  - 5 main characters (name, physical description, personality traits, typical emotions)
  - 5 main locations (name, detailed visual description, atmosphere)
  - Overall tone and style (genre, mood, narrative voice)
  - Key dramatic moments per chunk (for illustration)
  - **Character and location presence per chunk** (for metadata enrichment)
- Total cost per book: ≤$0.50 in AI tokens
- Progress indicator shown to user during analysis
- **Chunk metadata updated with character/location relationships**

**Technical Specifications:**
- Batch size: 10-15 chunks per GPT API call
- Use GPT-3.5-turbo or GPT-4-mini (128k context window)
- Structured output using JSON mode
- Consolidation step to merge character/location descriptions across batches
- Store results in database with timestamp
- **After consolidation, enrich each chunk with:**
  - List of character IDs present in that chunk
  - List of location IDs present in that chunk
  - Enables smart illustration generation (know which references to use)

**AI Prompting Strategy:**
```
First Pass (per batch):
- Extract characters mentioned with descriptions
- Extract locations mentioned with descriptions
- Identify most dramatic/visual moment in the chunk
- Tag which characters/locations appear in each chunk

Second Pass (consolidation):
- Merge all character descriptions into top 5
- Merge all location descriptions into top 5
- Generate overall tone/style summary

Third Pass (enrichment):
- Update each chunk record with character/location IDs
- Store relationships for efficient querying
```

#### 3.2.2 Reference Image Search
**Priority:** Must-Have

**User Story:**
As a user, I want the system to find reference images for characters and locations so I can approve visuals that match my interpretation.

**Acceptance Criteria:**
- For each character:
  - **2-3 reference images** showing diverse views/expressions
  - Images should capture the character's essence and key physical traits
- For each location:
  - **2-3 reference images** showing different angles/lighting
- Images displayed in grid format for user selection
- User can select 1 primary reference image per character/location
- Search queries enriched with book title/author when appropriate

**Technical Specifications:**
- Use Bing Image Search API or SerpAPI (free tier)
- Search query format: 
  - **Characters (well-known books):** "{character_name} {book_title} {author}" OR "{description} person from {book_title}"
  - **Characters (unknown books):** "{description} person portrait"
  - **Locations (well-known):** "{location_name} {book_title}" OR "{description} from {book_title}"
  - **Locations (unknown):** "{description} landscape/interior"
- **Book recognition logic:**
  - Check if book title matches known works (simple list or heuristic)
  - OR ask user during setup: "Is this a well-known published book?" (Yes/No)
  - If yes, include title/author in searches
- Fetch 3-5 results per character/location
- Filter: Safe search enabled, minimum 512x512px
- Deduplicate similar images
- Return top 2-3 most diverse and relevant images
- Store image URLs (not downloading images to save bandwidth)

**Search Strategy Example:**
```
For "Sherlock Holmes" in well-known book "A Study in Scarlet" by Arthur Conan Doyle:
- Query 1: "Sherlock Holmes A Study in Scarlet"
- Query 2: "Victorian detective portrait Sherlock Holmes"
- Query 3: "Sherlock Holmes illustration"
→ Select top 2-3 most varied results

For generic character "tall detective" in unknown book:
- Query 1: "tall male detective portrait"
- Query 2: "detective full body professional"
→ Select top 2-3 results
```

#### 3.2.3 Visual Bible Generation
**Priority:** Must-Have

**User Story:**
As a user, I want to review and approve a visual style guide before illustrations are generated so I ensure consistency.

**Acceptance Criteria:**
- Visual bible includes:
  - Book title and style setting
  - Selected illustration style (anime, realistic, classic, etc.)
  - **For each character:**
    - Character name
    - Comprehensive physical description (merged from AI analysis)
    - Personality traits and typical emotions
    - 2-3 reference images for user to choose from
    - User selects 1 primary reference image
  - **For each location:**
    - Location name
    - Detailed visual description (merged from AI analysis)
    - Atmosphere and mood
    - 2-3 reference images for user to choose from
    - User selects 1 primary reference image
  - Overall tone/mood description
- User can review entire visual bible
- User can approve or request regeneration
- Upon approval, visual bible locked for the book

**Technical Specifications:**
- Visual bible stored as structured JSON in database
- Reference images: Store URLs only (with backup handling)
- Generate unique visual_bible_id per book
- Timestamp and version tracking
- Include metadata: which chunks contain each character/location (from enrichment)

### 3.3 Illustration Generation

#### 3.3.1 GeminiGen API Integration
**Priority:** Must-Have

**User Story:**
As a system, I need to generate illustrations using the visual bible to maintain character and location consistency.

**Acceptance Criteria:**
- Support for Nano Banana model (image reference capability)
- Style transfer based on user selection
- Aspect ratio: Book-appropriate (3:4 or 4:3 for portrait/landscape)
- Resolution: 1K (1024px) for MVP
- **NOTE:** Nano Banana currently supports SINGLE reference image per generation
  - For MVP: Use primary character reference only
  - Future: Multi-reference capability when available

**Technical Specifications:**
- API Endpoint: GeminiGen API (based on their service)
- Request format:
  ```python
  {
    "model": "nano-banana",
    "prompt": "{scene_description} + {character_description} + {location_description}",
    "reference_image": "URL or base64",
    "style": "{user_selected_style}",
    "aspect_ratio": "3:4",
    "resolution": "1K"
  }
  ```
- Retry logic: 3 attempts with exponential backoff
- Timeout: 60 seconds per generation
- Error handling: Use placeholder image on failure

**Multi-Reference Workaround (MVP):**
- Primary character reference used directly
- Secondary elements (location, other characters) described in text prompt
- **Roadmap item:** When GeminiGen supports multi-reference, update to pass multiple images

#### 3.3.2 Smart Illustration Placement
**Priority:** Must-Have

**User Story:**
As a user, I want illustrations placed at narrative key moments throughout the book based on my preferred frequency.

**Acceptance Criteria:**
- First illustration on page 1 (must-have)
- Subsequent illustrations every N pages (user configurable: 2, 4, 8, 12 pages)
- Illustrations placed at most dramatic moment within the N-page window
- Total illustrations calculated and displayed before generation

**Technical Specifications:**
- Calculate illustration positions based on:
  - Total pages (estimated from word count)
  - User-selected frequency (N)
  - Dramatic moments from AI analysis
- Algorithm:
  ```
  For each N-page window:
    - Identify chunks within window
    - Select chunk with highest dramatic score (from AI analysis)
    - Generate illustration prompt for that scene
  ```

#### 3.3.3 Pre-Generation & Progressive Loading
**Priority:** Must-Have

**User Story:**
As a user, I want illustrations to load smoothly as I read without waiting for generation.

**Acceptance Criteria:**
- When user clicks "Read":
  - Generate first 4-5 illustrations immediately (with loading screen)
  - Allow user to start reading after first 2 illustrations ready
- Background generation:
  - Monitor user's reading speed (pages per minute)
  - Generate 2-3 illustrations ahead of current position
  - Queue management to prevent over-generation
- Progress indicator for illustration generation

**Technical Specifications:**
- Initial batch: First 5 illustrations (5 API calls)
- Reading speed tracking:
  - Calculate average time per page
  - Predict when user will reach next illustration
  - Start generation 2 illustrations ahead
- Queue system:
  - Max queue size: 3 pending generations
  - Priority: Sequential (nearest illustrations first)
- Store generated images on server filesystem
- Serve images via static file endpoint

### 3.4 Reading Experience

#### 3.4.1 Book-Like Reader Interface
**Priority:** Must-Have

**User Story:**
As a user, I want a beautiful, book-like reading experience with AI illustrations seamlessly integrated.

**Acceptance Criteria:**
- Two-page spread layout (like an open book)
- Page turn animation (flip or slide)
- Typography: Readable serif font (Georgia, Garamond, or similar)
- Layout:
  - Text width: Maximum 65 characters per line for readability
  - Adequate margins and line spacing
  - Page numbers displayed
- Illustration display options (user-selected during setup):
  - **Inline Classic:** Full-width image within text flow (like old illustrated books)
  - **Anime Style:** Panel-style boxes with text wrapping
- Smooth scrolling and responsive design

**Technical Specifications:**
- CSS Grid or Flexbox for two-page layout
- Page break algorithm:
  - Calculate characters per page based on viewport
  - Respect paragraph boundaries
  - Handle images without breaking across pages
- Image rendering:
  - Lazy loading for performance
  - Placeholder while loading
  - Fallback image if generation failed
- Keyboard navigation: Arrow keys for page turning
- Bookmark current page in database

#### 3.4.2 Reading Progress & Controls
**Priority:** Must-Have

**User Story:**
As a user, I want to track my progress and easily navigate through the book.

**Acceptance Criteria:**
- Progress bar showing % completed
- Current page / Total pages indicator
- Controls:
  - Previous page / Next page buttons
  - Jump to page (input field)
  - Table of contents (if chapters detected)
- Reading session persistence (resume where left off)

**Technical Specifications:**
- Store current_page in database on page turn
- Calculate progress: (current_page / total_pages) * 100
- Update every page turn
- Session timeout: None (persistent until user closes book)

### 3.5 User Interface & Workflows

#### 3.5.1 Book Setup Workflow
**Priority:** Must-Have

**Screen Sequence:**
1. **Upload Screen**
   - Google Drive link input
   - "Import Book" button
   - Loading indicator during download

2. **Style Selection Screen**
   - **Book Recognition Question:** "Is this a well-known published book?" (Yes/No toggle)
     - If Yes: Extract or ask for author name (optional field)
     - This improves reference image search accuracy
   - Visual style picker (radio buttons or cards):
     - Non-Fiction (realistic, documentary)
     - Fiction (versatile, balanced)
     - Romance (soft, dreamy)
     - Sci-Fi (futuristic, vibrant)
     - Fantasy (epic, painterly)
     - Fairy Tale (whimsical, storybook)
     - Classic Literature (vintage, engraving-style)
   - Illustration frequency slider (1 per 2, 4, 8, 12 pages)
   - Layout style choice:
     - Inline Classic
     - Anime Panels
   - "Analyze Book" button

3. **Analysis Screen (Wait Screen)**
   - Loading animation
   - Progress messages:
     - "Analyzing narrative structure..."
     - "Identifying key characters..."
     - "Mapping dramatic moments..."
     - "Searching reference images..."
   - Estimated time: 2-5 minutes
   - Cancel option (returns to upload)

4. **Visual Bible Review Screen**
   - Tabs or accordion for:
     - Characters (grid view)
       - Character name, description
       - 2-3 reference image options
       - Selection radio buttons
     - Locations (grid view)
       - Location name, description
       - 2-3 reference image options
       - Selection radio buttons
     - Style Summary (tone, mood, genre)
   - "Edit Description" buttons (inline editing)
   - "Approve & Generate Book" button

5. **Generation Wait Screen**
   - Progress bar for initial illustrations
   - Message: "Generating your personalized illustrated book..."
   - Estimated time: 3-5 minutes
   - Preview of first illustration when ready

6. **Reading Screen**
   - (See 3.4.1 for details)

#### 3.5.2 Error Handling & Edge Cases
**Priority:** Must-Have

**Scenarios:**
1. **Invalid Google Drive Link**
   - Error message: "Unable to access file. Please ensure link is publicly shareable."
   - Allow user to re-enter link

2. **File Too Large**
   - Error message: "File exceeds 10MB limit. Please use a smaller book."
   - Suggestion to split book into volumes

3. **AI Analysis Failure**
   - Retry automatically (up to 2 retries)
   - If fails: "Unable to analyze book. Please try again later."
   - Option to contact support

4. **Image Generation Failure**
   - Use placeholder image: Gray box with text "Illustration unavailable"
   - Log error for debugging
   - Continue reading experience

5. **Reference Image Search Returns No Results**
   - Message: "No reference images found for {character/location}. Using text description only."
   - Proceed with text-based prompts

---

## 4. Data Models

### 4.1 Database Schema

#### Books Table
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    google_drive_link TEXT,
    file_path TEXT,
    total_words INTEGER,
    total_pages INTEGER,
    status TEXT, -- 'imported', 'analyzing', 'ready', 'reading'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Chunks Table
```sql
CREATE TABLE chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    chunk_index INTEGER,
    text TEXT,
    start_page INTEGER,
    end_page INTEGER,
    word_count INTEGER,
    dramatic_score REAL, -- 0.0 to 1.0, for illustration selection
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Chunk-Character Junction Table (NEW)
```sql
CREATE TABLE chunk_characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER,
    character_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (character_id) REFERENCES characters(id),
    UNIQUE(chunk_id, character_id)
);
```

#### Chunk-Location Junction Table (NEW)
```sql
CREATE TABLE chunk_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER,
    location_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    UNIQUE(chunk_id, location_id)
);
```

#### Characters Table
```sql
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    name TEXT,
    physical_description TEXT,
    personality_traits TEXT,
    typical_emotions TEXT,
    reference_image_url TEXT, -- User-selected reference
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Locations Table
```sql
CREATE TABLE locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    name TEXT,
    visual_description TEXT,
    atmosphere TEXT,
    reference_image_url TEXT, -- User-selected reference
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Visual Bible Table
```sql
CREATE TABLE visual_bible (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE,
    style_category TEXT, -- 'fiction', 'sci-fi', 'romance', etc.
    tone_description TEXT,
    illustration_frequency INTEGER, -- Pages between illustrations
    layout_style TEXT, -- 'inline_classic', 'anime_panels'
    approved_at TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

#### Illustrations Table
```sql
CREATE TABLE illustrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER,
    chunk_id INTEGER,
    page_number INTEGER,
    image_path TEXT, -- Server filesystem path
    prompt TEXT, -- Full prompt used for generation
    style TEXT,
    reference_images TEXT, -- JSON array of reference URLs used
    status TEXT, -- 'pending', 'generating', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (chunk_id) REFERENCES chunks(id)
);
```

#### Reading Progress Table
```sql
CREATE TABLE reading_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER UNIQUE,
    current_page INTEGER DEFAULT 1,
    last_read_at TIMESTAMP,
    FOREIGN KEY (book_id) REFERENCES books(id)
);
```

### 4.2 API Endpoints

#### Book Management
- `POST /api/books/import`
  - Body: `{ "google_drive_link": "..." }`
  - Response: `{ "book_id": 1, "status": "imported" }`

- `GET /api/books/{book_id}`
  - Response: Book details with status

- `POST /api/books/{book_id}/analyze`
  - Triggers AI analysis
  - Response: `{ "status": "analyzing", "estimated_time": 180 }`

#### Visual Bible
- `GET /api/books/{book_id}/visual-bible`
  - Response: Characters, locations, reference images

- `POST /api/books/{book_id}/visual-bible/approve`
  - Body: Selected references and edits
  - Response: `{ "status": "approved" }`

#### Illustrations
- `POST /api/books/{book_id}/generate-illustrations`
  - Triggers initial illustration batch
  - Response: `{ "status": "generating", "total": 5 }`

- `GET /api/books/{book_id}/illustrations`
  - Response: Array of illustrations with status

- `GET /api/illustrations/{illustration_id}/image`
  - Serves the actual image file

#### Reading
- `GET /api/books/{book_id}/pages/{page_number}`
  - Response: Page content with illustration references

- `POST /api/books/{book_id}/progress`
  - Body: `{ "current_page": 42 }`
  - Updates reading progress

---

## 5. Non-Functional Requirements

### 5.1 Performance
- Book import: < 10 seconds for 500-page book
- AI analysis: < 5 minutes per book (within $0.50 budget)
- Initial illustration generation: < 5 minutes for 5 images
- Page load time: < 500ms
- Page turn animation: 60fps

### 5.2 Scalability (MVP)
- Single concurrent user (local development)
- Storage: 500MB for book texts and illustrations
- Database: SQLite supports up to 1 book actively

### 5.3 Cost Constraints
- AI analysis: ≤ $0.50 per book (GPT API)
- Image generation: ~$0.02 per image (GeminiGen)
  - 500-page book with 1 image per 4 pages = 125 images = ~$2.50
- Total per book: ~$3.00

### 5.4 Browser Compatibility
- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Responsive design: Desktop only for MVP (1024px+ width)

### 5.5 Security
- Google Drive links: No authentication required (public sharing)
- No user data stored beyond current book
- API keys: Stored in environment variables
- HTTPS for production deployment

---

## 6. Out of Scope (MVP)

### Deferred to Future Versions
1. **User Authentication & Multi-User Support**
   - Login/signup system
   - Personal libraries
   - Cloud storage

2. **Multiple Books**
   - Library management
   - Book switching
   - Favorites/collections

3. **Advanced Features**
   - Individual illustration regeneration
   - Custom prompt editing per illustration
   - Illustration quality voting
   - Social sharing
   - EPUB/PDF export

4. **File Formats**
   - EPUB support
   - PDF support
   - DOCX support

5. **Mobile Optimization**
   - Native mobile apps
   - Touch gestures
   - Offline reading

6. **Collaborative Features**
   - Shared visual bibles
   - Community reference images
   - Comments/annotations

---

## 7. Success Criteria (MVP)

### 7.1 Functional Success
- [ ] User can import 500-page book from Google Drive
- [ ] System analyzes book within $0.50 AI cost
- [ ] System extracts 5 characters and 5 locations
- [ ] User can review and select reference images
- [ ] User can approve visual bible
- [ ] System generates 5 initial illustrations
- [ ] User can read with 2-page spread layout
- [ ] Illustrations display correctly inline
- [ ] Reading progress is saved

### 7.2 Quality Success
- [ ] Illustrations are contextually relevant to scenes
- [ ] Character consistency maintained across illustrations
- [ ] Reading experience feels "book-like"
- [ ] No crashes or major bugs during demo flow
- [ ] Loading states are clear and informative

### 7.3 Technical Success
- [ ] Application runs on local development server
- [ ] All API integrations functional
- [ ] Database operations reliable
- [ ] Images stored and served correctly
- [ ] Code is readable and maintainable

---

## 8. Risks & Mitigation

### 8.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GeminiGen API limitations (single reference) | Medium | High | Use workaround with text descriptions; plan for multi-reference upgrade |
| AI analysis cost exceeds $0.50 | Medium | Medium | Implement strict batching; monitor token usage; use cheaper model if needed |
| Image generation failures | High | Low | Implement retry logic; use placeholder images; graceful degradation |
| Google Drive link parsing issues | Medium | Medium | Robust URL validation; clear error messages; multiple format support |
| SQLite performance with large books | Low | Low | Indexing; query optimization; consider PostgreSQL if needed |

### 8.2 User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Wait times too long (>5 min) | High | Medium | Clear progress indicators; cancel option; estimated times |
| Illustrations don't match user expectations | Medium | High | Manual reference selection; visual bible approval step |
| Reference image search returns poor results | Medium | Medium | Fallback to text-only prompts; allow manual URL input (future) |
| Reading layout uncomfortable | Low | Low | Responsive typography; user testing; adjustable font sizes (future) |

---

## 9. Assumptions & Dependencies

### 9.1 Assumptions
- Users have books in plain text format
- Books are in English (for MVP)
- Users have stable internet connection
- Google Drive links are publicly shareable
- Users are reading on desktop/laptop screens
- GeminiGen API remains available and affordable

### 9.2 External Dependencies
- **OpenAI API:** For text analysis (GPT-3.5-turbo or GPT-4-mini)
- **GeminiGen API:** For image generation (Nano Banana model)
- **Bing/SerpAPI:** For reference image search
- **Google Drive:** For book file hosting
- **Free hosting platforms:** Vercel, Render, etc.

### 9.3 Internal Dependencies
- Cursor IDE for development
- Python 3.10+ environment
- Node.js/npm for frontend build
- Git for version control

---

## 10. Future Roadmap (Post-MVP)

### Phase 2: Enhanced Illustration Control
- Individual illustration regeneration with custom prompts
- Multi-reference image support (when GeminiGen adds it)
- Style mixing (e.g., character in realistic style, background in anime)
- Illustration quality rating system

### Phase 3: Expanded Format Support
- EPUB import and parsing
- PDF import with text extraction
- DOCX import
- Chapter detection and navigation

### Phase 4: User Accounts & Library
- User authentication (email/OAuth)
- Personal library with multiple books
- Cloud storage for illustrations
- Cross-device sync

### Phase 5: Social & Sharing
- Share visual bibles with community
- Download illustrated book as PDF/EPUB
- Social media sharing of favorite illustrations
- Collaborative reading groups

### Phase 6: Mobile Experience
- Progressive Web App (PWA)
- Native iOS/Android apps
- Touch/swipe gestures
- Offline reading mode

---

## 11. Appendices

### 11.1 GeminiGen API Key Findings

**Model:** Nano Banana (google/nano-banana)

**Capabilities:**
- Text-to-image generation
- Image-to-image editing (reference-based)
- **Reference image support:** SINGLE reference image per request
- Style transfer support
- Aspect ratios: 1:1, 3:4, 4:3, 16:9, 9:16
- Resolutions: 1K (1024px), 2K, 4K

**Pricing:** ~$0.02 per 1K image (based on budget info provided)

**Request Format Example:**
```python
{
  "model": "nano-banana",
  "prompt": "A detailed scene description with character and setting",
  "reference_image": "URL or base64 encoded image",
  "aspect_ratio": "3:4",
  "style": "realistic" # or anime, classic, etc.
}
```

**Limitations:**
- Only ONE reference image per generation (critical for MVP design)
- Must consolidate character + location references in prompt text
- Style consistency relies on good prompting

**Mitigation Strategy:**
- Use primary character reference as the single reference image
- Describe other elements (location, other characters) in text prompt
- Future upgrade: When multi-reference available, refactor to use visual bible fully

### 11.2 Cost Breakdown Example

**500-Page Book with Illustration Every 4 Pages:**

| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| Book analysis (GPT-3.5-turbo) | ~30 batches | ~$0.015/batch | $0.45 |
| Reference image searches | 10 searches | Free (Bing API) | $0.00 |
| Illustrations (125 images) | 125 images | $0.02/image | $2.50 |
| **TOTAL PER BOOK** | | | **$2.95** |

**Note:** Actual costs may vary based on:
- Book length and complexity
- GPT model chosen (GPT-4-mini slightly more expensive)
- GeminiGen API pricing updates
- Number of retries needed

### 11.3 Glossary

- **Visual Bible:** A style guide containing approved reference images and descriptions for characters and locations to ensure illustration consistency.
- **Chunking:** Dividing book text into overlapping segments for AI analysis.
- **Dramatic Score:** AI-assigned value (0.0-1.0) indicating how visually interesting or action-packed a text chunk is.
- **Reference Image:** A real photograph used to guide AI illustration generation for consistent character/location appearance.
- **Nano Banana:** Google's Gemini-based image generation model, nickname for gemini-2.5-flash-image.
- **Two-Page Spread:** Reading interface showing two facing pages simultaneously, like an open book.
- **Inline Illustration:** Image embedded within text flow, as in traditional illustrated books.

---

**END OF REQUIREMENTS DOCUMENT**
