"""Deterministic unit and integration tests for playground governance (#279).

Covers:
- CircuitBreaker states (CLOSED, OPEN, HALF_OPEN) and transitions.
- Exclusive probe locking in HALF_OPEN state.
- Cooldown and monotonic timing with time-travel overrides.
- Failure classification (trippable vs non-trippable).
- Multi-threaded concurrency safety.
- Provider isolation in CircuitBreakerRegistry.
- TokenBudgetGuard actual and estimated token accounting and enforcement.
- Boundary conditions and disabled modes.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from governance import (
    BudgetExceededError,
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
    TokenBudgetGuard,
    circuit_registry,
    is_trippable_error,
)


@pytest.fixture(autouse=True)
def clean_governance_state():
    """Ensure clean registry state before and after each test."""
    circuit_registry.reset_all()
    yield
    circuit_registry.reset_all()


# ===========================================================================
# 1. Failure Classification Tests
# ===========================================================================


def test_is_trippable_error_status_codes():
    """Verify standard HTTP status codes are classified correctly."""

    class MockHTTPError(Exception):
        def __init__(self, code):
            self.status_code = code

    # Server errors & rate limits trip the breaker
    assert is_trippable_error(MockHTTPError(429)) is True
    assert is_trippable_error(MockHTTPError(500)) is True
    assert is_trippable_error(MockHTTPError(502)) is True
    assert is_trippable_error(MockHTTPError(503)) is True
    assert is_trippable_error(MockHTTPError(504)) is True

    # Client errors do not trip the breaker
    assert is_trippable_error(MockHTTPError(400)) is False
    assert is_trippable_error(MockHTTPError(401)) is False
    assert is_trippable_error(MockHTTPError(403)) is False
    assert is_trippable_error(MockHTTPError(404)) is False


def test_is_trippable_error_substrings_and_types():
    """Verify type names, message indicators, and exception chains."""
    assert is_trippable_error(RuntimeError("Rate limit reached")) is True
    assert is_trippable_error(TimeoutError("Connection timed out")) is True
    assert is_trippable_error(ConnectionResetError("Socket reset by peer")) is True
    assert is_trippable_error(Exception("503 Service Unavailable")) is True

    # Explicitly non-trippable
    assert is_trippable_error(ValueError("Invalid recipe parameter")) is False
    assert is_trippable_error(KeyError("missing_field")) is False
    assert is_trippable_error(InterruptedError("Client disconnected")) is False
    assert (
        is_trippable_error(
            BudgetExceededError("run-1", accumulated_tokens=100, limit=50)
        )
        is False
    )
    assert is_trippable_error(None) is False


def test_is_trippable_error_walks_cause_chain():
    """Verify chained exceptions are inspected recursively."""
    inner = ConnectionRefusedError("LLM port unavailable")
    outer = RuntimeError("Failed during crew kickoff")
    outer.__cause__ = inner

    assert is_trippable_error(outer) is True


# ===========================================================================
# 2. CircuitBreaker State Machine & Transition Tests
# ===========================================================================


def test_circuit_breaker_initial_state_closed():
    """A newly created breaker starts in CLOSED state and permits calls."""
    cb = CircuitBreaker(provider="primary", failure_threshold=3, cooldown_seconds=30.0)
    assert cb.state == CircuitState.CLOSED
    allowed, state = cb.can_execute(now=100.0)
    assert allowed is True
    assert state == CircuitState.CLOSED
    assert cb.get_cooldown_remaining(now=100.0) == 0.0


def test_circuit_breaker_trips_to_open_after_threshold():
    """Consecutive trippable failures equal to threshold transition state to OPEN."""
    cb = CircuitBreaker(provider="primary", failure_threshold=3, cooldown_seconds=30.0)

    # 1st failure: remains CLOSED
    tripped = cb.record_failure(RuntimeError("503 Service Unavailable"), now=100.0)
    assert tripped is False
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute(now=100.0)[0] is True

    # 2nd failure: remains CLOSED
    tripped = cb.record_failure(RuntimeError("503 Service Unavailable"), now=101.0)
    assert tripped is False
    assert cb.state == CircuitState.CLOSED

    # Non-trippable error (e.g. ValueError): does not count towards threshold
    tripped = cb.record_failure(ValueError("Bad input"), now=102.0)
    assert tripped is False
    assert cb.state == CircuitState.CLOSED

    # 3rd failure: reaches threshold -> trips to OPEN
    tripped = cb.record_failure(RuntimeError("Rate limit reached"), now=103.0)
    assert tripped is True
    assert cb.state == CircuitState.OPEN

    # In OPEN state: calls are rejected immediately
    allowed, state = cb.can_execute(now=103.5)
    assert allowed is False
    assert state == CircuitState.OPEN
    assert cb.get_cooldown_remaining(now=103.5) == 29.5


def test_circuit_breaker_success_resets_failure_counter():
    """A success in CLOSED state resets consecutive failures back to 0."""
    cb = CircuitBreaker(provider="primary", failure_threshold=3, cooldown_seconds=30.0)

    cb.record_failure(RuntimeError("503 error"), now=100.0)
    cb.record_failure(RuntimeError("503 error"), now=101.0)
    assert cb._consecutive_failures == 2

    # Intervening success resets count
    cb.record_success()
    assert cb._consecutive_failures == 0

    # Next failure is 1/3, not 3/3
    tripped = cb.record_failure(RuntimeError("503 error"), now=102.0)
    assert tripped is False
    assert cb.state == CircuitState.CLOSED


def test_circuit_breaker_cooldown_and_half_open_recovery():
    """After cooldown, breaker enters HALF_OPEN and tests recovery with a probe."""
    cb = CircuitBreaker(provider="primary", failure_threshold=2, cooldown_seconds=10.0)

    # Trip the circuit at t=100.0
    cb.record_failure(RuntimeError("503 error"), now=100.0)
    cb.record_failure(RuntimeError("503 error"), now=100.0)
    assert cb.state == CircuitState.OPEN

    # At t=105.0: cooldown still active (5s remaining)
    allowed, state = cb.can_execute(now=105.0)
    assert allowed is False
    assert state == CircuitState.OPEN
    assert cb.get_cooldown_remaining(now=105.0) == 5.0

    # At t=110.0: cooldown expires -> transitions to HALF_OPEN, grants probe
    allowed, state = cb.can_execute(now=110.0)
    assert allowed is True
    assert state == CircuitState.HALF_OPEN

    # Probe succeeds -> transitions to CLOSED
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute(now=110.1)[0] is True


def test_circuit_breaker_half_open_probe_failure_reopens_circuit():
    """If the probe in HALF_OPEN fails, circuit immediately reverts to OPEN."""
    cb = CircuitBreaker(provider="primary", failure_threshold=2, cooldown_seconds=10.0)

    # Trip circuit at t=100.0
    cb.record_failure(RuntimeError("503 error"), now=100.0)
    cb.record_failure(RuntimeError("503 error"), now=100.0)
    assert cb.state == CircuitState.OPEN

    # Advance to t=110.0: acquire probe permit
    allowed, state = cb.can_execute(now=110.0)
    assert allowed is True
    assert state == CircuitState.HALF_OPEN

    # Probe fails at t=110.5
    tripped = cb.record_failure(RuntimeError("Still overloaded"), now=110.5)
    assert tripped is True
    assert cb.state == CircuitState.OPEN

    # Cooldown is reset starting from t=110.5
    allowed, state = cb.can_execute(now=112.0)
    assert allowed is False
    assert state == CircuitState.OPEN
    assert cb.get_cooldown_remaining(now=112.0) == 8.5


def test_circuit_breaker_half_open_probe_exclusivity():
    """Strictly one thread gets the probe permit in HALF_OPEN; others are denied."""
    cb = CircuitBreaker(provider="primary", failure_threshold=1, cooldown_seconds=10.0)
    cb.record_failure(RuntimeError("503 error"), now=100.0)
    assert cb.state == CircuitState.OPEN

    # Thread 1 requests at t=110.0 -> gets probe permit
    allowed1, state1 = cb.can_execute(now=110.0)
    assert allowed1 is True
    assert state1 == CircuitState.HALF_OPEN

    # Thread 2 requests while Thread 1's probe is in flight -> denied probe
    allowed2, state2 = cb.can_execute(now=110.1)
    assert allowed2 is False
    assert state2 == CircuitState.HALF_OPEN

    # Thread 3 also denied
    allowed3, state3 = cb.can_execute(now=110.2)
    assert allowed3 is False
    assert state3 == CircuitState.HALF_OPEN


def test_circuit_breaker_disabled_mode():
    """When disabled, can_execute always returns True regardless of failures."""
    cb = CircuitBreaker(provider="primary", enabled=False)
    for _ in range(10):
        cb.record_failure(RuntimeError("503 error"))

    allowed, state = cb.can_execute()
    assert allowed is True
    assert state == CircuitState.CLOSED


# ===========================================================================
# 3. CircuitBreakerRegistry Tests
# ===========================================================================


def test_registry_provider_isolation():
    """Primary and fallback breakers maintain completely isolated state."""
    registry = CircuitBreakerRegistry()
    primary = registry.get_breaker("primary")
    fallback = registry.get_breaker("fallback")

    assert primary is not fallback

    # Trip primary
    primary.record_failure(RuntimeError("503 primary down"))
    primary.record_failure(RuntimeError("503 primary down"))
    primary.record_failure(RuntimeError("503 primary down"))

    assert primary.state == CircuitState.OPEN
    assert primary.can_execute()[0] is False

    # Fallback remains completely healthy in CLOSED state
    assert fallback.state == CircuitState.CLOSED
    assert fallback.can_execute()[0] is True


def test_registry_singleton_per_provider():
    """Calls to get_breaker for the same provider return the identical instance."""
    registry = CircuitBreakerRegistry()
    b1 = registry.get_breaker("primary")
    b2 = registry.get_breaker("PRIMARY ")
    assert b1 is b2


# ===========================================================================
# 4. TokenBudgetGuard Tests
# ===========================================================================


def test_token_budget_guard_within_limit():
    """Token accumulation within limit permits execution."""
    guard = TokenBudgetGuard(run_id="run-1", max_tokens=1000, warning_ratio=0.8)

    # 100 tokens: no warning, no error
    warn, total = guard.add_actual_tokens(100)
    assert warn is False
    assert total == 100
    assert guard.is_estimated is False


def test_token_budget_guard_warning_threshold():
    """At 80% utilization, a warning flag is triggered exactly once."""
    guard = TokenBudgetGuard(run_id="run-1", max_tokens=1000, warning_ratio=0.8)

    warn, total = guard.add_actual_tokens(799)
    assert warn is False

    # Cross 800 (80%)
    warn, total = guard.add_actual_tokens(10)
    assert warn is True
    assert total == 809

    # Further tokens do not re-emit warning
    warn, total = guard.add_actual_tokens(50)
    assert warn is False
    assert total == 859


def test_token_budget_guard_breach_raises_error():
    """Reaching or exceeding the ceiling raises BudgetExceededError."""
    guard = TokenBudgetGuard(run_id="run-test", max_tokens=500)

    guard.add_actual_tokens(400)
    with pytest.raises(BudgetExceededError) as exc_info:
        guard.add_actual_tokens(150)

    err = exc_info.value
    assert err.run_id == "run-test"
    assert err.accumulated_tokens == 550
    assert err.limit == 500
    assert err.is_estimated is False
    assert "exceeded token budget: 550" in str(err)


def test_token_budget_guard_step_text_estimation():
    """Step text is estimated using ~4 chars per token and flagged as estimated."""
    guard = TokenBudgetGuard(run_id="run-est", max_tokens=100)

    # 100 chars -> 25 tokens
    text = "a" * 100
    warn, total = guard.add_step_text(text)
    assert warn is False
    assert total == 25
    assert guard.is_estimated is True

    # Another 400 chars -> 100 tokens -> total 125 >= 100 -> breach!
    with pytest.raises(BudgetExceededError) as exc_info:
        guard.add_step_text("b" * 400)

    assert exc_info.value.is_estimated is True
    assert "estimated" in str(exc_info.value)


def test_token_budget_guard_set_final_usage():
    """Setting final actual usage checks the budget ceiling accurately."""
    guard = TokenBudgetGuard(run_id="run-final", max_tokens=1000)
    guard.add_step_text("short step")  # Estimated tokens

    # Final actual usage is 800 -> within limit, marks exact
    guard.set_final_usage(800)
    assert guard.accumulated_tokens == 800
    assert guard.is_estimated is False

    # Another guard with actual usage exceeding limit raises error
    guard2 = TokenBudgetGuard(run_id="run-over", max_tokens=1000)
    with pytest.raises(BudgetExceededError) as exc_info:
        guard2.set_final_usage(1200)
    assert exc_info.value.accumulated_tokens == 1200


def test_token_budget_guard_disabled_when_zero():
    """max_tokens=0 disables budget enforcement."""
    guard = TokenBudgetGuard(run_id="run-unlimited", max_tokens=0)
    assert guard.enabled is False

    warn, total = guard.add_actual_tokens(1_000_000)
    assert warn is False
    assert total == 0  # not tracked when disabled


# ===========================================================================
# 5. Multi-Threaded Concurrency Tests
# ===========================================================================


def test_circuit_breaker_concurrent_stress():
    """10 concurrent threads updating circuit state do not deadlock or corrupt counts."""
    cb = CircuitBreaker(provider="primary", failure_threshold=50, cooldown_seconds=1.0)
    errors = []

    def worker(worker_id: int):
        try:
            for _ in range(50):
                cb.can_execute()
                cb.record_failure(RuntimeError("503 error"))
                cb.record_success()
        except Exception as e:  # noqa: BLE001
            errors.append(e)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker, i) for i in range(10)]
        for f in futures:
            f.result()

    assert len(errors) == 0
    assert cb._total_failures == 500
    assert cb._total_successes == 500


def test_token_budget_concurrent_accumulation():
    """Multiple threads adding usage concurrently maintain exact atomic totals."""
    guard = TokenBudgetGuard(run_id="concurrent-run", max_tokens=100_000)

    def worker():
        for _ in range(100):
            guard.add_actual_tokens(10)

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # 10 threads * 100 iterations * 10 tokens = 10,000 tokens
    assert guard.accumulated_tokens == 10_000
