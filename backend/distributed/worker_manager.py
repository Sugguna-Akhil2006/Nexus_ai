"""WorkerManager - lifecycle management for individual cluster worker nodes."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from backend.distributed.models import NodeStatus, ResourceProfile, WorkerNode
from backend.distributed.worker_registry import WorkerRegistry
from backend.distributed.heartbeat import HeartbeatMonitor
from backend.distributed.failover import FailoverManager
from backend.runtime.logger import StructuredLogger


class WorkerManager:
    """Manages the full lifecycle of distributed worker nodes.

    Handles registration, heartbeat management, resource updates,
    graceful draining, and re-registration after recovery.

    Args:
        registry: WorkerRegistry for node storage.
        failover: FailoverManager to trigger on node failure.
        heartbeat_timeout_seconds: Seconds before a silent node is declared offline.
    """

    def __init__(
        self,
        registry: WorkerRegistry,
        failover: FailoverManager,
        heartbeat_timeout_seconds: float = 30.0,
    ) -> None:
        self._registry = registry
        self._failover = failover
        self._logger = StructuredLogger()
        self._monitor = HeartbeatMonitor(
            registry=registry,
            timeout_seconds=heartbeat_timeout_seconds,
            poll_interval_seconds=5.0,
            on_node_offline=self._on_node_offline,
        )

    def start_monitoring(self) -> None:
        """Starts the background heartbeat monitor."""
        self._monitor.start()

    def stop_monitoring(self) -> None:
        """Stops the background heartbeat monitor."""
        self._monitor.stop()

    def register_worker(
        self,
        address: str,
        capabilities: Optional[List[str]] = None,
        node_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> WorkerNode:
        """Registers a new worker and returns its node descriptor.

        Args:
            address: Network address of the worker.
            capabilities: Task capability tags the worker supports.
            node_id: Optional explicit node ID (auto-generated if omitted).
            metadata: Optional metadata dictionary.

        Returns:
            Registered WorkerNode instance.
        """
        node = WorkerNode(
            node_id=node_id or f"node-{uuid.uuid4().hex[:8]}",
            address=address,
            capabilities=capabilities or [],
            status=NodeStatus.ONLINE,
            registered_at=datetime.utcnow(),
            last_heartbeat=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._registry.register(node)
        return node

    def heartbeat(self, node_id: str, resources: Optional[ResourceProfile] = None) -> None:
        """Records a heartbeat from a worker, optionally updating resource metrics.

        Args:
            node_id: Worker node identifier.
            resources: Optional updated ResourceProfile.
        """
        self._monitor.record_heartbeat(node_id)
        if resources:
            self._registry.update_resources(node_id, resources)

    def drain_worker(self, node_id: str) -> None:
        """Puts a worker into draining mode (stops receiving new tasks).

        Args:
            node_id: Worker node identifier.
        """
        node = self._registry.get_node(node_id)
        if node:
            node.status = NodeStatus.DRAINING
            self._logger.info(f"Worker '{node_id}' set to DRAINING.")

    def remove_worker(self, node_id: str) -> None:
        """Forcibly removes a worker from the cluster.

        Args:
            node_id: Worker node identifier.
        """
        self._registry.deregister(node_id)

    def get_worker(self, node_id: str) -> Optional[WorkerNode]:
        """Returns a worker node by ID.

        Args:
            node_id: Worker node identifier.

        Returns:
            WorkerNode or None.
        """
        return self._registry.get_node(node_id)

    def list_workers(self) -> List[WorkerNode]:
        """Returns all registered workers regardless of status."""
        return self._registry.list_nodes()

    def _on_node_offline(self, node_id: str) -> None:
        """Callback invoked when a node is detected as offline."""
        self._logger.warning(f"WorkerManager: triggering failover for offline node '{node_id}'.")
        self._failover.handle_node_failure(node_id)
