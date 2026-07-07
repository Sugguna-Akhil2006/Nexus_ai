"""Agent Inspector retrieving structural configuration and execution histories of registered agents."""

from __future__ import annotations

from typing import List, Optional

from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityType
from backend.studio.models import AgentInspection


class AgentInspector:
    """Inspects platform agent capabilities and runtime histories."""

    def __init__(self, registry: Optional[CapabilityRegistry] = None) -> None:
        self.registry = registry or CapabilityRegistry()

    def inspect_agent(self, agent_id: str) -> Optional[AgentInspection]:
        """Resolves capability metadata and compiles agent details card."""
        cap = self.registry.get_capability(agent_id)
        if not cap or cap.type != CapabilityType.AGENT:
            # Fallback to search if prefix omitted
            cap = self.registry.get_capability(f"agent-{agent_id.lower()}")
            if not cap:
                return None

        # Build execution log history list from extra metadata fields
        execution_logs = cap.extra.get("execution_logs", [
            {"execution_id": "exec-001", "status": "completed", "timestamp": cap.health.last_execution}
        ])

        return AgentInspection(
            agent_id=cap.capability_id,
            name=cap.name,
            capabilities=cap.tags,
            health_status="healthy" if cap.health.is_available else "degraded",
            current_tasks=[],
            execution_history=execution_logs,
            dependencies=cap.dependencies
        )

    def list_inspectable_agents(self) -> List[AgentInspection]:
        """Lists details for every inspectable system agent."""
        caps = self.registry.list_capabilities(CapabilityType.AGENT)
        inspected = []
        for c in caps:
            inspection = self.inspect_agent(c.capability_id)
            if inspection:
                inspected.append(inspection)
        return inspected
