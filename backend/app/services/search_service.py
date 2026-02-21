"""Reference image search service with multi-provider engine selection and query diversification."""
import json as _json
import logging
from typing import Literal, Optional

from sqlalchemy.orm import Session

from app import crud
from app.services.providers import (
    ALL_PROVIDERS,
    UnsplashProvider,
    SerpApiProvider,
    PexelsProvider,
    PixabayProvider,
    OpenverseProvider,
    WikimediaProvider,
    DeviantArtProvider,
)
from app.services.engine_selector import select_engines

logger = logging.getLogger(__name__)

CHARACTER_PLACEHOLDER = "/static/placeholders/character.svg"
LOCATION_PLACEHOLDER = "/static/placeholders/location.svg"

# ---------------------------------------------------------------------------
# Resolve entity chunks & visual tokens
# ---------------------------------------------------------------------------


def _get_visual_tokens_for_entity(
    db: Session,
    entity_id: int,
    entity_type: str,
) -> dict:
    """
    Priority: entity_visual_tokens_json (entity-level, built from ontology) →
    fallback: chunk-based aggregation (existing behaviour, unchanged).

    Returns {core_tokens, style_tokens, archetype_tokens, anti_tokens}.
    """
    import json as _json

    # --- Priority: entity-level tokens (new) ---
    if entity_type == "character":
        entity = crud.get_character(db, entity_id)
    else:
        entity = crud.get_location(db, entity_id)

    if entity and getattr(entity, "entity_visual_tokens_json", None):
        try:
            tokens = _json.loads(entity.entity_visual_tokens_json)
            if tokens and tokens.get("core_tokens"):
                return tokens
        except (ValueError, TypeError):
            pass

    # --- Fallback: chunk-based aggregation (original behaviour, unchanged) ---
    if entity_type == "character":
        chunks = crud.get_chunks_for_character(db, entity_id)
    else:
        chunks = crud.get_chunks_for_location(db, entity_id)

    core_tokens: list[str] = []
    style_tokens: list[str] = []
    seen_core: set[str] = set()
    seen_style: set[str] = set()

    for chunk in chunks:
        data = crud.get_chunk_visual_analysis(db, chunk.id)
        if not data:
            continue

        vt = data.get("visual_tokens", {})
        for t in vt.get("core_tokens", [])[:4]:
            t_lower = t.lower().strip()
            if t_lower and t_lower not in seen_core:
                seen_core.add(t_lower)
                core_tokens.append(t)

        for t in vt.get("style_tokens", [])[:2]:
            t_lower = t.lower().strip()
            if t_lower and t_lower not in seen_style:
                seen_style.add(t_lower)
                style_tokens.append(t)

        if len(core_tokens) >= 8 and len(style_tokens) >= 4:
            break

    return {
        "core_tokens": core_tokens[:8],
        "style_tokens": style_tokens[:4],
        "archetype_tokens": [],
        "anti_tokens": [],
    }


# ---------------------------------------------------------------------------
# Query construction
# ---------------------------------------------------------------------------


def _character_suffix(visual_type: Optional[str]) -> str:
    """Suffix for character queries: visual_type drives man/woman/animal/AI/alien."""
    if not visual_type:
        return " person portrait"
    vt = (visual_type or "").strip().lower()
    if vt in ("man", "men"):
        return " man portrait"
    if vt in ("woman", "women"):
        return " woman portrait"
    if vt == "animal":
        return " animal portrait"
    if vt == "ai":
        return " AI robot humanoid"
    if vt == "alien":
        return " alien humanoid"
    if vt == "creature":
        return " creature portrait"
    return " person portrait"


