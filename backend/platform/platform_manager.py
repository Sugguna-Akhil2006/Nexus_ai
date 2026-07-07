"""Platform Manager admin controller aggregating sub-managers for unified visibility."""

from __future__ import annotations

from typing import Any, Dict

from backend.platform.provider_manager import ProviderManager
from backend.platform.model_manager import ModelManager
from backend.platform.routing_engine import RoutingEngine
from backend.platform.quota_manager import QuotaManager
from backend.platform.usage_analytics import UsageAnalytics
from backend.platform.cost_manager import CostManager
from backend.platform.capacity_planner import CapacityPlanner
from backend.platform.failover_manager import FailoverManager
from backend.platform.health_monitor import HealthMonitor
from backend.platform.configuration_center import ConfigurationCenter
from backend.platform.feature_flags import FeatureFlagsManager


class PlatformManager:
    """Central operations center aggregating all admin dashboards and routing controls."""

    def __init__(self) -> None:
        self.provider_mgr = ProviderManager()
        self.model_mgr = ModelManager()
        self.routing_engine = RoutingEngine(self.provider_mgr, self.model_mgr)
        self.quota_mgr = QuotaManager()
        self.analytics = UsageAnalytics()
        self.cost_mgr = CostManager()
        self.capacity_planner = CapacityPlanner(self.analytics)
        self.failover_mgr = FailoverManager(self.provider_mgr, self.model_mgr)
        self.health_monitor = HealthMonitor(self.provider_mgr)
        self.config_center = ConfigurationCenter()
        self.feature_flags = FeatureFlagsManager()

    def get_admin_dashboard_metrics(self) -> Dict[str, Any]:
        """Compiles health, costs, routing distribution and quotas metrics."""
        summary = self.analytics.get_metrics_summary()
        dist = self.analytics.get_distributions()
        health = self.health_monitor.get_provider_health()

        return {
            "active_models_count": len([m for m in self.model_mgr.list_models() if m.is_active]),
            "provider_health": health,
            "usage_summary": {
                "total_requests": summary.total_requests,
                "total_tokens": summary.total_tokens,
                "total_cost": summary.total_cost,
                "average_latency_ms": summary.average_latency_ms,
                "error_rate": summary.error_count / summary.total_requests if summary.total_requests else 0.0
            },
            "routing_statistics": dist.get("model_distribution", {}),
            "provider_distribution": dist.get("provider_distribution", {}),
            "flags": {
                "mcp_enabled": self.feature_flags.is_feature_enabled("mcp-integration")
            }
        }
