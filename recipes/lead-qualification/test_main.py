"""Smoke test: main() runs without errors and build_crew signature is correct."""

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
from agents import build_agents  # noqa: E402
from crew import build_crew  # noqa: E402
from tasks import build_tasks  # noqa: E402


def test_main_runs() -> None:
    """Smoke test executing main() with mocked crew kickoff output."""
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: "WARM — 55/100\nFollow up within 48h."
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        recipe_main.main()


def test_crew_structure() -> None:
    """Assert build_crew returns a Crew with 2 agents, 2 tasks, and correct roles."""
    company = "Acme Corp"
    description = "Enterprise SaaS AI Platform"
    crew = build_crew(company=company, description=description)

    assert len(crew.agents) == 2
    research_agent = crew.agents[0]
    scoring_agent = crew.agents[1]

    assert research_agent.role == "Company Research Analyst"
    assert scoring_agent.role == "ICP Scoring Specialist"

    assert not research_agent.allow_delegation
    assert not scoring_agent.allow_delegation

    assert len(crew.tasks) == 2
    research_task = crew.tasks[0]
    scoring_task = crew.tasks[1]

    # Verify context chaining
    assert scoring_task.context is not None
    assert research_task in scoring_task.context

    # Verify placeholders are injected
    assert company in research_task.description
    assert description in research_task.description
    assert company in scoring_task.description


def test_task_context_chaining() -> None:
    """Assert task context dependency chaining for agent handoff."""
    research_agent, scoring_agent = build_agents()
    tasks = build_tasks(
        research_agent=research_agent,
        scoring_agent=scoring_agent,
        company="Acme Corp",
        description="Enterprise SaaS AI Platform",
    )
    research_task = tasks[0]
    scoring_task = tasks[1]
    assert scoring_task.context is not None
    assert research_task in scoring_task.context


def test_agent_allow_delegation_disabled() -> None:
    """Assert allow_delegation is set to False for all agents."""
    agents = build_agents()
    for agent in agents:
        assert agent.allow_delegation is False, f"Agent {agent.role} should have allow_delegation=False"


if __name__ == "__main__":
    test_main_runs()
    test_crew_structure()
    test_task_context_chaining()
    test_agent_allow_delegation_disabled()
    print("✅ lead-qualification: tests passed")
