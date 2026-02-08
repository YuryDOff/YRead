"""Book-related API endpoints."""
import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    BookImportRequest,
    BookResponse,
    BookAnalyzeRequest,
    AnalyzeStatusResponse,
    StatusResponse,
    ReadingProgressResponse,
    ReadingProgressUpdate,
    ChunkResponse,
    CharacterResponse,
    LocationResponse,
)
from app import crud
from app.services.book_service import (
    download_text_from_google_drive,
    compute_metadata,
    guess_title,
    chunk_text,
)
from app.services.ai_service import run_full_analysis

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Book import
# ---------------------------------------------------------------------------

@router.post("/books/import", response_model=BookResponse)
async def import_book(req: BookImportRequest, db: Session = Depends(get_db)):
    """Import a book from a Google Drive shareable link."""
    try:
        text = await download_text_from_google_drive(req.google_drive_link)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))

    meta = compute_metadata(text)
    title = guess_title(text)

    book = crud.create_book(
        db,
        title=title,
        google_drive_link=req.google_drive_link,
        total_words=meta["total_words"],
        total_pages=meta["total_pages"],
    )

    # Persist raw text for later chunking (store in DB-adjacent file)
    import os
    texts_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "texts",
    )
    os.makedirs(texts_dir, exist_ok=True)
    file_path = os.path.join(texts_dir, f"book_{book.id}.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    crud.update_book(db, book.id, file_path=file_path)

    logger.info("Imported book id=%s title=%s words=%s", book.id, title, meta["total_words"])
    return crud.get_book(db, book.id)


# ---------------------------------------------------------------------------
# Book details
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get book details by ID."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/books", response_model=list[BookResponse])
def list_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all books."""
    return crud.get_books(db, skip=skip, limit=limit)


@router.delete("/books/{book_id}", response_model=StatusResponse)
def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book and all related data."""
    if not crud.delete_book(db, book_id):
        raise HTTPException(status_code=404, detail="Book not found")
    return StatusResponse(status="deleted", message=f"Book {book_id} deleted")


# ---------------------------------------------------------------------------
# Chunking
# ---------------------------------------------------------------------------

@router.post("/books/{book_id}/chunk", response_model=StatusResponse)
def chunk_book(book_id: int, db: Session = Depends(get_db)):
    """Split book text into overlapping chunks and store in DB."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if not book.file_path or not os.path.isfile(book.file_path):
        raise HTTPException(
            status_code=400,
            detail="Book text file not found. Import the book first.",
        )

    # Read raw text
    with open(book.file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Delete existing chunks (idempotent re-chunk)
    existing = crud.get_chunks_by_book(db, book_id)
    if existing:
        for c in existing:
            db.delete(c)
        db.commit()

    chunks_data = chunk_text(text)
    crud.create_chunks_batch(db, book_id, chunks_data)

    # Update book metadata
    total_pages = max(
        (cd["end_page"] for cd in chunks_data), default=book.total_pages or 1
    )
    crud.update_book(db, book_id, total_pages=total_pages, status="chunked")

    logger.info(
        "Book %s chunked into %d chunks (%d pages)",
        book_id,
        len(chunks_data),
        total_pages,
    )
    return StatusResponse(
        status="chunked",
        message=f"Created {len(chunks_data)} chunks",
    )


# ---------------------------------------------------------------------------
# AI Analysis
# ---------------------------------------------------------------------------

@router.post("/books/{book_id}/analyze", response_model=AnalyzeStatusResponse)
def analyze_book(
    book_id: int,
    req: BookAnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Run AI analysis on a book: extract characters, locations, dramatic moments.
    Also creates the visual bible and links chunk metadata.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    chunks_db = crud.get_chunks_by_book(db, book_id)
    if not chunks_db:
        raise HTTPException(
            status_code=400,
            detail="Book has no chunks. Call /chunk first.",
        )

    # Update book metadata from the request
    crud.update_book(
        db,
        book_id,
        author=req.author,
        is_well_known=1 if req.is_well_known else 0,
        status="analyzing",
    )

    # Prepare chunk dicts for the AI service
    chunks_for_ai = [
        {"chunk_index": c.chunk_index, "text": c.text} for c in chunks_db
    ]

    # Run the full analysis pipeline (synchronous for MVP)
    try:
        result = run_full_analysis(chunks_for_ai)
    except Exception as exc:
        crud.update_book_status(db, book_id, "error")
        logger.error("Analysis failed for book %s: %s", book_id, exc)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {exc}")

    # ----- Persist characters -----
    char_name_to_id: dict[str, int] = {}
    for ch_data in result.get("main_characters", []):
        char = crud.create_character(
            db,
            book_id=book_id,
            name=ch_data.get("name", "Unknown"),
            physical_description=ch_data.get("physical_description"),
            personality_traits=ch_data.get("personality_traits"),
            typical_emotions=", ".join(ch_data.get("typical_emotions", [])),
        )
        char_name_to_id[char.name.lower()] = char.id

    # ----- Persist locations -----
    loc_name_to_id: dict[str, int] = {}
    for loc_data in result.get("main_locations", []):
        loc = crud.create_location(
            db,
            book_id=book_id,
            name=loc_data.get("name", "Unknown"),
            visual_description=loc_data.get("visual_description"),
            atmosphere=loc_data.get("atmosphere"),
        )
        loc_name_to_id[loc.name.lower()] = loc.id

    # ----- Create visual bible -----
    tone = result.get("tone_and_style", {})
    crud.create_visual_bible(
        db,
        book_id=book_id,
        style_category=req.style_category,
        tone_description=(
            f"{tone.get('genre', '')} | {tone.get('mood', '')} | "
            f"{tone.get('visual_style', '')}"
        ),
        illustration_frequency=req.illustration_frequency,
        layout_style=req.layout_style,
    )

    # ----- Enrich chunks with character/location links + dramatic scores -----
    chunk_index_to_db_id = {c.chunk_index: c.id for c in chunks_db}

    for ca in result.get("chunk_analyses", []):
        idx = ca.get("chunk_index")
        db_chunk_id = chunk_index_to_db_id.get(idx)
        if db_chunk_id is None:
            continue

        # Dramatic score
        score = ca.get("dramatic_score")
        if score is not None:
            crud.update_chunk_dramatic_score(db, db_chunk_id, float(score))

        # Link characters
        char_ids = []
        for name in ca.get("characters_present", []):
            cid = char_name_to_id.get(name.lower())
            if cid:
                char_ids.append(cid)
        if char_ids:
            crud.link_chunk_characters(db, db_chunk_id, char_ids)

        # Link locations
        loc_ids = []
        for name in ca.get("locations_present", []):
            lid = loc_name_to_id.get(name.lower())
            if lid:
                loc_ids.append(lid)
        if loc_ids:
            crud.link_chunk_locations(db, db_chunk_id, loc_ids)

    crud.update_book_status(db, book_id, "ready")

    logger.info(
        "Analysis complete for book %s: %d characters, %d locations",
        book_id,
        len(char_name_to_id),
        len(loc_name_to_id),
    )
    return AnalyzeStatusResponse(status="ready", estimated_time=0)


# ---------------------------------------------------------------------------
# Characters & locations (read)
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/characters", response_model=list[CharacterResponse])
def get_characters(book_id: int, db: Session = Depends(get_db)):
    """Get all characters extracted for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_characters_by_book(db, book_id)


@router.get("/books/{book_id}/locations", response_model=list[LocationResponse])
def get_locations(book_id: int, db: Session = Depends(get_db)):
    """Get all locations extracted for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_locations_by_book(db, book_id)


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/chunks", response_model=list[ChunkResponse])
def get_chunks(book_id: int, db: Session = Depends(get_db)):
    """Get all chunks for a book, ordered by chunk_index."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_chunks_by_book(db, book_id)


# ---------------------------------------------------------------------------
# Reading progress
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/progress", response_model=ReadingProgressResponse)
def get_progress(book_id: int, db: Session = Depends(get_db)):
    """Get reading progress for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_or_create_reading_progress(db, book_id)


@router.post("/books/{book_id}/progress", response_model=ReadingProgressResponse)
def update_progress(
    book_id: int, req: ReadingProgressUpdate, db: Session = Depends(get_db)
):
    """Update reading progress (current page)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.update_reading_progress(db, book_id, req.current_page)
