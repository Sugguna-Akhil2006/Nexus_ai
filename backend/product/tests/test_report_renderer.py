"""Tests for backend.product.pdf_renderer."""

import pytest
from backend.product.pdf_renderer import PDFRenderer, PDFLayout


class MockResumeReport:
    __class__ = type("ProductResumeReport", (), {"__name__": "ProductResumeReport"})()

    def __init__(self):
        self.report_id = "rpt-resume-01"
        self.document_id = "doc-01"
        self.workspace_id = "ws-test"
        self.ats_score = 88.0
        self.executive_summary = "Excellent senior engineer with 8 years Python experience."
        self.skill_analysis = {"Languages": ["Python", "Go"], "Frameworks": ["FastAPI"]}
        self.missing_skills = ["Kubernetes", "Rust"]
        self.strengths = ["Strong API design", "TDD proficient"]
        self.career_readiness = "Ready for senior roles."
        self.action_plan = []


class MockGitHubReport:
    __class__ = type("GitHubIntelligenceReport", (), {"__name__": "GitHubIntelligenceReport"})()

    def __init__(self):
        self.report_id = "rpt-gh-01"
        self.repository = "org/nexus-ai"
        self.timestamp = "2025-01-01"
        self.executive_summary = "Well-maintained Python monorepo."
        self.technology_stack = {"languages": ["Python"], "frameworks": ["FastAPI"]}
        self.engineering_quality = {"maintainability_score": 85.0}
        self.strengths = ["Clean architecture"]
        self.improvement_roadmap = ["Add integration tests"]


class MockGenericReport:
    def __init__(self):
        self.report_id = "rpt-generic-01"
        self.workspace_id = "ws-test"
        self.name = "Document Report"
        self.confidence = 0.92

    def model_dump(self):
        return {
            "report_id": self.report_id,
            "workspace_id": self.workspace_id,
            "name": self.name,
            "confidence": self.confidence,
        }


class TestPDFRendererResume:
    def test_render_resume_returns_bytes(self):
        renderer = PDFRenderer()
        report = MockResumeReport()
        # Type hack: make isinstance checks work by forcing class name
        report.__class__.__name__ = "ProductResumeReport"
        pdf = renderer.render_resume(report)
        assert isinstance(pdf, bytes)

    def test_render_resume_starts_with_pdf_header(self):
        renderer = PDFRenderer()
        report = MockResumeReport()
        report.__class__.__name__ = "ProductResumeReport"
        pdf = renderer.render_resume(report)
        assert pdf.startswith(b"%PDF")

    def test_render_resume_ends_with_eof(self):
        renderer = PDFRenderer()
        report = MockResumeReport()
        report.__class__.__name__ = "ProductResumeReport"
        pdf = renderer.render_resume(report)
        assert b"%%EOF" in pdf


class TestPDFRendererGitHub:
    def test_render_github_returns_bytes(self):
        renderer = PDFRenderer()
        report = MockGitHubReport()
        report.__class__.__name__ = "GitHubIntelligenceReport"
        pdf = renderer.render_github(report)
        assert isinstance(pdf, bytes)

    def test_render_github_is_valid_pdf(self):
        renderer = PDFRenderer()
        report = MockGitHubReport()
        report.__class__.__name__ = "GitHubIntelligenceReport"
        pdf = renderer.render_github(report)
        assert pdf.startswith(b"%PDF")


class TestPDFRendererGeneric:
    def test_render_generic_returns_bytes(self):
        renderer = PDFRenderer()
        report = MockGenericReport()
        pdf = renderer.render_generic(report)
        assert isinstance(pdf, bytes)
        assert pdf.startswith(b"%PDF")

    def test_render_dispatches_to_generic_for_unknown(self):
        renderer = PDFRenderer()
        report = MockGenericReport()
        pdf = renderer.render(report)
        assert pdf.startswith(b"%PDF")


class TestPDFLayout:
    def test_default_layout_is_a4(self):
        layout = PDFLayout()
        assert layout.page_width == 595.0
        assert layout.page_height == 842.0

    def test_custom_layout_applied(self):
        layout = PDFLayout(margin_top=80.0, body_font_size=12)
        renderer = PDFRenderer(layout=layout)
        assert renderer.layout.margin_top == 80.0
        assert renderer.layout.body_font_size == 12

    def test_pdf_with_custom_layout_is_valid(self):
        layout = PDFLayout(page_width=612.0, page_height=792.0)  # US Letter
        renderer = PDFRenderer(layout=layout)
        report = MockGenericReport()
        pdf = renderer.render_generic(report)
        assert pdf.startswith(b"%PDF")
