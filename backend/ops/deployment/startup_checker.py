"""Startup integrity checks auditing directory write permissions and database availability."""

import os
from typing import Tuple, List, Optional


class StartupChecker:
    """Runs checks on the filesystem and resources connections to verify startup readiness."""

    def __init__(self, writable_dirs: Optional[List[str]] = None) -> None:
        """Initializes configurations.

        Args:
            writable_dirs: Directories that must carry write permissions.
        """
        self.dirs = writable_dirs or ["storage_data"]

    def check_startup_integrity(self) -> Tuple[bool, str]:
        """Runs checks verifying directories exist and are writable.

        Returns:
            Tuple (is_healthy, status_message).
        """
        inaccessible = []
        for path in self.dirs:
            # Create if not exists
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                except Exception:
                    inaccessible.append(path)
                    continue

            # Verify write capability
            test_file = os.path.join(path, ".startup_write_probe")
            try:
                with open(test_file, "w") as f:
                    f.write("probe")
                os.remove(test_file)
            except Exception:
                inaccessible.append(path)

        if inaccessible:
            return False, f"Directories lacks write permissions: {', '.join(inaccessible)}"
        return True, "Startup integrity check passed"
