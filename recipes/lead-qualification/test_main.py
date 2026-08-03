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


def test_main_runs() -> None:
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: "WARM — 55/100\nFollow up within 48h."
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        recipe_main.main()


def test_crew_structure() -> None:
    from crew import build_crew

    company = "Acme Corp"
    description = "A 40-person B2B SaaS startup..."
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


if __name__ == "__main__":
    test_main_runs()
    test_crew_structure()
    print("✅ lead-qualification: tests passed")
