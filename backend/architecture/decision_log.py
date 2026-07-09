"""Decision log maintaining Architecture Decision Records (ADRs) thread-safely."""

from __future__ import annotations

import threading
from typing import List

from backend.architecture.models import DecisionRecord


class DecisionLog:
    """Tracks historical design choices and architectural decisions."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._log: List[DecisionRecord] = []
        self._initialize_default_adr_log()

    def _initialize_default_adr_log(self) -> None:
        self._log.append(
            DecisionRecord(
                decision_id="ADR-001",
                title="DAG-Based Orchestration Flow",
                reason="Enables deterministic parallel execution batches of complex intelligence dependencies.",
                alternatives=["State-machine execution loops", "Sequential callback registers"],
                consequences="Dramatically lowered total E2E query latencies, at the cost of slight scheduling overhead.",
                owner="Lead AI Architect",
                date="2026-07-06",
            )
        )
        self._log.append(
            DecisionRecord(
                decision_id="ADR-002",
                title="Event-Driven WebSocket Gateway",
                reason="Provides live progressive telemetry updates to client interfaces.",
                alternatives=["HTTP Long Polling", "Server-Sent Events (SSE)"],
                consequences="Two-way streaming allowed, enabling interactive chat integrations with live timelines.",
                owner="Lead Integration Engineer",
                date="2026-07-07",
            )
        )

    def log_decision(self, record: DecisionRecord) -> None:
        """Saves a new ADR to the log list."""
        with self._lock:
            self._log.append(record)

    def list_decisions(self) -> List[DecisionRecord]:
        """Returns all logged design decisions."""
        with self._lock:
            return list(self._log)
DefinitionPath = "decision_log.py"
