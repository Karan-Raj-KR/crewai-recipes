"""Offline smoke tests for the support-escalation crew and CLI."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

os.environ.setdefault("LLM_API_KEY", "nvapi-test")
sys.path.insert(0, str(Path(__file__).parent))

import main as recipe_main  # noqa: E402
from crewai import Crew, Process  # noqa: E402
from crew import build_crew  # noqa: E402


def test_crew_build() -> None:
    """Verify the crew's agents, tasks, and sequential process."""
    crew = build_crew(
        ticket_text="Billing issue",
        customer_tier="pro",
        previous_contacts="0",
    )
    assert isinstance(crew, Crew)
    assert crew.process == Process.sequential
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3
    assert [agent.role for agent in crew.agents] == [
        "Support Ticket Triage Specialist",
        "Tier-1 Automated Support Resolver",
        "Human Handoff & Escalation Specialist",
    ]
    assert [task.agent for task in crew.tasks] == crew.agents


def test_task_context_chaining() -> None:
    """Resolution uses triage; the final handoff uses both prior tasks."""
    crew = build_crew(ticket_text="Billing issue")
    triage_task, resolver_task, escalation_task = crew.tasks

    assert resolver_task.context == [triage_task]
    assert escalation_task.context == [triage_task, resolver_task]


def test_inputs_interpolated_in_triage_task() -> None:
    """The incoming ticket and account context reach the first task."""
    ticket_text = "Invoice 847 was charged twice"
    customer_tier = "enterprise"
    previous_contacts = "3"
    crew = build_crew(
        ticket_text=ticket_text,
        customer_tier=customer_tier,
        previous_contacts=previous_contacts,
    )

    description = crew.tasks[0].description
    assert ticket_text in description
    assert customer_tier in description
    assert previous_contacts in description


def test_agents_do_not_delegate() -> None:
    """Each support role keeps its assigned task instead of delegating it."""
    crew = build_crew(ticket_text="Billing issue")
    assert all(agent.allow_delegation is False for agent in crew.agents)


def test_main_runs() -> None:
    """Verify main.py runs smoothly with mocked LLM kickoff."""
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: (
        "### HUMAN AGENT HANDOFF BRIEF\n- Customer Goal: Resolve SSO issue"
    )
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        recipe_main.main()


if __name__ == "__main__":
    test_crew_build()
    test_task_context_chaining()
    test_inputs_interpolated_in_triage_task()
    test_agents_do_not_delegate()
    test_main_runs()
    print("✅ support-escalation: test_main passed")
