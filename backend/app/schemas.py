"""Pydantic schemas for request / response validation."""
import json as _json
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


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
    well_known_book_title: Optional[str] = None
    similar_book_title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class BookAnalyzeRequest(BaseModel):
    style_category: str  # fiction | sci-fi | romance | …
    illustration_frequency: int = 4  # pages between illustrations
    layout_style: str = "inline_classic"  # inline_classic | anime_panels
    is_well_known: bool = False
    author: Optional[str] = None
    well_known_book_title: Optional[str] = None
    similar_book_title: Optional[str] = None
    scene_count: int = 10  # number of key scenes to extract


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
    is_main: Optional[int] = 0
    visual_type: Optional[str] = None
    is_well_known_entity: Optional[int] = 0
    canonical_search_name: Optional[str] = None
    search_visual_analog: Optional[str] = None
    ontology: Optional[dict] = None
    entity_visual_tokens: Optional[dict] = None

    @model_validator(mode="before")
    @classmethod
    def _deserialize_json_fields(cls, values):
        """Deserialize JSON text fields from DB into dicts."""
        if hasattr(values, "__dict__"):
            # SQLAlchemy model instance
            raw_onto = getattr(values, "ontology_json", None)
            raw_tokens = getattr(values, "entity_visual_tokens_json", None)
            d = dict(values.__dict__)
            if raw_onto and isinstance(raw_onto, str):
                try:
                    d["ontology"] = _json.loads(raw_onto)
                except Exception:
                    d["ontology"] = None
            if raw_tokens and isinstance(raw_tokens, str):
                try:
                    d["entity_visual_tokens"] = _json.loads(raw_tokens)
                except Exception:
                    d["entity_visual_tokens"] = None
            return d
        return values


class CharacterUpdate(BaseModel):
    physical_description: Optional[str] = None
    personality_traits: Optional[str] = None
    reference_image_url: Optional[str] = None
    visual_type: Optional[str] = None
    is_well_known_entity: Optional[bool] = None
    canonical_search_name: Optional[str] = None
    search_visual_analog: Optional[str] = None


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
    is_main: Optional[int] = 0
    is_well_known_entity: Optional[int] = 0
    canonical_search_name: Optional[str] = None
    search_visual_analog: Optional[str] = None
    ontology: Optional[dict] = None
    entity_visual_tokens: Optional[dict] = None

    @model_validator(mode="before")
    @classmethod
    def _deserialize_json_fields(cls, values):
        if hasattr(values, "__dict__"):
            raw_onto = getattr(values, "ontology_json", None)
            raw_tokens = getattr(values, "entity_visual_tokens_json", None)
            d = dict(values.__dict__)
            if raw_onto and isinstance(raw_onto, str):
                try:
                    d["ontology"] = _json.loads(raw_onto)
                except Exception:
                    d["ontology"] = None
            if raw_tokens and isinstance(raw_tokens, str):
                try:
                    d["entity_visual_tokens"] = _json.loads(raw_tokens)
                except Exception:
                    d["entity_visual_tokens"] = None
            return d
        return values


class LocationUpdate(BaseModel):
    visual_description: Optional[str] = None
    atmosphere: Optional[str] = None
    reference_image_url: Optional[str] = None
    is_well_known_entity: Optional[bool] = None
    canonical_search_name: Optional[str] = None
    search_visual_analog: Optional[str] = None


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
    # Each key is entity id (str in JSON); value is list of selected reference URLs
    character_selections: dict[str, list[str]] = {}   # character_id → [urls]
    location_selections: dict[str, list[str]] = {}     # location_id  → [urls]


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
# Search Queries
# ---------------------------------------------------------------------------

class SearchQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    entity_type: str
    entity_name: str
    query_text: str
    results_count: int = 0
    provider: Optional[str] = None
    created_at: Optional[datetime] = None


