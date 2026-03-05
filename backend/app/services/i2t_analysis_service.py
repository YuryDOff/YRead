"""
i2t_analysis_service.py
------------------------
Reverse-engineers the visual style of a reference book cover image using
GPT-4o Vision. Produces a style_template string suitable for direct use
as a T2I prompt by the PromptEngineeringService.

Extraction modes:
  cover       — optimised for book cover composition vocabulary
  illustration — scene composition vocabulary (Phase 17, future)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import I2TAnalysisResult

logger = logging.getLogger(__name__)

COVER_EXTRACTION_SYSTEM_PROMPT = """You are an expert at writing Stable Diffusion prompts
from reference images. Analyse the provided book cover image and describe it as a
Stable Diffusion generation prompt — the kind a professional concept artist would use
to recreate the same visual style, atmosphere, and composition.

Rules:
- DO NOT include any typography, text, titles, author names, or lettering in your output
- DO NOT include specific character identities, real names, or trademarked elements
- Focus ONLY on what makes this image visually reproducible: artistic style,
  composition, lighting, color, atmosphere, and rendering technique
- Use comma-separated descriptor tags in style_template — exactly as you would
  write a Stable Diffusion prompt (e.g. "dark fantasy illustration, hooded figure,
  misty forest, moonlit, Art Nouveau border, teal and gold palette, cinematic lighting,
  8k, bokeh background, dramatic upward angle")

Extract and return ONLY valid JSON matching this schema:
{
  "style_template": "<Stable Diffusion prompt string — comma-separated descriptors, no text/typography>",
  "composition_notes": "<one sentence: subject placement, foreground/background layers, camera angle>",
  "color_palette_extracted": {
    "dominant": "<primary color name or hex>",
    "accent": "<accent color name or hex>",
    "temperature": "warm | cool | neutral",
    "contrast": "high | medium | low"
  },
  "style_tags": ["<art style tag>", "<rendering technique>", "<art movement if applicable>"],
  "mood_keywords": ["<emotional tone>", "<atmosphere descriptor>"],
  "lighting_description": "<light source, direction, and mood contribution>"
}"""

ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT = """You are an expert at writing Stable Diffusion
prompts from illustrated book scenes. Analyse the provided image and describe it as a
Stable Diffusion generation prompt — the kind a professional concept artist would use
to recreate the same scene composition, atmosphere, and visual style.

Rules:
- DO NOT include any typography, text, captions, or lettering
- DO NOT include specific character names or trademarked elements
- Focus on: scene depth, character-environment relationship, action staging,
  lighting mood, color narrative role, compositional layers
- Use comma-separated descriptor tags in style_template — exactly as you would
  write a Stable Diffusion prompt (e.g. "fantasy illustration, young woman reading,
  candlelit library, warm amber glow, towering bookshelves, dust particles, detailed,
  painterly, cinematic composition, shallow depth of field")

Extract and return ONLY valid JSON matching this schema:
{
  "style_template": "<Stable Diffusion prompt string — comma-separated descriptors>",
  "composition_notes": "<one sentence: scene depth, subject placement, action staging>",
  "color_palette_extracted": {
    "dominant": "<primary color name or hex>",
    "accent": "<accent color name or hex>",
    "temperature": "warm | cool | neutral",
    "contrast": "high | medium | low"
  },
  "style_tags": ["<illustration style>", "<rendering technique>", "<art movement if applicable>"],
  "mood_keywords": ["<emotional tone>", "<narrative atmosphere>"],
  "lighting_description": "<light source, direction, and contribution to scene mood>"
}"""


async def run_i2t_analysis(
    image_url: str,
    mode: Literal["cover", "illustration"] = "cover",
) -> I2TAnalysisResult:
    """
    Calls GPT-4o Vision to extract style information from a reference image.

    Args:
        image_url: Publicly accessible URL of the reference image.
        mode: 'cover' uses cover composition vocabulary; 'illustration' uses scene vocabulary.

    Returns:
        I2TAnalysisResult with all fields populated.
        Returns an empty/default result if the Vision call fails — does NOT raise.
        Caller must handle the empty result gracefully (log, continue moodboard flow).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set — returning empty I2TAnalysisResult")
        return _empty_result()

    system_prompt = (
        COVER_EXTRACTION_SYSTEM_PROMPT
        if mode == "cover"
        else ILLUSTRATION_EXTRACTION_SYSTEM_PROMPT
    )

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",   # Cost-efficient; use gpt-4o for highest accuracy
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url, "detail": "high"},
                        },
                        {
                            "type": "text",
                            "text": "Analyse this book cover and extract its visual style as JSON.",
                        },
                    ],
                },
            ],
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)

        return I2TAnalysisResult(
            style_template=parsed.get("style_template", ""),
            composition_notes=parsed.get("composition_notes", ""),
            color_palette_extracted=parsed.get("color_palette_extracted", {}),
            style_tags=parsed.get("style_tags", []),
            mood_keywords=parsed.get("mood_keywords", []),
            lighting_description=parsed.get("lighting_description", ""),
        )

    except Exception as exc:
        logger.warning(f"I2T analysis failed for {image_url}: {exc}. Returning empty result.")
        return _empty_result()


def _empty_result() -> I2TAnalysisResult:
    return I2TAnalysisResult(
        style_template="",
        composition_notes="",
        color_palette_extracted={},
        style_tags=[],
        mood_keywords=[],
        lighting_description="",
    )
