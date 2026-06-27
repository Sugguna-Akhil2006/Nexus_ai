import threading
from typing import Any, List
import unittest
import uuid

from core.event import Event, EventBus, EventType
from core.exceptions import TaskValidationError
from core.planner import (
    ExecutionMode,
    ExecutionPlan,
    Planner,
    RetryPolicy,
)
from core.task import Task
from core.task_queue import QueuePriority


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestPlanner(unittest.TestCase):
    """Suite of tests covering the Execution Planner class."""

    def setUp(self) -> None:
        self.planner = Planner()
        self.event_bus = EventBus()
        self.event_bus.clear()

    def test_task_estimates(self) -> None:
        """Verifies estimation calculation math for cost and duration."""
        task = Task(description="Calculate math")
        cost = self.planner.estimate_cost(task)
        duration = self.planner.estimate_duration(task)

        # "Calculate math" length is 14
        # Cost: 14 * 0.05 = 0.70
        # Duration: 1.0 + 14 * 0.02 = 1.28
        self.assertEqual(cost, 0.70)
        self.assertEqual(duration, 1.28)

    def test_validation_empty_task(self) -> None:
        """Verifies validations enforce task presence rules."""
        with self.assertRaises(TaskValidationError):
            self.planner.validate_task(None)  # type: ignore

    def test_validation_missing_task_id(self) -> None:
        """Verifies validations enforce ID checks."""
        task = Task(description="valid desc")
        task.task_id = None  # type: ignore

        with self.assertRaises(TaskValidationError):
            self.planner.validate_task(task)

    def test_validation_empty_description(self) -> None:
        """Verifies validations enforce non-empty descriptions."""
        task1 = Task(description="")
        with self.assertRaises(TaskValidationError):
            self.planner.validate_task(task1)

        task2 = Task(description="   ")
        with self.assertRaises(TaskValidationError):
            self.planner.validate_task(task2)

    def test_create_plan_default_policy(self) -> None:
        """Verifies plan generation applies correct default policies and defaults."""
        task = Task(description="Default Planning Test")

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        plan = self.planner.create_plan(task)

        self.assertIsInstance(plan, ExecutionPlan)
        self.assertIsInstance(plan.plan_id, uuid.UUID)
        self.assertEqual(plan.execution_mode, ExecutionMode.IMMEDIATE)
        self.assertEqual(plan.priority, QueuePriority.NORMAL)
        self.assertEqual(plan.timeout, 30.0)
        self.assertEqual(plan.retry_policy.max_retries, 3)
        self.assertEqual(plan.retry_policy.retry_delay, 1.0)
        self.assertTrue(plan.retry_policy.exponential_backoff)

        # Event bus check
        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "planner.plan.created")
        self.assertEqual(receiver.events[0].payload["task_id"], str(task.task_id))

    def test_custom_plan_parameters(self) -> None:
        """Verifies customized task attributes parsing logic."""
        dep_uuid = uuid.uuid4()
        task = Task(
            description="Custom plan",
            metadata={
                "execution_mode": "ASYNC",
                "priority": "HIGH",
                "timeout": 15.5,
                "dependencies": [str(dep_uuid)],
                "retry_policy": {
                    "max_retries": 5,
                    "retry_delay": 2.5,
                    "exponential_backoff": False,
                    "backoff_multiplier": 1.5,
                    "retryable_exceptions": ["ValueError"]
                }
            }
        )

        plan = self.planner.create_plan(task)
        self.assertEqual(plan.execution_mode, ExecutionMode.ASYNC)
        self.assertEqual(plan.priority, QueuePriority.HIGH)
        self.assertEqual(plan.timeout, 15.5)
        self.assertEqual(plan.dependencies, [dep_uuid])
        self.assertEqual(plan.retry_policy.max_retries, 5)
        self.assertEqual(plan.retry_policy.retry_delay, 2.5)
        self.assertFalse(plan.retry_policy.exponential_backoff)
        self.assertEqual(plan.retry_policy.backoff_multiplier, 1.5)
        self.assertEqual(plan.retry_policy.retryable_exceptions, ["ValueError"])

    def test_invalid_plan_parameters_raises(self) -> None:
        """Verifies validation of bad metadata parameters."""
        # Unsupported Execution Mode
        t1 = Task(description="desc", metadata={"execution_mode": "CONCURRENT"})
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(t1)

        # Invalid Timeout
        t2 = Task(description="desc", metadata={"timeout": -10.0})
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(t2)

        # Malformed Dependency UUID
        t3 = Task(description="desc", metadata={"dependencies": ["not-a-uuid"]})
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(t3)

        # Invalid Retry delay
        t4 = Task(description="desc", metadata={"retry_policy": {"retry_delay": -1.0}})
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(t4)

    def test_invalid_backoff_multiplier(self) -> None:
        """Verifies invalid multiplier validation."""
        t = Task(description="desc", metadata={"retry_policy": {"backoff_multiplier": 0.0}})
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(t)

    def test_plan_failure_event_emitted(self) -> None:
        """Verifies planning failures trigger planner.plan.failed event publication."""
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.ERROR_OCCURRED, receiver)

        task = Task(description="")
        with self.assertRaises(TaskValidationError):
            self.planner.create_plan(task)

        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "planner.plan.failed")

    def test_immutability(self) -> None:
        """Verifies models are immutable dataclasses."""
        task = Task(description="Immutability check")
        plan = self.planner.create_plan(task)

        with self.assertRaises(AttributeError):
            plan.estimated_cost = 5.0  # type: ignore

        with self.assertRaises(AttributeError):
            plan.retry_policy.max_retries = 10  # type: ignore

    def test_thread_safety_concurrency(self) -> None:
        """Verifies that multiple planning calls concurrently execute safely."""
        num_threads = 15
        tasks_per_thread = 20

        plans: List[ExecutionPlan] = []
        plans_lock = threading.Lock()

        def worker(thread_idx: int) -> None:
            for i in range(tasks_per_thread):
                task = Task(description=f"Task_{thread_idx}_{i}")
                p = self.planner.create_plan(task)
                with plans_lock:
                    plans.append(p)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(plans), num_threads * tasks_per_thread)


if __name__ == "__main__":
    unittest.main()
