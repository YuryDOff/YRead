"""CRUD helper functions for database operations."""
import os
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

import json as _json

from app.models import (
    Book,
    Chunk,
    Character,
    Location,
    VisualBible,
    Illustration,
    ChunkCharacter,
    ChunkLocation,
    SearchQuery,
    ReferenceImage,
    Scene,
    SceneCharacter,
    SceneLocation,
    EngineRating,
)


# ---------------------------------------------------------------------------
# Books
# ---------------------------------------------------------------------------

def create_book(
    db: Session,
    *,
    title: str,
    author: Optional[str] = None,
    google_drive_link: Optional[str] = None,
    file_path: Optional[str] = None,
    total_words: Optional[int] = None,
    total_pages: Optional[int] = None,
    is_well_known: bool = False,
) -> Book:
    book = Book(
        title=title,
        author=author,
        google_drive_link=google_drive_link,
        file_path=file_path,
        total_words=total_words,
        total_pages=total_pages,
        is_well_known=1 if is_well_known else 0,
        status="imported",
    )
    db.add(book)
    db.commit()
    db.refresh(book)
    return book


def get_book(db: Session, book_id: int) -> Optional[Book]:
    return db.query(Book).filter(Book.id == book_id).first()


def get_book_with_relations(db: Session, book_id: int) -> Optional[Book]:
    return (
        db.query(Book)
        .options(
            joinedload(Book.characters),
            joinedload(Book.locations),
            joinedload(Book.visual_bible),
        )
        .filter(Book.id == book_id)
        .first()
    )


def get_books(db: Session, skip: int = 0, limit: int = 100) -> list[Book]:
    return db.query(Book).offset(skip).limit(limit).all()


def update_book_status(db: Session, book_id: int, status: str) -> Optional[Book]:
    book = get_book(db, book_id)
    if book:
        book.status = status
        book.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(book)
    return book


def update_book(db: Session, book_id: int, **kwargs) -> Optional[Book]:
    book = get_book(db, book_id)
    if book:
        for key, value in kwargs.items():
            if hasattr(book, key):
                setattr(book, key, value)
        book.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(book)
    return book


def delete_book(db: Session, book_id: int) -> bool:
    book = get_book(db, book_id)
    if not book:
        return False

    # Remove generated illustration files from disk before cascade deletes the rows
    illustrations = (
        db.query(Illustration)
        .filter(Illustration.book_id == book_id)
        .all()
    )
    for illus in illustrations:
        if illus.image_path:
            try:
                if os.path.isfile(illus.image_path):
                    os.remove(illus.image_path)
            except OSError:
                pass  # best-effort cleanup

    # ReferenceImage has book_id but no relationship on Book — delete explicitly
    db.query(ReferenceImage).filter(ReferenceImage.book_id == book_id).delete(
        synchronize_session="fetch"
    )
    # Orphan cleanup: rows whose book_id no longer exists (e.g. from before this fix)
    existing_book_ids = [r[0] for r in db.query(Book.id).all()]
    if existing_book_ids:
        db.query(ReferenceImage).filter(
            ReferenceImage.book_id.notin_(existing_book_ids)
        ).delete(synchronize_session="fetch")
    else:
        db.query(ReferenceImage).delete(synchronize_session="fetch")

    db.delete(book)
    db.commit()
    return True


