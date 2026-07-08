"""
FAQ Bot Recipe — agents.py

Two-agent crew for answering customer questions from a knowledge base:
  1. KnowledgeRetrieverAgent — searches the FAQ knowledge base for relevant answers
  2. ResponseDraftingAgent   — crafts a clear, helpful customer-facing response
"""

import os

from crewai import Agent
from langchain_groq import ChatGroq


def _get_llm(model: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Instantiate the Groq LLaMA LLM.

    Args:
        model: Groq model identifier.

    Returns:
        A configured ChatGroq instance.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Export it or add it to your .env file."
        )
    return ChatGroq(model=model, api_key=api_key, temperature=0.1)


def build_agents() -> tuple[Agent, Agent]:
    """Build and return the FAQ bot agents.

    Returns:
        A tuple of (retriever_agent, response_agent).
    """
    llm = _get_llm()

    retriever_agent = Agent(
        role="FAQ Knowledge Retriever",
        goal=(
            "Search the provided knowledge base to find the most relevant "
            "answer entries for the customer's question. If no direct match "
            "is found, identify the closest related topics and flag the gap."
        ),
        backstory=(
            "You are a librarian-level information specialist who can quickly "
            "scan a knowledge base and surface the most relevant excerpts. "
            "You are rigorous: you only surface information that genuinely "
            "addresses the question and clearly mark when no match exists. "
            "You never make up information that is not in the knowledge base."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    response_agent = Agent(
        role="Customer Support Response Writer",
        goal=(
            "Transform the retrieved knowledge base excerpts into a warm, "
            "clear, and complete customer-facing response. If the knowledge "
            "base did not contain a relevant answer, craft a graceful "
            "fallback message and suggest contacting support."
        ),
        backstory=(
            "You are a senior customer success specialist with a gift for "
            "turning technical documentation into human-friendly answers. "
            "Your responses are always empathetic, concise, and actionable. "
            "You never leave a customer without a clear next step."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return retriever_agent, response_agent
