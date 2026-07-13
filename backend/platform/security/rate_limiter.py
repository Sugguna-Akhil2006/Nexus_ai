"""Rate limiter module implementing token-bucket client request rate-limiting."""

import threading
import time
from typing import Dict, Tuple


class RateLimiter:
    """Thread-safe rate limiter managing token buckets per client IP/key."""

    def __init__(self, rate_limit: int = 60, window_seconds: float = 60.0) -> None:
        """Initializes settings.

        Args:
            rate_limit: Max allowed tokens (requests).
            window_seconds: Period of window in seconds.
        """
        self.rate_limit = rate_limit
        self.window = window_seconds
        # maps identifier -> (tokens_left, last_updated_epoch)
        self._buckets: Dict[str, Tuple[float, float]] = {}
        self._lock = threading.Lock()

    def is_allowed(self, identifier: str) -> bool:
        """Evaluates token bucket consumption, determining if request is allowed.

        Args:
            identifier: Client IP or token key.
        """
        now = time.time()
        with self._lock:
            bucket = self._buckets.get(identifier)
            if not bucket:
                self._buckets[identifier] = (self.rate_limit - 1, now)
                return True

            tokens, last_update = bucket
            # Refill tokens based on time elapsed
            elapsed = now - last_update
            refill = elapsed * (self.rate_limit / self.window)
            tokens = min(self.rate_limit, tokens + refill)

            if tokens >= 1:
                self._buckets[identifier] = (tokens - 1, now)
                return True
            else:
                self._buckets[identifier] = (tokens, now)
                return False
