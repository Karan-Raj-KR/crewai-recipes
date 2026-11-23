"""Governance and operational resilience engine for the CrewAI Recipes Playground (#279).

Provides:
- Thread-safe CircuitBreaker state machine (CLOSED, OPEN, HALF_OPEN) with monotonic
  cooldown timers and exclusive half-open probe locking.
- Trippable vs non-trippable provider failure classification.
- Process-level CircuitBreakerRegistry.
- TokenBudgetGuard for run-level token ceiling tracking and interruption.
"""

from __future__ import annotations

import enum
import logging
import math
import os
import random
import re
import threading
import time
from collections.abc import Callable

logger = logging.getLogger(__name__)


class CircuitState(str, enum.Enum):
    """States of a provider circuit breaker."""

    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


class GovernanceError(Exception):
    """Base exception for playground governance errors."""


class CircuitBreakerOpenError(GovernanceError):
    """Raised when an execution is attempted on a tripped (OPEN) provider circuit."""

    def __init__(
        self,
        provider: str,
        cooldown_remaining: float,
        message: str | None = None,
    ) -> None:
        self.provider = provider
        self.cooldown_remaining = max(0.0, cooldown_remaining)
        detail = message or (
            f"Provider '{provider}' circuit is OPEN (temporarily unavailable). "
            f"Cooldown remaining: {self.cooldown_remaining:.1f}s."
        )
        super().__init__(detail)


class BudgetExceededError(GovernanceError):
    """Raised when a run breaches its configured token consumption budget."""

    def __init__(
        self,
        run_id: str,
        accumulated_tokens: int,
        limit: int,
        is_estimated: bool = False,
    ) -> None:
        self.run_id = run_id
        self.accumulated_tokens = accumulated_tokens
        self.limit = limit
        self.is_estimated = is_estimated
        qualifier = "estimated " if is_estimated else ""
        detail = (
            f"Run '{run_id}' exceeded token budget: {accumulated_tokens} {qualifier}"
            f"tokens accumulated (limit: {limit})."
        )
        super().__init__(detail)


# Common HTTP status codes representing upstream provider failure or rate limiting
TRIPPABLE_STATUS_CODES: set[int] = {429, 500, 502, 503, 504}

# Substrings in exception types or messages indicating provider rate limit or outage
TRIPPABLE_INDICATORS: tuple[str, ...] = (
    "ratelimit",
    "rate_limit",
    "rate limit",
    "too many requests",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "timed out",
    "timeout",
    "connection error",
    "connectionerror",
    "connection refused",
    "connectionrefused",
    "connection reset",
    "connectionreset",
    "internalservererror",
    "internal server error",
    "overloaded",
)

# Explicitly excluded exceptions that represent client-side errors, not provider outages
NON_TRIPPABLE_TYPES: tuple[type[BaseException], ...] = (
    BudgetExceededError,
    InterruptedError,
    ValueError,
    KeyError,
    FileNotFoundError,
    PermissionError,
)


def is_trippable_error(exc: BaseException | None) -> bool:
    """Determine whether an exception represents a transient upstream provider failure.

    Trippable errors (rate limits, 5xx server errors, network timeouts, connection drops)
    increment the circuit breaker failure count.
    Client errors (400, 401, 403, 404, bad input syntax, budget breaches) bypass the breaker.
    """
    if exc is None:
        return False

    # Check cause/context chain
    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))

        # Check explicit non-trippable classes
        if isinstance(current, NON_TRIPPABLE_TYPES):
            return False

        # Check HTTP status code attributes if present (e.g. requests, httpx, openai)
        status_code = getattr(current, "status_code", None)
        if status_code is None and hasattr(current, "response"):
            status_code = getattr(current.response, "status_code", None)
        if status_code is None and hasattr(current, "code"):
            code_val = getattr(current, "code", None)
            if isinstance(code_val, int):
                status_code = code_val

        if isinstance(status_code, int):
            if status_code in TRIPPABLE_STATUS_CODES:
                return True
            if 400 <= status_code < 500 and status_code != 429:
                return False

        # Standard network/socket/connection error types
        if isinstance(current, (ConnectionError, TimeoutError)):
            return True

        # Inspect class name and message text
        type_name = type(current).__name__.lower()
        msg = str(current).lower()

        # Check explicit HTTP status codes with word boundaries to avoid false positives (e.g. 5040 bytes)
        if re.search(r"\b(?:http\s*)?(?:429|500|502|503|504)\b", msg):
            return True

        for indicator in TRIPPABLE_INDICATORS:
            if indicator in type_name or indicator in msg:
                return True

        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )

    return False


