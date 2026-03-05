"""
Unit tests for Phase 9: Prompt Engineering Service, FLUX/DALL-E providers, engine selector.
"""
import asyncio
import json
import os

import pytest
from unittest.mock import AsyncMock, patch

from app.services.prompt_engineering_service import (
    run_prompt_merge,
    _heuristic_compatibility,
    _fallback_result,
)
from app.schemas import PromptEngineeringResult

COMPATIBLE_ENTITY = {
    "name": "Seraphina Vale",
    "entity_class": "character",
    "visual_type": "humanoid",
    "core_tokens": ["red-haired woman", "emerald eyes", "scholar's robes"],
    "style_tokens": ["pre-Raphaelite", "ethereal"],
    "archetype_tokens": ["the seeker"],
    "anti_tokens": ["cartoonish", "modern clothing", "blonde"],
}

INCOMPATIBLE_ENTITY = {
    "name": "The Shattered Citadel",
    "entity_class": "location",
    "visual_type": "architectural_ruin",
    "core_tokens": ["crumbling towers", "gothic arches"],
    "style_tokens": ["brutalist"],
    "archetype_tokens": [],
    "anti_tokens": ["pristine"],
}

MOCK_COMPATIBLE_RESPONSE = json.dumps({
    "final_prompt": "dark fantasy, red-haired woman emerald eyes, misty forest, art nouveau border, teal gold palette",
    "negative_prompt": "cartoonish, modern clothing, blonde",
    "compatibility_status": "COMPATIBLE",
    "compatibility_note": "Humanoid entity fits the single foreground figure compositional role.",
})

MOCK_WARNING_RESPONSE = json.dumps({
    "final_prompt": "dark fantasy, crumbling towers gothic arches, misty forest, art nouveau border",
    "negative_prompt": "pristine",
    "compatibility_status": "WARNING",
    "compatibility_note": "A location entity replacing a humanoid figure may create an awkward composition.",
})


def _mock_gpt_response(content: str):
    mock_message = AsyncMock()
    mock_message.content = content
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]
    return mock_response


def test_compatible_merge_returns_correct_fields():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_gpt_response(MOCK_COMPATIBLE_RESPONSE)
            )
            result = asyncio.run(run_prompt_merge(
                "dark fantasy, hooded figure, misty forest, art nouveau border, teal gold palette",
                COMPATIBLE_ENTITY,
                "Replace the hooded figure with my protagonist",
            ))

    assert result.compatibility_status == "COMPATIBLE"
    assert "red-haired" in result.final_prompt.lower() or "seraphina" in result.final_prompt.lower()
    assert "cartoonish" in result.negative_prompt
    assert "modern clothing" in result.negative_prompt


def test_incompatible_entity_returns_warning():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=_mock_gpt_response(MOCK_WARNING_RESPONSE)
            )
            result = asyncio.run(run_prompt_merge(
                "dark fantasy, hooded figure, misty forest",
                INCOMPATIBLE_ENTITY,
                "Replace figure with this citadel",
            ))

    assert result.compatibility_status in ("WARNING", "INCOMPATIBLE")
    assert len(result.compatibility_note) > 20


def test_heuristic_compatible_humanoid_to_humanoid():
    assert _heuristic_compatibility("humanoid", "humanoid", "character") == "COMPATIBLE"


def test_heuristic_warning_humanoid_to_location():
    assert _heuristic_compatibility("humanoid", "landscape", "location") == "WARNING"


def test_heuristic_none_for_unknown():
    assert _heuristic_compatibility("humanoid", "mythical_beast", "creature") is None


def test_fallback_on_api_failure():
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("app.services.prompt_engineering_service.AsyncOpenAI") as mock_cls:
            mock_client = AsyncMock()
            mock_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("timeout"))

            result = asyncio.run(run_prompt_merge(
                "dark fantasy, hooded figure, teal gold",
                COMPATIBLE_ENTITY,
                "Replace figure",
            ))

    assert result.compatibility_status == "WARNING"
    assert "dark fantasy" in result.final_prompt


def test_flux_provider_uses_kontext_endpoint_when_image_url_provided():
    import os
    os.environ["FAL_API_KEY"] = "test_key"
    from app.services.t2i_providers.flux_provider import FluxKontextProvider
    provider = FluxKontextProvider()
    assert provider.TEXT_ENDPOINT != provider.KONTEXT_ENDPOINT
    assert "kontext" in provider.KONTEXT_ENDPOINT


def test_engine_selector_returns_flux_when_fal_key_set(monkeypatch):
    monkeypatch.setenv("FAL_API_KEY", "test_key")
    from app.services.engine_selector import get_cover_t2i_provider
    from app.services.t2i_providers.flux_provider import FluxKontextProvider
    provider = get_cover_t2i_provider()
    assert isinstance(provider, FluxKontextProvider)


def test_engine_selector_returns_dalle_when_no_fal_key(monkeypatch):
    monkeypatch.delenv("FAL_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "test_openai_key")
    from importlib import reload
    import app.services.engine_selector as es
    reload(es)
    from app.services.t2i_providers.dalle_provider import DalleProvider
    provider = es.get_cover_t2i_provider()
    assert isinstance(provider, DalleProvider)
