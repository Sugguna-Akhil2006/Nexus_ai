"""Session Manager tracking JSON-RPC transactions and negotiations threads."""

from __future__ import annotations

import json
import threading
from typing import Any, Callable, Dict, Optional

from backend.mcp.models import JSONRPCRequest, JSONRPCResponse
from backend.mcp.transport import StdioTransport


class MCPSession:
    """A thread-safe communication session over an MCP Transport."""

    def __init__(self, session_id: str, transport: StdioTransport) -> None:
        self.session_id = session_id
        self.transport = transport
        self._lock = threading.Lock()
        self._pending_requests: Dict[str, threading.Event] = {}
        self._responses: Dict[str, JSONRPCResponse] = {}
        self._handlers: Dict[str, Callable[[JSONRPCRequest], JSONRPCResponse]] = {}
        
        self.transport.set_on_message(self._handle_incoming_raw)

    def register_handler(self, method: str, handler: Callable[[JSONRPCRequest], JSONRPCResponse]) -> None:
        """Registers a handler for incoming requests of a specific method name."""
        with self._lock:
            self._handlers[method] = handler

    def send_request(self, request: JSONRPCRequest, timeout_seconds: float = 10.0) -> JSONRPCResponse:
        """Sends a request asynchronously and blocks waiting for matching response ID."""
        req_id = request.id
        if not req_id:
            raise ValueError("JSON-RPC Request must have a valid non-empty id.")

        event = threading.Event()
        with self._lock:
            self._pending_requests[req_id] = event

        # Serialize and send
        payload = json.dumps({
            "jsonrpc": request.jsonrpc,
            "method": request.method,
            "params": request.params,
            "id": req_id
        })
        self.transport.send_message(payload)

        # Block on event
        completed = event.wait(timeout=timeout_seconds)
        
        with self._lock:
            self._pending_requests.pop(req_id, None)
            response = self._responses.pop(req_id, None)

        if not completed or not response:
            return JSONRPCResponse(
                id=req_id,
                error={"code": -32603, "message": f"Request timeout after {timeout_seconds} seconds."}
            )

        return response

    def _handle_incoming_raw(self, message_str: str) -> None:
        """Processes raw message payload and dispatches requests or resolves responses."""
        try:
            data = json.loads(message_str)
        except Exception:
            return

        req_id = data.get("id")
        method = data.get("method")

        if method:
            # It's an incoming request
            req = JSONRPCRequest(
                jsonrpc=data.get("jsonrpc", "2.0"),
                method=method,
                params=data.get("params", {}),
                id=req_id
            )
            self._handle_incoming_request(req)
        else:
            # It's a response to a pending request we sent
            if not req_id:
                return
            res = JSONRPCResponse(
                jsonrpc=data.get("jsonrpc", "2.0"),
                result=data.get("result"),
                error=data.get("error"),
                id=req_id
            )
            with self._lock:
                event = self._pending_requests.get(req_id)
                if event:
                    self._responses[req_id] = res
                    event.set()

    def _handle_incoming_request(self, req: JSONRPCRequest) -> None:
        handler = None
        with self._lock:
            handler = self._handlers.get(req.method)

        if handler:
            try:
                res = handler(req)
            except Exception as e:
                res = JSONRPCResponse(
                    id=req.id,
                    error={"code": -32603, "message": f"Handler error: {str(e)}"}
                )
        else:
            res = JSONRPCResponse(
                id=req.id,
                error={"code": -32601, "message": f"Method not found: '{req.method}'."}
            )

        # Send response payload back
        if req.id:
            payload = json.dumps({
                "jsonrpc": res.jsonrpc,
                "result": res.result,
                "error": res.error,
                "id": res.id
            })
            self.transport.send_message(payload)
class MCPSessionManager:
    """Tracks and coordinates active MCP communication sessions."""

    def __init__(self) -> None:
        self._sessions: Dict[str, MCPSession] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, transport: StdioTransport) -> MCPSession:
        with self._lock:
            session = MCPSession(session_id, transport)
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[MCPSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def remove_session(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
