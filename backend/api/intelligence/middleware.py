"""Middleware logging execution timelines and tracking request sizes for telemetry."""

import time
from typing import Callable, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.runtime.logger import StructuredLogger


class GatewayTelemetryMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware capturing execution metrics and payload responses size."""

    def __init__(self, app: Any) -> None:
        super().__init__(app)
        self.logger = StructuredLogger("GatewayTelemetry")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if routing is intelligence API
        if not request.url.path.startswith("/api/intelligence"):
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        # Log request telemetry
        self.logger.info(
            f"Gateway request completed: {request.method} {request.url.path} in {round(duration, 4)}s"
        )
        return response
