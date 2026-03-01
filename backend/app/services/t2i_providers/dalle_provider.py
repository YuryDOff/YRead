"""DALL-E provider backed by OpenAI Images API."""
import os

from openai import AsyncOpenAI

from app.services.t2i_providers.base import BaseT2IProvider, T2IRequest, T2IResult


class DalleProvider(BaseT2IProvider):
    name = "dalle"

    def is_available(self) -> bool:
        return bool(os.getenv("OPENAI_API_KEY"))

    def format_prompt(self, t2i_prompt_json: dict) -> str:
        return t2i_prompt_json.get("dalle") or t2i_prompt_json.get("abstract") or ""

    async def generate(self, request: T2IRequest) -> T2IResult:
        if not self.is_available():
            raise RuntimeError("DalleProvider unavailable: OPENAI_API_KEY missing")
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        size = "1024x1024"
        if request.width == 1792 and request.height == 1024:
            size = "1792x1024"
        elif request.width == 1024 and request.height == 1792:
            size = "1024x1792"
        res = await client.images.generate(model=os.getenv("DALLE_MODEL", "gpt-image-1"), prompt=request.prompt, size=size)
        url = ""
        if getattr(res, "data", None):
            item = res.data[0]
            url = getattr(item, "url", "") or ""
        return T2IResult(image_url=url, image_path=url, provider=self.name, prompt_used=request.prompt)
