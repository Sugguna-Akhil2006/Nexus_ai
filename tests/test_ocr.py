import concurrent.futures
import time
from typing import Any, Dict, List, Optional
import unittest
import uuid

from core.ocr import (
    OCRError,
    OCRValidationError,
    OCRProviderError,
    OCRRequest,
    OCRTextBlock,
    OCRPage,
    OCRResult,
    LayoutTablePlaceholder,
    LayoutFormPlaceholder,
    LayoutAnalysis,
    OCRProvider,
    MockOCRProvider,
    OCRRegistry,
    OCRAgent,
    validate_image_format,
    validate_ocr_content,
    validate_language_code,
    extract_layout,
)
from core.base import AgentState, AgentStatus
from core.event import Event, EventBus, EventType
from core.task import Task


class MockEventReceiver:
    """Helper to collect emitted events from the EventBus."""

    def __init__(self) -> None:
        self.events: List[Event] = []

    def handle(self, event: Event) -> None:
        self.events.append(event)


class TestOCRSystem(unittest.TestCase):
    """Suite of tests covering OCR layout and text extraction layer."""

    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.event_bus.clear()
        self.receiver = MockEventReceiver()
        self.event_bus.subscribe(EventType.CUSTOM_EVENT, self.receiver.handle)

        self.registry = OCRRegistry()
        with self.registry._lock:
            self.registry._providers.clear()

        self.provider = MockOCRProvider()
        self.registry.register_provider("mock", self.provider)

        self.agent = OCRAgent()
        self.agent.initialize()

    def test_validation_utilities(self) -> None:
        """Verifies validations enforce formats, contents, and languages ISO rules."""
        # Formats
        validate_image_format("scanned.pdf")
        validate_image_format("diagram.png")
        validate_image_format("capture.webp")

        with self.assertRaises(OCRValidationError):
            validate_image_format("unsupported.txt")
        with self.assertRaises(OCRValidationError):
            validate_image_format("archive.zip")

        # Content payload
        validate_ocr_content(b"scanned image binary payload")
        with self.assertRaises(OCRValidationError):
            validate_ocr_content(b"")
        with self.assertRaises(OCRValidationError):
            validate_ocr_content(None)  # type: ignore

        # Language ISO checking
        validate_language_code("en")
        validate_language_code("eng")
        validate_language_code("DE")

        with self.assertRaises(OCRValidationError):
            validate_language_code("")
        with self.assertRaises(OCRValidationError):
            validate_language_code("e")  # too short
        with self.assertRaises(OCRValidationError):
            validate_language_code("en1")  # alphanumeric

    def test_registry_singleton(self) -> None:
        """Verifies singleton pattern constraints of OCRRegistry."""
        registry2 = OCRRegistry()
        self.assertIs(self.registry, registry2)

    def test_provider_registration(self) -> None:
        """Verifies provider register and unregister constraints on OCRRegistry."""
        with self.assertRaises(OCRValidationError):
            self.registry.register_provider("", self.provider)
        with self.assertRaises(OCRValidationError):
            # The base validation check raises OCRValidationError
            self.registry.register_provider("mock2", None)  # type: ignore
        with self.assertRaises(OCRValidationError):
            self.registry.register_provider("mock", self.provider)  # duplicate check

        self.registry.unregister_provider("mock")
        self.assertNotIn("mock", self.registry.list_providers())

    def test_layout_analysis_extraction(self) -> None:
        """Verifies layout extractor parses result details."""
        blocks = [
            OCRTextBlock("b1", "Paragraph text header.", 0.95, [0, 0, 10, 10], 1),
            OCRTextBlock("b2", "Content text body.", 0.92, [0, 15, 10, 10], 2)
        ]
        page = OCRPage(1, 100, 100, "0", blocks)
        result = OCRResult("r1", "doc1", "Paragraph text header.\nContent text body.", 0.935, [page], 0.1, "mock")

        layout = extract_layout(result)
        self.assertEqual(len(layout.text_blocks), 2)
        self.assertEqual(layout.paragraphs[0], "Paragraph text header.")
        self.assertEqual(layout.reading_order, ["b1", "b2"])
        self.assertEqual(len(layout.tables), 1)
        self.assertEqual(len(layout.forms), 1)

    def test_agent_extract_task(self) -> None:
        """Verifies agent executes full text extraction task."""
        task = Task(
            description="Extract text from scan",
            metadata={
                "action": "extract",
                "document_id": "doc_123",
                "workspace_id": "workspace_1",
                "content": b"Scanned document visual binary representation bytes.",
                "filename": "scan.pdf",
                "language": "es"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        res: OCRResult = self.agent.execute(task)
        self.agent.after_execute(res)

        self.assertEqual(res.document_id, "doc_123")
        self.assertGreater(res.confidence, 0.90)
        self.assertEqual(len(res.pages), 1)

        # Confirm EventBus triggers
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("ocr.started", events)
        self.assertIn("ocr.completed", events)

    def test_agent_extract_page_task(self) -> None:
        """Verifies agent executes page-level text extraction task."""
        task = Task(
            description="Extract target page text",
            metadata={
                "action": "extract_page",
                "document_id": "doc_123",
                "workspace_id": "workspace_1",
                "content": b"Scanned image binary.",
                "filename": "scan.png",
                "page_number": 3
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        page: OCRPage = self.agent.execute(task)
        self.agent.after_execute(page)

        self.assertEqual(page.page_number, 3)
        self.assertEqual(len(page.text_blocks), 1)
        self.assertIn("Page 3", page.text_blocks[0].text)

    def test_agent_supported_languages(self) -> None:
        """Verifies languages support query routing."""
        task = Task(
            description="Query languages",
            metadata={
                "action": "supported_languages",
                "provider_id": "mock"
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        languages = self.agent.execute(task)
        self.agent.after_execute(languages)
        self.assertIn("en", languages)
        self.assertIn("es", languages)

    def test_agent_layout_analysis(self) -> None:
        """Verifies layout analysis task parsing and events."""
        blocks = [
            OCRTextBlock("b1", "Header text", 0.95, [0, 0, 10, 10], 1)
        ]
        page = OCRPage(1, 100, 100, "0", blocks)
        result = OCRResult("r1", "doc1", "Header text", 0.95, [page], 0.1, "mock")

        task = Task(
            description="Layout analysis",
            metadata={
                "action": "layout_analysis",
                "ocr_result": result
            }
        )
        self.agent.validate_task(task)
        self.agent.before_execute(task)
        layout: LayoutAnalysis = self.agent.execute(task)
        self.agent.after_execute(layout)

        self.assertEqual(layout.paragraphs[0], "Header text")
        self.event_bus.dispatch_all()
        events = [e.payload.get("event_name") for e in self.receiver.events]
        self.assertIn("ocr.layout.generated", events)

    def test_registry_thread_safety(self) -> None:
        """Verifies concurrent registrations and lookups operate safely."""
        def run_thread(tid: int) -> None:
            class DummyOCRProvider(OCRProvider):
                def extract(self, request, content):
                    return OCRResult("r", "d", "t", 0.9, [], 0.1, "dummy")
                def extract_page(self, request, content, page_num):
                    return OCRPage(page_num, 100, 100, "0", [])
                def supported_languages(self): return ["en"]
                def health_check(self): return True

            pid = f"dummy-{tid}"
            self.registry.register_provider(pid, DummyOCRProvider())
            self.assertIn(pid, self.registry.list_providers())
            self.registry.unregister_provider(pid)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_thread, i) for i in range(50)]
            concurrent.futures.wait(futures)
            for f in futures:
                f.result()
