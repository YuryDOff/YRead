"""
Full database reset for development: clears all data so you can start analysis from scratch.

Usage (from backend directory):
  python -m scripts.reset_db

Or:
  cd backend && python scripts/reset_db.py

Tables are cleared in FK-safe order. Schema is preserved (init_db re-applied).
"""
import os
import sys

# Ensure backend/app is on path when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.database import engine, init_db


# Order: child tables first (respecting FK)
TABLES_TO_TRUNCATE = [
    "chunk_characters",
    "chunk_locations",
    "illustrations",
    "search_queries",
    "visual_bible",
    "covers",
    "kdp_exports",
    "chunks",
    "characters",
    "locations",
    "books",
]


def reset_database():
    """Delete all rows from application tables. Schema is left intact."""
    with engine.begin() as conn:
        for table in TABLES_TO_TRUNCATE:
            conn.execute(text(f"DELETE FROM {table}"))
        # Reset SQLite autoincrement counters (table may not exist in some setups)
        try:
            conn.execute(text("DELETE FROM sqlite_sequence"))
        except Exception:
            pass
    print("Database cleared: all application data removed.")
    init_db()
    print("Schema verified (init_db). Ready for fresh upload and analysis.")


if __name__ == "__main__":
    reset_database()
