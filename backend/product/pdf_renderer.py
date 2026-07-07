"""PDF layout compiler for the Product Experience Layer.

Provides PDFRenderer that generates production-quality PDF byte streams for
any supported intelligence report. Currently implements a structured text-
based PDF layout (ISO 32000-compatible) that is usable immediately without
third-party libraries, and is designed for seamless swap-in of ReportLab or
WeasyPrint when available.

Classes
-------
- PDFLayout   : Layout configuration (fonts, margins, colors, sections).
- PDFRenderer : Byte-stream generator dispatching per report domain.

Example usage::

    renderer = PDFRenderer()
    pdf_bytes = renderer.render(resume_report)
    pdf_bytes = renderer.render(github_report)
    pdf_bytes = renderer.render_generic(document_report)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PDFLayout:
    """Configuration for PDF page layout and typography.

    Attributes:
        page_width: Page width in points (1pt = 1/72 inch).
        page_height: Page height in points.
        margin_top: Top margin in points.
        margin_bottom: Bottom margin in points.
        margin_left: Left margin in points.
        margin_right: Right margin in points.
        title_font_size: Font size for the report title.
        heading_font_size: Font size for section headings.
        body_font_size: Font size for body text.
        leading: Line spacing in points.
        primary_color: Hex color for accents (informational only).
    """

    page_width: float = 595.0       # A4 width in points
    page_height: float = 842.0      # A4 height in points
    margin_top: float = 60.0
    margin_bottom: float = 60.0
    margin_left: float = 70.0
    margin_right: float = 70.0
    title_font_size: int = 18
    heading_font_size: int = 13
    body_font_size: int = 10
    leading: float = 18.0
    primary_color: str = "#00f0ff"


def _escape_pdf(text: str) -> str:
    """Escapes special characters in a PDF text string literal.

    Args:
        text: Raw text value.

    Returns:
        Text safe for use inside PDF parentheses ( ) delimiters.
    """
    return (
        text.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
            .replace("\r", " ")
            .replace("\n", " ")
    )


def _build_pdf(title: str, lines: List[str], layout: PDFLayout) -> bytes:
    """Assembles a minimal but valid multi-line PDF document.

    Constructs a cross-reference table and content stream containing the
    supplied title and text lines, fully conformant with PDF 1.4.

    Args:
        title: Report title printed at the top of the page.
        lines: Body text lines, each rendered on its own PDF row.
        layout: PDFLayout configuration.

    Returns:
        Complete PDF file as bytes.
    """
    y_start = layout.page_height - layout.margin_top
    leading = layout.leading

    # Build BT (begin text) stream content
    text_ops: List[str] = []
    text_ops.append("BT")
    # Title in large font
    text_ops.append(f"/F1 {layout.title_font_size} Tf")
    text_ops.append(f"{layout.margin_left:.0f} {y_start:.0f} Td")
    text_ops.append(f"({_escape_pdf(title[:80])}) Tj")

    # Move down one leading + extra gap
    text_ops.append(f"0 -{leading + 10:.0f} Td")
    text_ops.append(f"/F1 {layout.body_font_size} Tf")

    for line in lines:
        safe = _escape_pdf(line[:120])
        text_ops.append(f"({safe}) Tj")
        text_ops.append(f"0 -{leading:.0f} Td")

    text_ops.append("ET")
    stream_content = "\n".join(text_ops)
    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)

    # Minimal PDF object structure
    obj1 = "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = (
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 {layout.page_width:.0f} {layout.page_height:.0f}] "
        f"/Contents 4 0 R "
        f"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    obj4 = (
        f"4 0 obj\n<< /Length {stream_len} >>\nstream\n"
        + stream_content
        + "\nendstream\nendobj\n"
    )
    obj5 = (
        "5 0 obj\n"
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        "/Encoding /WinAnsiEncoding >>\nendobj\n"
    )

    header = "%PDF-1.4\n"
    body = obj1 + obj2 + obj3 + obj4 + obj5

    # Cross-reference table
    offsets = []
    pos = len(header)
    for obj_str in [obj1, obj2, obj3, obj4, obj5]:
        offsets.append(pos)
        pos += len(obj_str)

    xref_offset = len(header) + len(body)
    xref_lines = ["xref", f"0 6", "0000000000 65535 f "]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n ")
    xref = "\n".join(xref_lines) + "\n"

    trailer = f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF"

    full_doc = header + body + xref + trailer
    return full_doc.encode("latin-1", errors="replace")


class PDFRenderer:
    """PDF byte-stream generator for Resume, GitHub, and Document reports.

    Provides domain-specific render methods for rich section extraction,
    and a generic fallback for any serialisable report type.
    """

    def __init__(self, layout: Optional[PDFLayout] = None) -> None:
        """Initialises the renderer with an optional custom layout.

        Args:
            layout: PDFLayout configuration override. Defaults to A4 layout.
        """
        self.layout = layout or PDFLayout()

    def render(self, report: Any) -> bytes:
        """Detects the report domain and renders the appropriate PDF.

        Args:
            report: Any supported intelligence report object.

        Returns:
            Complete PDF byte stream.
        """
        cls_name = type(report).__name__
        if cls_name == "ProductResumeReport":
            return self.render_resume(report)
        if cls_name == "GitHubIntelligenceReport":
            return self.render_github(report)
        return self.render_generic(report)

    def render_resume(self, report: Any) -> bytes:
        """Renders a ProductResumeReport as a structured PDF.

        Args:
            report: ProductResumeReport instance.

        Returns:
            PDF byte stream.
        """
        title = f"Resume Analysis Report — {getattr(report, 'report_id', 'N/A')}"
        lines: List[str] = [
            f"Document ID : {getattr(report, 'document_id', 'N/A')}",
            f"Workspace   : {getattr(report, 'workspace_id', 'N/A')}",
            f"ATS Score   : {getattr(report, 'ats_score', 0.0)} / 100",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 60,
        ]
        summary = getattr(report, "executive_summary", "")
        # Wrap summary at ~80 chars
        for i in range(0, min(len(summary), 400), 80):
            lines.append(summary[i : i + 80])

        lines += ["", "SKILLS", "-" * 60]
        for cat, skills in (getattr(report, "skill_analysis", None) or {}).items():
            lines.append(f"  {cat}: {', '.join(skills[:6])}")

        lines += ["", "MISSING SKILLS", "-" * 60]
        missing = getattr(report, "missing_skills", [])
        if missing:
            lines.append(", ".join(missing[:10]))

        lines += ["", "STRENGTHS", "-" * 60]
        for s in (getattr(report, "strengths", []) or [])[:5]:
            lines.append(f"  + {s}")

        lines += ["", "CAREER READINESS", "-" * 60]
        readiness = getattr(report, "career_readiness", "")
        for i in range(0, min(len(readiness), 200), 80):
            lines.append(readiness[i : i + 80])

        lines += ["", "ACTION PLAN", "-" * 60]
        for step in (getattr(report, "action_plan", []) or [])[:5]:
            lines.append(f"  [{getattr(step, 'priority', '')}] {getattr(step, 'step', '')}")

        return _build_pdf(title, lines, self.layout)

    def render_github(self, report: Any) -> bytes:
        """Renders a GitHubIntelligenceReport as a structured PDF.

        Args:
            report: GitHubIntelligenceReport instance.

        Returns:
            PDF byte stream.
        """
        title = f"GitHub Engineering Report — {getattr(report, 'report_id', 'N/A')}"
        lines: List[str] = [
            f"Repository  : {getattr(report, 'repository', 'N/A')}",
            f"Analyzed At : {getattr(report, 'timestamp', 'N/A')}",
            "",
            "EXECUTIVE SUMMARY",
            "-" * 60,
        ]
        summary = getattr(report, "executive_summary", "")
        for i in range(0, min(len(summary), 400), 80):
            lines.append(summary[i : i + 80])

        tech = getattr(report, "technology_stack", {}) or {}
        langs = tech.get("languages", [])
        frameworks = tech.get("frameworks", [])
        lines += ["", "TECHNOLOGY STACK", "-" * 60]
        if langs:
            lines.append(f"  Languages  : {', '.join(langs[:8])}")
        if frameworks:
            lines.append(f"  Frameworks : {', '.join(frameworks[:8])}")

        quality = getattr(report, "engineering_quality", {}) or {}
        lines += ["", "ENGINEERING QUALITY", "-" * 60]
        for k, v in list(quality.items())[:6]:
            lines.append(f"  {k.replace('_', ' ').title()}: {v}")

        lines += ["", "STRENGTHS", "-" * 60]
        for s in (getattr(report, "strengths", []) or [])[:5]:
            lines.append(f"  + {s}")

        lines += ["", "IMPROVEMENT ROADMAP", "-" * 60]
        for r in (getattr(report, "improvement_roadmap", []) or [])[:5]:
            lines.append(f"  > {r}")

        return _build_pdf(title, lines, self.layout)

    def render_generic(self, report: Any) -> bytes:
        """Renders any serialisable report as a generic PDF.

        Falls back to model_dump / dict when domain-specific layout is
        not available (e.g. DocumentKnowledgeReport, future modules).

        Args:
            report: Any report object with a model_dump or dict method.

        Returns:
            PDF byte stream.
        """
        cls_name = type(report).__name__
        title = f"Intelligence Report — {cls_name}"
        lines: List[str] = [
            f"Type       : {cls_name}",
            f"Report ID  : {getattr(report, 'report_id', 'N/A')}",
            f"Workspace  : {getattr(report, 'workspace_id', 'N/A')}",
            "",
        ]

        data: Dict[str, Any] = {}
        if hasattr(report, "model_dump"):
            data = report.model_dump()
        elif hasattr(report, "dict"):
            data = report.dict()

        for key, value in list(data.items())[:20]:
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"{key.replace('_', ' ').title()}: {str(value)[:100]}")
            elif isinstance(value, list) and value:
                items_str = ", ".join(str(v)[:30] for v in value[:4])
                lines.append(f"{key.replace('_', ' ').title()}: {items_str}")

        return _build_pdf(title, lines, self.layout)
