"""Unit test for Issue #63: Verifies that running multiple recipes in the playground server

process does not contaminate sys.modules or reuse cached agents/tasks/llm modules.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

if "crewai" not in sys.modules:
    sys.modules["crewai"] = MagicMock()

from main import app, cleanup_recipe_modules

client = TestClient(app)


def test_cross_recipe_module_contamination() -> None:
    """Verify sequential execution of different recipes loads correct recipe-specific agents."""
    env_mock = {"LLM_API_KEY": "nvapi-test"}

    # Recipe 1: faq-bot (1 agent)
    with patch.dict(os.environ, env_mock), patch("crewai.Crew.kickoff", return_value="Mocked FAQ reply"):
        res1 = client.post(
            "/run",
            json={
                "recipe": "faq-bot",
                "inputs": {
                    "question": "Do you offer a free trial?",
                    "customer_name": "Alice",
                },
            },
        )
        assert res1.status_code == 200, f"faq-bot failed: {res1.text}"

    # Verify sys.modules does not contain leftover recipe-local modules
    assert "agents" not in sys.modules
    assert "tasks" not in sys.modules
    assert "llm" not in sys.modules
    assert "knowledge_base" not in sys.modules
    assert "recipe_crew" not in sys.modules

    # Recipe 2: lead-qualification (2 agents)
    # Without fix, lead-qualification would resolve from faq-bot's cached 'agents' module
    with patch.dict(os.environ, env_mock), patch("crewai.Crew.kickoff", return_value="Mocked Lead Report"):
        res2 = client.post(
            "/run",
            json={
                "recipe": "lead-qualification",
                "inputs": {
                    "company": "Acme Corp",
                    "description": "B2B SaaS startup",
                },
            },
        )
        assert res2.status_code == 200, f"lead-qualification failed: {res2.text}"

    assert "agents" not in sys.modules
    assert "tasks" not in sys.modules

    # Recipe 3: support-escalation (3 agents)
    with patch.dict(os.environ, env_mock), patch("crewai.Crew.kickoff", return_value="Mocked Support Outcome"):
        res3 = client.post(
            "/run",
            json={
                "recipe": "support-escalation",
                "inputs": {
                    "ticket_text": "Need billing invoice PDF",
                    "customer_tier": "pro",
                    "previous_contacts": "0",
                },
            },
        )
        assert res3.status_code == 200, f"support-escalation failed: {res3.text}"

    assert "agents" not in sys.modules

    print("✅ test_cross_recipe_module_contamination passed (#63)")


def test_cleanup_recipe_modules_direct() -> None:
    """Direct test for cleanup_recipe_modules helper function."""
    faq_dir = playground_dir.parent / "recipes" / "faq-bot"

    # Simulate module pollution in sys.modules
    sys.modules["agents"] = type(sys)("agents")
    sys.modules["tasks"] = type(sys)("tasks")
    sys.modules["knowledge_base"] = type(sys)("knowledge_base")
    sys.modules["recipe_crew"] = type(sys)("recipe_crew")

    cleanup_recipe_modules(faq_dir)

    assert "agents" not in sys.modules
    assert "tasks" not in sys.modules
    assert "knowledge_base" not in sys.modules
    assert "recipe_crew" not in sys.modules
    print("✅ test_cleanup_recipe_modules_direct passed (#63)")


if __name__ == "__main__":
    test_cross_recipe_module_contamination()
    test_cleanup_recipe_modules_direct()
    print("✅ All module contamination unit tests passed!")
