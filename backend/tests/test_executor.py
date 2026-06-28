from datetime import datetime
import threading
import time
from typing import List
import unittest
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.execution.executor import (
    Executor,
    ExecutionMetrics,
    ExecutionStatus,
    ExecutionNotFoundError,
)
from backend.execution.planner import ExecutionMode, ExecutionPlan, RetryPolicy
from backend.runtime.result import Result, ResultStatus
from backend.runtime.task import Task
from backend.execution.task_queue import QueuePriority


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestExecutor(unittest.TestCase):
    """Suite of tests covering the Execution Executor lifecycle."""

    def setUp(self) -> None:
        self.executor = Executor()
        # Clean executor states
        with self.executor._lock:
            self.executor._contexts.clear()
            self.executor._statuses.clear()
            self.executor._metrics.clear()
            self.executor._cancellations.clear()
            self.executor._handlers.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()

        self.task = Task(description="test_task")
        self.plan = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(max_retries=2, retry_delay=0.1, exponential_backoff=False),
            timeout=5.0,
            dependencies=[],
            metadata={},
            estimated_cost=1.0,
            estimated_duration=2.0
        )

    def test_singleton(self) -> None:
        """Verifies that Executor behaves as a singleton."""
        executor2 = Executor()
        self.assertIs(self.executor, executor2)

    def test_handler_registration(self) -> None:
        """Verifies custom handler registration matching task prefix."""
        def my_handler(t: Task) -> str:
            return "ok"

        self.executor.register_handler("test_task", my_handler)
        resolved = self.executor.get_handler("test_task_extended")
        self.assertIs(resolved, my_handler)

    def test_successful_execution(self) -> None:
        """Verifies standard successful execution workflow."""
        def success_handler(t: Task) -> str:
            return "execution success"

        self.executor.register_handler("test_task", success_handler)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        result = self.executor.execute(self.plan)

        self.assertTrue(result.is_success())
        self.assertEqual(result.output, "execution success")
        self.assertIn("execution_id", result.metadata)

        exec_id = uuid.UUID(result.metadata["execution_id"])
        self.assertEqual(self.executor.status(exec_id), ExecutionStatus.SUCCESS)

        metrics = self.executor.metrics(exec_id)
        self.assertIsInstance(metrics, ExecutionMetrics)
        self.assertEqual(metrics.retries, 0)
        self.assertEqual(metrics.execution_cost, 1.0)

        # Check Event bus
        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 2)
        self.assertEqual(receiver.events[0].payload["event_name"], "executor.started")
        self.assertEqual(receiver.events[1].payload["event_name"], "executor.completed")

    def test_failure_with_retries_and_success(self) -> None:
        """Verifies retry policy handles transient failures."""
        attempts = 0

        def flaky_handler(t: Task) -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 3:
                raise ValueError("Temporary glitch")
            return "recovered"

        # Allow up to 3 retries (total 4 attempts)
        plan_retry = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(max_retries=3, retry_delay=0.05, exponential_backoff=False),
            timeout=5.0,
            dependencies=[],
            metadata={},
            estimated_cost=1.0,
            estimated_duration=2.0
        )

        self.executor.register_handler("test_task", flaky_handler)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        result = self.executor.execute(plan_retry)

        self.assertTrue(result.is_success())
        self.assertEqual(result.output, "recovered")
        self.assertEqual(attempts, 3)

        exec_id = uuid.UUID(result.metadata["execution_id"])
        metrics = self.executor.metrics(exec_id)
        self.assertEqual(metrics.retries, 2)

        # Check event bus contains retries
        self.event_bus.dispatch_all()
        retry_events = [e for e in receiver.events if e.payload["event_name"] == "executor.retry"]
        self.assertEqual(len(retry_events), 2)

    def test_retry_exhaustion_failure(self) -> None:
        """Verifies retry exhaustion returns failure result."""
        def failing_handler(t: Task) -> None:
            raise ValueError("Always fails")

        self.executor.register_handler("test_task", failing_handler)

        result = self.executor.execute(self.plan)

        self.assertFalse(result.is_success())
        self.assertTrue(result.is_failure())
        self.assertEqual(result.status, ResultStatus.FAILURE)
        self.assertIn("Always fails", result.errors[0])

        exec_id = uuid.UUID(result.metadata["execution_id"])
        self.assertEqual(self.executor.status(exec_id), ExecutionStatus.FAILED)
        metrics = self.executor.metrics(exec_id)
        self.assertEqual(metrics.retries, 2)

    def test_execution_timeout(self) -> None:
        """Verifies execution timeout terminates thread and returns timeout result."""
        def slow_handler(t: Task) -> str:
            time.sleep(2.0)
            return "done"

        plan_timeout = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=0.1,  # 100ms timeout
            dependencies=[],
            metadata={},
            estimated_cost=1.0,
            estimated_duration=2.0
        )

        self.executor.register_handler("test_task", slow_handler)

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        result = self.executor.execute(plan_timeout)

        self.assertEqual(result.status, ResultStatus.TIMEOUT)
        self.assertTrue(result.is_failure())
        self.assertIn("exceeded timeout limit", result.errors[0])

        self.event_bus.dispatch_all()
        timeout_events = [e for e in receiver.events if e.payload["event_name"] == "executor.timeout"]
        self.assertEqual(len(timeout_events), 1)

    def test_concurrent_cancellation(self) -> None:
        """Verifies concurrent cancellations abort running execution."""
        def blocking_handler(t: Task) -> str:
            time.sleep(3.0)
            return "unreachable"

        self.executor.register_handler("test_task", blocking_handler)

        exec_result: List[Result] = []

        def runner() -> None:
            res = self.executor.execute(self.plan)
            exec_result.append(res)

        t = threading.Thread(target=runner)
        t.start()

        # Let the thread start running and register context
        time.sleep(0.1)

        # Retrieve execution ID
        with self.executor._lock:
            exec_id = list(self.executor._statuses.keys())[0]

        # Trigger cancellation
        cancelled = self.executor.cancel(exec_id)
        self.assertTrue(cancelled)

        t.join()

        self.assertEqual(len(exec_result), 1)
        self.assertEqual(exec_result[0].status, ResultStatus.CANCELLED)

    def test_status_missing_raises(self) -> None:
        """Verifies status checks raise ExecutionNotFoundError on unknown IDs."""
        with self.assertRaises(ExecutionNotFoundError):
            self.executor.status(uuid.uuid4())

    def test_thread_safety_concurrency(self) -> None:
        """Verifies thread-safe simultaneous executions under load."""
        def thread_handler(t: Task) -> str:
            return f"Processed: {t.description}"

        self.executor.register_handler("ThreadTask", thread_handler)

        num_threads = 15
        executions_per_thread = 20

        results: List[Result] = []
        results_lock = threading.Lock()

        def worker(thread_idx: int) -> None:
            for i in range(executions_per_thread):
                task = Task(description=f"ThreadTask_{thread_idx}_{i}")
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
                res = self.executor.execute(plan)
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

        self.assertEqual(len(results), num_threads * executions_per_thread)
        for res in results:
            self.assertTrue(res.is_success())
            self.assertTrue(res.output.startswith("Processed: ThreadTask_"))


if __name__ == "__main__":
    unittest.main()
