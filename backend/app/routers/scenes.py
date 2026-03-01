"""Scene API endpoints."""
import json as json_lib
import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.schemas import SceneResponse, SceneUpdateRequest, StatusResponse
from app import crud
from app.models import Scene, SceneCharacter, SceneLocation

logger = logging.getLogger(__name__)

router = APIRouter()


def _load_scene_with_relations(db: Session, scene_id: int) -> Optional[Scene]:
    return (
        db.query(Scene)
        .options(
            joinedload(Scene.scene_characters).joinedload(SceneCharacter.character),
            joinedload(Scene.scene_locations).joinedload(SceneLocation.location),
        )
        .filter(Scene.id == scene_id)
        .first()
    )


def _illustration_priority_rank(priority: Optional[str]) -> int:
    """Higher = more important for display order. high=3, medium=2, low=1, unknown=0."""
    if not priority:
        return 0
    p = priority.strip().lower()
    if p == "high":
        return 3
    if p == "medium":
        return 2
    if p == "low":
        return 1
    return 0


def _load_scenes_with_relations(db: Session, book_id: int) -> list[Scene]:
    return (
        db.query(Scene)
        .options(
            joinedload(Scene.scene_characters).joinedload(SceneCharacter.character),
            joinedload(Scene.scene_locations).joinedload(SceneLocation.location),
        )
        .filter(Scene.book_id == book_id)
        .all()
    )


@router.get("/books/{book_id}/scenes", response_model=list[SceneResponse])
def get_scenes(
    book_id: int,
    show_all: bool = False,
    db: Session = Depends(get_db),
):
    """Get scenes for a book. Unless show_all=True, returns top scene_display_count by dramatic importance."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    scenes = _load_scenes_with_relations(db, book_id)
    # Sort by dramatic importance: high priority first, then by visual_intensity desc, then by position in book
    scenes.sort(
        key=lambda s: (
            -_illustration_priority_rank(s.illustration_priority),
            -(s.visual_intensity or 0),
            s.chunk_start_index or 0,
        )
    )
    if not show_all:
        limit = getattr(book, "scene_display_count", None) or 10
        scenes = scenes[:limit]
    return scenes


@router.patch("/books/{book_id}/scenes/{scene_id}", response_model=SceneResponse)
def patch_scene(
    book_id: int,
    scene_id: int,
    req: SceneUpdateRequest,
    db: Session = Depends(get_db),
):
    """Update scene fields: title, scene_prompt_draft, is_selected."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    scene = _load_scene_with_relations(db, scene_id)
    if not scene or scene.book_id != book_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    updates: dict = {}
    if req.title is not None:
        updates["title"] = req.title
    if req.narrative_summary is not None:
        updates["narrative_summary"] = req.narrative_summary
    if req.dramatic_score_avg is not None:
        updates["dramatic_score_avg"] = req.dramatic_score_avg
    if req.scene_prompt_draft is not None:
        updates["scene_prompt_draft"] = req.scene_prompt_draft
    if req.is_selected is not None:
        updates["is_selected"] = 1 if req.is_selected else 0

    if updates:
        crud.update_scene(db, scene_id, **updates)

    return _load_scene_with_relations(db, scene_id)


@router.post(
    "/books/{book_id}/scenes/{scene_id}/generate-illustration",
    response_model=StatusResponse,
    status_code=202,
)
def generate_illustration(
    book_id: int,
    scene_id: int,
    db: Session = Depends(get_db),
):
    """Stub: trigger T2I illustration generation for a scene (future step)."""
    book = crud.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    scene = crud.get_scene(db, scene_id)
    if not scene or scene.book_id != book_id:
        raise HTTPException(status_code=404, detail="Scene not found")

    return StatusResponse(
        status="accepted",
        message="Illustration generation queued (T2I provider not yet configured)",
    )
