# ─── Documents ────────────────────────────────────────────────────────────────
# Upload → text nikalo → chunks → embeddings → DB. Aur sawaal ke waqt ulta:
# sawaal ka embedding → sabse milte-julte chunks.

from app.config.settings import RAG_MIN_SIMILARITY, RAG_TOP_K
from app.db.database import get_db
from app.db.models import Document, DocumentChunk
from app.rag.chunking import split_text
from app.rag.embeddings import cosine_similarity, embed
from app.rag.extract import extract_text
import json
import logging

logger = logging.getLogger(__name__)


class EmptyDocument(Exception):
    """File se kaam ka text nahi nikla"""


def ingest(filename: str, data: bytes, user_id: int | None = None) -> dict:
    """File ko chunks + embeddings mein badal kar save karo"""
    chunks = split_text(extract_text(filename, data))

    if not chunks:
        raise EmptyDocument("Is file mein kuch text nahi mila")

    # Embedding pehle banate hain — fail ho jaye toh adhoora document DB mein
    # nahi reh jaata
    vectors = embed(chunks)

    with get_db() as db:
        document = Document(
            filename=filename, user_id=user_id, chunk_count=len(chunks)
        )
        db.add(document)
        db.flush()          # id chahiye chunks ke liye

        db.add_all([
            DocumentChunk(
                document_id=document.id,
                content=chunk,
                embedding=json.dumps(vector),
            )
            for chunk, vector in zip(chunks, vectors)
        ])
        db.commit()

        logger.info("Indexed %s into %d chunks", filename, len(chunks))
        return _summary(document)


def list_documents(user_id: int | None = None) -> list[dict]:
    with get_db() as db:
        query = db.query(Document)

        if user_id is not None:
            query = query.filter(Document.user_id == user_id)

        return [
            _summary(d) for d in query.order_by(Document.created_at.desc()).all()
        ]


def delete_document(document_id: int, user_id: int | None = None) -> bool:
    with get_db() as db:
        query = db.query(Document).filter(Document.id == document_id)

        if user_id is not None:
            query = query.filter(Document.user_id == user_id)

        document = query.first()

        if document is None:
            return False

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete()
        db.delete(document)
        db.commit()
        return True


def search(question: str, user_id: int | None = None) -> list[dict]:
    """Sawaal se sabse milte-julte chunks do.

    Similarity Python mein nikalte hain. pgvector hota toh DB mein hota, par
    wo extension har jagah nahi hota — personal document collection ke scale
    par ye theek chalta hai.
    """
    with get_db() as db:
        query = db.query(DocumentChunk, Document.filename).join(
            Document, Document.id == DocumentChunk.document_id
        )

        if user_id is not None:
            query = query.filter(Document.user_id == user_id)

        rows = query.all()

    if not rows:
        return []

    question_vector = embed([question])[0]

    scored = [
        {
            "content": chunk.content,
            "filename": filename,
            "score": cosine_similarity(question_vector, json.loads(chunk.embedding)),
        }
        for chunk, filename in rows
    ]

    # Kamzor matches bhejne ka faayda nahi — wo context bhar dete hain aur
    # jawab kharab karte hain
    relevant = [s for s in scored if s["score"] >= RAG_MIN_SIMILARITY]
    relevant.sort(key=lambda s: s["score"], reverse=True)

    return relevant[:RAG_TOP_K]


def build_context(question: str, user_id: int | None = None) -> str:
    """Mile hue chunks ko system prompt mein jodne layak text banao"""
    matches = search(question, user_id)

    if not matches:
        return ""

    sections = "\n\n".join(
        f"[{m['filename']}]\n{m['content']}" for m in matches
    )

    return (
        "\n\nThe user has uploaded documents. Relevant excerpts are below.\n"
        "Use them when they help, and say so when they do not contain the "
        "answer — do not invent details that are not there.\n\n"
        f"{sections}\n"
    )


def _summary(document: Document) -> dict:
    return {
        "id": document.id,
        "filename": document.filename,
        "chunk_count": document.chunk_count,
        "created_at": document.created_at,
    }
