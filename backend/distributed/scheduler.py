"""Scheduler - pluggable task-to-node assignment policies."""

from __future__ import annotations

import itertools
import threading
from abc import ABC, abstractmethod
from typing import List, Optional

from backend.distributed.models import DistributedTask, SchedulingPolicy, WorkerNode
from backend.distributed.worker_registry import WorkerRegistry


class BaseSchedulingPolicy(ABC):
    """Abstract base class for worker selection strategies."""

    @abstractmethod
    def select_node(self, task: DistributedTask, candidates: List[WorkerNode]) -> Optional[WorkerNode]:
        """Selects the best worker node for the given task.

        Args:
            task: Task to schedule.
            candidates: List of eligible online nodes.

        Returns:
            Selected WorkerNode or None if no suitable node exists.
        """


class LeastLoadedPolicy(BaseSchedulingPolicy):
    """Selects the node with the lowest composite load score."""

    def select_node(self, task: DistributedTask, candidates: List[WorkerNode]) -> Optional[WorkerNode]:
        if not candidates:
            return None
        return min(candidates, key=lambda n: n.resources.load_score)


class RoundRobinPolicy(BaseSchedulingPolicy):
    """Distributes tasks evenly across nodes in cyclic order."""

    def __init__(self) -> None:
        self._counter: itertools.count = itertools.count()
        self._lock = threading.Lock()

    def select_node(self, task: DistributedTask, candidates: List[WorkerNode]) -> Optional[WorkerNode]:
        if not candidates:
            return None
        with self._lock:
            idx = next(self._counter) % len(candidates)
        return candidates[idx]


class PriorityPolicy(BaseSchedulingPolicy):
    """Routes high-priority tasks to the most capable (least loaded) node."""

    def select_node(self, task: DistributedTask, candidates: List[WorkerNode]) -> Optional[WorkerNode]:
        if not candidates:
            return None
        # High priority tasks get the least loaded; low priority take highest load (backfill)
        if task.priority >= 7:
            return min(candidates, key=lambda n: n.resources.load_score)
        return max(candidates, key=lambda n: n.resources.load_score)


class CapabilityBasedPolicy(BaseSchedulingPolicy):
    """Selects nodes that satisfy the task's capability requirements."""

    def select_node(self, task: DistributedTask, candidates: List[WorkerNode]) -> Optional[WorkerNode]:
        if not candidates:
            return None
        if not task.required_capabilities:
            return min(candidates, key=lambda n: n.resources.load_score)

        eligible = [
            n for n in candidates
            if all(cap in n.capabilities for cap in task.required_capabilities)
        ]
        if not eligible:
            return None
        return min(eligible, key=lambda n: n.resources.load_score)


class Scheduler:
    """Routes distributed tasks to worker nodes using configurable policies.

    Args:
        registry: WorkerRegistry providing available nodes.
        policy: Default SchedulingPolicy enum value.
    """

    _POLICY_MAP = {
        SchedulingPolicy.LEAST_LOADED: LeastLoadedPolicy,
        SchedulingPolicy.ROUND_ROBIN: RoundRobinPolicy,
        SchedulingPolicy.PRIORITY: PriorityPolicy,
        SchedulingPolicy.CAPABILITY_BASED: CapabilityBasedPolicy,
    }

    def __init__(
        self,
        registry: WorkerRegistry,
        policy: SchedulingPolicy = SchedulingPolicy.LEAST_LOADED,
    ) -> None:
        self._registry = registry
        self._active_policy: BaseSchedulingPolicy = self._POLICY_MAP[policy]()
        self._lock = threading.Lock()

    def set_policy(self, policy: SchedulingPolicy) -> None:
        """Switches the active scheduling policy at runtime.

        Args:
            policy: New SchedulingPolicy to apply.
        """
        with self._lock:
            self._active_policy = self._POLICY_MAP[policy]()

    def assign(self, task: DistributedTask) -> Optional[WorkerNode]:
        """Selects and returns the best worker for the task.

        Args:
            task: DistributedTask requiring node assignment.

        Returns:
            Selected WorkerNode or None if no suitable node is available.
        """
        candidates = self._registry.list_online_nodes()
        with self._lock:
            node = self._active_policy.select_node(task, candidates)
        if node:
            task.assigned_node_id = node.node_id
        return node
