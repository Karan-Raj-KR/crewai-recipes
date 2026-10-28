"""
Customer Onboarding Recipe — crew.py

Assembles the customer onboarding workflow Crew.
"""

from agents import build_agents
from crewai import Crew, Process
from tasks import build_tasks


def build_crew(
    customer_name: str,
    company: str,
    role: str,
    use_case: str,
    team_size: str,
    verbose: bool | None = None,
    json_output: bool = False,
) -> Crew:
    """Build and return the customer onboarding workflow Crew.

    Args:
        customer_name: Customer's full name.
        company: Customer's company name.
        role: Customer's job role or title.
        use_case: Stated primary use case or goal.
        team_size: Size of the team/organization.
        verbose: Whether to enable verbose execution traces. Defaults to False if json_output else True.
        json_output: Whether to produce a structured JSON onboarding result.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    effective_verbose = (not json_output) if verbose is None else verbose
    collector_agent, validator_agent, composer_agent = build_agents(
        verbose=effective_verbose
    )
    tasks = build_tasks(
        collector_agent,
        validator_agent,
        composer_agent,
        customer_name=customer_name,
        company=company,
        role=role,
        use_case=use_case,
        team_size=team_size,
        json_output=json_output,
    )

    crew = Crew(
        agents=[collector_agent, validator_agent, composer_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=effective_verbose,
    )
    return crew
