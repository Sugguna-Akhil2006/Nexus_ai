"""Artifact collector fetching files from sandbox sessions securely."""

from __future__ import annotations

import os
from typing import Optional

from backend.sandbox.filesystem_guard import FilesystemGuard


class ArtifactCollector:
    """Collects and reads files generated during sandbox execution runs."""

    @staticmethod
    def collect_file_bytes(root_path: str, filename: str) -> Optional[bytes]:
        """Reads file contents from the sandbox session folder safely.

        Args:
            root_path: Session directory.
            filename: Target file name.

        Returns:
            Bytes if path is safe and file exists, else None.
        """
        target = os.path.join(root_path, filename)
        if not FilesystemGuard.is_safe_path(root_path, target):
            return None

        if os.path.exists(target) and os.path.isfile(target):
            try:
                with open(target, "rb") as f:
                    return f.read()
            except Exception:
                return None
        return None
DefinitionPath = "artifact_collector.py"
