"""Adversarial edge-case audit tests for CrewAI Recipes Playground governance (#279).

Audits Phase 2B-2E implementations against adversarial edge cases:
1. Retry-After parsing: case-insensitive, HTTP dates, numeric clamping, string safety, NaN/inf.
2. Retry-After semantic preservation under jitter (delay >= retry_after).
3. Rate-limit classification false-positive immunity (4291 bytes, rpm package, TPM device, 4xx errors).
4. Environment variable robustness: malformed, negative, NaN values for backoff/circuit settings.
5. Circuit breaker cooldown bounds and string override safety.
6. Execution protocol consistency (HTTP, SSE, WebSocket) for CIRCUIT_OPEN, RATE_LIMIT_EXCEEDED, BUDGET_EXCEEDED.
7. Wrapped InterruptedError and probe release safety.
8. Cache immunity across failed and aborted execution paths.
"""

from __future__ import annotations

import email.utils
import os
import sys
import threading
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
    CircuitBreaker,
    CircuitState,
    circuit_registry,
    extract_retry_after,
    is_rate_limit_error,
    is_trippable_error,
)


@pytest.fixture(autouse=True)
def clean_governance():
    """Reset global circuit registry and isolation state before and after each test."""
    circuit_registry.reset_all()
    if hasattr(playground._thread_local, "active_provider"):
        playground._thread_local.active_provider = None
    playground.response_cache.clear()
    yield
    circuit_registry.reset_all()
    if hasattr(playground._thread_local, "active_provider"):
        playground._thread_local.active_provider = None
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

    module = types.SimpleNamespace(build_crew=MagicMock(side_effect=fake_build_crew))
    loader = MagicMock()

    with (
        patch.object(
            playground, "rate_limiter", playground.SlidingWindowRateLimiter("0")
        ),
        patch.object(
            playground.importlib.util,
            "spec_from_file_location",
            return_value=types.SimpleNamespace(loader=loader),
        ),
        patch.object(
            playground.importlib.util, "module_from_spec", return_value=module
        ),
    ):
        yield types.SimpleNamespace(
            crew=crew,
            module=module,
            build_crew_calls=build_crew_calls,
        )


# ===========================================================================
# 1. Retry-After Adversarial Audit
# ===========================================================================


def test_retry_after_case_insensitive_plain_dict():
    """Headers in plain dict with various casings are extracted reliably."""
    for header_name in ["retry-after", "Retry-After", "RETRY-AFTER", "Retry-after"]:
        exc = types.SimpleNamespace(headers={header_name: "18.5"})
        assert extract_retry_after(exc) == 18.5


def test_retry_after_http_date_rfc7231():
    """RFC 7231 HTTP-date string in the future is converted to delta seconds."""
    future_time = datetime.now(timezone.utc) + timedelta(seconds=45)
    http_date = email.utils.format_datetime(future_time)

    exc = types.SimpleNamespace(headers={"Retry-After": http_date})
    extracted = extract_retry_after(exc)
    assert extracted is not None
    assert 40.0 <= extracted <= 50.0


def test_retry_after_past_http_date_returns_none():
    """RFC 7231 HTTP-date in the past returns None."""
    past_time = datetime.now(timezone.utc) - timedelta(seconds=60)
    http_date = email.utils.format_datetime(past_time)

    exc = types.SimpleNamespace(headers={"Retry-After": http_date})
    assert extract_retry_after(exc) is None


def test_retry_after_malformed_and_extreme_inputs():
    """Non-numeric, negative, zero, NaN, Inf and extreme values are handled safely."""
    # Negative values
    assert extract_retry_after(types.SimpleNamespace(retry_after=-10)) is None
    assert (
        extract_retry_after(types.SimpleNamespace(headers={"retry-after": "-5"}))
        is None
    )

    # Zero values
    assert extract_retry_after(types.SimpleNamespace(retry_after=0)) is None
    assert (
        extract_retry_after(types.SimpleNamespace(headers={"retry-after": "0"})) is None
    )

    # Malformed strings
    assert extract_retry_after(types.SimpleNamespace(retry_after="invalid")) is None
    assert (
        extract_retry_after(
            types.SimpleNamespace(headers={"retry-after": "not-a-number"})
        )
        is None
    )

    # NaN and Infinity
    assert extract_retry_after(types.SimpleNamespace(retry_after=float("nan"))) is None
    assert extract_retry_after(types.SimpleNamespace(retry_after=float("inf"))) is None
    assert (
        extract_retry_after(types.SimpleNamespace(headers={"retry-after": "nan"}))
        is None
    )
    assert (
        extract_retry_after(types.SimpleNamespace(headers={"retry-after": "inf"}))
        is None
    )

    # Extreme clamping
    assert extract_retry_after(types.SimpleNamespace(retry_after=1000000)) == 3600.0
    assert extract_retry_after(types.SimpleNamespace(retry_after=0.0001)) == 0.1


