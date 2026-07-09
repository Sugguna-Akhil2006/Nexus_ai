"""Feature flag manager handling runtime toggles for experimental pipelines and modules."""

from __future__ import annotations

import threading
from typing import Dict


class FeatureFlagManager:
    """Thread-safe catalog containing experimental feature flags."""

    def __init__(self, initial_flags: Dict[str, bool]) -> None:
        self._lock = threading.RLock()
        self._flags = dict(initial_flags)

    def is_enabled(self, flag: str) -> bool:
        """Returns True if the feature flag is active."""
        with self._lock:
            return self._flags.get(flag.lower(), False)

    def set_flag(self, flag: str, enabled: bool) -> None:
        """Sets the state of a feature flag."""
        with self._lock:
            self._flags[flag.lower()] = enabled

    def list_flags(self) -> Dict[str, bool]:
        """Returns all configured feature flags."""
        with self._lock:
            return dict(self._flags)
