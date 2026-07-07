"""Tests for backend.product.progress_tracker."""

import pytest
from backend.product.progress_tracker import ProgressTracker, JobStatus


@pytest.fixture(autouse=True)
def fresh_tracker():
    """Reset the singleton tracker state before each test."""
    tracker = ProgressTracker()
    with tracker._lock:
        tracker._jobs.clear()
    yield
    with tracker._lock:
        tracker._jobs.clear()


class TestProgressTrackerSingleton:
    def test_singleton_returns_same_instance(self):
        a = ProgressTracker()
        b = ProgressTracker()
        assert a is b


class TestJobCreation:
    def test_create_job_returns_id(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job(job_type="test", label="Test Job")
        assert job_id.startswith("pjob-")

    def test_created_job_is_queued(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job(job_type="test", label="Test Job")
        job = tracker.get_job(job_id)
        assert job is not None
        assert job.status == JobStatus.QUEUED

    def test_created_job_has_zero_progress(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job(job_type="test", label="Test Job")
        job = tracker.get_job(job_id)
        assert job.progress_pct == 0


class TestJobLifecycle:
    def test_start_job_transitions_to_running(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("analysis", "Analyze")
        assert tracker.start_job(job_id) is True
        job = tracker.get_job(job_id)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_start_already_running_job_returns_false(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("analysis", "Analyze")
        tracker.start_job(job_id)
        assert tracker.start_job(job_id) is False

    def test_update_job_progress(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("analysis", "Analyze")
        tracker.start_job(job_id)
        tracker.update_job(job_id, progress_pct=50, stage="Midpoint", message="Half done")
        job = tracker.get_job(job_id)
        assert job.progress_pct == 50
        assert job.stage == "Midpoint"
        assert job.message == "Half done"

    def test_complete_job_sets_status(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("export", "Export")
        tracker.start_job(job_id)
        tracker.complete_job(job_id, result={"file": "report.pdf"})
        job = tracker.get_job(job_id)
        assert job.status == JobStatus.COMPLETED
        assert job.progress_pct == 100
        assert job.result == {"file": "report.pdf"}
        assert job.completed_at is not None

    def test_fail_job_sets_error(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("scan", "Scan")
        tracker.start_job(job_id)
        tracker.fail_job(job_id, error="Out of memory")
        job = tracker.get_job(job_id)
        assert job.status == JobStatus.FAILED
        assert "memory" in job.error

    def test_cancel_queued_job(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("scan", "Scan")
        assert tracker.cancel_job(job_id) is True
        job = tracker.get_job(job_id)
        assert job.status == JobStatus.CANCELLED

    def test_cancel_terminal_job_returns_false(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("scan", "Scan")
        tracker.start_job(job_id)
        tracker.complete_job(job_id)
        assert tracker.cancel_job(job_id) is False

    def test_retry_failed_job(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("retry_test", "Retry")
        tracker.start_job(job_id)
        tracker.fail_job(job_id, error="timeout")
        assert tracker.retry_job(job_id) is True
        job = tracker.get_job(job_id)
        assert job.status == JobStatus.QUEUED
        assert job.retry_count == 1

    def test_retry_exceeds_max_returns_false(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("retry_test", "Retry", max_retries=1)
        # First retry
        tracker.start_job(job_id)
        tracker.fail_job(job_id, "err1")
        tracker.retry_job(job_id)
        # Second failure — should hit max
        tracker.start_job(job_id)
        tracker.fail_job(job_id, "err2")
        assert tracker.retry_job(job_id) is False


class TestJobQueries:
    def test_list_jobs_returns_all(self):
        tracker = ProgressTracker()
        for i in range(3):
            tracker.create_job("type_a", f"Job {i}")
        jobs = tracker.list_jobs()
        assert len(jobs) >= 3

    def test_list_jobs_filter_by_status(self):
        tracker = ProgressTracker()
        j1 = tracker.create_job("type_a", "J1")
        j2 = tracker.create_job("type_a", "J2")
        tracker.start_job(j1)
        tracker.complete_job(j1)
        completed = tracker.list_jobs(status=JobStatus.COMPLETED)
        queued = tracker.list_jobs(status=JobStatus.QUEUED)
        assert all(j.status == JobStatus.COMPLETED for j in completed)
        assert all(j.status == JobStatus.QUEUED for j in queued)

    def test_list_jobs_filter_by_type(self):
        tracker = ProgressTracker()
        tracker.create_job("alpha", "A1")
        tracker.create_job("beta", "B1")
        alpha_jobs = tracker.list_jobs(job_type="alpha")
        assert all(j.job_type == "alpha" for j in alpha_jobs)

    def test_summary_returns_all_statuses(self):
        tracker = ProgressTracker()
        tracker.create_job("x", "X")
        summary = tracker.summary()
        assert "queued" in summary
        assert "running" in summary
        assert "completed" in summary
        assert "failed" in summary

    def test_get_nonexistent_job_returns_none(self):
        tracker = ProgressTracker()
        assert tracker.get_job("nonexistent-id") is None

    def test_duration_seconds_when_running(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("dur_test", "Dur")
        tracker.start_job(job_id)
        job = tracker.get_job(job_id)
        dur = job.duration_seconds()
        assert dur is not None
        assert dur >= 0.0

    def test_is_terminal_for_completed(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("term_test", "T")
        tracker.start_job(job_id)
        tracker.complete_job(job_id)
        job = tracker.get_job(job_id)
        assert job.is_terminal() is True

    def test_is_terminal_for_queued(self):
        tracker = ProgressTracker()
        job_id = tracker.create_job("term_test", "T")
        job = tracker.get_job(job_id)
        assert job.is_terminal() is False
