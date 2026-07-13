"""Health check manager consolidating subsystem states."""

import time
from typing import Dict, Any, List, Callable


class HealthCheckManager:
    """Aggregates multiple health indicator callbacks into a single state report."""

    def __init__(self) -> None:
        """Initializes storage for health check functions."""
        self._checkers: Dict[str, Callable[[], Dict[str, Any]]] = {}

    def register_checker(self, name: str, checker_fn: Callable[[], Dict[str, Any]]) -> None:
        """Registers a named subsystem health checking callable.

        Args:
            name: Subsystem name.
            checker_fn: Callable returning status dictionary.
        """
        self._checkers[name] = checker_fn

    def get_status(self) -> Dict[str, Any]:
        """Runs all checks, determining overall health.

        Returns:
            Overall state dictionary.
        """
        overall_healthy = True
        details = {}
        
        for name, checker in self._checkers.items():
            try:
                res = checker()
                details[name] = res
                if res.get("status") != "healthy":
                    overall_healthy = False
            except Exception as e:
                overall_healthy = False
                details[name] = {"status": "unhealthy", "error": str(e)}

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": time.time(),
            "details": details
        }
