from fastapi.testclient import TestClient

from app.api import health
from app.main import app

client = TestClient(app)


def test_health_reports_ok_when_database_reachable():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_reports_unreachable_database_without_crashing(monkeypatch):
    def broken_session():
        raise Exception("database is down")

    monkeypatch.setattr(health, "SessionLocal", broken_session)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "unreachable"
