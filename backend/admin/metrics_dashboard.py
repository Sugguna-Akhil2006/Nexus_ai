"""Aggregates metrics for usage, response times, throughput, and success rates."""

from typing import Any, Dict, List
import random
from datetime import datetime, timedelta, timezone

from backend.product.metrics_service import MetricsService


class MetricsDashboard:
    """Telemetry analyzer collecting analytics summaries for daily pipelines execution and errors."""

    def __init__(self) -> None:
        self._metrics_svc = MetricsService()

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Compiles timing percentiles and execution counts across active intelligence pipelines."""
        global_snapshot = self._metrics_svc.get_performance_snapshot()
        
        # Calculate pipeline throughput
        pipelines = self._metrics_svc.list_pipelines()
        pipeline_data = {}
        for p in pipelines:
            m = self._metrics_svc.get_pipeline_metrics(p)
            if m:
                pipeline_data[p] = {
                    "count": m.execution_count,
                    "avg_duration_ms": m.avg_duration_ms,
                    "error_rate": m.error_rate_pct,
                    "avg_tokens": m.avg_tokens
                }

        # Daily usage analytics from SQLite DB storage
        from backend.api.sqlite_mock import DBStorage
        db = DBStorage()
        daily_analyses = []
        now = datetime.now(timezone.utc)
        conn = db._get_connection()
        try:
            for i in range(7):
                day = now - timedelta(days=i)
                day_str = day.strftime("%Y-%m-%d")
                
                # Check resumes created on this day
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM documents WHERE datetime(created_at) >= ? AND datetime(created_at) < ?",
                    (f"{day_str} 00:00:00", f"{day_str} 23:59:59")
                )
                doc_count = cursor.fetchone()[0]
                
                # Add workflow runs
                cursor.execute(
                    "SELECT COUNT(*) FROM workflow_instances WHERE datetime(started_at) >= ? AND datetime(started_at) < ?",
                    (f"{day_str} 00:00:00", f"{day_str} 23:59:59")
                )
                flow_count = cursor.fetchone()[0]
                
                total_runs = doc_count + flow_count
                
                # Success rate
                cursor.execute(
                    "SELECT COUNT(*) FROM workflow_instances WHERE status = 'failed' AND datetime(started_at) >= ? AND datetime(started_at) < ?",
                    (f"{day_str} 00:00:00", f"{day_str} 23:59:59")
                )
                failed_count = cursor.fetchone()[0]
                
                success_rate = 100.0
                if total_runs > 0:
                    success_rate = round(((total_runs - failed_count) / total_runs) * 100, 1)
                
                daily_analyses.append({
                    "date": day_str,
                    "analyses_count": total_runs,
                    "success_rate_pct": success_rate
                })
        except Exception:
            for i in range(7):
                day = now - timedelta(days=i)
                daily_analyses.append({
                    "date": day.strftime("%Y-%m-%d"),
                    "analyses_count": 0,
                    "success_rate_pct": 100.0
                })
        finally:
            conn.close()

        # Most used intelligence module helper
        most_used = "Resume Intelligence"
        max_count = 0
        for p, data in pipeline_data.items():
            if data["count"] > max_count:
                max_count = data["count"]
                most_used = p.replace("_", " ").title()

        return {
            "total_executions": global_snapshot.total_executions,
            "overall_error_rate_pct": global_snapshot.overall_error_rate_pct,
            "overall_avg_duration_ms": global_snapshot.overall_avg_duration_ms,
            "pipelines": pipeline_data,
            "daily_analyses": list(reversed(daily_analyses)),
            "most_used_module": most_used,
            "success_rate_pct": round(100.0 - global_snapshot.overall_error_rate_pct, 2)
        }
