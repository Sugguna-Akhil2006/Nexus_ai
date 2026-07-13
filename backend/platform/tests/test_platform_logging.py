"""Unit tests for Platform JSON Structured Logging module."""

import json
import logging
import unittest
import io

from backend.platform.hardening.json_logger import JSONFormatter, set_correlation_ids, get_correlation_ids, clear_correlation_ids


class TestPlatformLogging(unittest.TestCase):
    """Test suite covering JSON formatting and thread-local correlation IDs context."""

    def test_correlation_ids(self) -> None:
        """Verifies correlation identifiers are bound and cleared correctly."""
        set_correlation_ids("req-123", "trace-456", "corr-789")
        ids = get_correlation_ids()
        self.assertEqual(ids["request_id"], "req-123")
        self.assertEqual(ids["trace_id"], "trace-456")
        self.assertEqual(ids["correlation_id"], "corr-789")

        clear_correlation_ids()
        ids_cleared = get_correlation_ids()
        self.assertEqual(ids_cleared["request_id"], "system")

    def test_json_formatter(self) -> None:
        """Verifies formatter transforms standard log record into JSON format."""
        formatter = JSONFormatter()
        set_correlation_ids("req-abc", "trace-def", "corr-ghi")
        
        # Build mock LogRecord
        logger = logging.getLogger("test_logger")
        record = logger.makeRecord(
            name="test_logger",
            level=logging.INFO,
            fn="test_file.py",
            lno=100,
            msg="Observed event log msg",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        log_dict = json.loads(formatted)
        
        self.assertEqual(log_dict["message"], "Observed event log msg")
        self.assertEqual(log_dict["level"], "INFO")
        self.assertEqual(log_dict["request_id"], "req-abc")
        self.assertEqual(log_dict["trace_id"], "trace-def")
        self.assertEqual(log_dict["correlation_id"], "corr-ghi")

        clear_correlation_ids()
