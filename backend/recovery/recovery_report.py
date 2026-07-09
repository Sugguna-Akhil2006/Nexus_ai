"""Recovery report generator producing Markdown, JSON, and HTML outputs."""

from __future__ import annotations

import json

from backend.recovery.models import RecoveryRun, RecoveryStatus


_STATUS_ICONS = {
    RecoveryStatus.COMPLETED: "✅",
    RecoveryStatus.PARTIAL: "⚠️",
    RecoveryStatus.FAILED: "❌",
    RecoveryStatus.IN_PROGRESS: "🔄",
    RecoveryStatus.PENDING: "⏳",
}


class RecoveryReport:
    """Converts :class:`RecoveryRun` objects into human-readable reports."""

    @staticmethod
    def to_markdown(run: RecoveryRun) -> str:
        """Renders a recovery run as a Markdown report.

        Args:
            run: Completed recovery run.

        Returns:
            Markdown string.
        """
        icon = _STATUS_ICONS.get(run.status, "❓")
        lines = [
            "# Nexus AI Disaster Recovery Report",
            "",
            f"| Field | Value |",
            f"|---|---|",
            f"| Run ID | `{run.run_id}` |",
            f"| Scenario | {run.scenario.value} |",
            f"| Status | {icon} **{run.status.value.upper()}** |",
            f"| Started | {run.started_at} |",
            f"| Completed | {run.completed_at} |",
            f"| Duration | {run.duration_ms:.1f}ms |",
            f"| Integrity Verified | {'✅ Yes' if run.integrity_verified else '❌ No'} |",
            "",
            "## Recovered Components",
            "",
        ]
        if run.recovered_components:
            for comp in run.recovered_components:
                lines.append(f"- ✅ {comp}")
        else:
            lines.append("_None_")

        lines += ["", "## Failed Components", ""]
        if run.failed_components:
            for comp in run.failed_components:
                lines.append(f"- ❌ {comp}")
        else:
            lines.append("_None_")

        lines += ["", "## Recovery Timeline", "", "| Event | Component | Status | Duration | Detail |", "|---|---|---|---|---|"]
        for ev in run.timeline:
            ev_icon = _STATUS_ICONS.get(ev.status, "❓")
            lines.append(
                f"| `{ev.event_id}` | {ev.component} | {ev_icon} {ev.status.value} | {ev.duration_ms:.1f}ms | {ev.detail} |"
            )
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def to_json(run: RecoveryRun) -> str:
        """Serialises a recovery run to JSON.

        Args:
            run: Completed recovery run.

        Returns:
            Indented JSON string.
        """
        return run.model_dump_json(indent=2)

    @staticmethod
    def to_html(run: RecoveryRun) -> str:
        """Renders a recovery run as a styled HTML page.

        Args:
            run: Completed recovery run.

        Returns:
            HTML string.
        """
        status_colour = {
            "completed": "#00c853",
            "partial": "#ffd600",
            "failed": "#e53935",
        }.get(run.status.value, "#bdbdbd")

        timeline_rows = "".join(
            f"<tr><td>{ev.component}</td><td>{ev.status.value}</td>"
            f"<td>{ev.duration_ms:.1f}ms</td><td>{ev.detail}</td></tr>"
            for ev in run.timeline
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Recovery Run {run.run_id}</title>
<style>
  body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: {status_colour}; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 1rem; border: 1px solid #333; text-align: left; }}
  th {{ background: #1e1e1e; }}
  .badge {{ background: {status_colour}; color: #000; padding: 0.25rem 0.75rem;
             border-radius: 4px; font-weight: bold; }}
</style>
</head>
<body>
<h1>Disaster Recovery Report</h1>
<p>Run: <code>{run.run_id}</code> | Scenario: {run.scenario.value} |
   <span class="badge">{run.status.value.upper()}</span></p>
<p>Duration: {run.duration_ms:.1f}ms &nbsp;|&nbsp;
   Integrity: {'✅' if run.integrity_verified else '❌'}</p>
<h2>Timeline</h2>
<table>
  <tr><th>Component</th><th>Status</th><th>Duration</th><th>Detail</th></tr>
  {timeline_rows}
</table>
</body>
</html>"""
