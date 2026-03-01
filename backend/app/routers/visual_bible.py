"""Visual Bible API endpoints."""
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    VisualBibleResponse,
    VisualBibleApproveRequest,
    SearchReferencesRequest,
    EntitySummariesUpdate,
    CharacterResponse,
    LocationResponse,
    StatusResponse,
    EngineRatingUpdate,
    EngineRatingResponse,
    CoverAnalysisResponse,
    CoverAnalysisUpdateRequest,
    VisualBibleEntryResponse,
    VisualBibleEntryGenerateRequest,
    VisualBibleEntryGenerateAllRequest,
    VisualBibleEntryPatchRequest,
)
from app import crud
from app.models import VisualBibleEntry
from app.services.search_service import (
    search_references_for_book,
    get_proposed_search_queries,
    CHARACTER_PLACEHOLDER,
    LOCATION_PLACEHOLDER,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Visual Bible retrieval
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/visual-bible")
async def get_visual_bible(book_id: int, db: Session = Depends(get_db)):
    """
    Get the visual bible for a book, including characters, locations,
    and their reference images.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    vb = crud.get_visual_bible(db, book_id)
    if not vb:
        raise HTTPException(
            status_code=404,
            detail="Visual bible not found. Analyze the book first.",
        )

    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)

    def char_dump(c):
        d = CharacterResponse.model_validate(c).model_dump()
        d["selected_reference_urls"] = (
            json.loads(c.selected_reference_urls) if getattr(c, "selected_reference_urls", None) else []
        )
        if not isinstance(d["selected_reference_urls"], list):
            d["selected_reference_urls"] = []
        return d

    def loc_dump(loc):
        d = LocationResponse.model_validate(loc).model_dump()
        d["selected_reference_urls"] = (
            json.loads(loc.selected_reference_urls) if getattr(loc, "selected_reference_urls", None) else []
        )
        if not isinstance(d["selected_reference_urls"], list):
            d["selected_reference_urls"] = []
        return d

    return {
        "visual_bible": VisualBibleResponse.model_validate(vb).model_dump(),
        "characters": [char_dump(c) for c in characters],
        "locations": [loc_dump(loc) for loc in locations],
    }


# ---------------------------------------------------------------------------
# Proposed search queries (for user review before search)
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/proposed-search-queries")
def get_proposed_queries(
    book_id: int,
    main_only: bool = True,
    db: Session = Depends(get_db),
):
    """
    Return proposed search query strings for each main (or all) character/location.
    User can review and edit these before calling POST search-references.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return get_proposed_search_queries(book_id, db, main_only=main_only)


# ---------------------------------------------------------------------------
# Entity summaries (batch update before search)
# ---------------------------------------------------------------------------

@router.patch("/books/{book_id}/entity-summaries")
def patch_entity_summaries(
    book_id: int,
    body: EntitySummariesUpdate,
    db: Session = Depends(get_db),
):
    """Update character/location summaries and search fields (for review step)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for item in body.characters:
        eid = item.get("id")
        if eid is not None:
            data = {k: v for k, v in item.items() if k != "id" and v is not None}
            if data:
                crud.update_character(db, int(eid), **data)
    for item in body.locations:
        eid = item.get("id")
        if eid is not None:
            data = {k: v for k, v in item.items() if k != "id" and v is not None}
            if data:
                crud.update_location(db, int(eid), **data)
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Reference image search
# ---------------------------------------------------------------------------

@router.post("/books/{book_id}/search-references")
async def search_references(
    book_id: int,
    req: Optional[SearchReferencesRequest] = None,
    db: Session = Depends(get_db),
):
    """
    Search reference images for characters and locations of a book.

    When *main_only* is True (default), only the main character and main
    location are searched. Optional body: character_queries, location_queries
    (entity id -> list of query strings) to use instead of built queries;
    character_summaries, location_summaries to update DB before search.

    Returns:
        characters: {name: images[]} — compatible with VisualBibleReview
        locations: {name: images[]}
        queries_run, provider_usage
    """
    main_only = req.main_only if req else True
    req = req or SearchReferencesRequest()

    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)

    search_entity_types = req.search_entity_types or "both"
    needs_chars_locs = search_entity_types in ("both", "characters", "locations", "all")
    if needs_chars_locs and not characters and not locations:
        raise HTTPException(
            status_code=400,
            detail="No characters or locations found. Analyze the book first.",
        )

    def _int_key(d: Optional[dict]) -> Optional[dict]:
        if not d:
            return None
        return {int(k): v for k, v in d.items()}

    def _int_key_cover_queries(q: Optional[list]) -> Optional[list[str]]:
        if not q:
            return None
        return [str(x).strip() for x in q if str(x).strip()]

    result = await search_references_for_book(
        book_id=book_id,
        search_all=not main_only,
        db=db,
        character_queries=_int_key(req.character_queries),
        location_queries=_int_key(req.location_queries),
        character_summaries=_int_key(req.character_summaries),
        location_summaries=_int_key(req.location_summaries),
        preferred_provider=req.preferred_provider,
        search_entity_types=search_entity_types,
        enabled_providers=req.enabled_providers,
        artefact_queries=_int_key(req.artefact_queries) if req.artefact_queries else None,
        cover_queries=_int_key_cover_queries(req.cover_queries),
    )

    # Convert to format expected by VisualBibleReview: characters: {name: images[]}
    # Preserve actual provider as source (unsplash, serpapi, pexels, pixabay, openverse, wikimedia, deviantart, user)
    chars_by_name: dict[str, list] = {}
    for item in result.get("characters", []):
        images = item.get("images", [])
        for img in images:
            img.setdefault("source", img.get("provider") or "unsplash")
        chars_by_name[item["name"]] = images

    locs_by_name: dict[str, list] = {}
    for item in result.get("locations", []):
        images = item.get("images", [])
        for img in images:
            img.setdefault("source", img.get("provider") or "serpapi")
        locs_by_name[item["name"]] = images

    # Persist search results to reference_images (append, FIFO cap 50 per entity)
    char_list = result.get("characters", [])
    for item in char_list:
        char = next((c for c in characters if c.name == item["name"]), None)
        if not char:
            continue
        for img in item.get("images", []):
            url = img.get("url")
            if not url:
                continue
            if crud.get_reference_image_by_entity_url(db, "character", char.id, url):
                continue
            src = img.get("source") or img.get("provider") or "unsplash"
            crud.create_reference_image(
                db,
                book_id=book_id,
                entity_type="character",
                entity_id=char.id,
                url=url,
                thumbnail=img.get("thumbnail"),
                width=img.get("width"),
                height=img.get("height"),
                source=src,
            )
        exclude = set(crud.get_selected_reference_urls(db, "character", char.id))
        crud.trim_reference_images_fifo(db, "character", char.id, exclude_urls=exclude)

    loc_list = result.get("locations", [])
    for item in loc_list:
        loc = next((l for l in locations if l.name == item["name"]), None)
        if not loc:
            continue
        for img in item.get("images", []):
            url = img.get("url")
            if not url:
                continue
            if crud.get_reference_image_by_entity_url(db, "location", loc.id, url):
                continue
            src = img.get("source") or img.get("provider") or "serpapi"
            crud.create_reference_image(
                db,
                book_id=book_id,
                entity_type="location",
                entity_id=loc.id,
                url=url,
                thumbnail=img.get("thumbnail"),
                width=img.get("width"),
                height=img.get("height"),
                source=src,
            )
        exclude = set(crud.get_selected_reference_urls(db, "location", loc.id))
        crud.trim_reference_images_fifo(db, "location", loc.id, exclude_urls=exclude)

    artefacts = crud.get_artefacts_by_book(db, book_id)
    artefacts_by_name = {a.name: a for a in artefacts}
    artefacts_out: dict[str, list] = {}
    for item in result.get("artefacts", []):
        images = item.get("images", [])
        for img in images:
            img.setdefault("source", img.get("provider") or "unsplash")
        artefacts_out[item["name"]] = images
        artefact = artefacts_by_name.get(item["name"])
        if artefact:
            for img in images:
                url = img.get("url")
                if not url:
                    continue
                if crud.get_reference_image_by_entity_url(db, "artefact", artefact.id, url):
                    continue
                src = img.get("source") or img.get("provider") or "unsplash"
                crud.create_reference_image(
                    db,
                    book_id=book_id,
                    entity_type="artefact",
                    entity_id=artefact.id,
                    url=url,
                    thumbnail=img.get("thumbnail"),
                    width=img.get("width"),
                    height=img.get("height"),
                    source=src,
                )
            exclude = set(crud.get_selected_reference_urls(db, "artefact", artefact.id))
            crud.trim_reference_images_fifo(db, "artefact", artefact.id, exclude_urls=exclude)

    cover_out: dict[str, list] = {}
    cover_result = result.get("cover")
    if cover_result:
        images = cover_result.get("images", [])
        for img in images:
            img.setdefault("source", img.get("provider") or "unsplash")
        cover_out["cover"] = images
        cover_analysis = crud.get_cover_analysis(db, book_id)
        if cover_analysis:
            for img in images:
                url = img.get("url")
                if not url:
                    continue
                if crud.get_reference_image_by_entity_url(db, "cover", cover_analysis.id, url):
                    continue
                src = img.get("source") or img.get("provider") or "unsplash"
                crud.create_reference_image(
                    db,
                    book_id=book_id,
                    entity_type="cover",
                    entity_id=cover_analysis.id,
                    url=url,
                    thumbnail=img.get("thumbnail"),
                    width=img.get("width"),
                    height=img.get("height"),
                    source=src,
                )
            exclude = set(crud.get_selected_reference_urls(db, "cover", cover_analysis.id))
            crud.trim_reference_images_fifo(db, "cover", cover_analysis.id, exclude_urls=exclude)

    response = {
        "characters": chars_by_name,
        "locations": locs_by_name,
        "artefacts": artefacts_out,
        "cover": cover_out,
        "queries_run": result.get("queries_run", 0),
        "provider_usage": result.get("provider_usage", {}),
    }

    logger.info(
        "Reference search complete for book %s (main_only=%s): "
        "queries_run=%s, provider_usage=%s",
        book_id,
        main_only,
        result.get("queries_run", 0),
        result.get("provider_usage", {}),
    )
    return response


# ---------------------------------------------------------------------------
# Reference results (persisted pool for review-search-result page)
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/reference-results")
def get_reference_results(book_id: int, db: Session = Depends(get_db)):
    """
    Return accumulated reference images per entity from reference_images table.
    Format: { characters: { entityName: images[] }, locations: { entityName: images[] } }
    Each image: { url, thumbnail, width, height, source } (source: unsplash | serpapi | user).
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)

    chars_out: dict[str, list] = {}
    for c in characters:
        rows = crud.get_reference_images_for_entity(db, "character", c.id)
        chars_out[c.name] = [
            {
                "url": r.url,
                "thumbnail": r.thumbnail or r.url,
                "width": r.width,
                "height": r.height,
                "source": r.source,
            }
            for r in rows
        ]

    locs_out: dict[str, list] = {}
    for loc in locations:
        rows = crud.get_reference_images_for_entity(db, "location", loc.id)
        locs_out[loc.name] = [
            {
                "url": r.url,
                "thumbnail": r.thumbnail or r.url,
                "width": r.width,
                "height": r.height,
                "source": r.source,
            }
            for r in rows
        ]

    artefacts = crud.get_artefacts_by_book(db, book_id)
    artefacts_out: dict[str, list] = {}
    for a in artefacts:
        rows = crud.get_reference_images_for_entity(db, "artefact", a.id)
        artefacts_out[a.name] = [
            {
                "url": r.url,
                "thumbnail": r.thumbnail or r.url,
                "width": r.width,
                "height": r.height,
                "source": r.source,
            }
            for r in rows
        ]

    cover_out: dict[str, list] = {}
    cover_analysis = crud.get_cover_analysis(db, book_id)
    cover_rows: list = []
    if cover_analysis:
        cover_rows = crud.get_reference_images_for_entity(db, "cover", cover_analysis.id)
        cover_out["cover"] = [
            {
                "url": r.url,
                "thumbnail": r.thumbnail or r.url,
                "width": r.width,
                "height": r.height,
                "source": r.source,
            }
            for r in cover_rows
        ]

    # Return cover first so it is not dropped if response is truncated (e.g. large payload)
    return {"cover": cover_out, "characters": chars_out, "locations": locs_out, "artefacts": artefacts_out}


