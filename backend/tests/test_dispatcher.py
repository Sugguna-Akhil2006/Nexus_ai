from datetime import datetime
import threading
from typing import List
import unittest
import uuid

from backend.execution.dispatcher import (
    Dispatcher,
    DispatchResult,
    DispatchStatus,
    DispatchTarget,
    DispatchValidationError,
    DuplicateTargetError,
    TargetNotFoundError,
)
from backend.runtime.event import Event, EventBus, EventType
from backend.execution.planner import ExecutionMode, ExecutionPlan, RetryPolicy
from backend.runtime.task import Task
from backend.execution.task_queue import QueuePriority


class MockTarget(DispatchTarget):
    """Concrete target implementation for test verification."""

    def __init__(self, name: str) -> None:
        self._name = name
        self.dispatched_plans: List[ExecutionPlan] = []

    @property
    def name(self) -> str:
        return self._name

    def handle_dispatch(self, plan: ExecutionPlan) -> None:
        self.dispatched_plans.append(plan)


class FailingTarget(DispatchTarget):
    """Concrete target simulated to crash during handle_dispatch."""

    @property
    def name(self) -> str:
        return "FailingTarget"

    def handle_dispatch(self, plan: ExecutionPlan) -> None:
        raise RuntimeError("Target hardware connection failure")


class MockEventReceiver:
    """Helper to collect emitted EventBus transactions."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestDispatcher(unittest.TestCase):
    """Suite of tests covering the Execution Dispatcher router."""

    def setUp(self) -> None:
        self.dispatcher = Dispatcher()
        # Clean targets registry and reset rules to default to avoid cross-test pollution
        with self.dispatcher._lock:
            self.dispatcher._targets.clear()
            self.dispatcher._routing_rules = {
                ExecutionMode.IMMEDIATE: "Executor",
                ExecutionMode.ASYNC: "Scheduler",
                ExecutionMode.PARALLEL: "Scheduler",
                ExecutionMode.SCHEDULED: "Scheduler",
                ExecutionMode.DISTRIBUTED: "Distributed"
            }
        self.event_bus = EventBus()
        self.event_bus.clear()

        # Build clean test plan
        self.task = Task(description="Dispatch test task")
        self.plan = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={},
            estimated_cost=0.5,
            estimated_duration=1.5
        )

    def test_singleton(self) -> None:
        """Verifies that Dispatcher behaves as a singleton."""
        dispatcher2 = Dispatcher()
        self.assertIs(self.dispatcher, dispatcher2)

    def test_registry_management(self) -> None:
        """Verifies registering, unregistering, and listing targets."""
        target1 = MockTarget("TargetOne")
        target2 = MockTarget("TargetTwo")

        self.dispatcher.register_target(target1)
        self.dispatcher.register_target(target2)
        self.assertIn("TargetOne", self.dispatcher.list_targets())
        self.assertIn("TargetTwo", self.dispatcher.list_targets())

        # Duplicate register raises DuplicateTargetError
        with self.assertRaises(DuplicateTargetError):
            self.dispatcher.register_target(target1)

        # Invalid target raises DispatchValidationError
        with self.assertRaises(DispatchValidationError):
            self.dispatcher.register_target(None)  # type: ignore

        # Unregistering works
        self.dispatcher.unregister_target("TargetOne")
        self.assertNotIn("TargetOne", self.dispatcher.list_targets())

        # Unregistering missing target raises TargetNotFoundError
        with self.assertRaises(TargetNotFoundError):
            self.dispatcher.unregister_target("TargetOne")

    def test_routing_resolution(self) -> None:
        """Verifies destination mapping and target resolution."""
        executor = MockTarget("Executor")
        self.dispatcher.register_target(executor)

        resolved = self.dispatcher.resolve_destination(self.plan)
        self.assertIs(resolved, executor)

        # Missing target raises TargetNotFoundError
        plan_async = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.ASYNC,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={},
            estimated_cost=0.5,
            estimated_duration=1.5
        )
        with self.assertRaises(TargetNotFoundError):
            self.dispatcher.resolve_destination(plan_async)

    def test_plan_validations(self) -> None:
        """Verifies validation of ExecutionPlan attributes before dispatching."""
        with self.assertRaises(DispatchValidationError):
            self.dispatcher.validate_plan(None)  # type: ignore

        # Missing plan_id
        plan_bad_id = ExecutionPlan(
            plan_id=None,  # type: ignore
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={},
            estimated_cost=0.5,
            estimated_duration=1.5
        )
        with self.assertRaises(DispatchValidationError):
            self.dispatcher.validate_plan(plan_bad_id)

    def test_successful_dispatch(self) -> None:
        """Verifies successful plan dispatch workflow and event publishing."""
        executor = MockTarget("Executor")
        self.dispatcher.register_target(executor)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        result = self.dispatcher.dispatch(self.plan)

        self.assertIsInstance(result, DispatchResult)
        self.assertEqual(result.status, DispatchStatus.SUCCESS)
        self.assertEqual(result.destination, "Executor")
        self.assertEqual(len(executor.dispatched_plans), 1)
        self.assertIs(executor.dispatched_plans[0], self.plan)

        # Check Event bus
        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 2)
        self.assertEqual(receiver.events[0].payload["event_name"], "dispatcher.started")
        self.assertEqual(receiver.events[1].payload["event_name"], "dispatcher.completed")

    def test_failing_dispatch(self) -> None:
        """Verifies failed plan dispatch triggers exception mapping and failed events."""
        failing_target = FailingTarget()
        self.dispatcher.register_target(failing_target)
        self.dispatcher.set_routing_rule(ExecutionMode.IMMEDIATE, failing_target.name)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Dispatch should fail and translate into a general DispatchError
        with self.assertRaises(Exception) as context:
            self.dispatcher.dispatch(self.plan)

        self.assertIn("Failed to dispatch plan", str(context.exception))

        self.event_bus.dispatch_all()
        # Find failed events
        failed_events = [e for e in receiver.events if e.payload["event_name"] == "dispatcher.failed"]
        self.assertEqual(len(failed_events), 1)
        self.assertIn("Target hardware connection failure", failed_events[0].payload["error"])

    def test_immutability(self) -> None:
        """Verifies that DispatchResult is an immutable dataclass."""
        res = DispatchResult(
            dispatch_id=uuid.uuid4(),
            plan_id=uuid.uuid4(),
            destination="Destination",
            dispatched_at=datetime.utcnow(),
            status=DispatchStatus.SUCCESS
        )
        with self.assertRaises(AttributeError):
            res.destination = "Other"  # type: ignore

    def test_thread_safety_concurrency(self) -> None:
        """Verifies thread-safe capability registrations concurrently."""
        num_threads = 15
        targets_per_thread = 20

        def worker(thread_idx: int) -> None:
            for i in range(targets_per_thread):
                target = MockTarget(f"Thread_{thread_idx}_Target_{i}")
                self.dispatcher.register_target(target)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(
            len(self.dispatcher.list_targets()),
            num_threads * targets_per_thread
        )


if __name__ == "__main__":
    unittest.main()