def _build_queries(
    entity_type: str,
    name: str,
    description: str,
    book_info: dict,
    visual_tokens: dict,
    *,
    visual_type: Optional[str] = None,
    is_well_known_entity: bool = False,
    canonical_search_name: Optional[str] = None,
    search_visual_analog: Optional[str] = None,
) -> list[str]:
    """
    Build search queries: well-known entity name first, then visual_type-based suffix
    for characters, then visual_analog/tokens/description for fictional entities.
    """
    queries: list[str] = []
    core = visual_tokens.get("core_tokens", [])
    style = visual_tokens.get("style_tokens", [])

    if entity_type == "character":
        suffix = _character_suffix(visual_type)
    else:
        suffix = " landscape"

    # Well-known entity: canonical name + suffix as first query
    if is_well_known_entity and canonical_search_name:
        canonical = (canonical_search_name or "").strip()
        if canonical:
            queries.append(f"{canonical}{suffix}".strip())

    # Descriptive query: prefer search_visual_analog for fictional, else tokens, else description
    analog = (search_visual_analog or "").strip()
    if analog:
        parts = analog[:120].split()
        base = " ".join(parts[:12]) if len(parts) > 12 else analog[:120]
        queries.append(f"{base}{suffix}".strip())
    elif core or style:
        parts = list(core[:4]) + list(style[:2])
        queries.append(f"{' '.join(parts)}{suffix}".strip())
    else:
        short_desc = (description or "")[:80]
        if short_desc:
            queries.append(f"{short_desc}{suffix}".strip())
        elif not queries:
            queries.append(suffix.strip())

    # Book context for well-known books (style/context only)
    if book_info.get("is_well_known"):
        title = book_info.get("well_known_book_title") or book_info.get("title", "")
        author = book_info.get("author", "")
        if title or author:
            parts = []
            if title:
                parts.append(title)
            if author:
                parts.append(author)
            if entity_type == "character":
                parts.append("character")
            parts.append("illustration")
            queries.append(" ".join(parts))

    # Append book style to every query so query_text in search_queries reflects user selection
    style_category = (book_info.get("style_category") or "").strip()
    if style_category:
        queries = [f"{q} {style_category}".strip() for q in queries]

    return queries[:3]


# ---------------------------------------------------------------------------
# Query diversification (new — 4–5 semantically distinct queries)
# ---------------------------------------------------------------------------


def _build_queries_diversified(
    entity_type: str,
    description: str,
    book_info: dict,
    entity_visual_tokens: dict,
    ontology: dict,
    *,
    visual_type: Optional[str] = None,
    is_well_known_entity: bool = False,
    canonical_search_name: Optional[str] = None,
    search_visual_analog: Optional[str] = None,
) -> list[str]:
    """
    Build 4–5 semantically distinct search queries using ontology + visual tokens.

    Query 1: Ontological archetype   — ontology.search_archetype + style_category
    Query 2: Visual markers          — top visual_markers + non-human suffix if applicable
    Query 3: Canonical / analog      — canonical name or visual analog phrase
    Query 4: Core + archetype tokens — entity_visual_tokens core + archetype
    Query 5: Adaptation query        — film/TV stills for well-known books (→ SerpAPI always)
    """
    style_category = (book_info.get("style_category") or "fiction").strip()
    is_well_known_book = bool(book_info.get("is_well_known"))
    known_adaptations: list[str] = book_info.get("known_adaptations") or []
    anti_human = bool(ontology.get("anti_human_override", False))
    search_archetype = (ontology.get("search_archetype") or "").strip()
    visual_markers: list[str] = ontology.get("visual_markers") or []
    entity_class = (ontology.get("entity_class") or "human").lower()

    core_tokens: list[str] = entity_visual_tokens.get("core_tokens") or []
    style_tokens: list[str] = entity_visual_tokens.get("style_tokens") or []
    archetype_tokens: list[str] = entity_visual_tokens.get("archetype_tokens") or []
    anti_tokens: list[str] = entity_visual_tokens.get("anti_tokens") or []

    # Suffix only for human characters
    if entity_type == "character" and not anti_human:
        human_suffix = _character_suffix(visual_type)
    else:
        human_suffix = ""

    queries: list[str] = []
    seen: set[str] = set()

    def _add(q: str) -> None:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            queries.append(q)

    # Q1: Ontological archetype + style
    if anti_human and search_archetype:
        _add(f"{search_archetype} {style_category}".strip())
    elif canonical_search_name and is_well_known_entity:
        _add(f"{canonical_search_name}{human_suffix} {style_category}".strip())
    elif description:
        short_desc = description[:80].strip()
        _add(f"{short_desc}{human_suffix}".strip())

    # Q2: Visual markers
    if visual_markers:
        markers_str = " ".join(vm for vm in visual_markers[:4])
        if anti_human:
            _add(f"{markers_str} {entity_class}".strip())
        else:
            _add(f"{markers_str}{human_suffix}".strip())

    # Q3: Canonical name or visual analog
    analog = (search_visual_analog or "").strip()
    canonical = (canonical_search_name or "").strip()
    if analog:
        _add(f"{analog[:100]}{human_suffix}".strip())
    elif canonical and is_well_known_entity:
        _add(f"{canonical} {entity_class} illustration".strip())

    # Q4: Core tokens + archetype tokens
    if core_tokens or archetype_tokens:
        parts = list(core_tokens[:3]) + list(archetype_tokens[:2])
        if parts:
            tokens_str = " ".join(parts)
            _add(f"{tokens_str} {style_category}".strip())

    # Q5: Adaptation queries for well-known books (forced through SerpAPI)
    if is_well_known_book and known_adaptations:
        title_label = book_info.get("well_known_book_title") or book_info.get("title", "")
        for adaptation in known_adaptations[:2]:
            if entity_type == "character":
                _add(f"{adaptation} {entity_type} still")
            else:
                _add(f"{adaptation} location still")

    # Q6: Book illustration query for well-known books
    if is_well_known_book:
        title = book_info.get("well_known_book_title") or book_info.get("title", "")
        author = book_info.get("author", "")
        parts = [p for p in [title, author] if p]
        if entity_type == "character":
            parts.append("character illustration")
        else:
            parts.append("book illustration")
        if parts:
            _add(" ".join(parts))

    # Ensure at least 2 queries by falling back to description
    if len(queries) < 2 and description:
        short_desc = description[:60].strip()
        _add(f"{short_desc} {style_category}".strip())

    return queries[:6]  # cap at 6


def _is_adaptation_query(query: str, known_adaptations: list[str]) -> bool:
    """Return True if the query is an adaptation-specific film/TV still query."""
    q_lower = query.lower()
    return (
        " still" in q_lower
        and any(
            any(word in q_lower for word in adapt.lower().split())
            for adapt in (known_adaptations or [])
        )
    )


# ---------------------------------------------------------------------------
# Deduplicate & filter
# ---------------------------------------------------------------------------


def _filter_and_dedupe(
    images: list[dict],
    min_size: int = 512,
    max_results: int = 10,
    prefer_unsplash: bool = True,
) -> list[dict]:
    """Filter by min size, dedupe by URL; prefer Unsplash when domain duplicate."""
    seen_urls: set[str] = set()
    seen_domains: set[str] = set()
    filtered: list[dict] = []

    for img in images:
        url = img.get("url", "")
        if not url or url in seen_urls:
            continue

        w = img.get("width", 0)
        h = img.get("height", 0)
        if w < min_size and h < min_size:
            continue

        domain = url.split("/")[2] if url.count("/") >= 2 else url
        if domain in seen_domains:
            if prefer_unsplash and img.get("provider") == "unsplash":
                filtered = [x for x in filtered if x.get("url", "").split("/")[2] != domain]
                seen_domains.discard(domain)
            else:
                continue

        seen_urls.add(url)
        seen_domains.add(domain)
        filtered.append(img)

        if len(filtered) >= max_results:
            break

    return filtered


# ---------------------------------------------------------------------------
# Save query to DB
# ---------------------------------------------------------------------------


def _save_query(
    db: Optional[Session],
    book_id: int,
    entity_type: str,
    entity_name: str,
    query_text: str,
    results_count: int,
    provider: str,
) -> None:
    if db is None:
        return
    crud.create_search_query(
        db,
        book_id=book_id,
        entity_type=entity_type,
        entity_name=entity_name,
        query_text=query_text,
        results_count=results_count,
        provider=provider,
    )


