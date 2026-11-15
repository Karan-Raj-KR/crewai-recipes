"""
Customer Feedback Summariser Recipe — crew.py

Assembles the CrewAI Crew: Feedback Analyst → Action Summariser, sequential process.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(feedback: str, verbose: bool = False, json_output: bool = False) -> Crew:
    """Build and return the customer feedback summariser Crew.

    Args:
        feedback: The raw customer feedback text to analyse.
        verbose: Whether to enable verbose agent trace output.
        json_output: Whether to produce a structured JSON summary (FeedbackSummary).

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    feedback_analyst, action_summariser = build_agents(verbose=verbose)
    tasks = build_tasks(
        feedback_analyst,
        action_summariser,
        feedback,
        json_output=json_output,
    )

    return Crew(
        agents=[feedback_analyst, action_summariser],
        tasks=tasks,
        process=Process.sequential,
        verbose=verbose,
    )
