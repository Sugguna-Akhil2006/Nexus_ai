"""Integration tests validating the Frontend Integration Layer.

Covers:
- Progress publication and adapter orchestration.
- WebSocket manager subscription and broadcasts.
- Streaming service SSE rendering and cancellation.
- Report formatter layouts (JSON, Markdown, HTML, PDF metadata).
- Concurrent user operations.
"""

from __future__ import annotations

import asyncio
import json
import unittest
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List

from backend.intelligence.contracts.request_models import (
    Attachment,
    AttachmentType,
    IntelligenceModule,
    IntelligenceRequest,
    RequestOptions,
)
from backend.intelligence.contracts.response_models import (
    Artifact,
    Citation,
    ExecutionMetrics,
    IntelligenceResponse,
    Recommendation,
    ResponseStatus,
)
from backend.integration.artifact_serializer import ArtifactSerializer
from backend.integration.frontend_adapter import FrontendAdapter
from backend.integration.frontend_contracts import ReportFormat
from backend.integration.report_formatter import ReportFormatter
from backend.integration.streaming_service import StreamingService
from backend.integration.websocket_manager import WebSocketManager
from backend.runtime.event import EventBus


class MockWebSocket:
    """Mock WebSocket matching FastAPI interface for integration testing."""

    def __init__(self) -> None:
        self.accepted = False
        self.sent_messages: List[Dict[str, Any]] = []
        self.closed = False

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, data: Any) -> None:
        self.sent_messages.append(data)

    async def close(self) -> None:
        self.closed = True


class TestWebSocketManager(unittest.IsolatedAsyncioTestCase):
    """Validates WebSocket registration, scopes, and broadcasts."""

    async def test_connection_and_broadcast(self) -> None:
        mgr = WebSocketManager()
        ws1 = MockWebSocket()
        ws2 = MockWebSocket()

        await mgr.connect(ws1, workspace_id="ws-1")
        await mgr.connect(ws2, workspace_id="ws-1", request_id="req-101")

        self.assertTrue(ws1.accepted)
        self.assertTrue(ws2.accepted)

        # Broadcast to workspace
        await mgr.broadcast("ws-1", {"event": "hello"})
        self.assertEqual(len(ws1.sent_messages), 1)
        self.assertEqual(len(ws2.sent_messages), 1)
        self.assertEqual(ws1.sent_messages[0]["event"], "hello")

        # Disconnect ws1
        mgr.disconnect(ws1, workspace_id="ws-1")
        await mgr.broadcast("ws-1", {"event": "world"})
        self.assertEqual(len(ws1.sent_messages), 1)  # unchanged
        self.assertEqual(len(ws2.sent_messages), 2)  # received second event


class TestStreamingService(unittest.IsolatedAsyncioTestCase):
    """Validates SSE formatting, cancellation, and completions."""

    async def test_sse_streaming_flow(self) -> None:
        service = StreamingService()
        session = service.create_session("req-abc", "resume")
        self.assertIsNotNone(session.stream_id)

        # Helper token generator
        async def token_gen() -> AsyncGenerator[str, None]:
            yield "Hello "
            yield "world!"

        sse_output = []
        async for line in service.generate_sse_stream(session.stream_id, token_gen()):
            sse_output.append(line)

        # Check line counts (started, token 1, token 2, completed = 4 events)
        self.assertEqual(len(sse_output), 4)
        self.assertIn("event: progress", sse_output[0])
        self.assertIn("event: token", sse_output[1])
        self.assertIn("event: token", sse_output[2])
        self.assertIn("event: completion", sse_output[3])

    async def test_streaming_cancellation(self) -> None:
        service = StreamingService()
        session = service.create_session("req-cancel", "github")

        # Cancel the session mid-stream
        service.cancel_session(session.stream_id, reason="user_abort")
        self.assertTrue(session.cancelled)

        async def token_gen() -> AsyncGenerator[str, None]:
            yield "token1"

        sse_output = []
        async for line in service.generate_sse_stream(session.stream_id, token_gen()):
            sse_output.append(line)

        # Output must contain started + cancellation events
        self.assertEqual(len(sse_output), 2)
        self.assertIn("event: cancellation", sse_output[1])


class TestReportFormatter(unittest.TestCase):
    """Validates serialization outputs for all standard formats."""

    def setUp(self) -> None:
        from backend.intelligence.composition.models import ComposedResponse, AggregatedConfidence, ConfidenceStrategy
        self.report = ComposedResponse(
            request_id="req-f",
            executive_summary="The analysis is successful.",
            participating_modules=["resume", "github"],
            aggregated_confidence=AggregatedConfidence(
                overall=0.85,
                strategy=ConfidenceStrategy.AVERAGE,
            ),
        )

    def test_markdown_format(self) -> None:
        res = ReportFormatter.format(self.report, ReportFormat.MARKDOWN, "req-f")
        self.assertEqual(res.content_type, "text/markdown")
        self.assertIn("# Intelligence Analysis Report", res.content)
        self.assertIn("The analysis is successful.", res.content)

    def test_html_format(self) -> None:
        res = ReportFormatter.format(self.report, ReportFormat.HTML, "req-f")
        self.assertEqual(res.content_type, "text/html")
        self.assertIn("<!DOCTYPE html>", res.content)
        self.assertIn("The analysis is successful.", res.content)

    def test_pdf_metadata_format(self) -> None:
        res = ReportFormatter.format(self.report, ReportFormat.PDF_METADATA, "req-f")
        self.assertEqual(res.content_type, "application/json")
        meta = json.loads(res.content)
        self.assertEqual(meta["title"], "Nexus AI Intelligence Analysis Report")


class TestFrontendAdapter(unittest.IsolatedAsyncioTestCase):
    """Validates end-to-end multi-module execution with WebSocket tracking."""

    async def test_full_adapter_execution(self) -> None:
        mgr = WebSocketManager()
        ws = MockWebSocket()
        await mgr.connect(ws, workspace_id="ws-test")

        adapter = FrontendAdapter(ws_manager=mgr)

        request = IntelligenceRequest(
            workspace_id="ws-test",
            user_id="user-123",
            module=IntelligenceModule.RESUME,
            input={"resume_text": "Sample"},
        )

        formatted = await adapter.execute_and_compose(
            request=request,
            target_modules=["resume", "github"],
            output_format=ReportFormat.JSON,
        )

        self.assertIsNotNone(formatted.content)
        self.assertEqual(formatted.format, ReportFormat.JSON)

        # Check WebSocket messages sent during execution
        events = [m["kind"] for m in ws.sent_messages]
        self.assertIn("workflow.started", events)
        self.assertIn("module.started", events)
        self.assertIn("module.completed", events)
        self.assertIn("workflow.progress", events)
        self.assertIn("analysis.completed", events)


class TestConcurrentUsers(unittest.IsolatedAsyncioTestCase):
    """Validates concurrent execution profiles under simultaneous loads."""

    async def test_parallel_adapter_runs(self) -> None:
        mgr = WebSocketManager()
        adapter = FrontendAdapter(ws_manager=mgr)

        async def run_one(user_id: str) -> str:
            req = IntelligenceRequest(
                workspace_id="ws-conc",
                user_id=user_id,
                module=IntelligenceModule.RESUME,
                input={"resume_text": f"Content of {user_id}"},
            )
            report = await adapter.execute_and_compose(
                request=req,
                target_modules=["resume"],
            )
            return report.request_id

        tasks = [run_one(f"user-{i}") for i in range(10)]
        results = await asyncio.gather(*tasks)

        self.assertEqual(len(results), 10)
        self.assertEqual(len(set(results)), 10)  # All requests processed uniquely
