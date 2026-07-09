"""Unit and integration tests for the Secure Execution Sandbox."""

from __future__ import annotations

import os
import unittest
from datetime import datetime

from backend.sandbox.artifact_collector import ArtifactCollector
from backend.sandbox.execution_session import ExecutionSession
from backend.sandbox.filesystem_guard import FilesystemGuard
from backend.sandbox.models import SandboxConfig
from backend.sandbox.network_policy import NetworkPolicy
from backend.sandbox.resource_limiter import ResourceLimiter
from backend.sandbox.sandbox_executor import SandboxExecutor
from backend.sandbox.sandbox_manager import SandboxManager
from backend.sandbox.security_policy import SecurityPolicy


class TestSecurityPolicy(unittest.TestCase):
    """Verifies allowed whitelists and blocked commands."""

    def setUp(self) -> None:
        self.config = SandboxConfig()
        self.policy = SecurityPolicy(self.config)

    def test_allowed_commands(self) -> None:
        self.assertTrue(self.policy.validate_command("python script.py"))
        self.assertTrue(self.policy.validate_command("echo hello"))

    def test_blocked_commands(self) -> None:
        self.assertFalse(self.policy.validate_command("rm -rf /"))
        self.assertFalse(self.policy.validate_command("del file.txt"))
        self.assertFalse(self.policy.validate_command("format C:"))


class TestFilesystemGuard(unittest.TestCase):
    """Verifies directory traversal and path protections."""

    def test_safe_paths(self) -> None:
        root = os.path.abspath("workspace")
        target = os.path.abspath(os.path.join(root, "sub", "file.txt"))
        self.assertTrue(FilesystemGuard.is_safe_path(root, target))

    def test_unsafe_paths(self) -> None:
        root = os.path.abspath("workspace")
        target = os.path.abspath(os.path.join(root, "..", "secret.txt"))
        self.assertFalse(FilesystemGuard.is_safe_path(root, target))


class TestNetworkPolicy(unittest.TestCase):
    """Verifies host connection access controls."""

    def test_host_whitelists(self) -> None:
        policy = NetworkPolicy()
        self.assertTrue(policy.is_host_allowed("github.com"))
        self.assertFalse(policy.is_host_allowed("malicious.site"))


class TestResourceLimiter(unittest.TestCase):
    """Verifies CPU, memory, and timeout threshold constraints."""

    def setUp(self) -> None:
        self.config = SandboxConfig(timeout_seconds=2, max_memory_mb=100)
        self.limiter = ResourceLimiter(self.config)

    def test_within_limits(self) -> None:
        self.assertTrue(self.limiter.check_limits(1000.0, 1024 * 1024 * 10))

    def test_outside_limits(self) -> None:
        # Timeout exceeded
        self.assertFalse(self.limiter.check_limits(3000.0, 1024 * 1024 * 10))
        # Memory exceeded
        self.assertFalse(self.limiter.check_limits(1000.0, 1024 * 1024 * 120))


class TestSandboxExecutor(unittest.TestCase):
    """Verifies command execution outcomes and timeout handles."""

    def setUp(self) -> None:
        self.config = SandboxConfig(timeout_seconds=1.0)
        self.executor = SandboxExecutor(self.config)

    def test_execute_echo(self) -> None:
        res = self.executor.execute("echo hello", os.path.abspath("."))
        self.assertEqual(res.exit_code, 0)
        self.assertIn("hello", res.stdout.strip())

    def test_execute_timeout(self) -> None:
        # Trigger timeout using a python script that sleeps
        res = self.executor.execute("python -c \"import time; time.sleep(3)\"", os.path.abspath("."))
        self.assertEqual(res.exit_code, -2)
        self.assertIn("Timeout Error", res.stderr)


class TestSandboxSessionE2E(unittest.TestCase):
    """Verifies complete session lifecycles, uploads, and cleanups."""

    def setUp(self) -> None:
        self.mgr = SandboxManager()

    def tearDown(self) -> None:
        self.mgr.shutdown()

    def test_session_lifecycle(self) -> None:
        sess_info = self.mgr.create_session()
        session_id = sess_info.session_id
        self.assertEqual(sess_info.status, "active")

        # Upload a file
        filename = "input.txt"
        content = b"hello sandbox"
        success = self.mgr.upload_to_session(session_id, filename, content)
        self.assertTrue(success)

        # Run command to check file
        res = self.mgr.execute_in_session(session_id, "python -c \"with open('input.txt') as f: print(f.read())\"")
        self.assertEqual(res.exit_code, 0)
        self.assertIn("hello sandbox", res.stdout.strip())

        # Download artifact
        data = self.mgr.download_from_session(session_id, filename)
        self.assertEqual(data, content)

        # Terminate
        terminated = self.mgr.terminate_session(session_id)
        self.assertTrue(terminated)
        self.assertIsNone(self.mgr.get_session(session_id))
