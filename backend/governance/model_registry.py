"""Model registry tracking LLM deployments, versions, and deprecations."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.governance.models import ApprovalState, ModelRecord


class ModelRegistry:
    """Thread-safe store cataloging approved models and deployment states."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._models: Dict[str, ModelRecord] = {}

    def register(self, model: ModelRecord) -> None:
        """Saves a model details registry entry."""
        with self._lock:
            self._models[model.model_id] = model

    def get(self, model_id: str) -> Optional[ModelRecord]:
        """Fetches a model registry entry by ID."""
        with self._lock:
            return self._models.get(model_id)

    def list_all(self) -> List[ModelRecord]:
        """Returns all registered model records."""
        with self._lock:
            return list(self._models.values())

    def update_state(self, model_id: str, state: ApprovalState) -> None:
        """Updates the approval lifecycle state of a registered model."""
        with self._lock:
            if model_id in self._models:
                self._models[model_id].approval_state = state
                if state == ApprovalState.DEPRECATED:
                    self._models[model_id].status = "deprecated"

    def clear(self) -> None:
        """Clear model records."""
        with self._lock:
            self._models.clear()
