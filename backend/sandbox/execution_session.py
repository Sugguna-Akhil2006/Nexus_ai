"""Execution session holding working directories and executing commands isolated."""

from __future__ import annotations

import os
import shutil
from datetime import datetime
from typing import List, Optional

from backend.sandbox.artifact_collector import ArtifactCollector
from backend.sandbox.filesystem_guard import FilesystemGuard
from backend.sandbox.models import CommandResult, SandboxConfig, SandboxSessionInfo
from backend.sandbox.sandbox_executor import SandboxExecutor


class ExecutionSession:
    """Represents an isolated workspace folder executing commands."""

    def __init__(self, session_id: str, config: SandboxConfig) -> None:
        self.session_id = session_id
        self.config = config
        self.status = "active"

        # Create session directory within the workspace to respect Cwd constraints
        # Ensure we place it in backend/sandbox/.sessions/
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.working_directory = os.path.join(base_dir, ".sessions", session_id)
        os.makedirs(self.working_directory, exist_ok=True)

        # Set allowed root path for FilesystemGuard
        self.config.allowed_root_path = self.working_directory
        self.executor = SandboxExecutor(self.config)
        self.created_at = datetime.utcnow().isoformat()

    def execute_command(self, command_str: str) -> CommandResult:
        """Executes a command inside the session working directory."""
        if self.status != "active":
            return CommandResult(
                stdout="",
                stderr="Session Error: Cannot execute commands in a terminated session.",
                exit_code=-4,
                duration_ms=0.0,
            )
        return self.executor.execute(command_str, self.working_directory)

    def upload_file(self, filename: str, content: bytes) -> bool:
        """Saves a file into the session working directory securely."""
        if self.status != "active":
            return False

        target = os.path.join(self.working_directory, filename)
        if not FilesystemGuard.is_safe_path(self.working_directory, target):
            return False

        try:
            # Create parent directories if any
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, "wb") as f:
                f.write(content)
            return True
        except Exception:
            return False

    def download_artifact(self, filename: str) -> Optional[bytes]:
        """Downloads an artifact file from the working directory."""
        return ArtifactCollector.collect_file_bytes(self.working_directory, filename)

    def terminate(self) -> None:
        """Cleans up the working directory and marks the session terminated."""
        self.status = "terminated"
        try:
            if os.path.exists(self.working_directory):
                shutil.rmtree(self.working_directory)
        except Exception:
            pass

    def get_info(self) -> SandboxSessionInfo:
        """Formats the session metadata descriptor."""
        return SandboxSessionInfo(
            session_id=self.session_id,
            status=self.status,
            working_directory=self.working_directory,
            config=self.config,
            created_at=self.created_at,
        )
