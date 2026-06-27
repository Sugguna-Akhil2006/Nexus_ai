import threading
import time
import unittest
import uuid

from core.task import Task
from core.task_queue import (
    DuplicateTaskError,
    QueueFullError,
    QueueItem,
    QueuePriority,
    QueueValidationError,
    TaskQueue,
)


class TestTaskQueue(unittest.TestCase):
    """Suite of tests covering the prioritized TaskQueue lifecycle."""

    def setUp(self) -> None:
        self.queue = TaskQueue()
        self.queue.clear()
        self.queue.max_capacity = None

    def test_singleton(self) -> None:
        """Verifies that TaskQueue behaves as a singleton."""
        queue2 = TaskQueue()
        self.assertIs(self.queue, queue2)

    def test_enqueue_and_dequeue(self) -> None:
        """Verifies basic task scheduling and popping workflow."""
        task = Task(description="basic task")
        q_item = self.queue.enqueue(task, priority=QueuePriority.HIGH)

        self.assertEqual(self.queue.count(), 1)
        self.assertFalse(self.queue.is_empty())
        self.assertTrue(self.queue.contains(task.task_id))

        peeked = self.queue.peek()
        self.assertIs(peeked, q_item)

        dequeued = self.queue.dequeue()
        self.assertIs(dequeued, q_item)
        self.assertIsNotNone(dequeued.started_at)
        self.assertTrue(self.queue.is_empty())

    def test_priority_ordering(self) -> None:
        """Verifies that tasks are dequeued in priority order."""
        t_low = Task(description="low priority")
        t_high = Task(description="high priority")
        t_system = Task(description="system priority")
        t_normal = Task(description="normal priority")

        self.queue.enqueue(t_low, priority=QueuePriority.LOW)
        self.queue.enqueue(t_high, priority=QueuePriority.HIGH)
        self.queue.enqueue(t_system, priority=QueuePriority.SYSTEM)
        self.queue.enqueue(t_normal, priority=QueuePriority.NORMAL)

        # Dequeue sequence should be system -> high -> normal -> low
        self.assertEqual(self.queue.dequeue().task.description, "system priority")
        self.assertEqual(self.queue.dequeue().task.description, "high priority")
        self.assertEqual(self.queue.dequeue().task.description, "normal priority")
        self.assertEqual(self.queue.dequeue().task.description, "low priority")

    def test_stable_fifo(self) -> None:
        """Verifies FIFO execution order for tasks of the same priority."""
        t1 = Task(description="first")
        t2 = Task(description="second")
        t3 = Task(description="third")

        self.queue.enqueue(t1, priority=QueuePriority.NORMAL)
        self.queue.enqueue(t2, priority=QueuePriority.NORMAL)
        self.queue.enqueue(t3, priority=QueuePriority.NORMAL)

        self.assertEqual(self.queue.dequeue().task.description, "first")
        self.assertEqual(self.queue.dequeue().task.description, "second")
        self.assertEqual(self.queue.dequeue().task.description, "third")

    def test_duplicate_prevention(self) -> None:
        """Verifies duplicate tasks raise DuplicateTaskError."""
        task = Task(description="task")
        self.queue.enqueue(task)

        with self.assertRaises(DuplicateTaskError):
            self.queue.enqueue(task)

    def test_remove(self) -> None:
        """Verifies manual removal from queue by ID."""
        t1 = Task(description="task 1")
        t2 = Task(description="task 2")

        q1 = self.queue.enqueue(t1)
        q2 = self.queue.enqueue(t2)

        removed = self.queue.remove(t1.task_id)
        self.assertIs(removed, q1)
        self.assertFalse(self.queue.contains(t1.task_id))
        self.assertTrue(self.queue.contains(t2.task_id))

        self.assertIsNone(self.queue.remove(uuid.uuid4()))

    def test_capacity_limits(self) -> None:
        """Verifies queue full exceptions are raised when capacity is exceeded."""
        self.queue.max_capacity = 2

        t1 = Task(description="t1")
        t2 = Task(description="t2")
        t3 = Task(description="t3")

        self.queue.enqueue(t1)
        self.queue.enqueue(t2)

        with self.assertRaises(QueueFullError):
            self.queue.enqueue(t3)

    def test_statistics(self) -> None:
        """Verifies metrics summary values."""
        t1 = Task(description="t1")
        t2 = Task(description="t2")

        self.queue.enqueue(t1, priority=QueuePriority.SYSTEM)
        self.queue.enqueue(t2, priority=QueuePriority.NORMAL)

        self.queue.remove(t1.task_id)
        self.queue.dequeue()

        stats = self.queue.statistics()
        self.assertEqual(stats["total_enqueued"], 2)
        self.assertEqual(stats["total_dequeued"], 1)
        self.assertEqual(stats["total_removed"], 1)
        self.assertEqual(stats["current_size"], 0)

    def test_serialization(self) -> None:
        """Verifies to_dict and from_dict methods on QueueItem."""
        task = Task(description="serial task", metadata={"env": "dev"})
        item = QueueItem(task=task, priority=QueuePriority.CRITICAL, retry_count=2)

        serialized = item.to_dict()
        self.assertEqual(serialized["priority"], "CRITICAL")
        self.assertEqual(serialized["retry_count"], 2)
        self.assertEqual(serialized["task"]["description"], "serial task")

        deserialized = QueueItem.from_dict(serialized)
        self.assertEqual(deserialized.queue_id, item.queue_id)
        self.assertEqual(deserialized.task.task_id, task.task_id)
        self.assertEqual(deserialized.priority, item.priority)
        self.assertEqual(deserialized.retry_count, item.retry_count)

    def test_from_dict_validation_error(self) -> None:
        """Verifies validation errors on bad deserializations."""
        with self.assertRaises(QueueValidationError):
            QueueItem.from_dict({"queue_id": "invalid-uuid"})

    def test_thread_safety(self) -> None:
        """Verifies concurrent enqueueing and dequeueing under high thread contention."""
        num_threads = 15
        tasks_per_thread = 40

        def enqueue_worker(thread_idx: int) -> None:
            for i in range(tasks_per_thread):
                task = Task(description=f"t_{thread_idx}_{i}")
                self.queue.enqueue(task, priority=QueuePriority.NORMAL)

        # Start enqueuing threads
        threads = [
            threading.Thread(target=enqueue_worker, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.queue.count(), num_threads * tasks_per_thread)

        # Dequeue concurrently
        dequeued_items = []
        dequeued_lock = threading.Lock()

        def dequeue_worker() -> None:
            while True:
                item = self.queue.dequeue()
                if item is None:
                    break
                with dequeued_lock:
                    dequeued_items.append(item)

        readers = [threading.Thread(target=dequeue_worker) for _ in range(5)]
        for r in readers:
            r.start()
        for r in readers:
            r.join()

        self.assertEqual(len(dequeued_items), num_threads * tasks_per_thread)
        self.assertTrue(self.queue.is_empty())


if __name__ == "__main__":
    unittest.main()
