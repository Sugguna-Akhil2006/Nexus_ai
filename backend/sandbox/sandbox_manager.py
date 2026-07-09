"""Sandbox manager coordinating multiple isolation execution sessions thread-safely."""

from __future__ import annotations

import threading
import uuid
from typing import Any, Dict, List, Optional

from backend.sandbox.execution_session import ExecutionSession
from backend.sandbox.models import CommandResult, SandboxConfig, SandboxSessionInfo


class SandboxManager:
    """The central manager (facade) coordinating active sandbox sessions thread-safely."""

    _instance: Optional["SandboxManager"] = None
    _singleton_lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "SandboxManager":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        self._lock = threading.RLock()
        self._sessions: Dict[str, ExecutionSession] = {}
        self._initialized = True

    def create_session(self, config: Optional[SandboxConfig] = None) -> SandboxSessionInfo:
        """Spawns a new isolated session."""
        session_id = f"sb-{uuid.uuid4().hex[:8]}"
        cfg = config or SandboxConfig()
        session = ExecutionSession(session_id, cfg)

        with self._lock:
            self._sessions[session_id] = session

        return session.get_info()

    def get_session(self, session_id: str) -> Optional[ExecutionSession]:
        """Retrieves a session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def list_sessions(self) -> List[SandboxSessionInfo]:
        """Lists metadata descriptors for all active sessions."""
        with self._lock:
            return [s.get_info() for s in self._sessions.values() if s.status == "active"]

    def execute_in_session(self, session_id: str, command_str: str) -> CommandResult:
        """Executes a command inside the specified session."""
        with self._lock:
            session = self._sessions.get(session_id)

        if not session:
            return CommandResult(
                stdout="",
                stderr=f"Session Error: Session '{session_id}' not found.",
                exit_code=-5,
                duration_ms=0.0,
            )

        return session.execute_command(command_str)

    def upload_to_session(self, session_id: str, filename: str, content: bytes) -> bool:
        """Saves a file into the specified session's folder."""
        with self._lock:
            session = self._sessions.get(session_id)

        if not session:
            return False

        return session.upload_file(filename, content)

    def download_from_session(self, session_id: str, filename: str) -> Optional[bytes]:
        """Reads a file out of the specified session's folder."""
        with self._lock:
            session = self._sessions.get(session_id)

        if not session:
            return None

        return session.download_artifact(filename)

    def terminate_session(self, session_id: str) -> bool:
        """Kills and cleans up a session."""
        with self._lock:
            session = self._sessions.pop(session_id, None)

        if session:
            session.terminate()
            return True
        return False

    def shutdown(self) -> None:
        """Terminates and cleans up all active sessions on system exit."""
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()

        for s in sessions:
            s.terminate()
DefinitionPath = "sandbox_manager.py"
