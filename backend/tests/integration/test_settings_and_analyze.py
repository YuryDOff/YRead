"""
Integration tests for Settings providers API (bugs/enhancements 13–14).
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_get_settings_providers_returns_list(client: TestClient):
    """GET /api/settings/providers returns providers with name, label, available."""
    r = client.get("/api/settings/providers")
    assert r.status_code == 200
    data = r.json()
    assert "providers" in data
    providers = data["providers"]
    assert isinstance(providers, list)
    for p in providers:
        assert "name" in p
        assert "label" in p
        assert "available" in p
        assert isinstance(p["available"], bool)