# ---------------------------------------------------------------------------
# Approve visual bible
# ---------------------------------------------------------------------------

@router.post("/books/{book_id}/visual-bible/approve", response_model=StatusResponse)
def approve_visual_bible(
    book_id: int,
    req: VisualBibleApproveRequest,
    db: Session = Depends(get_db),
):
    """
    Approve the visual bible with user-selected reference images (multiple per entity).
    Saves selected_reference_urls JSON and reference_image_url (first) per entity.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    vb = crud.get_visual_bible(db, book_id)
    if not vb:
        raise HTTPException(status_code=404, detail="Visual bible not found")

    selected_char_ids = set()
    for char_id_str, urls in req.character_selections.items():
        cid = int(char_id_str)
        selected_char_ids.add(cid)
        url_list = urls if isinstance(urls, list) else ([urls] if urls else [])
        first_url = url_list[0] if url_list else CHARACTER_PLACEHOLDER
        crud.update_character(
            db,
            cid,
            reference_image_url=first_url,
            selected_reference_urls=json.dumps(url_list) if url_list else None,
        )

    selected_loc_ids = set()
    for loc_id_str, urls in req.location_selections.items():
        lid = int(loc_id_str)
        selected_loc_ids.add(lid)
        url_list = urls if isinstance(urls, list) else ([urls] if urls else [])
        first_url = url_list[0] if url_list else LOCATION_PLACEHOLDER
        crud.update_location(
            db,
            lid,
            reference_image_url=first_url,
            selected_reference_urls=json.dumps(url_list) if url_list else None,
        )

    for artefact_id_str, urls in req.artefact_selections.items():
        aid = int(artefact_id_str)
        url_list = urls if isinstance(urls, list) else ([urls] if urls else [])
        first_url = url_list[0] if url_list else None
        crud.update_artefact(
            db,
            aid,
            reference_image_url=first_url,
            selected_reference_urls=json.dumps(url_list) if url_list else None,
        )

    # cover_selections accepted; no DB column for cover selected URLs yet

    all_char_ids = {c.id for c in crud.get_characters_by_book(db, book_id)}
    all_loc_ids = {loc.id for loc in crud.get_locations_by_book(db, book_id)}
    for cid in all_char_ids:
        if cid not in selected_char_ids:
            crud.update_character(
                db, cid,
                reference_image_url=CHARACTER_PLACEHOLDER,
                selected_reference_urls=None,
            )
    for lid in all_loc_ids:
        if lid not in selected_loc_ids:
            crud.update_location(
                db, lid,
                reference_image_url=LOCATION_PLACEHOLDER,
                selected_reference_urls=None,
            )

    crud.approve_visual_bible(db, book_id)
    logger.info("Visual bible approved for book %s", book_id)
    return StatusResponse(status="approved", message="Visual bible locked for generation")


# ---------------------------------------------------------------------------
# User reference upload
# ---------------------------------------------------------------------------

ALLOWED_REFERENCE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@router.post("/books/{book_id}/reference-upload")
def reference_upload(
    book_id: int,
    entity_type: str = Form(...),
    entity_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a user reference image for an entity. Saves to static/reference_uploads
    and inserts into reference_images with source=user.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if entity_type not in ("character", "location", "artefact", "cover"):
        raise HTTPException(status_code=400, detail="entity_type must be character, location, artefact, or cover")

    if entity_type == "character":
        ent = crud.get_characters_by_book(db, book_id)
        ent = next((c for c in ent if c.id == entity_id), None)
    elif entity_type == "location":
        ent = crud.get_locations_by_book(db, book_id)
        ent = next((l for l in ent if l.id == entity_id), None)
    elif entity_type == "artefact":
        ent = crud.get_artefact(db, entity_id)
        if ent and ent.book_id != book_id:
            ent = None
    else:
        # cover: entity_id must be the book's cover_analysis id
        cover_analysis = crud.get_cover_analysis(db, book_id)
        ent = cover_analysis if (cover_analysis and cover_analysis.id == entity_id) else None
    if not ent:
        raise HTTPException(status_code=404, detail="Entity not found for this book")

    ext = os.path.splitext((file.filename or "").lower())[1]
    if ext not in ALLOWED_REFERENCE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Allowed types: jpeg, png, webp",
        )

    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
    upload_dir = os.path.join(static_dir, "reference_uploads", str(book_id), entity_type)
    os.makedirs(upload_dir, exist_ok=True)
    safe_name = f"{entity_id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(upload_dir, safe_name)
    try:
        contents = file.file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
    except Exception as e:
        logger.exception("Reference upload write failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save file")

    url = f"/static/reference_uploads/{book_id}/{entity_type}/{safe_name}"
    rec = crud.create_reference_image(
        db,
        book_id=book_id,
        entity_type=entity_type,
        entity_id=entity_id,
        url=url,
        thumbnail=url,
        width=None,
        height=None,
        source="user",
    )
    exclude = set(crud.get_selected_reference_urls(db, entity_type, entity_id))
    crud.trim_reference_images_fifo(db, entity_type, entity_id, exclude_urls=exclude)

    return {
        "url": url,
        "thumbnail": url,
        "source": "user",
        "id": rec.id,
    }


# ---------------------------------------------------------------------------
# Engine ratings
# ---------------------------------------------------------------------------

@router.get("/books/{book_id}/cover-analysis", response_model=CoverAnalysisResponse)
def get_cover_analysis(book_id: int, db: Session = Depends(get_db)):
    """Get cover analysis for a book. 404 if not yet run."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    cover = crud.get_cover_analysis(db, book_id)
    if not cover:
        raise HTTPException(status_code=404, detail="Cover analysis not found. Run analysis first.")
    return cover


