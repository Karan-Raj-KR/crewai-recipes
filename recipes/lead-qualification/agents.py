"""
Lead Qualification Recipe — agents.py

Two agents:
  1. ResearchAgent — profiles the company from the provided description
  2. ScoringAgent  — applies ICP criteria and outputs a 0-100 score
"""

from crewai import Agent

from llm import get_llm


def build_agents() -> tuple[Agent, Agent]:
    """Build and return the Researcher and Scorer agents.

    Returns:
        A tuple of (research_agent, scoring_agent).
    """
    llm = get_llm()

    research_agent = Agent(
        role="Company Research Analyst",
        goal=(
            "Analyse the company description provided and extract all "
            "relevant signals for a B2B SaaS sales qualification: "
            "industry vertical, company size estimate, business model "
            "(B2B/B2C/marketplace), growth stage, likely tech stack, "
            "and the biggest operational pain points they probably face."
        ),
        backstory=(
            "You are a senior B2B sales researcher with a decade of "
            "experience profiling SaaS prospects. You are rigorous and "
            "methodical — you only draw conclusions that are supported "
            "by the description given. You never fabricate information. "
            "If something is unclear, you note the ambiguity explicitly."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    scoring_agent = Agent(
        role="ICP Scoring Specialist",
        goal=(
            "Score the company against a standard B2B SaaS Ideal Customer "
            "Profile (ICP) and produce a total score from 0 to 100. "
            "Break the score into four equally-weighted dimensions (25 pts each): "
            "Industry Fit, Company Size Fit, Pain Point Acuity, and "
            "Budget/Growth Signal. Provide a one-sentence rationale per dimension. "
            "End with a verdict: HOT (75-100), WARM (40-74), or COLD (0-39)."
        ),
        backstory=(
            "You are a data-driven revenue operations analyst who built ICP "
            "scoring frameworks for three Series B SaaS companies. You score "
            "objectively and conservatively — you only give high scores when "
            "there is clear evidence in the research, never on assumption."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return research_agent, scoring_agent
