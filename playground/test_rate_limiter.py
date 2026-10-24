"""Deterministic unit and integration tests for Issue #181: Playground rate limiting."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

# Ensure playground directory is on sys.path
playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

if "crewai" not in sys.modules:
    sys.modules["crewai"] = MagicMock()

from main import app, rate_limiter, response_cache  # noqa: E402
from rate_limiter import SlidingWindowRateLimiter, get_client_ip  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_rate_limiter_state():
    """Ensure clean rate limiter and cache state before and after each test."""
    rate_limiter.parse_config(os.getenv("PLAYGROUND_RATE_LIMIT", "30/5min"))
    rate_limiter.reset()
    response_cache.clear()
    yield
    rate_limiter.parse_config(os.getenv("PLAYGROUND_RATE_LIMIT", "30/5min"))
    rate_limiter.reset()
    response_cache.clear()


# ---------------------------------------------------------------------------
# Unit Tests: SlidingWindowRateLimiter
# ---------------------------------------------------------------------------


def test_sliding_window_unit_limits_and_expiry() -> None:
    """Verify exact request counting, sliding window cutoffs, and retry_after."""
    limiter = SlidingWindowRateLimiter(limit_string="3/10s")

    # t = 100.0: first 3 requests allowed
    assert limiter.is_allowed("client-1", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-1", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-1", now=100.0) == (True, 0)

    # 4th request at t=100.0 is blocked; oldest timestamp is 100.0 -> retry_after = 10s
    allowed, retry_after = limiter.is_allowed("client-1", now=100.0)
    assert allowed is False
    assert retry_after == 10

    # t = 104.0: still within the 10s window (oldest=100.0, expires at 110.0 -> retry_after = 6s)
    allowed, retry_after = limiter.is_allowed("client-1", now=104.0)
    assert allowed is False
    assert retry_after == 6

    # t = 111.0: window [101.0, 111.0] has 0 prior requests; all 3 from t=100 expired
    allowed, retry_after = limiter.is_allowed("client-1", now=111.0)
    assert allowed is True
    assert retry_after == 0


def test_sliding_window_disabled_mode() -> None:
    """Verify PLAYGROUND_RATE_LIMIT=0 permits arbitrary bursts without tracking."""
    limiter = SlidingWindowRateLimiter(limit_string="0")
    assert limiter.enabled is False

    for _ in range(50):
        allowed, retry_after = limiter.is_allowed("any-client")
        assert allowed is True
        assert retry_after == 0


def test_sliding_window_client_isolation() -> None:
    """Verify distinct client keys maintain separate rate-limiting windows."""
    limiter = SlidingWindowRateLimiter(limit_string="2/60s")

    # Exhaust client A
    assert limiter.is_allowed("client-a", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-a", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-a", now=100.0)[0] is False

    # Client B should have full quota
    assert limiter.is_allowed("client-b", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-b", now=100.0) == (True, 0)
    assert limiter.is_allowed("client-b", now=100.0)[0] is False


def test_sliding_window_time_units_and_fallback() -> None:
    """Verify time unit parsing (s, min, h, d) and graceful fallback on malformed input."""
    # Standard formats
    lim1 = SlidingWindowRateLimiter(limit_string="10/s")
    assert lim1.limit == 10 and lim1.window_seconds == 1

    lim2 = SlidingWindowRateLimiter(limit_string="30/5min")
    assert lim2.limit == 30 and lim2.window_seconds == 300

    lim3 = SlidingWindowRateLimiter(limit_string="60/m")
    assert lim3.limit == 60 and lim3.window_seconds == 60

    lim4 = SlidingWindowRateLimiter(limit_string="100/1h")
    assert lim4.limit == 100 and lim4.window_seconds == 3600

    # Malformed strings fall back safely to 30/300s (default 30/5min)
    lim_invalid = SlidingWindowRateLimiter(limit_string="invalid_syntax")
    assert lim_invalid.enabled is True
    assert lim_invalid.limit == 30
    assert lim_invalid.window_seconds == 300


def test_sliding_window_concurrency_atomic() -> None:
    """Verify thread-safety of sliding window under concurrent requests."""
    limiter = SlidingWindowRateLimiter(limit_string="25/60s")
    results: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        for _ in range(5):
            allowed, _ = limiter.is_allowed("thread-client")
            with lock:
                results.append(allowed)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Out of 50 total requests, exactly 25 must be permitted and 25 rejected
    assert results.count(True) == 25
    assert results.count(False) == 25


def test_sliding_window_memory_pruning() -> None:
    """Verify stale client keys are pruned to keep memory bounded."""
    limiter = SlidingWindowRateLimiter(limit_string="5/10s", max_clients=5)

    # Insert 5 clients at t=100.0
    for i in range(5):
        limiter.is_allowed(f"old-client-{i}", now=100.0)
    assert len(limiter._clients) == 5

    # At t=120.0 (past 10s window), adding a 6th client triggers pruning of stale clients
    limiter.is_allowed("new-client", now=120.0)
    assert len(limiter._clients) <= 5
    assert "new-client" in limiter._clients


def test_get_client_ip_fallbacks() -> None:
    """Verify safe IP extraction and fallback to 'unknown_client'."""
    # Valid client host
    req_valid = MagicMock(client=MagicMock(host="10.0.0.1"))
    assert get_client_ip(req_valid) == "10.0.0.1"

    # Missing client
    req_none = MagicMock(client=None)
    assert get_client_ip(req_none) == "unknown_client"

    # Empty host
    req_empty = MagicMock(client=MagicMock(host="   "))
    assert get_client_ip(req_empty) == "unknown_client"


# ---------------------------------------------------------------------------
# Integration Tests: FastAPI Endpoints
# ---------------------------------------------------------------------------


def test_run_endpoint_31st_request_returns_429() -> None:
    """Assert exactly 30 requests succeed and the 31st returns HTTP 429 with Retry-After."""
    rate_limiter.parse_config("30/5min")
    rate_limiter.reset()
    response_cache.clear()

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Test question", "customer_name": "Alice"},
    }

    def _exec(mod):
        mod.build_crew = MagicMock(
            return_value=MagicMock(kickoff=MagicMock(return_value="Output"))
        )

    with (
        patch.dict(os.environ, {"LLM_API_KEY": "test-key"}),
        patch("importlib.machinery.SourceFileLoader.exec_module", side_effect=_exec),
    ):
        # Send 30 requests in a tight loop -> all succeed
        for i in range(30):
            res = client.post("/run", json=payload)
            assert res.status_code == 200, f"Request {i + 1} failed: {res.text}"

        # 31st request from same client -> must be rejected with 429
        res31 = client.post("/run", json=payload)
        assert res31.status_code == 429
        assert "Retry-After" in res31.headers
        retry_after = int(res31.headers["Retry-After"])
        assert 0 < retry_after <= 300
        assert "Rate limit exceeded" in res31.json()["detail"]


def test_run_endpoint_rejection_prevents_llm_execution() -> None:
    """Verify that rejected requests never invoke crew.kickoff() or start LLM work."""
    rate_limiter.parse_config("3/60s")
    rate_limiter.reset()
    response_cache.clear()

    mock_kickoff = MagicMock(return_value="Output")

    def _exec(mod):
        mod.build_crew = MagicMock(return_value=MagicMock(kickoff=mock_kickoff))

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Test", "customer_name": "Bob"},
        "bypass_cache": True,  # Ensure every accepted request executes crew
    }

    with (
        patch.dict(os.environ, {"LLM_API_KEY": "test-key"}),
        patch("importlib.machinery.SourceFileLoader.exec_module", side_effect=_exec),
    ):
        # 3 allowed requests
        for _ in range(3):
            res = client.post("/run", json=payload)
            assert res.status_code == 200

        assert mock_kickoff.call_count == 3

        # 4th request rejected by limiter
        res_rejected = client.post("/run", json=payload)
        assert res_rejected.status_code == 429

        # Proof: kickoff was NOT called for the rejected request
        assert mock_kickoff.call_count == 3


def test_cross_endpoint_quota_sharing() -> None:
    """Verify that /run, /run/stream, and /run/ws share one unified per-client quota."""
    rate_limiter.parse_config("6/60s")
    rate_limiter.reset()
    response_cache.clear()

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Test", "customer_name": "Carol"},
    }

    def _exec(mod):
        mod.build_crew = MagicMock(
            return_value=MagicMock(kickoff=MagicMock(return_value="Output"))
        )

    with (
        patch.dict(os.environ, {"LLM_API_KEY": "test-key"}),
        patch("importlib.machinery.SourceFileLoader.exec_module", side_effect=_exec),
    ):
        # 1. Two calls to /run (uses quota 1 and 2)
        for _ in range(2):
            res = client.post("/run", json=payload)
            assert res.status_code == 200

        # 2. Two calls to /run/stream (uses quota 3 and 4)
        for _ in range(2):
            res = client.post("/run/stream", json=payload)
            assert res.status_code == 200

        # 3. Two connections to /run/ws (uses quota 5 and 6)
        for _ in range(2):
            with client.websocket_connect("/run/ws") as ws:
                ws.send_json(payload)
                msg1 = ws.receive_json()
                assert msg1["type"] == "start"

        # Quota of 6 is now completely exhausted.
        # 4. 7th call to /run -> rejected with 429
        res_run = client.post("/run", json=payload)
        assert res_run.status_code == 429

        # 5. 8th call to /run/stream -> rejected with 429
        res_stream = client.post("/run/stream", json=payload)
        assert res_stream.status_code == 429

        # 6. 9th connection to /run/ws -> rejected with close code 1008
        with (
            pytest.raises(WebSocketDisconnect) as exc_info,
            client.websocket_connect("/run/ws") as ws,
        ):
            ws.receive_json()
        assert exc_info.value.code == 1008


def test_stream_endpoint_rate_limit_exceeded() -> None:
    """Verify /run/stream returns HTTP 429 immediately when quota is exhausted."""
    rate_limiter.parse_config("1/60s")
    rate_limiter.reset()

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Test", "customer_name": "Dave"},
    }

    with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
        # First call succeeds
        res1 = client.post("/run/stream", json=payload)
        assert res1.status_code == 200

        # Second call exceeds limit -> clean HTTP 429
        res2 = client.post("/run/stream", json=payload)
        assert res2.status_code == 429
        assert "Retry-After" in res2.headers
        assert "Rate limit exceeded" in res2.json()["detail"]


def test_websocket_endpoint_rejection_code_1008() -> None:
    """Verify /run/ws closes with RFC 6455 status code 1008 before accept."""
    rate_limiter.parse_config("1/60s")
    rate_limiter.reset()

    payload = {"recipe": "faq-bot", "inputs": {"question": "Q"}}

    with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
        # First websocket connection allowed
        with client.websocket_connect("/run/ws") as ws:
            ws.send_json(payload)
            msg = ws.receive_json()
            assert msg["type"] == "start"

        # Second connection exceeds limit -> closed with 1008
        with (
            pytest.raises(WebSocketDisconnect) as exc_info,
            client.websocket_connect("/run/ws") as ws,
        ):
            ws.receive_json()
        assert exc_info.value.code == 1008


def test_disabled_mode_permits_burst_on_endpoints() -> None:
    """Verify PLAYGROUND_RATE_LIMIT=0 permits burst requests on /run."""
    rate_limiter.parse_config("0")
    rate_limiter.reset()
    response_cache.clear()

    payload = {
        "recipe": "faq-bot",
        "inputs": {"question": "Burst", "customer_name": "Eve"},
    }

    def _exec(mod):
        mod.build_crew = MagicMock(
            return_value=MagicMock(kickoff=MagicMock(return_value="Output"))
        )

    with (
        patch.dict(os.environ, {"LLM_API_KEY": "test-key"}),
        patch("importlib.machinery.SourceFileLoader.exec_module", side_effect=_exec),
    ):
        for _ in range(40):
            res = client.post("/run", json=payload)
            assert res.status_code == 200


def test_exempt_routes_unaffected_when_quota_exhausted() -> None:
    """Verify GET /recipes and static file serving remain unaffected by rate limiting."""
    rate_limiter.parse_config("1/60s")
    rate_limiter.reset()

    # Exhaust execution quota
    allowed, _ = rate_limiter.is_allowed("testclient")
    assert allowed is True
    allowed_again, _ = rate_limiter.is_allowed("testclient")
    assert allowed_again is False

    # GET /recipes must still return 200 OK
    res_recipes = client.get("/recipes")
    assert res_recipes.status_code == 200
    assert "recipes" in res_recipes.json()

    # Static file serving must still return 200 OK
    res_static = client.get("/")
    assert res_static.status_code == 200
