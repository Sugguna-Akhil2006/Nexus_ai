"""Public API Layer and Client Boundary Orchestration Module.

Provides abstractions, models, registries, middlewares, gateway request routing,
and WebSocket connection managers for clients interfacing with the Nexus AI platform.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import datetime
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import uuid

from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class APIException(NexusException):
    """Base exception for all Public API Layer related errors."""
    pass


class APIValidationError(APIException):
    """Raised when incoming parameters validation fails."""
    pass


class APIAuthenticationError(APIException):
    """Raised when caller identity credentials check fails."""
    pass


class APIAuthorizationError(APIException):
    """Raised when caller lacks authorization scopes."""
    pass


class APINotFoundError(APIException):
    """Raised when target endpoint URL path is not found."""
    pass


# =====================================================================
# Data Models
# =====================================================================

@dataclass(frozen=True)
class ApiRequest:
    """Incoming client request parameters package details.

    Attributes:
        request_id: Unique request trace correlation ID.
        api_version: API version path constraint (e.g. v1, v2).
        endpoint: Endpoint URL path string.
        method: HTTP request method verb (GET, POST, etc.).
        headers: Input HTTP header key-value maps.
        parameters: URL query query parameters.
        body: Request JSON body dictionary payload.
        user_identity: Caller identity attributes maps.
        workspace: Caller tenant workspace key.
        metadata: Extra metrics tracking metadata.
    """
    request_id: str
    api_version: str
    endpoint: str
    method: str
    headers: Dict[str, str]
    parameters: Dict[str, Any]
    body: Dict[str, Any]
    user_identity: Dict[str, Any]
    workspace: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApiResponse:
    """Outgoing API response packet.

    Attributes:
        request_id: Target correlation ID.
        status_code: HTTP response status integer.
        body: JSON payload output dictionary or list.
        headers: Output HTTP headers mapping.
        execution_time: Elapsed runtime duration in float seconds.
        diagnostics: Diagnostics tracking details.
    """
    request_id: str
    status_code: int
    body: Any
    headers: Dict[str, str]
    execution_time: float = 0.0
    diagnostics: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ApiError:
    """Standardized API response JSON payload on validation or internal failure.

    Attributes:
        error_code: String code categorization.
        message: General description text message.
        details: Specific fields validation messages details.
        correlation_id: Request tracking ID.
    """
    error_code: str
    message: str
    details: Dict[str, Any]
    correlation_id: str


# =====================================================================
# Endpoint Registry
# =====================================================================

class EndpointRegistry:
    """Thread-safe registry mapping API routes to active callback handlers."""

    _instance: Optional["EndpointRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "EndpointRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._routes: Dict[Tuple[str, str], Callable[[ApiRequest], ApiResponse]] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register(self, method: str, endpoint: str, handler: Callable[[ApiRequest], ApiResponse]) -> None:
        """Saves a route registration."""
        if not method or not endpoint or not handler:
            raise APIValidationError("Invalid registration parameters: empty route or handler.")

        normalized_method = method.upper().strip()
        normalized_endpoint = endpoint.lower().strip()

        with self._lock:
            key = (normalized_method, normalized_endpoint)
            if key in self._routes:
                raise APIValidationError(f"Endpoint '{method} {endpoint}' is already registered.")
            self._routes[key] = handler
            self._logger.info(f"Registered route handler: {normalized_method} {normalized_endpoint}")

    def unregister(self, method: str, endpoint: str) -> None:
        """Removes an active endpoint route."""
        normalized_method = method.upper().strip()
        normalized_endpoint = endpoint.lower().strip()
        key = (normalized_method, normalized_endpoint)

        with self._lock:
            if key not in self._routes:
                raise APIValidationError(f"Route '{method} {endpoint}' not found.")
            del self._routes[key]
            self._logger.info(f"Unregistered route handler: {normalized_method} {normalized_endpoint}")

    def resolve(self, method: str, endpoint: str) -> Callable[[ApiRequest], ApiResponse]:
        """Resolves target handler from normalized routes path."""
        normalized_method = method.upper().strip()
        normalized_endpoint = endpoint.lower().strip()
        key = (normalized_method, normalized_endpoint)

        with self._lock:
            if key not in self._routes:
                raise APINotFoundError(f"Route '{method} {endpoint}' not found.")
            return self._routes[key]

    def list_endpoints(self) -> List[Tuple[str, str]]:
        """Lists active routes path names."""
        with self._lock:
            return list(self._routes.keys())


# =====================================================================
# Middleware Abstractions
# =====================================================================

class ApiMiddleware(ABC):
    """Abstract interface defining middleware hooks."""

    @abstractmethod
    def process_request(self, request: ApiRequest) -> Optional[ApiResponse]:
        """Intercepts request prior to routing.

        Returns an ApiResponse if it needs to short-circuit, otherwise None.
        """
        pass

    @abstractmethod
    def process_response(self, request: ApiRequest, response: ApiResponse) -> ApiResponse:
        """Intercepts response post routing prior to dispatching."""
        pass


class AuthenticationMiddleware(ApiMiddleware):
    """Verifies client tokens or credentials headers validation."""

    def process_request(self, request: ApiRequest) -> Optional[ApiResponse]:
        # Validate JWT or API Key token presence
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")

        if not auth_header and not api_key:
            # Short-circuit and reject with unauthorized
            err = ApiError(
                error_code="UNAUTHORIZED",
                message="Missing or invalid authentication credentials.",
                details={},
                correlation_id=request.request_id
            )
            return ApiResponse(
                request_id=request.request_id,
                status_code=401,
                body=err.__dict__,
                headers={},
                execution_time=0.0
            )
        return None

    def process_response(self, request: ApiRequest, response: ApiResponse) -> ApiResponse:
        return response


class CorsMiddleware(ApiMiddleware):
    """Adds CORS origin control headers to the API responses."""

    def process_request(self, request: ApiRequest) -> Optional[ApiResponse]:
        return None

    def process_response(self, request: ApiRequest, response: ApiResponse) -> ApiResponse:
        new_headers = dict(response.headers)
        new_headers["access-control-allow-origin"] = "*"
        new_headers["access-control-allow-methods"] = "GET, POST, OPTIONS, PUT, DELETE"
        new_headers["access-control-allow-headers"] = "Content-Type, Authorization, X-API-Key"
        # Create updated response containing new headers
        import dataclasses
        return dataclasses.replace(response, headers=new_headers)


class RateLimitingMiddleware(ApiMiddleware):
    """Enforces API rate limiting limits (mock implementation)."""

    def process_request(self, request: ApiRequest) -> Optional[ApiResponse]:
        # Checks if request metadata specifies to trigger rate limit block
        if request.metadata.get("trigger_rate_limit", False):
            err = ApiError(
                error_code="RATE_LIMIT_EXCEEDED",
                message="Too many requests. Please try again later.",
                details={"retry_after_seconds": 60},
                correlation_id=request.request_id
            )
            return ApiResponse(
                request_id=request.request_id,
                status_code=429,
                body=err.__dict__,
                headers={"retry-after": "60"},
                execution_time=0.0
            )
        return None

    def process_response(self, request: ApiRequest, response: ApiResponse) -> ApiResponse:
        return response


# =====================================================================
# API Gateway Coordinator
# =====================================================================

class ApiGateway:
    """Gateway entrypoint routing requests and catching runtime exceptions."""

    def __init__(self) -> None:
        self.registry = EndpointRegistry()
        self.middlewares: List[ApiMiddleware] = []
        self.event_bus = EventBus()
        self.logger = StructuredLogger()

    def add_middleware(self, middleware: ApiMiddleware) -> None:
        """Registers a middleware class into execution pipeline."""
        self.middlewares.append(middleware)

    def handle_request(self, request: ApiRequest) -> ApiResponse:
        """Routes REST query through middlewares and resolutions pipeline."""
        if not request:
            raise APIValidationError("ApiRequest cannot be None.")

        self._publish_event("api.request.started", request_id=request.request_id, endpoint=request.endpoint)
        start_time = time.perf_counter()

        # 1. Execute Request Middlewares
        for mw in self.middlewares:
            short_circuit = mw.process_request(request)
            if short_circuit:
                duration = time.perf_counter() - start_time
                import dataclasses
                resp = dataclasses.replace(short_circuit, execution_time=duration)
                self._publish_event("api.request.completed", request_id=request.request_id, status=resp.status_code)
                return resp

        # 2. Resolve Endpoint & Run handler
        try:
            handler = self.registry.resolve(request.method, request.endpoint)
            raw_response = handler(request)
            duration = time.perf_counter() - start_time
            import dataclasses
            response = dataclasses.replace(raw_response, execution_time=duration)

        except Exception as e:
            # 3. Translate Exceptions to API response packets
            duration = time.perf_counter() - start_time
            response = self._translate_exception(request, e, duration)

        # 4. Execute Response Middlewares (in reverse order)
        for mw in reversed(self.middlewares):
            response = mw.process_response(request, response)

        self._publish_event("api.request.completed", request_id=request.request_id, status=response.status_code)
        self.logger.info(
            f"API Request completed: {request.method} {request.endpoint} -> {response.status_code} "
            f"Duration: {duration:.4f}s"
        )
        return response

    def _translate_exception(self, request: ApiRequest, exc: Exception, duration: float) -> ApiResponse:
        """Translates internal framework exceptions into standardized ApiError payloads."""
        status_code = 500
        error_code = "INTERNAL_SERVER_ERROR"

        exc_name = type(exc).__name__

        if isinstance(exc, APINotFoundError) or exc_name in ["DocumentNotFoundError", "WorkspaceNotFoundError"]:
            status_code = 404
            error_code = "NOT_FOUND"
        elif isinstance(exc, APIAuthenticationError) or exc_name == "AuthError":
            status_code = 401
            error_code = "UNAUTHORIZED"
        elif isinstance(exc, APIAuthorizationError) or exc_name == "PermissionDeniedError":
            status_code = 403
            error_code = "FORBIDDEN"
        elif isinstance(exc, APIValidationError) or exc_name in ["WorkspaceValidationError", "TaskValidationError", "ToolValidationError"]:
            status_code = 400
            error_code = "BAD_REQUEST"

        err = ApiError(
            error_code=error_code,
            message=str(exc),
            details={"exception_type": exc_name},
            correlation_id=request.request_id
        )

        self._publish_event("api.request.failed", request_id=request.request_id, error=str(exc))

        return ApiResponse(
            request_id=request.request_id,
            status_code=status_code,
            body=err.__dict__,
            headers={},
            execution_time=duration
        )

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="ApiGateway",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)


# =====================================================================
# WebSocket Manager
# =====================================================================

class WebSocketConnection:
    """Caches connection session states."""

    def __init__(self, connection_id: str) -> None:
        self.connection_id = connection_id
        self.messages: List[Dict[str, Any]] = []

    def send(self, message: Dict[str, Any]) -> None:
        """Sends data through WebSocket stream (cached in array)."""
        self.messages.append(message)


class WebSocketManager:
    """Thread-safe singleton managing active WebSocket channels."""

    _instance: Optional["WebSocketManager"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "WebSocketManager":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._connections: Dict[str, WebSocketConnection] = {}
            self._lock: threading.RLock = threading.RLock()
            self._event_bus = EventBus()
            self._initialized = True

    def connect(self, connection_id: str) -> WebSocketConnection:
        """Registers a connection channel."""
        with self._lock:
            conn = WebSocketConnection(connection_id)
            self._connections[connection_id] = conn

        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WebSocketManager",
            payload={"event_name": "api.websocket.connected", "connection_id": connection_id}
        )
        self._event_bus.publish(event)
        return conn

    def disconnect(self, connection_id: str) -> None:
        """Removes a connection channel."""
        with self._lock:
            if connection_id in self._connections:
                del self._connections[connection_id]

        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="WebSocketManager",
            payload={"event_name": "api.websocket.disconnected", "connection_id": connection_id}
        )
        self._event_bus.publish(event)

    def send_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Sends payload to target connection ID channel."""
        with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].send(message)

    def broadcast(self, message: Dict[str, Any]) -> None:
        """Sends data payload to all active connected channels."""
        with self._lock:
            for conn in self._connections.values():
                conn.send(message)
