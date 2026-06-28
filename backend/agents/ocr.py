"""OCR Agent and Document Text Extraction Layer Module.

Provides abstractions, registries, layout analysis engines, validation checks,
and mock providers for text and layout extraction from visual documents.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Set, Union
import uuid

from backend.runtime.base import AgentState, AgentStatus, BaseAgent
from backend.runtime.event import Event, EventBus, EventType
from backend.runtime.exceptions import (
    AgentInitializationError,
    AgentStateError,
    NexusException,
    TaskValidationError,
)
from backend.runtime.task import Task
from backend.runtime.logger import StructuredLogger


# =====================================================================
# Exceptions
# =====================================================================

class OCRError(NexusException):
    """Base exception for all OCR Agent related errors."""
    pass


class OCRValidationError(OCRError):
    """Raised when OCR validation checks fail."""
    pass


class OCRProviderError(OCRError):
    """Raised when an OCR provider fails to execute or is unavailable."""
    pass


# =====================================================================
# Core Models
# =====================================================================

@dataclass(frozen=True)
class OCRRequest:
    """Authentication parameters defining target document parameters.

    Attributes:
        request_id: Tracking request ID.
        document_id: Target document ID.
        workspace_id: Target workspace context ID.
        provider: Expected provider key string.
        language: ISO 639 format code.
        options: Custom options configurations.
        metadata: Extra tracking metadata.
    """
    request_id: str
    document_id: str
    workspace_id: str
    provider: str
    language: str = "en"
    options: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OCRTextBlock:
    """Extracted text layout block item details.

    Attributes:
        block_id: Bounding box identifier string.
        text: Plaintext content.
        confidence: Normalized OCR precision confidence value (0.0 to 1.0).
        bounding_box: Bounding box coordinates list [x, y, w, h].
        reading_order: Placement ordering sequence counter.
        metadata: Extra tag attributes dictionary.
    """
    block_id: str
    text: str
    confidence: float
    bounding_box: List[float]
    reading_order: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OCRPage:
    """Aggregated parsed page metrics.

    Attributes:
        page_number: Target page number.
        width: Bounding box page width.
        height: Bounding box page height.
        orientation: Degrees orientation string (e.g. "0", "90").
        text_blocks: Array list of OCRTextBlock blocks.
        metadata: Optional page layout flags metadata.
    """
    page_number: int
    width: float
    height: float
    orientation: str
    text_blocks: List[OCRTextBlock]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OCRResult:
    """Consolidated OCR result outcome.

    Attributes:
        result_id: Unique outcome ID.
        document_id: Associated document identifier.
        extracted_text: Combined plain text extraction.
        confidence: Combined average precision confidence score.
        pages: Multi-page array indexing.
        processing_time: Duration elapsed in float seconds.
        provider: Processing provider name.
        metadata: Extra metadata details.
    """
    result_id: str
    document_id: str
    extracted_text: str
    confidence: float
    pages: List[OCRPage]
    processing_time: float
    provider: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# =====================================================================
# Layout Analysis Abstraction
# =====================================================================

@dataclass(frozen=True)
class LayoutTablePlaceholder:
    """Placeholder model representing a detected layout table structural item."""
    table_id: str
    rows: int
    cols: int
    bounding_box: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LayoutFormPlaceholder:
    """Placeholder model representing a detected layout key-value form item."""
    form_id: str
    fields: Dict[str, Any]
    bounding_box: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LayoutAnalysis:
    """Structured collection of visual document layout items."""
    text_blocks: List[OCRTextBlock]
    paragraphs: List[str]
    tables: List[LayoutTablePlaceholder] = field(default_factory=list)
    forms: List[LayoutFormPlaceholder] = field(default_factory=list)
    images: List[Dict[str, Any]] = field(default_factory=list)
    reading_order: List[str] = field(default_factory=list)


# =====================================================================
# Validation Utilities
# =====================================================================

SUPPORTED_OCR_FORMATS: Set[str] = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}


def validate_image_format(filename: str) -> None:
    """Validates supported image extension names.

    Raises:
        OCRValidationError: If extension format is unsupported.
    """
    _, ext = os.path.splitext(filename.lower())
    if ext not in SUPPORTED_OCR_FORMATS:
        raise OCRValidationError(f"Unsupported OCR file format: {ext}")


def validate_ocr_content(content: bytes) -> None:
    """Validates binary payload integrity."""
    if content is None or not isinstance(content, (bytes, bytearray)):
        raise OCRValidationError("Invalid content type for OCR. Must be bytes.")
    if len(content) == 0:
        raise OCRValidationError("Content payload cannot be empty or corrupted.")


def validate_language_code(lang: str) -> None:
    """Validates ISO language codes structure format."""
    if not lang or not isinstance(lang, str) or not lang.strip():
        raise OCRValidationError("Language code cannot be empty.")
    lang_strip = lang.strip()
    if not (2 <= len(lang_strip) <= 3) or not lang_strip.isalpha():
        raise OCRValidationError(f"Invalid language format code: {lang}. Must be 2-3 alpha characters.")


# =====================================================================
# OCR Provider Abstraction
# =====================================================================

class OCRProvider(ABC):
    """Abstract contract for Visual OCR extractors."""

    @abstractmethod
    def extract(self, request: OCRRequest, content: bytes) -> OCRResult:
        """Parses document content fully, returning structured layout and text."""
        pass

    @abstractmethod
    def extract_page(self, request: OCRRequest, content: bytes, page_number: int) -> OCRPage:
        """Parses single target page content details."""
        pass

    @abstractmethod
    def supported_languages(self) -> List[str]:
        """Lists ISO codes indicating language configurations supported by provider."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Checks connection integrity."""
        pass


