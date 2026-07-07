"""Generic TTL-aware thread-safe cache service for the Product Experience Layer.

Provides a singleton, namespace-partitioned, in-memory cache that supports
time-to-live expiry, hit-count tracking, and per-namespace invalidation.
Suitable for caching reports, history records, dashboard statistics, job
states, and pipeline metrics.

Example usage::

    cache = CacheService()
    cache.set("reports", "rpt-001", report_data, ttl_seconds=300)
    value = cache.get("reports", "rpt-001")
    cache.invalidate("reports", "rpt-001")
    cache.invalidate_namespace("reports")
    stats = cache.stats()
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

T = TypeVar("T")

# Supported cache namespaces
NAMESPACE_REPORTS = "reports"
NAMESPACE_HISTORY = "history"
NAMESPACE_DASHBOARD = "dashboard_stats"
NAMESPACE_JOBS = "jobs"
NAMESPACE_METRICS = "metrics"

_VALID_NAMESPACES = {
    NAMESPACE_REPORTS,
    NAMESPACE_HISTORY,
    NAMESPACE_DASHBOARD,
    NAMESPACE_JOBS,
    NAMESPACE_METRICS,
}

# Default TTL values per namespace (seconds)
_DEFAULT_TTL: Dict[str, int] = {
    NAMESPACE_REPORTS: 600,       # 10 minutes
    NAMESPACE_HISTORY: 300,       # 5 minutes
    NAMESPACE_DASHBOARD: 120,     # 2 minutes
    NAMESPACE_JOBS: 3600,         # 1 hour
    NAMESPACE_METRICS: 60,        # 1 minute
}


@dataclass
class CacheEntry:
    """Single cache entry with expiry and access statistics.

    Attributes:
        value: The cached payload.
        expires_at: UNIX timestamp after which the entry is stale.
        hit_count: Number of successful cache reads.
        last_accessed: UNIX timestamp of the most recent read.
        created_at: UNIX timestamp of initial insertion.
    """

    value: Any
    expires_at: float
    hit_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        """Returns True when the current time is past the expiry timestamp."""
        return time.time() > self.expires_at

    def touch(self) -> None:
        """Updates access statistics on a cache hit."""
        self.hit_count += 1
        self.last_accessed = time.time()


class CacheService:
    """Singleton, namespace-partitioned, TTL-aware thread-safe cache.

    All public methods are safe for concurrent use across multiple threads.
    The singleton pattern ensures a single shared cache across the process.

    Namespace partitioning prevents key collisions between different data
    domains (reports, jobs, metrics, etc.).
    """

    _instance: Optional["CacheService"] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "CacheService":
        with cls._lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                # Namespace-keyed dict of {key: CacheEntry}
                instance._store: Dict[str, Dict[str, CacheEntry]] = {
                    ns: {} for ns in _VALID_NAMESPACES
                }
                instance._global_hits: int = 0
                instance._global_misses: int = 0
                instance._rw_lock = threading.RLock()
                cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Core Operations
    # ------------------------------------------------------------------

    def get(self, namespace: str, key: str) -> Optional[Any]:
        """Retrieves a cached value if present and not expired.

        Args:
            namespace: The cache namespace (use NAMESPACE_* constants).
            key: Unique key within the namespace.

        Returns:
            The cached value, or None on miss or expiry.
        """
        self._validate_namespace(namespace)
        with self._rw_lock:
            entry = self._store[namespace].get(key)
            if entry is None or entry.is_expired():
                if entry is not None:
                    del self._store[namespace][key]
                self._global_misses += 1
                return None
            entry.touch()
            self._global_hits += 1
            return entry.value

    def set(
        self,
        namespace: str,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Stores a value in the cache under the given namespace and key.

        Args:
            namespace: The cache namespace (use NAMESPACE_* constants).
            key: Unique key within the namespace.
            value: The payload to cache (must be serialisable for stats).
            ttl_seconds: Optional override for the namespace default TTL.
        """
        self._validate_namespace(namespace)
        ttl = ttl_seconds if ttl_seconds is not None else _DEFAULT_TTL[namespace]
        expires_at = time.time() + ttl
        with self._rw_lock:
            self._store[namespace][key] = CacheEntry(
                value=value,
                expires_at=expires_at,
            )

    def invalidate(self, namespace: str, key: str) -> bool:
        """Removes a single entry from the cache.

        Args:
            namespace: The cache namespace.
            key: Key to remove.

        Returns:
            True if the key existed and was removed, False otherwise.
        """
        self._validate_namespace(namespace)
        with self._rw_lock:
            existed = key in self._store[namespace]
            self._store[namespace].pop(key, None)
            return existed

    def invalidate_namespace(self, namespace: str) -> int:
        """Clears all entries in a given namespace.

        Args:
            namespace: The cache namespace to flush.

        Returns:
            Number of entries removed.
        """
        self._validate_namespace(namespace)
        with self._rw_lock:
            count = len(self._store[namespace])
            self._store[namespace] = {}
            return count

    def list_keys(self, namespace: str) -> List[str]:
        """Lists all non-expired keys in a namespace.

        Args:
            namespace: The cache namespace.

        Returns:
            List of active (non-expired) cache keys.
        """
        self._validate_namespace(namespace)
        with self._rw_lock:
            active: List[str] = []
            expired: List[str] = []
            for key, entry in self._store[namespace].items():
                if entry.is_expired():
                    expired.append(key)
                else:
                    active.append(key)
            for key in expired:
                del self._store[namespace][key]
            return active

    def exists(self, namespace: str, key: str) -> bool:
        """Checks whether a valid, non-expired entry exists.

        Args:
            namespace: The cache namespace.
            key: Key to check.

        Returns:
            True if the entry exists and is not expired.
        """
        return self.get(namespace, key) is not None

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        """Returns cache-wide hit/miss statistics and per-namespace counts.

        Returns:
            Dictionary with global stats and per-namespace entry counts.
        """
        with self._rw_lock:
            ns_counts: Dict[str, int] = {}
            for ns, entries in self._store.items():
                # Only count live entries
                ns_counts[ns] = sum(
                    1 for e in entries.values() if not e.is_expired()
                )
            total = self._global_hits + self._global_misses
            hit_rate = (self._global_hits / total * 100) if total > 0 else 0.0
            return {
                "global_hits": self._global_hits,
                "global_misses": self._global_misses,
                "hit_rate_pct": round(hit_rate, 2),
                "namespaces": ns_counts,
                "total_live_entries": sum(ns_counts.values()),
            }

    def reset_stats(self) -> None:
        """Resets global hit/miss counters without clearing cached data."""
        with self._rw_lock:
            self._global_hits = 0
            self._global_misses = 0

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_namespace(namespace: str) -> None:
        """Raises ValueError for unknown namespaces."""
        if namespace not in _VALID_NAMESPACES:
            raise ValueError(
                f"Unknown cache namespace '{namespace}'. "
                f"Valid namespaces: {sorted(_VALID_NAMESPACES)}"
            )
