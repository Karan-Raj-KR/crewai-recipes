"""Smoke test for email-drafting recipe main execution with mocked LLM."""

import os
from unittest.mock import patch

os.environ["LLM_API_KEY"] = "nvapi-test"

from crew import build_crew  # noqa: E402


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = build_crew(
        recipient="Team",
        purpose="Status update",
        key_points="Project on track",
        tone="professional",
    )
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2

    with patch("crewai.Crew.kickoff", return_value="Mocked Polished Email"):
        result = crew.kickoff()
        assert result == "Mocked Polished Email"


def test_crew_process_is_sequential() -> None:
    """Crew runs tasks in sequential order (#156)."""
    from crewai import Process

    crew = build_crew(
        recipient="Team",
        purpose="Status update",
        key_points="Project on track",
        tone="professional",
    )
    assert crew.process == Process.sequential


def test_task_context_chaining() -> None:
    """Editor task receives the draft task via context (#156)."""
    crew = build_crew(
        recipient="Team",
        purpose="Status update",
        key_points="Project on track",
        tone="professional",
    )
    draft_task, edit_task = crew.tasks
    assert edit_task.context is not None
    assert draft_task in edit_task.context


def test_inputs_interpolated_in_tasks() -> None:
    """CLI inputs reach the draft task description (#156)."""
    recipient = "CTO"
    purpose = "Q3 roadmap alignment"
    key_points = "ship faster, cut infra costs"
    tone = "formal"
    crew = build_crew(
        recipient=recipient,
        purpose=purpose,
        key_points=key_points,
        tone=tone,
    )
    draft_task = crew.tasks[0]
    assert recipient in draft_task.description
    assert purpose in draft_task.description
    assert key_points in draft_task.description
    assert tone in draft_task.description


def test_agents_do_not_delegate() -> None:
    """All agents have allow_delegation disabled (#156, pattern from #82)."""
    crew = build_crew(
        recipient="Team",
        purpose="Status update",
        key_points="Project on track",
        tone="professional",
    )
    for agent in crew.agents:
        assert agent.allow_delegation is False, (
            f"Agent {agent.role} should have allow_delegation=False"
        )


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ email-drafting: test_main passed")
