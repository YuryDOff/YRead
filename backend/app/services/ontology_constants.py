"""
Ontology constants shared by ontology_service.py and engine_selector.py.
Defines the closed entity class taxonomy (30+ classes), parent hierarchy, and non-human set.
"""

ENTITY_CLASSES = [
    # Human variants
    "human", "human_supernatural", "human_transformed", "human_enhanced",
    "clone", "human_hybrid",
    # Mechanical & Digital
    "android", "robot", "AI", "cyborg", "golem", "construct",
    # Divine & Cosmic
    "deity", "demigod", "angel", "demon", "cosmic_entity", "elemental",
    # Spirits & Undead
    "spirit", "ghost", "undead", "shade",
    # Fae & Mythical
    "fae", "mythical_beast", "folkloric", "trickster",
    # Animal-based
    "animal", "anthropomorphic_animal", "beast", "chimera", "shapeshifter",
    # Plant & Object
    "plant_being", "animated_object",
    # Alien & Unknown
    "alien", "alien_humanoid", "hivemind", "eldritch",
]

# Parent class hierarchy for tiered fallback in engine_selector
ENTITY_PARENT: dict[str, str] = {
    "human_supernatural": "human",
    "human_transformed":  "human",
    "human_enhanced":     "human",
    "clone":              "human",
    "human_hybrid":       "human_supernatural",
    "cyborg":             "android",
    "android":            "robot",
    "golem":              "construct",
    "animated_object":    "construct",
    "plant_being":        "construct",
    "ghost":              "spirit",
    "shade":              "spirit",
    "demigod":            "deity",
    "angel":              "deity",
    "demon":              "deity",
    "cosmic_entity":      "deity",
    "elemental":          "spirit",
    "fae":                "mythical_beast",
    "folkloric":          "mythical_beast",
    "trickster":          "mythical_beast",
    "beast":              "mythical_beast",
    "chimera":            "mythical_beast",
    "shapeshifter":       "mythical_beast",
    "anthropomorphic_animal": "animal",
    "alien_humanoid":     "alien",
    "hivemind":           "alien",
    "eldritch":           "cosmic_entity",
}

# Classes that require anti_human_override = True (non-human entities)
NON_HUMAN_CLASSES: set[str] = set(ENTITY_CLASSES) - {
    "human", "human_supernatural", "human_transformed",
    "human_enhanced", "clone", "human_hybrid",
    "demigod",  # demigods often have human visual form
}
