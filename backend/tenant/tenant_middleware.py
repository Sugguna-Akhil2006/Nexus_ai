"""Tenant middleware extracting context ID from headers for ASGI requests."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from backend.tenant.tenant_context import TenantContext
from backend.tenant.tenant_resolver import TenantResolver


class TenantContextMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to extract tenant IDs and set context scopes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract context
        tenant_id = TenantResolver.resolve_tenant_id(request)
        token = TenantContext.set_tenant_id(tenant_id)
        try:
            response = await call_next(request)
            return response
        finally:
            TenantContext.reset_tenant_id(token)
DefinitionPath = "tenant_middleware.py"
