"""
dalle_provider.py
------------------
DALL-E 3 HD via OpenAI API. Fallback when FAL_API_KEY is not set.
No image conditioning — image_url param is ignored with a warning.
"""
from __future__ import annotations

import logging
import os

from .base import BaseCoverT2IProvider as BaseT2IProvider, T2IGenerationResult

logger = logging.getLogger(__name__)


class DalleProvider(BaseT2IProvider):
    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        negative_prompt: str | None = None,
        aspect_ratio: str = "2:3",
        **kwargs,
    ) -> T2IGenerationResult:
        from openai import AsyncOpenAI

        if image_url:
            logger.warning(
                "DalleProvider: image_url ignored — DALL-E 3 has no img2img. "
                "Use FluxKontextProvider for moodboard-conditioned generation."
            )

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1792",
            quality="hd",
            n=1,
        )
        img = response.data[0]
        return T2IGenerationResult(
            url=img.url or "",
            model="dall-e-3-hd",
            prompt_used=img.revised_prompt or prompt,
            provider="dalle",
        )
