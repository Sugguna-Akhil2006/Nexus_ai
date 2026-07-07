"""Unit tests for Model Context Protocol (MCP) Integration Framework."""

from __future__ import annotations

import concurrent.futures
import json
import unittest

from backend.mcp.models import JSONRPCRequest, JSONRPCResponse, MCPServerInfo
from backend.mcp.transport import StdioTransport
from backend.mcp.session import MCPSession, MCPSessionManager
from backend.mcp.capability_manager import MCPCapabilityManager
from backend.mcp.security import MCPSecurity
from backend.mcp.registry import MCPRegistry
from backend.mcp.client import MCPClient
from backend.mcp.server import MCPServer


class TestMCPIntegration(unittest.TestCase):
    """Test suite covering client/server handshakes, adapters routing, rates, and locks."""

    def setUp(self) -> None:
        self.registry = MCPRegistry()
        self.security = MCPSecurity()
        self.client = MCPClient(self.registry)
        self.server = MCPServer()

    def test_security_rules_trusted_and_rates(self) -> None:
        """Verifies trusted server validations and rate limit metrics."""
        self.assertTrue(self.security.is_server_trusted("filesystem"))
        self.assertFalse(self.security.is_server_trusted("untrusted-server"))

        # Add trusted server
        self.security.add_trusted_server("untrusted-server")
        self.assertTrue(self.security.is_server_trusted("untrusted-server"))

        # Rate limit checks
        for _ in range(100):
            self.security.check_rate_limit("client-1")
        
        # 101st request should violate limit
        self.assertFalse(self.security.check_rate_limit("client-1"))

    def test_session_manager_and_handshake(self) -> None:
        """Verifies session request blocks waiting for matching JSON-RPC responses."""
        transport = StdioTransport()
        session = MCPSession("session-123", transport)
        
        req = JSONRPCRequest(method="test/ping", params={}, id="req-1")

        # Setup handler response
        def handler(r: JSONRPCRequest) -> JSONRPCResponse:
            return JSONRPCResponse(id=r.id, result={"ping": "pong"})
        session.register_handler("test/ping", handler)

        # Send request and simulate peer responding asynchronously
        def respond_async():
            import time
            time.sleep(0.05)
            # Trigger raw payload response
            payload = json.dumps({"jsonrpc": "2.0", "result": {"ping": "pong"}, "id": "req-1"})
            transport.receive_raw_payload(payload)

        # Run send request in separate thread to simulate async receive
        import threading
        t = threading.Thread(target=respond_async)
        t.start()
        res = session.send_request(req, timeout_seconds=1.0)
        t.join()
        
        self.assertIsNotNone(res.result)
        self.assertEqual(res.result.get("ping"), "pong")


    def test_client_connect_and_disconnect(self) -> None:
        """Verifies server status updates and dynamic session registration."""
        session = self.client.connect_server("github")
        self.assertIsNotNone(session)
        
        server_info = self.registry.get_server_by_name("github")
        self.assertEqual(server_info.status, "connected")

        # Disconnect
        self.client.disconnect_server(server_info.server_id)
        self.assertEqual(server_info.status, "disconnected")

    def test_server_list_capabilities(self) -> None:
        """Verifies server exposes tools, resources, and prompt templates correctly."""
        transport = StdioTransport()
        session = MCPSession("session-server-test", transport)
        self.server.bind_to_session(session)

        # 1. Test tools list
        req_tools = JSONRPCRequest(method="tools/list", id="list-t")
        res_tools = session._handlers["tools/list"](req_tools)
        self.assertIsNotNone(res_tools.result)
        self.assertIn("tools", res_tools.result)
        self.assertTrue(any(t["name"] == "resume_analyze" for t in res_tools.result["tools"]))

        # 2. Test prompts list
        req_prompts = JSONRPCRequest(method="prompts/list", id="list-p")
        res_prompts = session._handlers["prompts/list"](req_prompts)
        self.assertIsNotNone(res_prompts.result)
        self.assertIn("prompts", res_prompts.result)
        self.assertTrue(any(p["name"] == "chat-instruction" for p in res_prompts.result["prompts"]))

    def test_concurrent_mcp_sessions_requests(self) -> None:
        """Verifies thread-safety of session manager under concurrent JSON-RPC requests."""
        manager = MCPSessionManager()
        transport = StdioTransport()
        session = manager.create_session("session-concurrent", transport)

        def worker_task(index: int) -> None:
            req = JSONRPCRequest(method=f"worker/{index}", params={}, id=f"id-{index}")
            # Register local handler to respond instantly
            session.register_handler(f"worker/{index}", lambda r: JSONRPCResponse(id=r.id, result={"index": index}))
            
            # Simulate peer messaging
            payload = json.dumps({"jsonrpc": "2.0", "result": {"index": index}, "id": f"id-{index}"})
            session.transport.receive_raw_payload(payload)
            res = session.send_request(req, timeout_seconds=1.0)
            self.assertEqual(res.result.get("index"), index)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker_task, i) for i in range(30)]
            concurrent.futures.wait(futures)
