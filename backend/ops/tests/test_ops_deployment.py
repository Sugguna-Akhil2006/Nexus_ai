"""Unit tests for Operations Deployment package."""

import os
import unittest

from backend.ops.deployment.environment_validator import EnvironmentValidator
from backend.ops.deployment.startup_checker import StartupChecker
from backend.ops.deployment.shutdown_handler import ShutdownHandler


class TestOpsDeployment(unittest.TestCase):
    """Test suite covering operational deployment settings and graceful draining."""

    def test_environment_validator(self) -> None:
        """Verifies environment variables validator catches missing configurations."""
        os.environ["TEST_VALID_KEY"] = "true"
        validator = EnvironmentValidator(required_keys=["TEST_VALID_KEY"])
        ok, msg = validator.validate_env()
        self.assertTrue(ok)

        # Missing key
        bad_validator = EnvironmentValidator(required_keys=["TEST_MISSING_KEY"])
        ok_fail, msg_fail = bad_validator.validate_env()
        self.assertFalse(ok_fail)
        self.assertIn("TEST_MISSING_KEY", msg_fail)

    def test_startup_checker(self) -> None:
        """Verifies write permissions validations on startup paths."""
        checker = StartupChecker(writable_dirs=["test_ops_write"])
        ok, msg = checker.check_startup_integrity()
        self.assertTrue(ok)
        
        # Cleanup
        if os.path.exists("test_ops_write"):
            os.rmdir("test_ops_write")

    def test_shutdown_handler(self) -> None:
        """Verifies shutdown coordinator triggers LIFO callbacks."""
        handler = ShutdownHandler()
        stack = []

        handler.register_handler(lambda: stack.append(1))
        handler.register_handler(lambda: stack.append(2))
        
        handler.trigger_shutdown()
        self.assertEqual(stack, [2, 1])
