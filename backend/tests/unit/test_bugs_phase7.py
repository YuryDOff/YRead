"""
Unit tests for Phase 7: BUG-1/BUG-2, data model, VB entries, cover concepts.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, SessionLocal, init_db
from app import crud
from app.services.scene_extractor import _auto_scene_count
from app.routers.visual_bible import get_vb_angles


@pytest.fixture(scope="module")
def client():
    init_db()
    return TestClient(app)


@pytest.fixture
def db():
    """Session using app's engine (same as API)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client_with_book(client: TestClient, db):
    """Create a book with one character (is_main=1) via CRUD; yield (client, book_id)."""
    book = crud.create_book(db, title="T", author="A")
    crud.create_character(db, book_id=book.id, name="Hero", is_main=True)
    db.commit()
    yield client, book.id


@pytest.fixture
def client_with_scenes(client: TestClient, db):
    """Book with scene_display_count=5 and 15 scenes in DB."""
    book = crud.create_book(db, title="T", author="A")
    crud.update_book(db, book.id, scene_display_count=5)
    db.commit()
    from app.models import Scene
    for i in range(15):
        s = Scene(
            book_id=book.id,
            title=f"Scene {i+1}",
            chunk_start_index=i * 3,
            chunk_end_index=i * 3 + 2,
            narrative_summary="Summary",
            illustration_priority="high" if i < 5 else "low",
            visual_intensity=0.9 - i * 0.05,
        )
        db.add(s)
    db.commit()
    yield client, book.id


@pytest.fixture
def client_with_analysis(client: TestClient, db):
    """Book with characters and locations (for generate-all VB)."""
    book = crud.create_book(db, title="T", author="A")
    crud.create_character(db, book_id=book.id, name="C1", is_main=True, visual_bible_depth=2)
    crud.create_location(db, book_id=book.id, name="L1", is_main=False)
    db.commit()
    yield client, book.id


@pytest.fixture
def client_with_cover_analysis(client: TestClient, db):
    """Book with cover_analysis (has cover_t2i_prompt)."""
    book = crud.create_book(db, title="T", author="A")
    crud.create_or_update_cover_analysis(db, book.id, cover_t2i_prompt="A dramatic cover", thematic_statement="Theme")
    db.commit()
    yield client, book.id


@pytest.fixture
def client_with_concepts(client: TestClient, db):
    """Book with 2+ cover concepts."""
    book = crud.create_book(db, title="T", author="A")
    crud.create_cover_concept(db, book.id, concept_index=1, prompt_used="P1")
    crud.create_cover_concept(db, book.id, concept_index=2, prompt_used="P2")
    db.commit()
    yield client, book.id


# --- BUG-1: is_main isolation ---
def test_update_entity_reference_selection_does_not_touch_is_main(db):
    book = crud.create_book(db, title="T", author="A")
    char = crud.create_character(db, book_id=book.id, name="Hero", is_main=True)
    db.commit()
    crud.update_entity_reference_selection(db, char.id, 1, "character")
    refreshed = crud.get_character(db, char.id)
    assert refreshed.is_main == 1
    assert refreshed.is_selected_for_reference == 1


def test_entity_selections_endpoint_does_not_write_is_main(client_with_book):
    client, book_id = client_with_book
    r = client.get(f"/api/books/{book_id}/characters")
    assert r.status_code == 200
    chars = r.json()
    assert len(chars) >= 1
    char_id = chars[0]["id"]
    assert chars[0].get("is_main") == 1
    r2 = client.put(
        f"/api/books/{book_id}/entity-selections",
        json={"characters": [{"id": char_id, "is_main": 0}], "locations": [], "artefacts": []},
    )
    assert r2.status_code == 200
    r3 = client.get(f"/api/books/{book_id}/characters")
    updated = next(c for c in r3.json() if c["id"] == char_id)
    assert updated["is_main"] == 1
    assert updated.get("is_selected_for_reference") == 0


# --- BUG-2: scene_count ---
def test_auto_scene_count_scales_with_words():
    assert _auto_scene_count(6000) == 5
    assert _auto_scene_count(15000) == 5
    assert _auto_scene_count(30000) == 10
    assert _auto_scene_count(90000) == 30
    assert _auto_scene_count(200000) == 30


def test_get_scenes_show_all_false_limits_to_display_count(client_with_scenes):
    client, book_id = client_with_scenes
    r = client.get(f"/api/books/{book_id}/scenes")
    assert r.status_code == 200
    assert len(r.json()) == 5


def test_get_scenes_show_all_true_returns_all(client_with_scenes):
    client, book_id = client_with_scenes
    r = client.get(f"/api/books/{book_id}/scenes?show_all=true")
    assert r.status_code == 200
    assert len(r.json()) == 15


# --- Data model ---
def test_cover_analysis_cover_type_field(db):
    book = crud.create_book(db, title="T", author="A")
    ca = crud.create_or_update_cover_analysis(
        db, book.id,
        cover_type="object_centered",
        color_palette_structured='{"dominant":"black","accent":"amber"}',
    )
    assert ca.cover_type == "object_centered"


def test_cover_analysis_primary_ids(db):
    book = crud.create_book(db, title="T", author="A")
    ca = crud.create_or_update_cover_analysis(db, book.id, primary_cover_artefact_id=2)
    assert ca.primary_cover_artefact_id == 2
    assert ca.primary_cover_character_id is None


