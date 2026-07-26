import asyncio
import json
import os
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

# Ensure playground directory is on sys.path
playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

from main import app, execute_recipe_stream

client = TestClient(app)

def test_recipes_list():
    response = client.get("/recipes")
    assert response.status_code == 200
    data = response.json()
    assert "recipes" in data
    assert len(data["recipes"]) > 0
    print("✓ test_recipes_list passed")

def test_run_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        payload = {"recipe": "faq-bot", "inputs": {"question": "Hi", "customer_name": "Test"}}
        response = client.post("/run", json=payload)
        assert response.status_code == 401
        assert "LLM_API_KEY is not set" in response.json()["detail"]
    print("✓ test_run_missing_api_key passed")

def test_stream_missing_api_key():
    with patch.dict(os.environ, {}, clear=True):
        payload = {"recipe": "faq-bot", "inputs": {"question": "Hi", "customer_name": "Test"}}
        response = client.post("/run/stream", json=payload)
        assert response.status_code == 200
        lines = [line for line in response.text.split("\n\n") if line.strip()]
        assert len(lines) >= 2
        event1 = json.loads(lines[0].replace("data: ", ""))
        assert event1["type"] == "start"
        event2 = json.loads(lines[1].replace("data: ", ""))
        assert event2["type"] == "error"
        assert "API Key is missing" in event2["error"]
    print("✓ test_stream_missing_api_key passed")

def test_mock_execute_recipe_stream():
    events = []
    stop_event = threading.Event()
    def push_event(evt):
        events.append(evt)

    mock_crew = MagicMock()
    def mock_kickoff():
        step_mock = MagicMock()
        step_mock.agent = "Support Specialist"
        step_mock.thought = "Thinking..."
        step_mock.tool = "search"
        step_mock.tool_input = "query"
        step_mock.result = "found"
        mock_crew.step_callback(step_mock)

        task_mock = MagicMock()
        task_mock.agent = "Support Specialist"
        task_mock.description = "Task desc"
        task_mock.raw = "Task answer"
        mock_crew.task_callback(task_mock)
        return "Mock Answer"

    mock_crew.kickoff = mock_kickoff
    mock_module = MagicMock()
    mock_module.build_crew = MagicMock(return_value=mock_crew)

    with patch.dict(os.environ, {"LLM_API_KEY": "mock_key"}):
        with patch("importlib.util.spec_from_file_location") as mock_spec_from_file:
            mock_spec = MagicMock()
            mock_spec_from_file.return_value = mock_spec
            with patch("importlib.util.module_from_spec", return_value=mock_module):
                execute_recipe_stream("faq-bot", {"question": "q", "customer_name": "c"}, push_event, stop_event)

    event_types = [e["type"] for e in events]
    assert "agent_step" in event_types
    assert "task_complete" in event_types
    assert "complete" in event_types
    print("✓ test_mock_execute_recipe_stream passed")

def test_websocket_stream_missing_key():
    with patch.dict(os.environ, {}, clear=True):
        with client.websocket_connect("/run/ws") as websocket:
            websocket.send_json({"recipe": "faq-bot", "inputs": {"question": "q"}})
            msg1 = websocket.receive_json()
            assert msg1["type"] == "start"
            msg2 = websocket.receive_json()
            assert msg2["type"] == "error"
    print("✓ test_websocket_stream_missing_key passed")

if __name__ == "__main__":
    test_recipes_list()
    test_run_missing_api_key()
    test_stream_missing_api_key()
    test_mock_execute_recipe_stream()
    test_websocket_stream_missing_key()
    print("\nAll 5 streaming unit tests passed successfully!")
