"""Security Guard enforcing trusted server checks, rates, and permissions in MCP."""

from __future__ import annotations

import time
from typing import Dict, List, Set


class MCPSecurity:
    """Enforces authentication, authorization and rate limiting policies for MCP connections."""

    def __init__(self) -> None:
        self._trusted_servers: Set[str] = {"filesystem", "sqlite", "github", "slack"}
        self._request_timestamps: Dict[str, List[float]] = {}
        self._rate_limit_per_minute = 100

    def is_server_trusted(self, server_name: str) -> bool:
        """Checks if server is registered in trusted lists."""
        return server_name.lower() in self._trusted_servers

    def add_trusted_server(self, server_name: str) -> None:
        self._trusted_servers.add(server_name.lower())

    def check_rate_limit(self, client_id: str) -> bool:
        """Enforces call frequency limits."""
        now = time.time()
        if client_id not in self._request_timestamps:
            self._request_timestamps[client_id] = []

        # Filter timestamps within the last 60 seconds
        history = [t for t in self._request_timestamps[client_id] if now - t < 60.0]
        self._request_timestamps[client_id] = history

        if len(history) >= self._rate_limit_per_minute:
            return False

        self._request_timestamps[client_id].append(now)
        return True

    def validate_workspace_permissions(self, user_id: str, workspace_id: str, resource_uri: str) -> bool:
        """Checks permission scope bounds for resource access via MCP."""
        # Standard placeholder validation matching PermissionManager layout
        if user_id == "admin":
            return True
        # Read-only resource access bounds
        if "workspace/" in resource_uri and workspace_id in resource_uri:
            return True
        return False
