"""
prompt_engineering_service.py
------------------------------
Merges an I2T-extracted style_template with a book entity's visual tokens
to produce a final T2I prompt ready for fal.ai FLUX Kontext.

Primary mode (I2T path):
  Inputs:  style_template + primary_entity + user_instruction
  Process: Compatibility check → GPT-4o merge call → PromptEngineeringResult

Fallback mode (Simple tier / no reference image):
  Routes to CoverPromptAssembler using genre + mood + character core_tokens.
"""
from __future__ import annotations

import json
import logging
import os
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import PromptEngineeringResult

logger = logging.getLogger(__name__)

MERGE_SYSTEM_PROMPT = """You are the Noctua Prompt Engineering Service. Merge the provided
I2T style template with the replacement entity to produce a final T2I generation prompt.

RULES:
1. Preserve ALL atmospheric, color, lighting, and stylistic elements from the STYLE TEMPLATE.
2. Replace ONLY the primary subject with the REPLACEMENT ENTITY using its visual tokens.
3. Anti-tokens MUST appear in negative_prompt ONLY — never in the main prompt.
4. Compatibility check:
   COMPATIBLE: entity fits same compositional role (humanoid replacing humanoid).
   WARNING: entity type mismatch may cause awkward composition — explain the risk.
   INCOMPATIBLE: entity is irreconcilable with the composition.
5. Output ONLY valid JSON — no markdown.

OUTPUT SCHEMA:
{
  "final_prompt": "<merged T2I prompt>",
  "negative_prompt": "<comma-separated negative tokens>",
  "compatibility_status": "COMPATIBLE" | "WARNING" | "INCOMPATIBLE",
  "compatibility_note": "<1-2 sentences>"
}"""

_HUMANOID_VISUAL_TYPES = {"humanoid", "anthropomorphic", "creature"}
_SPATIAL_VISUAL_TYPES = {"landscape", "cityscape", "interior", "architectural_ruin", "seascape"}


def _heuristic_compatibility(
    template_subject_class: str,
    entity_visual_type: str,
    entity_class: str,
) -> Literal["COMPATIBLE", "WARNING", "INCOMPATIBLE"] | None:
    """
    Returns a fast compatibility verdict if deterministic, else None (route to LLM).
    template_subject_class: 'humanoid' | 'object' | 'location' | 'abstract'
    """
    if template_subject_class == "humanoid":
        if entity_visual_type in _HUMANOID_VISUAL_TYPES:
            return "COMPATIBLE"
        if entity_visual_type in _SPATIAL_VISUAL_TYPES:
            return "WARNING"
    return None


async def run_prompt_merge(
    style_template: str,
    entity: dict,
    user_instruction: str,
    template_subject_class: str = "humanoid",
) -> PromptEngineeringResult:
    """
    Merges style_template with the replacement entity.

    Args:
        style_template: Full T2I string from I2T analysis (CoverAnalysis.reference_style_template).
        entity: Dict with keys: name, entity_class, visual_type, core_tokens, style_tokens,
                archetype_tokens, anti_tokens. Matches entity visual_tokens_json structure.
        user_instruction: Author's natural-language instruction.
        template_subject_class: The compositional role of the original subject in the template.

    Returns:
        PromptEngineeringResult with all fields populated.
        On API failure: returns a safe fallback result (WARNING status, original template as prompt).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not set — returning fallback PromptEngineeringResult")
        return _fallback_result(style_template)

    fast_status = _heuristic_compatibility(
        template_subject_class,
        entity.get("visual_type", ""),
        entity.get("entity_class", ""),
    )

    core_tokens = ", ".join(entity.get("core_tokens", []))
    style_tokens = ", ".join(entity.get("style_tokens", []))
    archetype_tokens = ", ".join(entity.get("archetype_tokens", []))
    anti_tokens = ", ".join(entity.get("anti_tokens", []))

    user_message = f"""=== STYLE TEMPLATE (from I2T analysis) ===
{style_template}

=== ENTITY TO REPLACE (existing primary subject) ===
Description: {template_subject_class} (primary foreground subject)

=== REPLACEMENT ENTITY ===
Name: {entity.get("name", "unnamed")}
Class: {entity.get("entity_class", "")}
Visual type: {entity.get("visual_type", "")}
Core tokens: {core_tokens}
Style tokens: {style_tokens}
Archetype tokens: {archetype_tokens}
Anti-tokens (negative prompt only): {anti_tokens}

=== USER INSTRUCTION ===
{user_instruction}

Produce the merged prompt. Return ONLY the JSON object."""

    client = AsyncOpenAI(api_key=api_key)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": MERGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or ""
        parsed = json.loads(raw)

        result = PromptEngineeringResult(
            final_prompt=parsed["final_prompt"],
            negative_prompt=parsed["negative_prompt"],
            compatibility_status=parsed["compatibility_status"],
            compatibility_note=parsed["compatibility_note"],
        )

        if fast_status is not None and fast_status != result.compatibility_status:
            logger.info(
                "Heuristic overrides LLM compatibility: %s → %s",
                result.compatibility_status,
                fast_status,
            )
            result = result.model_copy(update={"compatibility_status": fast_status})

        return result

    except Exception as exc:
        logger.warning("Prompt merge LLM call failed: %s. Returning fallback.", exc)
        return _fallback_result(style_template)


def _fallback_result(style_template: str) -> PromptEngineeringResult:
    return PromptEngineeringResult(
        final_prompt=style_template,
        negative_prompt="",
        compatibility_status="WARNING",
        compatibility_note="Prompt merge service unavailable. Using raw style template.",
    )
