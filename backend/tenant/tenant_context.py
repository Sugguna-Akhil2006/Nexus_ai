"""Tenant context manager maintaining task-local tenant variable states."""

from __future__ import annotations

import contextvars
from typing import Optional

# Task-local storage variable tracking the active tenant ID
_current_tenant_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_tenant_id", default=None)


class TenantContext:
    """Manages setting and retrieving the current active tenant ID in the call stack."""

    @staticmethod
    def get_tenant_id() -> Optional[str]:
        """Retrieves the active tenant ID from local task context."""
        return _current_tenant_id.get()

    @staticmethod
    def set_tenant_id(tenant_id: Optional[str]) -> contextvars.Token:
        """Sets the active tenant ID in local task context.

        Args:
            tenant_id: Target tenant ID string.

        Returns:
            A contextvars Token to reset context.
        """
        return _current_tenant_id.set(tenant_id)

    @staticmethod
    def reset_tenant_id(token: contextvars.Token) -> None:
        """Resets the active tenant ID to its previous state."""
        _current_tenant_id.reset(token)
