"""Resource limiter managing timeouts, memory usage, and thread limits."""

from __future__ import annotations

from backend.sandbox.models import SandboxConfig


class ResourceLimiter:
    """Enforces execution limits (timeouts, max memory bounds) cross-platform."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config

    def check_limits(self, duration_ms: float, memory_bytes: int) -> bool:
        """Returns True if the metrics are within limits.

        Args:
            duration_ms: Run duration.
            memory_bytes: RAM footprint.

        Returns:
            True if resource limits are respected.
        """
        # Duration limits
        if duration_ms > (self.config.timeout_seconds * 1000.0):
            return False

        # Memory limits
        mem_mb = memory_bytes / (1024.0 * 1024.0)
        if mem_mb > self.config.max_memory_mb:
            return False

        return True
