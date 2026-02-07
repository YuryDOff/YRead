# Requirements Update Summary
## February 7, 2026

This document summarizes the changes made to the requirements and roadmap based on your follow-up questions.

---

## Changes Made

### 1. ✅ Chunk Metadata Enrichment (Section 3.2.1)

**What Changed:**
- Added **character and location tagging to each chunk** after AI analysis
- Created new junction tables: `chunk_characters` and `chunk_locations`

**Why This Helps:**
- **Smart reference selection:** System knows exactly which character/location appears in each scene
- **Better prompts:** Immediate access to relevant character/location data when generating illustrations
- **Efficient querying:** Can filter "all chunks featuring Sherlock Holmes" in milliseconds
- **Improved consistency:** Ensures correct references used for each illustration

**Technical Implementation:**
```sql
-- New junction tables added to database schema
CREATE TABLE chunk_characters (
    id INTEGER PRIMARY KEY,
    chunk_id INTEGER,
    character_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
);

CREATE TABLE chunk_locations (
    id INTEGER PRIMARY KEY,
    chunk_id INTEGER,
    location_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);
```

**AI Analysis Updated:**
- First Pass: Extract characters/locations AND tag which appear in each chunk
- Second Pass: Consolidate top 5 characters and locations
- **Third Pass (NEW):** Enrich chunk metadata with character/location IDs

---

### 2. ✅ Book Title/Author in Reference Search (Section 3.2.2)

**What Changed:**
- Reference image searches now include **book title and author** when appropriate
- Added **"Is this a well-known book?"** question during style selection
- If yes, user can optionally provide author name

**Why This Helps:**
For **well-known books:**
- Search "Sherlock Holmes A Study in Scarlet" → More accurate results
- Search "Hogwarts castle Harry Potter" → Finds iconic imagery
- Contextual understanding improves image relevance

For **unknown/personal books:**
- Falls back to generic searches: "tall detective portrait"
- Avoids confusion with wrong context

**Example Queries:**

| Book Type | Character | Old Query | New Query (if well-known) |
|-----------|-----------|-----------|---------------------------|
| Well-known | Sherlock Holmes | "Victorian detective portrait" | "Sherlock Holmes A Study in Scarlet" |
| Unknown | John Smith | "middle-aged businessman" | "middle-aged businessman" (unchanged) |

**UI Changes:**
- Style Selection Screen now includes:
  - Toggle: "Is this a well-known published book?" (Yes/No)
  - If Yes: Optional text input for author name
  - Help text: "This helps us find better reference images"

---

### 3. ✅ Reference Image Count: 2-3 Instead of 4-6 (Section 3.2.2)

**What Changed:**
- **Characters:** Now 2-3 reference images (previously 4-6)
- **Locations:** Remains 2-3 reference images (unchanged)

**Why This Makes Sense:**
- **Realistic expectations:** Hard to find 6 distinct images of same person via search
- **Faster user experience:** Less overwhelming to review and select
- **Better quality:** Focus on finding 2-3 great images vs. 6 mediocre ones
- **Simpler UI:** Cleaner grid layout, faster loading

**What Users See:**
```
Character: "Elizabeth Bennet"
Description: "Young woman, early 20s, dark curly hair, intelligent eyes..."

Reference Images: [Image 1] [Image 2] [Image 3]
                   ( )       (✓)       ( )
                   
Select one reference image ↑
```

---

### 4. ✅ Visual Bible Structure Clarification (Section 3.2.3)

**What Changed:**
- Moved **detailed acceptance criteria** for character/location reference images from 3.2.2 to 3.2.3
- Section 3.2.2 now focuses purely on the **search process**
- Section 3.2.3 now describes the complete **visual bible output**

**Why This Is Better:**
- **Logical flow:** Search → Results → Visual Bible
- **Clear separation:** Search process vs. final deliverable
- **Better documentation:** Each section has single, clear purpose

**Updated Structure:**

**3.2.2 Reference Image Search** (Process):
- How to search for images
- Query generation logic
- API integration
- Filtering and deduplication

**3.2.3 Visual Bible Generation** (Output):
- What the visual bible contains
- For each character: name, description, 2-3 images to choose from
- For each location: name, description, 2-3 images to choose from
- User selection and approval process

---

## Database Schema Changes

### New Tables Added:

```sql
-- Links chunks to characters appearing in them
CREATE TABLE chunk_characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER,
    character_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (character_id) REFERENCES characters(id),
    UNIQUE(chunk_id, character_id)
);

-- Links chunks to locations appearing in them
CREATE TABLE chunk_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER,
    location_id INTEGER,
    FOREIGN KEY (chunk_id) REFERENCES chunks(id),
    FOREIGN KEY (location_id) REFERENCES locations(id),
    UNIQUE(chunk_id, location_id)
);
```

### Updated Tables:

**Books Table** - No changes

**Chunks Table** - No structural changes, but now has relationships via junction tables

**Visual Bible Table** - Added note about including chunk metadata

---

## UI/UX Changes

### Style Selection Screen (NEW):

