"""Security policy implementing command whitelist and blacklist rules."""

from __future__ import annotations

import shlex
from typing import List

from backend.sandbox.models import SandboxConfig


class SecurityPolicy:
    """Audits command strings against allowed whitelists and blocked commands."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config

    def validate_command(self, command_str: str) -> bool:
        """Validates command structure and commands string tokens.

        Args:
            command_str: Raw shell command.

        Returns:
            True if allowed under current config policy constraints.
        """
        if not command_str:
            return False

        try:
            tokens = shlex.split(command_str)
        except Exception:
            return False

        if not tokens:
            return False

        base_cmd = tokens[0].lower()

        # 1. Blocked commands check
        for blocked in self.config.blocked_commands:
            if blocked in command_str.lower():
                return False

        # 2. Whitelisted base command check
        # Allow command if the base executable is whitelisted
        is_allowed = False
        for allowed in self.config.allowed_commands:
            if allowed.lower() in base_cmd:
                is_allowed = True
                break

        return is_allowed
