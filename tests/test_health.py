from contextlib import contextmanager

from fastapi.testclient import TestClient

from app.api import health
from app.main import app

client = TestClient(app)


class FakeSession:
    """SELECT 1 chal gaya — asli Postgres ki zarurat nahi"""

    def execute(self, statement):
        return None


@contextmanager
def working_db():
    yield FakeSession()


def test_health_reports_ok_when_database_reachable(monkeypatch):
    # Pehle ye test asli Postgres maangta tha, isliye DB band hone par fail hota
    # tha aur CI mein chal hi nahi sakta tha
    monkeypatch.setattr(health, "get_db", working_db)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_health_reports_unreachable_database_without_crashing(monkeypatch):
    def broken_session():
        raise Exception("database is down")

    monkeypatch.setattr(health, "get_db", broken_session)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["database"] == "unreachable"
