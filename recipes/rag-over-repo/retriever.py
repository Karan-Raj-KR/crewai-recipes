"""retriever.py — Lightweight vector retriever and similarity engine for local docs.

Uses TF-IDF vectorization and Cosine Similarity to retrieve top-k document chunks
matching a user question. No external vector DB or server required.
"""

import math
import re
from collections import Counter
from pathlib import Path

from ingest import ingest_docs_directory
from models import Citation, DocChunk, RetrievalResult


def tokenize(text: str) -> list[str]:
    """Tokenize and normalize text into lowercase alphanumeric terms."""
    return re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())


def compute_tf(tokens: list[str]) -> Counter:
    """Compute term frequencies for a list of tokens."""
    return Counter(tokens)


def compute_idf(corpus_tokens: list[list[str]]) -> dict:
    """Compute inverse document frequency (IDF) across chunks."""
    num_docs = len(corpus_tokens)
    if num_docs == 0:
        return {}

    df = Counter()
    for tokens in corpus_tokens:
        unique_terms = set(tokens)
        for term in unique_terms:
            df[term] += 1

    idf = {}
    for term, count in df.items():
        idf[term] = math.log((1.0 + num_docs) / (1.0 + count)) + 1.0
    return idf


def tfidf_vector(tokens: list[str], idf: dict) -> dict:
    """Compute TF-IDF vector for a tokenized text."""
    tf = compute_tf(tokens)
    vec = {}
    length_sq = 0.0
    for term, freq in tf.items():
        if term in idf:
            weight = (1 + math.log(freq)) * idf[term]
            vec[term] = weight
            length_sq += weight * weight

    # Normalize vector to unit length
    length = math.sqrt(length_sq)
    if length > 0:
        for term in vec:
            vec[term] /= length
    return vec


def cosine_similarity(vec1: dict, vec2: dict) -> float:
    """Calculate cosine similarity between two unit-normalized TF-IDF vectors."""
    score = 0.0
    for term, weight in vec1.items():
        if term in vec2:
            score += weight * vec2[term]
    return score


class DocumentRetriever:
    """Retriever class for querying locally ingested documentation chunks."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir).resolve()
        self.chunks: list[DocChunk] = []
        self.is_cached: bool = False
        self.corpus_tokens: list[list[str]] = []
        self.idf: dict = {}
        self.doc_vectors: list[dict] = []
        self._initialize_index()

    def _initialize_index(self):
        """Ingest docs and build local TF-IDF index."""
        self.chunks, self.is_cached = ingest_docs_directory(self.docs_dir)
        self.corpus_tokens = [tokenize(f"{c.heading} {c.content}") for c in self.chunks]
        self.idf = compute_idf(self.corpus_tokens)
        self.doc_vectors = [
            tfidf_vector(tokens, self.idf) for tokens in self.corpus_tokens
        ]

    def retrieve(
        self, query: str, top_k: int = 4, min_score: float = 0.05
    ) -> RetrievalResult:
        """Retrieve top-k relevant chunks for a user query.

        Args:
            query: User question string.
            top_k: Number of top chunks to return.
            min_score: Minimum similarity score threshold.

        Returns:
            RetrievalResult containing retrieved chunks and formatted context.
        """
        if not self.chunks:
            return RetrievalResult(
                query=query,
                chunks=[],
                formatted_context="[NO DOCUMENTATION CHUNKS FOUND IN DIRECTORY]",
            )

        query_tokens = tokenize(query)
        query_vec = tfidf_vector(query_tokens, self.idf)

        scored_chunks: list[tuple[float, DocChunk]] = []
        for idx, doc_vec in enumerate(self.doc_vectors):
            score = cosine_similarity(query_vec, doc_vec)
            if score >= min_score:
                chunk_copy = self.chunks[idx].model_copy()
                chunk_copy.score = round(score, 4)
                scored_chunks.append((score, chunk_copy))

        # Sort by relevance score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        top_chunks = [item[1] for item in scored_chunks[:top_k]]

        if not top_chunks:
            formatted_context = "[NO RELEVANT DOCUMENTATION CONTEXT FOUND FOR QUERY]"
        else:
            context_blocks = []
            for chunk in top_chunks:
                header = f"--- Source: {chunk.file_path}#{chunk.heading} (Relevance Score: {chunk.score}) ---"
                context_blocks.append(f"{header}\n{chunk.content}")
            formatted_context = "\n\n".join(context_blocks)

        return RetrievalResult(
            query=query,
            chunks=top_chunks,
            formatted_context=formatted_context,
        )

    def extract_citations(self, chunks: list[DocChunk]) -> list[Citation]:
        """Extract unique citations from retrieved chunks."""
        seen = set()
        citations = []
        for chunk in chunks:
            key = (chunk.file_path, chunk.heading)
            if key not in seen:
                seen.add(key)
                citations.append(
                    Citation(file_path=chunk.file_path, heading=chunk.heading)
                )
        return citations
