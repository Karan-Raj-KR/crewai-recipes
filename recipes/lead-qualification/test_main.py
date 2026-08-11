"""Smoke tests for the lead-qualification recipe (#82).

Validates crew wiring, task context chaining, agent roles,
and a mocked end-to-end run — all offline, no API calls.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# ── Windows cp1252 guard ─────────────────────────────────
# main.py prints emoji; on Windows terminals that default
# to cp1252 the print() would raise UnicodeEncodeError.
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# ── Environment & path setup (before any recipe imports) ─
os.environ.setdefault("LLM_API_KEY", "nvapi-test")
sys.path.insert(0, str(Path(__file__).parent))

from agents import build_agents
from crew import build_crew
from main import main
from tasks import build_tasks

# ─── Tests ────────────────────────────────────────────────


def test_main_runs() -> None:
    """main() completes without error (mocked kickoff)."""
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: "WARM \u2014 55/100\nFollow up within 48h."
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        main()


def test_crew_structure() -> None:
    """build_crew returns a sequential Crew with correct shape."""
    from crewai import Process

    company = "Acme Corp"
    description = "Enterprise SaaS AI Platform"
    crew = build_crew(company=company, description=description)

    # Two agents with the expected roles
    assert len(crew.agents) == 2
    research_agent = crew.agents[0]
    scoring_agent = crew.agents[1]

    assert research_agent.role == "Company Research Analyst"
    assert scoring_agent.role == "ICP Scoring Specialist"

    assert not research_agent.allow_delegation
    assert not scoring_agent.allow_delegation

    # Sequential process
    assert crew.process == Process.sequential

    # Two tasks, properly chained
    assert len(crew.tasks) == 2
    research_task = crew.tasks[0]
    scoring_task = crew.tasks[1]

    assert scoring_task.context is not None
    assert research_task in scoring_task.context

    # Placeholders injected into task descriptions
    assert company in research_task.description
    assert description in research_task.description
    assert company in scoring_task.description


def test_task_context_chaining() -> None:
    """Scoring task receives research task via context."""
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


def test_inputs_interpolated_in_tasks() -> None:
    """Company and description reach task descriptions."""
    research_agent, scoring_agent = build_agents()
    company = "Acme Corp"
    description = "Enterprise SaaS AI Platform"
    tasks = build_tasks(
        research_agent=research_agent,
        scoring_agent=scoring_agent,
        company=company,
        description=description,
    )
    assert company in tasks[0].description
    assert description in tasks[0].description
    assert company in tasks[1].description


def test_agent_allow_delegation_disabled() -> None:
    """All agents have allow_delegation=False."""
    agents = build_agents()
    for agent in agents:
        assert (
            agent.allow_delegation is False
        ), f"Agent {agent.role} should have allow_delegation=False"
