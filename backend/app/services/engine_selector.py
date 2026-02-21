"""
Engine Selection Logic for image search providers.
Picks the best providers for each entity based on entity_class, style_category,
engine affinity matrix, and per-book engine ratings.
"""
from app.services.ontology_constants import ENTITY_PARENT

ENGINE_AFFINITY: dict[str, dict[str, float]] = {
    # Human variants
    "human|fiction":               {"unsplash": 10, "pexels": 9},
    "human|romance":               {"unsplash": 10, "pexels": 9},
    "human|thriller":              {"unsplash": 9,  "pexels": 8, "serpapi": 6},
    "human|historical":            {"wikimedia": 10, "unsplash": 6},
    "human|adventure":             {"unsplash": 9, "pexels": 8},
    "human|mystery":               {"unsplash": 9, "pexels": 7, "serpapi": 6},
    "human_supernatural|fantasy":  {"pixabay": 9, "deviantart": 8, "unsplash": 5},
    "human_enhanced|sci-fi":       {"pixabay": 9, "serpapi": 7},
    "human_hybrid|fantasy":        {"deviantart": 10, "pixabay": 8},
    # Mechanical & Digital
    "android|sci-fi":              {"pixabay": 10, "deviantart": 9, "serpapi": 7},
    "android|cyberpunk":           {"pixabay": 10, "deviantart": 10, "serpapi": 8},
    "robot|sci-fi":                {"pixabay": 10, "deviantart": 8, "serpapi": 7},
    "AI|sci-fi":                   {"pixabay": 9, "openverse": 7, "serpapi": 8},
    "AI|cyberpunk":                {"pixabay": 10, "deviantart": 9},
    "cyborg|sci-fi":               {"pixabay": 9, "deviantart": 9, "serpapi": 7},
    "construct|fantasy":           {"deviantart": 10, "pixabay": 8},
    "golem|fantasy":               {"deviantart": 10, "pixabay": 8},
    # Divine & Cosmic
    "deity|fantasy":               {"deviantart": 10, "pixabay": 9},
    "deity|mythology":             {"wikimedia": 8, "deviantart": 9, "pixabay": 8},
    "demigod|fantasy":             {"deviantart": 10, "pixabay": 9},
    "angel|fantasy":               {"deviantart": 9, "pixabay": 8, "unsplash": 5},
    "demon|fantasy":               {"deviantart": 10, "pixabay": 9},
    "cosmic_entity|sci-fi":        {"deviantart": 10, "pixabay": 8, "serpapi": 6},
    "elemental|fantasy":           {"deviantart": 9, "pixabay": 9, "unsplash": 4},
    # Spirits & Undead
    "spirit|fantasy":              {"deviantart": 9, "pixabay": 8},
    "spirit|folklore":             {"wikimedia": 7, "deviantart": 8, "pixabay": 7},
    "ghost|horror":                {"deviantart": 9, "pixabay": 8, "serpapi": 6},
    "undead|fantasy":              {"deviantart": 10, "pixabay": 9},
    "undead|horror":               {"deviantart": 9, "serpapi": 8},
    # Fae & Mythical
    "fae|fantasy":                 {"deviantart": 10, "pixabay": 9},
    "mythical_beast|fantasy":      {"deviantart": 10, "pixabay": 9},
    "folkloric|fantasy":           {"deviantart": 9, "pixabay": 8, "wikimedia": 5},
    "folkloric|folklore":          {"wikimedia": 8, "deviantart": 8, "pixabay": 7},
    "trickster|fantasy":           {"deviantart": 9, "pixabay": 8},
    # Animal-based
    "animal|fiction":              {"unsplash": 10, "pexels": 8},
    "animal|adventure":            {"unsplash": 9, "pixabay": 7},
    "anthropomorphic_animal|fantasy": {"deviantart": 10, "pixabay": 9},
    "beast|fantasy":               {"deviantart": 10, "pixabay": 9},
    "beast|horror":                {"deviantart": 9, "serpapi": 7},
    "chimera|fantasy":             {"deviantart": 10, "pixabay": 9},
    "shapeshifter|fantasy":        {"deviantart": 9, "pixabay": 8},
    # Alien & Unknown
    "alien|sci-fi":                {"deviantart": 10, "pixabay": 9, "serpapi": 7},
    "alien_humanoid|sci-fi":       {"deviantart": 9, "pixabay": 8, "serpapi": 7},
    "hivemind|sci-fi":             {"deviantart": 9, "pixabay": 8},
    "eldritch|horror":             {"deviantart": 10, "pixabay": 8, "serpapi": 6},
    # Locations
    "location|fiction":            {"unsplash": 10, "pexels": 8},
    "location|romance":            {"unsplash": 10, "pexels": 9},
    "location|sci-fi":             {"pixabay": 9, "unsplash": 7, "serpapi": 6},
    "location|cyberpunk":          {"pixabay": 10, "deviantart": 8, "serpapi": 7},
    "location|fantasy":            {"deviantart": 9, "pixabay": 8, "unsplash": 6},
    "location|horror":             {"pixabay": 8, "deviantart": 8, "serpapi": 6},
    "location|historical":         {"wikimedia": 10, "unsplash": 6},
    "location|folklore":           {"wikimedia": 8, "pixabay": 7, "unsplash": 5},
    "location|thriller":           {"unsplash": 8, "pexels": 7, "serpapi": 6},
    "location|adventure":          {"unsplash": 9, "pixabay": 7, "pexels": 7},
    "location|mystery":            {"unsplash": 8, "pexels": 7, "pixabay": 6},
}

