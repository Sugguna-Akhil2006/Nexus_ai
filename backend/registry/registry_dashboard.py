"""Registry Dashboard compiling dashboard statistics for registry control plane display."""

from __future__ import annotations

from typing import Any, Dict

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityType
from backend.registry.registry_health import RegistryHealthMonitor


class RegistryDashboard:
    """Aggregates registry statistics for developer dashboard display."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()
        self.health_monitor = RegistryHealthMonitor(self.registry)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Compiles registration totals, health, and statistics."""
        caps = self.registry.list_capabilities()
        health = self.health_monitor.check_overall_health()

        counts = {
            "modules": sum(1 for c in caps if c.type == CapabilityType.MODULE),
            "providers": sum(
                1 for c in caps
                if c.type in (CapabilityType.LLM_PROVIDER, CapabilityType.EMBEDDING_PROVIDER)
            ),
            "plugins": sum(
                1 for c in caps
                if c.type in (CapabilityType.PLUGIN, CapabilityType.TOOL)
            ),
            "workflows": sum(1 for c in caps if c.type == CapabilityType.WORKFLOW)
        }

        # Calculate total usage and failure stats from health logs
        total_usage = sum(c.health.usage_count for c in caps)
        total_failures = sum(c.health.failure_count for c in caps)

        return {
            "registered_modules_count": counts["modules"],
            "available_providers_count": counts["providers"],
            "installed_plugins_count": counts["plugins"],
            "available_workflows_count": counts["workflows"],
            "overall_health_status": health["status"],
            "average_system_latency_ms": health["average_latency_ms"],
            "average_system_error_rate": health["average_error_rate"],
            "usage_statistics": {
                "total_executions": total_usage,
                "total_failures": total_failures,
                "success_rate": (
                    round((total_usage - total_failures) / total_usage, 4)
                    if total_usage > 0 else 1.0
                )
            }
        }
