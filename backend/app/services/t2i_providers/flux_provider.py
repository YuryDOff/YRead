"""
FLUX T2I provider skeleton.
Supports fal.ai (FAL_API_KEY) or Replicate (REPLICATE_API_KEY).
Only the skeleton is implemented — actual API calls are left as stubs for the T2I generation sprint.
"""
import logging
import os

from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult

logger = logging.getLogger(__name__)

FAL_API_KEY = os.getenv("FAL_API_KEY", "")
REPLICATE_API_KEY = os.getenv("REPLICATE_API_KEY", "")


class FluxProvider(BaseT2IProvider):
    name = "flux"

    def is_available(self) -> bool:
        return bool(FAL_API_KEY or REPLICATE_API_KEY)

    def format_prompt(self, t2i_prompt_json: dict) -> str:
        """Prefer FLUX-specific prompt; fall back to abstract."""
        return (
            t2i_prompt_json.get("flux")
            or t2i_prompt_json.get("abstract")
            or ""
        )

    async def generate(self, request: T2IRequest) -> T2IResult:
        if not self.is_available():
            raise RuntimeError("FluxProvider: no API key configured (FAL_API_KEY or REPLICATE_API_KEY)")

        logger.info("FluxProvider.generate called — stub, no image generated yet")
        # TODO: implement fal.ai / Replicate call in T2I generation sprint
        return T2IResult(
            image_url="",
            image_path="",
            provider=self.name,
            prompt_used=request.prompt,
        )
