"""Maintains trace execution logs and settings for a single reasoning turn."""

import time
from typing import Dict, List, Any


class ReasoningContext:
    """Session state manager for storing logs and metrics during reasoning."""

    def __init__(self, workspace_id: str, query: str, options: Dict[str, Any]) -> None:
        self.workspace_id = workspace_id
        self.query = query
        self.options = options
        self.traces: List[str] = []
        self.start_time = time.perf_counter()

    def add_trace(self, step: str) -> None:
        """Appends a trace message to the trace logs list."""
        self.traces.append(f"[{time.strftime('%H:%M:%S')}] {step}")

    def get_trace(self) -> List[str]:
        """Retrieves all generated trace messages."""
        return self.traces

    def get_elapsed_seconds(self) -> float:
        """Calculates execution duration in seconds."""
        return round(time.perf_counter() - self.start_time, 4)
