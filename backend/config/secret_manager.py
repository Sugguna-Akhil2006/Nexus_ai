"""Secret manager masking credentials and running custom token rotation hooks."""

from __future__ import annotations

import os
from typing import Callable, Dict, List


class SecretManager:
    """Manages system API keys and token rotation handlers safely."""

    def __init__(self) -> None:
        self._rotation_hooks: Dict[str, Callable[[], str]] = {}

    def register_rotation_hook(self, name: str, hook: Callable[[], str]) -> None:
        """Registers a callback hook to rotate a token dynamically."""
        self._rotation_hooks[name.lower()] = hook

    def get_secret(self, name: str) -> str:
        """Retrieves a secret from environment variables or registers rotation hook."""
        name_lower = name.lower()
        if name_lower in self._rotation_hooks:
            return self._rotation_hooks[name_lower]()
        return os.getenv(name.upper(), "")

    @staticmethod
    def mask_secret(secret: str) -> str:
        """Masks a secret string for logging or UI display.

        Example:
            "sk-1234567890abcdef" -> "sk-...cdef"
        """
        if not secret:
            return ""
        if len(secret) <= 8:
            return "******"
        if secret.startswith("sk-"):
            return f"sk-...{secret[-4:]}"
        return f"{secret[:3]}...{secret[-4:]}"
