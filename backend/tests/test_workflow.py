from datetime import datetime
import threading
import time
from typing import List
import unittest
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.execution.executor import Executor
from backend.execution.planner import ExecutionMode, ExecutionPlan, RetryPolicy
from backend.runtime.result import Result
from backend.runtime.task import Task
from backend.execution.task_queue import QueuePriority
from backend.workflow.workflow import (
    WorkflowEdge,
    WorkflowEngine,
    WorkflowNode,
    WorkflowStatus,
    WorkflowValidationError,
    WorkflowNotFoundError,
)


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestWorkflow(unittest.TestCase):
    """Suite of tests covering the Workflow Engine orchestration."""

    def setUp(self) -> None:
        self.engine = WorkflowEngine()
        with self.engine._lock:
            self.engine._workflows.clear()
            self.engine._workflow_statuses.clear()
            self.engine._definitions.clear()
        self.executor = Executor()
        with self.executor._lock:
            self.executor._handlers.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()

        # Default handler
        self.executor.register_handler("Task", lambda t: f"Run: {t.description}")

    def _create_node(self, node_id: str, desc: str, deps: List[str] = None) -> WorkflowNode:
        task = Task(description=desc)
        plan = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=5.0,
            dependencies=[],
            metadata={},
            estimated_cost=0.5,
            estimated_duration=1.0
        )
        return WorkflowNode(
            node_id=node_id,
            execution_plan=plan,
            dependencies=deps or []
        )

    def test_singleton(self) -> None:
        """Verifies that WorkflowEngine behaves as a singleton."""
        engine2 = WorkflowEngine()
        self.assertIs(self.engine, engine2)

    def test_workflow_validation_duplicate_nodes(self) -> None:
        """Verifies duplicate node IDs raise WorkflowValidationError."""
        n1 = self._create_node("NodeA", "Task A")
        n2 = self._create_node("NodeA", "Task A Duplicate")

        with self.assertRaises(WorkflowValidationError):
            self.engine.create_workflow("Duplicate Nodes", "Desc", [n1, n2], [])

    def test_workflow_validation_missing_dependency(self) -> None:
        """Verifies missing dependencies raise validation errors."""
        n1 = self._create_node("NodeA", "Task A", deps=["MissingNode"])
        with self.assertRaises(WorkflowValidationError):
            self.engine.create_workflow("Missing Dep", "Desc", [n1], [])

    def test_workflow_validation_circular_dependencies(self) -> None:
        """Verifies circular references raise validation errors."""
        n1 = self._create_node("NodeA", "Task A", deps=["NodeC"])
        n2 = self._create_node("NodeB", "Task B", deps=["NodeA"])
        n3 = self._create_node("NodeC", "Task C", deps=["NodeB"])

        with self.assertRaises(WorkflowValidationError):
            self.engine.create_workflow("Circular Ref", "Desc", [n1, n2, n3], [])

    def test_workflow_validation_orphan_nodes(self) -> None:
        """Verifies orphan node detection checks."""
        n1 = self._create_node("NodeA", "Task A")
        n2 = self._create_node("NodeB", "Task B")
        n3 = self._create_node("NodeC", "Task C")
        edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")

        # NodeC is completely disconnected (orphan) in a multi-node graph
        with self.assertRaises(WorkflowValidationError):
            self.engine.create_workflow("Orphan Nodes", "Desc", [n1, n2, n3], [edge])

    def test_successful_workflow_dag_execution(self) -> None:
        """Verifies concurrent/dependent successful nodes execution."""
        n1 = self._create_node("NodeA", "Task A")
        n2 = self._create_node("NodeB", "Task B")
        n3 = self._create_node("NodeC", "Task C", deps=["NodeA", "NodeB"])
        edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")

        workflow = self.engine.create_workflow(
            name="Success DAG",
            description="Parallel start, sequential dependency",
            nodes=[n1, n2, n3],
            edges=[edge]
        )

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        result = self.engine.execute(workflow)

        self.assertEqual(result.overall_status, WorkflowStatus.COMPLETED)
        self.assertEqual(len(result.node_results), 3)
        self.assertTrue(result.node_results["NodeC"].is_success())

        self.event_bus.dispatch_all()
        start_events = [e for e in receiver.events if e.payload["event_name"] == "workflow.started"]
        completed_events = [e for e in receiver.events if e.payload["event_name"] == "workflow.completed"]
        self.assertEqual(len(start_events), 1)
        self.assertEqual(len(completed_events), 1)

    def test_workflow_failure_propagation(self) -> None:
        """Verifies failing node prevents execution of downstream dependents."""
        def failing_handler(t: Task) -> None:
            raise ValueError("Forced test failure")

        self.executor.register_handler("FailingTask", failing_handler)

        n1 = self._create_node("NodeA", "FailingTask A")
        n2 = self._create_node("NodeB", "Task B", deps=["NodeA"])
        edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")

        workflow = self.engine.create_workflow(
            name="Failing DAG",
            description="Dependent fails",
            nodes=[n1, n2],
            edges=[edge]
        )

        result = self.engine.execute(workflow)

        self.assertEqual(result.overall_status, WorkflowStatus.FAILED)
        self.assertEqual(result.node_results["NodeA"].is_success(), False)
        # NodeB should never have completed successfully (or run at all, marked as failed/cancelled)
        self.assertEqual(result.node_results.get("NodeB"), None)

    def test_workflow_cancellation(self) -> None:
        """Verifies cancellation aborts execution of running workflows."""
        def slow_handler(t: Task) -> str:
            time.sleep(1.0)
            return "done"

        self.executor.register_handler("SlowTask", slow_handler)

        n1 = self._create_node("NodeA", "SlowTask A")
        n2 = self._create_node("NodeB", "Task B", deps=["NodeA"])
        edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")

        workflow = self.engine.create_workflow(
            name="Cancel DAG",
            description="Will cancel mid-execution",
            nodes=[n1, n2],
            edges=[edge]
        )

        exec_res = []

        def run_thread() -> None:
            res = self.engine.execute(workflow)
            exec_res.append(res)

        t = threading.Thread(target=run_thread)
        t.start()

        # Let it start
        time.sleep(0.1)

        # Signal cancellation
        success = self.engine.cancel(workflow.workflow_id)
        self.assertTrue(success)

        t.join()

        self.assertEqual(len(exec_res), 1)
        self.assertEqual(exec_res[0].overall_status, WorkflowStatus.CANCELLED)

    def test_pause_and_resume(self) -> None:
        """Verifies pause blocks downstream schedules until resume."""
        self.executor.register_handler("SlowPauseTask", lambda t: time.sleep(0.5) or "slow_ok")
        n1 = self._create_node("NodeA", "SlowPauseTask A")
        n2 = self._create_node("NodeB", "Task B", deps=["NodeA"])
        edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")

        workflow = self.engine.create_workflow(
            name="Pause Resume DAG",
            description="Pause mid-flow",
            nodes=[n1, n2],
            edges=[edge]
        )

        exec_res = []

        def run_thread() -> None:
            res = self.engine.execute(workflow)
            exec_res.append(res)

        t = threading.Thread(target=run_thread)
        t.start()

        # Let NodeA start running or finish
        time.sleep(0.1)

        # Trigger Pause
        paused = self.engine.pause(workflow.workflow_id)
        self.assertTrue(paused)
        self.assertEqual(self.engine.status(workflow.workflow_id), WorkflowStatus.PAUSED)

        # Let time pass - NodeB should NOT be execution complete yet
        time.sleep(0.3)

        # Resume
        resumed = self.engine.resume(workflow.workflow_id)
        self.assertTrue(resumed)
        self.assertEqual(self.engine.status(workflow.workflow_id), WorkflowStatus.RUNNING)

        t.join()

        self.assertEqual(len(exec_res), 1)
        self.assertEqual(exec_res[0].overall_status, WorkflowStatus.COMPLETED)
        self.assertTrue(exec_res[0].node_results["NodeB"].is_success())

    def test_status_missing_raises(self) -> None:
        """Verifies status calls raise WorkflowNotFoundError on missing IDs."""
        with self.assertRaises(WorkflowNotFoundError):
            self.engine.status(uuid.uuid4())

    def test_thread_safety_concurrency(self) -> None:
        """Verifies simultaneous execution of multiple workflow instances."""
        num_threads = 10
        workflows_per_thread = 5

        results = []
        results_lock = threading.Lock()

        def worker(thread_idx: int) -> None:
            for i in range(workflows_per_thread):
                n1 = self._create_node("NodeA", f"Task A {thread_idx} {i}")
                n2 = self._create_node("NodeB", f"Task B {thread_idx} {i}", deps=["NodeA"])
                edge = WorkflowEdge(source_node="NodeA", target_node="NodeB")
                workflow = self.engine.create_workflow(
                    name=f"Concurrent_{thread_idx}_{i}",
                    description="Desc",
                    nodes=[n1, n2],
                    edges=[edge]
                )
                res = self.engine.execute(workflow)
                with results_lock:
                    results.append(res)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), num_threads * workflows_per_thread)
        for res in results:
            self.assertEqual(res.overall_status, WorkflowStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
