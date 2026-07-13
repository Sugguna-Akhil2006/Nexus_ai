"""Retry manager with exponential backoff algorithms."""

import time
from typing import Callable, Any, TypeVar, Tuple

T = TypeVar("T")


class RetryManager:
    """Handles execution of operations with configurable retry logic and exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions_to_retry: Tuple[type[Exception], ...] = (Exception,)
    ) -> None:
        """Initializes settings.

        Args:
            max_attempts: Maximum run attempts.
            initial_delay: Initial sleep duration in seconds.
            backoff_factor: Multiplier for backoff sequence.
            exceptions_to_retry: Tuple of exceptions to intercept.
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.exceptions = exceptions_to_retry

    def execute(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executes a function, retrying with exponential backoff if configured exceptions occur.

        Args:
            operation: Callable function to execute.
            args: Positional args.
            kwargs: Keyword args.
        """
        attempt = 1
        delay = self.initial_delay
        while True:
            try:
                return operation(*args, **kwargs)
            except self.exceptions as e:
                if attempt >= self.max_attempts:
                    raise e
                
                time.sleep(delay)
                attempt += 1
                delay *= self.backoff_factor