RATE_LIMIT_INDICATORS: tuple[str, ...] = (
    "ratelimit",
    "rate_limit",
    "rate limit",
    "too many requests",
    "quota exceeded",
    "resource exhausted",
    "tokens per minute",
    "requests per minute",
)


def is_rate_limit_error(exc: BaseException | None) -> bool:
    """Determine whether an exception represents an upstream provider rate-limit (429) event."""
    if exc is None:
        return False

    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))

        if isinstance(current, NON_TRIPPABLE_TYPES):
            return False

        status_code = getattr(current, "status_code", None)
        if status_code is None and hasattr(current, "response"):
            status_code = getattr(current.response, "status_code", None)
        if status_code is None and hasattr(current, "code"):
            code_val = getattr(current, "code", None)
            if isinstance(code_val, int):
                status_code = code_val

        if isinstance(status_code, int):
            if status_code == 429:
                return True
            if 400 <= status_code < 500:
                return False

        type_name = type(current).__name__.lower()
        msg = str(current).lower()

        # Check explicit 429 status code with word boundary to avoid false positives (e.g. 4291 bytes)
        if re.search(r"\b(?:http\s*)?429\b", msg):
            return True

        # Check TPM / RPM with word boundaries and limit/quota association
        if re.search(r"\b(?:tpm|rpm)\b", msg) and any(
            kw in msg for kw in ("limit", "quota", "exceeded", "reached", "rate")
        ):
            return True

        for indicator in RATE_LIMIT_INDICATORS:
            if indicator in type_name or indicator in msg:
                return True

        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )

    return False


def extract_retry_after(exc: BaseException | None) -> float | None:
    """Extract retry-after delay in seconds from an exception or its HTTP response attributes.

    Inspects:
    1. Direct numeric/string attribute on the exception: getattr(exc, 'retry_after', None).
    2. Response or exception headers (case-insensitively, supporting numeric seconds and RFC 7231 HTTP dates).
    3. Error message string matching retry patterns (e.g. 'try again in 5.2s' or 'retry after 10s').

    Returns:
        Float delay in seconds clamped to [0.1, 3600.0] if found and positive, otherwise None.
    """
    if exc is None:
        return None

    current: BaseException | None = exc
    seen: set[int] = set()

    while current is not None and id(current) not in seen:
        seen.add(id(current))

        # Check direct retry_after attribute
        direct = getattr(current, "retry_after", None)
        if direct is not None:
            try:
                val = float(direct)
                if math.isfinite(val) and val > 0:
                    return max(0.1, min(3600.0, val))
            except (ValueError, TypeError):
                pass

        # Check response headers (e.g. httpx.Response, requests.Response)
        response = getattr(current, "response", None)
        headers = None
        if response is not None:
            headers = getattr(response, "headers", None)
        if headers is None:
            headers = getattr(current, "headers", None)

        if headers is not None:
            header_val = None
            if hasattr(headers, "get"):
                header_val = headers.get("retry-after") or headers.get("Retry-After")
            if header_val is None and hasattr(headers, "items"):
                for k, v in headers.items():
                    if str(k).lower() == "retry-after":
                        header_val = v
                        break

            if header_val is not None:
                # 1. Try numeric seconds
                try:
                    val = float(header_val)
                    if math.isfinite(val) and val > 0:
                        return max(0.1, min(3600.0, val))
                except (ValueError, TypeError):
                    # 2. Try RFC 7231 HTTP-date string
                    try:
                        import email.utils
                        from datetime import datetime, timezone

                        dt = email.utils.parsedate_to_datetime(str(header_val))
                        if dt is not None:
                            diff = (dt - datetime.now(timezone.utc)).total_seconds()
                            if math.isfinite(diff) and diff > 0:
                                return max(0.1, min(3600.0, diff))
                    except (ValueError, TypeError, OverflowError):
                        pass

        # Check regex in error message string
        msg = str(current)
        match = re.search(
            r"(?:retry[-_\s]after|try again in|wait)\s*[:=]?\s*(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?",
            msg,
            re.IGNORECASE,
        )
        if match:
            try:
                val = float(match.group(1))
                if math.isfinite(val) and val > 0:
                    return max(0.1, min(3600.0, val))
            except (ValueError, TypeError):
                pass

        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )

    return None


