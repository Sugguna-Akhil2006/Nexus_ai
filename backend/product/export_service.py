"""Multi-format export orchestrator for the Product Experience Layer.

Coordinates rendering calls and optional ZIP bundle packaging for single and
multi-format intelligence report exports (JSON, HTML, Markdown, PDF).

Classes
-------
- ExportRequest : Pydantic request model for export operations.
- ExportResult  : Pydantic result model carrying content bytes and metadata.
- ExportService : Orchestrates renderer calls and bundle packaging.

Example usage::

    svc = ExportService()
    result = svc.export(report, ExportRequest(format="html"))
    bundle = svc.export_bundle(report, formats=["json", "html", "markdown", "pdf"])
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from backend.product.report_renderer import UnifiedReportRenderer
from backend.product.pdf_renderer import PDFRenderer
from backend.product.html_renderer import HTMLRenderer
from backend.product.markdown_renderer import MarkdownRenderer
from backend.product.serialization import serialize_report_json


# Supported single-format export options
ExportFormat = Literal["json", "html", "markdown", "md", "pdf"]

# All supported formats for bundle exports
ALL_FORMATS: List[str] = ["json", "html", "markdown", "pdf"]


class ExportRequest(BaseModel):
    """Request payload for a single-format export.

    Attributes:
        format: Target export format.
        include_metadata: Whether to inject metadata into the export.
        filename_prefix: Optional filename prefix override.
    """

    format: ExportFormat = "json"
    include_metadata: bool = True
    filename_prefix: Optional[str] = None


class ExportResult(BaseModel):
    """Result of a completed export operation.

    Attributes:
        content: Raw byte content of the exported file.
        media_type: MIME type for the content.
        filename: Suggested download filename.
        size_bytes: Content size in bytes.
        format: The export format used.
        generated_at: UTC timestamp of generation.
    """

    content: bytes
    media_type: str
    filename: str
    size_bytes: int
    format: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"arbitrary_types_allowed": True}


_MEDIA_TYPES: Dict[str, str] = {
    "json": "application/json",
    "html": "text/html",
    "markdown": "text/markdown",
    "md": "text/markdown",
    "pdf": "application/pdf",
    "zip": "application/zip",
}

_EXTENSIONS: Dict[str, str] = {
    "json": ".json",
    "html": ".html",
    "markdown": ".md",
    "md": ".md",
    "pdf": ".pdf",
    "zip": ".zip",
}


class ExportService:
    """Multi-format export orchestrator.

    Delegates rendering to domain-specific renderers and packages results
    into individual files or ZIP bundles. Stateless—safe for shared use.
    """

    def __init__(self) -> None:
        self._unified = UnifiedReportRenderer()
        self._pdf = PDFRenderer()
        self._html = HTMLRenderer()
        self._markdown = MarkdownRenderer()

    # ------------------------------------------------------------------
    # Single-Format Export
    # ------------------------------------------------------------------

    def export(
        self,
        report: Any,
        request: Optional[ExportRequest] = None,
    ) -> ExportResult:
        """Exports a report in a single specified format.

        Args:
            report: Any supported intelligence report object.
            request: ExportRequest controlling format and options.

        Returns:
            ExportResult with content bytes and metadata.

        Raises:
            ValueError: If an unsupported format is specified.
        """
        req = request or ExportRequest()
        fmt = req.format.lower()
        report_id = getattr(report, "report_id", "report")
        prefix = req.filename_prefix or f"nexus_{report_id}"

        if fmt == "json":
            content_str = self._render_json(report, req.include_metadata)
            content = content_str.encode("utf-8")
        elif fmt == "html":
            content = self._html.render(report).encode("utf-8")
        elif fmt in ("markdown", "md"):
            content = self._markdown.render(report).encode("utf-8")
        elif fmt == "pdf":
            content = self._pdf.render(report)
        else:
            raise ValueError(f"Unsupported export format: '{fmt}'")

        filename = f"{prefix}{_EXTENSIONS.get(fmt, '.bin')}"
        return ExportResult(
            content=content,
            media_type=_MEDIA_TYPES.get(fmt, "application/octet-stream"),
            filename=filename,
            size_bytes=len(content),
            format=fmt,
        )

    # ------------------------------------------------------------------
    # Bundle Export (ZIP)
    # ------------------------------------------------------------------

    def export_bundle(
        self,
        report: Any,
        formats: Optional[List[str]] = None,
        filename_prefix: Optional[str] = None,
    ) -> ExportResult:
        """Exports a report in multiple formats packed into a ZIP archive.

        Args:
            report: Any supported intelligence report object.
            formats: List of format strings to include. Defaults to all formats.
            filename_prefix: Optional ZIP archive filename prefix.

        Returns:
            ExportResult with ZIP content and metadata.
        """
        formats = formats or ALL_FORMATS
        report_id = getattr(report, "report_id", "report")
        prefix = filename_prefix or f"nexus_{report_id}"

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            for fmt in formats:
                try:
                    result = self.export(
                        report,
                        ExportRequest(format=fmt, include_metadata=True),  # type: ignore[arg-type]
                    )
                    zf.writestr(result.filename, result.content)
                except Exception:
                    # Skip formats that fail rather than aborting the bundle
                    pass

        zip_bytes = buffer.getvalue()
        zip_filename = f"{prefix}_bundle.zip"
        return ExportResult(
            content=zip_bytes,
            media_type=_MEDIA_TYPES["zip"],
            filename=zip_filename,
            size_bytes=len(zip_bytes),
            format="zip",
        )

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    def _render_json(self, report: Any, include_metadata: bool) -> str:
        """Renders a report to a JSON string with optional metadata envelope.

        Args:
            report: Report object.
            include_metadata: When True, wraps the data in a metadata envelope.

        Returns:
            JSON string.
        """
        raw_json = serialize_report_json(report)
        if not include_metadata:
            return raw_json

        envelope = {
            "nexus_export": True,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "report_type": type(report).__name__,
            "data": json.loads(raw_json),
        }
        return json.dumps(envelope, indent=2, default=str)

    def get_supported_formats(self) -> List[str]:
        """Returns the list of supported single-format export values.

        Returns:
            List of format strings.
        """
        return list(ALL_FORMATS)
