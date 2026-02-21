"""Base classes for Text-to-Image generation providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class T2IRequest:
    prompt: str
    negative_prompt: str = ""
    reference_images: list[str] = field(default_factory=list)
    width: int = 1024
    height: int = 1024


@dataclass
class T2IResult:
    image_url: str
    image_path: str
    provider: str
    prompt_used: str


class BaseT2IProvider(ABC):
    name: str = ""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and ready to use."""
        ...

    @abstractmethod
    def format_prompt(self, t2i_prompt_json: dict) -> str:
        """
        Extract model-specific prompt variant from t2i_prompt_json dict.
        Falls back to 'abstract' key if model-specific key is absent.
        """
        ...

    @abstractmethod
    async def generate(self, request: T2IRequest) -> T2IResult:
        """Generate an image from the given request."""
        ...
