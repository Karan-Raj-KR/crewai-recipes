"""Unit tests for Issue #68: Playground response caching for identical runs."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

# Ensure playground directory is on sys.path
playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

from main import ResponseCache, app, response_cache  # noqa: E402

client = TestClient(app)


def test_response_cache_lru_and_canonicalization() -> None:
    """Test ResponseCache key ordering, LRU eviction, and maxsize bound."""
    cache = ResponseCache(maxsize=2)

    # Key canonicalization check (sorted dict keys produce identical cache keys)
    cache.set("faq-bot", {"b": "2", "a": "1"}, "Output 1")
    cached_val = cache.get("faq-bot", {"a": "1", "b": "2"})
    assert cached_val == "Output 1"

    # LRU eviction check
    cache.set("lead-qualification", {"company": "Acme"}, "Output 2")
    assert cache.get("faq-bot", {"a": "1", "b": "2"}) == "Output 1"

    # Overflowing maxsize=2 evicts oldest key ("lead-qualification")
    cache.set("support-escalation", {"ticket": "123"}, "Output 3")
    assert cache.get("lead-qualification", {"company": "Acme"}) is None
    assert cache.get("faq-bot", {"a": "1", "b": "2"}) == "Output 1"
    assert cache.get("support-escalation", {"ticket": "123"}) == "Output 3"


def test_run_endpoint_caching_and_bypass() -> None:
    """Test POST /run caching behavior and no_cache / bypass_cache flag."""
    response_cache.clear()
    env_mock = {"LLM_API_KEY": "nvapi-test"}
    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "What is the price?", "customer_name": "Bob"},
    }

    with patch.dict(os.environ, env_mock):
        with patch("crewai.Crew.kickoff", return_value="Fresh Output #1") as mock_kick:
            # 1. First run -> Fresh execution (cached: False)
            res1 = client.post("/run", json=payload)
            assert res1.status_code == 200
            data1 = res1.json()
            assert data1["output"] == "Fresh Output #1"
            assert data1["cached"] is False
            assert mock_kick.call_count == 1

        with patch("crewai.Crew.kickoff", return_value="Fresh Output #2") as mock_kick:
            # 2. Second identical run -> Returned from cache (cached: True, no kickoff call)
            res2 = client.post("/run", json=payload)
            assert res2.status_code == 200
            data2 = res2.json()
            assert data2["output"] == "Fresh Output #1"
            assert data2["cached"] is True
            assert mock_kick.call_count == 0

        with patch("crewai.Crew.kickoff", return_value="Fresh Output #3") as mock_kick:
            # 3. Third run with bypass_cache: True -> Forces fresh execution
            payload_bypass = {**payload, "bypass_cache": True}
            res3 = client.post("/run", json=payload_bypass)
            assert res3.status_code == 200
            data3 = res3.json()
            assert data3["output"] == "Fresh Output #3"
            assert data3["cached"] is False
            assert mock_kick.call_count == 1


def test_stream_endpoint_caching() -> None:
    """Test POST /run/stream SSE endpoint caching behavior."""
    response_cache.clear()
    response_cache.set(
        "faq-bot", {"question": "Hi", "customer_name": "Sam"}, "Cached Stream Output"
    )

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Hi", "customer_name": "Sam"},
    }
    res = client.post("/run/stream", json=payload)
    assert res.status_code == 200
    assert "data: " in res.text
    assert '"cached": true' in res.text or '"cached": True' in res.text
    assert "Cached Stream Output" in res.text


def test_errors_are_not_cached() -> None:
    """Verify that execution errors / HTTPExceptions are never saved to cache."""
    response_cache.clear()
    with patch.dict(os.environ, {}, clear=True):
        payload = {
            "recipe": "faq-bot",
            "inputs": {"question": "Hi", "customer_name": "Sam"},
        }
        res = client.post("/run", json=payload)
        assert res.status_code == 401
        assert response_cache.get("faq-bot", payload["inputs"]) is None
