"""Tests for backend.product.frontend_adapter."""

import pytest
from unittest.mock import patch, MagicMock
from backend.product.frontend_adapter import (
    ResumePageAdapter,
    GitHubPageAdapter,
    DocumentPageAdapter,
    ResearchPageAdapter,
    DeveloperConsoleAdapter,
    _score_color,
)
from backend.product.cache_service import CacheService
from backend.product.history_service import HistoryService


@pytest.fixture(autouse=True)
def clean_state():
    """Clears cache and history before each test."""
    svc = CacheService()
    from backend.product.cache_service import _VALID_NAMESPACES
    for ns in _VALID_NAMESPACES:
        svc.invalidate_namespace(ns)
    svc.reset_stats()

    hist = HistoryService()
    conn = hist._db._get_connection()
    with hist._lock:
        conn.execute("DELETE FROM product_history WHERE workspace_id LIKE 'ws-test%'")
        conn.commit()
    conn.close()
    yield


class MockResumeReport:
    def __init__(self):
        self.report_id = "rpt-resume-adapter"
        self.ats_score = 82.0
        self.executive_summary = "Strong Python developer"
        self.workspace_id = "ws-test"
        self.career_readiness = "Senior level"
        self.strengths = ["Python", "FastAPI"]
        self.weaknesses = []
        self.missing_skills = ["Kubernetes"]
        self.improvement_roadmap = []
        self.action_plan = []
        self.skill_analysis = {}
        self.job_match = None
        self.resume_pipeline = "Resume Intelligence"
        self.execution_id = "exec-01"
        self.module_timings = {}

    def model_dump(self):
        return {
            "report_id": self.report_id,
            "ats_score": self.ats_score,
            "executive_summary": self.executive_summary,
            "workspace_id": self.workspace_id,
            "career_readiness": self.career_readiness,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "missing_skills": self.missing_skills,
            "improvement_roadmap": self.improvement_roadmap,
            "action_plan": self.action_plan,
            "skill_analysis": self.skill_analysis,
        }

    def model_dump_json(self):
        import json
        return json.dumps(self.model_dump())


class TestResumePageAdapter:
    def test_format_analysis_result_includes_ats_score(self):
        adapter = ResumePageAdapter()
        report = MockResumeReport()
        result = adapter.format_analysis_result(report, workspace_id="ws-test", save_history=False)
        assert result["ats_score"] == 82.0

    def test_format_analysis_result_includes_ui_metadata(self):
        adapter = ResumePageAdapter()
        report = MockResumeReport()
        result = adapter.format_analysis_result(report, workspace_id="ws-test", save_history=False)
        assert "ui" in result
        assert "export_formats" in result["ui"]
        assert "pdf" in result["ui"]["export_formats"]

    def test_format_analysis_result_caches_report(self):
        adapter = ResumePageAdapter()
        report = MockResumeReport()
        adapter.format_analysis_result(report, workspace_id="ws-test", save_history=False)
        cache = CacheService()
        from backend.product.cache_service import NAMESPACE_REPORTS
        assert cache.exists(NAMESPACE_REPORTS, report.report_id)

    def test_format_analysis_saves_to_history(self):
        adapter = ResumePageAdapter()
        report = MockResumeReport()
        adapter.format_analysis_result(report, workspace_id="ws-test", save_history=True)
        hist = HistoryService()
        records = hist.list("ws-test", report_type="resume")
        assert len(records) >= 1


class TestGitHubPageAdapter:
    def test_get_dashboard_stats_has_total_analyses(self):
        adapter = GitHubPageAdapter()
        stats = adapter.get_dashboard_stats("ws-test")
        assert "total_analyses" in stats
        assert "recent_reports" in stats

    def test_get_history_page_returns_dict_with_items(self):
        adapter = GitHubPageAdapter()
        result = adapter.get_history_page("ws-test", page=1, page_size=10)
        assert "items" in result
        assert isinstance(result["items"], list)


class TestDocumentPageAdapter:
    def test_format_citations_returns_list(self):
        adapter = DocumentPageAdapter()
        citations = [
            {"citation_id": "c1", "document_id": "d1", "snippet": "Test content", "relevance_score": 0.9},
            {"citation_id": "c2", "document_id": "d2", "snippet": "Python is fast", "relevance_score": 0.8},
        ]
        result = adapter.format_citations(citations, highlight_query="Python")
        assert len(result) == 2
        assert result[0]["index"] == 1
        python_cit = next(c for c in result if "Python" in c["snippet"])
        assert python_cit["has_highlight"] is True

    def test_format_citations_no_highlight_query(self):
        adapter = DocumentPageAdapter()
        citations = [{"citation_id": "c1", "snippet": "Some text", "relevance_score": 0.5}]
        result = adapter.format_citations(citations)
        assert result[0]["has_highlight"] is False


class TestResearchPageAdapter:
    def test_format_search_results_includes_query(self):
        adapter = ResearchPageAdapter()
        result = adapter.format_search_results([], query="FastAPI performance", total_time_ms=42.0)
        assert result["query"] == "FastAPI performance"
        assert result["retrieval_time_ms"] == 42.0

    def test_format_search_results_empty(self):
        adapter = ResearchPageAdapter()
        result = adapter.format_search_results([], query="test")
        assert result["has_results"] is False
        assert result["results"] == []

    def test_format_citations_for_display(self):
        adapter = ResearchPageAdapter()
        chunks = [
            {"chunk_number": 1, "document_name": "Doc A", "section_name": "Intro", "snippet": "Hello", "similarity_score": 0.95, "included_in_prompt": True},
        ]
        result = adapter.format_citations_for_display(chunks)
        assert len(result) == 1
        assert result[0]["document"] == "Doc A"


class TestDeveloperConsoleAdapter:
    def test_get_timeline_returns_steps(self):
        adapter = DeveloperConsoleAdapter()
        trace = [
            {"step": "User Request", "status": "Success", "time": "0.01s", "error": ""},
            {"step": "Model Provider", "status": "Success", "time": "0.25s", "error": ""},
        ]
        result = adapter.get_timeline(trace)
        assert result["total_steps"] == 2
        assert result["error_count"] == 0

    def test_get_pipeline_stages_returns_stages(self):
        adapter = DeveloperConsoleAdapter()
        timings = {"parsing": "0.05s", "embedding": "0.12s"}
        result = adapter.get_pipeline_stages(timings)
        assert result["total_stages"] == 2
        assert result["slowest_stage"] is not None

    def test_get_agent_status_returns_map(self):
        adapter = DeveloperConsoleAdapter()
        states = {"ChatAgent": {"status": "success"}, "SearchAgent": {"status": "running"}}
        result = adapter.get_agent_status(states)
        assert result["total_count"] == 2
        assert result["active_count"] >= 1

    def test_get_event_stream_returns_events(self):
        adapter = DeveloperConsoleAdapter()
        events = [
            {"timestamp": "T1", "event": "Model inference start"},
            {"timestamp": "T2", "event": "Response streaming finished"},
        ]
        result = adapter.get_event_stream(events)
        assert result["total_events"] == 2


class TestScoreColor:
    def test_high_score_is_green(self):
        assert _score_color(90.0) == "#22c55e"

    def test_medium_score_is_yellow(self):
        assert _score_color(70.0) == "#eab308"

    def test_low_score_is_orange(self):
        assert _score_color(50.0) == "#f97316"

    def test_very_low_score_is_red(self):
        assert _score_color(20.0) == "#ef4444"
