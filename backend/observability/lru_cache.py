"""Thread-safe LRU Cache with TTL support and telemetry tracking."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timedelta
import threading
from typing import Any, Callable, Dict, Optional, Tuple


class LRUTTLCache:
    """Thread-safe Least Recently Used (LRU) Cache with Time-to-Live (TTL) expiration."""

    def __init__(self, capacity: int = 128, default_ttl_seconds: float = 300.0) -> None:
        self.capacity = capacity
        self.default_ttl_seconds = default_ttl_seconds
        self.cache: OrderedDict[str, Tuple[Any, datetime]] = OrderedDict()
        self.lock = threading.Lock()
        
        # Telemetry
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Retrieves value from cache if present and not expired."""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, expires = self.cache[key]
            if datetime.utcnow() > expires:
                # Expired
                self.cache.pop(key)
                self.misses += 1
                return None

            # Move to end to mark as recently used
            self.cache.move_to_end(key)
            self.hits += 1
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float] = None) -> None:
        """Sets key value pair in cache with expiration details."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        expires = datetime.utcnow() + timedelta(seconds=ttl)
        
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.capacity:
                # Evict oldest
                self.cache.popitem(last=False)
            
            self.cache[key] = (value, expires)

    def invalidate(self, key: str) -> None:
        """Invalidates/removes a single key from cache."""
        with self.lock:
            self.cache.pop(key, None)

    def clear(self) -> None:
        """Clears all cache elements."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    @property
    def hit_ratio(self) -> float:
        """Returns cache hit ratio (0.0 to 1.0)."""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 1.0
