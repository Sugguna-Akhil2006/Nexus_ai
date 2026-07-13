"""Readiness checks ensuring dependencies like database and storage are accessible."""

import os
from typing import Dict, Any, List, Callable


class ReadinessChecker:
    """Verifies that all external dependencies are fully responsive."""

    def __init__(self, checks: List[Callable[[], bool]]) -> None:
        """Initializes settings.

        Args:
            checks: List of callables returning True if healthy.
        """
        self.checks = checks

    def is_ready(self) -> bool:
        """Evaluates all registered checkers.

        Returns:
            True if all checks succeed, False otherwise.
        """
        for check in self.checks:
            try:
                if not check():
                    return False
            except Exception:
                return False
        return True
