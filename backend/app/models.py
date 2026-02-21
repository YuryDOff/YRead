"""SQLAlchemy models for StoryForge AI application."""
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
    Boolean,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ---------------------------------------------------------------------------
# Scenes (narrative units extracted from chunks)
# ---------------------------------------------------------------------------

class Scene(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    title = Column(String, nullable=True)
    title_display = Column(String, nullable=True)  # in manuscript language for UI
    scene_type = Column(String, nullable=True)
    chunk_start_index = Column(Integer, nullable=False)
    chunk_end_index = Column(Integer, nullable=False)
    narrative_summary = Column(Text, nullable=True)  # English for DB/API
    narrative_summary_display = Column(Text, nullable=True)  # manuscript language for UI
    visual_description = Column(Text, nullable=True)
    dramatic_score_avg = Column(Float, nullable=True)
    visual_intensity = Column(Float, nullable=True)
    illustration_priority = Column(String, nullable=True)
    narrative_position = Column(String, nullable=True)
    scene_prompt_draft = Column(Text, nullable=True)
    scene_visual_tokens_json = Column(Text, nullable=True)
    t2i_prompt_json = Column(Text, nullable=True)
    is_selected = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    book = relationship("Book", back_populates="scenes")
    scene_characters = relationship("SceneCharacter", cascade="all, delete-orphan")
    scene_locations = relationship("SceneLocation", cascade="all, delete-orphan")
    illustrations = relationship("Illustration", back_populates="scene", cascade="all, delete-orphan")

    __table_args__ = (Index("ix_scenes_book_id", "book_id"),)


class SceneCharacter(Base):
    __tablename__ = "scene_characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=False)

    character = relationship("Character")

    __table_args__ = (UniqueConstraint("scene_id", "character_id", name="uq_scene_character"),)


class SceneLocation(Base):
    __tablename__ = "scene_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    location = relationship("Location")

    __table_args__ = (UniqueConstraint("scene_id", "location_id", name="uq_scene_location"),)


# ---------------------------------------------------------------------------
# Engine Ratings (per-book provider feedback)
# ---------------------------------------------------------------------------

class EngineRating(Base):
    __tablename__ = "engine_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    provider = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    dislikes = Column(Integer, default=0)

    @property
    def net_score(self) -> int:
        return (self.likes or 0) - (self.dislikes or 0)

    __table_args__ = (
        UniqueConstraint("book_id", "provider", name="uq_engine_rating"),
        Index("ix_engine_ratings_book_id", "book_id"),
    )


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
    workflow_type = Column(String, default="full")  # 'full' or 'cover_only'
    is_well_known_book = Column(Boolean, default=False)  # B2B: is it a well-known book?
    well_known_book_title = Column(Text, nullable=True)  # B2B: title of the well-known published work (e.g. "A Study in Scarlet")
    similar_book_title = Column(Text, nullable=True)  # B2B: reference book for search optimization
    scene_count = Column(Integer, nullable=True, default=10)
    known_adaptations_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    chunks = relationship("Chunk", back_populates="book", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="book", cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="book", cascade="all, delete-orphan")
    visual_bible = relationship("VisualBible", back_populates="book", uselist=False, cascade="all, delete-orphan")
    illustrations = relationship("Illustration", back_populates="book", cascade="all, delete-orphan")
    covers = relationship("Cover", back_populates="book", cascade="all, delete-orphan")
    kdp_exports = relationship("KDPExport", back_populates="book", cascade="all, delete-orphan")
    search_queries = relationship("SearchQuery", back_populates="book", cascade="all, delete-orphan")
    scenes = relationship("Scene", back_populates="book", cascade="all, delete-orphan")
    engine_ratings = relationship("EngineRating", cascade="all, delete-orphan")


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
    visual_analysis_json = Column(Text, nullable=True)  # JSON: {visual_layers, visual_tokens}

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
    reference_image_url = Column(Text, nullable=True)  # primary user-selected reference (first of selected_reference_urls)
    selected_reference_urls = Column(Text, nullable=True)  # JSON array of selected reference URLs for visual bible
    is_main = Column(Integer, default=0)  # 0 = no, 1 = yes (SQLite bool)
    visual_type = Column(String, nullable=True)  # man | woman | animal | AI | alien | creature
    is_well_known_entity = Column(Integer, default=0)
    canonical_search_name = Column(String, nullable=True)
    search_visual_analog = Column(Text, nullable=True)
    text_to_image_prompt = Column(Text, nullable=True)
    ontology_json = Column(Text, nullable=True)
    entity_visual_tokens_json = Column(Text, nullable=True)

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
    reference_image_url = Column(Text, nullable=True)  # primary user-selected reference (first of selected_reference_urls)
    selected_reference_urls = Column(Text, nullable=True)  # JSON array of selected reference URLs for visual bible
    is_main = Column(Integer, default=0)  # 0 = no, 1 = yes (SQLite bool)
    is_well_known_entity = Column(Integer, default=0)
    canonical_search_name = Column(String, nullable=True)
    search_visual_analog = Column(Text, nullable=True)
    text_to_image_prompt = Column(Text, nullable=True)
    ontology_json = Column(Text, nullable=True)
    entity_visual_tokens_json = Column(Text, nullable=True)

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
    scene_id = Column(Integer, ForeignKey("scenes.id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    image_path = Column(Text, nullable=True)
    prompt = Column(Text, nullable=True)
    prompt_used = Column(Text, nullable=True)
    style = Column(String, nullable=True)
    reference_images = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending | generating | completed | failed
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="illustrations")
    chunk = relationship("Chunk", back_populates="illustrations")
    scene = relationship("Scene", back_populates="illustrations")

    __table_args__ = (
        Index("ix_illustrations_book_id", "book_id"),
        Index("ix_illustrations_status", "status"),
    )


# ---------------------------------------------------------------------------
# Covers (B2B: book covers for KDP)
# ---------------------------------------------------------------------------

class Cover(Base):
    __tablename__ = "covers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    front_visual_path = Column(Text, nullable=True)  # path to front cover visual
    full_cover_path = Column(Text, nullable=True)  # complete cover with spine/back
    template = Column(String, nullable=True)  # genre template used
    spine_width = Column(Float, nullable=True)  # spine width in inches
    customizations = Column(Text, nullable=True)  # JSON: custom settings
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="covers")

    __table_args__ = (
        Index("ix_covers_book_id", "book_id"),
    )


# ---------------------------------------------------------------------------
# KDP Exports (B2B: PDF exports for Amazon KDP)
# ---------------------------------------------------------------------------

class KDPExport(Base):
    __tablename__ = "kdp_exports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    trim_size = Column(String, nullable=True)  # e.g., "6x9", "5x8"
    interior_pdf_path = Column(Text, nullable=True)  # path to interior PDF
    cover_pdf_path = Column(Text, nullable=True)  # path to cover PDF
    zip_file_path = Column(Text, nullable=True)  # path to complete package ZIP
    exported_at = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)

    # Relationships
    book = relationship("Book", back_populates="kdp_exports")

    __table_args__ = (
        Index("ix_kdp_exports_book_id", "book_id"),
    )


# ---------------------------------------------------------------------------
# Search Queries (audit log for SerpAPI calls)
# ---------------------------------------------------------------------------

class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    entity_type = Column(String, nullable=False)   # "character" | "location"
    entity_name = Column(String, nullable=False)
    query_text = Column(Text, nullable=False)
    results_count = Column(Integer, default=0)
    provider = Column(String, nullable=True)  # "unsplash" | "serpapi"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="search_queries")

    __table_args__ = (
        Index("ix_search_queries_book_id", "book_id"),
    )


# ---------------------------------------------------------------------------
# Reference images pool (search results + user uploads, FIFO cap 50 per entity)
# ---------------------------------------------------------------------------

class ReferenceImage(Base):
    __tablename__ = "reference_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    entity_type = Column(String, nullable=False)  # "character" | "location"
    entity_id = Column(Integer, nullable=False)  # character.id or location.id
    url = Column(Text, nullable=False)
    thumbnail = Column(Text, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    source = Column(String, nullable=False)  # "unsplash" | "serpapi" | "user"
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_reference_images_book_entity", "book_id", "entity_type", "entity_id"),
        Index("ix_reference_images_entity_created", "entity_type", "entity_id", "created_at"),
    )


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
