"""Prompt engineering service for Noctua cover generation."""
from __future__ import annotations

import json
import logging
import os
from typing import Literal

from openai import AsyncOpenAI

from app.schemas import PromptEngineeringResult

logger = logging.getLogger(__name__)

_HUMANOID_VISUAL_TYPES = {"humanoid", "anthropomorphic", "creature", "man", "woman"}
_SPATIAL_VISUAL_TYPES = {"landscape", "cityscape", "interior", "architectural_ruin", "seascape", "location"}


def _heuristic_compatibility(
    template_subject_class: str,
    entity_visual_type: str,
    entity_class: str,
) -> Literal["COMPATIBLE", "WARNING", "INCOMPATIBLE"] | None:
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
    entity_visual_type = str(entity.get("visual_type", "")).lower()
    entity_class = str(entity.get("entity_class", "")).lower()
    quick = _heuristic_compatibility(template_subject_class, entity_visual_type, entity_class)

    if quick is not None and quick == "COMPATIBLE":
        core = ", ".join(entity.get("core_tokens", [])[:6])
        style = ", ".join(entity.get("style_tokens", [])[:4])
        anti = ", ".join(entity.get("anti_tokens", [])[:8])
        return PromptEngineeringResult(
            final_prompt=f"{style_template}. Replace subject with {entity.get('name','entity')}: {core}. {style}. {user_instruction}".strip(),
            negative_prompt=anti,
            compatibility_status=quick,
            compatibility_note="Entity appears compositionally compatible.",
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return PromptEngineeringResult(
            final_prompt=style_template,
            negative_prompt=", ".join(entity.get("anti_tokens", [])[:8]),
            compatibility_status=quick or "WARNING",
            compatibility_note="OPENAI_API_KEY missing; returned fallback prompt.",
        )

    client = AsyncOpenAI(api_key=api_key)
    payload = {
        "style_template": style_template,
        "entity": entity,
        "user_instruction": user_instruction,
        "template_subject_class": template_subject_class,
    }
    try:
        resp = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Merge template and replacement entity into T2I JSON output."},
                {"role": "user", "content": json.dumps(payload)},
            ],
        )
        data = json.loads((resp.choices[0].message.content or "{}").strip())
        return PromptEngineeringResult(
            final_prompt=str(data.get("final_prompt", style_template)),
            negative_prompt=str(data.get("negative_prompt", "")),
            compatibility_status=data.get("compatibility_status", "WARNING"),
            compatibility_note=str(data.get("compatibility_note", "")),
        )
    except Exception as exc:
        logger.error("run_prompt_merge failed: %s", exc)
        return PromptEngineeringResult(
            final_prompt=style_template,
            negative_prompt=", ".join(entity.get("anti_tokens", [])[:8]),
            compatibility_status="WARNING",
            compatibility_note="LLM merge failed; returned fallback prompt.",
        )
