"""
Customer Onboarding Recipe — agents.py

Defines the agents for the customer onboarding workflow crew.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the customer onboarding workflow agents.

    Returns:
        A tuple of (collector_agent, validator_agent, composer_agent).
    """
    llm = get_llm()

    collector_agent = Agent(
        role="Customer Onboarding Data Collector",
        goal=(
            "Structure and standardize raw customer signup information "
            "(name, company, role, use case, team size) into a clean customer profile."
        ),
        backstory=(
            "You are a meticulous customer operations specialist trained to parse raw "
            "signup details, extract key business metadata, and organize inputs into "
            "standardized customer onboarding records."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    validator_agent = Agent(
        role="Onboarding Data Validator",
        goal=(
            "Audit customer profiles for completeness, internal consistency, "
            "and onboarding readiness without inventing missing information."
        ),
        backstory=(
            "You are a conservative data auditor. You never fabricate or assume "
            "missing details. You strictly evaluate whether all essential onboarding "
            "requirements are met, highlight vague or contradictory fields, and determine "
            "if onboarding can proceed."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    composer_agent = Agent(
        role="Personalized Welcome Email Composer",
        goal=(
            "Draft a warm, highly tailored welcome email referencing the customer's "
            "company and use case if valid, or a polite follow-up request if data is missing."
        ),
        backstory=(
            "You are a customer success communication expert who writes engaging, "
            "professional welcome emails. When onboarding data is complete, you deliver "
            "tailored next steps and resources. When data is incomplete, you send a friendly, "
            "helpful message requesting clarification."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return collector_agent, validator_agent, composer_agent
