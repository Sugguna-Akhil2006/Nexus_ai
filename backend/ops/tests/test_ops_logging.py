"""Unit tests for Operations structured JSON logging package."""

import json
import logging
import unittest

from backend.ops.logging.structured_logger import StructuredJSONFormatter, set_trace_context, get_trace_context, clear_trace_context


class TestOpsLogging(unittest.TestCase):
    """Test suite covering structured JSON formatting and thread-local correlation IDs."""

    def test_json_formatter_fields(self) -> None:
        """Verifies logging details are serialized into JSON format."""
        formatter = StructuredJSONFormatter()
        set_trace_context("req-789", "trace-abc")

        logger = logging.getLogger("ops_test")
        record = logger.makeRecord(
            name="ops_test",
            level=logging.WARNING,
            fn="ops_file.py",
            lno=250,
            msg="Operations telemetry logging check",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        payload = json.loads(formatted)
        
        self.assertEqual(payload["message"], "Operations telemetry logging check")
        self.assertEqual(payload["level"], "WARNING")
        self.assertEqual(payload["request_id"], "req-789")
        self.assertEqual(payload["trace_id"], "trace-abc")
        
        clear_trace_context()
