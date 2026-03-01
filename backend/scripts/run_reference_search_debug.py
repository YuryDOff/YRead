"""
Debug script: run reference image search with all enabled providers and print
engine coverage and per-entity provider distribution.

Use this to verify:
  1) All selected engines are called and return non-zero results (see provider_usage).
  2) Final result per entity is fairly represented by providers (see distribution per entity).

Usage (from backend directory):
  python -m scripts.run_reference_search_debug <book_id>

Example:
  python -m scripts.run_reference_search_debug 1
"""
import asyncio
import os
import sys

# Ensure backend/app is on path when run as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env if present
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.isfile(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)

from app.database import SessionLocal
from app.services.providers import ALL_PROVIDERS
from app.services.search_service import search_references_for_book


def _provider_distribution(images: list) -> dict[str, int]:
    out: dict[str, int] = {}
    for img in images:
        p = img.get("provider") or "unknown"
        out[p] = out.get(p, 0) + 1
    return out


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.run_reference_search_debug <book_id>")
        sys.exit(1)
    try:
        book_id = int(sys.argv[1])
    except ValueError:
        print("book_id must be an integer")
        sys.exit(1)

    available = [n for n, p in ALL_PROVIDERS.items() if p.is_available()]
    if not available:
        print("No image search providers are available (check API keys in .env).")
        sys.exit(1)

    print(f"Available providers: {available}")
    print(f"Running search for book_id={book_id} with enabled_providers={available} (main_only=True)")
    print()

    db = SessionLocal()
    try:
        result = await search_references_for_book(
            book_id=book_id,
            search_all=False,
            db=db,
            enabled_providers=available,
        )
    finally:
        db.close()

    provider_usage = result.get("provider_usage", {})
    print("--- provider_usage (raw counts in aggregated pool) ---")
    for name, count in sorted(provider_usage.items(), key=lambda x: -x[1]):
        print(f"  {name}: {count}")
    print()

    print("--- Per-entity final image distribution (after filter/rank) ---")
    for kind, key in [("characters", "characters"), ("locations", "locations")]:
        items = result.get(key, [])
        for item in items:
            name = item.get("name", "?")
            images = item.get("images", [])
            dist = _provider_distribution(images)
            total = len(images)
            if total == 0:
                print(f"  [{kind}] {name}: 0 images")
            else:
                parts = [f"{p}:{c}" for p, c in sorted(dist.items(), key=lambda x: -x[1])]
                print(f"  [{kind}] {name}: {total} images — {', '.join(parts)}")
    print()
    print("queries_run:", result.get("queries_run", 0))


if __name__ == "__main__":
    asyncio.run(main())
