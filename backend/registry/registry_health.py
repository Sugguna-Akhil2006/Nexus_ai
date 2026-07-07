"""Registry health monitor tracking capability status metrics."""

from __future__ import annotations

from typing import Dict, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityHealth


class RegistryHealthMonitor:
    """Monitors capability status, error rates, latency bounds and executions."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def get_health_status(self, capability_id: str) -> Optional[CapabilityHealth]:
        """Retrieves health metrics for a specific capability."""
        cap = self.registry.get_capability(capability_id)
        if cap:
            return cap.health
        return None

    def check_overall_health(self) -> Dict[str, Any]:
        """Compiles health dashboard of all registered capabilities."""
        caps = self.registry.list_capabilities()
        total = len(caps)
        available = sum(1 for c in caps if c.health.is_available)
        avg_latency = (
            sum(c.health.latency_ms for c in caps) / total if total > 0 else 0.0
        )
        avg_errors = (
            sum(c.health.error_rate for c in caps) / total if total > 0 else 0.0
        )

        return {
            "status": "healthy" if available == total else "degraded",
            "total_registered": total,
            "available_count": available,
            "degraded_count": total - available,
            "average_latency_ms": round(avg_latency, 2),
            "average_error_rate": round(avg_errors, 4)
        }
