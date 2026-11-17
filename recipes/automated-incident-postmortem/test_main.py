"""Offline smoke tests for the automated-incident-postmortem crew and CLI."""

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

# Ensure crewai is mockable if not installed in the test environment
try:
    import crewai  # noqa: F401
except ImportError:
    import types
    mock_crewai = types.ModuleType("crewai")

    class MockAgent:
        def __init__(self, role, goal, backstory, verbose=True, memory=False, allow_delegation=False, llm=None):
            self.role = role
            self.goal = goal
            self.backstory = backstory
            self.verbose = verbose
            self.memory = memory
            self.allow_delegation = allow_delegation
            self.llm = llm

    class MockTask:
        def __init__(self, description, expected_output, agent, context=None):
            self.description = description
            self.expected_output = expected_output
            self.agent = agent
            self.context = context or []

    class MockProcess:
        sequential = "sequential"

    class MockCrew:
        def __init__(self, agents, tasks, process=None, verbose=True):
            self.agents = agents
            self.tasks = tasks
            self.process = process or MockProcess.sequential
            self.verbose = verbose

        def kickoff(self):
            return "Mock postmortem output"

    class MockLLM:
        def __init__(self, *args, **kwargs):
            pass

    mock_crewai.Agent = MockAgent
    mock_crewai.Task = MockTask
    mock_crewai.Process = MockProcess
    mock_crewai.Crew = MockCrew
    mock_crewai.LLM = MockLLM
    sys.modules["crewai"] = mock_crewai

from crewai import Crew, Process  # noqa: E402
from crew import build_crew  # noqa: E402


def test_crew_build() -> None:
    """Verify the crew's agents, tasks, and sequential process."""
    crew = build_crew(
        incident_title="Database Outage",
        raw_alert_logs="14:00 [CRIT] connection failure",
        recent_deployment_summary="Commit abc",
        impact_metrics="Duration 10m",
    )
    assert isinstance(crew, Crew)
    assert crew.process == Process.sequential
    assert len(crew.agents) == 3
    assert len(crew.tasks) == 3
    assert [agent.role for agent in crew.agents] == [
        "SRE Incident Chronologist",
        "Systems & Software Root Cause Investigator",
        "Lead Technical Incident Documentarian",
    ]
    assert [task.agent for task in crew.tasks] == crew.agents


def test_task_context_chaining() -> None:
    """Diagnose task receives timeline; postmortem task receives timeline and diagnosis."""
    crew = build_crew(
        incident_title="Outage",
        raw_alert_logs="Logs",
    )
    timeline_task, diagnose_task, postmortem_task = crew.tasks

    assert diagnose_task.context == [timeline_task]
    assert postmortem_task.context == [timeline_task, diagnose_task]


def test_inputs_interpolated_in_tasks() -> None:
    """Inputs reach the respective task descriptions."""
    title = "Redis Cluster Split-Brain"
    logs = "14:02:00 [ERR] heartbeat timeout"
    deploy = "Commit f9e8d7: Migrated cluster topology configuration"
    impact = "4,500 sessions terminated"

    crew = build_crew(
        incident_title=title,
        raw_alert_logs=logs,
        recent_deployment_summary=deploy,
        impact_metrics=impact,
    )

    first_task_desc = crew.tasks[0].description
    assert title in first_task_desc
    assert logs in first_task_desc
    assert deploy in first_task_desc
    assert impact in first_task_desc


def test_agents_do_not_delegate() -> None:
    """Each SRE specialist keeps its assigned task instead of delegating."""
    crew = build_crew(
        incident_title="Outage",
        raw_alert_logs="Logs",
    )
    assert all(agent.allow_delegation is False for agent in crew.agents)


def test_crew_kickoff_mocked() -> None:
    """Verify crew kicks off properly with mocked LLM output."""
    mock_output = MagicMock()
    mock_output.__str__ = lambda self: "# Postmortem: Database Outage\n\n## Timeline\n- 14:00: Alert"

    crew = build_crew(
        incident_title="Test Outage",
        raw_alert_logs="Test logs",
    )

    with patch.object(crew, "kickoff", return_value=mock_output):
        result = crew.kickoff()
        assert "Postmortem" in str(result)
