"""Developer console widget builders for the Product Experience Layer.

Provides a suite of lightweight, stateless widget classes that transform raw
pipeline execution data (traces, timings, events, memory snapshots) into
structured, frontend-ready dictionaries for rendering developer console
components.

Classes
-------
- ExecutionTimeline     : Normalised pipeline step timeline.
- PipelineStageWidget   : Per-stage timing card data.
- AgentStatusWidget     : Live agent status map.
- PerformanceMetricsWidget : KPI cards (latency, throughput, errors).
- MemoryUsageWidget     : Memory chart data.
- ExecutionLogsWidget   : Paginated log row data.
- EventTimelineWidget   : Chronological event stream.
- RequestInspectorWidget: Request/response diff view.

All widget build() methods are pure functions — they accept raw data and
return structured dicts with no side effects or I/O.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Execution Timeline
# ---------------------------------------------------------------------------


class ExecutionTimeline:
    """Builds a normalised execution timeline from workflow trace records.

    Input: A list of trace step dicts (from WebSocket metadata).
    Output: A list of timeline step dicts sorted by start time.
    """

    @staticmethod
    def build(workflow_trace: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts raw workflow trace steps into a timeline-ready structure.

        Args:
            workflow_trace: List of step dicts with keys: 'step', 'status',
                'time', 'error'.

        Returns:
            List of normalised timeline step dicts with added 'index' and
            'has_error' fields.
        """
        timeline = []
        for idx, step in enumerate(workflow_trace or []):
            status = step.get("status", "unknown").lower()
            timeline.append({
                "index": idx + 1,
                "step": step.get("step", f"Step {idx + 1}"),
                "status": status,
                "duration": step.get("time", "0.00s"),
                "error": step.get("error", ""),
                "has_error": bool(step.get("error", "")),
                "icon": _step_icon(status),
                "color": _status_color(status),
            })
        return timeline


def _step_icon(status: str) -> str:
    return {"success": "✅", "error": "❌", "running": "⏳", "skipped": "⏭️"}.get(status, "⬜")


def _status_color(status: str) -> str:
    return {
        "success": "#22c55e",
        "error": "#ef4444",
        "running": "#eab308",
        "skipped": "#64748b",
    }.get(status, "#94a3b8")


# ---------------------------------------------------------------------------
# Pipeline Stage Widget
# ---------------------------------------------------------------------------


