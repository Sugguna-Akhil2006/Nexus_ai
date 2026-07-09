"""Filesystem guard protecting against directory traversal and path violations."""

from __future__ import annotations

import os


class FilesystemGuard:
    """Validates files read/write paths to prevent directory traversals."""

    @staticmethod
    def is_safe_path(root_path: str, target_path: str) -> bool:
        """Verifies if the target path is resolved entirely under the root path.

        Args:
            root_path: Root folder of the sandbox session.
            target_path: File path under operation.

        Returns:
            True if path traversal is absent and resolved path is within bounds.
        """
        if not root_path or not target_path:
            return False

        abs_root = os.path.abspath(root_path)
        abs_target = os.path.abspath(target_path)

        # Allow target_path if it is located inside abs_root
        common = os.path.commonpath([abs_root, abs_target])
        return common == abs_root
