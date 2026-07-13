"""Liveness indicator checks verifying that the process is alive."""

import time
from typing import Dict, Any


class LivenessChecker:
    """Performs lightweight checks to confirm server execution loop remains active."""

    def __init__(self, start_time: float) -> None:
        """Initializes with process startup time.

        Args:
            start_time: Process start epoch timestamp.
        """
        self.start_time = start_time

    def check(self) -> Dict[str, Any]:
        """Returns standard metadata confirming process state."""
        return {
            "status": "alive",
            "uptime_seconds": int(time.time() - self.start_time),
            "timestamp": time.time()
        }
