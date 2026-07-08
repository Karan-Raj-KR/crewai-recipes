"""
FAQ Bot Recipe — crew.py

Assembles the FAQ bot CrewAI Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(customer_question: str, customer_name: str = "Customer") -> Crew:
    """Build and return the FAQ bot Crew.

    Args:
        customer_question: The question to answer.
        customer_name: The customer's name for personalised responses.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    retriever_agent, response_agent = build_agents()
    tasks = build_tasks(retriever_agent, response_agent, customer_question, customer_name)

    crew = Crew(
        agents=[retriever_agent, response_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
