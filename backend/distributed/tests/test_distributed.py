"""Comprehensive tests for the Nexus Distributed Runtime."""

from __future__ import annotations

import concurrent.futures
import time
import unittest

from backend.distributed.cluster_manager import ClusterManager
from backend.distributed.models import (
    DistributedTask,
    DistributedTaskStatus,
    ResourceProfile,
    SchedulingPolicy,
)
from backend.distributed.distributed_queue import DistributedQueue
from backend.distributed.worker_registry import WorkerRegistry
from backend.distributed.scheduler import Scheduler
from backend.distributed.failover import FailoverManager
from backend.distributed.execution_coordinator import ExecutionCoordinator
from backend.distributed.node_health import NodeHealthMonitor


class TestWorkerRegistry(unittest.TestCase):
    """Worker registration, discovery, and lifecycle tests."""

    def setUp(self) -> None:
        self.cluster = ClusterManager()

    def test_register_and_discover_worker(self) -> None:
        node = self.cluster.register_worker("worker-1:8080", capabilities=["gpu", "nlp"])
        self.assertEqual(node.capabilities, ["gpu", "nlp"])
        self.assertIn(node.node_id, [n.node_id for n in self.cluster.registry.list_nodes()])

    def test_duplicate_registration_rejoins(self) -> None:
        n1 = self.cluster.register_worker("worker-a:8080", node_id="w-fixed")
        n2 = self.cluster.register_worker("worker-a-new:8080", node_id="w-fixed")
        # Should have only one entry (re-registration)
        nodes = [n for n in self.cluster.registry.list_nodes() if n.node_id == "w-fixed"]
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].address, "worker-a-new:8080")

    def test_remove_worker(self) -> None:
        node = self.cluster.register_worker("worker-2:8080")
        self.cluster.remove_worker(node.node_id)
        self.assertIsNone(self.cluster.registry.get_node(node.node_id))

    def test_heartbeat_updates_resources(self) -> None:
        node = self.cluster.register_worker("worker-3:8080")
        resources = ResourceProfile(cpu_usage_percent=55.0, memory_used_mb=2048, queue_size=10)
        self.cluster.heartbeat(node.node_id, resources)
        updated = self.cluster.registry.get_node(node.node_id)
        self.assertEqual(updated.resources.cpu_usage_percent, 55.0)


class TestDistributedQueue(unittest.TestCase):
    """Priority queue ordering, cancellation, and requeue tests."""

    def setUp(self) -> None:
        self.queue = DistributedQueue()

    def _make_task(self, priority: int = 5, workflow_id: str = "wf-1") -> DistributedTask:
        import uuid
        return DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id=workflow_id, priority=priority)

    def test_priority_ordering(self) -> None:
        self.queue.enqueue(self._make_task(priority=3))
        self.queue.enqueue(self._make_task(priority=9))
        self.queue.enqueue(self._make_task(priority=1))
        t1 = self.queue.dequeue()
        t2 = self.queue.dequeue()
        self.assertEqual(t1.priority, 9)
        self.assertEqual(t2.priority, 3)

    def test_cancel_queued_task(self) -> None:
        task = self._make_task()
        self.queue.enqueue(task)
        result = self.queue.cancel(task.task_id)
        self.assertTrue(result)
        self.assertEqual(self.queue.get_task(task.task_id).status, DistributedTaskStatus.CANCELLED)

    def test_requeue_increments_attempts(self) -> None:
        task = self._make_task()
        task.attempts = 1
        self.queue.requeue(task)
        retrieved = self.queue.get_task(task.task_id)
        self.assertEqual(retrieved.attempts, 2)
        self.assertEqual(retrieved.status, DistributedTaskStatus.RETRYING)

    def test_queue_depth(self) -> None:
        for _ in range(5):
            self.queue.enqueue(self._make_task())
        self.assertEqual(self.queue.depth(), 5)


class TestScheduler(unittest.TestCase):
    """Scheduling policy selection tests."""

    def setUp(self) -> None:
        self.registry = WorkerRegistry()

    def _add_node(self, node_id: str, load: float = 0.3, caps: list = None):
        from backend.distributed.models import NodeStatus, WorkerNode
        node = WorkerNode(node_id=node_id, address=f"{node_id}:8080", capabilities=caps or [])
        node.resources.cpu_usage_percent = load * 100
        self.registry.register(node)
        return node

    def _make_task(self, caps: list = None) -> DistributedTask:
        import uuid
        return DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id="wf-1", required_capabilities=caps or [])

    def test_least_loaded_selects_lightest(self) -> None:
        n1 = self._add_node("n1", load=0.8)
        n2 = self._add_node("n2", load=0.2)
        scheduler = Scheduler(self.registry, SchedulingPolicy.LEAST_LOADED)
        selected = scheduler.assign(self._make_task())
        self.assertEqual(selected.node_id, "n2")

    def test_capability_based_filters_correctly(self) -> None:
        self._add_node("n-gpu", caps=["gpu", "nlp"])
        self._add_node("n-cpu", caps=["nlp"])
        scheduler = Scheduler(self.registry, SchedulingPolicy.CAPABILITY_BASED)
        task = self._make_task(caps=["gpu"])
        selected = scheduler.assign(task)
        self.assertEqual(selected.node_id, "n-gpu")

    def test_round_robin_cycles(self) -> None:
        self._add_node("r1")
        self._add_node("r2")
        import uuid
        scheduler = Scheduler(self.registry, SchedulingPolicy.ROUND_ROBIN)
        results = set()
        for _ in range(4):
            t = DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id="wf")
            node = scheduler.assign(t)
            results.add(node.node_id)
        self.assertEqual(results, {"r1", "r2"})

    def test_no_nodes_returns_none(self) -> None:
        scheduler = Scheduler(self.registry, SchedulingPolicy.LEAST_LOADED)
        import uuid
        task = DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id="wf")
        self.assertIsNone(scheduler.assign(task))


