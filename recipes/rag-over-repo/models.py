"""Pydantic data models for the rag-over-repo recipe."""

from pydantic import BaseModel, Field


class DocChunk(BaseModel):
    """Represents a chunk of text extracted from a documentation file."""

    chunk_id: str = Field(description="Unique identifier for the chunk.")
    file_path: str = Field(description="Relative path of the source file.")
    heading: str = Field(default="General", description="Section heading or title.")
    content: str = Field(description="Text content of the document chunk.")
    score: float | None = Field(default=0.0, description="Relevance score.")


class RetrievalResult(BaseModel):
    """Container for document chunks retrieved for a query."""

    query: str = Field(description="User query or question.")
    chunks: list[DocChunk] = Field(
        default_factory=list, description="Retrieved relevant chunks."
    )
    formatted_context: str = Field(
        description="Formatted context string passed to the LLM."
    )


class Citation(BaseModel):
    """Source citation reference."""

    file_path: str = Field(description="Relative file path.")
    heading: str = Field(description="Section heading or header.")


class RAGAnswer(BaseModel):
    """Final output response structure for the RAG answer."""

    question: str = Field(description="Original user question.")
    answer: str = Field(
        description="Answer synthesized from retrieved docs or refusal message."
    )
    citations: list[Citation] = Field(
        default_factory=list, description="List of source citations used."
    )
    refused: bool = Field(
        default=False, description="True if docs did not contain relevant information."
    )
