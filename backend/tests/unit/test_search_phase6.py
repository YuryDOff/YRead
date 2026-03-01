"""
Unit tests for Phase 6: Search service extensions (Behance/Dribbble providers,
artefact/cover search, engine_selector cover branch, get_proposed_search_queries).
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import crud


def test_behance_provider_available_with_serpapi_key(monkeypatch):
    monkeypatch.setenv("SERPAPI_KEY", "test_key")
    monkeypatch.setenv("SEARCH_API_KEY", "")  # ensure SERPAPI wins
    from app.services.providers.behance_provider import BehanceProvider
    provider = BehanceProvider()
    assert provider.is_available() is True


def test_dribbble_provider_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("SERPAPI_KEY", raising=False)
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)
    from app.services.providers.dribbble_provider import DribbbleProvider
    provider = DribbbleProvider()
    assert provider.is_available() is False


def test_select_engines_cover_returns_cover_providers():
    from app.services.engine_selector import select_engines
    engines = select_engines(
        "cover", "cover", "illustrated",
        ["behance", "dribbble", "unsplash", "pexels"],
        engine_ratings={},
    )
    assert "behance" in engines or "dribbble" in engines


def test_select_engines_artefact_physical_weapon():
    from app.services.engine_selector import select_engines
    engines = select_engines(
        "physical_weapon", "artefact", "historical",
        ["wikimedia", "pexels", "unsplash"],
        engine_ratings={},
    )
    assert "wikimedia" in engines


@pytest.fixture
def mock_db_with_artefacts():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    book = crud.create_book(session, title="Test", author="Author")
    crud.create_visual_bible(session, book_id=book.id, style_category="fiction")
    crud.create_artefact(
        session,
        book_id=book.id,
        name="Sword",
        physical_description="A glowing blade",
        is_main=1,
    )
    crud.create_or_update_cover_analysis(
        session,
        book.id,
        thematic_statement="A tale of courage",
        symbolic_anchors=["sword", "shield"],
        cover_mood_keywords=["dark", "epic"],
    )
    yield session, book.id
    session.close()


def test_get_proposed_search_queries_includes_artefacts(mock_db_with_artefacts):
    from app.services.search_service import get_proposed_search_queries
    db, book_id = mock_db_with_artefacts
    result = get_proposed_search_queries(book_id, db, main_only=False)
    assert "artefacts" in result
    assert "cover" in result


@pytest.fixture
def mock_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    book = crud.create_book(session, title="Test", author="Author")
    crud.create_visual_bible(session, book_id=book.id, style_category="fiction")
    crud.create_artefact(
        session,
        book_id=book.id,
        name="Ring",
        physical_description="Golden ring",
        is_main=1,
    )
    yield session, book.id
    session.close()


def test_search_references_for_book_artefact_entity_type(mock_db):
    from app.services.search_service import search_references_for_book

    async def _fake_search(*args, **kwargs):
        return [{"url": "https://example.com/1.jpg", "provider": "unsplash", "width": 600, "height": 600}]

    db, book_id = mock_db
    with patch("app.services.search_service._search_all_providers", new_callable=AsyncMock, side_effect=_fake_search):
        result = asyncio.run(search_references_for_book(
            book_id,
            db=db,
            search_entity_types="artefacts",
        ))
    assert "artefacts" in result
    assert "characters" in result
    assert "locations" in result
    assert isinstance(result["artefacts"], list)