_DEFAULT_SCORES: dict[str, float] = {"unsplash": 7.0, "serpapi": 5.0}


def _apply_ratings(scores: dict[str, float], engine_ratings: dict[str, int]) -> dict[str, float]:
    """Apply engine rating multiplier to affinity scores."""
    result: dict[str, float] = {}
    for provider, base_score in scores.items():
        net = engine_ratings.get(provider, 0)
        net_clamped = max(-5, min(10, net))
        result[provider] = base_score * (1 + 0.1 * net_clamped)
    return result


def select_engines(
    entity_class: str,
    entity_type: str,
    style_category: str,
    available_providers: list[str],
    engine_ratings: dict[str, int],
    top_n: int = 2,
) -> list[str]:
    """
    Select the best providers for an entity using tiered fallback:
    1. Exact key: "entity_class|style_category" (or "location|style_category" for locations)
    2. Parent class: ENTITY_PARENT[entity_class] + "|" + style_category
    3. Generic: "location|style_category" or "human|style_category"
    4. Hardcoded default: unsplash + serpapi

    engine_ratings modifies scores: final = affinity * (1 + 0.1 * clamp(net, -5, 10))

    Returns list of up to top_n provider names (only from available_providers).
    """
    if entity_type == "location":
        primary_key = f"location|{style_category}"
    else:
        primary_key = f"{entity_class}|{style_category}"

    # Tier 1: exact match
    scores = ENGINE_AFFINITY.get(primary_key)

    # Tier 2: parent class fallback
    if scores is None and entity_type != "location":
        parent = ENTITY_PARENT.get(entity_class, "")
        if parent:
            parent_key = f"{parent}|{style_category}"
            scores = ENGINE_AFFINITY.get(parent_key)
            # Walk up the parent chain one more level if still no match
            if scores is None:
                grandparent = ENTITY_PARENT.get(parent, "")
                if grandparent:
                    scores = ENGINE_AFFINITY.get(f"{grandparent}|{style_category}")

    # Tier 3: generic style fallback
    if scores is None:
        if entity_type == "location":
            scores = ENGINE_AFFINITY.get(f"location|fiction")
        else:
            scores = ENGINE_AFFINITY.get(f"human|{style_category}") or ENGINE_AFFINITY.get("human|fiction")

    # Tier 4: hardcoded default
    if scores is None:
        scores = dict(_DEFAULT_SCORES)

    # Apply engine rating modifier
    adjusted = _apply_ratings(scores, engine_ratings)

    # Filter to available providers, sort by adjusted score descending
    ranked = sorted(
        [(p, s) for p, s in adjusted.items() if p in available_providers],
        key=lambda x: x[1],
        reverse=True,
    )

    # If we don't have enough from affinity, pad with whatever is available
    selected = [p for p, _ in ranked[:top_n]]
    if len(selected) < top_n:
        for p in available_providers:
            if p not in selected:
                selected.append(p)
            if len(selected) >= top_n:
                break

    return selected
