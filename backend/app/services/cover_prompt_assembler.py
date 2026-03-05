"""
Fallback cover prompt assembly when no I2T style_template exists.
Uses genre, cover_type, and primary entity tokens to build a T2I prompt.
"""
from dataclasses import dataclass
from typing import List


@dataclass
class CoverAssemblerResult:
    """Result of assembling a cover prompt without I2T."""
    prompt: str
    negative_prompt: str


class CoverPromptAssembler:
    """
    Builds a cover T2I prompt from genre, cover_type, and primary entity tokens.
    Used when CoverAnalysis.reference_style_template is not set (Simple tier or no reference image).
    """

    def assemble(
        self,
        genre: str,
        cover_type: str,
        primary_entity_tokens: List[str],
    ) -> CoverAssemblerResult:
        """
        Assemble prompt and negative_prompt for cover generation.

        Args:
            genre: Book genre (e.g. fantasy, thriller).
            cover_type: One of illustrated, photographic, typographic, abstract, etc.
            primary_entity_tokens: Visual tokens (e.g. core_tokens) for the primary subject.

        Returns:
            CoverAssemblerResult with prompt and negative_prompt.
        """
        genre = (genre or "fantasy").strip().lower()
        cover_type = (cover_type or "illustrated").strip().lower()
        tokens_str = ", ".join(primary_entity_tokens) if primary_entity_tokens else "dramatic book cover subject"
        prompt = (
            f"Professional {cover_type} book cover, {genre} genre. "
            f"Main subject: {tokens_str}. "
            "High quality, atmospheric, suitable for publishing."
        )
        negative_prompt = "blurry, low quality, distorted, watermark, text, ugly"
        return CoverAssemblerResult(prompt=prompt, negative_prompt=negative_prompt)
