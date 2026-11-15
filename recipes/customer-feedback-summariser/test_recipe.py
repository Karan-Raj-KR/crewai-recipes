"""Offline structural tests for the customer-feedback-summariser recipe.

Validates:
  - Crew is sequential with exactly two agents.
  - Task 2 (summary_task) has task 1 (analysis_task) in its context.
  - The feedback input reaches the analysis task description.
  - FeedbackSummary Pydantic model validates correctly and rejects bad sentiment.
  - All agents have allow_delegation=False.

No real LLM calls are made — LLM_API_KEY=nvapi-test is sufficient.
"""

import os
import sys
from pathlib import Path

import pytest

# ── Windows cp1252 guard ─────────────────────────────────────────────────────
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── Environment & path setup (before any recipe imports) ─────────────────────
os.environ.setdefault("LLM_API_KEY", "nvapi-test")
sys.path.insert(0, str(Path(__file__).parent))

from agents import build_agents  # noqa: E402
from crew import build_crew  # noqa: E402
from tasks import FeedbackSummary, build_tasks  # noqa: E402

# ─── Sample data ──────────────────────────────────────────────────────────────

SAMPLE_FEEDBACK = (
    "Checkout is easy to use, but the payment page is slow. "
    "I also wish there was an option to save multiple cards."
)


# ─── Structural tests ─────────────────────────────────────────────────────────


def test_crew_is_sequential() -> None:
    """build_crew returns a sequential Crew."""
    from crewai import Process

    crew = build_crew(feedback=SAMPLE_FEEDBACK)
    assert crew.process == Process.sequential


def test_crew_has_two_agents() -> None:
    """Crew contains exactly two agents with the expected roles."""
    crew = build_crew(feedback=SAMPLE_FEEDBACK)
    assert len(crew.agents) == 2
    assert crew.agents[0].role == "Customer Feedback Analyst"
    assert crew.agents[1].role == "Action Summariser"


def test_crew_has_two_tasks() -> None:
    """Crew contains exactly two tasks."""
    crew = build_crew(feedback=SAMPLE_FEEDBACK)
    assert len(crew.tasks) == 2


def test_summary_task_context_chains_analysis_task() -> None:
    """Task 2 must have task 1 in its context (ensures information flows correctly)."""
    crew = build_crew(feedback=SAMPLE_FEEDBACK)
    analysis_task = crew.tasks[0]
    summary_task = crew.tasks[1]

    assert summary_task.context is not None, "summary_task.context must not be None"
    assert analysis_task in summary_task.context, (
        "analysis_task must appear in summary_task.context"
    )


def test_feedback_input_reaches_analysis_task_description() -> None:
    """The feedback text must be interpolated into the analysis task description."""
    feedback_analyst, action_summariser = build_agents()
    tasks = build_tasks(
        feedback_analyst=feedback_analyst,
        action_summariser=action_summariser,
        feedback=SAMPLE_FEEDBACK,
    )
    assert SAMPLE_FEEDBACK in tasks[0].description, (
        "Feedback text must appear in the analysis task description"
    )


def test_agents_have_delegation_disabled() -> None:
    """All agents must have allow_delegation=False."""
    agents = build_agents()
    for agent in agents:
        assert agent.allow_delegation is False, (
            f"Agent '{agent.role}' should have allow_delegation=False"
        )


def test_json_output_enables_output_pydantic() -> None:
    """When json_output=True, summary_task must set output_pydantic=FeedbackSummary."""
    feedback_analyst, action_summariser = build_agents()
    tasks = build_tasks(
        feedback_analyst=feedback_analyst,
        action_summariser=action_summariser,
        feedback=SAMPLE_FEEDBACK,
        json_output=True,
    )
    summary_task = tasks[1]
    assert summary_task.output_pydantic is FeedbackSummary, (
        "summary_task.output_pydantic must be FeedbackSummary when json_output=True"
    )


def test_no_pydantic_output_by_default() -> None:
    """By default (json_output=False), summary_task must NOT set output_pydantic."""
    feedback_analyst, action_summariser = build_agents()
    tasks = build_tasks(
        feedback_analyst=feedback_analyst,
        action_summariser=action_summariser,
        feedback=SAMPLE_FEEDBACK,
        json_output=False,
    )
    summary_task = tasks[1]
    assert summary_task.output_pydantic is None, (
        "summary_task.output_pydantic must be None when json_output=False"
    )


# ─── Pydantic model round-trip tests ─────────────────────────────────────────


def test_feedback_summary_valid_positive() -> None:
    """FeedbackSummary accepts all valid sentiment values."""
    for sentiment in ("positive", "neutral", "negative", "mixed"):
        model = FeedbackSummary(
            sentiment=sentiment,  # type: ignore[arg-type]
            themes=["Theme A", "Theme B"],
            concerns=["Concern 1"],
            actions=["Action 1"],
        )
        assert model.sentiment == sentiment


def test_feedback_summary_rejects_invalid_sentiment() -> None:
    """FeedbackSummary must reject sentiment values outside the Literal."""
    with pytest.raises(Exception):
        FeedbackSummary(
            sentiment="unknown",  # type: ignore[arg-type]
            themes=["Theme A"],
            concerns=["Concern 1"],
            actions=["Action 1"],
        )


def test_feedback_summary_round_trip() -> None:
    """FeedbackSummary serialises to dict and back correctly."""
    data = {
        "sentiment": "mixed",
        "themes": ["Checkout experience", "Payment performance"],
        "concerns": ["Payment page is slow", "Cannot save multiple cards"],
        "actions": [
            "Investigate payment-page load time.",
            "Add support for multiple saved payment methods.",
        ],
    }
    model = FeedbackSummary(**data)
    serialised = model.model_dump()
    assert serialised["sentiment"] == "mixed"
    assert len(serialised["themes"]) == 2
    assert len(serialised["concerns"]) == 2
    assert len(serialised["actions"]) == 2
