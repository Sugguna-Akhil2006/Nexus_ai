"""Request tracker maintaining request tracing history logs thread-safely."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.diagnostics.models import RequestTrace


class RequestTracker:
    """Thread-safe log manager keeping structured traces of all query requests."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._traces: Dict[str, RequestTrace] = {}

    def log_trace(self, trace: RequestTrace) -> None:
        """Adds or updates a request trace in the active pool."""
        with self._lock:
            self._traces[trace.request_id] = trace

    def get_trace(self, request_id: str) -> Optional[RequestTrace]:
        """Retrieves a single request trace by identifier."""
        with self._lock:
            return self._traces.get(request_id)

    def list_traces(self) -> List[RequestTrace]:
        """Returns all logged request traces."""
        with self._lock:
            return list(self._traces.values())
