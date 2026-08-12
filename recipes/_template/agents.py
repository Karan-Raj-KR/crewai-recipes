"""
Template Recipe — agents.py

Defines the agents for your crew. Every agent needs a role, goal, and backstory.
Replace the TODO comments with your agent definitions.
"""

from crewai import Agent

from llm import get_llm


def build_agents() -> Agent:
    """Build and return your crew's agent(s).

    Replace this function with your agent definitions. This template shows a
    single agent; you can add more by returning a tuple or list.

    Returns:
        An Agent instance (or tuple of agents if you have multiple).
    """
    llm = get_llm()

    # TODO: Replace this agent with your agent definition.
    # Change the role, goal, and backstory to match your use case.
    # Make sure to pass llm=llm to the Agent constructor.
    my_agent = Agent(
        role="TODO: Define your agent's role (e.g. 'Research Analyst')",
        goal=(
            "TODO: Define your agent's goal. What should it accomplish? "
            "(e.g. 'Gather comprehensive market research data')"
        ),
        backstory=(
            "TODO: Define your agent's backstory. Who is this agent and why is it skilled? "
            "(e.g. 'You are an experienced market researcher with 10 years of experience')"
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return my_agent