class MockOCRProvider(OCRProvider):
    """Mock identity provider simulating OCR processing maps."""

    def extract(self, request: OCRRequest, content: bytes) -> OCRResult:
        text_blocks = [
            OCRTextBlock("b1", "First parsed Mock text block details.", 0.95, [10.0, 20.0, 100.0, 30.0], 1),
            OCRTextBlock("b2", "Second line of extracted layout details.", 0.91, [10.0, 60.0, 100.0, 30.0], 2),
        ]
        page = OCRPage(
            page_number=1,
            width=612.0,
            height=792.0,
            orientation="0",
            text_blocks=text_blocks
        )
        extracted = "\n".join(b.text for b in text_blocks)
        return OCRResult(
            result_id=str(uuid.uuid4()),
            document_id=request.document_id,
            extracted_text=extracted,
            confidence=0.93,
            pages=[page],
            processing_time=0.08,
            provider="mock",
            metadata={"language": request.language}
        )

    def extract_page(self, request: OCRRequest, content: bytes, page_number: int) -> OCRPage:
        text_blocks = [
            OCRTextBlock(
                f"p{page_number}-b1",
                f"Page {page_number} mock parsed paragraph blocks.",
                0.94,
                [10.0, 20.0, 100.0, 30.0],
                1
            )
        ]
        return OCRPage(
            page_number=page_number,
            width=612.0,
            height=792.0,
            orientation="0",
            text_blocks=text_blocks
        )

    def supported_languages(self) -> List[str]:
        return ["en", "es", "fr", "de", "it"]

    def health_check(self) -> bool:
        return True


# =====================================================================
# OCR Registry
# =====================================================================

