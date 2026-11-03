"""
Meeting Notes Summariser Recipe — crew.py

Assembles the Crew. The build_crew() function signature MUST match the keys
in inputs.json — the playground calls it as build_crew(**req.inputs).

inputs.json for this recipe has a single key, "transcript", so:
    build_crew(transcript: str) -> Crew
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(transcript: str) -> Crew:
    """Build and return the meeting-notes Crew.

    The parameter name MUST match the "name" field in inputs.json. The
    playground calls this as build_crew(**req.inputs).

    Args:
        transcript: The raw meeting notes / transcript text.

    Returns:
        A configured sequential Crew (extractor -> drafter) ready for .kickoff().

    Raises:
        ValueError: If the transcript is empty or whitespace only.
    """
    if not transcript or not transcript.strip():
        raise ValueError("transcript must not be empty")

    extractor_agent, drafter_agent = build_agents()
    tasks = build_tasks(extractor_agent, drafter_agent, transcript.strip())

    crew = Crew(
        agents=[extractor_agent, drafter_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew