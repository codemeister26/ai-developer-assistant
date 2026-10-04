# ─── Chunking ─────────────────────────────────────────────────────────────────
# Poora document ek saath embed nahi kar sakte — embedding model ki apni limit
# hai, aur bade tukde ka matlab dhundhla ho jaata hai. Isliye tukdon mein todte
# hain, thode overlap ke saath taaki boundary par baat na kate.

from app.config.settings import CHUNK_OVERLAP, CHUNK_SIZE
import re


def split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Text ko overlapping chunks mein todo.

    Paragraph boundary par todne ki koshish karte hain; na mile toh size par.
    """
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if not text:
        return []

    if len(text) <= size:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + size

        if end < len(text):
            # Paragraph ya line break dhoondo taaki beech se na kate
            window = text[start:end]
            cut = max(window.rfind("\n\n"), window.rfind("\n"))

            # Bahut peeche ka break ho toh faayda nahi, size par hi kaat do
            if cut > size // 2:
                end = start + cut

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)   # start hamesha aage badhe

    return chunks
