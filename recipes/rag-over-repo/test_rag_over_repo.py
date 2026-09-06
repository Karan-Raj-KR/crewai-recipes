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