class CircuitBreaker:
    """Thread-safe circuit breaker protecting an external LLM provider endpoint.

    States:
        CLOSED: Normal operation. Success resets consecutive failure counter.
        OPEN: Tripped after failure_threshold consecutive failures. Diverts or fast-fails.
        HALF_OPEN: After cooldown_seconds, allows exactly one probe request to verify recovery.
    """

    def __init__(
        self,
        provider: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 30.0,
        enabled: bool = True,
    ) -> None:
        self.provider = provider
        self.failure_threshold = max(1, failure_threshold)
        self.cooldown_seconds = max(0.1, cooldown_seconds)
        self._active_cooldown_seconds: float = self.cooldown_seconds
        self.enabled = enabled

        self._state: CircuitState = CircuitState.CLOSED
        self._lock = threading.RLock()
        self._consecutive_failures: int = 0
        self._opened_at: float | None = None
        self._probe_in_progress: bool = False
        self._total_successes: int = 0
        self._total_failures: int = 0

    @property
    def state(self) -> CircuitState:
        """Current state of the breaker."""
        with self._lock:
            return self._state

    def get_state(self, now: float | None = None) -> CircuitState:
        """Return the current state of the breaker, evaluating cooldown transition if OPEN."""
        with self._lock:
            if self._state == CircuitState.OPEN and self._opened_at is not None:
                current_time = time.monotonic() if now is None else now
                if current_time - self._opened_at >= self._active_cooldown_seconds:
                    return CircuitState.HALF_OPEN
            return self._state

    def can_execute(self, now: float | None = None) -> tuple[bool, CircuitState]:
        """Check whether a request is permitted to call this provider.

        Args:
            now: Monotonic timestamp override for deterministic testing.

        Returns:
            Tuple of (allowed: bool, state: CircuitState).
            When allowed is True:
                - CLOSED: Normal execution permitted.
                - HALF_OPEN: This caller holds the exclusive probe permit.
            When allowed is False:
                - OPEN: Circuit is active and in cooldown. Caller should fast-fail or failover.
                - HALF_OPEN: A probe is already in progress by another thread.
        """
        if not self.enabled:
            return True, CircuitState.CLOSED

        current_time = time.monotonic() if now is None else now

        with self._lock:
            # Check if OPEN has elapsed cooldown
            if self._state == CircuitState.OPEN:
                elapsed = current_time - (self._opened_at or 0.0)
                if elapsed >= self._active_cooldown_seconds:
                    self._state = CircuitState.HALF_OPEN
                    self._probe_in_progress = False

            if self._state == CircuitState.CLOSED:
                return True, CircuitState.CLOSED

            if self._state == CircuitState.HALF_OPEN:
                # Exclusive probe permit: allow exactly one thread
                if not self._probe_in_progress:
                    self._probe_in_progress = True
                    return True, CircuitState.HALF_OPEN
                return False, CircuitState.HALF_OPEN

            return False, CircuitState.OPEN

    def record_success(self) -> None:
        """Record a successful execution against this provider."""
        with self._lock:
            self._total_successes += 1
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "Provider '%s' probe succeeded; circuit transitioning HALF_OPEN -> CLOSED.",
                    self.provider,
                )
                self._state = CircuitState.CLOSED
                self._opened_at = None
                self._active_cooldown_seconds = self.cooldown_seconds
                self._probe_in_progress = False
                self._consecutive_failures = 0
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    def record_failure(
        self,
        exc: BaseException | None = None,
        now: float | None = None,
        cooldown_override: float | None = None,
    ) -> bool:
        """Record an execution failure against this provider.

        Args:
            exc: Exception raised by the call. If not a trippable error, ignored.
            now: Monotonic timestamp override for deterministic testing.

        Returns:
            True if the circuit tripped to OPEN as a result of this failure, False otherwise.
        """
        if exc is not None and not is_trippable_error(exc):
            with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    self._probe_in_progress = False
            return False

        current_time = time.monotonic() if now is None else now

        with self._lock:
            self._total_failures += 1

            effective_cooldown = self.cooldown_seconds
            if cooldown_override is not None:
                try:
                    co_val = float(cooldown_override)
                    if math.isfinite(co_val) and co_val > 0:
                        effective_cooldown = max(
                            self.cooldown_seconds, min(300.0, co_val)
                        )
                except (ValueError, TypeError):
                    pass

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed: immediately revert to OPEN and reset cooldown
                logger.warning(
                    "Provider '%s' probe failed; circuit transitioning HALF_OPEN -> OPEN (cooldown: %.1fs).",
                    self.provider,
                    effective_cooldown,
                )
                self._state = CircuitState.OPEN
                self._opened_at = current_time
                self._active_cooldown_seconds = effective_cooldown
                self._probe_in_progress = False
                return True

            if self._state == CircuitState.CLOSED:
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.failure_threshold:
                    logger.warning(
                        "Provider '%s' reached %d consecutive failures; tripping circuit CLOSED -> OPEN (cooldown: %.1fs).",
                        self.provider,
                        self._consecutive_failures,
                        effective_cooldown,
                    )
                    self._state = CircuitState.OPEN
                    self._opened_at = current_time
                    self._active_cooldown_seconds = effective_cooldown
                    self._probe_in_progress = False
                    return True

            return False

    def release_probe(self) -> None:
        """Release probe permit if held, without altering state (e.g. on non-trippable error or cancellation)."""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._probe_in_progress = False

    def get_cooldown_remaining(self, now: float | None = None) -> float:
        """Return the remaining cooldown seconds if OPEN, or 0.0 if not."""
        with self._lock:
            if self._state != CircuitState.OPEN or self._opened_at is None:
                return 0.0
            current_time = time.monotonic() if now is None else now
            elapsed = current_time - self._opened_at
            return max(0.0, self._active_cooldown_seconds - elapsed)

    def reset(self) -> None:
        """Reset the breaker to initial CLOSED state (primarily for test isolation)."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._consecutive_failures = 0
            self._opened_at = None
            self._active_cooldown_seconds = self.cooldown_seconds
            self._probe_in_progress = False
            self._total_successes = 0
            self._total_failures = 0


class CircuitBreakerRegistry:
    """Process-level shared registry managing CircuitBreaker instances per provider."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._breakers: dict[str, CircuitBreaker] = {}
        self.load_from_env()

    def load_from_env(self) -> None:
        """Initialize or update configuration from environment variables."""
        enabled_raw = os.getenv("PLAYGROUND_CIRCUIT_ENABLED", "true").lower()
        self.enabled = enabled_raw not in ("false", "0", "no", "off")

        try:
            self.failure_threshold = max(
                1, int(os.getenv("PLAYGROUND_CIRCUIT_FAILURE_THRESHOLD", "3"))
            )
        except ValueError:
            self.failure_threshold = 3

        try:
            self.cooldown_seconds = max(
                0.1, float(os.getenv("PLAYGROUND_CIRCUIT_COOLDOWN_SECONDS", "30.0"))
            )
        except ValueError:
            self.cooldown_seconds = 30.0

    def get_breaker(self, provider: str) -> CircuitBreaker:
        """Retrieve or create the singleton CircuitBreaker for a provider key."""
        clean_key = str(provider).strip().lower() or "primary"
        with self._lock:
            breaker = self._breakers.get(clean_key)
            if breaker is None:
                breaker = CircuitBreaker(
                    provider=clean_key,
                    failure_threshold=self.failure_threshold,
                    cooldown_seconds=self.cooldown_seconds,
                    enabled=self.enabled,
                )
                self._breakers[clean_key] = breaker
            return breaker

    def reset_all(self) -> None:
        """Reset all managed circuit breakers to clean state."""
        with self._lock:
            for breaker in self._breakers.values():
                breaker.reset()
            self._breakers.clear()
            self.load_from_env()


