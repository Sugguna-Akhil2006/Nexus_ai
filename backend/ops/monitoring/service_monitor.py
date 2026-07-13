"""Aggregates multiple metrics and health monitors into consolidated telemetry."""

import time
from typing import Dict, Any

from backend.ops.monitoring.health_monitor import HealthMonitor
from backend.ops.monitoring.resource_monitor import ResourceMonitor


class ServiceMonitor:
    """Consolidates resource telemetry and dependencies connectivity status."""

    def __init__(self) -> None:
        """Initializes dependencies."""
        self.health = HealthMonitor()
        self.resources = ResourceMonitor()

    def get_summary(self) -> Dict[str, Any]:
        """Runs checks returning status summary.

        Returns:
            Status summary dictionary.
        """
        db = self.health.check_database()
        res = self.resources.get_system_metrics()

        return {
            "status": "healthy" if db["status"] == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "database": db,
            "resources": res
        }
