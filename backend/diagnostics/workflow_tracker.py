"""Workflow tracker recording execution step results, workflow state, and graph outcomes."""

from __future__ import annotations

import threading
from typing import Any, Dict, List, Optional


class WorkflowTracker:
    """Tracks active multi-module workflow runs and their corresponding graph steps."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._workflow_statuses: Dict[str, str] = {}  # request_id -> status
        self._workflow_details: Dict[str, Dict[str, Any]] = {}

    def start_workflow(self, request_id: str, details: Dict[str, Any]) -> None:
        """Logs the initialization of a workflow graph run."""
        with self._lock:
            self._workflow_statuses[request_id] = "running"
            self._workflow_details[request_id] = details

    def complete_workflow(self, request_id: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Sets workflow state to completed."""
        with self._lock:
            self._workflow_statuses[request_id] = "completed"
            if details:
                self._workflow_details[request_id].update(details)

    def fail_workflow(self, request_id: str, error_msg: str) -> None:
        """Sets workflow state to failed with error descriptions."""
        with self._lock:
            self._workflow_statuses[request_id] = "failed"
            if request_id in self._workflow_details:
                self._workflow_details[request_id]["error"] = error_msg

    def get_status(self, request_id: str) -> Optional[str]:
        """Returns the status of a workflow run."""
        with self._lock:
            return self._workflow_statuses.get(request_id)

    def get_details(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Returns details for a workflow."""
        with self._lock:
            return self._workflow_details.get(request_id)
