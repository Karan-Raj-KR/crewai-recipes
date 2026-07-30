"""
Email Drafting Recipe — crew.py

Assembles the 2-agent email drafting workflow Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    recipient: str,
    purpose: str,
    key_points: str,
    tone: str = "professional",
) -> Crew:
    """Build and return the email drafting workflow Crew.

    Args:
        recipient: Recipient name or role.
        purpose: Main purpose of the email.
        key_points: Key points to include.
        tone: Desired tone (professional / friendly / formal / direct).

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    drafter_agent, editor_agent = build_agents()
    tasks = build_tasks(
        drafter_agent,
        editor_agent,
        recipient=recipient,
        purpose=purpose,
        key_points=key_points,
        tone=tone,
    )

    crew = Crew(
        agents=[drafter_agent, editor_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
