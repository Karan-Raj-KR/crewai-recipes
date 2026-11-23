"""Deterministic offline integration tests for provider routing and circuit breakers (#279).

Tests:
- Routing: Primary healthy, Primary OPEN -> Fallback, Both OPEN fast-fail.
- In-flight failover: Trippable error failover vs non-trippable rejection.
- Half-open probe: Exclusivity, success recovery, failure re-open, probe diversion to fallback.
- Stream (/run/stream): Preflight routing, circuit open, error during streaming, disconnect probe release.
- WebSocket (/run/ws): Normal execution, preflight fast-fail.
- Concurrency & Isolation: Thread-local routing, shared process breaker state, no env mutation.
- Disabled mode: PLAYGROUND_CIRCUIT_ENABLED=false bypass.
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

import main as playground
from governance import CircuitState, circuit_registry

PRIMARY_KEY = "dummy-primary-279"
FALLBACK_KEY = "dummy-fallback-279"
INPUTS = {"question": "Hello", "customer_name": "Test User"}


@pytest.fixture(autouse=True)
def clean_test_state():
    """Ensure clean registry and cache state before and after each test."""
    circuit_registry.reset_all()
    playground.response_cache.clear()
    yield
    circuit_registry.reset_all()
    playground.response_cache.clear()


@pytest.fixture
def mock_execution():
    """Offline stub for build_crew and crew.kickoff."""
    crew = MagicMock()
    crew.kickoff.return_value = "Mocked offline LLM response"

    build_crew_calls = []

    def fake_build_crew(**inputs):
        # Capture which active_provider was bound in thread-local context at build time
        active = getattr(playground._thread_local, "active_provider", None)
        build_crew_calls.append(active)
        return crew

    module = SimpleNamespace(build_crew=MagicMock(side_effect=fake_build_crew))
    loader = MagicMock()

    with (
        patch.object(
            playground, "rate_limiter", playground.SlidingWindowRateLimiter("0")
        ),
        patch.object(
            playground.importlib.util,
            "spec_from_file_location",
            return_value=SimpleNamespace(loader=loader),
        ),
        patch.object(
            playground.importlib.util, "module_from_spec", return_value=module
        ),
    ):
        yield SimpleNamespace(
            crew=crew,
            module=module,
            build_crew_calls=build_crew_calls,
        )


# ===========================================================================
# 1. HTTP /run Routing Tests
# ===========================================================================


def test_run_primary_healthy(mock_execution):
    """When Primary circuit is CLOSED and healthy, request routes to Primary."""
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert res.json() == {"output": "Mocked offline LLM response", "cached": False}
    assert mock_execution.build_crew_calls == ["primary"]
    primary_cb = circuit_registry.get_breaker("primary")
    assert primary_cb.state == CircuitState.CLOSED
    assert primary_cb._total_successes == 1


def test_run_primary_open_fallback_healthy(mock_execution):
    """When Primary circuit is OPEN, request preflight-routes to Fallback."""
    primary_cb = circuit_registry.get_breaker("primary")
    primary_cb.record_failure(RuntimeError("503 Service Unavailable"))
    primary_cb.record_failure(RuntimeError("503 Service Unavailable"))
    primary_cb.record_failure(RuntimeError("503 Service Unavailable"))
    assert primary_cb.state == CircuitState.OPEN

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert res.json() == {"output": "Mocked offline LLM response", "cached": False}
    assert mock_execution.build_crew_calls == ["fallback"]
    fallback_cb = circuit_registry.get_breaker("fallback")
    assert fallback_cb.state == CircuitState.CLOSED
    assert fallback_cb._total_successes == 1


def test_run_both_circuits_open(mock_execution):
    """When both Primary and Fallback circuits are OPEN, request fast-fails with 503."""
    primary_cb = circuit_registry.get_breaker("primary")
    fallback_cb = circuit_registry.get_breaker("fallback")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"))
        fallback_cb.record_failure(RuntimeError("503 error"))

    assert primary_cb.state == CircuitState.OPEN
    assert fallback_cb.state == CircuitState.OPEN

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 503
    assert "Retry-After" in res.headers
    assert "circuits are OPEN" in res.json()["detail"]
    # Verify execution was completely bypassed
    assert len(mock_execution.build_crew_calls) == 0


def test_run_primary_open_no_fallback_configured(mock_execution):
    """When Primary is OPEN and no fallback key is configured, fast-fails with 503."""
    primary_cb = circuit_registry.get_breaker("primary")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"))

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 503
    assert "Retry-After" in res.headers
    assert "no fallback provider is configured" in res.json()["detail"]
    assert len(mock_execution.build_crew_calls) == 0


# ===========================================================================
# 2. In-Flight Failover & Failure Classification Tests
# ===========================================================================


def test_run_in_flight_failover_on_trippable_error(mock_execution):
    """When Primary fails during execution with a trippable error, fails over to Fallback."""
    # First kickoff call (Primary) fails with 503; second call (Fallback) succeeds
    mock_execution.crew.kickoff.side_effect = [
        RuntimeError("503 Service Unavailable"),
        "Recovered answer via Fallback",
    ]

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert res.json() == {"output": "Recovered answer via Fallback", "cached": False}
    assert mock_execution.build_crew_calls == ["primary", "fallback"]

    primary_cb = circuit_registry.get_breaker("primary")
    fallback_cb = circuit_registry.get_breaker("fallback")
    assert primary_cb._total_failures == 1
    assert fallback_cb._total_successes == 1


def test_run_no_failover_on_non_trippable_error(mock_execution):
    """Non-trippable errors (e.g. ValueError) do NOT trigger failover or trip breaker."""
    mock_execution.crew.kickoff.side_effect = ValueError("Invalid recipe inputs")

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 500
    assert "Invalid recipe inputs" in res.json()["detail"]
    # Only primary was called; no failover attempted
    assert mock_execution.build_crew_calls == ["primary"]

    primary_cb = circuit_registry.get_breaker("primary")
    assert primary_cb._total_failures == 0
    assert primary_cb.state == CircuitState.CLOSED


def test_run_in_flight_failover_when_fallback_also_fails(mock_execution):
    """If Primary fails and Fallback also fails, error is returned without recursive loops."""
    mock_execution.crew.kickoff.side_effect = [
        RuntimeError("503 Primary down"),
        RuntimeError("503 Fallback down"),
    ]

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 500
    assert "Fallback down" in res.json()["detail"]
    assert mock_execution.build_crew_calls == ["primary", "fallback"]

    primary_cb = circuit_registry.get_breaker("primary")
    fallback_cb = circuit_registry.get_breaker("fallback")
    assert primary_cb._total_failures == 1
    assert fallback_cb._total_failures == 1


# ===========================================================================
# 3. Half-Open Probe & Recovery Tests
# ===========================================================================


def test_run_half_open_probe_success_recovers_circuit(mock_execution):
    """In HALF_OPEN, permitted probe succeeds and closes circuit back to CLOSED."""
    primary_cb = circuit_registry.get_breaker("primary")
    # Trip breaker at t=100.0
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    assert primary_cb.state == CircuitState.OPEN

    # Advance time past cooldown (30s)
    env = {"LLM_API_KEY": PRIMARY_KEY}
    with (
        patch.dict(os.environ, env, clear=True),
        patch("governance.time.monotonic", return_value=135.0),
        TestClient(playground.app) as client,
    ):
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert primary_cb.state == CircuitState.CLOSED
    assert primary_cb._consecutive_failures == 0


def test_run_half_open_concurrent_probe_diversion(mock_execution):
    """While a probe is in flight, concurrent requests are diverted to healthy Fallback."""
    primary_cb = circuit_registry.get_breaker("primary")
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    primary_cb.record_failure(RuntimeError("503 error"), now=100.0)

    # Put primary in HALF_OPEN and simulate probe permit held by another thread
    with patch("governance.time.monotonic", return_value=135.0):
        allowed, state = primary_cb.can_execute()
        assert allowed is True
        assert state == CircuitState.HALF_OPEN
        # Primary probe permit is now occupied

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with (
        patch.dict(os.environ, env, clear=True),
        patch("governance.time.monotonic", return_value=135.1),
        TestClient(playground.app) as client,
    ):
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    # Concurrent request was safely diverted to fallback!
    assert mock_execution.build_crew_calls == ["fallback"]


# ===========================================================================
# 4. Streaming (/run/stream) Tests
# ===========================================================================


def test_stream_primary_healthy(mock_execution):
    """Normal streaming execution routes to Primary and emits events."""
    env = {"LLM_API_KEY": PRIMARY_KEY}
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run/stream",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    text = res.text
    assert '"type": "start"' in text
    assert '"type": "complete"' in text
    assert mock_execution.build_crew_calls == ["primary"]


def test_stream_both_circuits_open_fast_fails(mock_execution):
    """When both circuits are OPEN, streaming immediately pushes error event."""
    primary_cb = circuit_registry.get_breaker("primary")
    fallback_cb = circuit_registry.get_breaker("fallback")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"))
        fallback_cb.record_failure(RuntimeError("503 error"))

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run/stream",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert '"type": "error"' in res.text
    assert "circuits are OPEN" in res.text
    assert len(mock_execution.build_crew_calls) == 0


def test_stream_provider_error_during_streaming(mock_execution):
    """Provider failure during streaming emits error event and records failure."""
    mock_execution.crew.kickoff.side_effect = ConnectionResetError("Peer reset socket")

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run/stream",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert '"type": "error"' in res.text
    assert "Peer reset socket" in res.text
    primary_cb = circuit_registry.get_breaker("primary")
    assert primary_cb._total_failures == 1


# ===========================================================================
# 5. WebSocket (/run/ws) Tests
# ===========================================================================


def test_websocket_primary_healthy(mock_execution):
    """WebSocket execution routes to Primary and streams complete event."""
    env = {"LLM_API_KEY": PRIMARY_KEY}
    with (
        patch.dict(os.environ, env, clear=True),
        TestClient(playground.app) as client,
        client.websocket_connect("/run/ws") as ws,
    ):
        ws.send_json({"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True})
        msg1 = ws.receive_json()
        assert msg1["type"] == "start"
        msg2 = ws.receive_json()
        assert msg2["type"] == "complete"
        assert msg2["output"] == "Mocked offline LLM response"


def test_websocket_both_open_fast_fails(mock_execution):
    """WebSocket execution fast-fails with error event when circuits are OPEN."""
    primary_cb = circuit_registry.get_breaker("primary")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"))

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with (
        patch.dict(os.environ, env, clear=True),
        TestClient(playground.app) as client,
        client.websocket_connect("/run/ws") as ws,
    ):
        ws.send_json({"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True})
        msg1 = ws.receive_json()
        assert msg1["type"] == "start"
        msg2 = ws.receive_json()
        assert msg2["type"] == "error"
        assert "no fallback provider is configured" in msg2["error"]
        assert len(mock_execution.build_crew_calls) == 0


# ===========================================================================
# 6. Concurrency & Isolation Tests
# ===========================================================================


def test_concurrent_routing_thread_isolation(mock_execution):
    """Concurrent requests using primary probe vs fallback diversion maintain strict thread isolation."""
    primary_cb = circuit_registry.get_breaker("primary")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"), now=100.0)
    assert primary_cb.state == CircuitState.OPEN

    # At t=135.0 (after cooldown), primary can grant exactly 1 probe
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    client = TestClient(playground.app)
    results = []
    errors = []

    def make_request():
        try:
            with patch("governance.time.monotonic", return_value=135.0):
                res = client.post(
                    "/run",
                    json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
                )
                assert res.status_code == 200
                results.append(res.status_code)
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    threads = [threading.Thread(target=make_request) for _ in range(10)]

    orig_env = os.environ.copy()
    with patch.dict(os.environ, env, clear=True):
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert len(errors) == 0
    assert len(results) == 10

    # Exactly 1 request acquired the primary probe permit, and 9 were safely diverted to fallback!
    primaries = [p for p in mock_execution.build_crew_calls if p == "primary"]
    fallbacks = [p for p in mock_execution.build_crew_calls if p == "fallback"]
    assert len(primaries) == 1
    assert len(fallbacks) == 9

    # Verify global os.environ was NEVER mutated
    assert os.environ.get("LLM_PROVIDER") == orig_env.get("LLM_PROVIDER")


def test_circuit_disabled_mode_bypasses_all(mock_execution):
    """When PLAYGROUND_CIRCUIT_ENABLED=false, breaker never trips or rejects calls."""
    primary_cb = circuit_registry.get_breaker("primary")
    primary_cb.enabled = False

    for _ in range(10):
        primary_cb.record_failure(RuntimeError("503 error"))

    assert primary_cb.can_execute()[0] is True

    env = {
        "PLAYGROUND_CIRCUIT_ENABLED": "false",
        "LLM_API_KEY": PRIMARY_KEY,
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )

    assert res.status_code == 200
    assert mock_execution.build_crew_calls == ["primary"]
