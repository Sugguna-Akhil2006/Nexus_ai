"""Governance report generator producing JSON, HTML, and Markdown layouts."""

from __future__ import annotations

import json

from backend.governance.models import ComplianceStatusReport, RiskReport


class ReportGenerator:
    """Formats compliance status reports and risk scores into documentation templates."""

    @staticmethod
    def to_markdown(compliance: ComplianceStatusReport, risk: RiskReport) -> str:
        """Renders report summary as Markdown."""
        lines = [
            f"# AI Governance Compliance & Risk Report",
            f"",
            f"## Compliance Overview",
            f"",
            f"| Status | Checked At |",
            f"|---|---|",
            f"| {'✅ COMPLIANT' if compliance.overall_passed else '❌ NON-COMPLIANT'} | {compliance.checked_at} |",
            f"",
            f"### Compliance Checks Detail",
            f"",
            f"| Rule | Result | Details |",
            f"|---|---|---|",
        ]
        for res in compliance.results:
            status = "✅ Passed" if res.passed else "❌ Failed"
            lines.append(f"| {res.rule_name} | {status} | {res.details} |")

        lines += [
            f"",
            f"## Risk Assessment Summary",
            f"",
            f"| Risk Level | Risk Score | Checked At |",
            f"|---|---|---|",
            f"| **{risk.risk_level.value.upper()}** | {risk.score:.2f}/1.0 | {risk.calculated_at} |",
            f"",
        ]
        if risk.alerts:
            lines += ["### Risk Alerts", ""]
            for alert in risk.alerts:
                lines.append(f"- ⚠️ {alert}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_json(compliance: ComplianceStatusReport, risk: RiskReport) -> str:
        """Serializes summaries to JSON."""
        return json.dumps(
            {
                "compliance": compliance.model_dump(),
                "risk": risk.model_dump(),
            },
            indent=2,
        )

    @staticmethod
    def to_html(compliance: ComplianceStatusReport, risk: RiskReport) -> str:
        """Renders report summary as styled HTML."""
        colour = "#00c853" if compliance.overall_passed else "#e53935"
        risk_colour = {
            "low": "#00c853",
            "medium": "#ffd600",
            "high": "#ff9100",
            "critical": "#e53935",
        }.get(risk.risk_level.value, "#bdbdbd")

        rows = "".join(
            f"<tr><td>{r.rule_name}</td><td>{'Passed' if r.passed else 'Failed'}</td><td>{r.details}</td></tr>"
            for r in compliance.results
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>AI Governance Report</title>
<style>
  body {{ font-family: sans-serif; background: #121212; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: {colour}; }}
  .badge {{ background: {risk_colour}; color: #000; padding: 0.25rem 0.75rem; border-radius: 4px; font-weight: bold; }}
  table {{ border-collapse: collapse; width: 100%; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 1rem; border: 1px solid #333; }}
  th {{ background: #1e1e1e; }}
</style>
</head>
<body>
<h1>AI Governance Report</h1>
<p>Risk Level: <span class="badge">{risk.risk_level.value.upper()}</span> | Score: {risk.score:.2f}/1.0</p>
<h2>Compliance Checks</h2>
<table>
  <tr><th>Check</th><th>Status</th><th>Details</th></tr>
  {rows}
</table>
</body>
</html>"""
