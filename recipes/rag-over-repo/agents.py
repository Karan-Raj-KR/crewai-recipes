"""agents.py — Agent definitions for the rag-over-repo recipe.

Defines two specialized agents:
  1. Documentation Retriever Agent: Organizes and verifies relevant document chunks.
  2. Technical Documentation Answerer Agent: Formulates accurate answers with inline
     citations `[file_path#heading]` or explicitly refuses to answer if context is absent.
"""

from crewai import Agent
from llm import get_llm


def create_retriever_agent(llm=None) -> Agent:
    """Create the Document Retriever Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="Documentation Search Specialist",
        goal="Select and organize relevant documentation snippets for the user query.",
        backstory=(
            "You are an expert technical indexer. Your job is to analyze retrieved documentation "
            "snippets, verify their relevance to the user's question, and format them cleanly "
            "with precise source metadata (file paths and section headers) so the answering agent "
            "has accurate factual context."
        ),
        llm=llm,
        verbose=True,
    )


def create_answerer_agent(llm=None) -> Agent:
    """Create the Technical Documentation Answerer Agent."""
    if llm is None:
        llm = get_llm()

    return Agent(
        role="Technical Documentation Answerer",
        goal=(
            "Answer user questions accurately based strictly on retrieved documentation context with "
            "inline citations [file_path#heading], or state 'I don't know based on the provided docs' "
            "if the context does not contain the answer."
        ),
        backstory=(
            "You are a strict, precise technical writer. You never guess or synthesize facts "
            "outside the provided documentation context. Whenever you provide information, you append "
            "an inline citation matching the exact format `[file_path#heading]`. If the documentation "
            "context is empty or does not explicitly contain the answer, you must respond with: "
            "'I don't know based on the provided docs.'"
        ),
        llm=llm,
        verbose=True,
    )
