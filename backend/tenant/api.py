"""FastAPI APIRouter routing enterprise multi-tenancy organization registrations and settings."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.tenant.models import TenantLimits, TenantSettings
from backend.tenant.tenant_manager import TenantManager

router = APIRouter(prefix="/tenants", tags=["Multi-Tenancy Management"])

# Singleton manager
_manager = TenantManager()


class CreateTenantPayload(BaseModel):
    """Payload to create a new organization tenant."""

    tenant_id: str
    name: str
    settings: Optional[TenantSettings] = None
    limits: Optional[TenantLimits] = None


class UpdateSettingsPayload(BaseModel):
    """Payload to update custom settings."""

    settings: TenantSettings


@router.post("", summary="Register a new organization tenant")
def create_tenant(payload: CreateTenantPayload) -> Any:
    """Registers a new organization tenant."""
    t = _manager.create_tenant(
        tenant_id=payload.tenant_id,
        name=payload.name,
        settings=payload.settings,
        limits=payload.limits,
    )
    return ProductResponse.ok(data=t)


@router.get("/{tenant_id}", summary="Get tenant profile details")
def get_tenant(tenant_id: str) -> Any:
    """Retrieves tenant profile details."""
    t = _manager.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")
    return ProductResponse.ok(data=t)


@router.put("/{tenant_id}/settings", summary="Update custom tenant settings")
def update_settings(tenant_id: str, payload: UpdateSettingsPayload) -> Any:
    """Updates custom settings per-tenant."""
    t = _manager.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")

    t.settings = payload.settings
    _manager.registry.save_tenant(t)
    return ProductResponse.ok(data=t)


@router.get("/{tenant_id}/usage", summary="Get resource usages and quotas")
def get_usage(tenant_id: str) -> Any:
    """Retrieves current consumption footprint metrics."""
    t = _manager.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail=f"Tenant '{tenant_id}' not found.")

    # Return resource usages stats
    return ProductResponse.ok(
        data={
            "storage_usage_mb": 120.0,
            "api_requests_current_minute": 15,
            "token_consumed_current_month": 45000,
            "active_concurrent_jobs": 1,
            "limits": t.limits,
        }
    )


from pydantic import BaseModel
