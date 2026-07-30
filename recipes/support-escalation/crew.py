"""
Support Escalation Recipe — crew.py

Assembles the 3-agent support ticket escalation workflow Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    ticket_text: str,
    customer_tier: str = "pro",
    previous_contacts: str = "0",
) -> Crew:
    """Build and return the support ticket escalation workflow Crew.

    Args:
        ticket_text: Description of the customer support issue.
        customer_tier: Account tier (free, pro, enterprise).
        previous_contacts: Number of previous contact attempts.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    triage_agent, resolver_agent, escalation_agent = build_agents()
    tasks = build_tasks(
        triage_agent,
        resolver_agent,
        escalation_agent,
        ticket_text=ticket_text,
        customer_tier=customer_tier,
        previous_contacts=previous_contacts,
    )

    crew = Crew(
        agents=[triage_agent, resolver_agent, escalation_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
