import asyncio

from app.services.i2t_analysis_service import analyze_reference_image


def test_i2t_empty_on_missing_key(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    res = asyncio.run(analyze_reference_image('https://example.com/cover.jpg', mode='cover'))
    assert res.style_template == ''
    assert isinstance(res.style_tags, list)
