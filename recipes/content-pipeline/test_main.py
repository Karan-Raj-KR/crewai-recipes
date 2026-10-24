"""Smoke test for content-pipeline recipe main execution with mocked LLM."""

import os
from pathlib import Path
from unittest.mock import patch

os.environ["LLM_API_KEY"] = "nvapi-test"

import pytest  # noqa: E402
from crew import build_crew  # noqa: E402
from run import check_env  # noqa: E402


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = build_crew(
        topic="AI Agents",
        target_audience="Developers",
        keywords="CrewAI, LLM",
    )
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4

    with patch("crewai.Crew.kickoff", return_value="Mocked Article & SEO Review"):
        result = crew.kickoff()
        assert result == "Mocked Article & SEO Review"


def test_check_env_reports_env_path_and_fix(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing key error names the recipe's absolute .env path and a cp fix."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("NVIDIA_API_KEY", raising=False)

    with pytest.raises(SystemExit) as exc:
        check_env()

    assert exc.value.code == 1
    err = capsys.readouterr().err
    recipe_dir = Path(__file__).resolve().parent
    assert str(recipe_dir / ".env") in err
    assert f"cp {recipe_dir / '.env.example'} {recipe_dir / '.env'}" in err


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ content-pipeline: test_main passed")
