"""Policy registry catalog storing and querying active system rules."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.policy.models import Policy, PolicyType


class PolicyRegistry:
    """Thread-safe catalog storing all active platform policies."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._policies: Dict[str, Policy] = {}

    def register(self, policy: Policy) -> None:
        """Saves or updates a policy in the registry."""
        with self._lock:
            self._policies[policy.policy_id] = policy

    def remove(self, policy_id: str) -> None:
        """Deletes a policy from the registry."""
        with self._lock:
            self._policies.pop(policy_id, None)

    def get(self, policy_id: str) -> Optional[Policy]:
        """Fetches a policy by ID."""
        with self._lock:
            return self._policies.get(policy_id)

    def list_all(self) -> List[Policy]:
        """Returns all registered policies."""
        with self._lock:
            return list(self._policies.values())

    def list_by_type(self, policy_type: PolicyType) -> List[Policy]:
        """Filters registered policies by type."""
        with self._lock:
            return [p for p in self._policies.values() if p.policy_type == policy_type]

    def list_by_target(self, target_id: str) -> List[Policy]:
        """Filters registered policies by target target_id."""
        with self._lock:
            return [
                p for p in self._policies.values()
                if p.target_id == target_id or p.target_id == "*"
            ]

    def clear(self) -> None:
        """Clear all active policies."""
        with self._lock:
            self._policies.clear()
