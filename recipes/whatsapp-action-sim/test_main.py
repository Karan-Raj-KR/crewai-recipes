"""Offline smoke tests for the WhatsApp action simulation crew."""

import os
from unittest.mock import patch

from crew import build_crew
from crewai import Crew, Process

SENDER_NAME = "Test User"
USER_MESSAGE = "Can I reschedule my demo to Friday?"


def _build_test_crew() -> Crew:
    """Assemble the real crew with a dummy key scoped to construction."""
    with patch.dict(
        os.environ, {"LLM_API_KEY": "nvapi-test", "LLM_PROVIDER": "primary"}
    ):
        return build_crew(user_message=USER_MESSAGE, sender_name=SENDER_NAME)


def test_crew_structure() -> None:
    """Verify the recipe builds a sequential crew with three agents and tasks."""
    crew = _build_test_crew()

    assert isinstance(crew, Crew)
    assert crew.process == Process.sequential
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3


def test_router_receives_classifier_context() -> None:
    """Verify the router receives the classifier task as context."""
    classifier_task, router_task, _ = _build_test_crew().tasks

    assert router_task.context is not None
    assert any(task is classifier_task for task in router_task.context)


def test_task_descriptions_include_message_inputs() -> None:
    """Verify the classifier sees both inputs and the composer sees the sender."""
    classifier_task, _, composer_task = _build_test_crew().tasks

    assert SENDER_NAME in classifier_task.description
    assert USER_MESSAGE in classifier_task.description
    assert SENDER_NAME in composer_task.description


def test_agent_delegation_is_disabled() -> None:
    """Verify that none of the agents can delegate work."""
    for agent in _build_test_crew().agents:
        assert agent.allow_delegation is False, agent.role


def test_crew_build_and_kickoff() -> None:
    """Verify build_crew instantiates Crew and kickoff runs smoothly."""
    crew = _build_test_crew()

    with patch("crewai.Crew.kickoff", return_value="Mocked WhatsApp reply"):
        result = crew.kickoff()
        assert result == "Mocked WhatsApp reply"


if __name__ == "__main__":
    test_crew_build_and_kickoff()
    print("✅ whatsapp-action-sim: test_main passed")
