"""
Email Drafting Recipe — agents.py

Defines the 2 agents for the email drafting workflow crew (Drafter + Editor).
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent]:
    """Build and return the email drafting workflow agents.

    Returns:
        A tuple of (drafter_agent, editor_agent).
    """
    llm = get_llm()

    drafter_agent = Agent(
        role="Email Composition Specialist",
        goal=(
            "Draft a complete, well-structured email from a user brief, incorporating "
            "all requested key points and requested tone."
        ),
        backstory=(
            "You are an experienced communications manager skilled at turning unstructured "
            "briefs into clear, professional email drafts tailored to specific recipients."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    editor_agent = Agent(
        role="Executive Email Editor & Auditor",
        goal=(
            "Refine the initial draft for conciseness, enforce the requested tone "
            "(professional / friendly / formal / direct), verify every key point is included, "
            "and output the final email alongside a short editorial change log."
        ),
        backstory=(
            "You are a sharp communications editor. You ruthlessly cut padding, fix awkward "
            "phrasing, ensure the requested tone is strictly maintained, and verify that "
            "no required key point was omitted."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return drafter_agent, editor_agent
