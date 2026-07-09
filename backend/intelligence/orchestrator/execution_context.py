"""Thread-safe context manager tracking active orchestration state and stage timelines."""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class OrchestrationContext:
    """Carries runtime variables, shared memory, and module step durations thread-safely.

    Attributes:
        workspace_id: active tenant identifier.
        user_id: requesting user ID.
        query: primary search query or request.
        document_ids: document files under scope.
    """

    def __init__(
        self,
        workspace_id: str,
        user_id: str,
        query: str,
        document_ids: Optional[List[str]] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.query = query
        self.document_ids = document_ids or []
        self.session_id = session_id

        self._lock = threading.RLock()
        self._timings: Dict[str, float] = {}       # node_id -> duration_ms
        self._results: Dict[str, Dict[str, Any]] = {}  # module_name -> output_payload
        self._errors: Dict[str, str] = {}            # module_name -> error_msg
        self._memory: Dict[str, Any] = {}            # shared key-value cache
        self._start_times: Dict[str, float] = {}

    def start_node(self, node_id: str) -> None:
        """Starts timing for a node."""
        with self._lock:
            self._start_times[node_id] = time.perf_counter()

    def end_node(self, node_id: str, module: str, result: Optional[Dict[str, Any]], error: Optional[str] = None) -> None:
        """Stops timing for a node and stores its execution outcome."""
        with self._lock:
            start = self._start_times.pop(node_id, None)
            if start is not None:
                duration_ms = (time.perf_counter() - start) * 1000.0
                self._timings[node_id] = round(duration_ms, 2)

            if error:
                self._errors[module] = error
            elif result:
                self._results[module] = result

    def get_results(self) -> Dict[str, Dict[str, Any]]:
        """Returns all completed module outputs."""
        with self._lock:
            return dict(self._results)

    def get_errors(self) -> Dict[str, str]:
        """Returns all registered module errors."""
        with self._lock:
            return dict(self._errors)

    def get_timings(self) -> Dict[str, float]:
        """Returns all step execution durations in milliseconds."""
        with self._lock:
            return dict(self._timings)

    def set_memory(self, key: str, value: Any) -> None:
        """Stores a shared variable in the orchestration context."""
        with self._lock:
            self._memory[key] = value

    def get_memory(self, key: str) -> Optional[Any]:
        """Retrieves a shared variable."""
        with self._lock:
            return self._memory.get(key)
