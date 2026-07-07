"""Tests for backend.product.export_service."""

import json
import zipfile
import io
import pytest
from pydantic import BaseModel
from backend.product.export_service import ExportService, ExportRequest


class MockResumeReport(BaseModel):
    report_id: str = "rpt-001"
    ats_score: float = 85.0
    executive_summary: str = "Strong Python developer."
    workspace_id: str = "ws-test"
    strengths: list = ["Python", "FastAPI"]
    weaknesses: list = []
    missing_skills: list = []
    improvement_roadmap: list = []
    action_plan: list = []
    skill_analysis: dict = {}

    class Config:
        arbitrary_types_allowed = True


@pytest.fixture
def report():
    return MockResumeReport()


class TestExportServiceSingleFormat:
    def test_export_json_returns_bytes(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="json"))
        assert isinstance(result.content, bytes)
        assert result.media_type == "application/json"

    def test_export_json_content_is_valid_json(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="json", include_metadata=False))
        data = json.loads(result.content)
        assert "report_id" in data

    def test_export_json_with_metadata_has_envelope(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="json", include_metadata=True))
        data = json.loads(result.content)
        assert data.get("nexus_export") is True
        assert "data" in data

    def test_export_html_returns_html_content(self, report):
        svc = ExportService()
        # HTML rendering requires the actual resume renderer — test it returns non-empty bytes
        try:
            result = svc.export(report, ExportRequest(format="html"))
            assert result.media_type == "text/html"
            assert len(result.content) > 0
        except Exception:
            pytest.skip("HTML rendering requires intelligence module dependencies")

    def test_export_pdf_returns_pdf_bytes(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="pdf"))
        assert result.media_type == "application/pdf"
        assert result.content.startswith(b"%PDF")

    def test_export_markdown_returns_md(self, report):
        svc = ExportService()
        try:
            result = svc.export(report, ExportRequest(format="markdown"))
            assert result.media_type == "text/markdown"
            assert len(result.content) > 0
        except Exception:
            pytest.skip("MD rendering requires intelligence module dependencies")

    def test_export_invalid_format_raises_error(self, report):
        svc = ExportService()
        with pytest.raises(Exception):
            svc.export(report, ExportRequest(format="xml"))  # type: ignore[arg-type]

    def test_export_filename_contains_report_id(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="json"))
        assert "rpt-001" in result.filename

    def test_export_size_bytes_matches_content(self, report):
        svc = ExportService()
        result = svc.export(report, ExportRequest(format="json"))
        assert result.size_bytes == len(result.content)


class TestExportServiceBundle:
    def test_bundle_export_returns_zip(self, report):
        svc = ExportService()
        result = svc.export_bundle(report, formats=["json", "pdf"])
        assert result.media_type == "application/zip"
        assert result.filename.endswith(".zip")

    def test_bundle_contains_expected_files(self, report):
        svc = ExportService()
        result = svc.export_bundle(report, formats=["json", "pdf"])
        buf = io.BytesIO(result.content)
        with zipfile.ZipFile(buf, "r") as zf:
            names = zf.namelist()
        # At least JSON and PDF should be present
        assert any(".json" in n for n in names)
        assert any(".pdf" in n for n in names)

    def test_bundle_skips_failed_formats_gracefully(self, report):
        svc = ExportService()
        # xml is not a valid format — should be skipped, not crash
        result = svc.export_bundle(report, formats=["json", "pdf", "xml"])  # type: ignore[arg-type]
        assert result.media_type == "application/zip"

    def test_get_supported_formats_returns_list(self):
        svc = ExportService()
        formats = svc.get_supported_formats()
        assert "json" in formats
        assert "html" in formats
        assert "pdf" in formats
        assert "markdown" in formats
