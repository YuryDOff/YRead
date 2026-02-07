"""SQLAlchemy models for Reading Reinvented application."""
from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Books
# ---------------------------------------------------------------------------

class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    author = Column(String, nullable=True)
    google_drive_link = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    total_words = Column(Integer, nullable=True)
    total_pages = Column(Integer, nullable=True)
    status = Column(String, default="imported")  # imported | analyzing | ready | reading
    is_well_known = Column(Integer, default=0)  # 0 = no, 1 = yes (SQLite bool)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("Chunk", back_populates="book", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="book", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="book", cascade="all, delete-orphan")
    visual_bible = relationship("VisualBible", back_populates="book", uselist=False, cascade="all, delete-orphan")
    illustrations = relationship("Illustration", back_populates="book", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="book", uselist=False, cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Chunks
# ---------------------------------------------------------------------------

class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    start_page = Column(Integer, nullable=True)
    end_page = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    dramatic_score = Column(Float, nullable=True)  # 0.0 – 1.0

    # Relationships
    book = relationship("Book", back_populates="chunks")
    illustrations = relationship("Illustration", back_populates="chunk", cascade="all, delete-orphan")
    chunk_characters = relationship("ChunkCharacter", back_populates="chunk", cascade="all, delete-orphan")
    chunk_locations = relationship("ChunkLocation", back_populates="chunk", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_chunks_book_id", "book_id"),
        Index("ix_chunks_book_index", "book_id", "chunk_index"),
    )


# ---------------------------------------------------------------------------
# Characters
# ---------------------------------------------------------------------------

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    name = Column(String, nullable=False)
    physical_description = Column(Text, nullable=True)
    personality_traits = Column(Text, nullable=True)
    typical_emotions = Column(Text, nullable=True)
    reference_image_url = Column(Text, nullable=True)  # user-selected reference

    # Relationships
    book = relationship("Book", back_populates="characters")
    chunk_characters = relationship("ChunkCharacter", back_populates="character", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_characters_book_id", "book_id"),
    )


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    name = Column(String, nullable=False)
    visual_description = Column(Text, nullable=True)
    atmosphere = Column(Text, nullable=True)
    reference_image_url = Column(Text, nullable=True)  # user-selected reference

    # Relationships
    book = relationship("Book", back_populates="locations")
    chunk_locations = relationship("ChunkLocation", back_populates="location", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_locations_book_id", "book_id"),
    )


# ---------------------------------------------------------------------------
# Visual Bible
# ---------------------------------------------------------------------------

class VisualBible(Base):
    __tablename__ = "visual_bible"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), unique=True, nullable=False)
    style_category = Column(String, nullable=True)  # fiction | sci-fi | romance | …
    tone_description = Column(Text, nullable=True)
    illustration_frequency = Column(Integer, nullable=True)  # pages between illustrations
    layout_style = Column(String, nullable=True)  # inline_classic | anime_panels
    approved_at = Column(DateTime, nullable=True)

    # Relationships
    book = relationship("Book", back_populates="visual_bible")


# ---------------------------------------------------------------------------
# Illustrations
# ---------------------------------------------------------------------------

class Illustration(Base):
    __tablename__ = "illustrations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    image_path = Column(Text, nullable=True)  # server filesystem path
    prompt = Column(Text, nullable=True)  # full prompt used for generation
    style = Column(String, nullable=True)
    reference_images = Column(Text, nullable=True)  # JSON array of reference URLs
    status = Column(String, default="pending")  # pending | generating | completed | failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="illustrations")
    chunk = relationship("Chunk", back_populates="illustrations")

    __table_args__ = (
        Index("ix_illustrations_book_id", "book_id"),
        Index("ix_illustrations_status", "status"),
    )


# ---------------------------------------------------------------------------
# Reading Progress
# ---------------------------------------------------------------------------

class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), unique=True, nullable=False)
    current_page = Column(Integer, default=1)
    last_read_at = Column(DateTime, nullable=True)

    # Relationships
    book = relationship("Book", back_populates="reading_progress")


# ---------------------------------------------------------------------------
# Junction tables: Chunk ↔ Character, Chunk ↔ Location
# ---------------------------------------------------------------------------

class ChunkCharacter(Base):
    __tablename__ = "chunk_characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    # Relationships
    chunk = relationship("Chunk", back_populates="chunk_characters")
    character = relationship("Character", back_populates="chunk_characters")

    __table_args__ = (
        UniqueConstraint("chunk_id", "character_id", name="uq_chunk_character"),
        Index("ix_chunk_characters_chunk_id", "chunk_id"),
        Index("ix_chunk_characters_character_id", "character_id"),
    )


class ChunkLocation(Base):
    __tablename__ = "chunk_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(Integer, ForeignKey("chunks.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    # Relationships
    chunk = relationship("Chunk", back_populates="chunk_locations")
    location = relationship("Location", back_populates="chunk_locations")

    __table_args__ = (
        UniqueConstraint("chunk_id", "location_id", name="uq_chunk_location"),
        Index("ix_chunk_locations_chunk_id", "chunk_id"),
        Index("ix_chunk_locations_location_id", "location_id"),
    )
