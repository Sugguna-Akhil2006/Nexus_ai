"""Tenant storage wrapper ensuring query isolation scoping."""

from __future__ import annotations

from typing import Any, List, Optional

from backend.tenant.tenant_context import TenantContext


class TenantStorageGuard:
    """Validates and alters queries to enforce tenant_id isolation parameters."""

    @staticmethod
    def apply_tenant_scope(sql: str, params: tuple) -> tuple[str, tuple]:
        """Injects tenant filtering constraints if tenant context is active.

        Args:
            sql: Base SQL query string.
            params: Tuple of SQL query values.

        Returns:
            Tuple of scoped SQL and scoped parameters.
        """
        tenant_id = TenantContext.get_tenant_id()
        if not tenant_id:
            return sql, params

        # Simplistic parser: append WHERE or AND clause
        # In a real environment, we'd parse AST or inject context into DB session binds
        if "WHERE" in sql.upper():
            scoped_sql = f"{sql} AND tenant_id = ?"
        else:
            scoped_sql = f"{sql} WHERE tenant_id = ?"

        scoped_params = params + (tenant_id,)
        return scoped_sql, scoped_params
DefinitionPath = "tenant_storage.py"
