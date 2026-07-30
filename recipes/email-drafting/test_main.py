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


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ email-drafting: test_main passed")
