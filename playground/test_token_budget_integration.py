"""Deterministic offline integration tests for token budget governance (#279).

Tests:
- /run: Under-budget execution (200 OK, cached).
- /run: Mid-flight step estimation breach (429 Too Many Requests, uncached).
- /run: Post-kickoff actual usage reconciliation breach (429 Too Many Requests, uncached).
- /run: Disabled budget mode (PLAYGROUND_MAX_RUN_TOKENS=0).
- /run: In-flight failover with fallback budget breach (429).
- Cache safety: Breached responses are never cached; subsequent runs enforce budget.
- Stream (/run/stream): 80% warning emission, mid-flight breach error event, post-kickoff breach.
- WebSocket (/run/ws): Under-budget completion vs budget-breach error event.
- Concurrency & Isolation: Multiple concurrent runs with separate budgets without cross-talk.
- Circuit immunity: Budget breaches do NOT increment circuit breaker failure count.
"""

from __future__ import annotations

import json
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
# 1. HTTP /run Token Budget Enforcement Tests
# ===========================================================================


def test_run_under_budget_succeeds(mock_execution):
    """Execution within budget succeeds with 200 and caches result."""
    mock_execution.crew.usage_metrics = {"total_tokens": 1200}
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "5000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 200
        data = res.json()
        assert data["output"] == "Mocked offline LLM response"
        assert data["cached"] is False

        # Verify result was safely cached
        cached = playground.response_cache.get("faq-bot", INPUTS)
        assert cached == "Mocked offline LLM response"


