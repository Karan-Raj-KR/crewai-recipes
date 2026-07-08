"""
Lead Qualification Recipe — agents.py

Defines the three agents that make up the lead qualification crew:
  1. ResearchAgent  — gathers background info on the lead's company
  2. ScoringAgent   — applies ICP criteria to rate the lead
  3. SummaryAgent   — produces a structured qualification report
"""

import os

from crewai import Agent
from langchain_groq import ChatGroq


def _get_llm(model: str = "llama-3.1-8b-instant") -> ChatGroq:
    """Instantiate the Groq LLaMA LLM.

    Args:
        model: Groq model identifier.

    Returns:
        A configured ChatGroq instance.

    Raises:
        EnvironmentError: If GROQ_API_KEY is not set.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Export it or add it to your .env file."
        )
    return ChatGroq(model=model, api_key=api_key, temperature=0.2)


def build_agents() -> tuple[Agent, Agent, Agent]:
    """Build and return the lead qualification agents.

    Returns:
        A tuple of (research_agent, scoring_agent, summary_agent).
    """
    llm = _get_llm()

    research_agent = Agent(
        role="Lead Research Specialist",
        goal=(
            "Gather comprehensive, accurate background information about a "
            "sales lead: their company, industry, size, funding stage, and "
            "the lead's seniority and likely decision-making authority."
        ),
        backstory=(
            "You are a seasoned B2B sales researcher with 10+ years of "
            "experience profiling prospects. You know exactly what signals "
            "matter: team size, tech stack, recent funding, and growth "
            "trajectory. You rely only on the information provided and reason "
            "carefully rather than fabricating details."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    scoring_agent = Agent(
        role="ICP Scoring Analyst",
        goal=(
            "Evaluate the lead against the Ideal Customer Profile (ICP) and "
            "produce a numeric score from 0–100 along with clear reasoning "
            "for each scoring dimension."
        ),
        backstory=(
            "You are a data-driven sales strategist who has built and refined "
            "ICP frameworks for SaaS companies. You score leads objectively "
            "across four dimensions: company fit, role fit, timing signals, "
            "and engagement potential. You never inflate scores without evidence."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    summary_agent = Agent(
        role="Qualification Report Writer",
        goal=(
            "Synthesise the research and scoring into a concise, actionable "
            "qualification report that a sales rep can read in under 2 minutes."
        ),
        backstory=(
            "You are a former enterprise sales director who now coaches reps "
            "on pipeline hygiene. You write crystal-clear qualification reports "
            "with a recommended next action (call, nurture, or disqualify) and "
            "three bullet points the sales rep should mention in the first touch."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
    )

    return research_agent, scoring_agent, summary_agent
