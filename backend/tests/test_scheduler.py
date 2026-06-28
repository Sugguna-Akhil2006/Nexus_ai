from datetime import datetime, timedelta
import threading
from typing import List
import unittest
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import TaskValidationError
from backend.execution.planner import ExecutionMode, ExecutionPlan, RetryPolicy
from backend.execution.scheduler import (
    RecurrencePolicy,
    ScheduleEntry,
    Scheduler,
    ScheduleStatus,
    ScheduleValidationError,
)
from backend.runtime.task import Task
from backend.execution.task_queue import QueuePriority


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestScheduler(unittest.TestCase):
    """Suite of tests covering the Execution Scheduler lifecycle."""

    def setUp(self) -> None:
        self.scheduler = Scheduler()
        with self.scheduler._lock:
            self.scheduler._schedules.clear()
        self.event_bus = EventBus()
        self.event_bus.clear()

        # Build execution plan
        self.task = Task(description="Scheduler test task")
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
        """Verifies that Scheduler behaves as a singleton."""
        scheduler2 = Scheduler()
        self.assertIs(self.scheduler, scheduler2)

    def test_immediate_scheduling(self) -> None:
        """Verifies immediate scheduling defaults."""
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        entry = self.scheduler.schedule(self.plan)

        self.assertIsInstance(entry, ScheduleEntry)
        self.assertEqual(entry.status, ScheduleStatus.PENDING)
        self.assertEqual(entry.retry_count, 0)
        self.assertIsNotNone(entry.next_run)

        # Check event bus
        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "scheduler.plan.scheduled")

    def test_delayed_scheduling(self) -> None:
        """Verifies future delayed scheduling configuration."""
        target_time = datetime.utcnow() + timedelta(seconds=10)
        plan_delayed = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.SCHEDULED,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={"scheduled_time": target_time.isoformat()},
            estimated_cost=0.5,
            estimated_duration=1.5
        )

        entry = self.scheduler.schedule(plan_delayed)
        self.assertEqual(entry.scheduled_time, target_time)
        self.assertEqual(entry.next_run, target_time)

    def test_scheduling_past_time_rejection(self) -> None:
        """Verifies past scheduling boundaries logic."""
        past_time = datetime.utcnow() - timedelta(seconds=10)
        plan_past = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.SCHEDULED,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={"scheduled_time": past_time.isoformat()},
            estimated_cost=0.5,
            estimated_duration=1.5
        )

        with self.assertRaises(ScheduleValidationError):
            self.scheduler.schedule(plan_past)

        # Workaround with allow_past in metadata
        plan_past.metadata["allow_past"] = True
        entry = self.scheduler.schedule(plan_past)
        self.assertEqual(entry.scheduled_time, past_time)

    def test_invalid_recurrence_policy(self) -> None:
        """Verifies validations enforce positive recurrence rules."""
        # Negative interval
        p1 = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.SCHEDULED,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={"recurrence_policy": {"interval": -5.0}},
            estimated_cost=0.5,
            estimated_duration=1.5
        )
        with self.assertRaises(ScheduleValidationError):
            self.scheduler.schedule(p1)

    def test_cancellation(self) -> None:
        """Verifies cancellation status flow."""
        entry = self.scheduler.schedule(self.plan)
        self.assertEqual(entry.status, ScheduleStatus.PENDING)
        self.event_bus.dispatch_all()

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        # Successful cancellation
        success = self.scheduler.cancel(entry.schedule_id)
        self.assertTrue(success)
        self.assertEqual(entry.status, ScheduleStatus.CANCELLED)

        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "scheduler.plan.cancelled")

        # Double cancellation returns False
        self.assertFalse(self.scheduler.cancel(entry.schedule_id))

    def test_rescheduling(self) -> None:
        """Verifies rescheduling updates scheduling entry state."""
        entry = self.scheduler.schedule(self.plan)
        self.event_bus.dispatch_all()

        new_time = datetime.utcnow() + timedelta(seconds=30)
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        rescheduled_entry = self.scheduler.reschedule(entry.schedule_id, new_time)
        self.assertEqual(rescheduled_entry.scheduled_time, new_time)
        self.assertEqual(rescheduled_entry.next_run, new_time)

        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "scheduler.plan.rescheduled")

    def test_list_pending_and_ready(self) -> None:
        """Verifies pending schedules segregation and ready state transition."""
        future_time = datetime.utcnow() + timedelta(seconds=10)
        plan_future = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.SCHEDULED,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={"scheduled_time": future_time.isoformat()},
            estimated_cost=0.5,
            estimated_duration=1.5
        )

        entry_immediate = self.scheduler.schedule(self.plan)
        entry_future = self.scheduler.schedule(plan_future)
        self.event_bus.dispatch_all()

        # Pending should list future ones
        pending = self.scheduler.list_pending()
        self.assertEqual(len(pending), 1)
        self.assertIn(entry_future, pending)

        # Ready should list immediate ones when checked
        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        ready = self.scheduler.list_ready(datetime.utcnow())
        self.assertEqual(len(ready), 1)
        self.assertIn(entry_immediate, ready)
        self.assertEqual(entry_immediate.status, ScheduleStatus.READY)

        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "scheduler.plan.ready")

    def test_retry_scheduling(self) -> None:
        """Verifies retry increments and status flow."""
        entry = self.scheduler.schedule(self.plan)
        self.event_bus.dispatch_all()

        receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, receiver)

        retried_entry = self.scheduler.schedule_retry(entry.schedule_id, delay_seconds=5.0)
        self.assertEqual(retried_entry.retry_count, 1)
        self.assertEqual(retried_entry.status, ScheduleStatus.RETRYING)
        self.assertAlmostEqual(
            (retried_entry.next_run - datetime.utcnow()).total_seconds(),
            5.0,
            delta=1.0
        )

        self.event_bus.dispatch_all()
        self.assertEqual(len(receiver.events), 1)
        self.assertEqual(receiver.events[0].payload["event_name"], "scheduler.plan.retry")

    def test_recurrence_calculation(self) -> None:
        """Verifies recurrence triggering bounds."""
        target_time = datetime.utcnow()
        end_time = target_time + timedelta(seconds=15)
        plan_recur = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow(),
            execution_mode=ExecutionMode.SCHEDULED,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=30.0,
            dependencies=[],
            metadata={
                "scheduled_time": target_time.isoformat(),
                "recurrence_policy": {
                    "interval": 5.0,
                    "max_occurrences": 3,
                    "end_time": end_time.isoformat()
                }
            },
            estimated_cost=0.5,
            estimated_duration=1.5
        )

        entry = self.scheduler.schedule(plan_recur)

        # First recurrence trigger -> next run time is scheduled_time + 5s
        t1 = self.scheduler.trigger_recurrence(entry.schedule_id)
        self.assertIsNotNone(t1)
        self.assertEqual(entry.metadata["occurrence_count"], 1)
        self.assertEqual(entry.status, ScheduleStatus.PENDING)

        # Second recurrence trigger
        t2 = self.scheduler.trigger_recurrence(entry.schedule_id)
        self.assertIsNotNone(t2)
        self.assertEqual(entry.metadata["occurrence_count"], 2)

        # Third recurrence trigger -> reaches max_occurrences 3 -> should complete
        t3 = self.scheduler.trigger_recurrence(entry.schedule_id)
        self.assertIsNone(t3)
        self.assertEqual(entry.status, ScheduleStatus.COMPLETED)

    def test_cleanup_expired(self) -> None:
        """Verifies expired items cleanup based on timeout boundaries."""
        plan_expired = ExecutionPlan(
            plan_id=uuid.uuid4(),
            task=self.task,
            created_at=datetime.utcnow() - timedelta(seconds=50),
            execution_mode=ExecutionMode.IMMEDIATE,
            priority=QueuePriority.NORMAL,
            retry_policy=RetryPolicy(),
            timeout=10.0,  # 10s timeout has elapsed
            dependencies=[],
            metadata={"allow_past": True, "scheduled_time": (datetime.utcnow() - timedelta(seconds=40)).isoformat()},
            estimated_cost=0.5,
            estimated_duration=1.5
        )

        self.scheduler.schedule(plan_expired)
        expired_count = self.scheduler.cleanup_expired()
        self.assertEqual(expired_count, 1)

    def test_thread_safety_concurrency(self) -> None:
        """Verifies thread-safe registration and access concurrently."""
        num_threads = 15
        schedules_per_thread = 20

        entries: List[ScheduleEntry] = []
        entries_lock = threading.Lock()

        def worker(thread_idx: int) -> None:
            for i in range(schedules_per_thread):
                task = Task(description=f"ThreadTask_{thread_idx}_{i}")
                plan = ExecutionPlan(
                    plan_id=uuid.uuid4(),
                    task=task,
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
                entry = self.scheduler.schedule(plan)
                with entries_lock:
                    entries.append(entry)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(entries), num_threads * schedules_per_thread)


if __name__ == "__main__":
    unittest.main()
