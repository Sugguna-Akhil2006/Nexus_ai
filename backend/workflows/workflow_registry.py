"""Thread-safe registry storing named WorkflowDefinition objects."""

import threading
from typing import Dict, List, Optional
from backend.workflows.models import WorkflowDefinition


class WorkflowRegistry:
    """Maintains a catalogue of registered workflow definitions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._store: Dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        """Adds or replaces a workflow definition in the registry.

        Args:
            definition: The ``WorkflowDefinition`` to store.
        """
        with self._lock:
            self._store[definition.workflow_id] = definition

    def get(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        """Retrieves a workflow definition by its ID.

        Args:
            workflow_id: The unique workflow identifier.

        Returns:
            The matching ``WorkflowDefinition`` or ``None``.
        """
        with self._lock:
            return self._store.get(workflow_id)

    def get_by_name(self, name: str) -> Optional[WorkflowDefinition]:
        """Retrieves the first workflow definition matching the given name.

        Args:
            name: The workflow name to search for.

        Returns:
            The matching ``WorkflowDefinition`` or ``None``.
        """
        with self._lock:
            for wf in self._store.values():
                if wf.name == name:
                    return wf
            return None

    def list_all(self) -> List[WorkflowDefinition]:
        """Returns all registered workflow definitions."""
        with self._lock:
            return list(self._store.values())

    def delete(self, workflow_id: str) -> bool:
        """Removes a workflow definition from the registry.

        Args:
            workflow_id: The ID of the workflow to remove.

        Returns:
            ``True`` if the workflow was found and removed, ``False`` otherwise.
        """
        with self._lock:
            if workflow_id in self._store:
                del self._store[workflow_id]
                return True
            return False
