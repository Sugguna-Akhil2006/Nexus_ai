"""Migration report generator producing Markdown, JSON, and HTML formats."""

from __future__ import annotations

import json

from backend.migration.models import MigrationRun, MigrationStatus


class MigrationReport:
    """Renders migration run logs and plans into multiple documentation formats."""

    @staticmethod
    def to_markdown(run: MigrationRun) -> str:
        """Renders migration run as Markdown."""
        lines = [
            f"# Nexus AI Platform Migration Report",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| Run ID | `{run.run_id}` |",
            f"| Plan ID | `{run.plan_id}` |",
            f"| Source Version | {run.from_version} |",
            f"| Target Version | {run.to_version} |",
            f"| Status | **{run.status.value.upper()}** |",
            f"| Started At | {run.started_at} |",
            f"| Completed At | {run.completed_at} |",
            f"| Duration | {run.duration_ms:.2f}ms |",
            f"| Rollback Available | {'✅ Yes' if run.can_rollback else '❌ No'} |",
            f"",
            f"## Migration Steps",
            f"",
            f"| Step ID | Kind | Description | Status | Duration | Error |",
            f"|---|---|---|---|---|---|",
        ]
        for step in run.steps:
            err_msg = f"`{step.error}`" if step.error else ""
            lines.append(
                f"| `{step.step_id}` | {step.kind.value} | {step.description} | {step.status.value} | {step.duration_ms:.1f}ms | {err_msg} |"
            )
        return "\n".join(lines)

    @staticmethod
    def to_json(run: MigrationRun) -> str:
        """Serializes the run record to JSON."""
        return run.model_dump_json(indent=2)

    @staticmethod
    def to_html(run: MigrationRun) -> str:
        """Renders the run record as a styled HTML page."""
        colour = "#00c853" if run.status == MigrationStatus.COMPLETED else "#e53935"
        rows = "".join(
            f"<tr><td>{s.kind.value}</td><td>{s.description}</td><td>{s.status.value}</td>"
            f"<td>{s.duration_ms:.1f}ms</td><td>{s.error or ''}</td></tr>"
            for s in run.steps
        )
        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Migration Report {run.run_id}</title>
<style>
  body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: {colour}; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 1rem; border: 1px solid #333; text-align: left; }}
  th {{ background: #1e1e1e; }}
</style>
</head>
<body>
<h1>Migration Run Report</h1>
<p>Run ID: <code>{run.run_id}</code> | Status: <strong>{run.status.value.upper()}</strong></p>
<p>Upgrade: {run.from_version} &rarr; {run.to_version} | Duration: {run.duration_ms:.1f}ms</p>
<table>
  <tr><th>Kind</th><th>Description</th><th>Status</th><th>Duration</th><th>Error</th></tr>
  {rows}
</table>
</body>
</html>"""
