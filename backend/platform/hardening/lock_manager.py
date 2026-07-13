"""Distributed lock manager supporting Redis lock keys and thread-safe local lock fallbacks."""

import threading
import time
from typing import Dict, Optional


class LockManager:
    """Manages acquiring and releasing execution locks."""

    def __init__(self, host: str = "localhost", port: int = 6379) -> None:
        """Initializes lock manager. Fallback to in-memory locks on connection failure."""
        self.use_redis = False
        self._local_locks: Dict[str, threading.Lock] = {}
        self._local_lock = threading.Lock()

        try:
            import redis
            self.redis_client = redis.Redis(host=host, port=port, socket_timeout=2.0)
            self.redis_client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def acquire_lock(self, lock_key: str, ttl_seconds: int = 10, acquire_timeout: float = 5.0) -> bool:
        """Attempts to acquire a lock by key.

        Args:
            lock_key: Lock identifier.
            ttl_seconds: Auto-expire duration.
            acquire_timeout: Block wait time.
        """
        start_time = time.time()
        if self.use_redis:
            while True:
                try:
                    # SET with NX (not exists) and PX (millisecond TTL)
                    acquired = self.redis_client.set(
                        f"lock:{lock_key}",
                        "1",
                        nx=True,
                        ex=ttl_seconds
                    )
                    if acquired:
                        return True
                except Exception:
                    pass

                if time.time() - start_time > acquire_timeout:
                    return False
                time.sleep(0.05)

        # In-memory fallback
        with self._local_lock:
            if lock_key not in self._local_locks:
                self._local_locks[lock_key] = threading.Lock()
            lock = self._local_locks[lock_key]

        return lock.acquire(timeout=acquire_timeout)

    def release_lock(self, lock_key: str) -> bool:
        """Releases the lock.

        Args:
            lock_key: Lock key.
        """
        if self.use_redis:
            try:
                self.redis_client.delete(f"lock:{lock_key}")
                return True
            except Exception:
                pass

        # In-memory release
        with self._local_lock:
            lock = self._local_locks.get(lock_key)
            if not lock:
                return False
            try:
                lock.release()
                return True
            except RuntimeError:
                # Lock wasn't acquired by this thread
                return False
