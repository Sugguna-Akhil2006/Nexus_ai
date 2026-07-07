"""MCP Client managing connections, health checks, and requests routing to external servers."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.mcp.models import JSONRPCRequest, JSONRPCResponse, MCPServerInfo
from backend.mcp.session import MCPSession
from backend.mcp.transport import StdioTransport
from backend.mcp.registry import MCPRegistry
from backend.mcp.security import MCPSecurity


class MCPClient:
    """Orchestrates connections and queries to external MCP servers."""

    def __init__(self, registry: Optional[MCPRegistry] = None) -> None:
        self.registry = registry or MCPRegistry()
        self.event_bus = EventBus()
        self.security = MCPSecurity()
        self._active_sessions: Dict[str, MCPSession] = {}

    def connect_server(self, name: str, url: Optional[str] = None) -> Optional[MCPSession]:
        """Handshakes and registers a session with the named server."""
        if not self.security.is_server_trusted(name):
            raise PermissionError(f"Connection blocked: Server '{name}' is untrusted.")

        server = self.registry.get_server_by_name(name)
        if not server:
            server = MCPServerInfo(
                server_id=f"server-{name.lower()}",
                name=name,
                version="1.0.0",
                url=url
            )
            self.registry.register_server(server)

        # Build Transport and Session
        transport = StdioTransport()
        session = MCPSession(server.server_id, transport)
        self._active_sessions[server.server_id] = session

        # Capability Negotiation handshake simulation
        handshake_req = JSONRPCRequest(
            method="initialize",
            params={"clientName": "NexusClient", "clientVersion": "1.0.0"},
            id=f"init-{uuid.uuid4().hex[:8]}"
        )
        
        # Simulate local peer responding automatically to initialize
        def handle_init(req: JSONRPCRequest) -> JSONRPCResponse:
            return JSONRPCResponse(
                id=req.id,
                result={"serverName": name, "serverVersion": "1.0.0", "capabilities": {"tools": {}, "resources": {}}}
            )
        session.register_handler("initialize", handle_init)

        # Trigger receive initial response
        init_res_payload = json.dumps({
            "jsonrpc": "2.0",
            "result": {"serverName": name, "serverVersion": "1.0.0"},
            "id": handshake_req.id
        })
        # Let's frame message directly using transport to simulate successful handshake
        transport.receive_raw_payload(init_res_payload)

        # Mark Status
        self.registry.update_status(server.server_id, "connected")

        # Emit connected event
        self._publish_event("mcp.connected", {"server_id": server.server_id, "name": name})

        return session

    def disconnect_server(self, server_id: str) -> None:
        """Closes communication session with the server."""
        session = self._active_sessions.pop(server_id, None)
        if session:
            self.registry.update_status(server_id, "disconnected")
            server = self.registry.get_server(server_id)
            server_name = server.name if server else "unknown"
            self._publish_event("mcp.disconnected", {"server_id": server_id, "name": server_name})

    def execute_tool(self, server_name: str, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Routes execution query calls to the target server."""
        server = self.registry.get_server_by_name(server_name)
        if not server or server.status != "connected":
            raise ConnectionError(f"Server '{server_name}' is not connected.")

        session = self._active_sessions.get(server.server_id)
        if not session:
            raise ConnectionError(f"No active session for server '{server_name}'.")

        # Call rate limit check
        if not self.security.check_rate_limit("client-id-local"):
            raise PermissionError("Rate limit exceeded for MCP client requests.")

        req_id = f"tool-{uuid.uuid4().hex[:8]}"
        req = JSONRPCRequest(
            method="tools/call",
            params={"name": tool_name, "arguments": params},
            id=req_id
        )

        # Setup mock response handler to tools/call on session transport loop
        # For simulation, trigger raw payload response directly:
        mock_response = {
            "jsonrpc": "2.0",
            "result": {"status": "success", "content": f"Executed tool '{tool_name}' on server '{server_name}'"},
            "id": req_id
        }
        
        # Spawn message receiver in transport
        session.transport.receive_raw_payload(json.dumps(mock_response))
        res = session.send_request(req)

        # Emit execution event
        self._publish_event("mcp.tool.executed", {
            "server_id": server.server_id,
            "tool_name": tool_name,
            "status": "success" if not res.error else "failed"
        })

        if res.error:
            raise RuntimeError(res.error.get("message", "Tool invocation failed."))

        return res.result

    def _publish_event(self, event_name: str, payload: dict) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="MCPClient",
            payload={
                "event": event_name,
                "timestamp": datetime.utcnow().isoformat(),
                **payload
            }
        )
        self.event_bus.publish(event)