def clear_analysis_results(db: Session, book_id: int) -> None:
    """
    Remove all analysis artefacts for a book so that re-analysis starts fresh.

    Deletes: chunk_characters, chunk_locations, characters, locations,
    visual_bible, illustrations.  Resets dramatic_score on chunks to NULL.
    The book record and its chunks are preserved.
    """
    # 1. Delete junction rows (must go first due to FK constraints)
    chunk_ids = [
        c.id for c in db.query(Chunk.id).filter(Chunk.book_id == book_id).all()
    ]
    if chunk_ids:
        db.query(ChunkCharacter).filter(
            ChunkCharacter.chunk_id.in_(chunk_ids)
        ).delete(synchronize_session="fetch")
        db.query(ChunkLocation).filter(
            ChunkLocation.chunk_id.in_(chunk_ids)
        ).delete(synchronize_session="fetch")

    # 2. Delete characters & locations
    db.query(Character).filter(Character.book_id == book_id).delete(
        synchronize_session="fetch"
    )
    db.query(Location).filter(Location.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 3. Delete visual bible
    db.query(VisualBible).filter(VisualBible.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 4. Delete illustrations
    db.query(Illustration).filter(Illustration.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 5. Delete search query logs
    db.query(SearchQuery).filter(SearchQuery.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 5a. Reference images (per book; no relationship on Book)
    db.query(ReferenceImage).filter(ReferenceImage.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 5b. Delete scenes (cascade deletes SceneCharacter + SceneLocation via relationship)
    db.query(Scene).filter(Scene.book_id == book_id).delete(
        synchronize_session="fetch"
    )

    # 6. Reset dramatic scores on chunks
    if chunk_ids:
        db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).update(
            {"dramatic_score": None}, synchronize_session="fetch"
        )

    db.commit()


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

def create_chunks_batch(db: Session, book_id: int, chunks_data: list[dict]) -> list[Chunk]:
    """Insert multiple chunks in a single transaction."""
    chunks = []
    for data in chunks_data:
        chunk = Chunk(
            book_id=book_id,
            chunk_index=data["chunk_index"],
            text=data["text"],
            start_page=data.get("start_page"),
            end_page=data.get("end_page"),
            word_count=data.get("word_count"),
            dramatic_score=data.get("dramatic_score"),
        )
        db.add(chunk)
        chunks.append(chunk)
    db.commit()
    for c in chunks:
        db.refresh(c)
    return chunks


def get_chunks_by_book(db: Session, book_id: int) -> list[Chunk]:
    return (
        db.query(Chunk)
        .filter(Chunk.book_id == book_id)
        .order_by(Chunk.chunk_index)
        .all()
    )


def get_chunk(db: Session, chunk_id: int) -> Optional[Chunk]:
    return db.query(Chunk).filter(Chunk.id == chunk_id).first()


def update_chunk_dramatic_score(
    db: Session, chunk_id: int, dramatic_score: float
) -> Optional[Chunk]:
    chunk = get_chunk(db, chunk_id)
    if chunk:
        chunk.dramatic_score = dramatic_score
        db.commit()
        db.refresh(chunk)
    return chunk


def update_chunk_visual_analysis(
    db: Session, chunk_id: int, data: dict
) -> Optional[Chunk]:
    """Save visual_layers and visual_tokens from chunk_analyses to chunk."""
    import json
    chunk = get_chunk(db, chunk_id)
    if chunk:
        chunk.visual_analysis_json = json.dumps(data)
        db.commit()
        db.refresh(chunk)
    return chunk


def get_chunk_visual_analysis(db: Session, chunk_id: int) -> Optional[dict]:
    """Load visual_analysis_json from chunk. Returns None if empty or invalid."""
    import json
    chunk = get_chunk(db, chunk_id)
    if not chunk or not chunk.visual_analysis_json:
        return None
    try:
        return json.loads(chunk.visual_analysis_json)
    except (json.JSONDecodeError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

def create_character(
    db: Session,
    *,
    book_id: int,
    name: str,
    physical_description: Optional[str] = None,
    personality_traits: Optional[str] = None,
    typical_emotions: Optional[str] = None,
    reference_image_url: Optional[str] = None,
    is_main: bool = False,
    visual_type: Optional[str] = None,
    is_well_known_entity: bool = False,
    canonical_search_name: Optional[str] = None,
    search_visual_analog: Optional[str] = None,
) -> Character:
    char = Character(
        book_id=book_id,
        name=name,
        physical_description=physical_description,
        personality_traits=personality_traits,
        typical_emotions=typical_emotions,
        reference_image_url=reference_image_url,
        is_main=1 if is_main else 0,
        visual_type=visual_type,
        is_well_known_entity=1 if is_well_known_entity else 0,
        canonical_search_name=canonical_search_name,
        search_visual_analog=search_visual_analog,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return char


def get_characters_by_book(db: Session, book_id: int) -> list[Character]:
    return db.query(Character).filter(Character.book_id == book_id).all()


def update_character(db: Session, character_id: int, **kwargs) -> Optional[Character]:
    char = db.query(Character).filter(Character.id == character_id).first()
    if char:
        for key, value in kwargs.items():
            if hasattr(char, key):
                setattr(char, key, value)
        db.commit()
        db.refresh(char)
    return char


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

def create_location(
    db: Session,
    *,
    book_id: int,
    name: str,
    visual_description: Optional[str] = None,
    atmosphere: Optional[str] = None,
    reference_image_url: Optional[str] = None,
    is_main: bool = False,
    is_well_known_entity: bool = False,
    canonical_search_name: Optional[str] = None,
    search_visual_analog: Optional[str] = None,
) -> Location:
    loc = Location(
        book_id=book_id,
        name=name,
        visual_description=visual_description,
        atmosphere=atmosphere,
        reference_image_url=reference_image_url,
        is_main=1 if is_main else 0,
        is_well_known_entity=1 if is_well_known_entity else 0,
        canonical_search_name=canonical_search_name,
        search_visual_analog=search_visual_analog,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


def get_locations_by_book(db: Session, book_id: int) -> list[Location]:
    return db.query(Location).filter(Location.book_id == book_id).all()


def update_location(db: Session, location_id: int, **kwargs) -> Optional[Location]:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if loc:
        for key, value in kwargs.items():
            if hasattr(loc, key):
                setattr(loc, key, value)
        db.commit()
        db.refresh(loc)
    return loc


# ---------------------------------------------------------------------------
# Visual Bible
# ---------------------------------------------------------------------------

def create_visual_bible(
    db: Session,
    *,
    book_id: int,
    style_category: Optional[str] = None,
    tone_description: Optional[str] = None,
    illustration_frequency: Optional[int] = None,
    layout_style: Optional[str] = None,
) -> VisualBible:
    vb = VisualBible(
        book_id=book_id,
        style_category=style_category,
        tone_description=tone_description,
        illustration_frequency=illustration_frequency,
        layout_style=layout_style,
    )
    db.add(vb)
    db.commit()
    db.refresh(vb)
    return vb


def get_visual_bible(db: Session, book_id: int) -> Optional[VisualBible]:
    return db.query(VisualBible).filter(VisualBible.book_id == book_id).first()


def approve_visual_bible(db: Session, book_id: int) -> Optional[VisualBible]:
    vb = get_visual_bible(db, book_id)
    if vb:
        vb.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(vb)
    return vb


# ---------------------------------------------------------------------------
# Illustrations
# ---------------------------------------------------------------------------

def create_illustration(
    db: Session,
    *,
    book_id: int,
    chunk_id: Optional[int] = None,
    page_number: Optional[int] = None,
    prompt: Optional[str] = None,
    style: Optional[str] = None,
    reference_images: Optional[str] = None,
) -> Illustration:
    illus = Illustration(
        book_id=book_id,
        chunk_id=chunk_id,
        page_number=page_number,
        prompt=prompt,
        style=style,
        reference_images=reference_images,
        status="pending",
    )
    db.add(illus)
    db.commit()
    db.refresh(illus)
    return illus


def get_illustrations_by_book(db: Session, book_id: int) -> list[Illustration]:
    return (
        db.query(Illustration)
        .filter(Illustration.book_id == book_id)
        .order_by(Illustration.page_number)
        .all()
    )


def update_illustration_status(
    db: Session,
    illustration_id: int,
    status: str,
    image_path: Optional[str] = None,
) -> Optional[Illustration]:
    illus = db.query(Illustration).filter(Illustration.id == illustration_id).first()
    if illus:
        illus.status = status
        if image_path:
            illus.image_path = image_path
        db.commit()
        db.refresh(illus)
    return illus


# ---------------------------------------------------------------------------
# Junction tables: Chunk ↔ Character / Location
# ---------------------------------------------------------------------------

def link_chunk_characters(
    db: Session, chunk_id: int, character_ids: list[int], commit: bool = True
) -> None:
    """Create chunk-character links (skip duplicates)."""
    for cid in character_ids:
        exists = (
            db.query(ChunkCharacter)
            .filter(
                ChunkCharacter.chunk_id == chunk_id,
                ChunkCharacter.character_id == cid,
            )
            .first()
        )
        if not exists:
            db.add(ChunkCharacter(chunk_id=chunk_id, character_id=cid))
    if commit:
        db.commit()


def link_chunk_locations(
    db: Session, chunk_id: int, location_ids: list[int], commit: bool = True
) -> None:
    """Create chunk-location links (skip duplicates)."""
    for lid in location_ids:
        exists = (
            db.query(ChunkLocation)
            .filter(
                ChunkLocation.chunk_id == chunk_id,
                ChunkLocation.location_id == lid,
            )
            .first()
        )
        if not exists:
            db.add(ChunkLocation(chunk_id=chunk_id, location_id=lid))
    if commit:
        db.commit()


def get_chunks_for_character(db: Session, character_id: int) -> list[Chunk]:
    """Get all chunks where a specific character appears."""
    return (
        db.query(Chunk)
        .join(ChunkCharacter)
        .filter(ChunkCharacter.character_id == character_id)
        .order_by(Chunk.chunk_index)
        .all()
    )


def get_chunks_for_location(db: Session, location_id: int) -> list[Chunk]:
    """Get all chunks where a specific location appears."""
    return (
        db.query(Chunk)
        .join(ChunkLocation)
        .filter(ChunkLocation.location_id == location_id)
        .order_by(Chunk.chunk_index)
        .all()
    )


# ---------------------------------------------------------------------------
# Search Queries
# ---------------------------------------------------------------------------

def create_search_query(
    db: Session,
    *,
    book_id: int,
    entity_type: str,
    entity_name: str,
    query_text: str,
    results_count: int = 0,
    provider: Optional[str] = None,
) -> SearchQuery:
    sq = SearchQuery(
        book_id=book_id,
        entity_type=entity_type,
        entity_name=entity_name,
        query_text=query_text,
        results_count=results_count,
        provider=provider,
    )
    db.add(sq)
    db.commit()
    db.refresh(sq)
    return sq


def get_search_queries_by_book(db: Session, book_id: int) -> list[SearchQuery]:
    return (
        db.query(SearchQuery)
        .filter(SearchQuery.book_id == book_id)
        .order_by(SearchQuery.created_at)
        .all()
    )


# ---------------------------------------------------------------------------
# Reference images pool
# ---------------------------------------------------------------------------

REFERENCE_IMAGES_POOL_LIMIT = 50


def create_reference_image(
    db: Session,
    *,
    book_id: int,
    entity_type: str,
    entity_id: int,
    url: str,
    thumbnail: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    source: str,  # "unsplash" | "serpapi" | "user"
) -> ReferenceImage:
    rec = ReferenceImage(
        book_id=book_id,
        entity_type=entity_type,
        entity_id=entity_id,
        url=url,
        thumbnail=thumbnail,
        width=width,
        height=height,
        source=source,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def get_reference_image_by_entity_url(
    db: Session,
    entity_type: str,
    entity_id: int,
    url: str,
) -> Optional[ReferenceImage]:
    return (
        db.query(ReferenceImage)
        .filter(
            ReferenceImage.entity_type == entity_type,
            ReferenceImage.entity_id == entity_id,
            ReferenceImage.url == url,
        )
        .first()
    )


def get_reference_images_for_entity(
    db: Session,
    entity_type: str,
    entity_id: int,
) -> list[ReferenceImage]:
    return (
        db.query(ReferenceImage)
        .filter(
            ReferenceImage.entity_type == entity_type,
            ReferenceImage.entity_id == entity_id,
        )
        .order_by(ReferenceImage.created_at.asc())
        .all()
    )


def trim_reference_images_fifo(
    db: Session,
    entity_type: str,
    entity_id: int,
    limit: int = REFERENCE_IMAGES_POOL_LIMIT,
    exclude_urls: Optional[set[str]] = None,
) -> None:
    """
    Keep at most `limit` reference images per entity; remove oldest by created_at (FIFO).
    Never remove images whose url is in exclude_urls (e.g. currently selected).
    """
    exclude_urls = exclude_urls or set()
    rows = get_reference_images_for_entity(db, entity_type, entity_id)
    if len(rows) <= limit:
        return
    to_delete = []
    for r in rows:
        if len(rows) - len(to_delete) <= limit:
            break
        if r.url in exclude_urls:
            continue
        to_delete.append(r)
    for r in to_delete:
        db.delete(r)
    db.commit()


def get_selected_reference_urls(db: Session, entity_type: str, entity_id: int) -> list[str]:
    """Get selected_reference_urls JSON array for character or location."""
    if entity_type == "character":
        c = db.query(Character).filter(Character.id == entity_id).first()
        if not c or not c.selected_reference_urls:
            return []
        try:
            out = _json.loads(c.selected_reference_urls)
            return out if isinstance(out, list) else []
        except (TypeError, _json.JSONDecodeError):
            return []
    else:
        loc = db.query(Location).filter(Location.id == entity_id).first()
        if not loc or not loc.selected_reference_urls:
            return []
        try:
            out = _json.loads(loc.selected_reference_urls)
            return out if isinstance(out, list) else []
        except (TypeError, _json.JSONDecodeError):
            return []


def get_latest_stored_queries_for_entity(
    db: Session,
    book_id: int,
    entity_type: str,
    entity_name: str,
    max_queries: int = 20,
) -> list[str]:
    """
    Return query_text from the most recent reference-search run for this entity.
    Used to show last-saved queries on Review Search instead of recomputed ones.
    """
    from datetime import timedelta

    rows = (
        db.query(SearchQuery)
        .filter(
            SearchQuery.book_id == book_id,
            SearchQuery.entity_type == entity_type,
            SearchQuery.entity_name == entity_name,
        )
        .order_by(SearchQuery.created_at.desc())
        .limit(50)
        .all()
    )
    if not rows:
        return []
    # Treat as one "run" all rows within 15 seconds of the most recent
    cutoff = rows[0].created_at - timedelta(seconds=15)
    run_rows = [r for r in rows if r.created_at >= cutoff]
    run_rows.sort(key=lambda r: (r.created_at, r.id))
    return [r.query_text for r in run_rows[:max_queries]]


# ---------------------------------------------------------------------------
# Character / Location — name lookup and ontology updates
# ---------------------------------------------------------------------------

def get_character(db: Session, character_id: int) -> Optional[Character]:
    return db.query(Character).filter(Character.id == character_id).first()


def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_character_by_name(db: Session, book_id: int, name: str) -> Optional[Character]:
    return (
        db.query(Character)
        .filter(Character.book_id == book_id, Character.name == name)
        .first()
    )


def get_location_by_name(db: Session, book_id: int, name: str) -> Optional[Location]:
    return (
        db.query(Location)
        .filter(Location.book_id == book_id, Location.name == name)
        .first()
    )


def update_character_ontology(
    db: Session,
    character_id: int,
    ontology_json: str,
    entity_visual_tokens_json: Optional[str] = None,
) -> Optional[Character]:
    char = db.query(Character).filter(Character.id == character_id).first()
    if char:
        char.ontology_json = ontology_json
        if entity_visual_tokens_json is not None:
            char.entity_visual_tokens_json = entity_visual_tokens_json
        db.commit()
        db.refresh(char)
    return char


def update_location_ontology(
    db: Session,
    location_id: int,
    ontology_json: str,
    entity_visual_tokens_json: Optional[str] = None,
) -> Optional[Location]:
    loc = db.query(Location).filter(Location.id == location_id).first()
    if loc:
        loc.ontology_json = ontology_json
        if entity_visual_tokens_json is not None:
            loc.entity_visual_tokens_json = entity_visual_tokens_json
        db.commit()
        db.refresh(loc)
    return loc


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

def create_scene(
    db: Session,
    *,
    book_id: int,
    title: Optional[str] = None,
    title_display: Optional[str] = None,
    scene_type: Optional[str] = None,
    chunk_start_index: int,
    chunk_end_index: int,
    narrative_summary: Optional[str] = None,
    narrative_summary_display: Optional[str] = None,
    visual_description: Optional[str] = None,
    dramatic_score_avg: Optional[float] = None,
    visual_intensity: Optional[float] = None,
    illustration_priority: Optional[str] = None,
    narrative_position: Optional[str] = None,
    scene_prompt_draft: Optional[str] = None,
    scene_visual_tokens_json: Optional[str] = None,
    t2i_prompt_json: Optional[str] = None,
    is_selected: int = 1,
) -> Scene:
    scene = Scene(
        book_id=book_id,
        title=title,
        title_display=title_display,
        scene_type=scene_type,
        chunk_start_index=chunk_start_index,
        chunk_end_index=chunk_end_index,
        narrative_summary=narrative_summary,
        narrative_summary_display=narrative_summary_display,
        visual_description=visual_description,
        dramatic_score_avg=dramatic_score_avg,
        visual_intensity=visual_intensity,
        illustration_priority=illustration_priority,
        narrative_position=narrative_position,
        scene_prompt_draft=scene_prompt_draft,
        scene_visual_tokens_json=scene_visual_tokens_json,
        t2i_prompt_json=t2i_prompt_json,
        is_selected=is_selected,
    )
    db.add(scene)
    db.commit()
    db.refresh(scene)
    return scene


def get_scenes_by_book(db: Session, book_id: int) -> list[Scene]:
    return (
        db.query(Scene)
        .filter(Scene.book_id == book_id)
        .order_by(Scene.chunk_start_index)
        .all()
    )


def get_scene(db: Session, scene_id: int) -> Optional[Scene]:
    return db.query(Scene).filter(Scene.id == scene_id).first()


def update_scene(db: Session, scene_id: int, **kwargs) -> Optional[Scene]:
    scene = get_scene(db, scene_id)
    if scene:
        for key, value in kwargs.items():
            if hasattr(scene, key):
                setattr(scene, key, value)
        db.commit()
        db.refresh(scene)
    return scene


def delete_scenes_by_book(db: Session, book_id: int) -> int:
    """Delete all scenes for a book. Returns count of deleted rows."""
    scenes = db.query(Scene).filter(Scene.book_id == book_id).all()
    count = len(scenes)
    for scene in scenes:
        db.delete(scene)
    db.commit()
    return count


def create_scene_character(
    db: Session, scene_id: int, character_id: int, commit: bool = True
) -> Optional[SceneCharacter]:
    exists = (
        db.query(SceneCharacter)
        .filter(
            SceneCharacter.scene_id == scene_id,
            SceneCharacter.character_id == character_id,
        )
        .first()
    )
    if exists:
        return exists
    sc = SceneCharacter(scene_id=scene_id, character_id=character_id)
    db.add(sc)
    if commit:
        db.commit()
        db.refresh(sc)
    return sc


def create_scene_location(
    db: Session, scene_id: int, location_id: int, commit: bool = True
) -> Optional[SceneLocation]:
    exists = (
        db.query(SceneLocation)
        .filter(
            SceneLocation.scene_id == scene_id,
            SceneLocation.location_id == location_id,
        )
        .first()
    )
    if exists:
        return exists
    sl = SceneLocation(scene_id=scene_id, location_id=location_id)
    db.add(sl)
    if commit:
        db.commit()
        db.refresh(sl)
    return sl


# ---------------------------------------------------------------------------
# Engine Ratings
# ---------------------------------------------------------------------------

def get_engine_ratings(db: Session, book_id: int) -> dict[str, int]:
    """Returns {provider: net_score} for the book."""
    rows = db.query(EngineRating).filter(EngineRating.book_id == book_id).all()
    return {r.provider: r.net_score for r in rows}


def update_engine_rating(
    db: Session,
    book_id: int,
    provider: str,
    delta_likes: int = 0,
    delta_dislikes: int = 0,
) -> EngineRating:
    """Increments likes or dislikes. Creates row if not exists (upsert)."""
    row = (
        db.query(EngineRating)
        .filter(EngineRating.book_id == book_id, EngineRating.provider == provider)
        .first()
    )
    if not row:
        row = EngineRating(book_id=book_id, provider=provider, likes=0, dislikes=0)
        db.add(row)
    row.likes = (row.likes or 0) + delta_likes
    row.dislikes = (row.dislikes or 0) + delta_dislikes
    db.commit()
    db.refresh(row)
    return row


def get_engine_ratings_list(db: Session, book_id: int) -> list[EngineRating]:
    """Returns all EngineRating rows for the book."""
    return db.query(EngineRating).filter(EngineRating.book_id == book_id).all()
