"""Circuit Breaker pattern implementing Open, Closed, and Half-Open states."""

import time
import threading
from typing import Callable, Any, TypeVar

T = TypeVar("T")


class CircuitBreakerOpenException(Exception):
    """Exception raised when calls are blocked by an Open circuit breaker."""
    pass


class CircuitBreaker:
    """Protects downstream services from cascading errors."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout_seconds: float = 30.0) -> None:
        """Initializes the circuit breaker.

        Args:
            failure_threshold: Consecutive failures to trip the circuit.
            recovery_timeout_seconds: Seconds to wait before attempting recovery.
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN
        self.failure_count = 0
        self.last_state_change = time.time()
        self._lock = threading.Lock()

    def execute(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes a function through the circuit breaker protection.

        Args:
            func: Function to execute.
            args: Positional args.
            kwargs: Keyword args.
        """
        with self._lock:
            self._evaluate_state()
            if self.state == "OPEN":
                raise CircuitBreakerOpenException("Circuit breaker is currently OPEN. Execution blocked.")

        try:
            res = func(*args, **kwargs)
            
            with self._lock:
                if self.state == "HALF-OPEN":
                    # Success in half-open state resets circuit
                    self._reset()
                else:
                    self.failure_count = 0
            return res
        except Exception as e:
            with self._lock:
                self._record_failure()
            raise e

    def _evaluate_state(self) -> None:
        """Evaluates state transitions based on timeouts."""
        if self.state == "OPEN":
            if time.time() - self.last_state_change > self.recovery_timeout:
                self.state = "HALF-OPEN"
                self.last_state_change = time.time()

    def _record_failure(self) -> None:
        """Increments error counts and trips circuit if threshold exceeded."""
        self.failure_count += 1
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.last_state_change = time.time()
        elif self.state == "HALF-OPEN":
            # Any failure in half-open trips back to open
            self.state = "OPEN"
            self.last_state_change = time.time()

    def _reset(self) -> None:
        """Resets failure counts and transitions to CLOSED."""
        self.state = "CLOSED"
        self.failure_count = 0
        self.last_state_change = time.time()
