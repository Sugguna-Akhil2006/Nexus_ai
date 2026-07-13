"""Unit tests for Platform Circuit Breaker pattern."""

import unittest

from backend.platform.hardening.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException


class TestPlatformCircuitBreaker(unittest.TestCase):
    """Test suite covering circuit breaker thresholds, tripping, and half-open transitions."""

    def test_circuit_breaker_flow(self) -> None:
        """Verifies successive failures trip the breaker, blocking subsequent runs."""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout_seconds=0.2)

        calls = 0
        def failing_fn():
            nonlocal calls
            calls += 1
            raise ValueError("Downstream service failure")

        # Attempt 1
        with self.assertRaises(ValueError):
            cb.execute(failing_fn)
        self.assertEqual(cb.state, "CLOSED")

        # Attempt 2 (should trip to OPEN)
        with self.assertRaises(ValueError):
            cb.execute(failing_fn)
        self.assertEqual(cb.state, "OPEN")

        # Attempt 3 (blocked immediately)
        with self.assertRaises(CircuitBreakerOpenException):
            cb.execute(failing_fn)
        self.assertEqual(calls, 2)  # Function not run a third time
