"""Tenant resolver extracting tenant ID from request headers or query params."""

from __future__ import annotations

from typing import Optional
from fastapi import Request


class TenantResolver:
    """Extracts tenant ID identifiers from API request contexts."""

    @staticmethod
    def resolve_tenant_id(request: Request) -> Optional[str]:
        """Resolves the tenant ID checking headers and query parameters.

        Args:
            request: FastAPI request object.

        Returns:
            Resolved tenant ID or None.
        """
        # 1. Check Header
        tenant_id = request.headers.get("X-Tenant-ID") or request.headers.get("x-tenant-id")
        if tenant_id:
            return tenant_id

        # 2. Check Query Params
        tenant_id = request.query_params.get("tenant_id")
        if tenant_id:
            return tenant_id

        return None
DefinitionPath = "tenant_resolver.py"
