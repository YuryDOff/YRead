"""
Integration tests for Scene API endpoints (steps 10/11).
Uses FastAPI TestClient with a live SQLite DB.
No external API keys required.
"""
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import crud


# ---------------------------------------------------------------------------
# Test DB setup
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite:///./test_integration.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    try:
        Base.metadata.drop_all(bind=test_engine)
        test_engine.dispose()
    except Exception:
        pass
    import os
    import time
    time.sleep(0.5)
    try:
        if os.path.exists("test_integration.db"):
            os.remove("test_integration.db")
    except PermissionError:
        pass  # Background task may still hold the file; CI will clean on next run


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def book_with_scenes(client):
    """Create a book, then inject scenes directly into DB."""
    # Upload a minimal book
    r = client.post(
        "/api/manuscripts/upload",
        files={"file": ("test.txt", b"Chapter 1\n" + b"Test content " * 200, "text/plain")},
    )
    assert r.status_code == 200, f"Upload failed: {r.text}"
    book_id = r.json()["id"]

    # Inject scenes directly
    db = TestingSessionLocal()
    try:
        # Create characters
        char = crud.create_character(db, book_id=book_id, name="Robbie", is_main=True)
        loc = crud.create_location(db, book_id=book_id, name="Lab", is_main=True)

        # Create scenes
        s1 = crud.create_scene(
            db, book_id=book_id,
            title="The Robot Awakens",
            scene_type="inciting_incident",
            chunk_start_index=0, chunk_end_index=4,
            narrative_summary="Robbie first activates in the lab",
            scene_prompt_draft="A large robot standing in a dimly lit lab, wide shot",
            t2i_prompt_json=json.dumps({
                "abstract": "A large industrial robot stands motionless in a lab, dramatic lighting, wide angle"
            }),
            illustration_priority="high",
            is_selected=1,
        )
        s2 = crud.create_scene(
            db, book_id=book_id,
            title="Confrontation",
            scene_type="climax",
            chunk_start_index=8, chunk_end_index=12,
            narrative_summary="The scientists argue about robot rights",
            scene_prompt_draft="Scientists arguing in a bright office",
            t2i_prompt_json=json.dumps({
                "abstract": "Two scientists in a bright office, tense confrontation, medium shot"
            }),
            illustration_priority="medium",
            is_selected=1,
        )
        crud.create_scene_character(db, s1.id, char.id)
        crud.create_scene_location(db, s1.id, loc.id)
        db.commit()
    finally:
        db.close()

    return {"book_id": book_id}


# ---------------------------------------------------------------------------
# Scene endpoint tests
# ---------------------------------------------------------------------------

