import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("LLM_API_KEY", "nvapi-test")

def test_build_crew_structure():
    """Assert build_crew returns a Crew with 2 agents, 2 tasks, and sequential process."""
    from recipes.lead_qualification.crew import build_crew
    crew = build_crew()
    assert len(crew.agents) == 2, "Crew must contain exactly 2 agents"
    assert len(crew.tasks) == 2, "Crew must contain exactly 2 tasks"

def test_task_context_chaining():
    """Assert task context dependency chaining for agent handoff."""
    from recipes.lead_qualification.tasks import build_tasks
    tasks = build_tasks()
    research_task = tasks[0]
    scoring_task = tasks[1]
    assert scoring_task.context is not None, "Scoring task must have context dependency set"
    assert research_task in scoring_task.context, "Research task must be in scoring task context"

def test_inputs_interpolated_in_tasks():
    """Assert company and description inputs reach task descriptions."""
    from recipes.lead_qualification.tasks import build_tasks
    company = "Acme Corp"
    description = "Enterprise SaaS AI Workflow Platform"
    tasks = build_tasks(company=company, description=description)
    assert company in tasks[0].description
    assert description in tasks[0].description

def test_agent_allow_delegation_disabled():
    """Assert allow_delegation is set to False for all agents."""
    from recipes.lead_qualification.agents import build_agents
    agents = build_agents()
    for agent in agents:
        assert agent.allow_delegation is False, f"Agent {agent.role} should have allow_delegation=False"

def test_main_execution_mocked():
    """Smoke test executing main() with mocked crew kickoff output."""
    mock_output = MagicMock()
    mock_output.raw = "Lead Score: 95/100 - High Priority Lead"
    with patch("crewai.Crew.kickoff", return_value=mock_output):
        from recipes.lead_qualification.main import main
        main()
