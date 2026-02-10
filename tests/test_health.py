"""Tests for health check endpoints."""


def test_root_endpoint(client):
    """GET / returns OK status."""
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OK"


def test_health_endpoint(client):
    """GET /health returns database status."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "database" in data
