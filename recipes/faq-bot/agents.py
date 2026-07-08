"""
FAQ Bot Recipe — agents.py

Single agent: searches the knowledge base and drafts a customer-facing reply.
"""

from crewai import Agent

from llm import get_llm


def build_agents() -> tuple[Agent]:
    """Build and return the FAQ support agent.

    Returns:
        A single-element tuple containing the support_agent.
    """
    llm = get_llm()

    support_agent = Agent(
        role="Orbitly Customer Support Specialist",
        goal=(
            "Answer customer questions about Orbitly accurately and helpfully, "
            "drawing only from the provided knowledge base. "
            "If the knowledge base contains the answer, give it clearly and concisely. "
            "If not, acknowledge the gap honestly and invite the customer to "
            "contact support for more help — never invent an answer."
        ),
        backstory=(
            "You are a friendly, experienced support specialist for Orbitly, "
            "a B2B project management SaaS. You know the product inside out. "
            "Customers trust you because you are always accurate, never waffle, "
            "and always end your reply with a clear next step. "
            "You write in a warm, professional tone — no corporate jargon."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return (support_agent,)
