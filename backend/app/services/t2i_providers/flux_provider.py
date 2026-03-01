"""FLUX provider backed by fal.ai."""
import logging
import os

from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult

logger = logging.getLogger(__name__)


class FluxProvider(BaseT2IProvider):
    name = "flux"

    def is_available(self) -> bool:
        return bool(os.getenv("FAL_API_KEY"))

    def format_prompt(self, t2i_prompt_json: dict) -> str:
        return t2i_prompt_json.get("flux") or t2i_prompt_json.get("abstract") or ""

    async def generate(self, request: T2IRequest) -> T2IResult:
        if not self.is_available():
            raise RuntimeError("FluxProvider unavailable: FAL_API_KEY missing")

        import fal_client

        result = await fal_client.submit_async(
            "fal-ai/flux/dev",
            arguments={
                "prompt": request.prompt,
                "negative_prompt": request.negative_prompt,
                "image_size": {"width": request.width, "height": request.height},
            },
        )
        output = await result.get()
        images = output.get("images", []) if isinstance(output, dict) else []
        url = images[0].get("url", "") if images else ""
        return T2IResult(image_url=url, image_path=url, provider=self.name, prompt_used=request.prompt)
