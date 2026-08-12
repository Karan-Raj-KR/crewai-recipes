"""
Template Recipe — crew.py

Assembles your Crew. The build_crew() function signature MUST match the keys
in inputs.json — the playground calls it as build_crew(**req.inputs).

For example, if inputs.json has {"name": "...", "topic": "..."},
then build_crew(name: str, topic: str) -> Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    # TODO: Add your input parameters here. The parameter names MUST match
    # the "name" field in inputs.json. For example, if inputs.json has
    # {"name": "user_input", "label": "Your Input"},
    # then add: user_input: str
    **kwargs,
) -> Crew:
    """Build and return your Crew.

    The parameter names MUST match the keys in inputs.json. The playground
    calls this as build_crew(**req.inputs).

    Args:
        **kwargs: Input parameters matching inputs.json keys.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """

    # TODO: Extract your parameters from kwargs if needed.
    # For example: user_input = kwargs.get("user_input")

    my_agent = build_agents()
    tasks = build_tasks(my_agent)

    crew = Crew(
        agents=[my_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
