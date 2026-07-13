"""Structured JSON logging manager for production monitoring."""

import json
import logging
import threading
from typing import Dict, Any, Optional

# Thread local context for correlation trace IDs
_context = threading.local()


def set_trace_context(request_id: str, trace_id: Optional[str] = None) -> None:
    """Sets trace correlation values in thread context."""
    _context.request_id = request_id
    _context.trace_id = trace_id or request_id


def get_trace_context() -> Dict[str, str]:
    """Retrieves correlation details currently bound to thread."""
    return {
        "request_id": getattr(_context, "request_id", "system"),
        "trace_id": getattr(_context, "trace_id", "system")
    }


def clear_trace_context() -> None:
    """Clears context identifiers."""
    _context.request_id = "system"
    _context.trace_id = "system"


class StructuredJSONFormatter(logging.Formatter):
    """Logging Formatter transforming records into JSON format."""

    def format(self, record: logging.LogRecord) -> str:
        """Formats the record as JSON.

        Args:
            record: LogRecord object.
        """
        import datetime
        trace = get_trace_context()
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "file": record.filename,
            "line": record.lineno,
            "request_id": trace["request_id"],
            "trace_id": trace["trace_id"]
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)


def configure_structured_logger(logger_name: str = "nexus_ops", level: int = logging.INFO) -> logging.Logger:
    """Reconfigures named logger to output structured JSON logs.

    Args:
        logger_name: Name of the logger.
        level: Logger level.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Avoid duplicate handlers
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(StructuredJSONFormatter())
        logger.addHandler(ch)

    return logger
