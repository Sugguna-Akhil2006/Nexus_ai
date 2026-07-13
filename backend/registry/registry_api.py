"""FastAPI router exposing capability registry control plane endpoints."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityType
from backend.registry.registry_health import RegistryHealthMonitor
from backend.registry.registry_dashboard import RegistryDashboard


router = APIRouter(prefix="/registry", tags=["AI Capability Registry"])


def get_registry() -> CapabilityRegistry:
    return CapabilityRegistry()


def serialize_cap(c) -> Dict[str, Any]:
    return {
        "capability_id": c.capability_id,
        "name": c.name,
        "type": c.type.value,
        "version": c.version,
        "description": c.description,
        "author": c.author,
        "tags": c.tags,
        "dependencies": c.dependencies,
        "compatibilities": c.compatibilities,
        "is_deprecated": c.is_deprecated,
        "upgrade_path": c.upgrade_path,
        "health": {
            "is_available": c.health.is_available,
            "latency_ms": c.health.latency_ms,
            "error_rate": c.health.error_rate,
            "last_execution": c.health.last_execution,
            "usage_count": c.health.usage_count,
            "failure_count": c.health.failure_count
        }
    }


@router.get("/modules")
def get_registry_modules(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    caps = reg.list_capabilities(CapabilityType.MODULE)
    return {"modules": [serialize_cap(c) for c in caps]}


@router.get("/providers")
def get_registry_providers(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    llm = reg.list_capabilities(CapabilityType.LLM_PROVIDER)
    embed = reg.list_capabilities(CapabilityType.EMBEDDING_PROVIDER)
    return {
        "llm_providers": [serialize_cap(c) for c in llm],
        "embedding_providers": [serialize_cap(c) for c in embed]
    }


@router.get("/workflows")
def get_registry_workflows(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    caps = reg.list_capabilities(CapabilityType.WORKFLOW)
    return {"workflows": [serialize_cap(c) for c in caps]}


@router.get("/tools")
def get_registry_tools(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    tools = reg.list_capabilities(CapabilityType.TOOL)
    plugins = reg.list_capabilities(CapabilityType.PLUGIN)
    return {
        "tools": [serialize_cap(c) for c in tools],
        "plugins": [serialize_cap(c) for c in plugins]
    }


@router.get("/prompts")
def get_registry_prompts(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    caps = reg.list_capabilities(CapabilityType.PROMPT)
    return {"prompts": [serialize_cap(c) for c in caps]}


@router.get("/health")
def get_registry_health(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    monitor = RegistryHealthMonitor(reg)
    return monitor.check_overall_health()


@router.get("/dashboard")
def get_registry_dashboard(
    reg: CapabilityRegistry = Depends(get_registry)
) -> Dict[str, Any]:
    dashboard = RegistryDashboard(reg)
    return dashboard.get_dashboard_data()


from backend.studio.plugin_manager import PluginManager
from pydantic import BaseModel

class InstallPluginReq(BaseModel):
    plugin_id: str
    name: str
    version: str
    description: str

@router.get("/plugins")
def list_plugins(reg: CapabilityRegistry = Depends(get_registry)):
    from dataclasses import asdict
    pm = PluginManager(reg)
    plugins = pm.list_plugins()
    return {"plugins": [asdict(p) for p in plugins]}

@router.post("/plugins/install")
def install_plugin(req: InstallPluginReq, reg: CapabilityRegistry = Depends(get_registry)):
    from backend.registry.registry_models import CapabilityMetadata
    meta = CapabilityMetadata(
        capability_id=req.plugin_id,
        name=req.name,
        type=CapabilityType.PLUGIN,
        version=req.version,
        description=req.description,
        author="nexus",
        tags=[],
        dependencies=[]
    )
    pm = PluginManager(reg)
    success = pm.install_plugin(meta)
    return {"success": success}

@router.post("/plugins/{plugin_id}/uninstall")
def uninstall_plugin(plugin_id: str, reg: CapabilityRegistry = Depends(get_registry)):
    pm = PluginManager(reg)
    success = pm.remove_plugin(plugin_id)
    return {"success": success}

@router.post("/plugins/{plugin_id}/toggle")
def toggle_plugin(plugin_id: str, enabled: bool, reg: CapabilityRegistry = Depends(get_registry)):
    pm = PluginManager(reg)
    success = pm.set_enabled_status(plugin_id, enabled)
    return {"success": success}
