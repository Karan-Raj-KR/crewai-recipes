"""Offline tests for content-pipeline crew wiring and CLI inputs."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ["LLM_API_KEY"] = "nvapi-test"

import pytest  # noqa: E402
from crewai import Crew, Process  # noqa: E402
from crew import build_crew  # noqa: E402
import run as recipe_run  # noqa: E402


def test_crew_build_and_kickoff() -> None:
    """Verify the sequential crew shape and a mocked kickoff."""
    crew = build_crew(
        topic="AI Agents",
        target_audience="Developers",
        keywords="CrewAI, LLM",
    )
    assert isinstance(crew, Crew)
    assert crew.process == Process.sequential
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4
    assert [agent.role for agent in crew.agents] == [
        "Content Strategist & Ideator",
        "Content Outline & Research Architect",
        "Technical & Creative Blog Writer",
        "SEO & Content Quality Reviewer",
    ]
    assert [task.agent for task in crew.tasks] == crew.agents

    with patch("crewai.Crew.kickoff", return_value="Mocked Article & SEO Review"):
        result = crew.kickoff()
        assert result == "Mocked Article & SEO Review"


def test_task_context_chaining() -> None:
    """Each stage receives the upstream work it needs."""
    crew = build_crew(topic="AI Agents")
    ideation, research, drafting, seo = crew.tasks

    assert research.context == [ideation]
    assert drafting.context == [ideation, research]
    assert seo.context == [drafting]


def test_cli_inputs_reach_task_descriptions(monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI flags reach the corresponding task descriptions without an LLM call."""
    topic = "Reliable agent handoffs"
    audience = "Platform engineers"
    keywords = "handoffs, reliability"
    built_crews: list[Crew] = []

    def capture_build_crew(*, topic: str, target_audience: str, keywords: str) -> Crew:
        crew = build_crew(
            topic=topic,
            target_audience=target_audience,
            keywords=keywords,
        )
        built_crews.append(crew)
        return crew

    monkeypatch.setattr(recipe_run, "build_crew", capture_build_crew)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run.py",
            "--topic",
            topic,
            "--target_audience",
            audience,
            "--keywords",
            keywords,
        ],
    )
    with patch("crewai.Crew.kickoff", return_value="Mocked article"):
        recipe_run.main()

    assert len(built_crews) == 1
    ideation, _, drafting, seo = built_crews[0].tasks
    assert topic in ideation.description
    assert audience in ideation.description
    assert audience in drafting.description
    assert keywords in ideation.description
    assert keywords in seo.description


def test_agents_do_not_delegate() -> None:
    """All four content roles keep their assigned work."""
    crew = build_crew(topic="AI Agents")
    assert all(agent.allow_delegation is False for agent in crew.agents)


def test_check_env_reports_env_path_and_fix(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing key error names the recipe's absolute .env path and a cp fix."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(SystemExit) as exc:
        recipe_run.check_env()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    recipe_dir = Path(__file__).resolve().parent
    assert str(recipe_dir / ".env") in err
    assert f"cp {recipe_dir / '.env.example'} {recipe_dir / '.env'}" in err


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    test_task_context_chaining()
    test_agents_do_not_delegate()
    print("✅ content-pipeline: test_main passed")
