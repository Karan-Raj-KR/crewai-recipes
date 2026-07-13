"""
FAQ Bot Recipe — crew.py

Assembles the single-agent FAQ crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(question: str, customer_name: str = "there") -> Crew:
    """Build and return the FAQ bot Crew.

    Args:
        question: The customer's question.
        customer_name: Optional customer name for personalised replies.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    support_agent = build_agents()
    tasks = build_tasks(support_agent, question, customer_name)

    return Crew(
        agents=[support_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
