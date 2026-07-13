"""Request logger middleware tracing requests with correlation IDs."""

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from backend.ops.logging.structured_logger import set_trace_context, clear_trace_context


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Interceptors logging request latencies, and binding trace IDs."""

    def __init__(self, app, logger_name: str = "nexus_ops") -> None:
        """Initializes settings."""
        super().__init__(app)
        self.logger = logging.getLogger(logger_name)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Inspects request headers, sets trace details, and logs duration.

        Args:
            request: The incoming request.
            call_next: Next route handler.
        """
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-ID") or req_id
        
        set_trace_context(req_id, trace_id)
        start_time = time.time()
        
        self.logger.info(f"Incoming Request: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
            duration = round((time.time() - start_time) * 1000, 2)
            self.logger.info(f"Completed Request: {request.method} {request.url.path} - Status {response.status_code} in {duration}ms")
            response.headers["X-Request-ID"] = req_id
            return response
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            self.logger.error(f"Failed Request: {request.method} {request.url.path} in {duration}ms - Error: {str(e)}", exc_info=True)
            raise
        finally:
            clear_trace_context()
