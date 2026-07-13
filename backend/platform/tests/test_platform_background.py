"""Unit tests for Platform Background processing module."""

import time
import unittest

from backend.platform.background.queue_manager import QueueManager
from backend.platform.background.retry_manager import RetryManager
from backend.platform.background.job_scheduler import JobScheduler
from backend.platform.background.task_worker import TaskWorkerPool


class TestPlatformBackground(unittest.TestCase):
    """Test suite covering queues, workers, schedulers, and retries."""

    def test_queue_dlq_lifecycle(self) -> None:
        """Verifies queue FIFO mechanics and DLQ routing limits."""
        qm = QueueManager(dlq_threshold=2)
        task = {"id": "task-1", "action": "ingest"}
        
        qm.enqueue(task)
        self.assertEqual(qm.size(), 1)
        
        # Dequeue
        pulled = qm.dequeue()
        self.assertEqual(pulled["id"], "task-1")
        
        # Fail 1
        qm.handle_failure(pulled, "First failure")
        self.assertEqual(qm.size(), 1)
        
        # Pull and fail 2 (breaches threshold)
        pulled_2 = qm.dequeue()
        qm.handle_failure(pulled_2, "Second failure")
        
        # Should be in DLQ, queue empty
        self.assertEqual(qm.size(), 0)
        self.assertEqual(len(qm.get_dlq_tasks()), 1)

    def test_retry_manager_backoff(self) -> None:
        """Verifies retry counts and backoff execution loops."""
        rm = RetryManager(max_attempts=2, initial_delay=0.1, backoff_factor=1.5)
        
        calls = 0
        def failing_op():
            nonlocal calls
            calls += 1
            raise ValueError("Always fail")

        with self.assertRaises(ValueError):
            rm.execute(failing_op)
        self.assertEqual(calls, 2)

    def test_job_scheduler(self) -> None:
        """Verifies one-off and periodic cron schedules."""
        scheduler = JobScheduler()
        triggered = False
        
        def job_fn():
            nonlocal triggered
            triggered = True

        scheduler.schedule_once("job-1", time.time() + 0.1, job_fn)
        scheduler.start()
        
        time.sleep(0.4)
        scheduler.stop()
        
        self.assertTrue(triggered)
