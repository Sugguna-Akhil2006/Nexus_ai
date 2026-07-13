"""Cache manager implementing Redis caching with thread-safe local in-memory fallback."""

import json
import threading
import time
from typing import Any, Dict, Optional


class CacheManager:
    """Manages cache reads, writes, and expirations using Redis or thread-safe local memory."""

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0) -> None:
        """Initializes cache managers. Automatically falls back if connection fails.

        Args:
            host: Redis host.
            port: Redis port.
            db: Redis DB index.
        """
        self.host = host
        self.port = port
        self.db = db
        self.use_redis = False
        
        # In-memory fallback
        self._memory_cache: Dict[str, tuple[Any, float]] = {}
        self._lock = threading.Lock()

        try:
            import redis
            self.redis_client = redis.Redis(host=host, port=port, db=db, socket_timeout=2.0)
            self.redis_client.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False

    def get(self, key: str) -> Optional[Any]:
        """Retrieves raw or deserialized cached value.

        Args:
            key: Target cache key.
        """
        if self.use_redis:
            try:
                val = self.redis_client.get(key)
                if val:
                    return json.loads(val.decode("utf-8"))
                return None
            except Exception:
                pass  # Fallback to local memory on transient failure

        with self._lock:
            cached = self._memory_cache.get(key)
            if not cached:
                return None
            val, expires_at = cached
            if expires_at and time.time() > expires_at:
                del self._memory_cache[key]
                return None
            return val

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None) -> bool:
        """Writes serialized value to cache.

        Args:
            key: Target key.
            value: Cache value.
            expire_seconds: TTL duration.
        """
        if self.use_redis:
            try:
                serialized = json.dumps(value)
                if expire_seconds:
                    self.redis_client.setex(key, expire_seconds, serialized)
                else:
                    self.redis_client.set(key, serialized)
                return True
            except Exception:
                pass

        expires_at = time.time() + expire_seconds if expire_seconds else None
        with self._lock:
            self._memory_cache[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        """Removes key from cache."""
        if self.use_redis:
            try:
                self.redis_client.delete(key)
                return True
            except Exception:
                pass

        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False
            
    def clear(self) -> None:
        """Purges the entire cache."""
        if self.use_redis:
            try:
                self.redis_client.flushdb()
            except Exception:
                pass
        with self._lock:
            self._memory_cache.clear()
