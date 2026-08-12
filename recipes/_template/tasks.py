"""
Template Recipe — tasks.py

Defines the tasks for your crew. Each task should have a clear description
and expected output.
"""

from crewai import Agent, Task


def build_tasks(my_agent: Agent) -> list[Task]:
    """Build and return the task list for your crew.

    Args:
        my_agent: The agent (or agents) created in agents.py.

    Returns:
        An ordered list of Task objects.
    """

    # TODO: Replace this task with your task definition.
    # Make sure the description is clear, expected_output is concrete,
    # and the agent is set to the right agent from agents.py.
    task_1 = Task(
        description=(
            "TODO: Define your task. What should the agent do? "
            "Be specific and concrete. "
            "(e.g. 'Research the top 5 competitors in the SaaS market for Q1 2025')"
        ),
        expected_output=(
            "TODO: Define the expected output. What format should the result be in? "
            "(e.g. 'A detailed report with competitor names, features, pricing, and market share')"
        ),
        agent=my_agent,
    )

    return [task_1]
