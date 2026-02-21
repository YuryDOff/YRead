"""
Abstract T2I provider stub — returns prompt_used without any external API call.
Used for testing and as a no-op fallback when no real T2I provider is configured.
"""
from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult


class AbstractProvider(BaseT2IProvider):
    name = "abstract"

    def is_available(self) -> bool:
        return True

    def format_prompt(self, t2i_prompt_json: dict) -> str:
        return t2i_prompt_json.get("abstract") or t2i_prompt_json.get("flux") or t2i_prompt_json.get("sd") or ""

    async def generate(self, request: T2IRequest) -> T2IResult:
        """Return a stub result with the prompt but no actual image."""
        return T2IResult(
            image_url="",
            image_path="",
            provider=self.name,
            prompt_used=request.prompt,
        )
