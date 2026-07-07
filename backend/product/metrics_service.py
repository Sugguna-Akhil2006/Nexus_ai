"""Pipeline telemetry and performance metrics aggregation service.

Collects per-execution timing events from AI inference pipelines and
aggregates them into statistical summaries: p50/p95/p99 latencies,
throughput, error rates, and rolling window averages.

Designed as a singleton so all product-layer code shares a single
in-memory metrics store. Thread-safe for concurrent recording.

Example usage::

    svc = MetricsService()
    exec_id = svc.start_execution(pipeline="resume_analysis")
    svc.record_stage(exec_id, stage="parsing", duration_ms=42.0)
    svc.record_stage(exec_id, stage="scoring", duration_ms=155.0)
    svc.finish_execution(exec_id, success=True, total_tokens=512)
    snapshot = svc.get_performance_snapshot()
"""

from __future__ import annotations

import math
import threading
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# Maximum number of execution records to keep in the rolling window
_WINDOW_SIZE = 500


class StageRecord(BaseModel):
    """Timing record for a single pipeline stage within an execution.

    Attributes:
        stage: Name of the pipeline stage (e.g. 'parsing', 'embedding').
        duration_ms: Wall-clock duration in milliseconds.
        success: Whether the stage completed without error.
        error: Optional error message on failure.
    """

    stage: str
    duration_ms: float
    success: bool = True
    error: Optional[str] = None


class ExecutionRecord(BaseModel):
    """Complete telemetry record for a single pipeline execution.

    Attributes:
        execution_id: Unique identifier for this execution run.
        pipeline: Name of the pipeline (e.g. 'resume_analysis').
        stages: List of per-stage timing records.
        total_duration_ms: Total wall-clock time in milliseconds.
        total_tokens: Combined prompt + completion token count.
        success: Whether the execution completed without error.
        error: Optional top-level error message.
        started_at: UTC start timestamp.
        completed_at: UTC completion timestamp.
        metadata: Arbitrary execution-level context.
    """

    execution_id: str
    pipeline: str
    stages: List[StageRecord] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    success: bool = True
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineMetrics(BaseModel):
    """Aggregated metrics for a named pipeline over a rolling window.

    Attributes:
        pipeline: Pipeline name.
        execution_count: Total executions in the window.
        success_count: Successful executions.
        error_count: Failed executions.
        error_rate_pct: Percentage of failed executions.
        avg_duration_ms: Mean total duration.
        p50_ms: Median duration.
        p95_ms: 95th-percentile duration.
        p99_ms: 99th-percentile duration.
        avg_tokens: Mean token count per execution.
        stage_avg_ms: Per-stage average duration mapping.
    """

    pipeline: str
    execution_count: int
    success_count: int
    error_count: int
    error_rate_pct: float
    avg_duration_ms: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_tokens: float
    stage_avg_ms: Dict[str, float] = Field(default_factory=dict)


class PerformanceSnapshot(BaseModel):
    """Global performance snapshot across all tracked pipelines.

    Attributes:
        snapshot_at: UTC timestamp when this snapshot was generated.
        total_executions: Total executions across all pipelines.
        overall_error_rate_pct: Global error rate percentage.
        overall_avg_duration_ms: Global average duration.
        pipeline_metrics: Per-pipeline aggregated metrics.
        memory_peak_mb: Optional reported peak memory usage.
    """

    snapshot_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_executions: int = 0
    overall_error_rate_pct: float = 0.0
    overall_avg_duration_ms: float = 0.0
    pipeline_metrics: Dict[str, PipelineMetrics] = Field(default_factory=dict)
    memory_peak_mb: Optional[float] = None


