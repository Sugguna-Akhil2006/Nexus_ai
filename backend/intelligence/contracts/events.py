"""Intelligence API event contracts — published to the EventBus on analysis lifecycle changes.

All events reference ``EventType`` enum members so that downstream
subscribers (Session Intelligence, Observability, Platform Ops) can
consume them without coupling to intelligence internals.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from backend.runtime.event import Event, EventBus, EventPriority, EventType


# ---------------------------------------------------------------------------
# Event payload models
# ---------------------------------------------------------------------------


class AnalysisStartedPayload(BaseModel):
    """Payload for the ``analysis.started`` event."""

    request_id: str
    execution_id: str
    module: str
    workspace_id: str
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisProgressPayload(BaseModel):
    """Payload for the ``analysis.progress`` event."""

    request_id: str
    execution_id: str
    module: str
    stage: str
    percent_complete: float = 0.0
    message: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisCompletedPayload(BaseModel):
    """Payload for the ``analysis.completed`` event."""

    request_id: str
    execution_id: str
    module: str
    status: str
    confidence: float = 0.0
    duration_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisFailedPayload(BaseModel):
    """Payload for the ``analysis.failed`` event."""

    request_id: str
    execution_id: str
    module: str
    error_code: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ---------------------------------------------------------------------------
# Publisher helper
# ---------------------------------------------------------------------------


class AnalysisEventPublisher:
    """Publishes standardized analysis lifecycle events to the EventBus.

    Designed to be used by adapters that bridge ``IntelligenceRequest``
    to the internal module execution pipeline.

    Args:
        event_bus: Optional override for testing; defaults to singleton.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._bus = event_bus or EventBus()

    def publish_started(self, payload: AnalysisStartedPayload) -> None:
        """Publishes ``analysis.started``."""
        self._bus.publish(Event(
            event_type=EventType.ANALYSIS_STARTED,
            priority=EventPriority.NORMAL,
            payload=payload.model_dump(),
        ))

    def publish_progress(self, payload: AnalysisProgressPayload) -> None:
        """Publishes ``analysis.progress``."""
        self._bus.publish(Event(
            event_type=EventType.ANALYSIS_PROGRESS,
            priority=EventPriority.LOW,
            payload=payload.model_dump(),
        ))

    def publish_completed(self, payload: AnalysisCompletedPayload) -> None:
        """Publishes ``analysis.completed``."""
        self._bus.publish(Event(
            event_type=EventType.ANALYSIS_COMPLETED,
            priority=EventPriority.NORMAL,
            payload=payload.model_dump(),
        ))

    def publish_failed(self, payload: AnalysisFailedPayload) -> None:
        """Publishes ``analysis.failed``."""
        self._bus.publish(Event(
            event_type=EventType.ANALYSIS_FAILED,
            priority=EventPriority.HIGH,
            payload=payload.model_dump(),
        ))
