"""Event catalog documenting event-bus and streaming notification types."""

from __future__ import annotations

from typing import Dict, List


class EventCatalog:
    """Structures descriptions and schemas for all system events."""

    @staticmethod
    def get_events() -> List[Dict[str, str]]:
        """Returns the list of system event bus types and descriptions."""
        return [
            {
                "event_type": "ANALYSIS_STARTED",
                "source": "Gateway",
                "description": "Triggered when a new user query begins processing.",
            },
            {
                "event_type": "ANALYSIS_COMPLETED",
                "source": "ExecutionOrchestrator",
                "description": "Triggered when a query execution completes successfully.",
            },
            {
                "event_type": "ANALYSIS_FAILED",
                "source": "ExecutionOrchestrator",
                "description": "Triggered when a query execution fails or raises errors.",
            },
            {
                "event_type": "TASK_STARTED",
                "source": "WorkflowEngine",
                "description": "Triggered when an individual workflow task starts executing.",
            },
            {
                "event_type": "TASK_COMPLETED",
                "source": "WorkflowEngine",
                "description": "Triggered when an individual workflow task completes.",
            },
        ]
DefinitionPath = "event_catalog.py"