def test_run_step_estimation_breach_returns_429(mock_execution):
    """Mid-flight step estimation exceeding max_tokens interrupts run with 429."""

    def fake_kickoff():
        step = SimpleNamespace(
            thought="A" * 800,  # 800 chars -> ~200 tokens
            text="",
            result="",
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Should not reach here"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "100",  # Limit is 100 tokens
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 429
        detail = res.json()["detail"]
        assert "exceeded token budget" in detail
        assert "200 estimated tokens accumulated" in detail
        assert "limit: 100" in detail

        # Verify uncached
        assert playground.response_cache.get("faq-bot", INPUTS) is None


def test_run_actual_tokens_post_kickoff_breach_returns_429(mock_execution):
    """Post-kickoff actual metrics exceeding limit raises 429 and bypasses cache."""
    mock_result = SimpleNamespace(
        token_usage={"total_tokens": 1500},
        __str__=lambda self: "Raw result text",
    )
    mock_execution.crew.kickoff.return_value = mock_result
    mock_execution.crew.usage_metrics = None

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "1000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 429
        detail = res.json()["detail"]
        assert "exceeded token budget" in detail
        assert "1500 tokens accumulated" in detail
        assert "limit: 1000" in detail

        # Verify uncached
        assert playground.response_cache.get("faq-bot", INPUTS) is None


def test_run_disabled_budget_allows_large_usage(mock_execution):
    """When PLAYGROUND_MAX_RUN_TOKENS=0, budget enforcement is disabled."""
    mock_execution.crew.usage_metrics = {"total_tokens": 999999}

    def fake_kickoff():
        step = SimpleNamespace(
            thought="Large step text " * 1000,
            text="",
            result="",
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Completed without limit"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "0",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 200
        assert res.json()["output"] == "Completed without limit"


# ===========================================================================
# 2. Cache Protection Tests
# ===========================================================================


def test_cache_safety_breached_run_does_not_poison_cache(mock_execution):
    """A breached run is not cached; subsequent valid run can succeed and cache."""
    # Run 1: Breached
    mock_execution.crew.usage_metrics = {"total_tokens": 3000}
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "2000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res1 = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res1.status_code == 429
        assert playground.response_cache.get("faq-bot", INPUTS) is None

        # Run 2: Within budget
        mock_execution.crew.usage_metrics = {"total_tokens": 500}
        res2 = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res2.status_code == 200
        assert res2.json()["cached"] is False
        assert (
            playground.response_cache.get("faq-bot", INPUTS)
            == "Mocked offline LLM response"
        )

        # Run 3: Subsequent request hits cache (bypasses LLM call)
        res3 = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res3.status_code == 200
        assert res3.json()["cached"] is True


# ===========================================================================
# 3. Failover Token Accounting Tests
# ===========================================================================


def test_failover_fallback_budget_breached(mock_execution):
    """When primary trips and fallback exceeds token budget, 429 is returned."""
    primary_call = True

    def fake_build_crew(**inputs):
        nonlocal primary_call
        active = getattr(playground._thread_local, "active_provider", None)
        mock_execution.build_crew_calls.append(active)
        c = MagicMock()
        if primary_call:
            primary_call = False
            c.kickoff.side_effect = RuntimeError("503 Service Unavailable")
        else:
            # Fallback breaches budget
            c.usage_metrics = {"total_tokens": 5000}
            c.kickoff.return_value = "Fallback output"
        return c

    mock_execution.module.build_crew.side_effect = fake_build_crew

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "2000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 429
        assert (
            "exceeded token budget: 5000 tokens accumulated (limit: 2000)"
            in res.json()["detail"]
        )


# ===========================================================================
# 4. SSE Stream (/run/stream) Token Budget Tests
# ===========================================================================


def test_stream_warning_at_80_percent(mock_execution):
    """Streaming emits token_budget_warning event when reaching warning ratio (default 80%)."""

    def fake_kickoff():
        # 1000 limit, warning ratio 0.8 -> threshold 800 tokens (3200 chars)
        step = SimpleNamespace(
            agent="Researcher",
            thought="W" * 3400,  # 3400 chars // 4 = 850 tokens >= 800
            tool=None,
            tool_input=None,
            result="Preliminary finding",
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Complete analysis"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "1000",
    }
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

        event_types = [e.get("type") for e in events]
        assert "start" in event_types
        assert "complete" in event_types

        # Check for governance warning event
        warning_events = [
            e
            for e in events
            if e.get("type") == "governance"
            and e.get("event") == "token_budget_warning"
        ]
        assert len(warning_events) == 1
        assert warning_events[0]["accumulated"] >= 800
        assert warning_events[0]["limit"] == 1000
        assert warning_events[0]["is_estimated"] is True


def test_stream_step_breach_emits_error_and_aborts(mock_execution):
    """Streaming mid-flight step breach emits error event with BUDGET_EXCEEDED and closes."""

    def fake_kickoff():
        step = SimpleNamespace(
            agent="Researcher",
            thought="Massive thought " * 200,  # > 400 tokens
            tool=None,
            tool_input=None,
            result=None,
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Unreached"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "100",
    }
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

        # Must have start and error; must NOT have complete
        assert any(e.get("type") == "start" for e in events)
        assert not any(e.get("type") == "complete" for e in events)

        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert error_events[0].get("code") == "BUDGET_EXCEEDED"
        assert "exceeded token budget" in error_events[0].get("error", "")

        # Must not be cached
        assert playground.response_cache.get("faq-bot", INPUTS) is None


def test_stream_actual_tokens_breach_post_kickoff(mock_execution):
    """Streaming post-kickoff actual usage breach emits BUDGET_EXCEEDED without complete event."""
    mock_execution.crew.usage_metrics = {"total_tokens": 5000}
    mock_execution.crew.kickoff.return_value = "Kickoff result"

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "2500",
    }
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

        assert not any(e.get("type") == "complete" for e in events)
        error_events = [e for e in events if e.get("type") == "error"]
        assert len(error_events) == 1
        assert error_events[0].get("code") == "BUDGET_EXCEEDED"
        assert "5000 tokens accumulated (limit: 2500)" in error_events[0].get(
            "error", ""
        )


# ===========================================================================
# 5. WebSocket (/run/ws) Token Budget Tests
# ===========================================================================


def test_ws_under_budget_completes(mock_execution):
    """WebSocket receives start and complete events when under budget."""
    mock_execution.crew.usage_metrics = {"total_tokens": 300}
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "2000",
    }
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


