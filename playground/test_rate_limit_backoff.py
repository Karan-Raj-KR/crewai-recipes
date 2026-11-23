"""Deterministic offline unit and integration tests for adaptive rate-limit backoff (#279).

Tests:
- Rate-limit error classification (is_rate_limit_error).
- Retry-After extraction (extract_retry_after).
- AdaptiveBackoffPolicy exponential delay calculation and jitter bounds.
- Circuit breaker dynamic cooldown override on rate limit.
- /run failover backoff delay application and HTTP 429 status translation.
- Stream (/run/stream) RATE_LIMIT_EXCEEDED event emission with retry_after.
- Cache safety and budget guard preservation on rate-limit failures.
- Non-rate-limit error distinction (no false rate limits on 401/404/500/budget).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

playground_dir = Path(__file__).parent.resolve()
if str(playground_dir) not in sys.path:
    sys.path.insert(0, str(playground_dir))

import main as playground  # noqa: E402
from governance import (  # noqa: E402
    AdaptiveBackoffPolicy,
    BudgetExceededError,
    CircuitState,
    circuit_registry,
    extract_retry_after,
    is_rate_limit_error,
)

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
    crew.usage_metrics = None
    crew.kickoff.return_value = "Mocked offline LLM response"

    build_crew_calls = []

    def fake_build_crew(**inputs):
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
# 1. Rate-Limit Error Classification Tests
# ===========================================================================


def test_is_rate_limit_error_status_codes():
    """Status code 429 is classified as rate limit; other 4xx/5xx are not."""
    # 429 status attribute
    assert is_rate_limit_error(SimpleNamespace(status_code=429)) is True

    # 429 response.status_code
    res_mock = SimpleNamespace(status_code=429)
    assert is_rate_limit_error(SimpleNamespace(response=res_mock)) is True

    # 429 code attribute
    assert is_rate_limit_error(SimpleNamespace(code=429)) is True

    # Non-429 client errors must return False
    for code in (400, 401, 403, 404, 422):
        assert is_rate_limit_error(SimpleNamespace(status_code=code)) is False

    # Generic 500 without rate limit text returns False
    assert is_rate_limit_error(SimpleNamespace(status_code=500)) is False


def test_is_rate_limit_error_message_and_types():
    """Exception types and messages containing rate-limit indicators are recognized."""

    class CustomRateLimitError(Exception):
        pass

    assert is_rate_limit_error(CustomRateLimitError("Quota exceeded")) is True
    assert is_rate_limit_error(RuntimeError("429 Too Many Requests")) is True
    assert is_rate_limit_error(RuntimeError("Rate limit reached for model")) is True
    assert is_rate_limit_error(RuntimeError("TPM limit exceeded")) is True
    assert is_rate_limit_error(RuntimeError("Resource exhausted")) is True

    # Non-rate-limit errors
    assert is_rate_limit_error(RuntimeError("Database connection lost")) is False
    assert is_rate_limit_error(ValueError("Invalid syntax")) is False
    assert is_rate_limit_error(BudgetExceededError("r1", 100, 50)) is False
    assert is_rate_limit_error(None) is False


def test_is_rate_limit_error_walks_cause_chain():
    """Walks __cause__ and __context__ to detect wrapped rate limit errors."""
    inner = RuntimeError("Rate limit reached. Try again later.")
    outer = Exception("Outer task failed")
    outer.__cause__ = inner
    assert is_rate_limit_error(outer) is True


# ===========================================================================
# 2. Retry-After Extraction Tests
# ===========================================================================


def test_extract_retry_after_direct_attribute():
    """Extracts numeric or string retry_after attribute."""
    assert extract_retry_after(SimpleNamespace(retry_after=5.5)) == 5.5
    assert extract_retry_after(SimpleNamespace(retry_after="12.0")) == 12.0
    assert extract_retry_after(SimpleNamespace(retry_after=0)) is None
    assert extract_retry_after(SimpleNamespace(retry_after=-1)) is None


def test_extract_retry_after_headers():
    """Extracts Retry-After header from response or exception headers."""
    exc = SimpleNamespace(response=SimpleNamespace(headers={"Retry-After": "8.5"}))
    assert extract_retry_after(exc) == 8.5

    exc_lower = SimpleNamespace(headers={"retry-after": "15"})
    assert extract_retry_after(exc_lower) == 15.0


def test_extract_retry_after_message_regex():
    """Extracts retry seconds from common provider message patterns."""
    assert (
        extract_retry_after(
            RuntimeError("Rate limit exceeded. Please try again in 4.2s.")
        )
        == 4.2
    )
    assert (
        extract_retry_after(RuntimeError("Too Many Requests: retry after 20 seconds"))
        == 20.0
    )
    assert extract_retry_after(RuntimeError("RateLimitError (wait: 6s)")) == 6.0
    assert extract_retry_after(RuntimeError("Unrelated error without timing")) is None


def test_extract_retry_after_clamping():
    """Clamps extracted values to maximum reasonable limit (3600.0s)."""
    assert extract_retry_after(SimpleNamespace(retry_after=999999.0)) == 3600.0


# ===========================================================================
# 3. AdaptiveBackoffPolicy Tests
# ===========================================================================


def test_adaptive_backoff_exponential_scaling_no_jitter():
    """Exponential delay scales deterministically when jitter=False."""
    policy = AdaptiveBackoffPolicy(base_delay=0.5, max_delay=10.0, jitter=False)
    assert policy.compute_delay(attempt=0) == 0.5
    assert policy.compute_delay(attempt=1) == 1.0
    assert policy.compute_delay(attempt=2) == 2.0
    assert policy.compute_delay(attempt=3) == 4.0
    assert policy.compute_delay(attempt=4) == 8.0
    assert policy.compute_delay(attempt=5) == 10.0  # Clamped to max_delay


def test_adaptive_backoff_jitter_bounds():
    """Full jitter stays strictly within [0, ceiling]."""
    policy = AdaptiveBackoffPolicy(base_delay=1.0, max_delay=10.0, jitter=True)

    # Using deterministic mock random function
    def mock_rand(low: float, high: float) -> float:
        return high * 0.75

    delay0 = policy.compute_delay(attempt=0, rand_func=mock_rand)
    assert delay0 == pytest.approx(0.75, abs=0.01)

    delay2 = policy.compute_delay(attempt=2, rand_func=mock_rand)
    assert delay2 == pytest.approx(3.0, abs=0.01)  # ceiling is 4.0 -> 4.0 * 0.75 = 3.0


def test_adaptive_backoff_respects_retry_after():
    """When retry_after is provided, delay respects upstream duration clamped to max_delay."""
    policy = AdaptiveBackoffPolicy(base_delay=0.5, max_delay=10.0, jitter=False)
    assert policy.compute_delay(attempt=1, retry_after=6.5) == 6.5
    assert (
        policy.compute_delay(attempt=1, retry_after=25.0) == 10.0
    )  # Capped at max_delay


def test_adaptive_backoff_environment_overrides():
    """Reads configuration from environment variables."""
    env = {
        "PLAYGROUND_BACKOFF_BASE_SECONDS": "1.5",
        "PLAYGROUND_BACKOFF_MAX_SECONDS": "20.0",
        "PLAYGROUND_BACKOFF_MAX_RETRIES": "4",
    }
    with patch.dict(os.environ, env, clear=True):
        policy = AdaptiveBackoffPolicy()
        assert policy.base_delay == 1.5
        assert policy.max_delay == 20.0
        assert policy.max_retries == 4


# ===========================================================================
# 4. Adaptive Circuit Breaker Cooldown Interaction Tests
# ===========================================================================


def test_circuit_breaker_adaptive_cooldown_override():
    """Breaker dynamically extends cooldown when provider reports larger Retry-After."""
    cb = circuit_registry.get_breaker("primary")
    cb.cooldown_seconds = 30.0

    # Trip the circuit with a 45s Retry-After override
    for _ in range(3):
        cb.record_failure(
            RuntimeError("429 Rate Limit"), now=100.0, cooldown_override=45.0
        )

    assert cb.state == CircuitState.OPEN
    # At t=135.0 (35s elapsed, > default 30s but < override 45s): must remain OPEN!
    assert cb.get_state(now=135.0) == CircuitState.OPEN
    assert cb.get_cooldown_remaining(now=135.0) == pytest.approx(10.0, abs=0.1)

    # At t=146.0 (46s elapsed, >= override 45s): transitions to HALF_OPEN
    assert cb.get_state(now=146.0) == CircuitState.HALF_OPEN


def test_circuit_breaker_success_resets_cooldown_override():
    """Successful probe resets active cooldown back to default."""
    cb = circuit_registry.get_breaker("primary")
    cb.cooldown_seconds = 30.0

    cb.record_failure(RuntimeError("429 Rate Limit"), now=100.0, cooldown_override=60.0)
    for _ in range(2):
        cb.record_failure(
            RuntimeError("429 Rate Limit"), now=100.0, cooldown_override=60.0
        )

    assert cb._active_cooldown_seconds == 60.0

    # Probe recovery at t=161.0
    allowed, state = cb.can_execute(now=161.0)
    assert allowed is True
    assert state == CircuitState.HALF_OPEN

    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb._active_cooldown_seconds == 30.0


# ===========================================================================
# 5. /run Rate-Limit & Backoff Integration Tests
# ===========================================================================


def test_run_primary_rate_limit_failover_applies_backoff(mock_execution):
    """Primary 429 triggers adaptive backoff before executing fallback."""
    slept_durations = []

    def mock_sleep(seconds):
        slept_durations.append(seconds)

    primary_attempt = True

    def fake_build_crew(**inputs):
        nonlocal primary_attempt
        active = getattr(playground._thread_local, "active_provider", None)
        mock_execution.build_crew_calls.append(active)
        c = MagicMock()
        if primary_attempt:
            primary_attempt = False
            # Rate limit with 2.5s Retry-After in error message
            c.kickoff.side_effect = RuntimeError(
                "429 Too Many Requests (Retry-After: 2.5)"
            )
        else:
            c.kickoff.return_value = "Fallback succeeded"
        return c

    mock_execution.module.build_crew.side_effect = fake_build_crew

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(playground, "_backoff_sleep", side_effect=mock_sleep),
        TestClient(playground.app) as client,
    ):
        res = client.post(
            "/run", json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True}
        )
        assert res.status_code == 200
        assert res.json()["output"] == "Fallback succeeded"

        # Verify backoff delay was applied before fallback
        assert len(slept_durations) == 1
        assert slept_durations[0] >= 2.5


def test_run_rate_limit_exhausted_returns_429(mock_execution):
    """When fallback also hits 429, returns HTTP 429 with Retry-After header."""
    primary_attempt = True

    def fake_build_crew(**inputs):
        nonlocal primary_attempt
        c = MagicMock()
        if primary_attempt:
            primary_attempt = False
            c.kickoff.side_effect = RuntimeError("429 Too Many Requests")
        else:
            # Fallback also rate-limited with Retry-After 8
            err = RuntimeError("Fallback 429 rate limit")
            err.retry_after = 8.0
            c.kickoff.side_effect = err
        return c

    mock_execution.module.build_crew.side_effect = fake_build_crew

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
    }
    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(playground, "_backoff_sleep", return_value=None),
        TestClient(playground.app) as client,
    ):
        res = client.post(
            "/run", json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True}
        )
        assert res.status_code == 429
        assert "Provider rate limit exceeded" in res.json()["detail"]
        assert res.headers.get("Retry-After") == "8"


def test_run_primary_rate_limit_without_fallback_returns_429(mock_execution):
    """Primary 429 without configured fallback returns HTTP 429 instead of 500."""
    err = RuntimeError("429 Too Many Requests (Please try again in 7.0s)")
    mock_execution.crew.kickoff.side_effect = err

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run", json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True}
        )
        assert res.status_code == 429
        assert "Provider rate limit exceeded" in res.json()["detail"]
        assert res.headers.get("Retry-After") == "7"


# ===========================================================================
# 6. Streaming (/run/stream) Rate-Limit Integration Tests
# ===========================================================================


def test_stream_rate_limit_emits_rate_limit_exceeded_event(mock_execution):
    """Stream execution hitting 429 emits RATE_LIMIT_EXCEEDED error event with retry_after."""
    err = RuntimeError("Rate limit reached. Please try again in 5.0s.")
    mock_execution.crew.kickoff.side_effect = err

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run/stream",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )
        assert res.status_code == 200
        raw_events = [
            line.replace("data: ", "").strip()
            for line in res.text.split("\n\n")
            if line.strip()
        ]
        events = [json.loads(line) for line in raw_events]

        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert error_events[0].get("code") == "RATE_LIMIT_EXCEEDED"
        assert error_events[0].get("retry_after") == 5.0
        assert "Provider rate limit exceeded" in error_events[0].get("error", "")

        # Must not be cached
        assert playground.response_cache.get("faq-bot", INPUTS) is None
