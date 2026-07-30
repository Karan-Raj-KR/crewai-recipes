"""Smoke test for customer-onboarding recipe main execution with mocked LLM."""

import os
from unittest.mock import patch

os.environ["LLM_API_KEY"] = "nvapi-test"

import main as recipe_main
from crew import build_crew


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = build_crew(
        customer_name="Test User",
        company="Acme Corp",
        role="DevOps Lead",
        use_case="CI/CD Automation",
        team_size="10",
    )
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3

    with patch("crewai.Crew.kickoff", return_value="Mocked Onboarding Email"):
        recipe_main.main()


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ customer-onboarding: test_main passed")
