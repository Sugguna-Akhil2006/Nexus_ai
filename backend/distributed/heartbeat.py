"""Heartbeat monitor detecting stale worker nodes and triggering failover."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from typing import Callable, Optional

from backend.distributed.models import WorkerNode
from backend.distributed.worker_registry import WorkerRegistry
from backend.runtime.logger import StructuredLogger


class HeartbeatMonitor:
    """Background thread monitoring worker heartbeats and evicting stale nodes.

    Workers must call :meth:`record_heartbeat` regularly. Nodes that miss
    heartbeats beyond ``timeout_seconds`` are marked offline.

    Args:
        registry: WorkerRegistry to query and update.
        timeout_seconds: Seconds of silence before a node is declared offline.
        poll_interval_seconds: Check frequency in seconds.
        on_node_offline: Optional callback invoked with node_id when evicted.
    """

    def __init__(
        self,
        registry: WorkerRegistry,
        timeout_seconds: float = 30.0,
        poll_interval_seconds: float = 5.0,
        on_node_offline: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._registry = registry
        self._timeout = timeout_seconds
        self._poll_interval = poll_interval_seconds
        self._on_node_offline = on_node_offline
        self._logger = StructuredLogger()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def record_heartbeat(self, node_id: str) -> None:
        """Records a heartbeat from the given node, resetting its liveness timer.

        Args:
            node_id: Identifier of the pinging node.
        """
        node = self._registry.get_node(node_id)
        if node:
            with self._lock:
                node.last_heartbeat = datetime.utcnow()

    def start(self) -> None:
        """Starts the background heartbeat monitor thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True, name="HeartbeatMonitor")
        self._thread.start()
        self._logger.info("HeartbeatMonitor started.")

    def stop(self) -> None:
        """Stops the background monitor thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._poll_interval + 1)
        self._logger.info("HeartbeatMonitor stopped.")

    def _monitor_loop(self) -> None:
        """Internal polling loop that checks node liveness."""
        while self._running:
            self._check_nodes()
            time.sleep(self._poll_interval)

    def _check_nodes(self) -> None:
        """Marks nodes offline whose last heartbeat has exceeded the timeout."""
        cutoff = datetime.utcnow() - timedelta(seconds=self._timeout)
        for node in self._registry.list_online_nodes():
            if node.last_heartbeat < cutoff:
                self._logger.warning(
                    f"Node '{node.node_id}' missed heartbeat. Last seen: {node.last_heartbeat.isoformat()}"
                )
                self._registry.mark_offline(node.node_id)
                if self._on_node_offline:
                    try:
                        self._on_node_offline(node.node_id)
                    except Exception as exc:
                        self._logger.error(f"Failover callback error for '{node.node_id}': {exc}")
