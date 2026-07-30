"""
Support Escalation Recipe — agents.py

Defines the 3 agents for the support ticket triage, resolution, and escalation crew.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the support escalation workflow agents.

    Returns:
        A tuple of (triage_agent, resolver_agent, escalation_agent).
    """
    llm = get_llm()

    triage_agent = Agent(
        role="Support Ticket Triage Specialist",
        goal=(
            "Classify incoming customer support tickets into an issue category, "
            "assign an exact severity level (LOW, MEDIUM, HIGH, or CRITICAL), "
            "and assess whether Tier-1 automated resolution should be attempted."
        ),
        backstory=(
            "You are an experienced IT support triage coordinator. You accurately assess "
            "customer issue descriptions, evaluate account tiers, and categorize incoming "
            "tickets to ensure appropriate handling."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    resolver_agent = Agent(
        role="Tier-1 Automated Support Resolver",
        goal=(
            "Attempt to resolve Tier-1 support issues strictly using the in-memory "
            "knowledge base. Never speculate or invent solutions; explicitly declare "
            "ESCALATE_TO_HUMAN if no verified knowledge base match exists."
        ),
        backstory=(
            "You are a conservative support resolver agent. You strictly adhere to verified "
            "knowledge base articles. You never guess, hallucinate, or provide unverified "
            "workarounds. When a ticket falls outside known Tier-1 topics, you immediately "
            "recommend human escalation."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    escalation_agent = Agent(
        role="Human Handoff & Escalation Specialist",
        goal=(
            "Produce a complete, structured resolution response for auto-resolved issues "
            "OR a structured human handoff summary (Customer Goal, Attempted Resolution, "
            "Blocking Issue, Suggested Next Action) when escalated."
        ),
        backstory=(
            "You are a senior technical support lead. For auto-resolvable tickets, you draft "
            "clear instructions for the user. For escalated tickets, you compile a concise, "
            "high-value handoff brief for human support engineers so they can take over without "
            "re-reading the entire thread."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return triage_agent, resolver_agent, escalation_agent
