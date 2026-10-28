"""
Customer Feedback Summariser Recipe — agents.py

Two agents:
  1. FeedbackAnalyst  — reads raw feedback, extracts themes, sentiment, concerns
  2. ActionSummariser — converts concerns into concise, actionable recommendations
"""

from crewai import Agent

from llm import get_llm


def build_agents(verbose: bool = False) -> tuple[Agent, Agent]:
    """Build and return the Feedback Analyst and Action Summariser agents.

    Returns:
        A tuple of (feedback_analyst, action_summariser).
    """
    llm = get_llm()

    feedback_analyst = Agent(
        role="Customer Feedback Analyst",
        goal=(
            "Read raw customer feedback and extract the main topics or themes, "
            "determine the overall sentiment (positive, neutral, negative, or mixed), "
            "and identify the most important customer concerns that need attention."
        ),
        backstory=(
            "You are a seasoned product analyst with extensive experience interpreting "
            "customer feedback across SaaS and e-commerce products. You are precise and "
            "objective — you only report themes and concerns that are clearly present in "
            "the feedback text. You never embellish or invent issues. When feedback is "
            "ambiguous, you flag it rather than assume."
        ),
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    action_summariser = Agent(
        role="Action Summariser",
        goal=(
            "Convert the identified customer concerns into a short, prioritised list of "
            "concrete action items for the product or support team. "
            "Produce a final structured summary that includes overall sentiment, "
            "themes, key concerns, and suggested actions."
        ),
        backstory=(
            "You are a product operations specialist who has helped multiple teams turn "
            "mountains of customer feedback into focused sprint backlogs and support "
            "playbooks. You write clearly and concisely, using plain language that "
            "engineers and support leads can act on immediately."
        ),
        llm=llm,
        verbose=verbose,
        allow_delegation=False,
    )

    return feedback_analyst, action_summariser
