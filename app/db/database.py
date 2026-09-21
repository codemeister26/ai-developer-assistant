from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , DeclarativeBase
from app.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass


@contextmanager
def get_db():
    """Database session ka ek hi sahi tareeka — error pe rollback, hamesha close.

    Bina rollback ke fail hui transaction session mein padi reh jaati hai aur
    agli query ko bhi le dubti hai.
    """
    db = SessionLocal()

    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
