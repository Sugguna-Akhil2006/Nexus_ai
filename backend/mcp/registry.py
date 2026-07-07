"""MCP Registry keeping discovered servers, capabilities and statuses."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional

from backend.mcp.models import MCPServerInfo


class MCPRegistry:
    """Manages active external MCP servers and their capabilities catalogs."""

    def __init__(self) -> None:
        self._servers: Dict[str, MCPServerInfo] = {}
        self._lock = threading.Lock()
        self._init_default_servers()

    def _init_default_servers(self) -> None:
        # Prepopulate standard trusted server entries
        self.register_server(MCPServerInfo(
            server_id="server-filesystem",
            name="filesystem",
            version="1.0.0",
            status="disconnected"
        ))
        self.register_server(MCPServerInfo(
            server_id="server-github",
            name="github",
            version="1.0.0",
            status="disconnected"
        ))

    def register_server(self, server: MCPServerInfo) -> None:
        with self._lock:
            self._servers[server.server_id] = server

    def get_server(self, server_id: str) -> Optional[MCPServerInfo]:
        with self._lock:
            return self._servers.get(server_id)

    def get_server_by_name(self, name: str) -> Optional[MCPServerInfo]:
        with self._lock:
            for s in self._servers.values():
                if s.name.lower() == name.lower():
                    return s
            return None

    def list_servers(self) -> List[MCPServerInfo]:
        with self._lock:
            return list(self._servers.values())

    def update_status(self, server_id: str, status: str) -> None:
        with self._lock:
            if server_id in self._servers:
                self._servers[server_id].status = status