class SearchReferencesRequest(BaseModel):
    main_only: bool = True
    # Keys are entity ids (sent as strings in JSON)
    character_queries: Optional[dict[str, list[str]]] = None
    location_queries: Optional[dict[str, list[str]]] = None
    character_summaries: Optional[dict[str, dict]] = None
    location_summaries: Optional[dict[str, dict]] = None
    # Preferred reference image provider: "unsplash" | "serpapi" (default: try Unsplash first, then SerpAPI)
    preferred_provider: Optional[Literal["unsplash", "serpapi"]] = None
    # Which entity types to search: "characters" | "locations" | "both" (default: both)
    search_entity_types: Optional[Literal["characters", "locations", "both"]] = "both"
    # Optional: restrict search to these provider names (from Settings). If omitted, all available are used.
    enabled_providers: Optional[list[str]] = None


# ---------------------------------------------------------------------------
# Scenes
# ---------------------------------------------------------------------------

class SceneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    title: Optional[str] = None
    title_display: Optional[str] = None  # manuscript language for UI
    scene_type: Optional[str] = None
    chunk_start_index: int
    chunk_end_index: int
    narrative_summary: Optional[str] = None
    narrative_summary_display: Optional[str] = None  # manuscript language for UI
    visual_description: Optional[str] = None
    scene_prompt_draft: Optional[str] = None
    t2i_prompt_json: Optional[dict] = None
    scene_visual_tokens: Optional[dict] = None
    dramatic_score_avg: Optional[float] = None
    illustration_priority: Optional[str] = None
    narrative_position: Optional[str] = None
    is_selected: bool = True
    characters_present: list[str] = []
    primary_location: Optional[str] = None

    @field_validator("is_selected", mode="before")
    @classmethod
    def _coerce_is_selected(cls, v):
        return bool(v)

    @model_validator(mode="before")
    @classmethod
    def _deserialize_json_and_relations(cls, values):
        if hasattr(values, "__dict__"):
            d = dict(values.__dict__)
            raw_t2i = getattr(values, "t2i_prompt_json", None)
            raw_svt = getattr(values, "scene_visual_tokens_json", None)
            if raw_t2i and isinstance(raw_t2i, str):
                try:
                    d["t2i_prompt_json"] = _json.loads(raw_t2i)
                except Exception:
                    d["t2i_prompt_json"] = None
            if raw_svt and isinstance(raw_svt, str):
                try:
                    d["scene_visual_tokens"] = _json.loads(raw_svt)
                except Exception:
                    d["scene_visual_tokens"] = None
            # Build characters_present from scene_characters relationship
            chars = []
            for sc in (getattr(values, "scene_characters", None) or []):
                char = getattr(sc, "character", None)
                if char and hasattr(char, "name"):
                    chars.append(char.name)
            if chars:
                d["characters_present"] = chars
            # Build primary_location from scene_locations relationship
            loc_name = None
            for sl in (getattr(values, "scene_locations", None) or []):
                loc = getattr(sl, "location", None)
                if loc and hasattr(loc, "name"):
                    loc_name = loc.name
                    break
            d["primary_location"] = loc_name
            return d
        return values


class SceneUpdateRequest(BaseModel):
    title: Optional[str] = None
    scene_prompt_draft: Optional[str] = None
    is_selected: Optional[bool] = None


# ---------------------------------------------------------------------------
# Engine Ratings
# ---------------------------------------------------------------------------

class EngineRatingUpdate(BaseModel):
    provider: str
    action: Literal["like", "dislike"]


class EngineRatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    likes: int
    dislikes: int
    net_score: int


class EntitySummariesUpdate(BaseModel):
    """Batch update entity summaries and search-related fields."""
    characters: list[dict] = []  # [{id, physical_description?, visual_type?, ...}]
    locations: list[dict] = []   # [{id, visual_description?, ...}]


# ---------------------------------------------------------------------------
# Entity selection (batch update is_main)
# ---------------------------------------------------------------------------

class EntityMainFlag(BaseModel):
    id: int
    is_main: bool


class EntitySelectionsRequest(BaseModel):
    """Batch-update is_main flags for characters and locations."""
    characters: list[EntityMainFlag] = []
    locations: list[EntityMainFlag] = []


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

class StatusResponse(BaseModel):
    status: str
    message: Optional[str] = None


class AnalyzeStatusResponse(BaseModel):
    status: str
    estimated_time: Optional[int] = None  # seconds
