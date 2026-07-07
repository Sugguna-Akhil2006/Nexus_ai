"""Network policy managing network access rules within the secure sandbox."""

from __future__ import annotations

from typing import List, Optional


class NetworkPolicy:
    """Restricts or logs outbound requests originating from sandbox sessions."""

    def __init__(self, allowed_hosts: Optional[List[str]] = None) -> None:
        self.allowed_hosts = allowed_hosts or ["github.com", "pypi.org", "python.org"]

    def is_host_allowed(self, host: str) -> bool:
        """Returns True if the connection host is whitelisted."""
        if not host:
            return False
        host_lower = host.lower()
        return any(h in host_lower for h in self.allowed_hosts)
