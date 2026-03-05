"""Illustration and cover concept API endpoints."""
import json as _json
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.schemas import (
    CoverConceptResponse,
    CoverConceptGenerateRequest,
    CoverConceptPatchRequest,
    StatusResponse,
)
from app import crud
from app.services.cover_prompt_assembler import CoverPromptAssembler

logger = logging.getLogger(__name__)

router = APIRouter()


def _entity_to_merge_dict(entity, entity_type: str) -> dict:
    """Build entity dict for run_prompt_merge from Character/Location/Artefact model."""
    tokens = {}
    if getattr(entity, "entity_visual_tokens_json", None):
        try:
            tokens = _json.loads(entity.entity_visual_tokens_json) or {}
        except (TypeError, ValueError):
            pass
    ontology = {}
    if getattr(entity, "ontology_json", None):
        try:
            ontology = _json.loads(entity.ontology_json) or {}
        except (TypeError, ValueError):
            pass
    return {
        "name": getattr(entity, "name", "unnamed"),
        "entity_class": ontology.get("entity_class", "human" if entity_type == "character" else "other_artefact"),
        "visual_type": getattr(entity, "visual_type", "") or "",
        "core_tokens": tokens.get("core_tokens") or [],
        "style_tokens": tokens.get("style_tokens") or [],
        "archetype_tokens": tokens.get("archetype_tokens") or [],
        "anti_tokens": tokens.get("anti_tokens") or [],
    }


def _get_primary_entity_tokens(db, cover_analysis) -> list:
    """Extract primary entity visual tokens for CoverPromptAssembler fallback."""
    entity = _resolve_primary_entity(db, cover_analysis)
    if not entity:
        return []
    entity_type, _ = _primary_entity_type_and_id(cover_analysis)
    tokens = {}
    if getattr(entity, "entity_visual_tokens_json", None):
        try:
            tokens = _json.loads(entity.entity_visual_tokens_json) or {}
        except (TypeError, ValueError):
            pass
    return list(tokens.get("core_tokens") or [])


def _primary_entity_type_and_id(cover_analysis):
    """Return (entity_type, entity_id) for primary cover entity or (None, None)."""
    if getattr(cover_analysis, "primary_cover_character_id", None):
        return "character", cover_analysis.primary_cover_character_id
    if getattr(cover_analysis, "primary_cover_location_id", None):
        return "location", cover_analysis.primary_cover_location_id
    if getattr(cover_analysis, "primary_cover_artefact_id", None):
        return "artefact", cover_analysis.primary_cover_artefact_id
    return None, None


def _resolve_primary_entity(db, cover_analysis):
    """Get Character, Location, or Artefact for primary cover entity."""
    entity_type, entity_id = _primary_entity_type_and_id(cover_analysis)
    if not entity_type or not entity_id:
        return None
    if entity_type == "character":
        return crud.get_character(db, entity_id)
    if entity_type == "location":
        return crud.get_location(db, entity_id)
    if entity_type == "artefact":
        return crud.get_artefact(db, entity_id)
    return None


def _get_entity_reference_url(db, cover_analysis) -> Optional[str]:
    """First reference image URL for primary entity (for FLUX Kontext conditioning)."""
    entity_type, entity_id = _primary_entity_type_and_id(cover_analysis)
    if not entity_type or not entity_id:
        return None
    rows = crud.get_reference_images_for_entity(db, entity_type, entity_id)
    if not rows:
        return None
    return getattr(rows[0], "url", None)


async def _generate_concept_background(
    book_id: int,
    concept_id: int,
    body: CoverConceptGenerateRequest,
) -> None:
    """
    Background: run full cover generation pipeline for one concept.
    Uses PromptEngineeringService when style_template exists, else CoverPromptAssembler.
    """
    from app.services.prompt_engineering_service import run_prompt_merge
    from app.services.engine_selector import get_cover_t2i_provider

    db = SessionLocal()
    try:
        cover_analysis = crud.get_cover_analysis(db, book_id)
        if not cover_analysis:
            crud.update_cover_concept(db, concept_id, status="failed")
            return
        book = crud.get_book(db, book_id)
        primary_entity = _resolve_primary_entity(db, cover_analysis)
        style_template = getattr(cover_analysis, "reference_style_template", None) or ""

        if style_template.strip() and primary_entity:
            entity_type, _ = _primary_entity_type_and_id(cover_analysis)
            entity_dict = _entity_to_merge_dict(primary_entity, entity_type or "character")
            user_instruction = (body.user_instruction or "").strip() or "Replace the main subject with this entity."
            pe_result = await run_prompt_merge(
                style_template=style_template,
                entity=entity_dict,
                user_instruction=user_instruction,
            )
            final_prompt = pe_result.final_prompt
            negative_prompt = pe_result.negative_prompt or ""
        else:
            assembler = CoverPromptAssembler()
            genre = (book.genre or "fantasy") if book else "fantasy"
            cover_type = getattr(cover_analysis, "cover_type", None) or "illustrated"
            primary_tokens = _get_primary_entity_tokens(db, cover_analysis)
            asm_result = assembler.assemble(genre=genre, cover_type=cover_type, primary_entity_tokens=primary_tokens)
            final_prompt = asm_result.prompt
            negative_prompt = asm_result.negative_prompt

        ref_image_url = _get_entity_reference_url(db, cover_analysis)
        provider = get_cover_t2i_provider()
        try:
            gen_result = await provider.generate(
                prompt=final_prompt,
                image_url=ref_image_url,
                negative_prompt=negative_prompt or None,
            )
            crud.update_cover_concept(
                db,
                concept_id,
                image_path=gen_result.url,
                prompt_used=final_prompt,
                negative_prompt=negative_prompt,
                status="complete",
            )
        except Exception as exc:
            logger.exception("Cover generation failed for concept %s: %s", concept_id, exc)
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
    """
    Create concept_count cover concepts (status=generating) and queue real T2I pipeline per concept.
    Pipeline: PromptEngineeringService when style_template exists, else CoverPromptAssembler; then get_cover_t2i_provider().generate().
    """
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    req = body or CoverConceptGenerateRequest()
    concept_count = max(1, min(10, req.concept_count or 3))
    existing = crud.get_cover_concepts(db, book_id)
    next_index = max([c.concept_index for c in existing], default=0) + 1
    concepts_created = []
    for i in range(concept_count):
        c = crud.create_cover_concept(
            db,
            book_id=book_id,
            concept_index=next_index + i,
            prompt_used=None,
            negative_prompt=None,
            style_variant=req.style_variant,
        )
        crud.update_cover_concept(db, c.id, status="generating")
        c = crud.get_cover_concept(db, c.id)
        concepts_created.append(c)
        background_tasks.add_task(_generate_concept_background, book_id, c.id, req)
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
