"""
Customer Onboarding Recipe — crew.py

Assembles the customer onboarding workflow Crew.
"""

from crewai import Crew, Process

from agents import build_agents
from tasks import build_tasks


def build_crew(
    customer_name: str,
    company: str,
    role: str,
    use_case: str,
    team_size: str,
) -> Crew:
    """Build and return the customer onboarding workflow Crew.

    Args:
        customer_name: Customer's full name.
        company: Customer's company name.
        role: Customer's job role or title.
        use_case: Stated primary use case or goal.
        team_size: Size of the team/organization.

    Returns:
        A configured Crew instance ready to call .kickoff().
    """
    collector_agent, validator_agent, composer_agent = build_agents()
    tasks = build_tasks(
        collector_agent,
        validator_agent,
        composer_agent,
        customer_name=customer_name,
        company=company,
        role=role,
        use_case=use_case,
        team_size=team_size,
    )

    crew = Crew(
        agents=[collector_agent, validator_agent, composer_agent],
        tasks=tasks,
        process=Process.sequential,
        verbose=True,
    )
    return crew
