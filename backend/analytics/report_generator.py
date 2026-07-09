"""Analytics report generator formatting JSON, HTML, and Markdown dashboards."""

from __future__ import annotations

from backend.analytics.models import AggregateReport


class ReportGenerator:
    """Formats aggregated platform reports into documentation assets."""

    @staticmethod
    def to_markdown(report: AggregateReport) -> str:
        """Renders report object as Markdown."""
        lines = [
            f"# Nexus AI Platform Usage Analytics Report",
            f"",
            f"| Period Start | Period End |",
            f"|---|---|",
            f"| {report.start_time} | {report.end_time} |",
            f"",
            f"## Workflow Success Metrics",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Total Runs | {report.workflow_metrics.get('total_runs', 0)} |",
            f"| Success Rate | {report.workflow_metrics.get('success_rate', 1.0) * 100:.1f}% |",
            f"| Failure Rate | {report.workflow_metrics.get('failure_rate', 0.0) * 100:.1f}% |",
            f"| Average Duration | {report.workflow_metrics.get('avg_duration_ms', 0.0):.1f}ms |",
            f"",
            f"## LLM Provider Metrics",
            f"",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Total Cost | ${report.provider_metrics.get('total_cost_usd', 0.0):.6f} |",
            f"| Total Tokens | {report.provider_metrics.get('total_tokens_consumed', 0)} |",
            f"| Average Latency | {report.provider_metrics.get('avg_latency_ms', 0.0):.1f}ms |",
        ]
        return "\n".join(lines)

    @staticmethod
    def to_json(report: AggregateReport) -> str:
        """Serializes report object to JSON."""
        return report.model_dump_json(indent=2)

    @staticmethod
    def to_html(report: AggregateReport) -> str:
        """Renders report as styled HTML."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Platform Usage Report</title>
<style>
  body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 2rem; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 1rem; border: 1px solid #333; }}
  th {{ background: #1e1e1e; }}
</style>
</head>
<body>
<h1>Usage Analytics Dashboard</h1>
<p>Period: {report.start_time} to {report.end_time}</p>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Total Workflow Runs</td><td>{report.workflow_metrics.get('total_runs', 0)}</td></tr>
  <tr><td>Total Cost (USD)</td><td>{report.provider_metrics.get('total_cost_usd', 0.0):.6f}</td></tr>
</table>
</body>
</html>"""
