"""Settings and provider status API."""
from fastapi import APIRouter

from app.services.providers import ALL_PROVIDERS

router = APIRouter()

# Display labels for provider names
PROVIDER_LABELS: dict[str, str] = {
    "unsplash": "Unsplash",
    "serpapi": "SerpAPI",
    "pexels": "Pexels",
    "pixabay": "Pixabay",
    "openverse": "Openverse",
    "wikimedia": "Wikimedia",
    "deviantart": "DeviantArt",
}


@router.get("/settings/providers")
def get_providers_status():
    """
    Return list of reference image search providers with name, label, and availability.
    Used by the Settings page to show checkboxes (default: all available enabled).
    """
    result = []
    for name, provider in ALL_PROVIDERS.items():
        result.append({
            "name": name,
            "label": PROVIDER_LABELS.get(name, name),
            "available": provider.is_available(),
        })
    return {"providers": result}
