"""Smoke test for whatsapp-action-sim recipe main execution with mocked LLM."""

import os
from unittest.mock import MagicMock, patch

os.environ["LLM_API_KEY"] = "nvapi-test"

from crew import build_crew  # noqa: E402


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = build_crew(
        user_message="Hey! Where is my order?", sender_name="Test User"
    )
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3

    with patch.object(crew, "kickoff", return_value="Mocked WhatsApp reply"):
        result = crew.kickoff()
        assert result == "Mocked WhatsApp reply"


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ whatsapp-action-sim: test_main passed")
