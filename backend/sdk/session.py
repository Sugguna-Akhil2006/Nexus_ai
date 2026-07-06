"""Session management for Nexus AI SDK clients."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.sdk.config import NexusConfig


@dataclass
class SessionState:
    """Mutable session state tracked by the SDK client.

    Attributes:
        session_id: Unique session identifier.
        workspace_id: Active workspace identifier.
        user_id: Optional authenticated user identifier.
        created_at: ISO timestamp of session creation.
        metadata: Arbitrary session-scoped metadata.
    """

    session_id: str = field(default_factory=lambda: f"sess-{uuid.uuid4().hex[:12]}")
    workspace_id: str = "default-ws"
    user_id: Optional[str] = None
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Thread-safe session manager for SDK client instances."""

    def __init__(self, config: NexusConfig) -> None:
        self._config = config
        self._state = SessionState(workspace_id=config.workspace_id)
        self._lock = threading.RLock()

    @property
    def session_id(self) -> str:
        """Returns the current session identifier.

        Returns:
            Session ID string.
        """
        with self._lock:
            return self._state.session_id

    @property
    def workspace_id(self) -> str:
        """Returns the active workspace identifier.

        Returns:
            Workspace ID string.
        """
        with self._lock:
            return self._state.workspace_id

    @property
    def user_id(self) -> Optional[str]:
        """Returns the active user identifier.

        Returns:
            User ID string or None.
        """
        with self._lock:
            return self._state.user_id

    def set_workspace(self, workspace_id: str) -> None:
        """Sets the active workspace for subsequent requests.

        Args:
            workspace_id: Target workspace identifier.
        """
        with self._lock:
            self._state.workspace_id = workspace_id
            self._config.workspace_id = workspace_id

    def set_user(self, user_id: str) -> None:
        """Sets the active user for subsequent requests.

        Args:
            user_id: Target user identifier.
        """
        with self._lock:
            self._state.user_id = user_id

    def set_metadata(self, key: str, value: Any) -> None:
        """Stores a session-scoped metadata value.

        Args:
            key: Metadata key.
            value: Metadata value.
        """
        with self._lock:
            self._state.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Retrieves a session-scoped metadata value.

        Args:
            key: Metadata key.
            default: Value returned when the key is absent.

        Returns:
            Stored metadata value or default.
        """
        with self._lock:
            return self._state.metadata.get(key, default)

    def reset(self) -> None:
        """Creates a new session while preserving workspace and user context."""
        with self._lock:
            workspace = self._state.workspace_id
            user = self._state.user_id
            self._state = SessionState(workspace_id=workspace, user_id=user)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes session state to a dictionary.

        Returns:
            Dictionary representation of the session.
        """
        with self._lock:
            return {
                "session_id": self._state.session_id,
                "workspace_id": self._state.workspace_id,
                "user_id": self._state.user_id,
                "created_at": self._state.created_at,
                "metadata": dict(self._state.metadata),
            }
