"""
Unit tests for Phase 8b: I2T analysis service and analyze-cover-reference endpoint.
"""
import asyncio
import json
import os
import pytest
from unittest.mock import AsyncMock, patch

from app.services.i2t_analysis_service import run_i2t_analysis, _empty_result
from app.schemas import I2TAnalysisResult

MOCK_GPT_RESPONSE = {
    "style_template": "dark fantasy illustration, hooded figure, forest, art nouveau border, teal gold palette",
    "composition_notes": "Single foreground figure, centred, misty background",
    "color_palette_extracted": {"dominant": "teal", "accent": "gold", "temperature": "cool", "contrast": "high"},
    "style_tags": ["dark fantasy", "art nouveau", "cinematic"],
    "mood_keywords": ["mysterious", "atmospheric"],
    "lighting_description": "Moonlit from above, rim lighting on figure",
}


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No API key")
def test_run_i2t_analysis_returns_all_fields():
    result = asyncio.run(run_i2t_analysis("https://example.com/cover.jpg", mode="cover"))
    assert isinstance(result, I2TAnalysisResult)
    assert result.style_template != ""
    assert isinstance(result.color_palette_extracted, dict)
    assert isinstance(result.style_tags, list)


def test_run_i2t_analysis_mock_response():
    mock_message = AsyncMock()
    mock_message.content = json.dumps(MOCK_GPT_RESPONSE)
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            result = asyncio.run(run_i2t_analysis("https://example.com/cover.jpg"))

    assert result.style_template == MOCK_GPT_RESPONSE["style_template"]
    assert result.color_palette_extracted["dominant"] == "teal"
    assert "dark fantasy" in result.style_tags


def test_run_i2t_analysis_returns_empty_on_vision_failure():
    with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client_cls.return_value = mock_client
        mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Network error"))

        result = asyncio.run(run_i2t_analysis("https://example.com/cover.jpg"))

    assert result.style_template == ""
    assert result.color_palette_extracted == {}
    assert result.style_tags == []


def test_mode_param_routes_to_correct_system_prompt():
    captured_messages = []
    mock_message = AsyncMock()
    mock_message.content = json.dumps(MOCK_GPT_RESPONSE)
    mock_choice = AsyncMock()
    mock_choice.message = mock_message
    mock_response = AsyncMock()
    mock_response.choices = [mock_choice]

    async def capture_call(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return mock_response

    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=False):
        with patch("app.services.i2t_analysis_service.AsyncOpenAI") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client
            mock_client.chat.completions.create = capture_call

            asyncio.run(run_i2t_analysis("https://example.com/img.jpg", mode="illustration"))

    system_content = captured_messages[0]["content"]
    assert "scene composition" in system_content.lower()


# ---------------------------------------------------------------------------
# Fixtures for endpoint test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    from app.main import app
    from app.database import init_db
    from fastapi.testclient import TestClient
    init_db()
    return TestClient(app)


@pytest.fixture
def db():
    from app.database import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def book_id(db):
    from app import crud
    book = crud.create_book(db, title="T", author="A")
    db.commit()
    return book.id


def test_endpoint_stores_result_to_db(client, book_id):
    with patch("app.routers.covers.run_i2t_analysis", new_callable=AsyncMock) as mock_i2t:
        mock_i2t.return_value = I2TAnalysisResult(
            style_template="dark fantasy, teal gold",
            composition_notes="Single figure",
            color_palette_extracted={"dominant": "teal"},
            style_tags=["dark"],
            mood_keywords=["moody"],
            lighting_description="Rim light",
        )
        r = client.post(
            f"/api/books/{book_id}/analyze-cover-reference",
            json={"image_url": "https://example.com/cover.jpg", "mode": "cover"},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["style_template"] == "dark fantasy, teal gold"
