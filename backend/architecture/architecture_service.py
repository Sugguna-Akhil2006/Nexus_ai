"""Architecture service providing unified access to catalogs, dependencies, sequences, and handbooks."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.architecture.api_catalog import APICatalog
from backend.architecture.component_diagram import ComponentDiagram
from backend.architecture.decision_log import DecisionLog
from backend.architecture.dependency_mapper import DependencyMapper
from backend.architecture.event_catalog import EventCatalog
from backend.architecture.models import APIEndpointInfo, DecisionRecord, DependencyGraph, ModuleMetadata, SequenceFlow
from backend.architecture.module_catalog import ModuleCatalog
from backend.architecture.sequence_generator import SequenceGenerator
from backend.architecture.workflow_catalog import WorkflowCatalog


class ArchitectureService:
    """The central manager (facade) coordinating system documentation extraction."""

    _instance: Optional["ArchitectureService"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "ArchitectureService":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self.modules = ModuleCatalog()
        self.decisions = DecisionLog()
        self._initialized = True

    def get_modules(self) -> List[ModuleMetadata]:
        """Returns catalog entries for all registered intelligence modules."""
        return self.modules.get_catalog()

    def get_dependency_graph(self) -> DependencyGraph:
        """Generates the component interaction layout."""
        return DependencyMapper.get_map()

    def get_sequence(self, scenario: str) -> SequenceFlow:
        """Compiles sequence diagram steps in Mermaid format."""
        return SequenceGenerator.generate_flow(scenario)

    def get_decisions(self) -> List[DecisionRecord]:
        """Returns all ADR entries."""
        return self.decisions.list_decisions()

    def get_api_catalog(self) -> List[APIEndpointInfo]:
        """Returns catalog mappings of endpoints."""
        return APICatalog.get_catalog()

    def get_event_catalog(self) -> List[Dict[str, str]]:
        """Returns catalog mappings of event types."""
        return EventCatalog.get_events()

    def get_workflow_catalog(self) -> List[Dict[str, Any]]:
        """Returns catalog mappings of execution workflows."""
        return WorkflowCatalog.get_workflows()

    def get_component_diagram(self) -> str:
        """Returns the full system package layout diagram."""
        return ComponentDiagram.compile_diagram()
