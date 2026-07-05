"""Handles report exporting formats including raw JSON and Markdown downloads."""

import json
from backend.intelligence.document.models import DocumentKnowledgeReport
from backend.intelligence.document.report_renderer import DocumentReportRenderer


class DocumentReportExporter:
    """Helper service class to export reports to download payloads."""

    def __init__(self) -> None:
        self.renderer = DocumentReportRenderer()

    def export_json(self, report: DocumentKnowledgeReport) -> str:
        """Serializes report data model to json string layout."""
        return report.model_dump_json(indent=2)

    def export_markdown(self, report: DocumentKnowledgeReport) -> str:
        """Serializes report layout to raw markdown text formatting."""
        return self.renderer.render_markdown(report)
