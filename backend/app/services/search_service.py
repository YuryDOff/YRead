"""Reference image search service using SerpAPI / Bing Search."""
import logging
import os
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

SEARCH_API_KEY = os.getenv("SEARCH_API_KEY", "")

# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------


def _build_character_queries(
    name: str,
    description: str,
    book_title: Optional[str] = None,
    author: Optional[str] = None,
    is_well_known: bool = False,
) -> list[str]:
    """Build 2-3 search queries for a character."""
    queries: list[str] = []
    if is_well_known and book_title:
        queries.append(f"{name} {book_title}")
        if author:
            queries.append(f"{name} {book_title} {author}")
        queries.append(f"{name} illustration")
    else:
        short_desc = description[:80] if description else name
        queries.append(f"{short_desc} person portrait")
        queries.append(f"{short_desc} character illustration")
    return queries[:3]


def _build_location_queries(
    name: str,
    description: str,
    book_title: Optional[str] = None,
    is_well_known: bool = False,
) -> list[str]:
    """Build 2-3 search queries for a location."""
    queries: list[str] = []
    if is_well_known and book_title:
        queries.append(f"{name} {book_title}")
        queries.append(f"{name} illustration")
    else:
        short_desc = description[:80] if description else name
        queries.append(f"{short_desc} landscape scenery")
        queries.append(f"{short_desc} interior illustration")
    return queries[:3]


# ---------------------------------------------------------------------------
# SerpAPI image search
# ---------------------------------------------------------------------------


async def _search_images_serpapi(query: str, num: int = 5) -> list[dict]:
    """
    Search images via SerpAPI Google Images endpoint.
    Returns list of {url, width, height, source}.
    """
    if not SEARCH_API_KEY:
        logger.warning("SEARCH_API_KEY not set; returning empty results")
        return []

    params = {
        "engine": "google_images",
        "q": query,
        "api_key": SEARCH_API_KEY,
        "safe": "active",
        "num": num,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get("https://serpapi.com/search.json", params=params)
        if resp.status_code != 200:
            logger.error("SerpAPI returned %s for query: %s", resp.status_code, query)
            return []
        data = resp.json()

    results: list[dict] = []
    for img in data.get("images_results", [])[:num]:
        original = img.get("original", "")
        if not original:
            continue
        results.append({
            "url": original,
            "width": img.get("original_width", 0),
            "height": img.get("original_height", 0),
            "source": img.get("source", ""),
            "thumbnail": img.get("thumbnail", ""),
        })
    return results


# ---------------------------------------------------------------------------
# Deduplicate & filter
# ---------------------------------------------------------------------------


def _filter_and_dedupe(
    images: list[dict], min_size: int = 512, max_results: int = 3
) -> list[dict]:
    """Filter by minimum size and deduplicate by domain."""
    seen_domains: set[str] = set()
    filtered: list[dict] = []

    for img in images:
        w = img.get("width", 0)
        h = img.get("height", 0)
        if w < min_size and h < min_size:
            continue

        # Simple domain-based dedup
        url = img.get("url", "")
        domain = url.split("/")[2] if url.count("/") >= 2 else url
        if domain in seen_domains:
            continue
        seen_domains.add(domain)
        filtered.append(img)

        if len(filtered) >= max_results:
            break

    return filtered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search_character_references(
    name: str,
    description: str,
    book_title: Optional[str] = None,
    author: Optional[str] = None,
    is_well_known: bool = False,
) -> list[dict]:
    """
    Search reference images for a character.
    Returns up to 3 diverse image results.
    """
    queries = _build_character_queries(
        name, description, book_title, author, is_well_known
    )
    all_images: list[dict] = []
    for q in queries:
        results = await _search_images_serpapi(q)
        all_images.extend(results)

    return _filter_and_dedupe(all_images, max_results=3)


async def search_location_references(
    name: str,
    description: str,
    book_title: Optional[str] = None,
    is_well_known: bool = False,
) -> list[dict]:
    """
    Search reference images for a location.
    Returns up to 3 diverse image results.
    """
    queries = _build_location_queries(name, description, book_title, is_well_known)
    all_images: list[dict] = []
    for q in queries:
        results = await _search_images_serpapi(q)
        all_images.extend(results)

    return _filter_and_dedupe(all_images, max_results=3)


async def search_all_references(
    characters: list[dict],
    locations: list[dict],
    book_title: Optional[str] = None,
    author: Optional[str] = None,
    is_well_known: bool = False,
) -> dict:
    """
    Search reference images for all characters and locations.

    Returns:
    {
        "characters": {name: [image_results]},
        "locations": {name: [image_results]}
    }
    """
    char_refs: dict[str, list[dict]] = {}
    for ch in characters:
        name = ch.get("name", "")
        desc = ch.get("physical_description", "")
        images = await search_character_references(
            name, desc, book_title, author, is_well_known
        )
        char_refs[name] = images

    loc_refs: dict[str, list[dict]] = {}
    for loc in locations:
        name = loc.get("name", "")
        desc = loc.get("visual_description", "")
        images = await search_location_references(
            name, desc, book_title, is_well_known
        )
        loc_refs[name] = images

    return {"characters": char_refs, "locations": loc_refs}
