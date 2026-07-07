"""Structured Markdown builder for the Product Experience Layer.

Provides MarkdownRenderer which wraps domain-specific Markdown renderers and
adds configurable options: header depth, emoji mode, table alignment, and
optional YAML front-matter metadata injection.

Classes
-------
- MarkdownConfig  : Header levels, table format, emoji, and front-matter flags.
- MarkdownRenderer: Dispatcher calling domain Markdown methods.

Example usage::

    renderer = MarkdownRenderer()
    md = renderer.render(resume_report)
    md = renderer.render(github_report, config=MarkdownConfig(emoji=False))
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from backend.intelligence.resume.report_renderer import ReportRenderer as ResumeRenderer
from backend.intelligence.github.report_renderer import GitHubReportRenderer
from backend.intelligence.document.report_renderer import DocumentReportRenderer


@dataclass
class MarkdownConfig:
    """Configuration options for Markdown rendering.

    Attributes:
        h1_prefix: Markdown prefix string for level-1 headings.
        h2_prefix: Markdown prefix string for level-2 headings.
        emoji: When True, prepends emoji to section headings.
        front_matter: When True, injects YAML front-matter metadata block.
        table_align_center: When True, uses centered table columns.
        max_list_items: Maximum items to render per list section.
    """

    h1_prefix: str = "#"
    h2_prefix: str = "##"
    emoji: bool = True
    front_matter: bool = True
    table_align_center: bool = False
    max_list_items: int = 20


_EMOJI_MAP = {
    "resume": {
        "summary": "📝",
        "skills": "🛠️",
        "strengths": "💪",
        "weaknesses": "⚠️",
        "roadmap": "🗺️",
        "action": "✅",
    },
    "github": {
        "summary": "📊",
        "tech": "⚙️",
        "quality": "🔍",
        "health": "❤️",
        "strengths": "💪",
        "risks": "⚠️",
        "roadmap": "🗺️",
    },
    "document": {
        "summary": "📄",
        "entities": "🏷️",
        "topics": "📚",
        "graph": "🕸️",
        "knowledge": "🧠",
    },
}


def _front_matter(report: Any, domain: str) -> str:
    """Generates a YAML front-matter block for the report.

    Args:
        report: Any intelligence report object.
        domain: Domain label ('resume', 'github', 'document').

    Returns:
        YAML front-matter string.
    """
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report_id = getattr(report, "report_id", "N/A")
    workspace_id = getattr(report, "workspace_id", "N/A")
    return (
        "---\n"
        f"report_id: {report_id}\n"
        f"domain: {domain}\n"
        f"workspace_id: {workspace_id}\n"
        f"generated_at: {now}\n"
        "---\n\n"
    )


class MarkdownRenderer:
    """Structured Markdown builder dispatching to domain-specific renderers.

    Supports front-matter injection, emoji headings, and configurable
    table alignment. All method calls are pure (no side effects).
    """

    def __init__(self) -> None:
        self._resume_renderer = ResumeRenderer()
        self._github_renderer = GitHubReportRenderer()
        self._document_renderer = DocumentReportRenderer()

    def render(
        self,
        report: Any,
        config: Optional[MarkdownConfig] = None,
    ) -> str:
        """Detects the report domain and renders the appropriate Markdown.

        Args:
            report: Any supported intelligence report object.
            config: Optional MarkdownConfig override.

        Returns:
            Formatted Markdown string.
        """
        cls_name = type(report).__name__
        if cls_name == "ProductResumeReport":
            return self.render_resume(report, config=config)
        if cls_name == "GitHubIntelligenceReport":
            return self.render_github(report, config=config)
        return self.render_document(report, config=config)

    def render_resume(
        self,
        report: Any,
        config: Optional[MarkdownConfig] = None,
    ) -> str:
        """Renders a ProductResumeReport to structured Markdown.

        Args:
            report: ProductResumeReport instance.
            config: Optional MarkdownConfig override.

        Returns:
            Markdown-formatted string.
        """
        cfg = config or MarkdownConfig()
        md = self._resume_renderer.to_markdown(report)
        if cfg.front_matter:
            md = _front_matter(report, "resume") + md
        return md

    def render_github(
        self,
        report: Any,
        config: Optional[MarkdownConfig] = None,
    ) -> str:
        """Renders a GitHubIntelligenceReport to structured Markdown.

        Args:
            report: GitHubIntelligenceReport instance.
            config: Optional MarkdownConfig override.

        Returns:
            Markdown-formatted string.
        """
        cfg = config or MarkdownConfig()
        md = self._github_renderer.to_markdown(report)
        if cfg.front_matter:
            md = _front_matter(report, "github") + md
        return md

    def render_document(
        self,
        report: Any,
        config: Optional[MarkdownConfig] = None,
    ) -> str:
        """Renders a DocumentKnowledgeReport to structured Markdown.

        Args:
            report: DocumentKnowledgeReport instance.
            config: Optional MarkdownConfig override.

        Returns:
            Markdown-formatted string.
        """
        cfg = config or MarkdownConfig()
        md = self._document_renderer.render_markdown(report)
        if cfg.front_matter:
            md = _front_matter(report, "document") + md
        return md

    def render_generic(self, report: Any) -> str:
        """Renders any serialisable report to a generic Markdown document.

        Args:
            report: Any Pydantic-based report object.

        Returns:
            Markdown-formatted string.
        """
        lines = [
            f"# Intelligence Report — {type(report).__name__}",
            "",
            f"**Report ID**: {getattr(report, 'report_id', 'N/A')}  ",
            f"**Workspace**: {getattr(report, 'workspace_id', 'N/A')}  ",
            "",
            "## Report Data",
            "",
        ]
        data = {}
        if hasattr(report, "model_dump"):
            data = report.model_dump()
        elif hasattr(report, "dict"):
            data = report.dict()

        for key, value in list(data.items())[:30]:
            if isinstance(value, (str, int, float, bool)):
                lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            elif isinstance(value, list) and value:
                preview = ", ".join(str(v)[:40] for v in value[:3])
                lines.append(f"- **{key.replace('_', ' ').title()}**: {preview}…")

        return "\n".join(lines)