class OCRRegistry:
    """Thread-safe singleton registry mapping OCR providers."""

    _instance: Optional["OCRRegistry"] = None
    _singleton_lock: threading.Lock = threading.Lock()

    def __new__(cls, *args: Any, **kwargs: Any) -> "OCRRegistry":
        if not cls._instance:
            with cls._singleton_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return
        with self._singleton_lock:
            if getattr(self, "_initialized", False):
                return
            self._providers: Dict[str, OCRProvider] = {}
            self._lock: threading.RLock = threading.RLock()
            self._logger = StructuredLogger()
            self._initialized = True

    def register_provider(self, provider_id: str, provider: OCRProvider) -> None:
        """Registers an OCRProvider."""
        if not provider_id or not str(provider_id).strip():
            raise OCRValidationError("provider_id cannot be empty.")
        if not provider:
            raise OCRValidationError("provider instance cannot be None.")

        with self._lock:
            if provider_id in self._providers:
                raise OCRValidationError(f"Provider '{provider_id}' already registered.")
            self._providers[provider_id] = provider
            self._logger.info(f"OCR provider registered: {provider_id}")

    def unregister_provider(self, provider_id: str) -> None:
        """Removes an OCR provider registration."""
        with self._lock:
            if provider_id not in self._providers:
                raise OCRValidationError(f"Provider '{provider_id}' not found.")
            del self._providers[provider_id]
            self._logger.info(f"OCR provider unregistered: {provider_id}")

    def get_provider(self, provider_id: str) -> OCRProvider:
        """Retrieves provider."""
        with self._lock:
            if provider_id not in self._providers:
                raise OCRValidationError(f"Provider '{provider_id}' not registered.")
            return self._providers[provider_id]

    def list_providers(self) -> List[str]:
        """Lists registered provider keys."""
        with self._lock:
            return list(self._providers.keys())

    def health_check(self) -> Dict[str, bool]:
        """Queries health status across registered providers."""
        with self._lock:
            results = {}
            for pid, provider in self._providers.items():
                try:
                    results[pid] = provider.health_check()
                except Exception:
                    results[pid] = False
            return results


# =====================================================================
# OCR Layout Analysis Utility
# =====================================================================

def extract_layout(ocr_result: OCRResult) -> LayoutAnalysis:
    """Builds structural layout data coordinates mapping text elements.

    Args:
        ocr_result: Consumed OCRResult object.

    Returns:
        LayoutAnalysis: Mapped elements container.
    """
    text_blocks = []
    paragraphs = []
    reading_order = []

    for page in ocr_result.pages:
        sorted_blocks = sorted(page.text_blocks, key=lambda b: b.reading_order)
        for block in sorted_blocks:
            text_blocks.append(block)
            paragraphs.append(block.text)
            reading_order.append(block.block_id)

    # Tables/Forms placeholders
    tables = [
        LayoutTablePlaceholder(
            table_id="table_placeholder_1",
            rows=2,
            cols=2,
            bounding_box=[10.0, 100.0, 200.0, 150.0]
        )
    ]
    forms = [
        LayoutFormPlaceholder(
            form_id="form_placeholder_1",
            fields={"name": "placeholder"},
            bounding_box=[10.0, 300.0, 200.0, 50.0]
        )
    ]

    return LayoutAnalysis(
        text_blocks=text_blocks,
        paragraphs=paragraphs,
        tables=tables,
        forms=forms,
        reading_order=reading_order
    )


# =====================================================================
# OCR Agent
# =====================================================================

