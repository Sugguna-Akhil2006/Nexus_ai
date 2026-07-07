"""NodeHealth - health scoring and degradation detection for worker nodes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from backend.distributed.models import NodeStatus, WorkerNode


@dataclass(frozen=True)
class NodeHealthReport:
    """Immutable health assessment for a single node.

    Attributes:
        node_id: Node identifier.
        status: Current NodeStatus.
        load_score: Composite load score (0.0–1.0; lower is healthier).
        memory_free_mb: Available memory in megabytes.
        cpu_usage_percent: Current CPU utilisation.
        queue_size: Pending tasks on this node.
        is_healthy: True if the node is considered healthy.
        assessed_at: Timestamp of this assessment.
    """

    node_id: str
    status: NodeStatus
    load_score: float
    memory_free_mb: int
    cpu_usage_percent: float
    queue_size: int
    is_healthy: bool
    assessed_at: datetime


class NodeHealthMonitor:
    """Evaluates and reports health status for worker nodes.

    A node is considered degraded if:
    - CPU usage exceeds 90 %
    - Memory free < 256 MB
    - Queue depth > 50 tasks
    """

    CPU_DEGRADED_THRESHOLD = 90.0
    MEMORY_DEGRADED_THRESHOLD_MB = 256
    QUEUE_DEGRADED_THRESHOLD = 50

    def assess(self, node: WorkerNode) -> NodeHealthReport:
        """Produces a NodeHealthReport for the given worker.

        Args:
            node: WorkerNode to evaluate.

        Returns:
            NodeHealthReport for the node.
        """
        r = node.resources
        is_degraded = (
            r.cpu_usage_percent >= self.CPU_DEGRADED_THRESHOLD
            or r.memory_free_mb < self.MEMORY_DEGRADED_THRESHOLD_MB
            or r.queue_size > self.QUEUE_DEGRADED_THRESHOLD
        )
        is_healthy = node.status == NodeStatus.ONLINE and not is_degraded

        return NodeHealthReport(
            node_id=node.node_id,
            status=node.status,
            load_score=r.load_score,
            memory_free_mb=r.memory_free_mb,
            cpu_usage_percent=r.cpu_usage_percent,
            queue_size=r.queue_size,
            is_healthy=is_healthy,
            assessed_at=datetime.utcnow(),
        )

    def assess_all(self, nodes: List[WorkerNode]) -> List[NodeHealthReport]:
        """Assesses all provided nodes.

        Args:
            nodes: List of WorkerNode instances.

        Returns:
            List of NodeHealthReport instances.
        """
        return [self.assess(n) for n in nodes]
