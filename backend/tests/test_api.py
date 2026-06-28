import concurrent.futures
import threading
from typing import Any, Dict, List, Optional
import unittest
import uuid

from backend.interfaces.api import (
    APIException,
    APIValidationError,
    APIAuthenticationError,
    APIAuthorizationError,
    APINotFoundError,
    ApiRequest,
    ApiResponse,
    ApiError,
    EndpointRegistry,
    AuthenticationMiddleware,
    CorsMiddleware,
    RateLimitingMiddleware,
    ApiGateway,
    WebSocketManager,
)
from backend.agents.workspace import WorkspaceValidationError
from backend.agents.document import DocumentNotFoundError
from backend.runtime.event import Event, EventBus, EventType


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestAPISystem(unittest.TestCase):
    """Suite of tests covering request routing pipelines, middleware chains, and WebSockets."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = EndpointRegistry()
        with self.registry._lock:
            self.registry._routes.clear()

        # Register simple mock handlers
        def mock_chat_handler(req: ApiRequest) -> ApiResponse:
            return ApiResponse(
                request_id=req.request_id,
                status_code=200,
                body={"answer": "hello world"},
                headers={}
            )

        def mock_fail_handler(req: ApiRequest) -> ApiResponse:
            raise WorkspaceValidationError("Invalid workspace config details.")

        def mock_not_found_handler(req: ApiRequest) -> ApiResponse:
            raise DocumentNotFoundError("Document id not located.")

        self.registry.register("POST", "/v1/chat", mock_chat_handler)
        self.registry.register("GET", "/v1/fail", mock_fail_handler)
        self.registry.register("GET", "/v1/missing", mock_not_found_handler)

        self.gateway = ApiGateway()
        self.gateway.add_middleware(AuthenticationMiddleware())
        self.gateway.add_middleware(CorsMiddleware())
        self.gateway.add_middleware(RateLimitingMiddleware())

        self.ws_manager = WebSocketManager()
        with self.ws_manager._lock:
            self.ws_manager._connections.clear()

    def test_endpoint_registry_routing(self) -> None:
        """Verifies route registration, duplicate validations, and resolution bounds."""
        # Test Resolve
        handler = self.registry.resolve("POST", "/v1/chat")
        self.assertIsNotNone(handler)

        # Duplicate Registration
        with self.assertRaises(APIValidationError):
            self.registry.register("POST", "/v1/chat", handler)

        # Route Not Found
        with self.assertRaises(APINotFoundError):
            self.registry.resolve("GET", "/v1/chat")

    def test_authentication_middleware_blocking(self) -> None:
        """Verifies authentication middleware blocks requests with empty auth headers."""
        req_unauth = ApiRequest(
            request_id="req_unauth",
            api_version="v1",
            endpoint="/v1/chat",
            method="POST",
            headers={},  # Missing Authorization and X-API-Key
            parameters={},
            body={},
            user_identity={},
            workspace="ws_1"
        )
        res = self.gateway.handle_request(req_unauth)
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.body["error_code"], "UNAUTHORIZED")

    def test_cors_middleware_headers(self) -> None:
        """Verifies CORS middleware injects control headers into all responses."""
        req = ApiRequest(
            request_id="req_cors",
            api_version="v1",
            endpoint="/v1/chat",
            method="POST",
            headers={"authorization": "Bearer token123"},
            parameters={},
            body={},
            user_identity={},
            workspace="ws_1"
        )
        res = self.gateway.handle_request(req)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("access-control-allow-origin"), "*")
        self.assertEqual(res.body["answer"], "hello world")

    def test_rate_limiting_short_circuit(self) -> None:
        """Verifies rate limit middleware triggers 429 short circuit responses."""
        req = ApiRequest(
            request_id="req_rate",
            api_version="v1",
            endpoint="/v1/chat",
            method="POST",
            headers={"authorization": "Bearer token123"},
            parameters={},
            body={},
            user_identity={},
            workspace="ws_1",
            metadata={"trigger_rate_limit": True}
        )
        res = self.gateway.handle_request(req)
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.body["error_code"], "RATE_LIMIT_EXCEEDED")

    def test_runtime_exception_translations(self) -> None:
        """Verifies gateway translates internal exceptions into structured ApiErrors."""
        # 1. 400 Bad Request
        req_fail = ApiRequest(
            request_id="req_fail",
            api_version="v1",
            endpoint="/v1/fail",
            method="GET",
            headers={"authorization": "Bearer token"},
            parameters={},
            body={},
            user_identity={},
            workspace="ws_1"
        )
        res_fail = self.gateway.handle_request(req_fail)
        self.assertEqual(res_fail.status_code, 400)
        self.assertEqual(res_fail.body["error_code"], "BAD_REQUEST")

        # 2. 404 Not Found
        req_missing = ApiRequest(
            request_id="req_missing",
            api_version="v1",
            endpoint="/v1/missing",
            method="GET",
            headers={"authorization": "Bearer token"},
            parameters={},
            body={},
            user_identity={},
            workspace="ws_1"
        )
        res_missing = self.gateway.handle_request(req_missing)
        self.assertEqual(res_missing.status_code, 404)
        self.assertEqual(res_missing.body["error_code"], "NOT_FOUND")

    def test_websocket_lifecycle_and_broadcasting(self) -> None:
        """Verifies WebSocket connections registration, send caches, and event broadcasts."""
        conn1 = self.ws_manager.connect("conn_1")
        conn2 = self.ws_manager.connect("conn_2")

        self.assertEqual(conn1.connection_id, "conn_1")

        # Send target message
        self.ws_manager.send_message("conn_1", {"message": "direct hello"})
        self.assertEqual(len(conn1.messages), 1)
        self.assertEqual(len(conn2.messages), 0)

        # Broadcast
        self.ws_manager.broadcast({"message": "broadcast alert"})
        self.assertEqual(len(conn1.messages), 2)
        self.assertEqual(len(conn2.messages), 1)

        # Disconnect
        self.ws_manager.disconnect("conn_1")
        with self.ws_manager._lock:
            self.assertNotIn("conn_1", self.ws_manager._connections)

        # Verify EventBus events
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("api.websocket.connected", events)
        self.assertIn("api.websocket.disconnected", events)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent route registrations operate safely."""
        def run_thread(tid: int) -> None:
            endpoint = f"/v1/path-{tid}"
            handler = lambda r: ApiResponse(r.request_id, 200, {}, {})
            self.registry.register("GET", endpoint, handler)
            self.assertIsNotNone(self.registry.resolve("GET", endpoint))
            self.registry.unregister("GET", endpoint)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
