"""
Lead Qualification Recipe — crew.py

Assembles the CrewAI Crew: Researcher → Scorer, sequential process.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    company: str, description: str, verbose: bool = False, json_output: bool = False
) -> Crew:
    """Build and return the lead qualification Crew.

    Args:
        company: The company name to qualify.
        description: A short description of the company.
        verbose: Whether to enable verbose agent trace output.
        json_output: Whether to produce a structured JSON scorecard.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    research_agent, scoring_agent = build_agents(verbose=verbose)
    tasks = build_tasks(
        research_agent,
        scoring_agent,
        company,
        description,
        json_output=json_output,
    )

    return Crew(
        agents=[research_agent, scoring_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )
