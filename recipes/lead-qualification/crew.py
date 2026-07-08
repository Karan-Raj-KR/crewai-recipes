"""
Lead Qualification Recipe — crew.py

Assembles the CrewAI Crew from agents and tasks.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(lead_data: dict[str, str]) -> Crew:
    """Build and return the lead qualification Crew.

    Args:
        lead_data: Dictionary containing raw lead information.
            Expected keys: name, company, role, email, notes (optional).

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    research_agent, scoring_agent, summary_agent = build_agents()
    tasks = build_tasks(research_agent, scoring_agent, summary_agent, lead_data)

    crew = Crew(
        agents=[research_agent, scoring_agent, summary_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
