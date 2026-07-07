"""Distributed Runtime data models for nodes, tasks, cluster state, and resources."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NodeStatus(Enum):
    """Lifecycle status of a cluster worker node."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    DRAINING = "draining"


class DistributedTaskStatus(Enum):
    """Status of a task within the distributed execution system."""

    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class SchedulingPolicy(Enum):
    """Supported worker selection scheduling strategies."""

    LEAST_LOADED = "least_loaded"
    ROUND_ROBIN = "round_robin"
    PRIORITY = "priority"
    CAPABILITY_BASED = "capability_based"


@dataclass
class ResourceProfile:
    """Available and consumed resource metrics for a worker node.

    Attributes:
        cpu_cores: Total CPU core count.
        cpu_usage_percent: Current CPU utilisation percentage (0–100).
        memory_total_mb: Total memory in megabytes.
        memory_used_mb: Used memory in megabytes.
        gpu_count: Number of available GPU devices.
        gpu_usage_percent: GPU utilisation percentage.
        queue_size: Number of tasks currently queued on the node.
        current_load: Normalised load score (0.0–1.0).
    """

    cpu_cores: int = 4
    cpu_usage_percent: float = 0.0
    memory_total_mb: int = 8192
    memory_used_mb: int = 0
    gpu_count: int = 0
    gpu_usage_percent: float = 0.0
    queue_size: int = 0
    current_load: float = 0.0

    @property
    def memory_free_mb(self) -> int:
        """Returns free memory in megabytes."""
        return self.memory_total_mb - self.memory_used_mb

    @property
    def load_score(self) -> float:
        """Composite load score combining CPU, memory, and queue pressure."""
        cpu_norm = self.cpu_usage_percent / 100.0
        mem_norm = self.memory_used_mb / max(self.memory_total_mb, 1)
        queue_norm = min(self.queue_size / 100.0, 1.0)
        return round((cpu_norm * 0.4) + (mem_norm * 0.3) + (queue_norm * 0.3), 4)


@dataclass
class WorkerNode:
    """Represents a registered distributed worker node.

    Attributes:
        node_id: Unique identifier for the node.
        address: Network address (e.g. ``"worker-1:8080"``).
        capabilities: Set of task capability tags the node supports.
        status: Current node lifecycle status.
        resources: Runtime resource metrics.
        registered_at: Registration timestamp.
        last_heartbeat: Most recent heartbeat timestamp.
        metadata: Arbitrary node metadata.
    """

    node_id: str
    address: str
    capabilities: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.ONLINE
    resources: ResourceProfile = field(default_factory=ResourceProfile)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DistributedTask:
    """A unit of work dispatched across the cluster.

    Attributes:
        task_id: Unique task identifier.
        workflow_id: Parent workflow identifier.
        payload: Task input data dictionary.
        priority: Scheduling priority (higher = processed first).
        required_capabilities: Capabilities the executing node must support.
        status: Current task lifecycle status.
        assigned_node_id: Node assigned to execute the task.
        created_at: Task creation timestamp.
        started_at: Execution start timestamp.
        completed_at: Execution completion timestamp.
        attempts: Number of execution attempts made.
        max_retries: Maximum allowed retry attempts.
        result: Task output data.
        error: Error message if the task failed.
        timeout_seconds: Maximum allowed execution duration.
    """

    task_id: str
    workflow_id: str
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: int = 5
    required_capabilities: List[str] = field(default_factory=list)
    status: DistributedTaskStatus = DistributedTaskStatus.QUEUED
    assigned_node_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0
    max_retries: int = 3
    result: Optional[Any] = None
    error: Optional[str] = None
    timeout_seconds: float = 60.0


@dataclass
class ClusterSnapshot:
    """Point-in-time snapshot of the cluster state.

    Attributes:
        snapshot_id: Unique snapshot identifier.
        timestamp: Capture timestamp.
        total_nodes: Total registered node count.
        online_nodes: Number of online nodes.
        total_tasks_queued: Aggregated queue depth across all nodes.
        total_tasks_running: Count of actively running tasks.
        cluster_load: Average normalised load across online nodes.
        nodes: List of node summaries.
    """

    snapshot_id: str
    timestamp: datetime
    total_nodes: int = 0
    online_nodes: int = 0
    total_tasks_queued: int = 0
    total_tasks_running: int = 0
    cluster_load: float = 0.0
    nodes: List[Dict[str, Any]] = field(default_factory=list)
