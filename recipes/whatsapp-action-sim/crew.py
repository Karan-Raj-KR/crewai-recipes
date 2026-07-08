"""
WhatsApp Action Sim Recipe — crew.py

Assembles the WhatsApp action simulation Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(user_message: str, sender_name: str = "User") -> Crew:
    """Build and return the WhatsApp action simulation Crew.

    Args:
        user_message: The incoming WhatsApp message text.
        sender_name: The sender's display name.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    intent_agent, router_agent, composer_agent = build_agents()
    tasks = build_tasks(
        intent_agent, router_agent, composer_agent, user_message, sender_name
    )

    crew = Crew(
        agents=[intent_agent, router_agent, composer_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
