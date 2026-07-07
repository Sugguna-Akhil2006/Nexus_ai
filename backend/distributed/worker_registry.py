"""WorkerRegistry - thread-safe registration and discovery of cluster worker nodes."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.distributed.models import NodeStatus, WorkerNode
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.logger import StructuredLogger


class WorkerRegistry:
    """Thread-safe registry tracking all registered cluster worker nodes.

    Workers register on startup, update heartbeats during operation, and
    are automatically marked offline when heartbeats lapse.
    """

    def __init__(self) -> None:
        self._nodes: Dict[str, WorkerNode] = {}
        self._lock = threading.RLock()
        self._event_bus = EventBus()
        self._logger = StructuredLogger()

    def register(self, node: WorkerNode) -> None:
        """Registers a new worker node.

        Args:
            node: WorkerNode instance to register.

        Raises:
            ValueError: If a node with the same ID is already registered.
        """
        with self._lock:
            if node.node_id in self._nodes:
                # Re-registration (rejoin): update status and reset
                existing = self._nodes[node.node_id]
                existing.status = NodeStatus.ONLINE
                existing.address = node.address
                existing.capabilities = node.capabilities
                self._logger.info(f"Worker '{node.node_id}' re-joined the cluster.")
            else:
                self._nodes[node.node_id] = node
                self._logger.info(f"Worker '{node.node_id}' registered at {node.address}.")

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkerRegistry",
            payload={"event": "worker.registered", "node_id": node.node_id},
        ))

    def deregister(self, node_id: str) -> None:
        """Removes a worker node from the registry.

        Args:
            node_id: Identifier of the node to remove.
        """
        with self._lock:
            if node_id in self._nodes:
                del self._nodes[node_id]
                self._logger.info(f"Worker '{node_id}' deregistered.")

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkerRegistry",
            payload={"event": "worker.deregistered", "node_id": node_id},
        ))

    def get_node(self, node_id: str) -> Optional[WorkerNode]:
        """Retrieves a node by ID.

        Args:
            node_id: Node identifier.

        Returns:
            WorkerNode or None if not found.
        """
        with self._lock:
            return self._nodes.get(node_id)

    def list_nodes(self, status: Optional[NodeStatus] = None) -> List[WorkerNode]:
        """Lists registered nodes, optionally filtered by status.

        Args:
            status: Optional NodeStatus filter.

        Returns:
            List of matching WorkerNode instances.
        """
        with self._lock:
            nodes = list(self._nodes.values())
        if status is not None:
            nodes = [n for n in nodes if n.status == status]
        return nodes

    def list_online_nodes(self) -> List[WorkerNode]:
        """Returns all currently online worker nodes."""
        return self.list_nodes(status=NodeStatus.ONLINE)

    def mark_offline(self, node_id: str) -> None:
        """Marks a node as offline (e.g. after missed heartbeats).

        Args:
            node_id: Node identifier.
        """
        with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node.status = NodeStatus.OFFLINE
                self._logger.warning(f"Worker '{node_id}' marked OFFLINE.")

        self._event_bus.publish(Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WorkerRegistry",
            payload={"event": "worker.offline", "node_id": node_id},
        ))

    def update_resources(self, node_id: str, resources: "ResourceProfile") -> None:  # type: ignore[name-defined]
        """Updates the resource profile of a registered node.

        Args:
            node_id: Node identifier.
            resources: Updated ResourceProfile.
        """
        with self._lock:
            node = self._nodes.get(node_id)
            if node:
                node.resources = resources

    def count(self) -> int:
        """Returns total number of registered nodes."""
        with self._lock:
            return len(self._nodes)

    def clear(self) -> None:
        """Removes all registered nodes (primarily for tests)."""
        with self._lock:
            self._nodes.clear()
