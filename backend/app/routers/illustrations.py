"""Illustration and cover concept API endpoints."""
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CoverConceptResponse,
    CoverConceptGenerateRequest,
    CoverConceptPatchRequest,
    StatusResponse,
)
from app import crud
from app.services.t2i_providers import ALL_T2I_PROVIDERS
from app.services.t2i_providers.base import T2IRequest

logger = logging.getLogger(__name__)

router = APIRouter()


async def _run_cover_concept_t2i(concept_id: int, prompt: str, negative_prompt: str) -> None:
    """Background: call T2I stub for one cover concept (Phase 9 wires real provider)."""
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        provider = ALL_T2I_PROVIDERS.get("abstract")
        if not provider:
            return
        req = T2IRequest(prompt=prompt or "Cover concept", negative_prompt=negative_prompt or "")
        result = await provider.generate(req)
        crud.update_cover_concept(db, concept_id, status="complete", prompt_used=prompt)
        if result.image_path:
            crud.update_cover_concept(db, concept_id, image_path=result.image_path)
    except Exception as e:
        logger.exception("Cover concept T2I failed for concept_id=%s: %s", concept_id, e)
        crud.update_cover_concept(db, concept_id, status="failed")
    finally:
        db.close()


@router.get("/books/{book_id}/cover-concepts", response_model=list[CoverConceptResponse])
def get_cover_concepts(book_id: int, db: Session = Depends(get_db)):
    """List all cover concepts for a book."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    concepts = crud.get_cover_concepts(db, book_id)
    return [CoverConceptResponse.model_validate(c) for c in concepts]


@router.post("/books/{book_id}/cover-concepts/generate")
async def generate_cover_concepts(
    book_id: int,
    background_tasks: BackgroundTasks,
    body: Optional[CoverConceptGenerateRequest] = None,
    db: Session = Depends(get_db),
):
    """Create concept_count cover concepts (status=pending) and queue T2I stub per concept."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    req = body or CoverConceptGenerateRequest()
    concept_count = max(1, min(10, req.concept_count or 3))
    default_prompt = None
    cover_analysis = crud.get_cover_analysis(db, book_id)
    if cover_analysis and getattr(cover_analysis, "cover_t2i_prompt", None):
        default_prompt = cover_analysis.cover_t2i_prompt
    prompt = req.prompt if req.prompt is not None and req.prompt != "" else default_prompt or "Book cover concept"
    negative_prompt = req.negative_prompt or (cover_analysis.cover_negative_prompt if cover_analysis else "") or ""
    style_variant = req.style_variant
    existing = crud.get_cover_concepts(db, book_id)
    next_index = max([c.concept_index for c in existing], default=0) + 1
    concepts_created = []
    for i in range(concept_count):
        c = crud.create_cover_concept(
            db,
            book_id=book_id,
            concept_index=next_index + i,
            prompt_used=prompt,
            negative_prompt=negative_prompt,
            style_variant=style_variant,
        )
        concepts_created.append(c)
        background_tasks.add_task(_run_cover_concept_t2i, c.id, prompt, negative_prompt)
    return {
        "queued": len(concepts_created),
        "concepts": [CoverConceptResponse.model_validate(c) for c in concepts_created],
    }


@router.patch("/books/{book_id}/cover-concepts/{concept_id}", response_model=CoverConceptResponse)
def patch_cover_concept(
    book_id: int,
    concept_id: int,
    body: CoverConceptPatchRequest,
    db: Session = Depends(get_db),
):
    """Update is_selected, prompt_used, or style_variant of a cover concept."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    concept = crud.get_cover_concept(db, concept_id)
    if not concept or concept.book_id != book_id:
        raise HTTPException(status_code=404, detail="Cover concept not found")
    updates = body.model_dump(exclude_unset=True)
    if updates:
        crud.update_cover_concept(db, concept_id, **updates)
        concept = crud.get_cover_concept(db, concept_id)
    return CoverConceptResponse.model_validate(concept)


@router.post("/books/{book_id}/cover-concepts/{concept_id}/select", response_model=StatusResponse)
def select_cover_concept(book_id: int, concept_id: int, db: Session = Depends(get_db)):
    """Set this concept as the selected one (is_selected=1, others=0)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    concept = crud.get_cover_concept(db, concept_id)
    if not concept or concept.book_id != book_id:
        raise HTTPException(status_code=404, detail="Cover concept not found")
    crud.set_selected_cover_concept(db, book_id, concept_id)
    return StatusResponse(status="ok", message="Selected")
