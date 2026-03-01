"""
Genre-based default entity activations for analysis (Phase 4).
Used when workflow_type is not full/full_book to decide which entity types to analyze.
"""

GENRE_DEFAULT_ACTIVATIONS = {
    "fantasy":           ["cover", "characters", "locations", "artefacts"],
    "sci_fi":            ["cover", "characters", "locations"],
    "childrens":         ["cover", "characters"],
    "romance":           ["cover", "characters"],
    "thriller":          ["cover"],
    "mystery":           ["cover"],
    "literary_fiction":  ["cover"],
    "historical_fiction": ["cover", "locations", "artefacts"],
    "default":           ["cover"],
}


def get_default_activations(genre: str, workflow_type: str) -> list[str]:
    """
    Return default entity_types to activate for analysis.
    For full_book/full workflow always return all four. Otherwise use genre map.
    """
    if workflow_type in ("full_book", "full"):
        return ["cover", "characters", "locations", "artefacts"]
    return GENRE_DEFAULT_ACTIVATIONS.get(genre, GENRE_DEFAULT_ACTIVATIONS["default"])
