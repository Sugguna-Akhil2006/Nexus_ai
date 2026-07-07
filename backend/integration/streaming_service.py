"""Streaming service coordinating token streams, progress updates, and connection lifecycle."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Optional, Union

from backend.intelligence.contracts.streaming_models import (
    StreamCancellationEvent,
    StreamCompletionEvent,
    StreamErrorEvent,
    StreamEventKind,
    StreamPartialResponseEvent,
    StreamProgressEvent,
    StreamSession,
    StreamTokenEvent,
)
from backend.runtime.event import Event, EventBus, EventPriority, EventType

logger = logging.getLogger("nexus.integration.streaming")


class StreamingService:
    """Manages active streaming sessions and generates standardized SSE events."""

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self._bus = event_bus or EventBus()
        self._sessions: Dict[str, StreamSession] = {}

    def create_session(self, request_id: str, module: str) -> StreamSession:
        """Initializes a new streaming session."""
        session = StreamSession(request_id=request_id, module=module)
        self._sessions[session.stream_id] = session
        return session

    def get_session(self, stream_id: str) -> Optional[StreamSession]:
        """Retrieves a streaming session by ID."""
        return self._sessions.get(stream_id)

    def cancel_session(self, stream_id: str, reason: str = "caller_cancelled") -> Optional[StreamCancellationEvent]:
        """Cancels an active streaming session."""
        session = self._sessions.get(stream_id)
        if not session:
            return None

        session.cancelled = True
        event = StreamCancellationEvent(
            stream_id=stream_id,
            request_id=session.request_id,
            reason=reason,
        )

        # Publish event
        self._bus.publish(
            Event(
                event_type=EventType.ANALYSIS_FAILED,
                priority=EventPriority.HIGH,
                payload={
                    "request_id": session.request_id,
                    "stream_id": stream_id,
                    "reason": reason,
                    "status": "cancelled",
                },
            )
        )
        return event

    async def generate_sse_stream(
        self,
        stream_id: str,
        token_generator: AsyncGenerator[str, None],
        progress_steps: Optional[AsyncGenerator[tuple[str, float], None]] = None,
    ) -> AsyncGenerator[str, None]:
        """Formats a raw token/progress stream into a line-by-line SSE-compliant format.

        Format:
        event: <kind>
        data: <json_string>
        """
        session = self._sessions.get(stream_id)
        if not session:
            yield f"event: error\ndata: {json.dumps({'message': 'Invalid session ID'})}\n\n"
            return

        start_time = datetime.utcnow()
        token_count = 0

        # Broadcast start progress
        yield self._format_sse(
            StreamProgressEvent(
                stream_id=stream_id,
                request_id=session.request_id,
                stage="started",
                message="Starting streaming output",
                percent_complete=0.0,
            )
        )

        try:
            # If progress steps are provided, yield them first or concurrently
            if progress_steps:
                try:
                    async for stage, pct in progress_steps:
                        if session.cancelled:
                            yield self._format_sse(
                                StreamCancellationEvent(
                                    stream_id=stream_id,
                                    request_id=session.request_id,
                                )
                            )
                            return
                        yield self._format_sse(
                            StreamProgressEvent(
                                stream_id=stream_id,
                                    request_id=session.request_id,
                                    stage=stage,
                                    percent_complete=pct,
                            )
                        )
                except Exception as e:
                    logger.error(f"Error yielding progress: {e}")

            # Yield tokens
            async for token in token_generator:
                if session.cancelled:
                    yield self._format_sse(
                        StreamCancellationEvent(
                            stream_id=stream_id,
                            request_id=session.request_id,
                        )
                    )
                    return

                token_count += 1
                yield self._format_sse(
                    StreamTokenEvent(
                        stream_id=stream_id,
                        request_id=session.request_id,
                        token=token,
                        cumulative_tokens=token_count,
                    )
                )

            # Mark completed
            session.completed = True
            duration = (datetime.utcnow() - start_time).total_seconds() * 1000.0
            yield self._format_sse(
                StreamCompletionEvent(
                    stream_id=stream_id,
                    request_id=session.request_id,
                    execution_id=f"exec-stream-{stream_id[-6:]}",
                    total_tokens=token_count,
                    duration_ms=duration,
                    final_confidence=0.9,
                )
            )

        except Exception as e:
            logger.error(f"Stream generation error: {e}")
            yield self._format_sse(
                StreamErrorEvent(
                    stream_id=stream_id,
                    request_id=session.request_id,
                    error_code="stream_execution_error",
                    message=str(e),
                )
            )

    def _format_sse(self, event: Union[StreamProgressEvent, StreamTokenEvent, StreamCompletionEvent, StreamCancellationEvent, StreamErrorEvent]) -> str:
        """Formats a Pydantic model into SSE protocol standard lines."""
        kind = event.kind.value
        data = event.model_dump_json()
        return f"event: {kind}\ndata: {data}\n\n"
