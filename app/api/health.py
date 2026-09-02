from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import SessionLocal

router = APIRouter()

@router.get("/health")
def health():
    db_status = "ok"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception:
        db_status = "unreachable"

    return {
        "status": "ok",
        "message": "Backend is running successfully",
        "database": db_status
    }
