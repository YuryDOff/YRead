"""Book-related API endpoints."""
import json as json_lib
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas import (
    BookImportRequest,
    BookResponse,
    BookAnalyzeRequest,
    AnalyzeStatusResponse,
    StatusResponse,
    ChunkResponse,
    CharacterResponse,
    LocationResponse,
    SearchQueryResponse,
    EntitySelectionsRequest,
)
from app import crud
from app.services.book_service import (
    download_text_from_google_drive,
    compute_metadata,
    guess_title,
    chunk_text,
)
from app.services.upload_service import process_manuscript_upload, UploadError
from app.services.ai_service import run_full_analysis

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory progress for analysis (book_id -> { current_batch, total_batches })
_analysis_progress: dict[int, dict[str, int]] = {}


# ---------------------------------------------------------------------------
# Book upload (B2B: direct file upload)
# ---------------------------------------------------------------------------

@router.post("/manuscripts/upload", response_model=BookResponse)
async def upload_manuscript(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a manuscript file (.txt, .docx, .pdf) and create a book record.
    This replaces the Google Drive import for B2B author workflow.
    """
    import time
    t0 = time.perf_counter()
    logger.info("[upload] manuscripts/upload: endpoint entered (db session ready) in %.2fs", time.perf_counter() - t0)
    try:
        logger.info("[upload] reading file...")
        file_content = await file.read()
        logger.info("[upload] file.read() done in %.2fs, size=%d bytes", time.perf_counter() - t0, len(file_content))

        upload_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "uploads",
        )

        t1 = time.perf_counter()
        text, metadata = process_manuscript_upload(
            file_content,
            file.filename or "manuscript.txt",
            upload_dir
        )
        logger.info("[upload] process_manuscript_upload done in %.2fs", time.perf_counter() - t1)

        t2 = time.perf_counter()
        book = crud.create_book(
            db,
            title=metadata['title'],
            total_words=metadata['word_count'],
            total_pages=metadata['estimated_pages'],
        )
        logger.info("[upload] crud.create_book done in %.2fs, book_id=%s", time.perf_counter() - t2, book.id)

        texts_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "texts",
        )
        os.makedirs(texts_dir, exist_ok=True)
        text_file_path = os.path.join(texts_dir, f"book_{book.id}.txt")

        t3 = time.perf_counter()
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("[upload] write text file done in %.2fs", time.perf_counter() - t3)

        crud.update_book(db, book.id, file_path=text_file_path)
        logger.info("[upload] full upload flow done in %.2fs", time.perf_counter() - t0)

        logger.info(
            f"Uploaded manuscript: book_id={book.id}, title={metadata['title']}, "
            f"words={metadata['word_count']}, pages={metadata['estimated_pages']}"
        )
        
        return crud.get_book(db, book.id)
        
    except UploadError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Manuscript upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Upload failed. Please try again.")


# ---------------------------------------------------------------------------
# Book import (legacy Google Drive - kept for backwards compatibility)
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

def _run_analysis_background(book_id: int, req_dict: dict[str, Any]) -> None:
    """Run full AI analysis and persist results in a background task (own DB session)."""
    db = SessionLocal()
    try:
        book = crud.get_book(db, book_id)
        if not book:
            logger.error("[analyze] background: book %s not found", book_id)
            return
        chunks_db = crud.get_chunks_by_book(db, book_id)
        if not chunks_db:
            crud.update_book_status(db, book_id, "error")
            logger.error("[analyze] background: no chunks for book %s", book_id)
            return
        chunks_for_ai = [
            {"chunk_index": c.chunk_index, "text": c.text} for c in chunks_db
        ]
        total_chunks = len(chunks_for_ai)
        _analysis_progress[book_id] = {"current_chunk": 0, "total_chunks": total_chunks}
        try:
            def _on_chunks(chunks_processed: int, total: int) -> None:
                _analysis_progress[book_id] = {"current_chunk": chunks_processed, "total_chunks": total}

            scene_count = req_dict.get("scene_count", 10)
            is_well_known_book = bool(req_dict.get("is_well_known", False))
            logger.info("[analyze] background: run_full_analysis book_id=%s chunks=%s scene_count=%s is_well_known=%s", book_id, total_chunks, scene_count, is_well_known_book)
            result = run_full_analysis(chunks_for_ai, progress_callback=_on_chunks, scene_count=scene_count, is_well_known_book=is_well_known_book)
        finally:
            _analysis_progress.pop(book_id, None)
        logger.info("[analyze] background: run_full_analysis done, persisting...")

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
                is_main=bool(ch_data.get("is_main", False)),
                visual_type=ch_data.get("visual_type") or None,
                is_well_known_entity=bool(ch_data.get("is_well_known_entity", False)),
                canonical_search_name=ch_data.get("canonical_search_name") or None,
                search_visual_analog=ch_data.get("search_visual_analog") or None,
            )
            char_name_to_id[char.name.lower()] = char.id
            # Save ontology and entity visual tokens if available
            ontology = ch_data.get("ontology")
            entity_visual_tokens = ch_data.get("entity_visual_tokens")
            if ontology or entity_visual_tokens:
                crud.update_character_ontology(
                    db, char.id,
                    ontology_json=json_lib.dumps(ontology) if ontology else None,
                    entity_visual_tokens_json=json_lib.dumps(entity_visual_tokens) if entity_visual_tokens else None,
                )

        # ----- Persist locations -----
        loc_name_to_id: dict[str, int] = {}
        for loc_data in result.get("main_locations", []):
            loc = crud.create_location(
                db,
                book_id=book_id,
                name=loc_data.get("name", "Unknown"),
                visual_description=loc_data.get("visual_description"),
                atmosphere=loc_data.get("atmosphere"),
                is_main=bool(loc_data.get("is_main", False)),
                is_well_known_entity=bool(loc_data.get("is_well_known_entity", False)),
                canonical_search_name=loc_data.get("canonical_search_name") or None,
                search_visual_analog=loc_data.get("search_visual_analog") or None,
            )
            loc_name_to_id[loc.name.lower()] = loc.id
            # Save ontology and entity visual tokens if available
            ontology = loc_data.get("ontology")
            entity_visual_tokens = loc_data.get("entity_visual_tokens")
            if ontology or entity_visual_tokens:
                crud.update_location_ontology(
                    db, loc.id,
                    ontology_json=json_lib.dumps(ontology) if ontology else None,
                    entity_visual_tokens_json=json_lib.dumps(entity_visual_tokens) if entity_visual_tokens else None,
                )

        # ----- Save known_adaptations to Book -----
        known_adaptations = result.get("known_adaptations")
        if known_adaptations and is_well_known_book:
            try:
                crud.update_book(
                    db, book_id,
                    known_adaptations_json=json_lib.dumps(known_adaptations),
                )
            except Exception as e:
                logger.warning("[analyze] Could not save known_adaptations: %s", e)

        # ----- Create visual bible -----
        tone = result.get("tone_and_style", {})
        crud.create_visual_bible(
            db,
            book_id=book_id,
            style_category=req_dict.get("style_category", "fiction"),
            tone_description=(
                f"{tone.get('genre', '')} | {tone.get('mood', '')} | "
                f"{tone.get('visual_style', '')}"
            ),
            illustration_frequency=req_dict.get("illustration_frequency", 4),
            layout_style=req_dict.get("layout_style", "inline_classic"),
        )

        # ----- Enrich chunks -----
        chunk_index_to_db_id = {c.chunk_index: c.id for c in chunks_db}
        chunks_to_update: dict[int, dict] = {}
        chunk_char_links: list[tuple[int, list[int]]] = []
        chunk_loc_links: list[tuple[int, list[int]]] = []
        for ca in result.get("chunk_analyses", []):
            idx = ca.get("chunk_index")
            db_chunk_id = chunk_index_to_db_id.get(idx)
            if db_chunk_id is None:
                continue
            score = ca.get("dramatic_score")
            if score is not None:
                if db_chunk_id not in chunks_to_update:
                    chunks_to_update[db_chunk_id] = {}
                chunks_to_update[db_chunk_id]["dramatic_score"] = float(score)
            char_ids = [char_name_to_id[n.lower()] for n in ca.get("characters_present", []) if n.lower() in char_name_to_id]
            if char_ids:
                chunk_char_links.append((db_chunk_id, char_ids))
            loc_ids = [loc_name_to_id[n.lower()] for n in ca.get("locations_present", []) if n.lower() in loc_name_to_id]
            if loc_ids:
                chunk_loc_links.append((db_chunk_id, loc_ids))
            visual_data = {}
            if "visual_layers" in ca:
                visual_data["visual_layers"] = ca["visual_layers"]
            if "visual_tokens" in ca:
                visual_data["visual_tokens"] = ca["visual_tokens"]
            if visual_data:
                if db_chunk_id not in chunks_to_update:
                    chunks_to_update[db_chunk_id] = {}
                chunks_to_update[db_chunk_id]["visual_data"] = visual_data
        for chunk_id, updates in chunks_to_update.items():
            chunk = crud.get_chunk(db, chunk_id)
            if chunk:
                if "dramatic_score" in updates:
                    chunk.dramatic_score = updates["dramatic_score"]
                if "visual_data" in updates:
                    chunk.visual_analysis_json = json_lib.dumps(updates["visual_data"])
        for chunk_id, char_ids in chunk_char_links:
            crud.link_chunk_characters(db, chunk_id, char_ids, commit=False)
        for chunk_id, loc_ids in chunk_loc_links:
            crud.link_chunk_locations(db, chunk_id, loc_ids, commit=False)
        try:
            db.commit()
        except Exception as e:
            logger.error("Failed to commit chunk updates: %s", e)
            db.rollback()
            crud.update_book_status(db, book_id, "error")
            return
        # ----- Persist scenes -----
        scenes_data = result.get("scenes", [])
        if scenes_data:
            crud.delete_scenes_by_book(db, book_id)
            for scene_data in scenes_data:
                svt = scene_data.get("scene_visual_tokens")
                t2i = scene_data.get("t2i_prompt_json")
                scene = crud.create_scene(
                    db,
                    book_id=book_id,
                    title=scene_data.get("title"),
                    title_display=scene_data.get("title_display"),
                    scene_type=scene_data.get("scene_type"),
                    chunk_start_index=scene_data.get("chunk_start_index", 0),
                    chunk_end_index=scene_data.get("chunk_end_index", 0),
                    narrative_summary=scene_data.get("narrative_summary"),
                    narrative_summary_display=scene_data.get("narrative_summary_display"),
                    visual_description=scene_data.get("visual_description"),
                    visual_intensity=scene_data.get("visual_intensity"),
                    illustration_priority=scene_data.get("illustration_priority"),
                    scene_prompt_draft=scene_data.get("scene_prompt_draft"),
                    scene_visual_tokens_json=json_lib.dumps(svt) if svt else None,
                    t2i_prompt_json=json_lib.dumps(t2i) if t2i else None,
                    is_selected=1,
                )
                # Link characters
                for char_name in (scene_data.get("characters_present") or []):
                    char_id = char_name_to_id.get(char_name.lower())
                    if char_id:
                        try:
                            crud.create_scene_character(db, scene_id=scene.id, character_id=char_id)
                        except Exception:
                            db.rollback()
                # Link primary location
                primary_loc = scene_data.get("primary_location", "")
                if primary_loc:
                    loc_id = loc_name_to_id.get(primary_loc.lower())
                    if loc_id:
                        try:
                            crud.create_scene_location(db, scene_id=scene.id, location_id=loc_id)
                        except Exception:
                            db.rollback()
            try:
                db.commit()
            except Exception as e:
                logger.error("Failed to commit scenes: %s", e)
                db.rollback()
            logger.info("[analyze] Saved %d scenes for book_id=%s", len(scenes_data), book_id)

        crud.update_book_status(db, book_id, "ready")
        logger.info(
            "[analyze] background complete book_id=%s: %d characters, %d locations, %d scenes",
            book_id, len(char_name_to_id), len(loc_name_to_id), len(scenes_data),
        )
    except Exception as exc:
        logger.exception("Analysis failed for book %s: %s", book_id, exc)
        _analysis_progress.pop(book_id, None)
        try:
            crud.update_book_status(db, book_id, "error")
            db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


@router.post("/books/{book_id}/analyze", response_model=AnalyzeStatusResponse, status_code=202)
def analyze_book(
    book_id: int,
    req: BookAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Start AI analysis in the background. Returns 202 immediately; poll GET /books/{id} for status.
    """
    logger.info("[analyze] START (async) book_id=%s", book_id)
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    chunks_db = crud.get_chunks_by_book(db, book_id)
    if not chunks_db:
        raise HTTPException(
            status_code=400,
            detail="Book has no chunks. Call /chunk first.",
        )
    logger.info("[analyze] Clearing previous analysis for book_id=%s", book_id)
    crud.clear_analysis_results(db, book_id)
    crud.update_book(
        db,
        book_id,
        author=req.author,
        is_well_known=1 if req.is_well_known else 0,
        well_known_book_title=req.well_known_book_title,
        similar_book_title=req.similar_book_title,
        status="analyzing",
    )
    db.commit()
    background_tasks.add_task(_run_analysis_background, book_id, req.model_dump())
    logger.info("[analyze] 202 Accepted – background task started")
    return AnalyzeStatusResponse(status="analyzing", estimated_time=600)


@router.get("/books/{book_id}/analysis-progress")
def get_analysis_progress(book_id: int):
    """Return current batch / total batches while analysis is running. 404 if not in progress."""
    if book_id not in _analysis_progress:
        raise HTTPException(status_code=404, detail="No analysis in progress for this book")
    return _analysis_progress[book_id]


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


@router.put("/books/{book_id}/entity-selections", response_model=StatusResponse)
def update_entity_selections(
    book_id: int,
    req: EntitySelectionsRequest,
    db: Session = Depends(get_db),
):
    """Batch-update is_main flags for characters and locations."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for item in req.characters:
        crud.update_character(db, item.id, is_main=1 if item.is_main else 0)

    for item in req.locations:
        crud.update_location(db, item.id, is_main=1 if item.is_main else 0)

    return StatusResponse(
        status="updated",
        message=f"Updated {len(req.characters)} characters, {len(req.locations)} locations",
    )


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
# Search queries (audit log)
# ---------------------------------------------------------------------------

@router.get(
    "/books/{book_id}/search-queries",
    response_model=list[SearchQueryResponse],
)
def get_search_queries(book_id: int, db: Session = Depends(get_db)):
    """Get all search queries that were run for a book's reference images."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_search_queries_by_book(db, book_id)