@router.patch("/books/{book_id}/cover-analysis", response_model=CoverAnalysisResponse)
def patch_cover_analysis(
    book_id: int,
    body: CoverAnalysisUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update cover analysis (user edits). All fields optional."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    cover = crud.get_cover_analysis(db, book_id)
    if not cover:
        raise HTTPException(status_code=404, detail="Cover analysis not found. Run analysis first.")
    updates = body.model_dump(exclude_unset=True)
    if updates:
        crud.create_or_update_cover_analysis(db, book_id, **updates)
    updated = crud.get_cover_analysis(db, book_id)
    return updated


@router.patch("/books/{book_id}/engine-ratings", response_model=StatusResponse)
def update_engine_rating(
    book_id: int,
    req: EngineRatingUpdate,
    db: Session = Depends(get_db),
):
    """
    Update like/dislike count for a search provider for this book.
    Upserts: creates the row if it doesn't exist.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    delta_likes = 1 if req.action == "like" else 0
    delta_dislikes = 1 if req.action == "dislike" else 0
    crud.update_engine_rating(
        db, book_id, req.provider,
        delta_likes=delta_likes,
        delta_dislikes=delta_dislikes,
    )
    return StatusResponse(status="ok", message=f"{req.action} recorded for {req.provider}")


@router.get("/books/{book_id}/engine-ratings", response_model=list[EngineRatingResponse])
def get_engine_ratings(book_id: int, db: Session = Depends(get_db)):
    """Get all engine rating rows for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    rows = crud.get_engine_ratings_list(db, book_id)
    return [
        EngineRatingResponse(
            provider=r.provider,
            likes=r.likes or 0,
            dislikes=r.dislikes or 0,
            net_score=r.net_score,
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Visual Bible Entries (per-entity T2I images)
# ---------------------------------------------------------------------------

def get_vb_angles(entity_type: str, visual_bible_depth: int, is_main: bool) -> list[str]:
    """Return angle labels for this entity type and depth. is_main increases depth."""
    CHARACTER_ANGLES = ["front", "3/4 left", "3/4 right", "profile", "action pose", "close-up face"]
    LOCATION_ANGLES = ["exterior wide", "interior", "atmospheric detail", "establishing shot"]
    ARTEFACT_ANGLES = ["front", "back", "detail/open", "in-use context"]
    depth = visual_bible_depth or (6 if is_main else 3)
    if entity_type == "character":
        return CHARACTER_ANGLES[:depth]
    if entity_type == "location":
        return LOCATION_ANGLES[: min(depth, 4)]
    if entity_type == "artefact":
        return ARTEFACT_ANGLES[: min(depth, 4)]
    return []


async def _run_vb_entry_t2i(entry_id: int, prompt: str, book_id: int) -> None:
    """Background: call T2I stub and update entry (Phase 9 wires real provider)."""
    from app.database import SessionLocal
    from app.services.t2i_providers import ALL_T2I_PROVIDERS
    from app.services.t2i_providers.base import T2IRequest

    db = SessionLocal()
    try:
        provider = ALL_T2I_PROVIDERS.get("abstract")
        if not provider:
            db.close()
            return
        req = T2IRequest(prompt=prompt or "Visual bible entry", negative_prompt="")
        result = await provider.generate(req)
        crud.update_visual_bible_entry(db, entry_id, status="complete", prompt_used=prompt)
        if result.image_path:
            crud.update_visual_bible_entry(db, entry_id, image_path=result.image_path)
    except Exception as e:
        logger.exception("VB entry T2I failed for entry_id=%s: %s", entry_id, e)
        crud.update_visual_bible_entry(db, entry_id, status="failed")
    finally:
        db.close()


@router.get("/books/{book_id}/visual-bible/entries", response_model=list[VisualBibleEntryResponse])
def get_visual_bible_entries(
    book_id: int,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """List VB entries, optionally filtered by entity_type and/or entity_id."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    entries = crud.get_visual_bible_entries(db, book_id, entity_type=entity_type, entity_id=entity_id)
    return [VisualBibleEntryResponse.model_validate(e) for e in entries]


@router.post(
    "/books/{book_id}/visual-bible/entries/generate",
    response_model=VisualBibleEntryResponse,
    status_code=202,
)
async def generate_visual_bible_entry(
    book_id: int,
    body: VisualBibleEntryGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Create one VB entry with status=pending and queue T2I (stub)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    entry = crud.create_visual_bible_entry(
        db,
        book_id=book_id,
        entity_type=body.entity_type,
        entity_id=body.entity_id,
        angle_label=body.angle_label,
        prompt_used=body.prompt,
    )
    background_tasks.add_task(_run_vb_entry_t2i, entry.id, body.prompt or "", book_id)
    return VisualBibleEntryResponse.model_validate(entry)


@router.post("/books/{book_id}/visual-bible/entries/generate-all")
async def generate_all_visual_bible_entries(
    book_id: int,
    background_tasks: BackgroundTasks,
    body: Optional[VisualBibleEntryGenerateAllRequest] = None,
    db: Session = Depends(get_db),
):
    """Queue VB entries for all (or filtered) entities; returns queued count and entries."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    entity_type_filter = (body and body.entity_type) or None
    entries_created: list = []
    characters = crud.get_characters_by_book(db, book_id) if entity_type_filter in (None, "character") else []
    locations = crud.get_locations_by_book(db, book_id) if entity_type_filter in (None, "location") else []
    artefacts = crud.get_artefacts_by_book(db, book_id) if entity_type_filter in (None, "artefact") else []
    for c in characters:
        angles = get_vb_angles("character", getattr(c, "visual_bible_depth", None) or 0, bool(getattr(c, "is_main", 0)))
        for angle in angles:
            entry = crud.create_visual_bible_entry(db, book_id, "character", c.id, angle_label=angle)
            entries_created.append(entry)
            background_tasks.add_task(_run_vb_entry_t2i, entry.id, None, book_id)
    for loc in locations:
        angles = get_vb_angles("location", getattr(loc, "visual_bible_depth", None) or 0, bool(getattr(loc, "is_main", 0)))
        for angle in angles:
            entry = crud.create_visual_bible_entry(db, book_id, "location", loc.id, angle_label=angle)
            entries_created.append(entry)
            background_tasks.add_task(_run_vb_entry_t2i, entry.id, None, book_id)
    for a in artefacts:
        angles = get_vb_angles("artefact", getattr(a, "visual_bible_depth", None) or 0, bool(getattr(a, "is_main", 0)))
        for angle in angles:
            entry = crud.create_visual_bible_entry(db, book_id, "artefact", a.id, angle_label=angle)
            entries_created.append(entry)
            background_tasks.add_task(_run_vb_entry_t2i, entry.id, None, book_id)
    return {"queued": len(entries_created), "entries": [VisualBibleEntryResponse.model_validate(e) for e in entries_created]}


@router.patch("/books/{book_id}/visual-bible/entries/{entry_id}", response_model=VisualBibleEntryResponse)
def patch_visual_bible_entry(
    book_id: int,
    entry_id: int,
    body: VisualBibleEntryPatchRequest,
    db: Session = Depends(get_db),
):
    """Update is_approved, image_path, or status of a VB entry."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    entry = db.query(VisualBibleEntry).filter(
        VisualBibleEntry.id == entry_id,
        VisualBibleEntry.book_id == book_id,
    ).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Visual bible entry not found")
    updates = {k: v for k, v in body.model_dump(exclude_unset=True).items() if v is not None}
    if updates:
        crud.update_visual_bible_entry(db, entry_id, **updates)
        db.refresh(entry)
    entry = db.query(VisualBibleEntry).filter(VisualBibleEntry.id == entry_id).first()
    return VisualBibleEntryResponse.model_validate(entry)