# ---------------------------------------------------------------------------
# assign_placeholder
# ---------------------------------------------------------------------------


def assign_placeholder(db: Session, entity_id: int, entity_type: str) -> None:
    """Assign placeholder image URL to non-main entity."""
    url = CHARACTER_PLACEHOLDER if entity_type == "character" else LOCATION_PLACEHOLDER
    if entity_type == "character":
        crud.update_character(db, entity_id, reference_image_url=url)
    else:
        crud.update_location(db, entity_id, reference_image_url=url)


# ---------------------------------------------------------------------------
# Proposed search queries (for user review before running search)
# ---------------------------------------------------------------------------


def get_proposed_search_queries(
    book_id: int,
    db: Session,
    main_only: bool = True,
) -> dict:
    """
    Build proposed query_text list for each main (or all) character/location.
    Does not run search. For use by GET proposed-search-queries and frontend review.
    """
    book = crud.get_book(db, book_id)
    if not book:
        return {"characters": [], "locations": []}

    vb = crud.get_visual_bible(db, book_id)
    style_category = (vb.style_category if vb and vb.style_category else None) or "fiction"

    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)
    if main_only:
        characters = [c for c in characters if c.is_main]
        locations = [loc for loc in locations if loc.is_main]

    known_adaptations: list[str] = []
    if getattr(book, "known_adaptations_json", None):
        try:
            known_adaptations = _json.loads(book.known_adaptations_json) or []
        except (ValueError, TypeError):
            known_adaptations = []

    book_info = {
        "title": book.title,
        "author": book.author,
        "is_well_known": bool(book.is_well_known),
        "well_known_book_title": getattr(book, "well_known_book_title", None) or None,
        "similar_book_title": getattr(book, "similar_book_title", None) or None,
        "style_category": style_category,
        "known_adaptations": known_adaptations,
    }

    char_list: list[dict] = []
    for c in characters:
        desc = c.physical_description or ""
        stored = crud.get_latest_stored_queries_for_entity(db, book_id, "character", c.name)
        if stored:
            queries = stored
        else:
            visual_tokens = _get_visual_tokens_for_entity(db, c.id, "character")
            ontology = {}
            if getattr(c, "ontology_json", None):
                try:
                    ontology = _json.loads(c.ontology_json) or {}
                except (ValueError, TypeError):
                    ontology = {}
            queries = _build_queries_diversified(
                "character",
                desc,
                book_info,
                visual_tokens,
                ontology,
                visual_type=getattr(c, "visual_type", None),
                is_well_known_entity=bool(getattr(c, "is_well_known_entity", 0)),
                canonical_search_name=getattr(c, "canonical_search_name", None),
                search_visual_analog=getattr(c, "search_visual_analog", None),
            ) or _build_queries(
                "character", c.name, desc, book_info, visual_tokens,
                visual_type=getattr(c, "visual_type", None),
                is_well_known_entity=bool(getattr(c, "is_well_known_entity", 0)),
                canonical_search_name=getattr(c, "canonical_search_name", None),
                search_visual_analog=getattr(c, "search_visual_analog", None),
            )
        char_list.append({
            "id": c.id,
            "name": c.name,
            "summary": desc or "",
            "visual_type": getattr(c, "visual_type", None),
            "is_well_known_entity": bool(getattr(c, "is_well_known_entity", 0)),
            "canonical_search_name": getattr(c, "canonical_search_name", None),
            "proposed_queries": queries,
            "text_to_image_prompt": getattr(c, "text_to_image_prompt", None) or "",
        })

    loc_list: list[dict] = []
    for loc in locations:
        desc = loc.visual_description or ""
        stored = crud.get_latest_stored_queries_for_entity(db, book_id, "location", loc.name)
        if stored:
            queries = stored
        else:
            visual_tokens = _get_visual_tokens_for_entity(db, loc.id, "location")
            ontology = {}
            if getattr(loc, "ontology_json", None):
                try:
                    ontology = _json.loads(loc.ontology_json) or {}
                except (ValueError, TypeError):
                    ontology = {}
            queries = _build_queries_diversified(
                "location",
                desc,
                book_info,
                visual_tokens,
                ontology,
                is_well_known_entity=bool(getattr(loc, "is_well_known_entity", 0)),
                canonical_search_name=getattr(loc, "canonical_search_name", None),
                search_visual_analog=getattr(loc, "search_visual_analog", None),
            ) or _build_queries(
                "location", loc.name, desc, book_info, visual_tokens,
                is_well_known_entity=bool(getattr(loc, "is_well_known_entity", 0)),
                canonical_search_name=getattr(loc, "canonical_search_name", None),
                search_visual_analog=getattr(loc, "search_visual_analog", None),
            )
        loc_list.append({
            "id": loc.id,
            "name": loc.name,
            "summary": desc or "",
            "is_well_known_entity": bool(getattr(loc, "is_well_known_entity", 0)),
            "canonical_search_name": getattr(loc, "canonical_search_name", None),
            "proposed_queries": queries,
            "text_to_image_prompt": getattr(loc, "text_to_image_prompt", None) or "",
        })

    # Include selected scenes (review/edit only — no T2I generation here)
    scenes = crud.get_scenes_by_book(db, book_id)
    scene_list: list[dict] = []
    for scene in scenes:
        if not getattr(scene, "is_selected", 1):
            continue
        t2i = None
        if getattr(scene, "t2i_prompt_json", None):
            try:
                t2i = _json.loads(scene.t2i_prompt_json)
            except (ValueError, TypeError):
                t2i = None
        scene_list.append({
            "id": scene.id,
            "title": scene.title,
            "title_display": getattr(scene, "title_display", None),
            "scene_type": scene.scene_type,
            "narrative_summary": scene.narrative_summary,
            "narrative_summary_display": getattr(scene, "narrative_summary_display", None),
            "scene_prompt_draft": scene.scene_prompt_draft,
            "t2i_prompt_json": t2i,
            "illustration_priority": scene.illustration_priority,
            "is_selected": bool(getattr(scene, "is_selected", 1)),
        })

    return {"characters": char_list, "locations": loc_list, "scenes": scene_list}


