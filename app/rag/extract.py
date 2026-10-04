# ─── Text extraction ──────────────────────────────────────────────────────────
# Upload kiye file se plain text nikalo. Sirf wahi formats jinse text sach
# mein nikal sakta hai — baaki ko saaf mana kar dete hain.

from io import BytesIO
import logging

logger = logging.getLogger(__name__)

TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst", ".csv", ".json", ".py",
                   ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".sql",
                   ".yml", ".yaml", ".html", ".css", ".sh"}


class UnsupportedFile(Exception):
    """Is file se text nahi nikal sakte"""


def extension_of(filename: str) -> str:
    return "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def extract_text(filename: str, data: bytes) -> str:
    extension = extension_of(filename)

    if extension == ".pdf":
        return _from_pdf(data)

    if extension in TEXT_EXTENSIONS:
        # Kuch files mein ajeeb bytes hote hain — poora upload fail karne se
        # behtar hai unhe chhod dena
        return data.decode("utf-8", errors="replace")

    raise UnsupportedFile(
        f"'{extension or filename}' supported nahi hai. PDF ya text file bhejo."
    )


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as e:
        raise UnsupportedFile("Ye PDF padhi nahi ja saki") from e

    text = "\n\n".join(p.strip() for p in pages if p.strip())

    if not text.strip():
        # Scanned PDF mein sirf images hoti hain — OCR ke bina kuch nahi milega
        raise UnsupportedFile(
            "Is PDF mein text nahi mila. Scanned PDF ho sakti hai — "
            "uske liye OCR chahiye hoga."
        )

    return text
