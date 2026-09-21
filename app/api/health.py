from fastapi import APIRouter
from sqlalchemy import text
from app.db.database import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
def health():
    db_status = "ok"
    try:
        with get_db() as db:
            db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("Health check: database unreachable")
        db_status = "unreachable"

    return {
        "status": "ok",
        "message": "Backend is running successfully",
        "database": db_status
    }
