"""Pydantic schemas for request / response validation."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# Book
# ---------------------------------------------------------------------------

class BookImportRequest(BaseModel):
    google_drive_link: str


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    author: Optional[str] = None
    google_drive_link: Optional[str] = None
    total_words: Optional[int] = None
    total_pages: Optional[int] = None
    status: Optional[str] = None
    is_well_known: Optional[int] = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookAnalyzeRequest(BaseModel):
    style_category: str  # fiction | sci-fi | romance | …
    illustration_frequency: int = 4  # pages between illustrations
    layout_style: str = "inline_classic"  # inline_classic | anime_panels
    is_well_known: bool = False
    author: Optional[str] = None


# ---------------------------------------------------------------------------
# Character
# ---------------------------------------------------------------------------

class CharacterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    name: str
    physical_description: Optional[str] = None
    personality_traits: Optional[str] = None
    typical_emotions: Optional[str] = None
    reference_image_url: Optional[str] = None


class CharacterUpdate(BaseModel):
    physical_description: Optional[str] = None
    personality_traits: Optional[str] = None
    reference_image_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------

class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    name: str
    visual_description: Optional[str] = None
    atmosphere: Optional[str] = None
    reference_image_url: Optional[str] = None


class LocationUpdate(BaseModel):
    visual_description: Optional[str] = None
    atmosphere: Optional[str] = None
    reference_image_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Visual Bible
# ---------------------------------------------------------------------------

class VisualBibleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    style_category: Optional[str] = None
    tone_description: Optional[str] = None
    illustration_frequency: Optional[int] = None
    layout_style: Optional[str] = None
    approved_at: Optional[datetime] = None


class VisualBibleApproveRequest(BaseModel):
    """Payload sent when user approves the visual bible with their selections."""
    character_selections: dict[int, str] = {}   # character_id → reference_image_url
    location_selections: dict[int, str] = {}    # location_id  → reference_image_url


# ---------------------------------------------------------------------------
# Illustration
# ---------------------------------------------------------------------------

class IllustrationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    chunk_id: Optional[int] = None
    page_number: Optional[int] = None
    image_path: Optional[str] = None
    prompt: Optional[str] = None
    style: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Reading Progress
# ---------------------------------------------------------------------------

class ReadingProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    current_page: int = 1
    last_read_at: Optional[datetime] = None


class ReadingProgressUpdate(BaseModel):
    current_page: int


# ---------------------------------------------------------------------------
# Chunk
# ---------------------------------------------------------------------------

class ChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    chunk_index: int
    text: str
    start_page: Optional[int] = None
    end_page: Optional[int] = None
    word_count: Optional[int] = None
    dramatic_score: Optional[float] = None


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None


class AnalyzeStatusResponse(BaseModel):
    status: str
    estimated_time: Optional[int] = None  # seconds
