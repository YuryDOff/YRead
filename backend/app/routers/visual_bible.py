"""Visual Bible API endpoints."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    VisualBibleResponse,
    VisualBibleApproveRequest,
    CharacterResponse,
    LocationResponse,
    StatusResponse,
)
from app import crud
from app.services.search_service import search_all_references

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

    return {
        "visual_bible": VisualBibleResponse.model_validate(vb).model_dump(),
        "characters": [
            CharacterResponse.model_validate(c).model_dump() for c in characters
        ],
        "locations": [
            LocationResponse.model_validate(loc).model_dump() for loc in locations
        ],
    }


# ---------------------------------------------------------------------------
# Reference image search
# ---------------------------------------------------------------------------

@router.post("/books/{book_id}/search-references")
async def search_references(book_id: int, db: Session = Depends(get_db)):
    """
    Search reference images for all characters and locations of a book.
    Stores first result URL as default reference for each entity.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)

    if not characters and not locations:
        raise HTTPException(
            status_code=400,
            detail="No characters or locations found. Analyze the book first.",
        )

    is_well_known = bool(book.is_well_known)

    char_dicts = [
        {"name": c.name, "physical_description": c.physical_description or ""}
        for c in characters
    ]
    loc_dicts = [
        {"name": loc.name, "visual_description": loc.visual_description or ""}
        for loc in locations
    ]

    results = await search_all_references(
        char_dicts,
        loc_dicts,
        book_title=book.title,
        author=book.author,
        is_well_known=is_well_known,
    )

    # Auto-select first result as default reference (user can change later)
    for char in characters:
        images = results.get("characters", {}).get(char.name, [])
        if images:
            crud.update_character(
                db, char.id, reference_image_url=images[0]["url"]
            )

    for loc in locations:
        images = results.get("locations", {}).get(loc.name, [])
        if images:
            crud.update_location(
                db, loc.id, reference_image_url=images[0]["url"]
            )

    logger.info(
        "Reference search complete for book %s: %d char sets, %d loc sets",
        book_id,
        len(results.get("characters", {})),
        len(results.get("locations", {})),
    )
    return results


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
    Approve the visual bible with user-selected reference images.
    Locks the visual bible for illustration generation.
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    vb = crud.get_visual_bible(db, book_id)
    if not vb:
        raise HTTPException(status_code=404, detail="Visual bible not found")

    # Apply user selections for characters
    for char_id, ref_url in req.character_selections.items():
        crud.update_character(db, int(char_id), reference_image_url=ref_url)

    # Apply user selections for locations
    for loc_id, ref_url in req.location_selections.items():
        crud.update_location(db, int(loc_id), reference_image_url=ref_url)

    # Mark as approved
    crud.approve_visual_bible(db, book_id)

    logger.info("Visual bible approved for book %s", book_id)
    return StatusResponse(status="approved", message="Visual bible locked for generation")
