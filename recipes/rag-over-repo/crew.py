"""crew.py — Crew assembly for the rag-over-repo recipe."""

from pathlib import Path

from agents import create_answerer_agent, create_retriever_agent
from crewai import Crew, Process
from llm import get_llm
from retriever import DocumentRetriever
from tasks import create_answering_task, create_retrieval_task


def build_crew(
    docs_dir: str | Path,
    question: str,
    top_k: int = 4,
    llm: object | None = None,
) -> Crew:
    """Build and configure the rag-over-repo Crew.

    Args:
        docs_dir: Path to directory containing documentation files (*.md, *.txt, *.rst).
        question: User question to answer.
        top_k: Number of relevant document chunks to retrieve (default: 4).
        llm: Optional pre-configured LLM instance.

    Returns:
        Configured Crew instance ready for kickoff().
    """
    if llm is None:
        llm = get_llm()

    docs_path = Path(docs_dir).resolve()
    retriever = DocumentRetriever(docs_path)
    retrieval_result = retriever.retrieve(question, top_k=top_k)

    retriever_agent = create_retriever_agent(llm=llm)
    answerer_agent = create_answerer_agent(llm=llm)

    retrieval_task = create_retrieval_task(
        retriever_agent=retriever_agent,
        question=question,
        formatted_context=retrieval_result.formatted_context,
    )

    answering_task = create_answering_task(
        answerer_agent=answerer_agent,
        question=question,
        retrieval_task=retrieval_task,
    )

    return Crew(
        agents=[retriever_agent, answerer_agent],
        tasks=[retrieval_task, answering_task],
        process=Process.sequential,
        verbose=True,
    )