class OCRAgent(BaseAgent):
    """System agent governing Visual Layout Analysis and OCR Extraction pipelines."""

    def __init__(
        self,
        name: str = "OCRAgent",
        description: str = "Extracts structured text layout, coordinates, pages, and metadata from visual documents",
        version: str = "1.0.0",
        capabilities: Optional[List[str]] = None
    ) -> None:
        caps = capabilities or ["OCR_EXTRACTION", "LAYOUT_ANALYSIS"]
        super().__init__(name=name, description=description, version=version, capabilities=caps)
        self.registry = OCRRegistry()
        self.event_bus = EventBus()

    def initialize(self) -> None:
        """Initializes OCR agent."""
        super().initialize()

    def validate_task(self, task: Task) -> None:
        super().validate_task(task)
        if not task.metadata or "action" not in task.metadata:
            raise TaskValidationError("Task metadata must contain an 'action' field.")

    def execute(self, task: Task) -> Any:
        action = task.metadata["action"]
        provider_id = task.metadata.get("provider_id")

        if not provider_id:
            providers = self.registry.list_providers()
            if not providers:
                raise OCRValidationError("No OCR providers registered.")
            provider_id = providers[0]

        provider = self.registry.get_provider(provider_id)

        if action == "extract":
            doc_id = task.metadata.get("document_id")
            ws_id = task.metadata.get("workspace_id")
            content = task.metadata.get("content")
            filename = task.metadata.get("filename")
            lang = task.metadata.get("language", "en")
            options = task.metadata.get("options", {})
            req_metadata = task.metadata.get("metadata", {})

            if not doc_id or not ws_id or content is None or not filename:
                raise OCRValidationError("Missing parameter inputs (document_id, workspace_id, content, filename).")

            # Ingestion payload check
            validate_ocr_content(content)
            validate_image_format(filename)
            validate_language_code(lang)

            self._publish_event("ocr.started", document_id=doc_id, provider=provider_id)

            req = OCRRequest(
                request_id=str(uuid.uuid4()),
                document_id=doc_id,
                workspace_id=ws_id,
                provider=provider_id,
                language=lang,
                options=options,
                metadata=req_metadata
            )

            try:
                start_time = time.time()
                res = provider.extract(req, content)
                duration = time.time() - start_time

                # Update processing time dynamically
                import dataclasses
                updated_res = dataclasses.replace(res, processing_time=duration)

                # Trace logs count metrics
                self.logger.info(
                    "OCR task completed. Pages: %d. Duration: %.2fs. Confidence: %.2f.",
                    len(updated_res.pages),
                    updated_res.processing_time,
                    updated_res.confidence
                )

                self._publish_event("ocr.completed", document_id=doc_id, confidence=updated_res.confidence)
                return updated_res
            except Exception as e:
                self._publish_event("ocr.failed", document_id=doc_id, error=str(e))
                raise OCRProviderError(f"OCR provider failed: {e}") from e

        elif action == "extract_page":
            doc_id = task.metadata.get("document_id")
            ws_id = task.metadata.get("workspace_id")
            content = task.metadata.get("content")
            filename = task.metadata.get("filename")
            page_num = task.metadata.get("page_number")
            lang = task.metadata.get("language", "en")
            options = task.metadata.get("options", {})

            if not doc_id or not ws_id or content is None or not filename or page_num is None:
                raise OCRValidationError("Missing parameter inputs (document_id, workspace_id, content, filename, page_number).")

            validate_ocr_content(content)
            validate_image_format(filename)
            validate_language_code(lang)

            req = OCRRequest(
                request_id=str(uuid.uuid4()),
                document_id=doc_id,
                workspace_id=ws_id,
                provider=provider_id,
                language=lang,
                options=options
            )

            page = provider.extract_page(req, content, page_num)
            return page

        elif action == "supported_languages":
            return provider.supported_languages()

        elif action == "layout_analysis":
            res_val = task.metadata.get("ocr_result")
            if not res_val:
                raise OCRValidationError("Missing ocr_result parameter for layout analysis.")

            if isinstance(res_val, dict):
                # Reconstruct OCRResult
                pages_list = []
                for p in res_val["pages"]:
                    blocks = [
                        OCRTextBlock(
                            block_id=b["block_id"],
                            text=b["text"],
                            confidence=b["confidence"],
                            bounding_box=b["bounding_box"],
                            reading_order=b["reading_order"],
                            metadata=b.get("metadata", {})
                        )
                        for b in p["text_blocks"]
                    ]
                    pages_list.append(
                        OCRPage(
                            page_number=p["page_number"],
                            width=p["width"],
                            height=p["height"],
                            orientation=p["orientation"],
                            text_blocks=blocks,
                            metadata=p.get("metadata", {})
                        )
                    )
                ocr_result = OCRResult(
                    result_id=res_val["result_id"],
                    document_id=res_val["document_id"],
                    extracted_text=res_val["extracted_text"],
                    confidence=res_val["confidence"],
                    pages=pages_list,
                    processing_time=res_val["processing_time"],
                    provider=res_val["provider"],
                    metadata=res_val.get("metadata", {})
                )
            else:
                ocr_result = res_val

            layout = extract_layout(ocr_result)
            self._publish_event("ocr.layout.generated", document_id=ocr_result.document_id)
            return layout

        else:
            raise OCRValidationError(f"Unsupported action: {action}")

    def _publish_event(self, event_name: str, **kwargs: Any) -> None:
        event = Event(
            event_type=EventType.CUSTOM_EVENT,
            source="OCRAgent",
            payload={"event_name": event_name, **kwargs}
        )
        self.event_bus.publish(event)
