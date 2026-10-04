from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from datetime import datetime

from app.api.auth import current_user
from app.config.settings import MAX_UPLOAD_MB
from app.rag import documents
from app.rag.embeddings import EmbeddingError
from app.rag.extract import UnsupportedFile
from typing import List

router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


class DocumentOut(BaseModel):
    id: int
    filename: str
    chunk_count: int
    created_at: datetime


def _uid(user: dict | None) -> int | None:
    return user["id"] if user else None


@router.get("", response_model=List[DocumentOut])
def list_all(user: dict | None = Depends(current_user)):
    return documents.list_documents(_uid(user))


@router.post("", response_model=DocumentOut)
async def upload(
    file: UploadFile = File(...),
    user: dict | None = Depends(current_user),
):
    """File upload karo — wo chunks mein tut kar index ho jaayegi"""
    data = await file.read()

    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum is {MAX_UPLOAD_MB} MB.",
        )

    if not data:
        raise HTTPException(status_code=400, detail="File is empty")

    try:
        return documents.ingest(file.filename or "upload", data, _uid(user))

    except (UnsupportedFile, documents.EmptyDocument) as e:
        # User ki file ka masla hai — 400, aur wajah batao
        raise HTTPException(status_code=400, detail=str(e))

    except EmbeddingError as e:
        # Embedding model missing ya band — ye setup ka masla hai
        raise HTTPException(status_code=503, detail=str(e))


@router.delete("/{document_id}")
def remove(document_id: int, user: dict | None = Depends(current_user)):
    if not documents.delete_document(document_id, _uid(user)):
        raise HTTPException(status_code=404, detail="Document not found")

    return {"message": "Document deleted", "id": document_id}
