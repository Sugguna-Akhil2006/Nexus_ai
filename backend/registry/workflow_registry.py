"""Workflow Registry managing discovery and listing of execution pipelines."""

from __future__ import annotations

from typing import Optional

from backend.api.sqlite_mock import DBStorage
from backend.registry.capability_registry import CapabilityRegistry
from backend.registry.registry_models import CapabilityMetadata, CapabilityType


class WorkflowRegistry:
    """Discovers and manages workflow capabilities."""

    def __init__(self, cap_registry: Optional[CapabilityRegistry] = None) -> None:
        self.cap_registry = cap_registry or CapabilityRegistry()
        self._db = DBStorage()

    def discover_workflows(self) -> None:
        """Discovers registered workflow definitions from the sqlite database and publishes them."""
        conn = self._db._get_connection()
        try:
            rows = conn.execute("SELECT * FROM workflow_definitions").fetchall()
            for r in rows:
                self.cap_registry.register_capability(CapabilityMetadata(
                    capability_id=f"workflow-{r['definition_id']}",
                    name=r["name"],
                    type=CapabilityType.WORKFLOW,
                    version="1.0.0",
                    description=r["description"] or "Workflow Automation execution definition.",
                    tags=["workflow", "pipeline", "automation"]
                ))
        except Exception:
            pass
        finally:
            conn.close()
