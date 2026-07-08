"""
FAQ Bot Recipe — tasks.py

Defines two tasks: retrieval from the knowledge base, and response drafting.
"""

from crewai import Agent, Task

from knowledge_base import get_knowledge_base_text


def build_tasks(
    retriever_agent: Agent,
    response_agent: Agent,
    customer_question: str,
    customer_name: str = "Customer",
) -> list[Task]:
    """Build the task list for the FAQ bot crew.

    Args:
        retriever_agent: Agent that searches the knowledge base.
        response_agent: Agent that drafts the final response.
        customer_question: The question submitted by the customer.
        customer_name: Optional name of the customer for personalisation.

    Returns:
        An ordered list of Task objects.
    """
    kb_text = get_knowledge_base_text()

    retrieval_task = Task(
        description=(
            f"A customer named '{customer_name}' has asked the following question:\n\n"
            f'  "{customer_question}"\n\n'
            "Search the knowledge base below and identify the most relevant "
            "entries that address this question. Quote the relevant answer "
            "text directly. If no entry matches, say so explicitly and "
            "identify the closest related topic.\n\n"
            f"{kb_text}"
        ),
        expected_output=(
            "A retrieval report in markdown with two sections:\n"
            "1. **Matched Entries** — quoted relevant passages from the KB "
            "   (or 'No direct match found' if nothing applies).\n"
            "2. **Gap Analysis** — any aspect of the question not covered by "
            "   the knowledge base."
        ),
        agent=retriever_agent,
    )

    response_task = Task(
        description=(
            f"Using the retrieval results, write a customer-facing response "
            f"to {customer_name}'s question:\n\n"
            f'  "{customer_question}"\n\n'
            "Guidelines:\n"
            "- Start with a warm, personalised greeting using their name.\n"
            "- Answer the question directly using the retrieved KB content.\n"
            "- If the KB had no match, acknowledge the question, apologise "
            "  briefly, and invite them to contact support.\n"
            "- End with a friendly offer to help further.\n"
            "- Keep it under 120 words.\n"
            "- Do NOT invent information not in the retrieved content."
        ),
        expected_output=(
            "A complete, ready-to-send customer support response in plain "
            "text (no markdown). Warm, concise, and actionable."
        ),
        agent=response_agent,
        context=[retrieval_task],
    )

    return [retrieval_task, response_task]