# ---------------------------------------------------------------------------
# Public API: search_references_for_book
# ---------------------------------------------------------------------------


async def _search_with_providers(
    query: str,
    content_type: str,
    providers: list,
    count: int = 15,
    *,
    force_serpapi: bool = False,
    serpapi: "SerpApiProvider | None" = None,
) -> tuple[list[dict], str]:
    """
    Search using the given list of provider instances.
    If force_serpapi=True, route to SerpAPI regardless of provider list.
    Returns (results, used_provider_name).
    """
    if force_serpapi and serpapi and serpapi.is_available():
        try:
            results = await serpapi.search(query, content_type, count=count)
            if results:
                return results, "serpapi"
        except Exception as e:
            logger.exception("SerpAPI (forced) search failed: %s", e)

    for provider in providers:
        if not provider.is_available():
            continue
        try:
            formatted_query = provider.format_query(query)
            results = await provider.search(formatted_query, content_type, count=count)
            if results:
                return results, provider.name
        except Exception as e:
            logger.exception("%s search failed: %s", provider.name, e)

    return [], "unknown"


async def search_references_for_book(
    book_id: int,
    search_all: bool = False,
    db: Optional[Session] = None,
    *,
    character_queries: Optional[dict[int, list[str]]] = None,
    location_queries: Optional[dict[int, list[str]]] = None,
    character_summaries: Optional[dict[int, dict]] = None,
    location_summaries: Optional[dict[int, dict]] = None,
    preferred_provider: Optional[str] = None,
    search_entity_types: Literal["characters", "locations", "both"] = "both",
    enabled_providers: Optional[list[str]] = None,
) -> dict:
    """
    Search reference images for book entities.
    When character_queries/location_queries are provided (entity id -> list of query strings),
    use those instead of _build_queries for that entity.
    When character_summaries/location_summaries are provided, update DB before search.

    Returns:
        {
            book_id, mode, characters: [{id, name, is_main, images, placeholder_assigned}],
            locations: [...],
            queries_run, provider_usage: {unsplash, serpapi}
        }
    """
    if character_summaries and db:
        for cid, data in character_summaries.items():
            crud.update_character(db, cid, **data)
    if location_summaries and db:
        for lid, data in location_summaries.items():
            crud.update_location(db, lid, **data)

    book = crud.get_book(db, book_id)
    if not book:
        return {"book_id": book_id, "mode": "main_only", "characters": [], "locations": [], "queries_run": 0, "provider_usage": {}}

    # Re-fetch so we have updated descriptions if summaries were applied
    characters = crud.get_characters_by_book(db, book_id)
    locations = crud.get_locations_by_book(db, book_id)

    main_only = not search_all
    if main_only:
        search_chars = [c for c in characters if c.is_main]
        placeholder_chars = [c for c in characters if not c.is_main]
        search_locs = [loc for loc in locations if loc.is_main]
        placeholder_locs = [loc for loc in locations if not loc.is_main]
    else:
        search_chars = list(characters)
        placeholder_chars = []
        search_locs = list(locations)
        placeholder_locs = []

    vb = crud.get_visual_bible(db, book_id) if db else None
    style_category = (vb.style_category if vb and vb.style_category else None) or "fiction"

    known_adaptations: list[str] = []
    if getattr(book, "known_adaptations_json", None):
        try:
            known_adaptations = _json.loads(book.known_adaptations_json) or []
        except (ValueError, TypeError):
            known_adaptations = []

    book_info = {
        "title": book.title,
        "author": book.author,
        "is_well_known": bool(book.is_well_known),
        "well_known_book_title": getattr(book, "well_known_book_title", None) or None,
        "similar_book_title": getattr(book, "similar_book_title", None) or None,
        "style_category": style_category,
        "known_adaptations": known_adaptations,
    }

    # Build available providers list and get engine ratings for this book
    available_provider_names = [name for name, p in ALL_PROVIDERS.items() if p.is_available()]
    if enabled_providers is not None and len(enabled_providers) > 0:
        available_provider_names = [n for n in available_provider_names if n in enabled_providers]
    if not available_provider_names:
        logger.warning("No image search providers available")

    engine_ratings: dict[str, int] = {}
    if db:
        try:
            engine_ratings = crud.get_engine_ratings(db, book_id)
        except Exception:
            engine_ratings = {}

    serpapi_instance = ALL_PROVIDERS.get("serpapi")

    queries_run = 0
    provider_usage: dict[str, int] = {name: 0 for name in ALL_PROVIDERS}
    search_characters = search_entity_types in ("both", "characters")
    search_locations = search_entity_types in ("both", "locations")

    def _get_queries_for_entity(entity, entity_type: str, user_overrides: dict) -> list[str]:
        if entity.id in user_overrides:
            return [q.strip() for q in user_overrides[entity.id] if q and str(q).strip()]
        visual_tokens = _get_visual_tokens_for_entity(db, entity.id, entity_type)
        desc = (entity.physical_description if entity_type == "character" else entity.visual_description) or ""
        ontology = {}
        if getattr(entity, "ontology_json", None):
            try:
                ontology = _json.loads(entity.ontology_json) or {}
            except (ValueError, TypeError):
                ontology = {}
        queries = _build_queries_diversified(
            entity_type, desc, book_info, visual_tokens, ontology,
            visual_type=getattr(entity, "visual_type", None) if entity_type == "character" else None,
            is_well_known_entity=bool(getattr(entity, "is_well_known_entity", 0)),
            canonical_search_name=getattr(entity, "canonical_search_name", None),
            search_visual_analog=getattr(entity, "search_visual_analog", None),
        )
        if not queries:
            queries = _build_queries(
                entity_type, entity.name, desc, book_info, visual_tokens,
                visual_type=getattr(entity, "visual_type", None) if entity_type == "character" else None,
                is_well_known_entity=bool(getattr(entity, "is_well_known_entity", 0)),
                canonical_search_name=getattr(entity, "canonical_search_name", None),
                search_visual_analog=getattr(entity, "search_visual_analog", None),
            )
        return queries

    def _get_providers_for_entity(entity, entity_type: str) -> list:
        """Select engine instances for this entity using engine_selector."""
        if preferred_provider and preferred_provider != "auto":
            p = ALL_PROVIDERS.get(preferred_provider)
            return [p] if p else []

        ontology = {}
        if getattr(entity, "ontology_json", None):
            try:
                ontology = _json.loads(entity.ontology_json) or {}
            except (ValueError, TypeError):
                ontology = {}
        entity_class = ontology.get("entity_class", "human" if entity_type == "character" else "location")
        provider_names = select_engines(
            entity_class=entity_class,
            entity_type=entity_type,
            style_category=style_category,
            available_providers=available_provider_names,
            engine_ratings=engine_ratings,
            top_n=2,
        )
        return [ALL_PROVIDERS[name] for name in provider_names if name in ALL_PROVIDERS]

    async def _search_entity(entity, entity_type: str, user_overrides: dict) -> tuple[dict, int]:
        queries = _get_queries_for_entity(entity, entity_type, user_overrides)
        providers = _get_providers_for_entity(entity, entity_type)

        all_images: list[dict] = []
        entity_name = entity.name
        local_queries_run = 0

        for q in queries:
            # Adaptation queries always go through SerpAPI
            force_serpapi = _is_adaptation_query(q, known_adaptations)
            results, used_provider = await _search_with_providers(
                q, entity_type, providers,
                force_serpapi=force_serpapi,
                serpapi=serpapi_instance,
            )
            if results:
                local_queries_run += 1
                provider_usage[used_provider] = provider_usage.get(used_provider, 0) + 1
                _save_query(db, book_id, entity_type, entity_name, q, len(results), used_provider)
                all_images.extend(results)

        filtered = _filter_and_dedupe(all_images, max_results=15)
        return {
            "id": entity.id,
            "name": entity.name,
            "is_main": bool(entity.is_main),
            "images": filtered,
            "placeholder_assigned": False,
        }, local_queries_run

    char_results: list[dict] = []
    user_char_queries = character_queries or {}
    if search_characters:
        for c in search_chars:
            result, q_count = await _search_entity(c, "character", user_char_queries)
            queries_run += q_count
            char_results.append(result)
        for c in placeholder_chars:
            if db:
                assign_placeholder(db, c.id, "character")
            char_results.append({"id": c.id, "name": c.name, "is_main": False, "images": [], "placeholder_assigned": True})
    else:
        for c in search_chars + placeholder_chars:
            if db:
                assign_placeholder(db, c.id, "character")
            char_results.append({"id": c.id, "name": c.name, "is_main": bool(c.is_main), "images": [], "placeholder_assigned": True})

    loc_results: list[dict] = []
    user_loc_queries = location_queries or {}
    if search_locations:
        for loc in search_locs:
            result, q_count = await _search_entity(loc, "location", user_loc_queries)
            queries_run += q_count
            loc_results.append(result)
        for loc in placeholder_locs:
            if db:
                assign_placeholder(db, loc.id, "location")
            loc_results.append({"id": loc.id, "name": loc.name, "is_main": False, "images": [], "placeholder_assigned": True})
    else:
        for loc in search_locs + placeholder_locs:
            if db:
                assign_placeholder(db, loc.id, "location")
            loc_results.append({"id": loc.id, "name": loc.name, "is_main": bool(loc.is_main), "images": [], "placeholder_assigned": True})

    mode = "all" if search_all else "main_only"
    return {
        "book_id": book_id,
        "mode": mode,
        "characters": char_results,
        "locations": loc_results,
        "queries_run": queries_run,
        "provider_usage": {k: v for k, v in provider_usage.items() if v > 0},
    }
