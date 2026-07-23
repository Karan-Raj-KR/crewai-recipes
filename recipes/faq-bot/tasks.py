"""
FAQ Bot Recipe — tasks.py

Single task: answer a customer question from the knowledge base.
"""

from crewai import Agent, Task

from knowledge_base import get_knowledge_base_text


def build_tasks(
    support_agent: Agent,
    question: str,
    customer_name: str = "there",
) -> list[Task]:
    """Build the task list for the FAQ bot crew.

    Args:
        support_agent: The single support agent.
        question: The customer's question.
        customer_name: Optional customer name for a personalised reply.

    Returns:
        A list with a single Task.
    """
    kb_text = get_knowledge_base_text()

    answer_task = Task(
        description=(
            f"A customer named '{customer_name}' has sent this question:\n\n"
            f'  "{question}"\n\n'
            "Use the knowledge base below to find the answer.\n\n"
            f"{kb_text}\n\n"
            "Reply guidelines:\n"
            f"1. Start with 'Hi {customer_name},' (use their name).\n"
            "2. Answer directly from the knowledge base — do not guess.\n"
            "3. If no entry matches, say so honestly and suggest they email "
            "   support@orbitly.example.com or start a chat on the website.\n"
            "4. End with: 'Is there anything else I can help with?'\n"
            "5. Keep the reply under 120 words.\n"
            "6. Plain text only — no markdown."
        ),
        expected_output=(
            "A complete customer support reply in plain text. "
            "Warm, accurate, under 120 words."
        ),
        agent=support_agent,
    )

    return [answer_task]
