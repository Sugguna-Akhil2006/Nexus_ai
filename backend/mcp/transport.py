"""MCP Transport layer framing and dispatching JSON-RPC requests."""

from __future__ import annotations

import json
import threading
from typing import Callable, Optional


class StdioTransport:
    """Stdio or memory-based transport channel managing message serialization."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._on_message_callback: Optional[Callable[[str], None]] = None

    def set_on_message(self, callback: Callable[[str], None]) -> None:
        """Sets the message receiver callback."""
        with self._lock:
            self._on_message_callback = callback

    def send_message(self, message_str: str) -> None:
        """Sends framed message payload string."""
        # Standard stdout stream or proxy receiver simulation
        pass

    def receive_raw_payload(self, payload: str) -> None:
        """Simulates receiving raw framed data from the other peer."""
        callback = None
        with self._lock:
            callback = self._on_message_callback
        
        if callback:
            callback(payload)
