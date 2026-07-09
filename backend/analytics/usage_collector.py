"""Usage collector capturing anonymous operational metrics and usage patterns."""

from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from backend.analytics.models import MetricRecord, MetricType


class UsageCollector:
    """Thread-safe collector gathering raw platform usage and telemetry events."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._metrics: List[MetricRecord] = []

    def collect(
        self,
        metric_type: MetricType,
        name: str,
        value: float,
        context: Optional[Dict] = None,
    ) -> MetricRecord:
        """Appends a new operational metric record to the collection."""
        record = MetricRecord(
            metric_id=str(uuid.uuid4())[:8],
            metric_type=metric_type,
            name=name,
            value=value,
            context=context or {},
        )
        with self._lock:
            self._metrics.append(record)
        return record

    def list_metrics(self) -> List[MetricRecord]:
        """Returns all collected raw metric records."""
        with self._lock:
            return list(self._metrics)

    def clear(self) -> None:
        """Wipes the metrics list."""
        with self._lock:
            self._metrics.clear()
