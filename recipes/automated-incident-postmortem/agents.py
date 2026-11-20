"""
Automated Incident Postmortem Recipe — agents.py

Defines 3 specialized SRE agents for chronological reconstruction, root cause diagnosis (Five Whys),
and blameless postmortem report generation.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the incident postmortem workflow agents.

    Returns:
        A tuple of (timeline_agent, diagnostician_agent, postmortem_agent).
    """
    llm = get_llm()

    timeline_agent = Agent(
        role="SRE Incident Chronologist",
        goal=(
            "Ingest raw alert logs, system metrics, and deployment timestamps to reconstruct "
            "an accurate, normalized chronological timeline from anomaly detection to full recovery."
        ),
        backstory=(
            "You are an expert site reliability engineer skilled at sifting through noisy event streams "
            "and server logs. You identify critical inflection points, alert triggers, mitigation steps, "
            "and recovery milestones with precise UTC timestamps."
        ),
        verbose=True,
        memory=False,
        allow_delegation=False,
        llm=llm,
    )

    diagnostician_agent = Agent(
        role="Systems & Software Root Cause Investigator",
        goal=(
            "Correlate error stack traces, monitoring telemetry, and recent deployment commit diffs "
            "to pinpoint the primary technical failure mode and perform a rigorous Five Whys root cause analysis."
        ),
        backstory=(
            "You are a principal infrastructure and distributed systems architect. You specialize in "
            "debugging complex cascading failures, database connection pool exhaustion, unindexed queries, "
            "race conditions, and configuration regressions under high load."
        ),
        verbose=True,
        memory=False,
        allow_delegation=False,
        llm=llm,
    )

    postmortem_agent = Agent(
        role="Lead Technical Incident Documentarian",
        goal=(
            "Synthesize the incident timeline and root cause findings into an industry-standard, blameless "
            "Markdown postmortem document featuring executive summary, impact metrics, lessons learned, and "
            "prioritized preventative action items (P0, P1, P2)."
        ),
        backstory=(
            "You are an engineering director dedicated to building resilient engineering cultures through "
            "psychological safety and blameless retrospectives. You excel at translating technical outages "
            "into clear retrospectives with concrete, accountable engineering action items."
        ),
        verbose=True,
        memory=False,
        allow_delegation=False,
        llm=llm,
    )

    return timeline_agent, diagnostician_agent, postmortem_agent
