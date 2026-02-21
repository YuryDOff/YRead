"""Database connection and session management."""
import logging
import os
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables and run lightweight migrations."""
    from app.models import (  # noqa: F401 – ensure models registered
        Book, Chunk, Character, Location, VisualBible,
        Illustration, Cover, KDPExport, ChunkCharacter, ChunkLocation,
        SearchQuery, ReferenceImage,
        Scene, SceneCharacter, SceneLocation, EngineRating,
    )
    try:
        Base.metadata.create_all(bind=engine)
        _run_migrations()
    except Exception as e:
        raise


def _run_migrations():
    """Add columns that may be missing on existing SQLite tables."""
    # Existing migrations
    _add_column_if_missing("characters", "is_main", "INTEGER DEFAULT 0")
    _add_column_if_missing("locations", "is_main", "INTEGER DEFAULT 0")
    
    # B2B migrations for books table
    _add_column_if_missing("books", "workflow_type", "TEXT DEFAULT 'full'")
    _add_column_if_missing("books", "is_well_known_book", "BOOLEAN DEFAULT 0")
    _add_column_if_missing("books", "well_known_book_title", "TEXT")
    _add_column_if_missing("books", "similar_book_title", "TEXT")

    # Task 1.6: Reference Image Search v2
    _add_column_if_missing("search_queries", "provider", "TEXT")
    _add_column_if_missing("chunks", "visual_analysis_json", "TEXT")

    # Smart visual query: character/location search fields
    _add_column_if_missing("characters", "visual_type", "TEXT")
    _add_column_if_missing("characters", "is_well_known_entity", "INTEGER DEFAULT 0")
    _add_column_if_missing("characters", "canonical_search_name", "TEXT")
    _add_column_if_missing("characters", "search_visual_analog", "TEXT")
    _add_column_if_missing("locations", "is_well_known_entity", "INTEGER DEFAULT 0")
    _add_column_if_missing("locations", "canonical_search_name", "TEXT")
    _add_column_if_missing("locations", "search_visual_analog", "TEXT")

    # Text-to-image prompt per entity (review-search step)
    _add_column_if_missing("characters", "text_to_image_prompt", "TEXT")
    _add_column_if_missing("locations", "text_to_image_prompt", "TEXT")

    # Review Search Result: multiple selected references per entity
    _add_column_if_missing("characters", "selected_reference_urls", "TEXT")
    _add_column_if_missing("locations", "selected_reference_urls", "TEXT")

    # v3: Ontology + Visual Tokens per entity
    _add_column_if_missing("characters", "ontology_json", "TEXT")
    _add_column_if_missing("characters", "entity_visual_tokens_json", "TEXT")
    _add_column_if_missing("locations", "ontology_json", "TEXT")
    _add_column_if_missing("locations", "entity_visual_tokens_json", "TEXT")

    # v3: Book scene count + known adaptations
    _add_column_if_missing("books", "scene_count", "INTEGER DEFAULT 10")
    _add_column_if_missing("books", "known_adaptations_json", "TEXT")

    # v3: Illustration scene_id + prompt_used
    _add_column_if_missing("illustrations", "scene_id", "INTEGER")
    _add_column_if_missing("illustrations", "prompt_used", "TEXT")

    # Scene display in manuscript language (for cohesive UX)
    _add_column_if_missing("scenes", "title_display", "TEXT")
    _add_column_if_missing("scenes", "narrative_summary_display", "TEXT")

    # Reference images pool table (created via create_all if new)

    # Drop reading_progress table if it exists (not needed for B2B)
    _drop_table_if_exists("reading_progress")


def _add_column_if_missing(table: str, column: str, col_type: str):
    """Safely add a column to an existing table (SQLite ALTER TABLE)."""
    insp = inspect(engine)
    existing = [c["name"] for c in insp.get_columns(table)]
    if column not in existing:
        with engine.begin() as conn:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))
        logger.info("Migration: added column %s.%s", table, column)


def _drop_table_if_exists(table: str):
    """Safely drop a table if it exists (for deprecated tables)."""
    insp = inspect(engine)
    if table in insp.get_table_names():
        with engine.begin() as conn:
            conn.execute(text(f"DROP TABLE {table}"))
        logger.info("Migration: dropped table %s", table)