class MetricsService:
    """Singleton pipeline telemetry collector and performance aggregator.

    Records per-execution stage timings and aggregates them into statistical
    summaries on demand. Maintains a rolling window of the last _WINDOW_SIZE
    executions per pipeline to bound memory usage.
    """

    _instance: Optional["MetricsService"] = None
    _class_lock: threading.Lock = threading.Lock()

    def __new__(cls) -> "MetricsService":
        with cls._class_lock:
            if cls._instance is None:
                instance = super().__new__(cls)
                # Active (in-progress) executions keyed by execution_id
                instance._active: Dict[str, ExecutionRecord] = {}
                # Completed execution rolling windows keyed by pipeline name
                instance._windows: Dict[str, Deque[ExecutionRecord]] = defaultdict(
                    lambda: deque(maxlen=_WINDOW_SIZE)
                )
                instance._lock = threading.RLock()
                cls._instance = instance
        return cls._instance

    # ------------------------------------------------------------------
    # Recording API
    # ------------------------------------------------------------------

    def start_execution(
        self,
        pipeline: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Begins recording a new pipeline execution.

        Args:
            pipeline: Pipeline name label.
            metadata: Optional context metadata.

        Returns:
            Unique execution_id string.
        """
        execution_id = f"exec-{str(uuid.uuid4())[:12]}"
        record = ExecutionRecord(
            execution_id=execution_id,
            pipeline=pipeline,
            metadata=metadata or {},
        )
        with self._lock:
            self._active[execution_id] = record
        return execution_id

    def record_stage(
        self,
        execution_id: str,
        stage: str,
        duration_ms: float,
        success: bool = True,
        error: Optional[str] = None,
    ) -> bool:
        """Records a stage timing event for an active execution.

        Args:
            execution_id: Target execution identifier.
            stage: Stage name.
            duration_ms: Stage duration in milliseconds.
            success: Whether the stage succeeded.
            error: Optional error message.

        Returns:
            True on success, False if execution not found.
        """
        with self._lock:
            record = self._active.get(execution_id)
            if record is None:
                return False
            record.stages.append(
                StageRecord(
                    stage=stage,
                    duration_ms=duration_ms,
                    success=success,
                    error=error,
                )
            )
            return True

    def finish_execution(
        self,
        execution_id: str,
        success: bool = True,
        total_tokens: int = 0,
        error: Optional[str] = None,
    ) -> Optional[ExecutionRecord]:
        """Finalises an active execution and archives it in the rolling window.

        Args:
            execution_id: Target execution identifier.
            success: Whether the overall execution succeeded.
            total_tokens: Total token count (prompt + completion).
            error: Optional top-level error description.

        Returns:
            The completed ExecutionRecord, or None if not found.
        """
        with self._lock:
            record = self._active.pop(execution_id, None)
            if record is None:
                return None
            record.success = success
            record.error = error
            record.total_tokens = total_tokens
            record.completed_at = datetime.now(timezone.utc)
            if record.started_at and record.completed_at:
                record.total_duration_ms = (
                    record.completed_at - record.started_at
                ).total_seconds() * 1000
            self._windows[record.pipeline].append(record)
            return record

    # ------------------------------------------------------------------
    # Aggregation API
    # ------------------------------------------------------------------

    def get_pipeline_metrics(self, pipeline: str) -> Optional[PipelineMetrics]:
        """Computes aggregated metrics for a named pipeline.

        Args:
            pipeline: Pipeline name label.

        Returns:
            PipelineMetrics if any executions exist, else None.
        """
        with self._lock:
            records = list(self._windows.get(pipeline, []))
        if not records:
            return None
        return self._compute_metrics(pipeline, records)

    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """Returns a global snapshot across all tracked pipelines.

        Returns:
            PerformanceSnapshot with per-pipeline metrics and global KPIs.
        """
        with self._lock:
            all_pipelines = {k: list(v) for k, v in self._windows.items()}

        pipeline_metrics: Dict[str, PipelineMetrics] = {}
        all_durations: List[float] = []
        total_exec = 0
        total_err = 0

        for pipeline, records in all_pipelines.items():
            if not records:
                continue
            m = self._compute_metrics(pipeline, records)
            pipeline_metrics[pipeline] = m
            total_exec += m.execution_count
            total_err += m.error_count
            all_durations.extend(r.total_duration_ms for r in records)

        overall_err_rate = (total_err / total_exec * 100) if total_exec > 0 else 0.0
        overall_avg = (sum(all_durations) / len(all_durations)) if all_durations else 0.0

        return PerformanceSnapshot(
            total_executions=total_exec,
            overall_error_rate_pct=round(overall_err_rate, 2),
            overall_avg_duration_ms=round(overall_avg, 2),
            pipeline_metrics=pipeline_metrics,
        )

    def list_pipelines(self) -> List[str]:
        """Returns names of all pipelines that have been recorded.

        Returns:
            List of pipeline name strings.
        """
        with self._lock:
            return list(self._windows.keys())

    def clear(self) -> None:
        """Clears all recorded execution data (useful in tests)."""
        with self._lock:
            self._active.clear()
            self._windows.clear()

    # ------------------------------------------------------------------
    # Internal Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _percentile(values: List[float], pct: float) -> float:
        """Computes a percentile value from a sorted list.

        Args:
            values: Sorted list of numeric values.
            pct: Percentile (0–100).

        Returns:
            Interpolated percentile value, or 0.0 for empty lists.
        """
        if not values:
            return 0.0
        k = (len(values) - 1) * pct / 100
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return values[int(k)]
        return values[f] * (c - k) + values[c] * (k - f)

    def _compute_metrics(
        self, pipeline: str, records: List[ExecutionRecord]
    ) -> PipelineMetrics:
        """Builds a PipelineMetrics from a list of execution records.

        Args:
            pipeline: Pipeline name.
            records: List of completed ExecutionRecord instances.

        Returns:
            Aggregated PipelineMetrics.
        """
        durations = sorted(r.total_duration_ms for r in records)
        successes = sum(1 for r in records if r.success)
        errors = len(records) - successes
        error_rate = (errors / len(records) * 100) if records else 0.0

        # Stage aggregation
        stage_totals: Dict[str, List[float]] = defaultdict(list)
        for record in records:
            for stage in record.stages:
                stage_totals[stage.stage].append(stage.duration_ms)
        stage_avg = {
            s: round(sum(v) / len(v), 2) for s, v in stage_totals.items()
        }

        avg_tokens = sum(r.total_tokens for r in records) / len(records)

        return PipelineMetrics(
            pipeline=pipeline,
            execution_count=len(records),
            success_count=successes,
            error_count=errors,
            error_rate_pct=round(error_rate, 2),
            avg_duration_ms=round(sum(durations) / len(durations), 2),
            p50_ms=round(self._percentile(durations, 50), 2),
            p95_ms=round(self._percentile(durations, 95), 2),
            p99_ms=round(self._percentile(durations, 99), 2),
            avg_tokens=round(avg_tokens, 1),
            stage_avg_ms=stage_avg,
        )
