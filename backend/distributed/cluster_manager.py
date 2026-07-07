"""ClusterManager - top-level facade orchestrating the Distributed Runtime."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from backend.distributed.models import (
    ClusterSnapshot,
    DistributedTask,
    NodeStatus,
    ResourceProfile,
    SchedulingPolicy,
    WorkerNode,
)
from backend.distributed.worker_registry import WorkerRegistry
from backend.distributed.worker_manager import WorkerManager
from backend.distributed.distributed_queue import DistributedQueue
from backend.distributed.scheduler import Scheduler
from backend.distributed.task_dispatcher import TaskDispatcher
from backend.distributed.failover import FailoverManager
from backend.distributed.execution_coordinator import ExecutionCoordinator
from backend.distributed.node_health import NodeHealthMonitor
from backend.distributed.resource_allocator import ResourceAllocator
from backend.runtime.logger import StructuredLogger


class ClusterManager:
    """Central administrative facade for the Nexus Distributed Runtime.

    Provides a unified interface for:
    - Worker registration and lifecycle management.
    - Task submission and distributed execution.
    - Cluster health monitoring and snapshots.
    - Scheduling policy configuration.

    The Distributed Runtime is backward-compatible with the standard
    Nexus execution engine; distributed features are opt-in.

    Example::

        cluster = ClusterManager()
        cluster.start()

        node = cluster.register_worker("worker-1:8080", capabilities=["gpu"])
        task_id = cluster.submit_task(workflow_id="wf-1", payload={"data": "..."})

        snapshot = cluster.get_cluster_snapshot()
    """

    def __init__(
        self,
        scheduling_policy: SchedulingPolicy = SchedulingPolicy.LEAST_LOADED,
        heartbeat_timeout_seconds: float = 30.0,
        execute_fn: Optional[Callable[[DistributedTask, WorkerNode], None]] = None,
    ) -> None:
        # Core subsystems
        self.registry = WorkerRegistry()
        self.queue = DistributedQueue()
        self.scheduler = Scheduler(self.registry, scheduling_policy)
        self.failover = FailoverManager(self.queue, self.registry)
        self.worker_manager = WorkerManager(self.registry, self.failover, heartbeat_timeout_seconds)
        self.dispatcher = TaskDispatcher(self.queue, self.scheduler, execute_fn)
        self.coordinator = ExecutionCoordinator(self.queue)
        self.health_monitor = NodeHealthMonitor()
        self.allocator = ResourceAllocator(self.registry)
        self._logger = StructuredLogger()

    # ──────────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ──────────────────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Starts background services (heartbeat monitor, task dispatcher)."""
        self.worker_manager.start_monitoring()
        self.dispatcher.start()
        self._logger.info("ClusterManager started.")

    def stop(self) -> None:
        """Gracefully stops all background services."""
        self.dispatcher.stop()
        self.worker_manager.stop_monitoring()
        self._logger.info("ClusterManager stopped.")

    # ──────────────────────────────────────────────────────────────────────────
    # Worker Management
    # ──────────────────────────────────────────────────────────────────────────

    def register_worker(
        self,
        address: str,
        capabilities: Optional[List[str]] = None,
        node_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> WorkerNode:
        """Registers a new worker node with the cluster.

        Args:
            address: Worker network address.
            capabilities: Supported task capability tags.
            node_id: Optional explicit node ID.
            metadata: Optional metadata.

        Returns:
            Registered WorkerNode.
        """
        return self.worker_manager.register_worker(address, capabilities, node_id, metadata)

    def heartbeat(self, node_id: str, resources: Optional[ResourceProfile] = None) -> None:
        """Records a heartbeat from the given worker.

        Args:
            node_id: Worker node identifier.
            resources: Optional resource profile update.
        """
        self.worker_manager.heartbeat(node_id, resources)

    def remove_worker(self, node_id: str) -> None:
        """Removes a worker from the cluster.

        Args:
            node_id: Node identifier to remove.
        """
        self.worker_manager.remove_worker(node_id)

    # ──────────────────────────────────────────────────────────────────────────
    # Task Execution
    # ──────────────────────────────────────────────────────────────────────────

    def submit_task(
        self,
        workflow_id: str,
        payload: Optional[Dict[str, Any]] = None,
        priority: int = 5,
        required_capabilities: Optional[List[str]] = None,
        max_retries: int = 3,
        timeout_seconds: float = 60.0,
    ) -> str:
        """Submits a task to the distributed queue.

        Args:
            workflow_id: Parent workflow identifier.
            payload: Task input data.
            priority: Scheduling priority (1–10; 10 = highest).
            required_capabilities: Capability tags required on the worker.
            max_retries: Maximum retry attempts.
            timeout_seconds: Execution timeout.

        Returns:
            Generated task_id string.
        """
        task = DistributedTask(
            task_id=f"task-{uuid.uuid4().hex[:8]}",
            workflow_id=workflow_id,
            payload=payload or {},
            priority=priority,
            required_capabilities=required_capabilities or [],
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
        )

        # Register workflow if not already tracked
        if not self.coordinator._workflows.get(workflow_id):
            self.coordinator.register_workflow(workflow_id)

        self.coordinator.add_task_to_workflow(workflow_id, task)
        self.queue.enqueue(task)
        return task.task_id

    def set_scheduling_policy(self, policy: SchedulingPolicy) -> None:
        """Changes the active scheduling policy.

        Args:
            policy: New SchedulingPolicy value.
        """
        self.scheduler.set_policy(policy)

    # ──────────────────────────────────────────────────────────────────────────
    # Observability
    # ──────────────────────────────────────────────────────────────────────────

    def get_cluster_snapshot(self) -> ClusterSnapshot:
        """Returns a point-in-time snapshot of the full cluster state.

        Returns:
            ClusterSnapshot with node counts, queue depth, and load metrics.
        """
        online_nodes = self.registry.list_online_nodes()
        all_nodes = self.registry.list_nodes()
        health_reports = self.health_monitor.assess_all(online_nodes)

        avg_load = (
            sum(r.load_score for r in health_reports) / len(health_reports)
            if health_reports else 0.0
        )

        running = sum(1 for t in self.queue.list_all() if t.status.value == "running")

        return ClusterSnapshot(
            snapshot_id=f"snap-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.utcnow(),
            total_nodes=len(all_nodes),
            online_nodes=len(online_nodes),
            total_tasks_queued=self.queue.depth(),
            total_tasks_running=running,
            cluster_load=round(avg_load, 4),
            nodes=[
                {
                    "node_id": n.node_id,
                    "address": n.address,
                    "status": n.status.value,
                    "load_score": n.resources.load_score,
                    "queue_size": n.resources.queue_size,
                }
                for n in all_nodes
            ],
        )

    def get_workflow_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Returns task completion progress for a workflow.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Progress summary dictionary.
        """
        return self.coordinator.get_workflow_progress(workflow_id)

    def list_active_tasks(self) -> List[DistributedTask]:
        """Returns all currently running tasks across the cluster."""
        return self.dispatcher.list_active_tasks()

    def clear(self) -> None:
        """Resets all cluster state (primarily for tests)."""
        self.queue.clear()
        self.registry.clear()
        self.coordinator.clear()
