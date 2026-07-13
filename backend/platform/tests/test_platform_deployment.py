"""Unit tests for Platform Deployment module."""

import os
import time
import unittest

from backend.platform.deployment.healthcheck import HealthCheckManager
from backend.platform.deployment.readiness import ReadinessChecker
from backend.platform.deployment.liveness import LivenessChecker
from backend.platform.deployment.startup_validator import StartupValidator
from backend.platform.deployment.shutdown_manager import ShutdownManager


class TestPlatformDeployment(unittest.TestCase):
    """Test suite covering health, liveness/readiness indicators, startup validations, and shutdowns."""

    def test_healthcheck_aggregation(self) -> None:
        """Verifies health states aggregation logic."""
        hm = HealthCheckManager()
        hm.register_checker("db", lambda: {"status": "healthy"})
        hm.register_checker("storage", lambda: {"status": "healthy"})

        res = hm.get_status()
        self.assertEqual(res["status"], "healthy")

        # Mock failure
        hm.register_checker("redis", lambda: {"status": "unhealthy"})
        res_fail = hm.get_status()
        self.assertEqual(res_fail["status"], "unhealthy")

    def test_readiness_checker(self) -> None:
        """Verifies readiness subchecks pass/fail calculations."""
        rc_ok = ReadinessChecker([lambda: True, lambda: True])
        self.assertTrue(rc_ok.is_ready())

        rc_fail = ReadinessChecker([lambda: True, lambda: False])
        self.assertFalse(rc_fail.is_ready())

    def test_liveness_checker(self) -> None:
        """Verifies liveness returns uptime metrics."""
        lc = LivenessChecker(time.time() - 10)
        res = lc.check()
        self.assertEqual(res["status"], "alive")
        self.assertGreaterEqual(res["uptime_seconds"], 10)

    def test_startup_validator(self) -> None:
        """Verifies environment variables presence and folder write accesses checks."""
        os.environ["TEST_ENV_KEY"] = "configured"
        sv = StartupValidator(required_envs=["TEST_ENV_KEY"], writable_dirs=["test_write_dir"])
        
        env_ok, missing = sv.validate_environment()
        self.assertTrue(env_ok)
        self.assertEqual(len(missing), 0)

        dir_ok, inaccessible = sv.validate_directories()
        self.assertTrue(dir_ok)
        self.assertEqual(len(inaccessible), 0)

        if os.path.exists("test_write_dir"):
            os.rmdir("test_write_dir")

    def test_shutdown_manager(self) -> None:
        """Verifies cleanup routines invocation sequence on shutdown."""
        sm = ShutdownManager()
        triggered = []

        sm.register_handler(lambda: triggered.append(1))
        sm.register_handler(lambda: triggered.append(2))

        sm.trigger_shutdown()
        # LIFO execution order (reversed)
        self.assertEqual(triggered, [2, 1])
