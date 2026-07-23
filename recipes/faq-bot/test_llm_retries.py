"""Regression test for Issue #109: Verifies that LLM retries actually fire on transient HTTP failures."""

import http.server
import json
import os
import sys
import threading
from pathlib import Path

# Fix Windows console UTF-8 output if needed
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure recipe directory is on sys.path
sys.path.insert(0, str(Path(__file__).parent))

from llm import MAX_RETRIES, get_llm  # noqa: E402


class MockOpenAIHandler(http.server.BaseHTTPRequestHandler):
    request_count = 0
    mode = "retry_success"  # "retry_success" or "always_fail"

    def log_message(self, format, *args):
        pass  # Suppress HTTP server log output during test execution

    def do_POST(self):
        MockOpenAIHandler.request_count += 1

        if MockOpenAIHandler.mode == "retry_success":
            if MockOpenAIHandler.request_count <= 2:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.send_header("Retry-After", "0")
                self.end_headers()
                response = {
                    "error": {
                        "message": "Rate limit reached",
                        "type": "requests",
                        "code": "rate_limit_exceeded",
                    }
                }
                self.wfile.write(json.dumps(response).encode("utf-8"))
                return

        elif MockOpenAIHandler.mode == "always_fail":
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", "0")
            self.end_headers()
            response = {
                "error": {
                    "message": "Rate limit reached",
                    "type": "requests",
                    "code": "rate_limit_exceeded",
                }
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        # Return 200 OK on 3rd request or default success
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        response = {
            "id": "chatcmpl-mock-test",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "meta/llama-3.1-8b-instruct",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Mock completion response",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 8,
                "completion_tokens": 4,
                "total_tokens": 12,
            },
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))


def test_retries_on_transient_429_then_succeeds() -> None:
    """Test 1: Verify retries occur on HTTP 429 and subsequent call succeeds."""
    server = http.server.HTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    os.environ["LLM_API_KEY"] = "nvapi-test"
    os.environ["LLM_BASE_URL"] = f"http://127.0.0.1:{port}/v1"

    MockOpenAIHandler.request_count = 0
    MockOpenAIHandler.mode = "retry_success"

    try:
        llm = get_llm()
        result = llm.call([{"role": "user", "content": "test"}])
        assert "Mock completion response" in str(
            result
        ), f"Unexpected response: {result}"
        assert (
            MockOpenAIHandler.request_count == 3
        ), f"Expected 3 HTTP attempts (2 retries + 1 success), got {MockOpenAIHandler.request_count}"
    finally:
        server.shutdown()


def test_exhausting_retries_raises_exception() -> None:
    """Test 2: Verify exhausting retries raises an exception after MAX_RETRIES + 1 attempts."""
    server = http.server.HTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    os.environ["LLM_API_KEY"] = "nvapi-test"
    os.environ["LLM_BASE_URL"] = f"http://127.0.0.1:{port}/v1"

    MockOpenAIHandler.request_count = 0
    MockOpenAIHandler.mode = "always_fail"

    failed = False
    try:
        llm = get_llm()
        llm.call([{"role": "user", "content": "test"}])
    except Exception:
        failed = True
    finally:
        server.shutdown()

    assert failed, "Expected call to fail after exhausting all retries"
    expected_attempts = MAX_RETRIES + 1
    assert (
        MockOpenAIHandler.request_count == expected_attempts
    ), f"Expected {expected_attempts} attempts before raising, got {MockOpenAIHandler.request_count}"


if __name__ == "__main__":
    test_retries_on_transient_429_then_succeeds()
    test_exhausting_retries_raises_exception()
    print("✅ faq-bot: LLM retry regression test passed (#109)")
