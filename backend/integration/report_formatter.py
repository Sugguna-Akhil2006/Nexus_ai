"""Report formatter — serializes ``ComposedResponse`` into frontend-consumable formats.

Supports JSON, Markdown, HTML, and PDF metadata.  No third-party
PDF library is required; PDF metadata is returned as a JSON descriptor
that the frontend uses to trigger a client-side PDF generation step.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict

from backend.intelligence.composition.models import ComposedResponse
from backend.integration.frontend_contracts import FormattedReport, ReportFormat


class ReportFormatter:
    """Converts a ``ComposedResponse`` into the format requested by the frontend."""

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    @classmethod
    def format(
        cls,
        report: ComposedResponse,
        fmt: ReportFormat,
        request_id: str,
    ) -> FormattedReport:
        """Serializes *report* in the requested *fmt*.

        Args:
            report:     The composed intelligence report.
            fmt:        Target output format.
            request_id: Originating request ID, echoed into the result.

        Returns:
            ``FormattedReport`` with ``content`` and ``content_type`` filled.
        """
        dispatch = {
            ReportFormat.JSON: cls._to_json,
            ReportFormat.MARKDOWN: cls._to_markdown,
            ReportFormat.HTML: cls._to_html,
            ReportFormat.PDF_METADATA: cls._to_pdf_metadata,
        }
        handler = dispatch[fmt]
        content, content_type = handler(report)
        return FormattedReport(
            request_id=request_id,
            format=fmt,
            content=content,
            content_type=content_type,
            size_bytes=len(content.encode("utf-8")),
        )

    # ------------------------------------------------------------------
    # JSON
    # ------------------------------------------------------------------

    @classmethod
    def _to_json(cls, r: ComposedResponse) -> tuple[str, str]:
        data: Dict[str, Any] = {
            "composition_id": r.composition_id,
            "status": r.status.value,
            "executive_summary": r.executive_summary,
            "overall_confidence": (
                r.aggregated_confidence.overall if r.aggregated_confidence else 0.0
            ),
            "participating_modules": r.participating_modules,
            "detailed_findings": [f.model_dump() for f in r.detailed_findings],
            "recommendations": [rec.model_dump() for rec in r.recommendations],
            "citations": [c.model_dump() for c in r.citations],
            "artifacts": [a.model_dump() for a in r.artifacts],
            "conflicts": [c.model_dump() for c in r.conflicts],
            "metrics": {
                "total_duration_ms": r.total_duration_ms,
                "total_tokens_in": r.total_tokens_in,
                "total_tokens_out": r.total_tokens_out,
                "estimated_cost_usd": r.estimated_cost_usd,
            },
            "generated_at": datetime.utcnow().isoformat(),
        }
        return json.dumps(data, indent=2, default=str), "application/json"

    # ------------------------------------------------------------------
    # Markdown
    # ------------------------------------------------------------------

    @classmethod
    def _to_markdown(cls, r: ComposedResponse) -> tuple[str, str]:
        lines = [
            f"# Intelligence Analysis Report",
            f"",
            f"**Composition ID:** `{r.composition_id}`  ",
            f"**Status:** {r.status.value}  ",
            f"**Confidence:** "
            f"{r.aggregated_confidence.overall:.0%}" if r.aggregated_confidence else "N/A",
            f"**Modules:** {', '.join(r.participating_modules)}",
            f"",
            f"---",
            f"",
            f"## Executive Summary",
            f"",
            r.executive_summary,
            f"",
        ]

        if r.detailed_findings:
            lines += ["## Detailed Findings", ""]
            for f in r.detailed_findings:
                lines += [
                    f"### {f.title}",
                    f"**Category:** {f.category}  ",
                    f"**Confidence:** {f.confidence:.0%}  ",
                    f"**Sources:** {', '.join(f.source_modules)}  ",
                    f"",
                    f.description,
                    f"",
                ]

        if r.recommendations:
            lines += ["## Recommendations", ""]
            for rec in r.recommendations:
                lines += [
                    f"- **[{rec.priority.upper()}]** {rec.title}: {rec.description}"
                ]
            lines.append("")

        if r.citations:
            lines += ["## References", ""]
            for i, cit in enumerate(r.citations, 1):
                lines.append(f"{i}. **{cit.title or cit.identifier}** ({cit.source_type})")
            lines.append("")

        if r.conflicts:
            lines += ["## Conflicts Detected", ""]
            for c in r.conflicts:
                resolved = "✅ Resolved" if c.resolved else "⚠️ Unresolved"
                lines += [
                    f"- **{c.field}** ({c.severity.value} severity): "
                    f"{c.module_a}=`{c.value_a}` vs {c.module_b}=`{c.value_b}` — {resolved}"
                ]
            lines.append("")

        lines += [
            "---",
            f"*Generated at {datetime.utcnow().isoformat()} | "
            f"Duration: {r.total_duration_ms:.0f}ms | "
            f"Cost: ${r.estimated_cost_usd:.4f}*",
        ]
        return "\n".join(lines), "text/markdown"

    # ------------------------------------------------------------------
    # HTML
    # ------------------------------------------------------------------

    @classmethod
    def _to_html(cls, r: ComposedResponse) -> tuple[str, str]:
        conf = r.aggregated_confidence.overall if r.aggregated_confidence else 0.0
        findings_html = "".join(
            f"<li><strong>{f.title}</strong> — {f.description[:200]}</li>"
            for f in r.detailed_findings
        )
        recs_html = "".join(
            f"<li><span class='priority-{rec.priority}'>[{rec.priority.upper()}]</span> "
            f"<strong>{rec.title}</strong>: {rec.description}</li>"
            for rec in r.recommendations
        )
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Nexus AI Intelligence Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           max-width: 900px; margin: 40px auto; color: #1a1a1a; line-height: 1.6; }}
    h1 {{ color: #6366f1; border-bottom: 2px solid #6366f1; padding-bottom: 8px; }}
    h2 {{ color: #4f46e5; margin-top: 32px; }}
    .meta {{ background: #f5f3ff; padding: 12px 16px; border-radius: 8px;
             display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 24px; }}
    .meta span {{ font-size: 0.9em; color: #555; }}
    .meta strong {{ color: #1a1a1a; }}
    .summary {{ background: #fafafa; border-left: 4px solid #6366f1;
                padding: 16px; border-radius: 4px; }}
    ul.findings {{ list-style: none; padding: 0; }}
    ul.findings li {{ background: #f9f9f9; margin: 8px 0; padding: 12px;
                      border-radius: 6px; border: 1px solid #eee; }}
    .priority-high, .priority-critical {{ color: #dc2626; }}
    .priority-medium {{ color: #d97706; }}
    .priority-low {{ color: #16a34a; }}
    footer {{ margin-top: 48px; font-size: 0.8em; color: #888; border-top: 1px solid #eee;
              padding-top: 12px; }}
  </style>
</head>
<body>
  <h1>Nexus AI — Intelligence Analysis Report</h1>
  <div class="meta">
    <span><strong>ID:</strong> {r.composition_id}</span>
    <span><strong>Status:</strong> {r.status.value}</span>
    <span><strong>Confidence:</strong> {conf:.0%}</span>
    <span><strong>Modules:</strong> {', '.join(r.participating_modules)}</span>
    <span><strong>Duration:</strong> {r.total_duration_ms:.0f}ms</span>
  </div>
  <h2>Executive Summary</h2>
  <div class="summary">{r.executive_summary}</div>
  <h2>Detailed Findings</h2>
  <ul class="findings">{findings_html}</ul>
  <h2>Recommendations</h2>
  <ul>{recs_html}</ul>
  <footer>Generated {datetime.utcnow().isoformat()} &bull;
          Cost: ${r.estimated_cost_usd:.4f}</footer>
</body>
</html>"""
        return html, "text/html"

    # ------------------------------------------------------------------
    # PDF metadata (client-side PDF trigger)
    # ------------------------------------------------------------------

    @classmethod
    def _to_pdf_metadata(cls, r: ComposedResponse) -> tuple[str, str]:
        meta = {
            "title": "Nexus AI Intelligence Analysis Report",
            "composition_id": r.composition_id,
            "author": "Nexus AI Platform",
            "subject": f"Intelligence report for modules: {', '.join(r.participating_modules)}",
            "keywords": ["nexus", "intelligence", "analysis"] + r.participating_modules,
            "confidence": r.aggregated_confidence.overall if r.aggregated_confidence else 0.0,
            "page_count_estimate": max(2, len(r.detailed_findings) // 4 + 1),
            "sections": [
                "Executive Summary",
                "Detailed Findings",
                "Recommendations",
                "Citations",
                "Conflicts",
                "Metrics",
            ],
            "created_at": datetime.utcnow().isoformat(),
        }
        return json.dumps(meta, indent=2), "application/json"
