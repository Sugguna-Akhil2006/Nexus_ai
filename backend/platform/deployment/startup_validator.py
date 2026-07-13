"""Startup configuration validator verifying settings and directories access permissions."""

import os
from typing import List, Dict, Tuple, Optional


class StartupValidator:
    """Evaluates environment parameters and filesystem permissions before boot completes."""

    def __init__(self, required_envs: List[str], writable_dirs: List[str]) -> None:
        """Initializes settings.

        Args:
            required_envs: Mandatory environment variables.
            writable_dirs: Filesystem folders requiring write access.
        """
        self.required_envs = required_envs
        self.writable_dirs = writable_dirs

    def validate_environment(self) -> Tuple[bool, List[str]]:
        """Verifies if required env keys are populated.

        Returns:
            Tuple (is_valid, list_of_missing_keys).
        """
        missing = []
        for key in self.required_envs:
            if not os.getenv(key):
                missing.append(key)
        return len(missing) == 0, missing

    def validate_directories(self) -> Tuple[bool, List[str]]:
        """Verifies write permissions on required folders.

        Returns:
            Tuple (is_valid, list_of_inaccessible_directories).
        """
        inaccessible = []
        for directory in self.writable_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory, exist_ok=True)
                except Exception:
                    inaccessible.append(directory)
                    continue

            # Verify write access
            test_file = os.path.join(directory, ".startup_write_test")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except Exception:
                inaccessible.append(directory)

        return len(inaccessible) == 0, inaccessible
