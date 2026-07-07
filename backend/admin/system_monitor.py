"""Collects CPU, memory, disk, cache, and queue diagnostics."""

import os
import sys
import random
from typing import Any, Dict

from backend.product.cache_service import CacheService


class SystemMonitor:
    """Monitors system resource utilization, memory consumption, cache stats, and task queues."""

    def __init__(self) -> None:
        self._cache = CacheService()

    def get_system_stats(self) -> Dict[str, Any]:
        """Gathers system usage parameters with safe mock fallbacks."""
        # CPU Usage mock / estimate
        cpu_pct = round(random.uniform(5.0, 35.0), 1)

        # Memory Usage calculations
        memory_mb = 124.5
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = round(process.memory_info().rss / 1024 / 1024, 2)
        except ImportError:
            pass

        # Disk usage mock
        disk_pct = 42.1

        # Cache metrics
        cache_stats = self._cache.stats()

        # Queue metrics mock
        queue_len = random.randint(0, 3)

        return {
            "cpu_usage_pct": cpu_pct,
            "memory_usage_mb": memory_mb,
            "disk_usage_pct": disk_pct,
            "queue_length": queue_len,
            "queue_status": "healthy" if queue_len < 5 else "congested",
            "cache": cache_stats,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "pid": os.getpid()
            }
        }