class TokenBudgetGuard:
    """Run-level token consumption tracker and ceiling enforcer.

    Tracks accumulated prompt and completion tokens. Evaluates whether a run
    exceeds the configured hard budget, distinguishing exact metrics from step
    character estimates.
    """

    def __init__(
        self,
        run_id: str = "default",
        max_tokens: int | None = None,
        max_cost: float | None = None,
        warning_ratio: float | None = 0.8,
        enabled: bool | None = None,
    ) -> None:
        self.run_id = run_id
        self._lock = threading.RLock()
        if warning_ratio is None:
            raw_ratio = os.getenv("PLAYGROUND_TOKEN_WARNING_RATIO", "0.8")
            try:
                self.warning_ratio = max(0.1, min(0.99, float(raw_ratio)))
            except ValueError:
                self.warning_ratio = 0.8
        else:
            self.warning_ratio = max(0.1, min(0.99, float(warning_ratio)))

        # Configuration resolution
        if max_tokens is None:
            raw_tokens = os.getenv("PLAYGROUND_MAX_RUN_TOKENS", "50000")
            try:
                self.max_tokens = int(raw_tokens)
            except ValueError:
                self.max_tokens = 50000
        else:
            self.max_tokens = max(0, max_tokens)

        if max_cost is None:
            raw_cost = os.getenv("PLAYGROUND_MAX_RUN_COST", "5.0")
            try:
                self.max_cost = float(raw_cost)
            except ValueError:
                self.max_cost = 5.0
        else:
            self.max_cost = max(0.0, max_cost)

        if enabled is None:
            # 0 max_tokens disables enforcement
            self.enabled = self.max_tokens > 0
        else:
            self.enabled = enabled and self.max_tokens > 0

        self.accumulated_tokens: int = 0
        self.is_estimated: bool = False
        self.warning_emitted: bool = False

    def add_step_text(self, text: str) -> tuple[bool, int]:
        """Estimate tokens from an agent thought or step text and add to the run budget.

        Uses standard heuristic of ~4 characters per token.
        Returns:
            Tuple of (warning_needed: bool, accumulated_tokens: int).
        Raises:
            BudgetExceededError: If the accumulated count reaches or exceeds max_tokens.
        """
        if not text or not self.enabled:
            return False, self.accumulated_tokens

        # Conservative character heuristic
        estimated = max(1, len(text) // 4)
        return self._add_tokens(estimated, is_estimated=True)

    def add_actual_tokens(self, tokens: int) -> tuple[bool, int]:
        """Add verified token counts (e.g. from task completion metrics)."""
        if tokens <= 0 or not self.enabled:
            return False, self.accumulated_tokens
        return self._add_tokens(tokens, is_estimated=False)

    def set_final_usage(self, actual_total_tokens: int) -> None:
        """Update guard with exact final tokens after run completion.

        Raises:
            BudgetExceededError: If actual usage exceeded max_tokens.
        """
        if not self.enabled or actual_total_tokens <= 0:
            return

        with self._lock:
            self.accumulated_tokens = actual_total_tokens
            self.is_estimated = False
            if self.accumulated_tokens >= self.max_tokens:
                raise BudgetExceededError(
                    run_id=self.run_id,
                    accumulated_tokens=self.accumulated_tokens,
                    limit=self.max_tokens,
                    is_estimated=False,
                )

    def _add_tokens(self, tokens: int, is_estimated: bool) -> tuple[bool, int]:
        """Internal helper to increment tokens and check limits."""
        with self._lock:
            self.accumulated_tokens += tokens
            if is_estimated:
                self.is_estimated = True

            if self.accumulated_tokens >= self.max_tokens:
                raise BudgetExceededError(
                    run_id=self.run_id,
                    accumulated_tokens=self.accumulated_tokens,
                    limit=self.max_tokens,
                    is_estimated=self.is_estimated,
                )

            warning_threshold = int(self.max_tokens * self.warning_ratio)
            if (
                self.accumulated_tokens >= warning_threshold
                and not self.warning_emitted
            ):
                self.warning_emitted = True
                return True, self.accumulated_tokens

            return False, self.accumulated_tokens


class AdaptiveBackoffPolicy:
    """Calculates adaptive backoff delays with exponential scaling and full jitter (#279).

    Formula (Full Jitter):
        target = min(max_delay, base_delay * (2 ** attempt))
        delay = random.uniform(0, target)
        If retry_after is provided, delay respects the upstream window clamped to max_delay.
    """

    def __init__(
        self,
        base_delay: float | None = None,
        max_delay: float | None = None,
        max_retries: int | None = None,
        jitter: bool = True,
    ) -> None:
        if base_delay is None:
            raw_base = os.getenv("PLAYGROUND_BACKOFF_BASE_SECONDS", "0.5")
            try:
                val = float(raw_base)
                if not math.isfinite(val) or val <= 0:
                    self.base_delay = 0.5
                else:
                    self.base_delay = max(0.01, val)
            except ValueError:
                self.base_delay = 0.5
        else:
            try:
                val = float(base_delay)
                if not math.isfinite(val) or val <= 0:
                    self.base_delay = 0.5
                else:
                    self.base_delay = max(0.01, val)
            except (ValueError, TypeError):
                self.base_delay = 0.5

        if max_delay is None:
            raw_max = os.getenv("PLAYGROUND_BACKOFF_MAX_SECONDS", "10.0")
            try:
                val = float(raw_max)
                if not math.isfinite(val) or val <= 0:
                    self.max_delay = 10.0
                else:
                    self.max_delay = max(self.base_delay, val)
            except ValueError:
                self.max_delay = 10.0
        else:
            try:
                val = float(max_delay)
                if not math.isfinite(val) or val <= 0:
                    self.max_delay = 10.0
                else:
                    self.max_delay = max(self.base_delay, val)
            except (ValueError, TypeError):
                self.max_delay = 10.0

        if max_retries is None:
            raw_retries = os.getenv("PLAYGROUND_BACKOFF_MAX_RETRIES", "3")
            try:
                self.max_retries = max(1, min(5, int(raw_retries)))
            except ValueError:
                self.max_retries = 3
        else:
            try:
                self.max_retries = max(1, min(5, int(max_retries)))
            except (ValueError, TypeError):
                self.max_retries = 3

        self.jitter = jitter

    def compute_delay(
        self,
        attempt: int,
        retry_after: float | None = None,
        rand_func: Callable[[float, float], float] | None = None,
    ) -> float:
        """Compute the delay in seconds for an attempt index (0-based or 1-based).

        Args:
            attempt: Attempt count (>= 0).
            retry_after: Optional upstream Retry-After delay in seconds.
            rand_func: Optional uniform random function (low, high) -> float for testing.

        Returns:
            Computed delay in seconds, bounded by max_delay.
        """
        attempt = min(30, max(0, attempt))
        ceiling = min(self.max_delay, self.base_delay * (2**attempt))

        if retry_after is not None:
            try:
                ra = float(retry_after)
                if math.isfinite(ra) and ra > 0:
                    base = min(self.max_delay, ra)
                    if self.jitter:
                        # Additive jitter ensures delay never falls below base
                        jitter_range = min(1.0, max(0.1, base * 0.1))
                        rnd = (
                            rand_func(0.0, jitter_range)
                            if rand_func
                            else random.uniform(0.0, jitter_range)
                        )
                        return base + rnd
                    return base
            except (ValueError, TypeError):
                pass

        if self.jitter:
            rnd = rand_func(0.0, ceiling) if rand_func else random.uniform(0.0, ceiling)
            return rnd

        return ceiling


# Global default registry
circuit_registry = CircuitBreakerRegistry()


def resolve_provider(preferred: str | None = None) -> tuple[str, CircuitBreaker, bool]:
    """Deterministically select a healthy provider (primary or fallback) based on circuit state.

    Args:
        preferred: Explicit provider name ("primary", "fallback", "secondary", etc.).
                   If None, reads LLM_PROVIDER from the environment (default: "primary").

    Returns:
        Tuple of (provider_name: str, breaker: CircuitBreaker, is_fallback: bool).

    Raises:
        CircuitBreakerOpenError: If the chosen provider or all candidate providers are unavailable.
    """
    if preferred is None:
        preferred = os.getenv("LLM_PROVIDER", "primary").strip().lower()
    else:
        preferred = preferred.strip().lower()

    has_primary_keys = bool(os.getenv("LLM_API_KEY") or os.getenv("NVIDIA_API_KEY"))
    has_fallback_keys = bool(os.getenv("LLM_FALLBACK_API_KEY"))

    primary_cb = circuit_registry.get_breaker("primary")
    fallback_cb = circuit_registry.get_breaker("fallback")

    # Case 1: Caller explicitly requested fallback or secondary
    if preferred in ("fallback", "secondary"):
        allowed, _ = fallback_cb.can_execute()
        if allowed:
            return "fallback", fallback_cb, True
        cooldown = fallback_cb.get_cooldown_remaining()
        raise CircuitBreakerOpenError("fallback", cooldown)

    # Case 2: Only fallback keys exist (implicit auto-fallback per recipe llm contract)
    if not has_primary_keys and has_fallback_keys:
        allowed, _ = fallback_cb.can_execute()
        if allowed:
            return "fallback", fallback_cb, True
        cooldown = fallback_cb.get_cooldown_remaining()
        raise CircuitBreakerOpenError("fallback", cooldown)

    # Case 3: Primary candidate (has primary keys or default configuration)
    primary_allowed, primary_state = primary_cb.can_execute()
    if primary_allowed:
        return "primary", primary_cb, False

    # Primary circuit is OPEN (or probe in progress by another thread).
    # Check if eligible fallback is available.
    if has_fallback_keys:
        fallback_allowed, _ = fallback_cb.can_execute()
        if fallback_allowed:
            logger.info(
                "Primary provider unavailable (state: %s); routing to fallback.",
                primary_state.value,
            )
            return "fallback", fallback_cb, True

        # Both providers are unavailable
        cooldown = primary_cb.get_cooldown_remaining()
        raise CircuitBreakerOpenError(
            "primary",
            cooldown,
            message=(
                f"All LLM provider circuits are OPEN (temporarily unavailable). "
                f"Primary cooldown remaining: {cooldown:.1f}s."
            ),
        )

    # Primary is OPEN and no fallback keys configured
    cooldown = primary_cb.get_cooldown_remaining()
    raise CircuitBreakerOpenError(
        "primary",
        cooldown,
        message=(
            f"Provider 'primary' circuit is OPEN (temporarily unavailable) and "
            f"no fallback provider is configured. Cooldown remaining: {cooldown:.1f}s."
        ),
    )


def can_failover_to_fallback() -> bool:
    """Return True if a fallback provider has credentials and its circuit permits execution."""
    if not os.getenv("LLM_FALLBACK_API_KEY"):
        return False
    fallback_cb = circuit_registry.get_breaker("fallback")
    allowed, _ = fallback_cb.can_execute()
    return allowed


def extract_actual_tokens(crew: object = None, result: object = None) -> int | None:
    """Extract actual total token count from CrewAI crew or kickoff result if available.

    Args:
        crew: Crew instance after .kickoff() execution.
        result: Kickoff result object.

    Returns:
        Integer total tokens if found and > 0, otherwise None.
    """
    if crew is not None:
        usage = getattr(crew, "usage_metrics", None)
        if usage is not None:
            if isinstance(usage, dict):
                total = usage.get("total_tokens")
                if isinstance(total, int) and total > 0:
                    return total
            else:
                total = getattr(usage, "total_tokens", None)
                if isinstance(total, int) and total > 0:
                    return total

    if result is not None:
        for attr in ("token_usage", "usage_metrics"):
            res_usage = getattr(result, attr, None)
            if res_usage is not None:
                if isinstance(res_usage, dict):
                    total = res_usage.get("total_tokens")
                    if isinstance(total, int) and total > 0:
                        return total
                else:
                    total = getattr(res_usage, "total_tokens", None)
                    if isinstance(total, int) and total > 0:
                        return total

    return None
