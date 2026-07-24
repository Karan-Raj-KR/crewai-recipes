"""
Content Pipeline Recipe — crew.py

Assembles the 4-agent content production pipeline Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    topic: str,
    target_audience: str = "General Tech Audience",
    keywords: str = "AI, Automation",
) -> Crew:
    """Build and return the content production pipeline Crew.

    Args:
        topic: Core topic or theme.
        target_audience: Target readership profile.
        keywords: Comma-separated target keywords.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    ideator_agent, researcher_agent, writer_agent, seo_agent = build_agents()
    tasks = build_tasks(
        ideator_agent,
        researcher_agent,
        writer_agent,
        seo_agent,
        topic=topic,
        target_audience=target_audience,
        keywords=keywords,
    )

    crew = Crew(
        agents=[ideator_agent, researcher_agent, writer_agent, seo_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
