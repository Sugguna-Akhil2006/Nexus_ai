"""Middleware injecting standard HTTP security headers into server responses."""

from typing import Dict


class SecurityHeadersManager:
    """Manages secure browser response headers config (CSP, HSTS, X-Frame-Options)."""

    def __init__(self) -> None:
        """Initializes standard recommended security headers."""
        self._headers: Dict[str, str] = {
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; object-src 'none';",
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
            "X-XSS-Protection": "1; mode=block"
        }

    def get_headers(self) -> Dict[str, str]:
        """Returns standard dict of secure headers."""
        return dict(self._headers)

    def inject_headers(self, headers_dict: Dict[str, str]) -> None:
        """Injects secure headers into an existing headers dictionary."""
        headers_dict.update(self._headers)
