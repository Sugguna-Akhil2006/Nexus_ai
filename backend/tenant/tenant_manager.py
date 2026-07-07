"""Tenant manager coordinating organizations registration, limits, and context."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.tenant.models import Tenant, TenantLimits, TenantSettings, TenantStatus
from backend.tenant.tenant_events import TenantEvents
from backend.tenant.tenant_limits import TenantLimitsValidator
from backend.tenant.tenant_registry import TenantRegistry
from backend.tenant.tenant_settings import TenantSettingsValidator


class TenantManager:
    """The central manager (facade) coordinating multi-tenant configurations."""

    _instance: Optional["TenantManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "TenantManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        self.registry = TenantRegistry(db_path)
        self.events = TenantEvents()
        self._initialized = True

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        settings: Optional[TenantSettings] = None,
        limits: Optional[TenantLimits] = None,
    ) -> Tenant:
        """Registers a new tenant and triggers a system event log."""
        t = self.registry.create_tenant(tenant_id, name, settings, limits)
        self.events.publish_created(tenant_id, name)
        return t

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Retrieves tenant details by ID."""
        return self.registry.get_tenant(tenant_id)

    def suspend_tenant(self, tenant_id: str) -> bool:
        """Suspends a tenant's operations (sets status = suspended) and publishes events."""
        t = self.registry.get_tenant(tenant_id)
        if t:
            t.status = TenantStatus.SUSPENDED
            self.registry.save_tenant(t)
            self.events.publish_suspended(tenant_id)
            return True
        return False

    def archive_tenant(self, tenant_id: str) -> bool:
        """Archives a tenant's operations (sets status = archived)."""
        t = self.registry.get_tenant(tenant_id)
        if t:
            t.status = TenantStatus.ARCHIVED
            self.registry.save_tenant(t)
            return True
        return False

    def list_active_tenants(self) -> List[Tenant]:
        """Lists active (non-suspended, non-archived) tenants."""
        return [t for t in self.registry.list_tenants() if t.status == TenantStatus.ACTIVE]
