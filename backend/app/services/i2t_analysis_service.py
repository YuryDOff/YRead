"""I2T cover reference analysis via GPT-4o Vision."""
from __future__ import annotations

import json
import logging
import os
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import I2TAnalysisResult

logger = logging.getLogger(__name__)

COVER_EXTRACTION_SYSTEM_PROMPT = """Analyze this book cover and return JSON with style_template, composition_notes,
color_palette_extracted, style_tags, mood_keywords, lighting_description."""
ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT = """Analyze this illustration and return JSON with style_template, composition_notes,
color_palette_extracted, style_tags, mood_keywords, lighting_description."""


def _empty_result() -> I2TAnalysisResult:
    return I2TAnalysisResult(
        style_template="",
        composition_notes="",
        color_palette_extracted={"dominant": [], "accent": [], "temperature": "", "contrast": ""},
        style_tags=[],
        mood_keywords=[],
        lighting_description="",
    )


async def analyze_reference_image(
    image_url: str,
    mode: Literal["cover", "illustration"] = "cover",
) -> I2TAnalysisResult:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.warning("OPENAI_API_KEY not set; returning empty I2T result")
        return _empty_result()

    client = AsyncOpenAI(api_key=api_key)
    system_prompt = COVER_EXTRACTION_SYSTEM_PROMPT if mode == "cover" else ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT
    try:
        resp = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract visual style for T2I reuse."},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        )
        content = (resp.choices[0].message.content or "{}").strip()
        data = json.loads(content)
        return I2TAnalysisResult(
            style_template=str(data.get("style_template", "")),
            composition_notes=str(data.get("composition_notes", "")),
            color_palette_extracted=data.get("color_palette_extracted", {}) or {},
            style_tags=[str(x) for x in (data.get("style_tags", []) or [])],
            mood_keywords=[str(x) for x in (data.get("mood_keywords", []) or [])],
            lighting_description=str(data.get("lighting_description", "")),
        )
    except Exception as exc:
        logger.error("I2T analysis failed: %s", exc)
        return _empty_result()
