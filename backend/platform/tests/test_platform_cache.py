"""Unit tests for Platform Caching and Locking managers."""

import time
import unittest

from backend.platform.hardening.cache_manager import CacheManager
from backend.platform.hardening.lock_manager import LockManager


class TestPlatformCacheAndLock(unittest.TestCase):
    """Test suite covering cache read/write limits, expirations, and lock boundaries."""

    def test_cache_fallback_and_expiry(self) -> None:
        """Verifies local cache memory fallback reads, writes, and TTL expirations."""
        cache = CacheManager(host="localhost", port=9999)  # invalid port to force fallback
        self.assertFalse(cache.use_redis)

        # Write
        self.assertTrue(cache.set("session-key", {"user": "alice"}, expire_seconds=1))
        self.assertEqual(cache.get("session-key"), {"user": "alice"})

        # Wait for expiration
        time.sleep(1.2)
        self.assertIsNone(cache.get("session-key"))

    def test_lock_fallback_concurrency(self) -> None:
        """Verifies lock acquisitions and releases."""
        lm = LockManager(host="localhost", port=9999)
        self.assertFalse(lm.use_redis)

        # Acquire lock
        acquired = lm.acquire_lock("resource-1", ttl_seconds=1, acquire_timeout=0.1)
        self.assertTrue(acquired)

        # Acquire second lock (should fail while held)
        second_acquired = lm.acquire_lock("resource-1", ttl_seconds=1, acquire_timeout=0.1)
        self.assertFalse(second_acquired)

        # Release lock
        self.assertTrue(lm.release_lock("resource-1"))