# --- VB entries ---
def test_get_vb_angles_character_main():
    angles = get_vb_angles("character", 6, is_main=True)
    assert len(angles) == 6
    assert "front" in angles


def test_get_vb_angles_artefact_secondary():
    angles = get_vb_angles("artefact", 2, is_main=False)
    assert len(angles) == 2


def test_generate_vb_entries_creates_correct_count(client_with_analysis):
    client, book_id = client_with_analysis
    r = client.post(f"/api/books/{book_id}/visual-bible/entries/generate-all", json={})
    assert r.status_code == 200
    assert r.json()["queued"] > 0


def test_generate_cover_concepts_creates_3(client_with_cover_analysis):
    client, book_id = client_with_cover_analysis
    r = client.post(f"/api/books/{book_id}/cover-concepts/generate", json={"concept_count": 3})
    assert r.status_code == 200
    assert r.json()["queued"] == 3


def test_cover_concept_generate_uses_cover_analysis_prompt(client_with_cover_analysis):
    client, book_id = client_with_cover_analysis
    client.post(f"/api/books/{book_id}/cover-concepts/generate", json={})
    concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
    assert len(concepts) >= 1
    assert concepts[0]["prompt_used"]


def test_select_cover_concept_exclusive(client_with_concepts):
    client, book_id = client_with_concepts
    concepts = client.get(f"/api/books/{book_id}/cover-concepts").json()
    c1_id, c2_id = concepts[0]["id"], concepts[1]["id"]
    client.post(f"/api/books/{book_id}/cover-concepts/{c1_id}/select")
    client.post(f"/api/books/{book_id}/cover-concepts/{c2_id}/select")
    r = client.get(f"/api/books/{book_id}/cover-concepts")
    selected = [c for c in r.json() if c["is_selected"]]
    assert len(selected) == 1
    assert selected[0]["id"] == c2_id


# --- Phase 7.6–7.8: Editable entities, cover, scenes, book strategy ---
def test_patch_book_search_query_strategy(client_with_book):
    """PATCH /books/{id} updates search_query_strategy (7.7.4)."""
    client, book_id = client_with_book
    r = client.patch(f"/api/books/{book_id}", json={"search_query_strategy": "adaptive"})
    assert r.status_code == 200
    assert r.json().get("search_query_strategy") == "adaptive"
    r2 = client.get(f"/api/books/{book_id}")
    assert r2.json().get("search_query_strategy") == "adaptive"


def test_patch_scene_narrative_and_dramatic(client_with_scenes):
    """PATCH /books/{id}/scenes/{id} accepts narrative_summary and dramatic_score_avg (7.6.3)."""
    client, book_id = client_with_scenes
    scenes = client.get(f"/api/books/{book_id}/scenes").json()
    scene_id = scenes[0]["id"]
    r = client.patch(
        f"/api/books/{book_id}/scenes/{scene_id}",
        json={"title": "Updated title", "narrative_summary": "New summary", "dramatic_score_avg": 0.85},
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Updated title"
    assert r.json()["narrative_summary"] == "New summary"
    assert r.json()["dramatic_score_avg"] == 0.85


def test_patch_cover_analysis_partial(client_with_cover_analysis):
    """PATCH /books/{id}/cover-analysis accepts partial fields (7.6.2 / 7.6.4)."""
    client, book_id = client_with_cover_analysis
    r = client.patch(
        f"/api/books/{book_id}/cover-analysis",
        json={"thematic_statement": "New theme", "cover_type": "character_centered"},
    )
    assert r.status_code == 200
    assert r.json()["thematic_statement"] == "New theme"
    assert r.json()["cover_type"] == "character_centered"
    assert r.json().get("cover_t2i_prompt")  # unchanged


@pytest.fixture
def client_with_artefact(client: TestClient, db):
    """Book with one artefact."""
    book = crud.create_book(db, title="T", author="A")
    art = crud.create_artefact(db, book_id=book.id, name="Sword", physical_description="A blade", is_main=False)
    db.commit()
    yield client, book.id, art.id


def test_put_artefact_partial(client_with_artefact):
    """PUT /books/{id}/artefacts/{id} updates name, full_description, symbolic_role (7.6.1)."""
    client, book_id, art_id = client_with_artefact
    r = client.put(
        f"/api/books/{book_id}/artefacts/{art_id}",
        json={"name": "Excalibur", "full_description": "A legendary blade for search", "symbolic_role": "Power"},
    )
    assert r.status_code == 200
    assert r.json()["name"] == "Excalibur"
    assert r.json().get("full_description") == "A legendary blade for search"
    assert r.json().get("symbolic_role") == "Power"


def test_patch_entity_summaries_full_description(client_with_book):
    """PATCH /entity-summaries accepts full_description for characters/locations (7.6.1)."""
    client, book_id = client_with_book
    chars = client.get(f"/api/books/{book_id}/characters").json()
    char_id = chars[0]["id"]
    r = client.patch(
        f"/api/books/{book_id}/entity-summaries",
        json={
            "characters": [{"id": char_id, "physical_description": "Updated", "full_description": "Full sentence for search"}],
            "locations": [],
        },
    )
    assert r.status_code == 200
    r2 = client.get(f"/api/books/{book_id}/characters")
    updated = next(c for c in r2.json() if c["id"] == char_id)
    assert updated.get("physical_description") == "Updated"
    assert updated.get("full_description") == "Full sentence for search"
