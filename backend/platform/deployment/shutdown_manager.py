"""Shutdown coordinator ensuring graceful service terminations and connections draining."""

import logging
from typing import List, Callable, Optional


class ShutdownManager:
    """Manages collection and invocation of cleanup routines during server exit."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes storage for handlers."""
        self._handlers: List[Callable[[], None]] = []
        self.logger = logger or logging.getLogger(__name__)

    def register_handler(self, handler: Callable[[], None]) -> None:
        """Registers a cleanup callback.

        Args:
            handler: Callable representing cleanup logic.
        """
        self._handlers.append(handler)

    def trigger_shutdown(self) -> None:
        """Executes all registered cleanup handlers sequentially, catching exceptions."""
        self.logger.info("Graceful shutdown initiated. Executing registered cleanup hooks...")
        for handler in reversed(self._handlers):
            try:
                handler()
            except Exception as e:
                self.logger.error(f"Error executing shutdown handler {handler.__name__}: {str(e)}")
        self.logger.info("Cleanup hooks complete. Server shutdown finished.")
