from datetime import datetime, timedelta
import json
import threading
import unittest
import uuid

from backend.runtime.logger import (
    LogEntry,
    LogLevel,
    LogValidationError,
    StructuredLogger,
)


class TestStructuredLogger(unittest.TestCase):
    """Suite of tests covering the telemetric StructuredLogger lifecycle."""

    def setUp(self) -> None:
        self.logger = StructuredLogger()
        self.logger.clear()

    def test_singleton(self) -> None:
        """Verifies that StructuredLogger behaves as a singleton."""
        logger2 = StructuredLogger()
        self.assertIs(self.logger, logger2)

    def test_logging_severities(self) -> None:
        """Verifies the logging interface helpers trace, debug, etc."""
        a_id = uuid.uuid4()
        t_id = uuid.uuid4()
        w_id = uuid.uuid4()
        tr_id = uuid.uuid4()

        self.logger.trace("trace msg", agent_id=a_id)
        self.logger.debug("debug msg", task_id=t_id)
        self.logger.info("info msg", workflow_id=w_id)
        self.logger.warning("warning msg", trace_id=tr_id)
        self.logger.error("error msg", duration_ms=120.0, exception="RuntimeError")
        self.logger.critical("critical msg", metadata={"system": "core"})

        self.assertEqual(self.logger.count(), 6)

        logs = self.logger.get_logs()
        self.assertEqual(logs[0].level, LogLevel.TRACE)
        self.assertEqual(logs[0].agent_id, a_id)

        self.assertEqual(logs[1].level, LogLevel.DEBUG)
        self.assertEqual(logs[1].task_id, t_id)

        self.assertEqual(logs[2].level, LogLevel.INFO)
        self.assertEqual(logs[2].workflow_id, w_id)

        self.assertEqual(logs[3].level, LogLevel.WARNING)
        self.assertEqual(logs[3].trace_id, tr_id)

        self.assertEqual(logs[4].level, LogLevel.ERROR)
        self.assertEqual(logs[4].duration_ms, 120.0)
        self.assertEqual(logs[4].exception, "RuntimeError")

        self.assertEqual(logs[5].level, LogLevel.CRITICAL)
        self.assertEqual(logs[5].metadata, {"system": "core"})

    def test_validation_errors(self) -> None:
        """Verifies validations enforce log model rules."""
        with self.assertRaises(LogValidationError):
            LogEntry(
                level=LogLevel.INFO,
                message="test",
                log_id="not-a-uuid"  # type: ignore
            )

        with self.assertRaises(LogValidationError):
            LogEntry(
                level=LogLevel.INFO,
                message="test",
                duration_ms=-100.0
            )

    def test_filtering(self) -> None:
        """Verifies filter selects logs matching specific keys."""
        a_id1 = uuid.uuid4()
        a_id2 = uuid.uuid4()
        t_id = uuid.uuid4()

        start = datetime.utcnow()

        self.logger.info("msg 1", agent_id=a_id1, metadata={"env": "prod"})
        self.logger.info("msg 2", agent_id=a_id2, metadata={"env": "dev"})
        self.logger.error("msg 3", task_id=t_id, metadata={"env": "prod"})

        # Filter by agent
        res1 = self.logger.filter(agent_id=a_id1)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0].message, "msg 1")

        # Filter by level
        res2 = self.logger.filter(level=LogLevel.ERROR)
        self.assertEqual(len(res2), 1)
        self.assertEqual(res2[0].message, "msg 3")

        # Filter by metadata subset
        res3 = self.logger.filter(metadata={"env": "prod"})
        self.assertEqual(len(res3), 2)

        # Filter by time range
        end = datetime.utcnow() + timedelta(seconds=1)
        res4 = self.logger.filter(start_time=start, end_time=end)
        self.assertEqual(len(res4), 3)

    def test_searching(self) -> None:
        """Verifies substring searching is case-insensitive."""
        self.logger.info("Initialize database connection")
        self.logger.info("Execute processing sequence")
        self.logger.error("Database connection timeout error")

        results = self.logger.search("database")
        self.assertEqual(len(results), 2)
        self.assertIn("connection", results[0].message)

    def test_statistics(self) -> None:
        """Verifies metrics aggregation logic."""
        self.logger.info("run success", duration_ms=50.0)
        self.logger.info("run success", duration_ms=150.0)
        self.logger.error("failed", exception=RuntimeError("err"))

        stats = self.logger.statistics()
        self.assertEqual(stats["total_count"], 3)
        self.assertEqual(stats["by_level"][LogLevel.INFO.value], 2)
        self.assertEqual(stats["by_level"][LogLevel.ERROR.value], 1)
        self.assertEqual(stats["average_duration_ms"], 100.0)
        self.assertEqual(stats["exception_count"], 1)

    def test_export_dict_and_json(self) -> None:
        """Verifies exporting capability."""
        self.logger.info("export test", metadata={"key": "val"})

        export_dicts = self.logger.export_dict()
        self.assertEqual(len(export_dicts), 1)
        self.assertEqual(export_dicts[0]["message"], "export test")
        self.assertEqual(export_dicts[0]["metadata"], {"key": "val"})

        json_str = self.logger.export_json()
        parsed = json.loads(json_str)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["message"], "export test")

    def test_thread_safety(self) -> None:
        """Verifies concurrent logging safety under high load."""
        num_threads = 15
        logs_per_thread = 50

        def worker(thread_idx: int) -> None:
            for i in range(logs_per_thread):
                self.logger.info(f"Thread {thread_idx} log {i}", duration_ms=10.0)

        threads = [
            threading.Thread(target=worker, args=(i,))
            for i in range(num_threads)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(self.logger.count(), num_threads * logs_per_thread)

        stats = self.logger.statistics()
        self.assertEqual(stats["average_duration_ms"], 10.0)


if __name__ == "__main__":
    unittest.main()
