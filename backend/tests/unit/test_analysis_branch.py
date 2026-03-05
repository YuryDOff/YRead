"""
Unit tests for Phase 8a: analysis_mode (Simple vs Pro) and get_entity_types_for_mode.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import init_db
from app.services.ai_service import get_entity_types_for_mode


def test_simple_mode_returns_only_characters():
    result = get_entity_types_for_mode("simple", ["character", "location", "artefact"])
    assert result == ["character"]


def test_pro_mode_returns_all_requested():
    types = ["character", "location", "artefact", "scene"]
    result = get_entity_types_for_mode("pro", types)
    assert result == types


def test_simple_mode_ignores_requested_types():
    result = get_entity_types_for_mode("simple", ["artefact"])
    assert result == ["character"]


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


def test_default_mode_is_pro(client: TestClient):
    r = client.post("/api/books", json={"title": "Test", "author": "Author"})
    assert r.status_code == 201
    assert r.json()["analysis_mode"] == "pro"


def test_simple_mode_persists(client: TestClient):
    r = client.post(
        "/api/books",
        json={"title": "Test", "author": "Author", "analysis_mode": "simple"},
    )
    assert r.status_code == 201
    assert r.json()["analysis_mode"] == "simple"
