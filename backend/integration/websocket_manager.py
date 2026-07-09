"""WebSocket connection manager for live progress and token streaming.

Manages active connections grouped by workspace ID and/or request ID, allowing
broadcast or target-specific delivery of frontend integration events.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger("nexus.integration.websocket")


class WebSocketManager:
    """Thread-safe manager for active WebSocket connections."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # Mapping from workspace_id -> set of active WebSockets
        self._workspace_connections: Dict[str, Set[WebSocket]] = {}
        # Mapping from request_id -> set of active WebSockets
        self._request_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(
        self,
        websocket: WebSocket,
        workspace_id: str,
        request_id: Optional[str] = None,
    ) -> None:
        """Accepts and registers a new WebSocket connection."""
        await websocket.accept()
        with self._lock:
            if workspace_id not in self._workspace_connections:
                self._workspace_connections[workspace_id] = set()
            self._workspace_connections[workspace_id].add(websocket)

            if request_id:
                if request_id not in self._request_connections:
                    self._request_connections[request_id] = set()
                self._request_connections[request_id].add(websocket)

        logger.info(
            f"WebSocket connected for workspace={workspace_id}, request={request_id}"
        )

    def disconnect(
        self,
        websocket: WebSocket,
        workspace_id: str,
        request_id: Optional[str] = None,
    ) -> None:
        """Unregisters a WebSocket connection."""
        with self._lock:
            if workspace_id in self._workspace_connections:
                self._workspace_connections[workspace_id].discard(websocket)
                if not self._workspace_connections[workspace_id]:
                    del self._workspace_connections[workspace_id]

            if request_id and request_id in self._request_connections:
                self._request_connections[request_id].discard(websocket)
                if not self._request_connections[request_id]:
                    del self._request_connections[request_id]

        logger.info(
            f"WebSocket disconnected for workspace={workspace_id}, request={request_id}"
        )

    async def send_to_request(self, request_id: str, message: Any) -> None:
        """Sends a JSON message to all WebSockets listening to a request."""
        sockets = set()
        with self._lock:
            if request_id in self._request_connections:
                sockets = set(self._request_connections[request_id])

        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to request WebSocket: {e}")

    async def broadcast(self, workspace_id: str, message: Any) -> None:
        """Broadcasts a JSON message to all WebSockets listening to a workspace."""
        sockets = set()
        with self._lock:
            if workspace_id in self._workspace_connections:
                sockets = set(self._workspace_connections[workspace_id])

        for ws in sockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send message to workspace WebSocket: {e}")
