"""Report generator producing Markdown and JSON certification reports."""

from __future__ import annotations

import json

from backend.certification.models import CertificationRun, CheckStatus


class ReportGenerator:
    """Converts a completed :class:`CertificationRun` into human-readable reports.

    Supported formats:
    - **Markdown** – structured report suitable for documentation and GitHub.
    - **JSON** – machine-readable dump for CI/CD pipelines.
    - **HTML** – styled HTML page for browser viewing.
    """

    @staticmethod
    def to_markdown(run: CertificationRun) -> str:
        """Renders a :class:`CertificationRun` as a Markdown report.

        Args:
            run: Completed certification run.

        Returns:
            Markdown string.
        """
        lines = [
            f"# Nexus AI Platform Certification Report",
            f"",
            f"| Field | Value |",
            f"|---|---|",
            f"| Run ID | `{run.run_id}` |",
            f"| Started | {run.started_at} |",
            f"| Completed | {run.completed_at} |",
            f"| Overall Score | **{run.overall_score}/100** |",
            f"| Certification Level | **{run.certification_level.value.upper()}** |",
            f"| Total Checks | {run.total_checks} |",
            f"| Passed | ✅ {run.total_passed} |",
            f"| Failed | ❌ {run.total_failed} |",
            f"| Warnings | ⚠️ {run.total_warnings} |",
            f"",
        ]

        for domain_report in run.domain_reports:
            lines += [
                f"## {domain_report.domain.value.title()} Domain — Score: {domain_report.score}/100",
                f"",
                f"| Check | Status | Duration | Message |",
                f"|---|---|---|---|",
            ]
            for check in domain_report.checks:
                icon = {"passed": "✅", "failed": "❌", "warning": "⚠️", "skipped": "⏭️"}.get(
                    check.status.value, "❓"
                )
                lines.append(
                    f"| {check.name} | {icon} {check.status.value} | {check.duration_ms}ms | {check.message} |"
                )
            lines.append("")

        if run.recommended_improvements:
            lines += ["## Recommended Improvements", ""]
            for rec in run.recommended_improvements:
                lines.append(f"- {rec}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_json(run: CertificationRun) -> str:
        """Serialises a :class:`CertificationRun` to a JSON string.

        Args:
            run: Completed certification run.

        Returns:
            Indented JSON string.
        """
        return run.model_dump_json(indent=2)

    @staticmethod
    def to_html(run: CertificationRun) -> str:
        """Renders a :class:`CertificationRun` as a minimal styled HTML page.

        Args:
            run: Completed certification run.

        Returns:
            HTML string.
        """
        level_colours = {
            "enterprise": "#00c853",
            "gold": "#ffd600",
            "silver": "#bdbdbd",
            "bronze": "#bf360c",
            "none": "#e53935",
        }
        colour = level_colours.get(run.certification_level.value, "#e53935")

        domain_rows = ""
        for dr in run.domain_reports:
            domain_rows += f"<tr><td>{dr.domain.value.title()}</td><td>{dr.score}</td><td>{dr.passed}/{len(dr.checks)}</td></tr>\n"

        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Nexus Certification {run.run_id}</title>
<style>
  body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: {colour}; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 1rem; border: 1px solid #333; text-align: left; }}
  th {{ background: #1e1e1e; }}
  .badge {{ background: {colour}; color: #000; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: bold; }}
</style>
</head>
<body>
<h1>Nexus AI Platform Certification</h1>
<p>Run ID: <code>{run.run_id}</code> &nbsp;|&nbsp; Completed: {run.completed_at}</p>
<p>Overall Score: <strong>{run.overall_score}/100</strong> &nbsp;
   <span class="badge">{run.certification_level.value.upper()}</span></p>
<table>
  <tr><th>Domain</th><th>Score</th><th>Passed/Total</th></tr>
  {domain_rows}
</table>
</body>
</html>"""
