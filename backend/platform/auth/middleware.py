"""Authentication middleware for FastAPI requests."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response
from typing import Optional

from backend.platform.auth.jwt_manager import JWTManager
from backend.platform.auth.session_manager import SessionManager


class AuthMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware enforcing bearer tokens and checking session validity."""

    def __init__(
        self,
        app,
        jwt_manager: JWTManager,
        session_manager: SessionManager,
        secret_key: str = "default_secret"
    ) -> None:
        """Initializes the middleware.

        Args:
            app: FastAPI app.
            jwt_manager: Configured JWT manager.
            session_manager: Active session manager.
            secret_key: JWT secret key fallback.
        """
        super().__init__(app)
        self.jwt_manager = jwt_manager
        self.session_manager = session_manager

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Inspects request headers for Auth details.

        Args:
            request: The incoming FastAPI HTTP request.
            call_next: The next middleware / route handler.
        """
        # Skip auth for docs, public, and login/register paths
        path = request.url.path
        if path in [
            "/docs", "/openapi.json", "/redoc",
            "/api/auth/login", "/api/auth/register",
            "/api/health", "/api/readiness", "/api/liveness"
        ] or path.startswith("/static"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            cookie_val = request.cookies.get("Authorization")
            if cookie_val:
                auth_header = cookie_val

        if not auth_header or not auth_header.startswith("Bearer "):
            # We don't block yet, we just allow the endpoint or lower handlers to inspect state.
            # However, we'll store guest status in request state.
            request.state.user = None
            return await call_next(request)

        token = auth_header.split(" ")[1]
        try:
            payload = self.jwt_manager.decode(token)
            request.state.user = payload
        except Exception:
            # Token failed to validate. Return 401.
            return Response(
                content='{"detail": "Invalid or expired token"}',
                status_code=status.HTTP_401_UNAUTHORIZED,
                media_type="application/json"
            )

        return await call_next(request)
