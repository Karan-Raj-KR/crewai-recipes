"""Regression test for Issue #109: Verifies that LLM retries actually fire on transient HTTP failures."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Fix Windows console UTF-8 output if needed
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure repo root and recipe directory are on sys.path
recipe_dir = Path(__file__).parent
repo_root = recipe_dir.parent.parent
sys.path.insert(0, str(repo_root))
sys.path.insert(0, str(recipe_dir))

from llm import MAX_RETRIES, get_llm  # noqa: E402
from tests.shared_mock import (  # noqa: E402
    MockOpenAIHandler,
    start_mock_openai_server,
    stop_mock_openai_server,
)


def test_retries_on_transient_429_then_succeeds() -> None:
    """Test 1: Verify retries occur on HTTP 429 and subsequent call succeeds."""
    server, _, port = start_mock_openai_server()

    MockOpenAIHandler.request_count = 0
    MockOpenAIHandler.mode = "retry_success"

    env_mock = {
        "LLM_API_KEY": "nvapi-test",
        "LLM_BASE_URL": f"http://127.0.0.1:{port}/v1",
    }

    try:
        with patch.dict(os.environ, env_mock):
            llm = get_llm()
            result = llm.call([{"role": "user", "content": "test"}])
            assert "Mock completion response" in str(
                result
            ), f"Unexpected response: {result}"
            assert (
                MockOpenAIHandler.request_count == 3
            ), f"Expected 3 HTTP attempts (2 retries + 1 success), got {MockOpenAIHandler.request_count}"
    finally:
        stop_mock_openai_server(server)


def test_exhausting_retries_raises_exception() -> None:
    """Test 2: Verify exhausting retries raises an exception after MAX_RETRIES + 1 attempts."""
    server, _, port = start_mock_openai_server()

    MockOpenAIHandler.request_count = 0
    MockOpenAIHandler.mode = "always_fail"

    env_mock = {
        "LLM_API_KEY": "nvapi-test",
        "LLM_BASE_URL": f"http://127.0.0.1:{port}/v1",
    }

    failed = False
    try:
        with patch.dict(os.environ, env_mock):
            llm = get_llm()
            llm.call([{"role": "user", "content": "test"}])
    except Exception:
        failed = True
    finally:
        stop_mock_openai_server(server)

    assert failed, "Expected call to fail after exhausting all retries"
    expected_attempts = MAX_RETRIES + 1
    assert (
        MockOpenAIHandler.request_count == expected_attempts
    ), f"Expected {expected_attempts} attempts before raising, got {MockOpenAIHandler.request_count}"


if __name__ == "__main__":
    test_retries_on_transient_429_then_succeeds()
    test_exhausting_retries_raises_exception()
    print("✅ appointment-booking: LLM retry regression test passed (#109)")
