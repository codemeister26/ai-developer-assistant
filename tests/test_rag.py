import pytest

from app.rag.chunking import split_text
from app.rag.embeddings import cosine_similarity
from app.rag.extract import UnsupportedFile, extension_of, extract_text


# ─── Chunking ─────────────────────────────────────────────────────────────────

def test_short_text_stays_one_chunk():
    assert split_text("chhota text", size=100) == ["chhota text"]


def test_long_text_is_split():
    chunks = split_text("x" * 500, size=100, overlap=10)

    assert len(chunks) > 1


def test_every_chunk_respects_the_size_limit():
    chunks = split_text("word " * 400, size=200, overlap=20)

    assert all(len(c) <= 200 for c in chunks)


def test_nothing_is_lost_when_splitting():
    """Overlap ke saath bhi har hissa kisi na kisi chunk mein hona chahiye"""
    text = "\n\n".join(f"paragraph {i} with some content" for i in range(30))

    joined = " ".join(split_text(text, size=200, overlap=40))

    assert "paragraph 0" in joined
    assert "paragraph 29" in joined


def test_chunks_overlap_so_meaning_is_not_cut_at_the_edge():
    chunks = split_text("x" * 300, size=100, overlap=30)

    # Overlap ka matlab — tukdon ki kul lambai original se zyada hogi
    assert sum(len(c) for c in chunks) > 300


def test_empty_text_gives_no_chunks():
    assert split_text("") == []
    assert split_text("   \n\n  ") == []


def test_splitting_always_terminates():
    """Overlap size se bada ho toh loop atak sakta tha"""
    chunks = split_text("x" * 1000, size=50, overlap=80)

    assert len(chunks) > 0


# ─── Similarity ───────────────────────────────────────────────────────────────

def test_identical_vectors_score_one():
    assert cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0]) == pytest.approx(1.0)


def test_opposite_vectors_score_minus_one():
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)


def test_unrelated_vectors_score_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_zero_vector_does_not_divide_by_zero():
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0


# ─── Extraction ───────────────────────────────────────────────────────────────

def test_text_file_is_read():
    assert extract_text("notes.md", b"# Heading\n\ncontent") == "# Heading\n\ncontent"


def test_code_files_are_supported():
    assert extract_text("main.py", b"print('hi')") == "print('hi')"


def test_unsupported_type_is_rejected_clearly():
    with pytest.raises(UnsupportedFile, match="supported nahi"):
        extract_text("photo.jpg", b"\xff\xd8\xff")


def test_broken_pdf_is_rejected_not_crashed():
    with pytest.raises(UnsupportedFile):
        extract_text("broken.pdf", b"not really a pdf")


def test_bad_bytes_do_not_fail_the_whole_upload():
    """Ek ajeeb byte ke liye poori file reject karna theek nahi"""
    assert "hello" in extract_text("notes.txt", b"hello \xff\xfe world")


@pytest.mark.parametrize(
    "filename,expected",
    [("a.PDF", ".pdf"), ("a.tar.gz", ".gz"), ("noext", "")],
)
def test_extension_detection(filename, expected):
    assert extension_of(filename) == expected


# ─── Sources ──────────────────────────────────────────────────────────────────

def test_build_context_reports_which_files_it_used(monkeypatch):
    from app.rag import documents

    monkeypatch.setattr(documents, "search", lambda q, u=None: [
        {"content": "a", "filename": "manual.pdf", "score": 0.9},
        {"content": "b", "filename": "notes.md", "score": 0.8},
    ])

    context, sources = documents.build_context("q")

    assert sources == ["manual.pdf", "notes.md"]
    assert "manual.pdf" in context


def test_same_file_is_named_only_once(monkeypatch):
    """Ek hi PDF ke kai chunks mil sakte hain — naam ek hi baar dikhe"""
    from app.rag import documents

    monkeypatch.setattr(documents, "search", lambda q, u=None: [
        {"content": "a", "filename": "manual.pdf", "score": 0.9},
        {"content": "b", "filename": "manual.pdf", "score": 0.8},
    ])

    _, sources = documents.build_context("q")

    assert sources == ["manual.pdf"]


def test_no_matches_means_no_context_and_no_sources(monkeypatch):
    from app.rag import documents

    monkeypatch.setattr(documents, "search", lambda q, u=None: [])

    assert documents.build_context("q") == ("", [])
