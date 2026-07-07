"""Connector Rate Limiter implementing token bucket algorithm."""

from __future__ import annotations

import time
import threading


class ConnectorRateLimiter:
    """Regulates connection call frequencies preventing API rate limit limits blocks."""

    def __init__(self, limit_per_minute: int = 60) -> None:
        self.limit = limit_per_minute
        self.capacity = limit_per_minute
        self.tokens = float(limit_per_minute)
        self.last_refill = time.time()
        self._lock = threading.Lock()

    def consume(self) -> bool:
        """Attempts to consume 1 token. Returns True if successful, False if throttled."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.last_refill = now
            
            # Refill tokens rate: limit / 60 per second
            self.tokens = min(float(self.capacity), self.tokens + elapsed * (self.limit / 60.0))
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return True
            return False
