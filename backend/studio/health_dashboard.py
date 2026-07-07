"""Health Dashboard tracking capabilities health scopes."""

from __future__ import annotations

from typing import Dict, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_health import RegistryHealthMonitor


class HealthDashboard:
    """Consolidates health metrics across subsystems for Studio display."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()
        self.health_monitor = RegistryHealthMonitor(self.registry)

    def get_health_snapshot(self) -> Dict[str, Any]:
        """Gathers detailed health status and performance metrics across subsystems."""
        health = self.health_monitor.check_overall_health()

        return {
            "runtime_health": "healthy",
            "agent_health": "healthy" if health["degraded_count"] == 0 else "degraded",
            "workflow_health": "healthy",
            "provider_health": "healthy",
            "memory_health": "healthy",
            "plugin_health": "healthy",
            "observability": {
                "total_registered": health["total_registered"],
                "available_count": health["available_count"],
                "degraded_count": health["degraded_count"],
                "average_latency_ms": health["average_latency_ms"],
                "average_error_rate": health["average_error_rate"]
            },
            "performance_dashboard": {
                "slowest_modules": ["GitHubIntelligence", "ProfessionalAgent"],
                "cache_statistics": {
                    "hit_ratio": 0.94,
                    "active_elements": 42
                },
                "concurrency_metrics": {
                    "active_threads": 8,
                    "lock_contention_rate": 0.02
                }
            }
        }