class TestFailoverManager(unittest.TestCase):
    """Failover detection and task rescheduling tests."""

    def setUp(self) -> None:
        self.queue = DistributedQueue()
        self.registry = WorkerRegistry()
        self.failover = FailoverManager(self.queue, self.registry)

    def _make_running_task(self, node_id: str) -> DistributedTask:
        import uuid
        task = DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id="wf-1", max_retries=3)
        task.status = DistributedTaskStatus.RUNNING
        task.assigned_node_id = node_id
        task.attempts = 1
        self.queue._tasks[task.task_id] = task
        return task

    def test_failover_requeues_running_tasks(self) -> None:
        task = self._make_running_task("dead-node")
        requeued = self.failover.handle_node_failure("dead-node")
        self.assertEqual(len(requeued), 1)
        self.assertEqual(requeued[0].task_id, task.task_id)
        self.assertEqual(requeued[0].status, DistributedTaskStatus.RETRYING)

    def test_exhausted_tasks_marked_failed(self) -> None:
        task = self._make_running_task("dead-node")
        task.attempts = 3  # equals max_retries=3 → no more retries
        self.failover.handle_node_failure("dead-node")
        self.assertEqual(task.status, DistributedTaskStatus.FAILED)


class TestExecutionCoordinator(unittest.TestCase):
    """Workflow state and progress tracking tests."""

    def setUp(self) -> None:
        self.queue = DistributedQueue()
        self.coord = ExecutionCoordinator(self.queue)

    def _make_task(self, status: DistributedTaskStatus) -> DistributedTask:
        import uuid
        task = DistributedTask(task_id=f"t-{uuid.uuid4().hex[:4]}", workflow_id="wf-test")
        task.status = status
        self.queue._tasks[task.task_id] = task
        return task

    def test_register_workflow(self) -> None:
        state = self.coord.register_workflow("wf-1", metadata={"owner": "alice"})
        self.assertEqual(state.workflow_id, "wf-1")
        self.assertEqual(state.metadata["owner"], "alice")

    def test_progress_reporting(self) -> None:
        self.coord.register_workflow("wf-2")
        t1 = self._make_task(DistributedTaskStatus.COMPLETED)
        t2 = self._make_task(DistributedTaskStatus.RUNNING)
        self.coord.add_task_to_workflow("wf-2", t1)
        self.coord.add_task_to_workflow("wf-2", t2)

        progress = self.coord.get_workflow_progress("wf-2")
        self.assertEqual(progress["total_tasks"], 2)
        self.assertEqual(progress["progress_percent"], 50.0)

    def test_workflow_status_update(self) -> None:
        self.coord.register_workflow("wf-3")
        self.coord.update_workflow_status("wf-3", "completed")
        workflows = {w["workflow_id"]: w for w in self.coord.list_workflows()}
        self.assertEqual(workflows["wf-3"]["status"], "completed")


class TestNodeHealth(unittest.TestCase):
    """Node health scoring and degradation detection tests."""

    def test_healthy_node(self) -> None:
        from backend.distributed.models import WorkerNode
        monitor = NodeHealthMonitor()
        node = WorkerNode(node_id="n1", address="n1:8080")
        node.resources.cpu_usage_percent = 30.0
        report = monitor.assess(node)
        self.assertTrue(report.is_healthy)

    def test_degraded_on_high_cpu(self) -> None:
        from backend.distributed.models import WorkerNode
        monitor = NodeHealthMonitor()
        node = WorkerNode(node_id="n2", address="n2:8080")
        node.resources.cpu_usage_percent = 95.0
        report = monitor.assess(node)
        self.assertFalse(report.is_healthy)


class TestClusterManagerIntegration(unittest.TestCase):
    """End-to-end cluster submission, execution, and snapshot tests."""

    def test_submit_and_snapshot(self) -> None:
        cluster = ClusterManager()
        cluster.register_worker("w1:8080")
        cluster.register_worker("w2:8080")

        task_id = cluster.submit_task("wf-integration", payload={"data": "test"}, priority=8)
        self.assertTrue(task_id.startswith("task-"))

        snap = cluster.get_cluster_snapshot()
        self.assertEqual(snap.total_nodes, 2)
        self.assertEqual(snap.online_nodes, 2)
        self.assertGreaterEqual(snap.total_tasks_queued, 1)

    def test_workflow_progress_empty(self) -> None:
        cluster = ClusterManager()
        cluster.coordinator.register_workflow("wf-empty")
        progress = cluster.get_workflow_progress("wf-empty")
        self.assertEqual(progress["total_tasks"], 0)
        self.assertEqual(progress["progress_percent"], 0.0)


class TestConcurrentSubmissions(unittest.TestCase):
    """Stress and concurrency tests."""

    def test_concurrent_task_submission(self) -> None:
        cluster = ClusterManager()
        cluster.register_worker("stress-w1:8080")
        cluster.register_worker("stress-w2:8080")

        submitted = []
        errors = []

        def submit(i: int) -> None:
            try:
                tid = cluster.submit_task(f"wf-stress-{i % 5}", payload={"i": i}, priority=i % 10)
                submitted.append(tid)
            except Exception as e:
                errors.append(str(e))

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(submit, i) for i in range(50)]
            concurrent.futures.wait(futures)

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(submitted), 50)
        # Queue should have all 50 tasks
        self.assertEqual(cluster.queue.depth(), 50)


if __name__ == "__main__":
    unittest.main()
