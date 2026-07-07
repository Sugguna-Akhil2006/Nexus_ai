"""Config watcher monitoring settings file updates to trigger hot-reloads safely."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger("nexus.config.watcher")


class ConfigWatcher:
    """Monitors a configuration file on disk and reloads parameters dynamically."""

    def __init__(
        self,
        config_path: str,
        reload_callback: Callable[[dict], None],
    ) -> None:
        self.config_path = config_path
        self.reload_callback = reload_callback
        self._last_modified: float = 0.0
        self._active: bool = False
        self._thread: Optional[threading.Thread] = None

        if os.path.exists(config_path):
            self._last_modified = os.path.getmtime(config_path)

    def start(self) -> None:
        """Launches the background file monitor thread."""
        self._active = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stops the file monitor thread."""
        self._active = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def force_check(self) -> None:
        """Forces checking file timestamp modifications and reloads."""
        if not os.path.exists(self.config_path):
            return
        mtime = os.path.getmtime(self.config_path)
        if mtime > self._last_modified:
            self._last_modified = mtime
            self._reload_file()

    def _watch_loop(self) -> None:
        while self._active:
            try:
                self.force_check()
            except Exception as e:
                logger.error(f"Error checking config file modification: {e}")
            time.sleep(1.0)

    def _reload_file(self) -> None:
        try:
            with open(self.config_path, "r") as f:
                data = json.load(f)
            self.reload_callback(data)
            logger.info(f"Hot-reloaded configuration settings from: {self.config_path}")
        except Exception as e:
            logger.error(f"Hot-reload failed to parse new settings: {e}")
DefinitionPath = "config_watcher.py"
