"""Unified multi-domain report renderer for the Product Experience Layer.

Provides a single UnifiedReportRenderer entry point that dispatches to the
appropriate domain-specific renderer based on report type, enabling the
product layer to render any intelligence report without coupling to the
specific domain module.

Supported report types
----------------------
- ProductResumeReport       (from intelligence.resume.product)
- GitHubIntelligenceReport  (from intelligence.github.models)
- DocumentKnowledgeReport   (from intelligence.document.models)

Output formats
--------------
- JSON  : Model-serialized dictionary or JSON string
- HTML  : Premium dark-mode styled HTML
- PDF   : PDF layout bytes (ISO-standard)
- Markdown : Structured Markdown document

Example usage::

    from backend.product.report_renderer import UnifiedReportRenderer
    renderer = UnifiedReportRenderer()
    html = renderer.to_html(resume_report)
    pdf  = renderer.to_pdf(github_report)
    md   = renderer.to_markdown(document_report)
"""

from __future__ import annotations

from typing import Any, Union

from backend.intelligence.resume.report_renderer import ReportRenderer as ResumeRenderer
from backend.intelligence.github.report_renderer import GitHubReportRenderer
from backend.intelligence.document.report_renderer import DocumentReportRenderer

# Lazy imports to keep the type hints readable without circular deps
_RESUME_TYPE_NAME = "ProductResumeReport"
_GITHUB_TYPE_NAME = "GitHubIntelligenceReport"
_DOCUMENT_TYPE_NAME = "DocumentKnowledgeReport"


def _detect_domain(report: Any) -> str:
    """Determines the intelligence domain of a report object.

    Inspects the class name and module path to identify the correct
    renderer dispatch target.

    Args:
        report: Any intelligence report object.

    Returns:
        Domain string: 'resume', 'github', or 'document'.

    Raises:
        TypeError: If the report type is not recognised.
    """
    cls_name = type(report).__name__
    module = getattr(type(report), "__module__", "")

    if cls_name == _RESUME_TYPE_NAME or "resume" in module:
        return "resume"
    if cls_name == _GITHUB_TYPE_NAME or "github" in module:
        return "github"
    if cls_name == _DOCUMENT_TYPE_NAME or "document" in module:
        return "document"

    raise TypeError(
        f"Unrecognised report type '{cls_name}'. "
        "UnifiedReportRenderer supports ProductResumeReport, "
        "GitHubIntelligenceReport, and DocumentKnowledgeReport."
    )


class UnifiedReportRenderer:
    """Domain-agnostic renderer dispatching to domain-specific implementations.

    Maintains single instances of each domain renderer to avoid redundant
    object creation. All public methods accept any supported report type.
    """

    def __init__(self) -> None:
        self._resume_renderer = ResumeRenderer()
        self._github_renderer = GitHubReportRenderer()
        self._document_renderer = DocumentReportRenderer()

    # ------------------------------------------------------------------
    # Public Rendering API
    # ------------------------------------------------------------------

    def to_json(self, report: Any) -> str:
        """Serializes any supported report to a JSON string.

        Args:
            report: An intelligence report object.

        Returns:
            JSON-encoded string representation.
        """
        domain = _detect_domain(report)
        if domain == "resume":
            return self._resume_renderer.to_json(report)
        if domain == "github":
            return self._github_renderer.to_json(report)
        # Document renderer uses model_dump_json directly
        if hasattr(report, "model_dump_json"):
            return report.model_dump_json()
        import json
        return json.dumps(report.dict() if hasattr(report, "dict") else {}, default=str)

    def to_html(self, report: Any) -> str:
        """Renders any supported report to a premium styled HTML string.

        Args:
            report: An intelligence report object.

        Returns:
            Complete HTML document string.
        """
        domain = _detect_domain(report)
        if domain == "resume":
            return self._resume_renderer.to_html(report)
        if domain == "github":
            return self._github_renderer.to_html(report)
        # Document
        return self._document_renderer.render_html(report)

    def to_pdf(self, report: Any) -> bytes:
        """Renders any supported report to PDF-compatible bytes.

        Args:
            report: An intelligence report object.

        Returns:
            PDF byte stream.
        """
        domain = _detect_domain(report)
        if domain == "resume":
            return self._resume_renderer.to_pdf(report)
        if domain == "github":
            return self._github_renderer.to_pdf(report)
        # Document: delegate to PDFRenderer for generic layout
        from backend.product.pdf_renderer import PDFRenderer
        return PDFRenderer().render_generic(report)

    def to_markdown(self, report: Any) -> str:
        """Renders any supported report to a structured Markdown document.

        Args:
            report: An intelligence report object.

        Returns:
            Markdown-formatted string.
        """
        domain = _detect_domain(report)
        if domain == "resume":
            return self._resume_renderer.to_markdown(report)
        if domain == "github":
            return self._github_renderer.to_markdown(report)
        # Document
        return self._document_renderer.render_markdown(report)

    def detect_domain(self, report: Any) -> str:
        """Exposes the domain detection logic publicly for inspection.

        Args:
            report: An intelligence report object.

        Returns:
            Domain string: 'resume', 'github', or 'document'.
        """
        return _detect_domain(report)
