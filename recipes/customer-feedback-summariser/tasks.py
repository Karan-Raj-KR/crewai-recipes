"""
Customer Feedback Summariser Recipe — tasks.py

Two sequential tasks:
  1. analysis_task  — reads raw feedback, extracts themes, sentiment, concerns
  2. summary_task   — produces structured output (FeedbackSummary) with action items
"""

from typing import Literal

from crewai import Agent, Task
from pydantic import BaseModel, Field


class FeedbackSummary(BaseModel):
    """Structured output produced by the Action Summariser agent."""

    sentiment: Literal["positive", "neutral", "negative", "mixed"] = Field(
        description="Overall sentiment across all feedback: positive, neutral, negative, or mixed"
    )
    themes: list[str] = Field(
        description="Main topics or themes identified in the feedback (2-6 items)"
    )
    concerns: list[str] = Field(
        description="Important customer concerns extracted from the feedback (1-5 items)"
    )
    actions: list[str] = Field(
        description="Concrete, actionable recommendations for the team (1-5 items)"
    )


def build_tasks(
    feedback_analyst: Agent,
    action_summariser: Agent,
    feedback: str,
    json_output: bool = False,
) -> list[Task]:
    """Build the ordered task list for the feedback summariser crew.

    Args:
        feedback_analyst: Agent that analyses raw feedback.
        action_summariser: Agent that summarises and produces action items.
        feedback: The raw customer feedback text to analyse.
        json_output: If True, the summary task uses output_pydantic for
                     structured JSON; otherwise it returns readable Markdown.

    Returns:
        An ordered list of [analysis_task, summary_task].
    """
    analysis_task = Task(
        description=(
            f'Customer Feedback:\n"""\n{feedback}\n"""\n\n'
            "Analyse the customer feedback provided above. Do NOT use any external "
            "information beyond what is written in the text.\n\n"
            "Extract and clearly present:\n"
            "1. **Themes** — the main topics or recurring subjects (2-6 bullet points).\n"
            "2. **Sentiment** — the overall tone: positive, neutral, negative, or mixed. "
            "   State your reasoning in one sentence.\n"
            "3. **Key Concerns** — the most important pain points or issues customers "
            "   mention (1-5 bullet points). Be specific and quote or paraphrase directly "
            "   from the feedback where possible.\n\n"
            "If any part of the feedback is ambiguous, note it explicitly. "
            "Keep your analysis concise — maximum 250 words."
        ),
        expected_output=(
            "A structured markdown analysis with three clearly labelled sections: "
            "Themes, Sentiment, and Key Concerns. Maximum 250 words."
        ),
        agent=feedback_analyst,
    )

    summary_task = Task(
        description=(
            "Using the feedback analysis produced by the Feedback Analyst, "
            "create a final structured summary for the team.\n\n"
            "The summary must include:\n"
            "- **Overall Sentiment**: one word — positive, neutral, negative, or mixed.\n"
            "- **Themes**: a concise bulleted list of the main topics (2-6 items).\n"
            "- **Key Concerns**: the most important issues customers raised (1-5 items).\n"
            "- **Suggested Actions**: concrete, specific action items the team can act on "
            "  immediately (1-5 items). Start each action with an imperative verb "
            "  (e.g. 'Investigate', 'Add', 'Review').\n\n"
            "Be direct and specific. Avoid vague filler phrases."
        ),
        expected_output=(
            "A JSON object matching the FeedbackSummary schema."
            if json_output
            else (
                "A structured markdown summary with four labelled sections:\n"
                "- Overall Sentiment\n"
                "- Themes\n"
                "- Key Concerns\n"
                "- Suggested Actions"
            )
        ),
        output_pydantic=FeedbackSummary if json_output else None,
        agent=action_summariser,
        context=[analysis_task],
    )

    return [analysis_task, summary_task]
