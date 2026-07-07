"""Admin Service coordinating monitoring modules."""

from typing import Any, Dict, List, Optional

from backend.admin.system_monitor import SystemMonitor
from backend.admin.metrics_dashboard import MetricsDashboard
from backend.admin.audit_logs import AuditLogsManager
from backend.admin.notification_center import NotificationCenter
from backend.admin.health_monitor import HealthMonitor
from backend.admin.usage_statistics import UsageStatisticsService


class AdminService:
    """Enterprise Admin service aggregating monitoring and administration logic."""

    def __init__(self) -> None:
        self.system = SystemMonitor()
        self.metrics = MetricsDashboard()
        self.audit = AuditLogsManager()
        self.notifications = NotificationCenter()
        self.health = HealthMonitor()
        self.usage = UsageStatisticsService()

    def get_system_report(self) -> Dict[str, Any]:
        """Gathers system stats report."""
        return self.system.get_system_stats()

    def get_metrics_dashboard(self) -> Dict[str, Any]:
        """Gathers performance metrics telemetry."""
        return self.metrics.get_metrics_summary()

    def get_health_report(self) -> Dict[str, Any]:
        """Performs health check on subsystems."""
        return self.health.perform_checks()

    def get_users_list(self) -> Dict[str, Any]:
        """Compiles usage statistics."""
        return self.usage.get_usage_statistics()
