"""Tests for backend.product.history_service."""

import pytest
from backend.product.history_service import HistoryService, HistoryRecord


def _make_mock_report(report_id: str = "rpt-001", ats_score: float = 80.0):
    """Creates a minimal mock resume-like report object."""
    class MockReport:
        def __init__(self):
            self.report_id = report_id
            self.ats_score = ats_score
            self.executive_summary = "Strong candidate"
            self.workspace_id = "ws-test"

    return MockReport()


@pytest.fixture(autouse=True)
def clean_history():
    """Wipe history table before each test by deleting all records for the test workspace."""
    svc = HistoryService()
    # Remove all records for test workspaces
    conn = svc._db._get_connection()
    with svc._lock:
        conn.execute("DELETE FROM product_history WHERE workspace_id LIKE 'ws-test%'")
        conn.commit()
    conn.close()
    yield
    conn = svc._db._get_connection()
    with svc._lock:
        conn.execute("DELETE FROM product_history WHERE workspace_id LIKE 'ws-test%'")
        conn.commit()
    conn.close()


class TestHistoryServiceSingleton:
    def test_singleton_returns_same_instance(self):
        a = HistoryService()
        b = HistoryService()
        assert a is b


class TestSaveReport:
    def test_save_report_returns_record_id(self):
        svc = HistoryService()
        report = _make_mock_report()
        record_id = svc.save_report(report, report_type="resume", workspace_id="ws-test")
        assert record_id.startswith("hist-")

    def test_saved_report_is_retrievable(self):
        svc = HistoryService()
        report = _make_mock_report(report_id="rpt-saved")
        record_id = svc.save_report(report, report_type="resume", workspace_id="ws-test")
        record = svc.get(record_id)
        assert record is not None
        assert record.report_type == "resume"
        assert record.workspace_id == "ws-test"


class TestListHistory:
    def test_list_returns_records_for_workspace(self):
        svc = HistoryService()
        for i in range(3):
            report = _make_mock_report(report_id=f"rpt-{i}")
            svc.save_report(report, report_type="resume", workspace_id="ws-test")
        records = svc.list("ws-test")
        assert len(records) >= 3

    def test_list_filters_by_report_type(self):
        svc = HistoryService()
        report = _make_mock_report(report_id="rpt-gh")
        svc.save_report(report, report_type="github", workspace_id="ws-test")
        svc.save_report(_make_mock_report(), report_type="resume", workspace_id="ws-test")
        gh_records = svc.list("ws-test", report_type="github")
        assert all(r.report_type == "github" for r in gh_records)

    def test_list_empty_for_unknown_workspace(self):
        svc = HistoryService()
        records = svc.list("ws-unknown-xyz")
        assert records == []


class TestSearchHistory:
    def test_search_finds_records_by_title_substring(self):
        svc = HistoryService()
        report = _make_mock_report()
        svc.save_report(report, report_type="resume", workspace_id="ws-test", title="Senior Python Engineer")
        results = svc.search("ws-test", "Python")
        assert any("Python" in r.title for r in results)

    def test_search_returns_empty_for_no_match(self):
        svc = HistoryService()
        results = svc.search("ws-test", "zzznomatch_xyz")
        assert results == []


class TestPinAndFavorite:
    def test_pin_record(self):
        svc = HistoryService()
        record_id = svc.save_report(_make_mock_report(), report_type="resume", workspace_id="ws-test")
        assert svc.pin(record_id, pinned=True) is True
        record = svc.get(record_id)
        assert record.is_pinned is True

    def test_unpin_record(self):
        svc = HistoryService()
        record_id = svc.save_report(_make_mock_report(), report_type="resume", workspace_id="ws-test")
        svc.pin(record_id, pinned=True)
        svc.pin(record_id, pinned=False)
        record = svc.get(record_id)
        assert record.is_pinned is False

    def test_favorite_record(self):
        svc = HistoryService()
        record_id = svc.save_report(_make_mock_report(), report_type="resume", workspace_id="ws-test")
        assert svc.favorite(record_id, favorited=True) is True
        record = svc.get(record_id)
        assert record.is_favorite is True

    def test_pin_nonexistent_returns_false(self):
        svc = HistoryService()
        assert svc.pin("nonexistent-id", pinned=True) is False


class TestDeleteHistory:
    def test_delete_existing_record_returns_true(self):
        svc = HistoryService()
        record_id = svc.save_report(_make_mock_report(), report_type="resume", workspace_id="ws-test")
        assert svc.delete(record_id) is True
        assert svc.get(record_id) is None

    def test_delete_nonexistent_returns_false(self):
        svc = HistoryService()
        assert svc.delete("fake-id") is False

    def test_bulk_delete_returns_count(self):
        svc = HistoryService()
        ids = []
        for i in range(5):
            rid = svc.save_report(_make_mock_report(f"rpt-bulk-{i}"), report_type="resume", workspace_id="ws-test")
            ids.append(rid)
        deleted = svc.bulk_delete(ids)
        assert deleted == 5

    def test_bulk_delete_empty_list(self):
        svc = HistoryService()
        assert svc.bulk_delete([]) == 0


class TestCountHistory:
    def test_count_by_type(self):
        svc = HistoryService()
        svc.save_report(_make_mock_report("c1"), "resume", "ws-test")
        svc.save_report(_make_mock_report("c2"), "github", "ws-test")
        svc.save_report(_make_mock_report("c3"), "github", "ws-test")
        counts = svc.count("ws-test")
        assert counts.get("resume", 0) >= 1
        assert counts.get("github", 0) >= 2
