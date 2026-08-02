from unittest.mock import patch
from crewai import Crew, Process
from crew import build_crew
from agents import build_agents
from tasks import build_tasks

@patch("agents.get_llm")
def test_build_agents(mock_get_llm):
    mock_get_llm.return_value = 'mock_model'
    researcher, scorer = build_agents()
    
    assert researcher.role == "Company Research Analyst"
    assert researcher.allow_delegation is False
    
    assert scorer.role == "ICP Scoring Specialist"
    assert scorer.allow_delegation is False

@patch("agents.get_llm")
def test_build_tasks(mock_get_llm):
    mock_get_llm.return_value = 'mock_model'
    researcher, scorer = build_agents()
    
    company_name = "TestCorp"
    company_desc = "Test description of TestCorp"
    
    tasks = build_tasks(researcher, scorer, company_name, company_desc)
    
    assert len(tasks) == 2
    research_task = tasks[0]
    scoring_task = tasks[1]
    
    assert research_task.agent == researcher
    assert company_name in research_task.description
    assert company_desc in research_task.description
    
    assert scoring_task.agent == scorer
    assert company_name in scoring_task.description
    # Verify chaining
    assert scoring_task.context == [research_task]

@patch("agents.get_llm")
def test_build_crew(mock_get_llm):
    mock_get_llm.return_value = 'mock_model'
    company_name = "TestCorp"
    company_desc = "Test description of TestCorp"
    
    crew = build_crew(company_name, company_desc)
    
    assert isinstance(crew, Crew)
    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2
    assert crew.process == Process.sequential
