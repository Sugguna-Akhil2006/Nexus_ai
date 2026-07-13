"""Checks environment settings to ensure key database and port settings are defined."""

import os
from typing import Tuple, List, Optional


class EnvironmentValidator:
    """Verifies that all required environment variables are set and conform to expectations."""

    def __init__(self, required_keys: Optional[List[str]] = None) -> None:
        """Initializes with required env keys list.

        Args:
            required_keys: Optional list of mandatory environment keys.
        """
        self.required_keys = required_keys or ["PORT", "REDIS_HOST", "DB_TYPE"]

    def validate_env(self) -> Tuple[bool, str]:
        """Checks if all required environment variables are populated.

        Returns:
            Tuple (is_valid, validation_message).
        """
        missing = []
        for key in self.required_keys:
            if not os.getenv(key):
                missing.append(key)

        if missing:
            return False, f"Missing required env keys: {', '.join(missing)}"
        return True, "Environment validated successfully"
