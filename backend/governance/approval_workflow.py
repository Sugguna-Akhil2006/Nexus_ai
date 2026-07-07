"""Approval workflows routing high-risk actions to administrator queues."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.governance.models import ApprovalState


class ApprovalWorkflow:
    """Manages manual approval tickets for deploying or deprecated models."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # model_id -> ApprovalState
        self._tickets: Dict[str, ApprovalState] = {}

    def submit(self, model_id: str) -> None:
        """Submits a model approval ticket."""
        with self._lock:
            self._tickets[model_id] = ApprovalState.PENDING

    def get_status(self, model_id: str) -> ApprovalState:
        """Fetches status of the ticket."""
        with self._lock:
            return self._tickets.get(model_id, ApprovalState.APPROVED)

    def approve(self, model_id: str) -> None:
        """Approves a pending ticket."""
        with self._lock:
            self._tickets[model_id] = ApprovalState.APPROVED

    def reject(self, model_id: str) -> None:
        """Rejects a pending ticket."""
        with self._lock:
            self._tickets[model_id] = ApprovalState.REJECTED

    def clear(self) -> None:
        """Wipes the workflow tickets."""
        with self._lock:
            self._tickets.clear()
