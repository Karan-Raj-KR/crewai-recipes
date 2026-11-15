"""Unit tests for the rag-over-repo recipe."""

import shutil
from pathlib import Path

import pytest
from ingest import (
    extract_chunks_from_markdown,
    extract_chunks_from_rst,
    extract_chunks_from_txt,
    find_doc_files,
    ingest_docs_directory,
)
from models import RAGAnswer
from retriever import DocumentRetriever


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "tests" / "fixtures"


def test_find_doc_files(fixtures_dir: Path):
    doc_files = find_doc_files(fixtures_dir)
    file_names = [f.name for f in doc_files]
    assert "architecture.md" in file_names
    assert "installation.txt" in file_names
    assert "faq.rst" in file_names


@pytest.mark.parametrize("location", ["docs", ".workspace/project/docs", ".docs"])
@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
def test_find_doc_files_under_selected_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    location: str,
    relative: bool,
) -> None:
    """Selected roots remain readable while hidden descendants stay excluded."""
    docs_dir = tmp_path / location
    for name in (
        "guide.md",
        "notes.txt",
        "nested/install.RST",
        "unsupported.py",
        ".git/internal.md",
        ".rag-cache/snapshot.txt",
        "nested/.private/secret.rst",
    ):
        path = docs_dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Documentation", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    search_root = docs_dir.relative_to(tmp_path) if relative else docs_dir
    found = find_doc_files(search_root)

    assert found == sorted(found)
    assert [path.relative_to(search_root).as_posix() for path in found] == [
        "guide.md",
        "nested/install.RST",
        "notes.txt",
    ]


def test_retrieval_under_hidden_ancestor(tmp_path: Path) -> None:
    """Real ingestion and cached retrieval retain docs under a hidden ancestor."""
    docs_dir = tmp_path / ".workspace" / "docs"
    docs_dir.mkdir(parents=True)
    (docs_dir / "guide.md").write_text(
        "# Installation\nInstall widgets with pip.", encoding="utf-8"
    )

    for cached in (False, True):
        retriever = DocumentRetriever(docs_dir)
        result = retriever.retrieve("Install widgets")
        assert retriever.is_cached is cached
        assert len(result.chunks) == 1
        assert result.chunks[0].file_path == "guide.md"
        assert "Install widgets with pip." in result.formatted_context


def test_extract_chunks_markdown():
    content = (
        "# Main Title\n\nSome intro text.\n\n## Section One\n\nSection one content."
    )
    chunks = extract_chunks_from_markdown(content, "test.md")
    assert len(chunks) == 2
    assert chunks[0].heading == "Main Title"
    assert "intro text" in chunks[0].content
    assert chunks[1].heading == "Section One"
    assert "Section one content" in chunks[1].content


def test_extract_chunks_rst():
    content = "Title Header\n============\n\nIntro rst text.\n\nSub Header\n----------\n\nSub header text."
    chunks = extract_chunks_from_rst(content, "test.rst")
    assert len(chunks) >= 1
    headings = [c.heading for c in chunks]
    assert "Title Header" in headings or "Sub Header" in headings


def test_extract_chunks_txt():
    content = "First paragraph of text.\n\nSecond paragraph of text."
    chunks = extract_chunks_from_txt(content, "test.txt")
    assert len(chunks) == 2
    assert chunks[0].heading == "Paragraph 1"
    assert chunks[1].heading == "Paragraph 2"


def test_ingest_and_caching(fixtures_dir: Path):
    cache_dir = fixtures_dir / ".rag-cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    try:
        # First run: parse and create cache
        chunks1, is_cached1 = ingest_docs_directory(fixtures_dir)
        assert len(chunks1) > 0
        assert is_cached1 is False
        assert cache_dir.exists()

        # Second run: serve from cache
        chunks2, is_cached2 = ingest_docs_directory(fixtures_dir)
        assert len(chunks2) == len(chunks1)
        assert is_cached2 is True
    finally:
        if cache_dir.exists():
            shutil.rmtree(cache_dir)


def test_retriever_query(fixtures_dir: Path):
    retriever = DocumentRetriever(fixtures_dir)
    res = retriever.retrieve("How do I install dependencies?", top_k=2)

    assert len(res.chunks) > 0
    assert any("installation.txt" in c.file_path for c in res.chunks)
    assert (
        "[NO RELEVANT DOCUMENTATION CONTEXT FOUND FOR QUERY]"
        not in res.formatted_context
    )


def test_refusal_when_unrelated_query(fixtures_dir: Path):
    retriever = DocumentRetriever(fixtures_dir)
    res = retriever.retrieve(
        "quantum entanglement in astrophysics", top_k=2, min_score=0.2
    )

    assert len(res.chunks) == 0
    assert (
        "[NO RELEVANT DOCUMENTATION CONTEXT FOUND FOR QUERY]" in res.formatted_context
    )


def test_rag_answer_model():
    ans = RAGAnswer(
        question="What database is used?",
        answer="PostgreSQL is used for relational data [architecture.md#Data Layer].",
        citations=[{"file_path": "architecture.md", "heading": "Data Layer"}],
        refused=False,
    )
    assert ans.refused is False
    assert len(ans.citations) == 1
    assert ans.citations[0].file_path == "architecture.md"