class TestGetScenes:
    def test_returns_list(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_required_fields_present(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        for scene in r.json():
            assert "id" in scene
            assert "title" in scene
            assert "scene_type" in scene
            assert "chunk_start_index" in scene
            assert "chunk_end_index" in scene
            assert "scene_prompt_draft" in scene
            assert "t2i_prompt_json" in scene
            assert "is_selected" in scene
            assert "characters_present" in scene

    def test_t2i_prompt_has_abstract(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        for scene in r.json():
            if scene["t2i_prompt_json"]:
                assert "abstract" in scene["t2i_prompt_json"]

    def test_characters_present_populated(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scenes = r.json()
        scene1 = next((s for s in scenes if s["title"] == "The Robot Awakens"), None)
        assert scene1 is not None
        assert "Robbie" in scene1["characters_present"]

    def test_primary_location_populated(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scenes = r.json()
        scene1 = next((s for s in scenes if s["title"] == "The Robot Awakens"), None)
        assert scene1 is not None
        assert scene1["primary_location"] == "Lab"

    def test_404_for_nonexistent_book(self, client):
        r = client.get("/api/books/9999/scenes")
        assert r.status_code == 404


class TestPatchScene:
    def test_patch_is_selected_false(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scene_id = r.json()[0]["id"]

        r2 = client.patch(
            f"/api/books/{book_id}/scenes/{scene_id}",
            json={"is_selected": False},
        )
        assert r2.status_code == 200
        assert r2.json()["is_selected"] is False

    def test_patch_is_selected_persists(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scene_id = r.json()[0]["id"]

        client.patch(f"/api/books/{book_id}/scenes/{scene_id}", json={"is_selected": False})
        r2 = client.get(f"/api/books/{book_id}/scenes")
        updated = next(s for s in r2.json() if s["id"] == scene_id)
        assert updated["is_selected"] is False

    def test_patch_scene_prompt_draft(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scene_id = r.json()[0]["id"]
        new_prompt = "A tense confrontation in a dimly lit laboratory, wide angle shot"

        r2 = client.patch(
            f"/api/books/{book_id}/scenes/{scene_id}",
            json={"scene_prompt_draft": new_prompt},
        )
        assert r2.status_code == 200
        assert r2.json()["scene_prompt_draft"] == new_prompt

    def test_404_for_wrong_book(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/scenes")
        scene_id = r.json()[0]["id"]
        r2 = client.patch(f"/api/books/9999/scenes/{scene_id}", json={"is_selected": False})
        assert r2.status_code == 404


class TestProposedSearchQueriesWithScenes:
    def test_includes_scenes_key(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/proposed-search-queries?main_only=true")
        assert r.status_code == 200
        data = r.json()
        assert "scenes" in data, f"scenes key missing from response: {list(data.keys())}"

    def test_scenes_key_is_list(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/proposed-search-queries?main_only=true")
        assert isinstance(r.json()["scenes"], list)

    def test_deselected_scene_excluded(self, client, book_with_scenes):
        """After deselecting a scene, it should NOT appear in proposed-search-queries."""
        book_id = book_with_scenes["book_id"]

        # Get scenes, deselect all
        scenes_r = client.get(f"/api/books/{book_id}/scenes")
        scenes = scenes_r.json()
        for scene in scenes:
            client.patch(
                f"/api/books/{book_id}/scenes/{scene['id']}",
                json={"is_selected": False}
            )

        # Now proposed queries should have 0 scenes
        r = client.get(f"/api/books/{book_id}/proposed-search-queries?main_only=true")
        assert len(r.json()["scenes"]) == 0

        # Re-select first scene
        if scenes:
            client.patch(
                f"/api/books/{book_id}/scenes/{scenes[0]['id']}",
                json={"is_selected": True}
            )


# ---------------------------------------------------------------------------
# Engine ratings tests
# ---------------------------------------------------------------------------

class TestEngineRatings:
    def test_empty_ratings_returns_list(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.get(f"/api/books/{book_id}/engine-ratings")
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_like_increments_likes(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        r = client.patch(
            f"/api/books/{book_id}/engine-ratings",
            json={"provider": "pixabay", "action": "like"},
        )
        assert r.status_code == 200

        r2 = client.get(f"/api/books/{book_id}/engine-ratings")
        ratings = {x["provider"]: x for x in r2.json()}
        assert "pixabay" in ratings
        assert ratings["pixabay"]["likes"] >= 1

    def test_dislike_increments_dislikes(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        client.patch(
            f"/api/books/{book_id}/engine-ratings",
            json={"provider": "unsplash", "action": "dislike"},
        )
        r = client.get(f"/api/books/{book_id}/engine-ratings")
        ratings = {x["provider"]: x for x in r.json()}
        assert "unsplash" in ratings
        assert ratings["unsplash"]["dislikes"] >= 1
        assert ratings["unsplash"]["net_score"] < 0

    def test_net_score_calculated_correctly(self, client, book_with_scenes):
        book_id = book_with_scenes["book_id"]
        # Like pexels twice
        client.patch(f"/api/books/{book_id}/engine-ratings",
                     json={"provider": "pexels", "action": "like"})
        client.patch(f"/api/books/{book_id}/engine-ratings",
                     json={"provider": "pexels", "action": "like"})
        # Dislike once
        client.patch(f"/api/books/{book_id}/engine-ratings",
                     json={"provider": "pexels", "action": "dislike"})

        r = client.get(f"/api/books/{book_id}/engine-ratings")
        ratings = {x["provider"]: x for x in r.json()}
        pexels = ratings["pexels"]
        assert pexels["likes"] == 2
        assert pexels["dislikes"] == 1
        assert pexels["net_score"] == 1

    def test_upsert_no_duplicate_rows(self):
        """Same provider rated multiple times → only one row per provider."""
        db = TestingSessionLocal()
        try:
            # Create a fresh book
            from app.crud import create_book, update_engine_rating, get_engine_ratings_list
            book = create_book(db, title="Rating test book")
            update_engine_rating(db, book.id, "pixabay", delta_likes=1)
            update_engine_rating(db, book.id, "pixabay", delta_likes=1)
            rows = get_engine_ratings_list(db, book.id)
            pixabay_rows = [r for r in rows if r.provider == "pixabay"]
            assert len(pixabay_rows) == 1, "Should be exactly one row per provider"
            assert pixabay_rows[0].likes == 2
        finally:
            db.close()

    def test_404_for_nonexistent_book(self, client):
        r = client.patch(
            "/api/books/9999/engine-ratings",
            json={"provider": "pixabay", "action": "like"},
        )
        assert r.status_code == 404

    def test_ratings_isolated_between_books(self, client):
        """Ratings for one book should not affect another book."""
        db = TestingSessionLocal()
        try:
            from app.crud import create_book, update_engine_rating, get_engine_ratings
            book_a = create_book(db, title="Book A")
            book_b = create_book(db, title="Book B")
            update_engine_rating(db, book_a.id, "pixabay", delta_likes=5)
            ratings_b = get_engine_ratings(db, book_b.id)
            assert ratings_b.get("pixabay", 0) == 0
        finally:
            db.close()


# ---------------------------------------------------------------------------
# Backward compatibility tests
# ---------------------------------------------------------------------------

class TestBackwardCompat:
    def test_analyze_without_scene_count_returns_202(self, client, book_with_scenes):
        """Old clients without scene_count should still get 202."""
        book_id = book_with_scenes["book_id"]
        db = TestingSessionLocal()
        try:
            # Chunk the book first
            r = client.post(f"/api/books/{book_id}/chunk")
            assert r.status_code == 200

            # Analyze without scene_count — should use default=10
            r = client.post(
                f"/api/books/{book_id}/analyze",
                json={
                    "style_category": "sci-fi",
                    "illustration_frequency": 4,
                    "layout_style": "inline_classic",
                    "is_well_known": False,
                },
            )
            assert r.status_code == 202, f"Expected 202, got {r.status_code}: {r.text}"
        finally:
            db.close()
