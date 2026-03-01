"""Book-related API endpoints."""
import json as json_lib
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas import (
    BookImportRequest,
    BookUpdateRequest,
    BookCreate,
    BookRead,
    BookResponse,
    BookAnalyzeRequest,
    AnalyzeStatusResponse,
    AnalyzeEntityRequest,
    StatusResponse,
    ChunkResponse,
    CharacterResponse,
    LocationResponse,
    SearchQueryResponse,
    EntitySelectionsRequest,
    EntityActivationsRequest,
    ArtefactResponse,
    ArtefactUpdate,
)
from app import crud
from app.services.book_service import (
    download_text_from_google_drive,
    compute_metadata,
    guess_title,
    chunk_text,
)
from app.services.upload_service import process_manuscript_upload, UploadError
from app.services.ai_service import MAX_MAIN_CHARACTERS, MAX_MAIN_LOCATIONS, run_full_analysis, get_entity_types_for_mode

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory progress: book_id -> { overall_status, entity_progress: { entity_type: { status, current, total } } }
_analysis_progress: dict[int, dict[str, Any]] = {}
_progress_lock = threading.Lock()


def _update_entity_progress(book_id: int, entity_type: str, status: str, current: int, total: int) -> None:
    """Thread-safe update of a single entity's progress."""
    with _progress_lock:
        if book_id in _analysis_progress and "entity_progress" in _analysis_progress[book_id]:
            _analysis_progress[book_id]["entity_progress"][entity_type] = {
                "status": status,
                "current": current,
                "total": total,
            }


def _set_overall_status(book_id: int, status: str) -> None:
    """Thread-safe update of overall_status."""
    with _progress_lock:
        if book_id in _analysis_progress:
            _analysis_progress[book_id]["overall_status"] = status




@router.post("/books", response_model=BookRead, status_code=201)
def create_book(body: BookCreate, db: Session = Depends(get_db)):
    """Create a book record (minimal payload) for tests and lightweight workflows."""
    book = crud.create_book(
        db,
        title=body.title,
        author=body.author,
        analysis_mode=body.analysis_mode,
    )
    return book
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


