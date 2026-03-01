"""
Integration tests for Phase 5: analysis endpoint extensions, artefacts, cover-analysis, entity-activations.
Order: tests that require "no analysis yet" (404, empty) run before tests that trigger analysis.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import SessionLocal
from app import crud


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def client_with_book(client: TestClient):
    """Upload a minimal manuscript and chunk it; yield (client, book_id)."""
    r = client.post(
        "/api/manuscripts/upload",
        files={"file": ("phase5_test.txt", b"Chapter One\n\n" + b"Sample text for analysis. " * 150, "text/plain")},
    )
    assert r.status_code == 200, f"Upload failed: {r.text}"
    book_id = r.json()["id"]
    r2 = client.post(f"/api/books/{book_id}/chunk")
    assert r2.status_code == 200, f"Chunk failed: {r2.text}"
    yield client, book_id


def test_get_artefacts_empty_before_analysis(client_with_book):
    """GET artefacts before any analysis: must return empty list."""
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/artefacts")
    assert r.status_code == 200
    assert r.json() == []


def test_get_cover_analysis_404_before_analysis(client_with_book):
    """GET cover-analysis before any analysis: must return 404."""
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/cover-analysis")
    assert r.status_code == 404


def test_analyze_with_entity_types_param(client_with_book):
    client, book_id = client_with_book
    r = client.post(
        f"/api/books/{book_id}/analyze",
        json={"entity_types": ["cover"], "style_category": "illustrated"},
    )
    assert r.status_code == 202


def test_analysis_progress_new_format(client_with_book):
    """Progress response is Phase 5 format: overall_status and entity_progress only (no current_chunk/total_chunks)."""
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/analysis-progress")
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        data = r.json()
        assert "overall_status" in data
        assert "entity_progress" in data
        assert isinstance(data["entity_progress"], dict)


def test_patch_cover_analysis_updates_fields(client_with_book):
    client, book_id = client_with_book
    db = SessionLocal()
    try:
        crud.create_or_update_cover_analysis(
            db,
            book_id=book_id,
            thematic_statement="Original theme",
            emotional_promise="Tension",
        )
        db.commit()
    finally:
        db.close()
    r = client.patch(
        f"/api/books/{book_id}/cover-analysis",
        json={"thematic_statement": "A story about loss"},
    )
    assert r.status_code == 200
    assert r.json()["thematic_statement"] == "A story about loss"


def test_update_entity_activations(client_with_book):
    client, book_id = client_with_book
    r = client.put(
        f"/api/books/{book_id}/entity-activations",
        json={"entity_activations": ["cover", "characters"]},
    )
    assert r.status_code == 200
    book_r = client.get(f"/api/books/{book_id}")
    assert book_r.status_code == 200
    assert "characters" in book_r.json().get("entity_activations", [])


def test_analyze_single_entity_endpoint(client_with_book):
    client, book_id = client_with_book
    r = client.post(
        f"/api/books/{book_id}/analyze/entity",
        json={"entity_type": "artefacts"},
    )
    assert r.status_code == 202
