"""tasks.py — Task definitions for the rag-over-repo recipe.

Defines the task flow:
  1. Retrieval & Context Verification Task
  2. Citation Answering & Refusal Task
"""

from crewai import Task


def create_retrieval_task(
    retriever_agent, question: str, formatted_context: str
) -> Task:
    """Create task to evaluate and format retrieved documentation snippets."""
    return Task(
        description=(
            f"User Question: '{question}'\n\n"
            f"Retrieved Documentation Snippets:\n{formatted_context}\n\n"
            "Analyze the retrieved snippets above. Verify if any snippet contains factual information "
            "relevant to answering the user question. Summarize the pertinent sections along with "
            "their file path and section header metadata."
        ),
        expected_output=(
            "A structured summary of relevant snippets with source metadata (file path and section header), "
            "or a clear note stating no relevant context was found."
        ),
        agent=retriever_agent,
    )


def create_answering_task(answerer_agent, question: str, retrieval_task: Task) -> Task:
    """Create task to synthesize final answer with inline citations or refuse."""
    return Task(
        description=(
            f"Question to answer: '{question}'\n\n"
            "Review the verified documentation context from the previous step. Construct a clear, "
            "factual answer adhering strictly to these rules:\n"
            "1. Every factual statement must be backed by an inline citation in the exact format `[file_path#heading]`.\n"
            "2. Do NOT hallucinate or use outside knowledge.\n"
            "3. If the context is missing, empty, or does not contain the answer, you MUST state:\n"
            "   'I don't know based on the provided docs.'"
        ),
        expected_output=(
            "A concise answer containing inline citations formatted as [file_path#heading], "
            "or exact refusal string 'I don't know based on the provided docs.'"
        ),
        agent=answerer_agent,
        context=[retrieval_task],
    )