def test_ws_budget_breached_emits_error(mock_execution):
    """WebSocket receives error event with code BUDGET_EXCEEDED on breach."""

    def fake_kickoff():
        step = SimpleNamespace(
            agent="Agent",
            thought="Step thought " * 150,  # ~375 tokens
            tool=None,
            tool_input=None,
            result=None,
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Unreached"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "150",
    }
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
        assert msg2.get("code") == "BUDGET_EXCEEDED"
        assert "exceeded token budget" in msg2["error"]


# ===========================================================================
# 6. Concurrency & Run-Level Isolation Tests
# ===========================================================================


def test_concurrent_runs_budget_isolation(mock_execution):
    """Concurrent requests have independent TokenBudgetGuard instances with no token bleeding."""
    results = {}
    barrier = threading.Barrier(2)

    crews = {
        "worker_over": MagicMock(usage_metrics={"total_tokens": 1500}),
        "worker_under": MagicMock(usage_metrics={"total_tokens": 300}),
    }
    for c in crews.values():
        c.kickoff.return_value = "Mocked offline LLM response"

    def thread_build_crew(**inputs):
        worker_id = inputs.get("worker")
        barrier.wait()
        return crews[worker_id]

    mock_execution.module.build_crew.side_effect = thread_build_crew

    def worker(worker_id: str):
        with TestClient(playground.app) as client:
            res = client.post(
                "/run",
                json={
                    "recipe": "faq-bot",
                    "inputs": {"worker": worker_id},
                    "no_cache": True,
                },
            )
            results[worker_id] = res

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "1000",
    }
    with patch.dict(os.environ, env, clear=True):
        t1 = threading.Thread(target=worker, args=("worker_over",))
        t2 = threading.Thread(target=worker, args=("worker_under",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

    # Worker 1 breached (1500 > 1000) -> 429
    assert results["worker_over"].status_code == 429
    assert "exceeded token budget" in results["worker_over"].json()["detail"]

    # Worker 2 was within budget (300 <= 1000) -> 200
    assert results["worker_under"].status_code == 200
    assert results["worker_under"].json()["output"] == "Mocked offline LLM response"


# ===========================================================================
# 7. Circuit Breaker Immunity Tests
# ===========================================================================


def test_circuit_breaker_immune_to_budget_breaches(mock_execution):
    """BudgetExceededError does not trip or increment the provider circuit breaker."""
    mock_execution.crew.usage_metrics = {"total_tokens": 5000}

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "1000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        primary_cb = circuit_registry.get_breaker("primary")
        assert primary_cb._consecutive_failures == 0
        assert primary_cb._total_failures == 0
        assert primary_cb.state == CircuitState.CLOSED

        # Trigger 5 consecutive budget breaches
        for i in range(5):
            res = client.post(
                "/run",
                json={"recipe": "faq-bot", "inputs": {"idx": str(i)}, "no_cache": True},
            )
            assert res.status_code == 429

        # Provider circuit breaker must remain completely healthy
        assert primary_cb._consecutive_failures == 0
        assert primary_cb._total_failures == 0
        assert primary_cb.state == CircuitState.CLOSED


# ===========================================================================
# 8. Adversarial Edge Cases & Cleanup Tests
# ===========================================================================


def test_actual_tokens_reconciliation_variations():
    """extract_actual_tokens correctly extracts from dicts, objects, or returns None."""
    from governance import TokenBudgetGuard, extract_actual_tokens

    # Case 1: crew.usage_metrics as object with total_tokens attribute
    class UsageObj:
        total_tokens = 450

    mock_crew = SimpleNamespace(usage_metrics=UsageObj())
    assert extract_actual_tokens(crew=mock_crew) == 450

    # Case 2: result.usage_metrics as dict
    mock_res = SimpleNamespace(usage_metrics={"total_tokens": 780})
    assert extract_actual_tokens(result=mock_res) == 780

    # Case 3: result.token_usage as object
    mock_res2 = SimpleNamespace(token_usage=UsageObj())
    assert extract_actual_tokens(result=mock_res2) == 450

    # Case 4: Neither has metrics -> returns None
    assert extract_actual_tokens(crew=SimpleNamespace(), result="plain string") is None

    # Case 5: set_final_usage ignores <= 0 and preserves estimated tokens
    guard = TokenBudgetGuard(run_id="test", max_tokens=1000)
    guard.add_step_text("A" * 400)  # ~100 estimated tokens
    assert guard.is_estimated is True
    assert guard.accumulated_tokens == 100
    guard.set_final_usage(0)
    assert guard.is_estimated is True
    assert guard.accumulated_tokens == 100


def test_failover_fallback_midflight_step_breach(mock_execution):
    """When primary trips with 503 and fallback step callback breaches budget, 429 is returned."""
    primary_call = True

    def fake_build_crew(**inputs):
        nonlocal primary_call
        active = getattr(playground._thread_local, "active_provider", None)
        mock_execution.build_crew_calls.append(active)
        c = MagicMock()
        if primary_call:
            primary_call = False
            c.kickoff.side_effect = RuntimeError("503 Service Unavailable")
        else:

            def fallback_kickoff():
                step = SimpleNamespace(
                    thought="Fallback step " * 100,  # ~350 tokens
                    text="",
                    result="",
                )
                if hasattr(c, "step_callback") and c.step_callback:
                    c.step_callback(step)
                return "Should not reach here"

            c.kickoff.side_effect = fallback_kickoff
        return c

    mock_execution.module.build_crew.side_effect = fake_build_crew

    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "LLM_FALLBACK_API_KEY": FALLBACK_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "150",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post("/run", json={"recipe": "faq-bot", "inputs": INPUTS})
        assert res.status_code == 429
        assert "exceeded token budget" in res.json()["detail"]


def test_bypassed_cache_still_enforces_budget(mock_execution):
    """When cache is bypassed via no_cache=True, budget enforcement is strictly applied."""
    # Pre-populate cache with a previously successful result
    playground.response_cache.set("faq-bot", INPUTS, "Pre-existing cached output")
    assert (
        playground.response_cache.get("faq-bot", INPUTS) == "Pre-existing cached output"
    )

    # New request with no_cache=True exceeds budget
    mock_execution.crew.usage_metrics = {"total_tokens": 5000}
    env = {
        "LLM_API_KEY": PRIMARY_KEY,
        "PLAYGROUND_MAX_RUN_TOKENS": "1000",
    }
    with patch.dict(os.environ, env, clear=True), TestClient(playground.app) as client:
        res = client.post(
            "/run",
            json={"recipe": "faq-bot", "inputs": INPUTS, "no_cache": True},
        )
        assert res.status_code == 429
        # Existing valid cache entry must remain intact
        assert (
            playground.response_cache.get("faq-bot", INPUTS)
            == "Pre-existing cached output"
        )


def test_stream_disconnect_releases_probe(mock_execution):
    """Client disconnect during streaming cleanly releases half-open circuit breaker probe."""
    primary_cb = circuit_registry.get_breaker("primary")
    for _ in range(3):
        primary_cb.record_failure(RuntimeError("503 error"), now=100.0)

    # Move time forward past cooldown (cooldown 30s) -> HALF_OPEN
    assert primary_cb.get_state(now=135.0) == CircuitState.HALF_OPEN

    events = []
    stop_event = threading.Event()

    def fake_kickoff():
        stop_event.set()
        step = SimpleNamespace(
            agent="Researcher",
            thought="Step thought",
            tool=None,
            tool_input=None,
            result=None,
        )
        if (
            hasattr(mock_execution.crew, "step_callback")
            and mock_execution.crew.step_callback
        ):
            mock_execution.crew.step_callback(step)
        return "Complete"

    mock_execution.crew.kickoff.side_effect = fake_kickoff

    env = {"LLM_API_KEY": PRIMARY_KEY}
    with (
        patch.dict(os.environ, env, clear=True),
        patch("time.monotonic", return_value=135.0),
    ):
        playground.execute_recipe_stream(
            "faq-bot",
            INPUTS,
            push_event=events.append,
            stop_event=stop_event,
        )

    # Probe must be released, meaning another probe can now be acquired
    allowed, state = primary_cb.can_execute(now=135.0)
    assert allowed is True
    assert state == CircuitState.HALF_OPEN
