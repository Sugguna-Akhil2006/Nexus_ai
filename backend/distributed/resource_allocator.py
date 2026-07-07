"""ResourceAllocator - tracks and manages node resource consumption."""

from __future__ import annotations

import threading
from typing import Dict, Optional

from backend.distributed.models import ResourceProfile, WorkerNode
from backend.distributed.worker_registry import WorkerRegistry


class ResourceAllocator:
    """Tracks resource consumption across worker nodes and enforces capacity.

    Resource updates flow from worker heartbeat payloads. The allocator
    maintains a local cache of the latest profiles and exposes
    capacity-aware queries.
    """

    def __init__(self, registry: WorkerRegistry) -> None:
        self._registry = registry
        self._lock = threading.RLock()

    def update_node_resources(self, node_id: str, profile: ResourceProfile) -> None:
        """Updates the resource profile for a specific node.

        Args:
            node_id: Node identifier.
            profile: Latest ResourceProfile snapshot.
        """
        with self._lock:
            self._registry.update_resources(node_id, profile)

    def get_resource_profile(self, node_id: str) -> Optional[ResourceProfile]:
        """Returns the current resource profile for a node.

        Args:
            node_id: Node identifier.

        Returns:
            ResourceProfile or None if not found.
        """
        node = self._registry.get_node(node_id)
        return node.resources if node else None

    def get_least_loaded_node(self, required_capabilities: Optional[list] = None) -> Optional[WorkerNode]:
        """Returns the online node with the lowest composite load score.

        Args:
            required_capabilities: Optional list of capability tags the node must support.

        Returns:
            WorkerNode with minimum load score, or None if no eligible nodes.
        """
        with self._lock:
            candidates = self._registry.list_online_nodes()

        if required_capabilities:
            candidates = [
                n for n in candidates
                if all(c in n.capabilities for c in required_capabilities)
            ]

        if not candidates:
            return None

        return min(candidates, key=lambda n: n.resources.load_score)

    def get_estimated_completion_ms(self, node_id: str, task_cpu_estimate_ms: float = 100.0) -> float:
        """Rough estimate of when a new task would complete on the node.

        Args:
            node_id: Node identifier.
            task_cpu_estimate_ms: Estimated task CPU time in milliseconds.

        Returns:
            Estimated completion time offset in milliseconds.
        """
        profile = self.get_resource_profile(node_id)
        if not profile:
            return float("inf")
        load_factor = max(profile.load_score, 0.01)
        return task_cpu_estimate_ms / (1.0 - load_factor + 0.01) + (profile.queue_size * task_cpu_estimate_ms)
