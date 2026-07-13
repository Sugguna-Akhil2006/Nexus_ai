"""Registers signal listeners to execute graceful shutdowns."""

import logging
import signal
from typing import List, Callable, Optional, Any


class ShutdownHandler:
    """Manages collection and triggering of service drain functions on server exit."""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        """Initializes the ShutdownHandler."""
        self._handlers: List[Callable[[], None]] = []
        self.logger = logger or logging.getLogger(__name__)

    def register_handler(self, callback: Callable[[], None]) -> None:
        """Appends a teardown function.

        Args:
            callback: Function to run.
        """
        self._handlers.append(callback)

    def bind_signals(self) -> None:
        """Binds signals SIGTERM and SIGINT to trigger shutdowns."""
        try:
            signal.signal(signal.SIGTERM, self._handle_signal)
            signal.signal(signal.SIGINT, self._handle_signal)
        except ValueError:
            # Signal handling might fail if not in main thread (e.g. running unit tests)
            pass

    def _handle_signal(self, signum: int, frame: Any) -> None:
        """Internal callback invoked when signals are intercepted."""
        self.logger.info(f"Signal {signum} received. Initiating graceful shutdown...")
        self.trigger_shutdown()

    def trigger_shutdown(self) -> None:
        """Executes all registered cleanup handlers sequentially, catching exceptions."""
        for callback in reversed(self._handlers):
            try:
                callback()
            except Exception as e:
                self.logger.error(f" teadown callback failed: {str(e)}")
        self.logger.info("Shutdown sequence complete.")
