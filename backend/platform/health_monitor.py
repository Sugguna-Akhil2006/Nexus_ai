"""Health Monitor tracking provider availability and error rates."""

from __future__ import annotations

from typing import Dict, Optional

from backend.platform.provider_manager import ProviderManager


class HealthMonitor:
    """Calculates provider health aggregates."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None) -> None:
        self.provider_mgr = provider_mgr or ProviderManager()

    def get_provider_health(self) -> Dict[str, Any]:
        """Gathers error rates and statuses of active providers."""
        providers = self.provider_mgr.list_providers()
        summary = {}
        for p in providers:
            summary[p.provider_id] = {
                "name": p.name,
                "status": p.health_status,
                "error_rate": p.error_rate,
                "is_active": p.is_active
            }
        return summary
class HealthMonitor:
    """Calculates provider health aggregates."""

    def __init__(self, provider_mgr: Optional[ProviderManager] = None) -> None:
        self.provider_mgr = provider_mgr or ProviderManager()

    def get_provider_health(self) -> Dict[str, Any]:
        """Gathers error rates and statuses of active providers."""
        providers = self.provider_mgr.list_providers()
        summary = {}
        for p in providers:
            summary[p.provider_id] = {
                "name": p.name,
                "status": p.health_status,
                "error_rate": p.error_rate,
                "is_active": p.is_active
            }
        return summary
