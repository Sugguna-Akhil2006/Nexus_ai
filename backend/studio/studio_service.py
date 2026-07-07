"""Studio Service coordinating inspections, configurations, and health dashboard."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.studio.workspace_manager import WorkspaceManager
from backend.studio.agent_inspector import AgentInspector
from backend.studio.workflow_inspector import WorkflowInspector
from backend.studio.execution_visualizer import ExecutionVisualizer
from backend.studio.memory_inspector import MemoryInspector
from backend.studio.provider_dashboard import ProviderDashboard
from backend.studio.plugin_manager import PluginManager
from backend.studio.prompt_library import PromptLibrary
from backend.studio.configuration_manager import ConfigurationManager
from backend.studio.health_dashboard import HealthDashboard
from backend.studio.project_generator import ProjectGenerator


class StudioService:
    """Central orchestrator facade for developer experience capabilities."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()
        
        self.workspace_mgr = WorkspaceManager()
        self.agent_ins = AgentInspector(self.registry)
        self.workflow_ins = WorkflowInspector()
        self.visualizer = ExecutionVisualizer()
        self.memory_ins = MemoryInspector()
        self.provider_dash = ProviderDashboard(self.registry)
        self.plugin_mgr = PluginManager(self.registry)
        self.prompt_lib = PromptLibrary(self.registry)
        self.config_mgr = ConfigurationManager(self.registry)
        self.health_dash = HealthDashboard(self.registry)
        self.generator = ProjectGenerator()

    def get_studio_health_status(self) -> Dict[str, str]:
        """Retrieves subsystem health indicators."""
        return self.health_dash.get_health_snapshot()

    def get_workspace_overview(self, workspace_id: str) -> Dict[str, Any]:
        """Compiles unified overview card for a developer workspace."""
        info = self.workspace_mgr.get_workspace_info(workspace_id)
        mem = self.memory_ins.get_memory_snapshot(workspace_id)
        
        return {
            "workspace_id": workspace_id,
            "name": info.name if info else "unknown",
            "active_jobs": info.active_jobs_count if info else 0,
            "memory_usage_bytes": mem.memory_usage_bytes,
            "knowledge_profile_keys": list(mem.knowledge_profile.keys())
        }