@router.patch("/books/{book_id}", response_model=BookResponse)
def patch_book(
    book_id: int,
    body: BookUpdateRequest,
    db: Session = Depends(get_db),
):
    """Partial update of book (e.g. search_query_strategy for Phase 7.7.4)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    updates = body.model_dump(exclude_unset=True)
    if updates:
        crud.update_book(db, book_id, **updates)
        book = crud.get_book(db, book_id)
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
    """
    Runs entity analysis jobs based on entity_types in req_dict.
    Updates _analysis_progress per-entity. Selective clear per type.
    """
    from app.services.artefact_analysis_service import run_artefact_analysis
    from app.services.cover_analysis_service import run_cover_analysis
    from app.services.ai_service import detect_manuscript_language

    db = SessionLocal()
    entity_types = req_dict.get("entity_types") or ["cover", "characters", "locations", "artefacts"]
    genre = req_dict.get("genre") or ""
    try:
        book = crud.get_book(db, book_id)
        if not book:
            logger.error("[analyze] background: book %s not found", book_id)
            return
        analysis_mode = getattr(book, "analysis_mode", "pro") or "pro"
        mapped = get_entity_types_for_mode(analysis_mode, entity_types)
        if mapped == ["character"]:
            entity_types = ["characters"]

        # Persist display/audience from request (extraction uses total_words, not scene_count)
        if "scene_display_count" in req_dict:
            crud.update_book(db, book_id, scene_display_count=req_dict["scene_display_count"])
        if "target_audience" in req_dict:
            crud.update_book(db, book_id, target_audience=req_dict["target_audience"])
        if "search_query_strategy" in req_dict:
            crud.update_book(db, book_id, search_query_strategy=req_dict["search_query_strategy"])
        chunks_db = crud.get_chunks_by_book(db, book_id)
        if not chunks_db:
            crud.update_book_status(db, book_id, "error")
            logger.error("[analyze] background: no chunks for book %s", book_id)
            return
        chunks_for_ai = [{"chunk_index": c.chunk_index, "text": c.text} for c in chunks_db]
        total_chunks = len(chunks_for_ai)
        _analysis_progress[book_id] = {
            "overall_status": "running",
            "entity_progress": {
                et: {"status": "pending", "current": 0, "total": total_chunks if et in ("characters", "locations") else (3 if et == "artefacts" else 2)}
                for et in entity_types
            },
        }
        for et in _analysis_progress[book_id]["entity_progress"]:
            tot = 3 if et == "artefacts" else (2 if et == "cover" else total_chunks)
            _update_entity_progress(book_id, et, "pending", 0, tot)

        result_full = None
        chunk_analyses_for_downstream = []
        chunk_text_map = {c.chunk_index: c.text for c in chunks_db}
        manuscript_lang = "en"

        try:
            if "characters" in entity_types or "locations" in entity_types:
                for et in ("characters", "locations"):
                    if et in _analysis_progress.get(book_id, {}).get("entity_progress", {}):
                        _update_entity_progress(book_id, et, "running", 0, total_chunks)
                crud.clear_characters_locations_scenes(db, book_id)

                def _on_chunks(chunks_processed: int, total: int) -> None:
                    if book_id in _analysis_progress:
                        for et in ("characters", "locations"):
                            if et in _analysis_progress[book_id]["entity_progress"]:
                                _update_entity_progress(book_id, et, "running", chunks_processed, total)

                workflow_type = (getattr(book, "workflow_type", None) or "full").strip().lower()
                skip_scenes = (workflow_type == "cover_only") and ("characters" not in entity_types)
                total_words = (book.total_words or 0) if not skip_scenes else 0
                is_well_known_book = bool(req_dict.get("is_well_known", False))
                result_full = run_full_analysis(
                    chunks_for_ai,
                    progress_callback=_on_chunks,
                    total_words=total_words,
                    is_well_known_book=is_well_known_book,
                )
                chunk_analyses_for_downstream = result_full.get("chunk_analyses", [])
                manuscript_lang = detect_manuscript_language(chunks_for_ai)
                for et in ("characters", "locations"):
                    if et in _analysis_progress.get(book_id, {}).get("entity_progress", {}):
                        _update_entity_progress(book_id, et, "complete", total_chunks, total_chunks)
                # ----- Persist characters -----
                char_name_to_id = {}
                for ch_data in result_full.get("main_characters", [])[:MAX_MAIN_CHARACTERS]:
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
                        cover_role=ch_data.get("cover_role", 0) or 0,
                        visual_bible_depth=ch_data.get("visual_bible_depth"),
                        full_description=ch_data.get("full_description"),
                    )
                    char_name_to_id[char.name.lower()] = char.id
                    ontology = ch_data.get("ontology")
                    entity_visual_tokens = ch_data.get("entity_visual_tokens")
                    if ontology or entity_visual_tokens:
                        crud.update_character_ontology(
                            db, char.id,
                            ontology_json=json_lib.dumps(ontology) if ontology else None,
                            entity_visual_tokens_json=json_lib.dumps(entity_visual_tokens) if entity_visual_tokens else None,
                        )

                # ----- Persist locations -----
                loc_name_to_id = {}
                for loc_data in result_full.get("main_locations", [])[:MAX_MAIN_LOCATIONS]:
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
                        cover_role=loc_data.get("cover_role", 0) or 0,
                        visual_bible_depth=loc_data.get("visual_bible_depth"),
                        full_description=loc_data.get("full_description"),
                    )
                    loc_name_to_id[loc.name.lower()] = loc.id
                    ontology = loc_data.get("ontology")
                    entity_visual_tokens = loc_data.get("entity_visual_tokens")
                    if ontology or entity_visual_tokens:
                        crud.update_location_ontology(
                            db, loc.id,
                            ontology_json=json_lib.dumps(ontology) if ontology else None,
                            entity_visual_tokens_json=json_lib.dumps(entity_visual_tokens) if entity_visual_tokens else None,
                        )

                if is_well_known_book and result_full.get("known_adaptations"):
                    try:
                        crud.update_book(db, book_id, known_adaptations_json=json_lib.dumps(result_full["known_adaptations"]))
                    except Exception as e:
                        logger.warning("[analyze] Could not save known_adaptations: %s", e)

                tone = result_full.get("tone_and_style", {})
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
                chunks_to_update = {}
                chunk_char_links = []
                chunk_loc_links = []
                for ca in result_full.get("chunk_analyses", []):
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
                    raise
                scenes_data = result_full.get("scenes", [])
                if scenes_data:
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
                        for char_name in (scene_data.get("characters_present") or []):
                            char_id = char_name_to_id.get(char_name.lower())
                            if char_id:
                                try:
                                    crud.create_scene_character(db, scene_id=scene.id, character_id=char_id)
                                except Exception:
                                    db.rollback()
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

            # Chunk analyses for artefacts/cover (from run_full_analysis or DB)
            if not chunk_analyses_for_downstream:
                chunk_analyses_for_downstream, _ctm = crud.get_chunk_analyses_for_book(db, book_id)
                if _ctm and not chunk_analyses_for_downstream:
                    chunk_analyses_for_downstream = [{"chunk_index": ci, "dramatic_score": 0.0, "visual_moment": "", "narrative_summary": ""} for ci in _ctm]
                if _ctm:
                    chunk_text_map = _ctm

            need_artefacts = "artefacts" in entity_types
            need_cover = "cover" in entity_types
            if need_cover:
                existing_chars = [{"name": c.name, "is_main": c.is_main, "cover_role": getattr(c, "cover_role", 0)} for c in crud.get_characters_by_book(db, book_id)]
                existing_locs = [{"name": l.name, "is_main": l.is_main, "cover_role": getattr(l, "cover_role", 0)} for l in crud.get_locations_by_book(db, book_id)]
            else:
                existing_chars = []
                existing_locs = []

            def _artefact_progress(_et: str, cur: int, tot: int) -> None:
                if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "artefacts", "running", cur, tot)

            def _persist_artefacts(artefact_result: dict) -> None:
                artefacts_data = artefact_result.get("artefacts", [])
                chunk_index_to_db_id = {c.chunk_index: c.id for c in chunks_db}
                scenes_db = crud.get_scenes_by_book(db, book_id)
                scene_title_to_id = {s.title.lower(): s.id for s in scenes_db if s.title}
                for a_data in artefacts_data:
                    a = crud.create_artefact(
                        db,
                        book_id=book_id,
                        name=a_data.get("name", "Unknown"),
                        physical_description=a_data.get("physical_description"),
                        symbolic_role=a_data.get("symbolic_role"),
                        narrative_function=a_data.get("narrative_function"),
                        typical_contexts=a_data.get("typical_contexts"),
                        is_main=1 if a_data.get("is_main") else 0,
                        full_description=a_data.get("full_description"),
                    )
                    crud.update_artefact(db, a.id, visual_type=a_data.get("visual_type"))
                    onto = {k: v for k, v in a_data.items() if k in ("entity_class", "visual_markers", "search_archetype") and v is not None}
                    tokens = {k: a_data.get(k) for k in ("core_tokens", "style_tokens", "archetype_tokens", "anti_tokens") if a_data.get(k)}
                    crud.update_artefact_ontology(
                        db, a.id,
                        ontology_json=json_lib.dumps(onto) if onto else None,
                        entity_visual_tokens_json=json_lib.dumps(tokens) if tokens else None,
                    )
                    for chunk_idx in a_data.get("chunks_present") or []:
                        cid = chunk_index_to_db_id.get(chunk_idx)
                        if cid:
                            crud.link_chunk_artefact(db, cid, a.id)
                    for scene_title_hint in (a_data.get("scenes_present") or [])[:5]:
                        sid = scene_title_to_id.get(str(scene_title_hint).lower())
                        if sid:
                            crud.link_scene_artefact(db, sid, a.id)
                db.commit()

            if need_artefacts and need_cover:
                # Run artefact and cover analysis in parallel (LLM only); persist in main thread after both complete
                if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "artefacts", "running", 0, 3)
                if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "cover", "running", 0, 2)
                crud.clear_artefacts_for_book(db, book_id)
                artefact_result = None
                cover_brief = None
                try:
                    with ThreadPoolExecutor(max_workers=2) as executor:
                        future_art = executor.submit(
                            run_artefact_analysis,
                            chunk_analyses_for_downstream,
                            chunk_text_map,
                            manuscript_lang=manuscript_lang,
                            progress_callback=_artefact_progress,
                        )
                        future_cover = executor.submit(
                            run_cover_analysis,
                            chunk_analyses_for_downstream,
                            genre=genre or "fiction",
                            style_category=req_dict.get("style_category", "fiction"),
                            existing_characters=existing_chars,
                            existing_locations=existing_locs,
                        )
                        artefact_result = future_art.result()
                        cover_brief = future_cover.result()
                except Exception as e:
                    logger.exception("[analyze] artefacts or cover (parallel) failed: %s", e)
                    if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                        _update_entity_progress(book_id, "artefacts", "failed", 0, 3)
                    if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                        _update_entity_progress(book_id, "cover", "failed", 0, 2)
                    raise
                if artefact_result is not None:
                    _persist_artefacts(artefact_result)
                if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "artefacts", "complete", 3, 3)
                if cover_brief is not None:
                    char_by_name = {c.name.lower(): c.id for c in crud.get_characters_by_book(db, book_id)}
                    loc_by_name = {l.name.lower(): l.id for l in crud.get_locations_by_book(db, book_id)}
                    artefact_by_name = {a.name.lower(): a.id for a in crud.get_artefacts_by_book(db, book_id)}
                    cover_role_char_ids = [char_by_name[n.lower()] for n in (cover_brief.get("cover_role_character_ids_hints") or []) if n and n.lower() in char_by_name]
                    cover_role_loc_ids = [loc_by_name[n.lower()] for n in (cover_brief.get("cover_role_location_ids_hints") or []) if n and n.lower() in loc_by_name]
                    cover_role_artefact_ids = [artefact_by_name[n.lower()] for n in (cover_brief.get("cover_role_artefact_ids_hints") or []) if n and n.lower() in artefact_by_name]
                    primary_hint = (cover_brief.get("cover_role_primary_hint") or "").strip()
                    primary_char_id = char_by_name.get(primary_hint.lower()) if primary_hint else None
                    primary_loc_id = loc_by_name.get(primary_hint.lower()) if primary_hint else None
                    primary_art_id = artefact_by_name.get(primary_hint.lower()) if primary_hint else None
                    primary_cover_character_id = primary_char_id if primary_char_id else None
                    primary_cover_location_id = primary_loc_id if primary_loc_id else None
                    primary_cover_artefact_id = primary_art_id if primary_art_id else None
                    genre = req_dict.get("genre") or ""
                    thematic = cover_brief.get("thematic_statement") or f"Cover concept for {genre or 'fiction'}."
                    symbolic_anchors = cover_brief.get("symbolic_anchors")
                    symbolic_anchors = symbolic_anchors if isinstance(symbolic_anchors, list) else []
                    mood_kw = cover_brief.get("cover_mood_keywords")
                    mood_kw = mood_kw if isinstance(mood_kw, list) else []
                    crud.create_or_update_cover_analysis(
                        db,
                        book_id=book_id,
                        thematic_statement=thematic,
                        emotional_promise=cover_brief.get("emotional_promise"),
                        dominant_motifs=cover_brief.get("dominant_motifs"),
                        symbolic_anchors=symbolic_anchors,
                        cover_mood_keywords=mood_kw,
                        genre_conventions=cover_brief.get("genre_conventions"),
                        genre_subversion_opportunity=cover_brief.get("genre_subversion_opportunity"),
                        typography_direction=cover_brief.get("typography_direction"),
                        color_palette_direction=cover_brief.get("color_palette_direction"),
                        cover_t2i_prompt=cover_brief.get("cover_t2i_prompt"),
                        cover_negative_prompt=cover_brief.get("cover_negative_prompt"),
                        cover_role_character_ids=cover_role_char_ids,
                        cover_role_location_ids=cover_role_loc_ids,
                        cover_role_artefact_ids=cover_role_artefact_ids,
                        cover_type=cover_brief.get("cover_type"),
                        color_palette_structured=cover_brief.get("color_palette_structured"),
                        primary_cover_character_id=primary_cover_character_id,
                        primary_cover_location_id=primary_cover_location_id,
                        primary_cover_artefact_id=primary_cover_artefact_id,
                    )
                    db.commit()
                if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "cover", "complete", 2, 2)
            elif need_artefacts:
                if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "artefacts", "running", 0, 3)
                crud.clear_artefacts_for_book(db, book_id)
                try:
                    artefact_result = run_artefact_analysis(
                        chunk_analyses_for_downstream,
                        chunk_text_map,
                        manuscript_lang=manuscript_lang,
                        progress_callback=_artefact_progress,
                    )
                    _persist_artefacts(artefact_result)
                except Exception as e:
                    logger.exception("[analyze] artefacts failed: %s", e)
                    if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                        _update_entity_progress(book_id, "artefacts", "failed", 0, 3)
                    raise
                if book_id in _analysis_progress and "artefacts" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "artefacts", "complete", 3, 3)
            elif need_cover:
                if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "cover", "running", 0, 2)
                try:
                    cover_brief = run_cover_analysis(
                        chunk_analyses_for_downstream,
                        genre=genre or "fiction",
                        style_category=req_dict.get("style_category", "fiction"),
                        existing_characters=existing_chars,
                        existing_locations=existing_locs,
                    )
                    char_by_name = {c.name.lower(): c.id for c in crud.get_characters_by_book(db, book_id)}
                    loc_by_name = {l.name.lower(): l.id for l in crud.get_locations_by_book(db, book_id)}
                    artefact_by_name = {a.name.lower(): a.id for a in crud.get_artefacts_by_book(db, book_id)}
                    cover_role_char_ids = [char_by_name[n.lower()] for n in (cover_brief.get("cover_role_character_ids_hints") or []) if n and n.lower() in char_by_name]
                    cover_role_loc_ids = [loc_by_name[n.lower()] for n in (cover_brief.get("cover_role_location_ids_hints") or []) if n and n.lower() in loc_by_name]
                    cover_role_artefact_ids = [artefact_by_name[n.lower()] for n in (cover_brief.get("cover_role_artefact_ids_hints") or []) if n and n.lower() in artefact_by_name]
                    primary_hint = (cover_brief.get("cover_role_primary_hint") or "").strip()
                    primary_cover_character_id = char_by_name.get(primary_hint.lower()) if primary_hint else None
                    primary_cover_location_id = loc_by_name.get(primary_hint.lower()) if primary_hint else None
                    primary_cover_artefact_id = artefact_by_name.get(primary_hint.lower()) if primary_hint else None
                    g = genre or "fiction"
                    thematic = cover_brief.get("thematic_statement") or f"Cover concept for {g}."
                    sym = cover_brief.get("symbolic_anchors")
                    sym = sym if isinstance(sym, list) else []
                    mood = cover_brief.get("cover_mood_keywords")
                    mood = mood if isinstance(mood, list) else []
                    crud.create_or_update_cover_analysis(
                        db,
                        book_id=book_id,
                        thematic_statement=thematic,
                        emotional_promise=cover_brief.get("emotional_promise"),
                        dominant_motifs=cover_brief.get("dominant_motifs"),
                        symbolic_anchors=sym,
                        cover_mood_keywords=mood,
                        genre_conventions=cover_brief.get("genre_conventions"),
                        genre_subversion_opportunity=cover_brief.get("genre_subversion_opportunity"),
                        typography_direction=cover_brief.get("typography_direction"),
                        color_palette_direction=cover_brief.get("color_palette_direction"),
                        cover_t2i_prompt=cover_brief.get("cover_t2i_prompt"),
                        cover_negative_prompt=cover_brief.get("cover_negative_prompt"),
                        cover_role_character_ids=cover_role_char_ids,
                        cover_role_location_ids=cover_role_loc_ids,
                        cover_role_artefact_ids=cover_role_artefact_ids,
                        cover_type=cover_brief.get("cover_type"),
                        color_palette_structured=cover_brief.get("color_palette_structured"),
                        primary_cover_character_id=primary_cover_character_id,
                        primary_cover_location_id=primary_cover_location_id,
                        primary_cover_artefact_id=primary_cover_artefact_id,
                    )
                    db.commit()
                except Exception as e:
                    logger.exception("[analyze] cover failed: %s", e)
                    if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                        _update_entity_progress(book_id, "cover", "failed", 0, 2)
                    raise
                if book_id in _analysis_progress and "cover" in _analysis_progress[book_id]["entity_progress"]:
                    _update_entity_progress(book_id, "cover", "complete", 2, 2)

            completed = [et for et in entity_types if _analysis_progress.get(book_id, {}).get("entity_progress", {}).get(et, {}).get("status") == "complete"]
            existing_activations = []
            if book.entity_activations:
                try:
                    existing_activations = json_lib.loads(book.entity_activations) or []
                except Exception:
                    pass
            merged = list(dict.fromkeys(existing_activations + completed))
            crud.update_book(db, book_id, entity_activations=merged)
            if genre:
                crud.update_book(db, book_id, genre=genre)
            db.commit()
            _set_overall_status(book_id, "complete")
            crud.update_book_status(db, book_id, "ready")
            logger.info("[analyze] background complete book_id=%s entity_types=%s", book_id, entity_types)
        except Exception:
            _set_overall_status(book_id, "failed")
            crud.update_book_status(db, book_id, "error")
            raise
        finally:
            pass
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
    entity_types = getattr(req, "entity_types", None) or ["cover", "characters", "locations", "artefacts"]
    if set(entity_types) == {"cover", "characters", "locations", "artefacts"}:
        logger.info("[analyze] Full entity set: clearing previous analysis for book_id=%s", book_id)
        crud.clear_analysis_results(db, book_id)
    update_kw: dict = {
        "author": req.author,
        "is_well_known": 1 if req.is_well_known else 0,
        "well_known_book_title": req.well_known_book_title,
        "similar_book_title": req.similar_book_title,
        "genre": req.genre or book.genre,
        "scene_count": getattr(req, "scene_count", None) or book.scene_count or 10,
        "status": "analyzing",
    }
    if hasattr(req, "workflow_type") and req.workflow_type:
        update_kw["workflow_type"] = (req.workflow_type or "").strip().lower() or "full"
    crud.update_book(db, book_id, **update_kw)
    db.commit()
    background_tasks.add_task(_run_analysis_background, book_id, req.model_dump())
    logger.info("[analyze] 202 Accepted – background task started")
    return AnalyzeStatusResponse(status="analyzing", estimated_time=600)


@router.get("/books/{book_id}/analysis-progress")
def get_analysis_progress(book_id: int):
    """Return overall_status and entity_progress (Phase 5 format). 404 if no analysis in progress."""
    if book_id not in _analysis_progress:
        raise HTTPException(status_code=404, detail="No analysis in progress for this book")
    return _analysis_progress[book_id]


@router.post("/books/{book_id}/analyze/entity", response_model=AnalyzeStatusResponse, status_code=202)
def analyze_entity(
    book_id: int,
    req: AnalyzeEntityRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Run analysis for a single entity type only (e.g. artefacts). Preserves other entity data."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    chunks_db = crud.get_chunks_by_book(db, book_id)
    if not chunks_db:
        raise HTTPException(status_code=400, detail="Book has no chunks. Call /chunk first.")
    et = (req.entity_type or "").strip().lower()
    if et not in ("characters", "locations", "artefacts", "cover"):
        raise HTTPException(status_code=400, detail="entity_type must be one of: characters, locations, artefacts, cover")
    req_dict = {
        "entity_types": [et],
        "genre": book.genre or "",
        "style_category": getattr(book, "style_category", None) or "fiction",
        "scene_count": book.scene_count or 10,
        "is_well_known": bool(book.is_well_known),
        "illustration_frequency": 4,
        "layout_style": "inline_classic",
    }
    background_tasks.add_task(_run_analysis_background, book_id, req_dict)
    return AnalyzeStatusResponse(status="analyzing", estimated_time=300)


# ---------------------------------------------------------------------------
# Artefacts (Phase 5)
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/artefacts", response_model=list[ArtefactResponse])
def get_artefacts(book_id: int, db: Session = Depends(get_db)):
    """Get all artefacts extracted for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return crud.get_artefacts_by_book(db, book_id)