```
┌─────────────────────────────────────────┐
│  Step 2: Choose Your Illustration Style │
└─────────────────────────────────────────┘

📚 Book Information
   Is this a well-known published book?
   ○ Yes    ● No
   
   [?] This helps us find better reference images
   
   (If Yes selected)
   Author (optional): [____________]

🎨 Visual Style
   [Non-Fiction] [Fiction] [Romance] [Sci-Fi]
   [Fantasy] [Fairy Tale] [Classic Literature]

🖼️ Illustration Frequency
   ────●──────────────────
   1 per 4 pages (~125 illustrations)

📖 Layout Style
   ○ Inline Classic    ● Anime Panels
   
   [Analyze Book →]
```

### Visual Bible Review Screen (UPDATED):

**Before (OLD):**
- 4-6 reference images per character
- Could be overwhelming

**After (NEW):**
- 2-3 reference images per character
- Cleaner, faster selection

```
┌─────────────────────────────────────────┐
│  Character: Elizabeth Bennet             │
│                                          │
│  Young woman, early 20s, dark curly     │
│  hair, intelligent eyes, witty          │
│  expression...                           │
│                                          │
│  Reference Images:                       │
│  ┌─────┐  ┌─────┐  ┌─────┐             │
│  │ Img │  │ Img │  │ Img │             │
│  │  1  │  │  2  │  │  3  │             │
│  └──○──┘  └──●──┘  └──○──┘             │
│     ↑         ↑         ↑                │
│              Selected                    │
└─────────────────────────────────────────┘
```

---

## Impact on Implementation

### Backend Changes Needed:

1. **Database migrations:**
   - Add `chunk_characters` table
   - Add `chunk_locations` table
   - Add `is_well_known` and `author` fields to `books` table

2. **AI Analysis Service:**
   - Update batch analysis to tag character/location presence per chunk
   - Add third pass to enrich chunk metadata
   - Store relationships in junction tables

3. **Search Service:**
   - Check `book.is_well_known` flag
   - If true, include `book.title` and `book.author` in queries
   - Fetch 3-5 results per search, return top 2-3

4. **Prompt Generation:**
   - Query junction tables to find which characters/locations in chunk
   - Select appropriate reference image based on metadata

### Frontend Changes Needed:

1. **Style Selector Component:**
   - Add book recognition toggle
   - Add optional author input
   - Pass to backend on submit

2. **Visual Bible Review Component:**
   - Update grid to show 2-3 images (not 4-6)
   - Cleaner layout with less crowding

3. **No other UI changes required**

---

## Cost Impact

**GOOD NEWS: No significant cost increase**

| Item | Old | New | Change |
|------|-----|-----|--------|
| Reference image searches | 5 chars × 6 queries = 30 | 5 chars × 2-3 queries = 10-15 | **Reduced by 50%** ✅ |
| AI analysis | $0.50 | $0.50 + ~$0.02 for enrichment | **+$0.02** (negligible) |
| Search API calls | Free tier sufficient | Free tier sufficient | No change |

**Total cost per book: Still ~$3.00** (actually slightly less due to fewer searches)

---

## Timeline Impact

**Minimal - adds ~1-2 hours to development:**

| Task | Additional Time |
|------|----------------|
| Add junction tables to schema | 15 min |
| Update AI analysis (third pass) | 30 min |
| Update search service logic | 30 min |
| Add book recognition to UI | 20 min |
| Update visual bible display | 15 min |
| **TOTAL** | **~2 hours** |

This is well within the existing 40-60 hour MVP timeline.

---

## Benefits Summary

### ✅ Improved Accuracy
- Reference images more contextually relevant (uses book title)
- Character/location consistency (chunk metadata enrichment)

### ✅ Better UX
- Less overwhelming (2-3 images vs 4-6)
- Faster selection process
- More relevant search results for known books

### ✅ Better Performance
- Fewer API calls (2-3 searches vs 6 per character)
- Faster queries (junction tables with indexes)
- More efficient illustration generation

### ✅ Maintainability
- Clearer code structure (search vs visual bible sections)
- Better data model (proper relationships)
- Easier to debug and extend

---

## Updated Feature Checklist

### Must-Have (MVP) - All Updated:
- [x] Book upload via Google Drive ✓
- [x] Text chunking with character/location metadata ✓ (ENHANCED)
- [x] AI analysis with enrichment ✓ (ENHANCED)
- [x] Reference image search with book context ✓ (ENHANCED)
- [x] Visual bible with 2-3 images per element ✓ (STREAMLINED)
- [x] Illustration generation ✓
- [x] Book reader interface ✓
- [x] Reading progress tracking ✓

### Future Enhancements (Post-MVP):
- [ ] Multi-reference image support (when GeminiGen adds it)
- [ ] Manual URL input for reference images
- [ ] Edit character/location descriptions in visual bible
- [ ] Regenerate individual illustrations
- [ ] Advanced chunk querying ("show all scenes with Character X and Location Y")

---

## Conclusion

All your suggested changes have been successfully integrated into both the requirements document and development roadmap. The updates:

1. ✅ **Improve data structure** (chunk enrichment)
2. ✅ **Enhance search quality** (book title/author)
3. ✅ **Streamline UX** (2-3 images instead of 4-6)
4. ✅ **Clarify documentation** (better section organization)

The changes add minimal development time (~2 hours) while significantly improving the quality and usability of the application.

**Next Steps:**
1. Review updated requirements_document.md
2. Review updated development_roadmap.md
3. Begin Phase 1 implementation with Cursor IDE

---

**All changes are reflected in the updated documents.**
