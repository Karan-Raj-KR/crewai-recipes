"""
Lead Qualification Recipe — crew.py

Assembles the CrewAI Crew: Researcher → Scorer, sequential process.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(company: str, description: str) -> Crew:
    """Build and return the lead qualification Crew.

    Args:
        company: The company name to qualify.
        description: A short description of the company.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    research_agent, scoring_agent = build_agents()
    tasks = build_tasks(research_agent, scoring_agent, company, description)

    return Crew(
        agents=[research_agent, scoring_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
