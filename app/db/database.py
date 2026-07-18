from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker , DeclarativeBase
from app.config.settings import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass
