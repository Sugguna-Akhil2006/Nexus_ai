"""Workspace config registry tracking overrides for specific tenant workspaces."""

from __future__ import annotations

import threading
from typing import Dict, Any


class WorkspaceConfig:
    """Thread-safe store mapping workspace-specific operational property overrides."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._overrides: Dict[str, Dict[str, Any]] = {}

    def set_override(self, workspace_id: str, key: str, value: Any) -> None:
        """Saves a single override value for a workspace."""
        with self._lock:
            ws_map = self._overrides.get(workspace_id)
            if not ws_map:
                ws_map = {}
                self._overrides[workspace_id] = ws_map
            ws_map[key] = value

    def get_override(self, workspace_id: str, key: str, default: Any = None) -> Any:
        """Retrieves a workspace-specific config option or returns the default value."""
        with self._lock:
            ws_map = self._overrides.get(workspace_id)
            if ws_map and key in ws_map:
                return ws_map[key]
            return default

    def list_overrides(self, workspace_id: str) -> Dict[str, Any]:
        """Lists all overrides defined for a workspace."""
        with self._lock:
            return dict(self._overrides.get(workspace_id, {}))
