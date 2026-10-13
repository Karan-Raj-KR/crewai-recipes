"""Shared mock HTTP server utilities for OpenAI-compatible LLM endpoint testing."""

import http.server
import json
import threading
from typing import Tuple


class MockOpenAIHandler(http.server.BaseHTTPRequestHandler):
    """Mock HTTP handler simulating OpenAI chat completions API responses."""

    request_count = 0
    mode = "retry_success"  # "retry_success" (429 x2 then 200) or "always_fail" (503)

    def log_message(self, format, *args):
        pass  # Suppress HTTP server log output during test runs

    def do_POST(self):
        # Read the incoming request body to prevent connection reset errors in clients
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            self.rfile.read(content_length)

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
            # 503, not 429: since crewai 1.15.23 a rate-limit error is retried
            # again by crewai's own outer loop (3 attempts), so a persistent 429
            # yields (MAX_RETRIES + 1) * 3 requests. A server error is retried
            # only by the SDK, which isolates the MAX_RETRIES wiring under test.
            # The body must not say "rate limit" or crewai classifies it as one.
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.send_header("Retry-After", "0")
            self.end_headers()
            response = {
                "error": {
                    "message": "Service temporarily unavailable",
                    "type": "server_error",
                    "code": "service_unavailable",
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


def start_mock_openai_server() -> Tuple[http.server.HTTPServer, threading.Thread, int]:
    """Start an in-process mock OpenAI HTTP server on a random free port.

    Returns:
        A tuple of (server_instance, server_thread, port).
    """
    server = http.server.HTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
    port = server.server_address[1]
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    return server, server_thread, port


def stop_mock_openai_server(server: http.server.HTTPServer) -> None:
    """Safely shut down and close listening socket to prevent file descriptor leaks."""
    try:
        server.shutdown()
    finally:
        server.server_close()
