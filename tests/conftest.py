import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db import models   # noqa: F401 — import zaruri hai taaki tables register hon


@pytest.fixture
def db():
    """Har test ke liye fresh in-memory database — asli Postgres ko haath nahi lagta"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()

    try:
        yield session
    finally:
        session.close()
        engine.dispose()
