"""CRUD helper functions for database operations."""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models import (
    Book,
    Chunk,
    Character,
    Location,
    VisualBible,
    Illustration,
    ReadingProgress,
    ChunkCharacter,
    ChunkLocation,
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
            joinedload(Book.reading_progress),
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
    if book:
        db.delete(book)
        db.commit()
        return True
    return False


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
) -> Character:
    char = Character(
        book_id=book_id,
        name=name,
        physical_description=physical_description,
        personality_traits=personality_traits,
        typical_emotions=typical_emotions,
        reference_image_url=reference_image_url,
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
) -> Location:
    loc = Location(
        book_id=book_id,
        name=name,
        visual_description=visual_description,
        atmosphere=atmosphere,
        reference_image_url=reference_image_url,
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
# Reading Progress
# ---------------------------------------------------------------------------

def get_or_create_reading_progress(db: Session, book_id: int) -> ReadingProgress:
    progress = (
        db.query(ReadingProgress)
        .filter(ReadingProgress.book_id == book_id)
        .first()
    )
    if not progress:
        progress = ReadingProgress(book_id=book_id, current_page=1)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def update_reading_progress(
    db: Session, book_id: int, current_page: int
) -> ReadingProgress:
    progress = get_or_create_reading_progress(db, book_id)
    progress.current_page = current_page
    progress.last_read_at = datetime.utcnow()
    db.commit()
    db.refresh(progress)
    return progress


# ---------------------------------------------------------------------------
# Junction tables: Chunk ↔ Character / Location
# ---------------------------------------------------------------------------

def link_chunk_characters(
    db: Session, chunk_id: int, character_ids: list[int]
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
    db.commit()


def link_chunk_locations(
    db: Session, chunk_id: int, location_ids: list[int]
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
