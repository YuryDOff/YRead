import asyncio

from app.services.prompt_engineering_service import _heuristic_compatibility, run_prompt_merge


def test_heuristic_compatibility_humanoid():
    assert _heuristic_compatibility('humanoid', 'woman', 'character') == 'COMPATIBLE'


def test_heuristic_warning_for_spatial():
    assert _heuristic_compatibility('humanoid', 'landscape', 'location') == 'WARNING'


def test_run_prompt_merge_fallback(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    out = asyncio.run(run_prompt_merge(
        'moody illustrated cover',
        {'name': 'Eira', 'visual_type': 'woman', 'core_tokens': ['silver hair'], 'style_tokens': [], 'anti_tokens': ['extra limbs']},
        'epic fantasy',
    ))
    assert out.final_prompt
    assert out.compatibility_status in {'COMPATIBLE', 'WARNING'}
