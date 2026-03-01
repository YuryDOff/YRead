import asyncio

from app.services.providers.serper_provider import SerperProvider


def test_unavailable_without_key(monkeypatch):
    monkeypatch.delenv('SERPER_API_KEY', raising=False)
    p = SerperProvider()
    assert p.is_available() is False


def test_search_empty_without_key(monkeypatch):
    monkeypatch.delenv('SERPER_API_KEY', raising=False)
    p = SerperProvider()
    out = asyncio.run(p.search('query', 'character'))
    assert out == []
