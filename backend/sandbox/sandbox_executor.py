"""Sandbox executor spawning subprocesses and capturing stdout/stderr safely."""

from __future__ import annotations

import os
import subprocess
import time
from typing import Dict, List, Optional

from backend.sandbox.models import CommandResult, SandboxConfig
from backend.sandbox.security_policy import SecurityPolicy


class SandboxExecutor:
    """Spawns subprocess commands within config limits and environments."""

    def __init__(self, config: SandboxConfig) -> None:
        self.config = config
        self.policy = SecurityPolicy(config)

    def execute(self, command_str: str, cwd: str) -> CommandResult:
        """Executes a command safely, capturing outputs and timing out if exceeded.

        Args:
            command_str: Shell command to execute.
            cwd: Working directory.

        Returns:
            CommandResult.
        """
        # 1. Validate security policy
        if not self.policy.validate_command(command_str):
            return CommandResult(
                stdout="",
                stderr="Security Error: Command is blocked or not in whitelist policy.",
                exit_code=-1,
                duration_ms=0.0,
            )

        start = time.perf_counter()
        # Isolated environment variables
        env = {"PATH": os.environ.get("PATH", "")}
        env.update(self.config.env_vars)

        try:
            # Spawn process safely
            proc = subprocess.Popen(
                command_str,
                shell=True,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            # Wait for execution with timeout
            stdout, stderr = proc.communicate(timeout=self.config.timeout_seconds)
            exit_code = proc.returncode
        except subprocess.TimeoutExpired as e:
            # Handle timeout
            proc.kill()
            stdout, stderr = e.stdout or "", e.stderr or ""
            stderr += f"\nTimeout Error: Execution exceeded {self.config.timeout_seconds} seconds limit."
            exit_code = -2
        except Exception as e:
            stdout, stderr = "", f"System Error: {e}"
            exit_code = -3

        duration = (time.perf_counter() - start) * 1000.0

        # Scan for generated files
        generated = []
        try:
            for f in os.listdir(cwd):
                full = os.path.join(cwd, f)
                # If modified after start, list it
                if os.path.isfile(full) and os.path.getmtime(full) * 1000.0 >= start * 1000.0:
                    generated.append(f)
        except Exception:
            pass

        return CommandResult(
            stdout=stdout or "",
            stderr=stderr or "",
            exit_code=exit_code,
            duration_ms=round(duration, 2),
            generated_files=generated,
        )
DefinitionPath = "sandbox_executor.py"