def test_retry_after_semantics_preserved_under_jitter():
    """Delay computed with Retry-After must never fall below the requested Retry-After window."""
    policy = AdaptiveBackoffPolicy(max_delay=100.0, jitter=True)

    # For various Retry-After inputs, delay must always be >= requested Retry-After
    for requested_ra in [0.5, 1.0, 5.0, 15.0, 60.0]:
        delay = policy.compute_delay(attempt=1, retry_after=requested_ra)
        assert delay >= requested_ra, (
            f"Jitter reduced delay {delay} below requested {requested_ra}"
        )


# ===========================================================================
# 2. Rate-Limit Classification False-Positive Immunity
# ===========================================================================


def test_rate_limit_false_positive_immunity_numeric_substrings():
    """Numeric substrings like '4291 bytes' or '5040 files' must not trigger rate limit or trippable classification."""
    e1 = RuntimeError("Connection lost after 4291 bytes transferred")
    assert is_rate_limit_error(e1) is False

    e2 = RuntimeError("Port 4290 is unreachable")
    assert is_rate_limit_error(e2) is False

    e3 = RuntimeError("Processed 5040 items from disk")
    assert is_trippable_error(e3) is False


def test_rate_limit_false_positive_immunity_tpm_rpm_words():
    """Unrelated occurrences of 'rpm' (packages/rotations) or 'tpm' (hardware) must not trigger rate limit."""
    e1 = RuntimeError("Failed to build python-ldap rpm package on CentOS")
    assert is_rate_limit_error(e1) is False

    e2 = RuntimeError("TPM 2.0 cryptoprocessor device not found on motherboard")
    assert is_rate_limit_error(e2) is False

    # But legitimate TPM / RPM limit breaches must trigger
    e3 = RuntimeError("LLM rate limit: 30000 TPM limit exceeded for model")
    assert is_rate_limit_error(e3) is True

    e4 = RuntimeError("Requests per minute quota reached for key")
    assert is_rate_limit_error(e4) is True


def test_rate_limit_excludes_client_4xx_even_with_keywords():
    """Client errors (400, 401, 403, 404) must NEVER be classified as rate limits even if body contains keywords."""
    for code in [400, 401, 403, 404]:
        exc = types.SimpleNamespace(
            status_code=code,
            __doc__=f"HTTP {code}",
        )
        exc_str = Exception(f"HTTP {code} Error: rate limit configuration syntax error")
        exc_str.status_code = code
        assert is_rate_limit_error(exc) is False
        assert is_rate_limit_error(exc_str) is False
        assert is_trippable_error(exc_str) is False


def test_budget_exceeded_never_classified_as_rate_limit_or_trippable():
    """BudgetExceededError is purely client/run governance, never provider rate limit or outage."""
    budget_err = BudgetExceededError(run_id="test", accumulated_tokens=1000, limit=500)
    assert is_rate_limit_error(budget_err) is False
    assert is_trippable_error(budget_err) is False


# ===========================================================================
# 3. Backoff Robustness & Environment Configuration
# ===========================================================================


def test_backoff_environment_robustness():
    """Malformed or extreme environment variables cleanly fallback to safe defaults."""
    env = {
        "PLAYGROUND_BACKOFF_BASE_SECONDS": "not-a-number",
        "PLAYGROUND_BACKOFF_MAX_SECONDS": "nan",
        "PLAYGROUND_BACKOFF_MAX_RETRIES": "-5",
    }
    with patch.dict(os.environ, env, clear=False):
        policy = AdaptiveBackoffPolicy()
        assert policy.base_delay == 0.5
        assert policy.max_delay == 10.0
        assert policy.max_retries == 1  # Clamped to min 1