class PipelineStageWidget:
    """Builds per-stage timing card data from pipeline execution metadata."""

    @staticmethod
    def build(stage_timings: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Converts a stage-timing dict into a list of card data objects.

        Args:
            stage_timings: Dict mapping stage name to timing string or float.
                Example: {'extraction': '0.042s', 'embedding': 0.155}

        Returns:
            List of stage card dicts with name, duration_ms, bar_pct, and color.
        """
        if not stage_timings:
            return []

        # Parse durations to float milliseconds
        parsed: List[tuple[str, float]] = []
        for name, val in stage_timings.items():
            try:
                if isinstance(val, str):
                    val = float(val.rstrip("s")) * 1000
                else:
                    val = float(val) * 1000
                parsed.append((name, val))
            except (ValueError, AttributeError):
                parsed.append((name, 0.0))

        max_ms = max((v for _, v in parsed), default=1.0) or 1.0
        cards = []
        for name, ms in parsed:
            cards.append({
                "stage": name.replace("_", " ").title(),
                "key": name,
                "duration_ms": round(ms, 2),
                "duration_label": f"{ms:.1f} ms",
                "bar_pct": round(ms / max_ms * 100, 1),
                "color": _stage_color(name),
            })
        return sorted(cards, key=lambda c: c["duration_ms"], reverse=True)


def _stage_color(stage: str) -> str:
    palette = [
        "#00f0ff", "#a855f7", "#22c55e", "#eab308",
        "#3b82f6", "#f97316", "#ec4899", "#14b8a6",
    ]
    return palette[hash(stage) % len(palette)]


# ---------------------------------------------------------------------------
# Agent Status Widget
# ---------------------------------------------------------------------------


class AgentStatusWidget:
    """Builds a live agent status map from agent state dicts."""

    @staticmethod
    def build(agent_states: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Converts raw agent states to structured status cards.

        Args:
            agent_states: Dict mapping agent name to state dict with
                optional 'status', 'task', 'latency_ms', 'error' keys.

        Returns:
            Dict mapping agent name to enriched status card.
        """
        result: Dict[str, Dict[str, Any]] = {}
        for name, state in (agent_states or {}).items():
            status = state.get("status", "idle")
            result[name] = {
                "agent": name,
                "status": status,
                "task": state.get("task", ""),
                "latency_ms": state.get("latency_ms", 0.0),
                "error": state.get("error", ""),
                "is_active": status in ("running", "processing"),
                "color": _status_color(status),
                "icon": _step_icon(status),
            }
        return result


# ---------------------------------------------------------------------------
# Performance Metrics Widget
# ---------------------------------------------------------------------------


class PerformanceMetricsWidget:
    """Builds KPI card data from PipelineMetrics or PerformanceSnapshot."""

    @staticmethod
    def build(metrics: Any) -> List[Dict[str, Any]]:
        """Converts a PipelineMetrics or PerformanceSnapshot into KPI cards.

        Args:
            metrics: PipelineMetrics or PerformanceSnapshot instance from
                MetricsService, or a plain dict.

        Returns:
            List of KPI card dicts with label, value, unit, and trend color.
        """
        if hasattr(metrics, "model_dump"):
            data = metrics.model_dump()
        elif isinstance(metrics, dict):
            data = metrics
        else:
            return []

        cards: List[Dict[str, Any]] = []

        def _card(label: str, value: Any, unit: str, trend: str = "neutral") -> Dict[str, Any]:
            colors = {"positive": "#22c55e", "negative": "#ef4444", "neutral": "#94a3b8"}
            return {
                "label": label,
                "value": value,
                "unit": unit,
                "trend_color": colors.get(trend, colors["neutral"]),
            }

        if "avg_duration_ms" in data:
            cards.append(_card("Avg Latency", data["avg_duration_ms"], "ms"))
        if "p95_ms" in data:
            cards.append(_card("P95 Latency", data["p95_ms"], "ms"))
        if "p99_ms" in data:
            cards.append(_card("P99 Latency", data["p99_ms"], "ms"))
        if "error_rate_pct" in data:
            trend = "negative" if data["error_rate_pct"] > 5 else "positive"
            cards.append(_card("Error Rate", data["error_rate_pct"], "%", trend))
        if "execution_count" in data:
            cards.append(_card("Executions", data["execution_count"], "runs"))
        if "avg_tokens" in data:
            cards.append(_card("Avg Tokens", data["avg_tokens"], "tok"))

        return cards


# ---------------------------------------------------------------------------
# Memory Usage Widget
# ---------------------------------------------------------------------------


class MemoryUsageWidget:
    """Builds memory chart data from a memory snapshot dict."""

    @staticmethod
    def build(snapshot: Dict[str, Any]) -> Dict[str, Any]:
        """Converts a memory snapshot into a chart-ready data structure.

        Args:
            snapshot: Dict with keys like 'rss_mb', 'heap_mb', 'peak_mb',
                'history' (list of {ts, rss_mb} dicts).

        Returns:
            Chart data dict with current, peak, and history series.
        """
        return {
            "current_rss_mb": snapshot.get("rss_mb", 0.0),
            "heap_mb": snapshot.get("heap_mb", 0.0),
            "peak_mb": snapshot.get("peak_mb", 0.0),
            "history": snapshot.get("history", []),
            "unit": "MB",
            "status": (
                "warning"
                if snapshot.get("rss_mb", 0) > 500
                else "healthy"
            ),
        }


# ---------------------------------------------------------------------------
# Execution Logs Widget
# ---------------------------------------------------------------------------


class ExecutionLogsWidget:
    """Builds paginated, level-filtered log row data."""

    @staticmethod
    def build(
        logs: List[Dict[str, Any]],
        level: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict[str, Any]:
        """Converts raw log records into a paginated, level-tagged structure.

        Args:
            logs: List of log dicts with 'timestamp', 'level', 'message' keys.
            level: Optional log level filter ('DEBUG', 'INFO', 'WARNING', 'ERROR').
            page: Page number (1-indexed).
            page_size: Items per page.

        Returns:
            Dict with 'rows', 'total', 'page', 'has_next', 'has_prev'.
        """
        filtered = logs
        if level:
            filtered = [l for l in logs if l.get("level", "").upper() == level.upper()]

        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_items = filtered[start:end]

        rows = []
        for log in page_items:
            lvl = log.get("level", "INFO").upper()
            rows.append({
                "timestamp": log.get("timestamp", ""),
                "level": lvl,
                "message": log.get("message", ""),
                "color": _log_color(lvl),
            })

        return {
            "rows": rows,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": end < total,
            "has_prev": page > 1,
        }


def _log_color(level: str) -> str:
    return {
        "DEBUG": "#64748b",
        "INFO": "#94a3b8",
        "WARNING": "#eab308",
        "ERROR": "#ef4444",
        "CRITICAL": "#dc2626",
    }.get(level, "#94a3b8")


# ---------------------------------------------------------------------------
# Event Timeline Widget
# ---------------------------------------------------------------------------


class EventTimelineWidget:
    """Builds a chronological, categorised event stream for display."""

    @staticmethod
    def build(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Converts raw event records into a timeline-ready list.

        Args:
            events: List of event dicts with 'timestamp' and 'event' keys.

        Returns:
            List of enriched event dicts with 'index', 'icon', and 'color'.
        """
        enriched = []
        for idx, ev in enumerate(events or []):
            event_text = ev.get("event", "")
            enriched.append({
                "index": idx + 1,
                "timestamp": ev.get("timestamp", ""),
                "event": event_text,
                "icon": _event_icon(event_text),
                "color": "#00f0ff" if idx % 2 == 0 else "#a855f7",
            })
        return enriched


def _event_icon(event_text: str) -> str:
    text_lower = event_text.lower()
    if "error" in text_lower or "fail" in text_lower:
        return "❌"
    if "start" in text_lower or "begin" in text_lower:
        return "🚀"
    if "finish" in text_lower or "complet" in text_lower or "done" in text_lower:
        return "✅"
    if "retriev" in text_lower or "search" in text_lower:
        return "🔍"
    if "embed" in text_lower:
        return "🧬"
    if "model" in text_lower or "inference" in text_lower:
        return "🤖"
    if "stream" in text_lower:
        return "📡"
    return "📌"


# ---------------------------------------------------------------------------
# Request Inspector Widget
# ---------------------------------------------------------------------------


class RequestInspectorWidget:
    """Builds request/response diff view data for the developer console."""

    @staticmethod
    def build(
        request: Dict[str, Any],
        response: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Structures a request/response pair for display in the inspector.

        Args:
            request: Raw request payload dict.
            response: Raw response payload dict.

        Returns:
            Inspector dict with 'request', 'response', 'diff_keys', and metadata.
        """
        req_keys = set(request.keys())
        resp_keys = set(response.keys())
        diff_keys = list(req_keys.symmetric_difference(resp_keys))

        return {
            "request": request,
            "response": response,
            "request_key_count": len(req_keys),
            "response_key_count": len(resp_keys),
            "diff_keys": sorted(diff_keys),
            "has_diff": bool(diff_keys),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