@router.put("/books/{book_id}/artefacts/{artefact_id}", response_model=ArtefactResponse)
def update_artefact_endpoint(
    book_id: int,
    artefact_id: int,
    body: ArtefactUpdate,
    db: Session = Depends(get_db),
):
    """Update an artefact (user edits). Accepts partial fields."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    artefact = crud.get_artefact(db, artefact_id)
    if not artefact or artefact.book_id != book_id:
        raise HTTPException(status_code=404, detail="Artefact not found")
    updates = body.model_dump(exclude_unset=True)
    if updates:
        crud.update_artefact(db, artefact_id, **updates)
    return crud.get_artefact(db, artefact_id)


@router.put("/books/{book_id}/entity-activations", response_model=StatusResponse)
def update_entity_activations(
    book_id: int,
    req: EntityActivationsRequest,
    db: Session = Depends(get_db),
):
    """Update book.entity_activations (list of active entity types)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    crud.update_book_entity_activations(db, book_id, req.entity_activations or [])
    return StatusResponse(status="updated", message="Entity activations updated")


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
    """Batch-update is_selected_for_reference only. Never writes is_main."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    for item in req.characters:
        crud.update_entity_reference_selection(db, item.id, 1 if item.is_main else 0, "character")
    for item in req.locations:
        crud.update_entity_reference_selection(db, item.id, 1 if item.is_main else 0, "location")
    for item in req.artefacts:
        crud.update_entity_reference_selection(db, item.id, 1 if item.is_main else 0, "artefact")

    return StatusResponse(
        status="updated",
        message=f"Updated {len(req.characters)} characters, {len(req.locations)} locations, {len(req.artefacts)} artefacts",
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
