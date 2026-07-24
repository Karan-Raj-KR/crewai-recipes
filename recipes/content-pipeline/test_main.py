"""Smoke test for content-pipeline recipe main execution with mocked LLM."""

import os
from unittest.mock import patch

os.environ["LLM_API_KEY"] = "nvapi-test"

from crew import build_crew  # noqa: E402


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = build_crew(
        topic="AI Agents",
        target_audience="Developers",
        keywords="CrewAI, LLM",
    )
    assert len(crew.agents) == 4
    assert len(crew.tasks) == 4

    with patch.object(crew, "kickoff", return_value="Mocked Article & SEO Review"):
        result = crew.kickoff()
        assert result == "Mocked Article & SEO Review"


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ content-pipeline: test_main passed")
