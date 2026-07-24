"""
Content Pipeline Recipe — agents.py

Defines the 4 agents for the automated blog content production pipeline.
"""

from crewai import Agent
from llm import get_llm


def build_agents() -> tuple[Agent, Agent, Agent, Agent]:
    """Build and return the 4 content pipeline agents.

    Returns:
        A tuple of (ideator_agent, researcher_agent, writer_agent, seo_agent).
    """
    llm = get_llm()

    ideator_agent = Agent(
        role="Content Strategist & Ideator",
        goal=(
            "Generate 3 compelling article headlines, distinct content angles, "
            "and sub-topic hooks tailored to the target audience and keywords."
        ),
        backstory=(
            "You are a seasoned digital content strategist expert at brainstorming "
            "engaging blog topics, catchy titles, and unique editorial angles that "
            "resonate with specific audiences."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    researcher_agent = Agent(
        role="Content Outline & Research Architect",
        goal=(
            "Build a logical section-by-section outline with core talking points "
            "and key arguments, explicitly flagging any uncertain facts."
        ),
        backstory=(
            "You are a meticulous content architect who structures clear outlines "
            "based on verified domain knowledge. You do not browse the live web or "
            "fabricate statistics; you push for foundational clarity and flag unverified claims."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    writer_agent = Agent(
        role="Technical & Creative Blog Writer",
        goal=(
            "Write a clear, engaging, short-form blog post (under 500 words) "
            "following the structured outline and incorporating target keywords naturally."
        ),
        backstory=(
            "You are a skilled technology and business writer who crafts punchy, "
            "well-formatted articles. You focus on concise, high-value prose that stays "
            "well within token limits without sacrificing readability."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    seo_agent = Agent(
        role="SEO & Content Quality Reviewer",
        goal=(
            "Review the article draft and provide concrete, actionable editorial "
            "and SEO edit recommendations (heading optimizations, keyword placement, "
            "readability improvements)."
        ),
        backstory=(
            "You are a senior SEO editor. You do not just output arbitrary numerical scores; "
            "you provide specific, constructive, line-by-line edit recommendations to optimize "
            "the draft for readers and search engines."
        ),
        verbose=True,
        memory=False,
        llm=llm,
    )

    return ideator_agent, researcher_agent, writer_agent, seo_agent
