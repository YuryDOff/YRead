"""
flux_provider.py
-----------------
FLUX.1 Pro (text-only) and FLUX.1 Kontext Pro (image+text) via fal.ai.

FLUX Kontext is used when a moodboard reference URL is supplied — enabling
style transfer from Visual Bible entity reference images.

Install: pip install fal-client>=0.10.0
Requires: FAL_API_KEY environment variable.
"""
from __future__ import annotations

import logging
import os

from .base import BaseCoverT2IProvider as BaseT2IProvider, T2IGenerationResult

logger = logging.getLogger(__name__)


class FluxKontextProvider(BaseT2IProvider):
    TEXT_ENDPOINT = "fal-ai/flux-pro/v1.1"
    KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"

    def __init__(self) -> None:
        api_key = os.getenv("FAL_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "FAL_API_KEY not set. Set it in .env before using FluxKontextProvider."
            )
        os.environ["FAL_KEY"] = api_key

    def is_available(self) -> bool:
        return bool(os.getenv("FAL_API_KEY"))

    async def generate(
        self,
        prompt: str,
        image_url: str | None = None,
        negative_prompt: str | None = None,
        aspect_ratio: str = "2:3",
        num_inference_steps: int = 28,
        guidance_scale: float = 3.5,
    ) -> T2IGenerationResult:
        try:
            import fal_client
        except ImportError as exc:
            raise RuntimeError("fal-client not installed. Run: pip install fal-client") from exc

        endpoint = self.KONTEXT_ENDPOINT if image_url else self.TEXT_ENDPOINT
        args: dict = {
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "num_inference_steps": num_inference_steps,
            "guidance_scale": guidance_scale,
        }
        if image_url:
            args["image_url"] = image_url
        if negative_prompt:
            args["negative_prompt"] = negative_prompt

        logger.info(
            "FLUX generate — endpoint=%s, prompt_tokens=%s, image_url=%s",
            endpoint,
            len(prompt.split()),
            "yes" if image_url else "no",
        )

        result = await fal_client.run_async(endpoint, arguments=args)
        image_data = result["images"][0]

        return T2IGenerationResult(
            url=image_data["url"],
            width=image_data.get("width"),
            height=image_data.get("height"),
            model=endpoint,
            prompt_used=prompt,
            provider="flux_kontext" if image_url else "flux_pro",
        )
