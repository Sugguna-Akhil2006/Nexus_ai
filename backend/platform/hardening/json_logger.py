"""JSON logger producing structured logs for production observability."""

import json
import logging
import threading
import uuid
from typing import Any, Dict, Optional

# Thread-local storage for request correlation details
_context = threading.local()


def set_correlation_ids(request_id: str, trace_id: Optional[str] = None, correlation_id: Optional[str] = None) -> None:
    """Sets trace/correlation identifiers in thread local storage.

    Args:
        request_id: ID of the request.
        trace_id: Trace ID.
        correlation_id: Correlation ID.
    """
    _context.request_id = request_id
    _context.trace_id = trace_id or request_id
    _context.correlation_id = correlation_id or request_id


def get_correlation_ids() -> Dict[str, str]:
    """Retrieves correlation details currently bound to thread."""
    return {
        "request_id": getattr(_context, "request_id", "system"),
        "trace_id": getattr(_context, "trace_id", "system"),
        "correlation_id": getattr(_context, "correlation_id", "system")
    }


def clear_correlation_ids() -> None:
    """Clears context identifiers."""
    _context.request_id = "system"
    _context.trace_id = "system"
    _context.correlation_id = "system"


class JSONFormatter(logging.Formatter):
    """Logging Formatter transforming records into JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the record as JSON.

        Args:
            record: LogRecord object.
        """
        import datetime
        corr = get_correlation_ids()
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "file": record.filename,
            "line": record.lineno,
            "request_id": corr["request_id"],
            "trace_id": corr["trace_id"],
            "correlation_id": corr["correlation_id"]
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def configure_json_logger(level: int = logging.INFO) -> None:
    """Reconfigures the root logger handlers to output JSON.

    Args:
        level: Minimum log level.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Clear existing handlers
    for handler in list(root.handlers):
        root.removeHandler(handler)

    ch = logging.StreamHandler()
    ch.setFormatter(JSONFormatter())
    root.addHandler(ch)
