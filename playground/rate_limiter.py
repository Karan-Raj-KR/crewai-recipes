from __future__ import annotations

import logging
import math
import os
import re
import threading
import time
from collections import deque
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import Request, WebSocket

logger = logging.getLogger(__name__)

# Supported time units and their duration in seconds
TIME_UNIT_MULTIPLIERS: dict[str, int] = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hr": 3600,
    "hour": 3600,
    "hours": 3600,
    "d": 86400,
    "day": 86400,
    "days": 86400,
}

RATE_LIMIT_PATTERN = re.compile(r"^\s*(\d+)\s*\/\s*(?:(\d+)\s*)?([a-zA-Z]+)\s*$")


class SlidingWindowRateLimiter:
    """Thread-safe, in-memory sliding-window rate limiter for the playground.

    Tracks request timestamps within a rolling window per client key using
    collections.deque and time.monotonic(). Prevents runaway execution loops
    without external storage dependencies.
    """

    def __init__(
        self, limit_string: str | None = None, max_clients: int = 10000
    ) -> None:
        """Initialize the rate limiter.

        Args:
            limit_string: Rate limit expression (e.g., '30/5min', '0' to disable).
                If None, reads from PLAYGROUND_RATE_LIMIT env var (default '30/5min').
            max_clients: Maximum number of distinct client keys to retain in memory.
        """
        self.lock = threading.Lock()
        self.max_clients = max_clients
        self._clients: dict[str, deque[float]] = {}
        self.enabled: bool = True
        self.limit: int = 30
        self.window_seconds: int = 300
        self.parse_config(limit_string)

    def parse_config(self, limit_string: str | None) -> None:
        """Parse configuration string into rate limit and window parameters.

        Args:
            limit_string: String specification or None.
        """
        raw = (
            limit_string
            if limit_string is not None
            else os.getenv("PLAYGROUND_RATE_LIMIT", "30/5min")
        )
        cleaned = str(raw).strip()

        if cleaned == "0":
            self.enabled = False
            self.limit = 0
            self.window_seconds = 0
            return

        match = RATE_LIMIT_PATTERN.match(cleaned)
        if match:
            count_str, duration_str, unit_str = match.groups()
            unit_lower = unit_str.lower()
            if unit_lower in TIME_UNIT_MULTIPLIERS:
                count = int(count_str)
                multiplier = TIME_UNIT_MULTIPLIERS[unit_lower]
                duration = int(duration_str) if duration_str else 1
                if count > 0 and duration > 0:
                    self.enabled = True
                    self.limit = count
                    self.window_seconds = duration * multiplier
                    return

        logger.warning(
            "Invalid PLAYGROUND_RATE_LIMIT '%s'; falling back to default '30/5min'.",
            cleaned,
        )
        self.enabled = True
        self.limit = 30
        self.window_seconds = 300

    def is_allowed(self, client_key: str, now: float | None = None) -> tuple[bool, int]:
        """Check if a request from the given client key is permitted.

        Args:
            client_key: Client identifier (e.g. IP address or hostname).
            now: Monotonic timestamp override for deterministic testing.

        Returns:
            Tuple of (allowed: bool, retry_after_seconds: int).
            When allowed is True, retry_after_seconds is 0.
            When allowed is False, retry_after_seconds is the ceil integer seconds
            until the client's oldest timestamp rolls out of the active window.
        """
        if not self.enabled:
            return True, 0

        current_time = time.monotonic() if now is None else now

        with self.lock:
            dq = self._clients.get(client_key)
            if dq is None:
                if len(self._clients) >= self.max_clients:
                    self._prune_stale_clients(current_time)
                dq = deque()
                self._clients[client_key] = dq

            # Expire timestamps outside the rolling window
            cutoff = current_time - self.window_seconds
            while dq and dq[0] <= cutoff:
                dq.popleft()

            # Check capacity
            if len(dq) >= self.limit:
                oldest_timestamp = dq[0]
                retry_after = max(
                    1,
                    math.ceil(oldest_timestamp + self.window_seconds - current_time),
                )
                return False, retry_after

            # Permitted: record request timestamp
            dq.append(current_time)
            return True, 0

    def _prune_stale_clients(self, current_time: float) -> None:
        """Evict inactive client keys to prevent unbounded memory growth."""
        cutoff = current_time - self.window_seconds
        stale_keys = [
            k for k, dq in self._clients.items() if not dq or dq[-1] <= cutoff
        ]
        for k in stale_keys:
            self._clients.pop(k, None)

        # If still over threshold, evict oldest idle keys
        if len(self._clients) >= self.max_clients:
            evict_count = max(1, len(self._clients) // 10)
            keys_to_remove = list(self._clients.keys())[:evict_count]
            for k in keys_to_remove:
                self._clients.pop(k, None)

    def reset(self) -> None:
        """Clear all in-memory client rate-limiting state (primarily for test isolation)."""
        with self.lock:
            self._clients.clear()


def get_client_ip(connection: Request | WebSocket) -> str:
    """Extract client IP address safely from a request or websocket connection.

    Uses connection.client.host. Does not trust spoofable X-Forwarded-For headers
    in local or direct deployments to prevent rate-limit bypass. Falls back to
    'unknown_client' if client address is missing.

    Args:
        connection: Starlette/FastAPI Request or WebSocket object.

    Returns:
        Client IP string or 'unknown_client'.
    """
    client = getattr(connection, "client", None)
    if client and getattr(client, "host", None):
        host = str(client.host).strip()
        if host:
            return host
    return "unknown_client"