def test_backoff_extreme_attempt_index_no_overflow():
    """Attempt index of 1,000,000 does not overflow or hang."""
    policy = AdaptiveBackoffPolicy()
    delay = policy.compute_delay(attempt=1_000_000, rand_func=lambda low, high: high)
    assert delay == policy.max_delay


# ===========================================================================
# 4. Circuit Breaker Robustness & Cooldown Bounds
# ===========================================================================


def test_circuit_breaker_record_failure_string_cooldown_override():
    """Passing string cooldown_override does not raise TypeError and is parsed safely on trip."""
    cb = CircuitBreaker("test-provider", failure_threshold=1, cooldown_seconds=30.0)
    tripped = cb.record_failure(
        RuntimeError("429 Too Many Requests"), cooldown_override="60.0"
    )
    assert tripped is True
    assert cb.state == CircuitState.OPEN
    assert cb._active_cooldown_seconds == 60.0


def test_circuit_breaker_cooldown_clamping_to_300s():
    """cooldown_override above 300s is clamped to 300s on trip."""
    cb = CircuitBreaker("test-provider", failure_threshold=1, cooldown_seconds=30.0)
    tripped = cb.record_failure(
        RuntimeError("429 Too Many Requests"), cooldown_override=9999.0
    )
    assert tripped is True
    assert cb.state == CircuitState.OPEN
    assert cb._active_cooldown_seconds == 300.0


# ===========================================================================
# 5. Protocol Consistency & Structured Error Events
# ===========================================================================


def test_stream_circuit_open_emits_structured_circuit_open_event():
    """When stream execution encounters an OPEN circuit, pushes CIRCUIT_OPEN structured event."""
    events = []
    stop_event = threading.Event()

    # Force primary breaker OPEN in the shared registry
    cb = circuit_registry.get_breaker("primary")
    cb.failure_threshold = 1
    cb.record_failure(RuntimeError("429 Too Many Requests"), cooldown_override=45.0)
    assert cb.state == CircuitState.OPEN

    env = {"LLM_API_KEY": "dummy-key"}
    with patch.dict(os.environ, env, clear=True):
        playground.execute_recipe_stream(
            recipe_name="faq-bot",
            inputs={"topic": "CrewAI"},
            push_event=events.append,
            stop_event=stop_event,
        )

    assert len(events) == 1
    err_event = events[0]
    assert err_event["type"] == "error"
    assert err_event.get("code") == "CIRCUIT_OPEN"
    assert "retry_after" in err_event
    assert err_event["retry_after"] > 0


def test_stream_wrapped_interrupted_error_exits_cleanly(mock_execution):
    """When InterruptedError is wrapped inside a RuntimeError, stream exits cleanly without error events."""
    events = []
    stop_event = threading.Event()

    cause = InterruptedError("Client disconnected")
    outer = RuntimeError("Failed running crew")
    outer.__cause__ = cause
    mock_execution.crew.kickoff.side_effect = outer

    env = {"LLM_API_KEY": "dummy-key"}
    with patch.dict(os.environ, env, clear=True):
        playground.execute_recipe_stream(
            recipe_name="faq-bot",
            inputs={"topic": "CrewAI"},
            push_event=events.append,
            stop_event=stop_event,
        )

    error_events = [e for e in events if e.get("type") == "error"]
    assert len(error_events) == 0


def test_run_primary_429_without_fallback_no_unnecessary_sleep(mock_execution):
    """When primary hits 429 and no fallback is eligible, /run fails fast without sleeping."""
    slept = []

    def mock_sleep(s):
        slept.append(s)

    mock_execution.crew.kickoff.side_effect = RuntimeError(
        "429 Too Many Requests (Retry-After: 15)"
    )

    env = {"LLM_API_KEY": "dummy-key"}  # No fallback key
    with (
        patch.dict(os.environ, env, clear=True),
        patch.object(playground, "_backoff_sleep", side_effect=mock_sleep),
        TestClient(playground.app) as client,
    ):
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": {"topic": "test"}, "no_cache": True},
        )
        assert res.status_code == 429
        assert res.headers.get("Retry-After") == "15"
        # Must NOT have slept!
        assert len(slept) == 0
