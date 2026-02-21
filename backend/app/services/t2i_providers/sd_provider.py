"""
Stable Diffusion T2I provider skeleton.
Supports A1111 (SD_A1111_URL) or ComfyUI (SD_COMFYUI_URL) local/remote endpoints.
Only the skeleton is implemented — actual API calls are left as stubs for the T2I generation sprint.
"""
import logging
import os

from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult

logger = logging.getLogger(__name__)

SD_A1111_URL = os.getenv("SD_A1111_URL", "")
SD_COMFYUI_URL = os.getenv("SD_COMFYUI_URL", "")


class SDProvider(BaseT2IProvider):
    name = "sd"

    def is_available(self) -> bool:
        return bool(SD_A1111_URL or SD_COMFYUI_URL)

    def format_prompt(self, t2i_prompt_json: dict) -> str:
        """Prefer SD-specific prompt; fall back to abstract."""
        return (
            t2i_prompt_json.get("sd")
            or t2i_prompt_json.get("abstract")
            or ""
        )

    async def generate(self, request: T2IRequest) -> T2IResult:
        if not self.is_available():
            raise RuntimeError("SDProvider: no endpoint configured (SD_A1111_URL or SD_COMFYUI_URL)")

        logger.info("SDProvider.generate called — stub, no image generated yet")
        # TODO: implement A1111/ComfyUI call in T2I generation sprint
        return T2IResult(
            image_url="",
            image_path="",
            provider=self.name,
            prompt_used=request.prompt,
        )
