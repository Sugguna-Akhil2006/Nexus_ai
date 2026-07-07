"""Nexus AI Product Experience Layer.

This package delivers the full product-facing integration of all Nexus AI
intelligence modules (Resume, GitHub, Document) without modifying any runtime,
memory, or AI reasoning components.

Exports
-------
- CacheService             : Generic TTL-aware thread-safe cache
- ProgressTracker          : Thread-safe background job lifecycle manager
- MetricsService           : Pipeline telemetry and performance aggregation
- HistoryService           : Analysis history with search/filter/sort/favorites
- ExportService            : Multi-format export bundle orchestrator
- UnifiedReportRenderer    : Dispatcher calling domain-specific renderers
- PDFRenderer              : PDF layout compiler
- HTMLRenderer             : Premium HTML exporter
- MarkdownRenderer         : Structured Markdown builder
- FrontendAdapter          : Page-level response adapters
- DeveloperConsole         : Widget builders for the developer console
- ProductResponse          : Typed generic response wrapper
- PaginatedResponse        : Paginated list response wrapper
"""

from backend.product.cache_service import CacheService
from backend.product.progress_tracker import ProgressTracker, JobStatus
from backend.product.metrics_service import MetricsService
from backend.product.history_service import HistoryService, HistoryRecord
from backend.product.export_service import ExportService, ExportRequest, ExportResult
from backend.product.report_renderer import UnifiedReportRenderer
from backend.product.pdf_renderer import PDFRenderer
from backend.product.html_renderer import HTMLRenderer
from backend.product.markdown_renderer import MarkdownRenderer
from backend.product.serialization import ProductResponse, PaginatedResponse, ErrorResponse
from backend.product.frontend_adapter import (
    ResumePageAdapter,
    GitHubPageAdapter,
    DocumentPageAdapter,
    ResearchPageAdapter,
    DeveloperConsoleAdapter,
)
from backend.product.developer_console import (
    ExecutionTimeline,
    PipelineStageWidget,
    AgentStatusWidget,
    PerformanceMetricsWidget,
    MemoryUsageWidget,
    ExecutionLogsWidget,
    EventTimelineWidget,
    RequestInspectorWidget,
)

__all__ = [
    "CacheService",
    "ProgressTracker",
    "JobStatus",
    "MetricsService",
    "HistoryService",
    "HistoryRecord",
    "ExportService",
    "ExportRequest",
    "ExportResult",
    "UnifiedReportRenderer",
    "PDFRenderer",
    "HTMLRenderer",
    "MarkdownRenderer",
    "ProductResponse",
    "PaginatedResponse",
    "ErrorResponse",
    "ResumePageAdapter",
    "GitHubPageAdapter",
    "DocumentPageAdapter",
    "ResearchPageAdapter",
    "DeveloperConsoleAdapter",
    "ExecutionTimeline",
    "PipelineStageWidget",
    "AgentStatusWidget",
    "PerformanceMetricsWidget",
    "MemoryUsageWidget",
    "ExecutionLogsWidget",
    "EventTimelineWidget",
    "RequestInspectorWidget",
]
