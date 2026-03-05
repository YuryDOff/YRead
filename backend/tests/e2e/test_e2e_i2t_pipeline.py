"""
E2E: I2T analysis → CoverAnalysis storage → cover concept generation (Phase 14).
Requires OPENAI_API_KEY. Skips generation poll when FAL_API_KEY not set.
"""
import os
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="Requires OPENAI_API_KEY",
)

TEST_DB_URL = "sqlite:///./test_e2e_i2t.db"
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
    try:
        if os.path.exists("test_e2e_i2t.db"):
            os.remove("test_e2e_i2t.db")
    except (PermissionError, OSError):
        pass


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def book_id(client):
    """Minimal book via upload + chunk for I2T and cover-concept E2E."""
    r = client.post(
        "/api/manuscripts/upload",
        files={
            "file": (
                "short.txt",
                b"The Ember Crown. Chapter One. In the northern keep, the heir woke to horns.",
                "text/plain",
            )
        },
        data={"analysis_mode": "simple"},
    )
    assert r.status_code == 200, r.text
    bid = r.json()["id"]
    r2 = client.post(f"/api/books/{bid}/chunk")
    assert r2.status_code == 200, r2.text
    return bid


def test_full_i2t_pipeline(client, book_id):
    """End-to-end: reference image → I2T → prompt merge → CoverConcept."""
    # 1. Run I2T analysis
    r = client.post(
        f"/api/books/{book_id}/analyze-cover-reference",
        json={
            "image_url": "https://covers.openlibrary.org/b/id/8224689-L.jpg",
            "mode": "cover",
        },
    )
    assert r.status_code == 200, r.text
    i2t = r.json()
    assert i2t.get("style_template", "") != ""

    # 2. Verify CoverAnalysis updated
    r2 = client.get(f"/api/books/{book_id}/cover-analysis")
    assert r2.status_code == 200, r2.text
    assert r2.json().get("reference_style_template") == i2t["style_template"]

    # 3. Trigger generation (uses I2T result automatically)
    r3 = client.post(
        f"/api/books/{book_id}/cover-concepts/generate",
        json={"user_instruction": "Keep the atmospheric style, use the main character"},
    )
    assert r3.status_code == 200, r3.text
    body = r3.json()
    assert "concepts" in body and len(body["concepts"]) >= 1
    concept_id = body["concepts"][0]["id"]
    assert body["concepts"][0]["status"] == "generating"

    # 4. Poll until complete (skip in CI if no FAL_API_KEY)
    if not os.getenv("FAL_API_KEY"):
        pytest.skip("FAL_API_KEY not set — skipping generation poll")

    r4 = None
    for _ in range(30):
        r4 = client.get(f"/api/books/{book_id}/cover-concepts")
        assert r4.status_code == 200, r4.text
        concepts = r4.json()
        concept = next((c for c in concepts if c["id"] == concept_id), None)
        if concept and concept.get("status") in ("complete", "failed"):
            break
        time.sleep(2)

    assert r4 is not None
    concepts = r4.json()
    concept = next((c for c in concepts if c["id"] == concept_id), None)
    assert concept is not None, "Concept not found after poll"
    assert concept["status"] == "complete", f"Expected complete, got {concept.get('status')}"
    if concept.get("image_path"):
        assert concept["image_path"].startswith("http") or concept["image_path"].startswith("/")
