"""Exports ExecutionTrace objects to JSON, Markdown, and HTML formats."""

import json
from backend.observability.models import ExecutionTrace, ExportFormat


class ExportService:
    """Converts finalized execution traces into various output formats."""

    def export(self, trace: ExecutionTrace, fmt: ExportFormat) -> str:
        """Dispatches export to the appropriate format handler.

        Args:
            trace: The ``ExecutionTrace`` to export.
            fmt: The desired ``ExportFormat``.

        Returns:
            A string containing the serialized trace in the chosen format.

        Raises:
            ValueError: If an unsupported format is provided.
        """
        if fmt == ExportFormat.JSON:
            return self.export_json(trace)
        elif fmt == ExportFormat.MARKDOWN:
            return self.export_markdown(trace)
        elif fmt == ExportFormat.HTML:
            return self.export_html(trace)
        raise ValueError(f"Unsupported export format: {fmt}")

    # ------------------------------------------------------------------
    # Format handlers
    # ------------------------------------------------------------------

    def export_json(self, trace: ExecutionTrace) -> str:
        """Serializes the trace to a pretty-printed JSON string."""
        return json.dumps(trace.model_dump(), indent=2, default=str)

    def export_markdown(self, trace: ExecutionTrace) -> str:
        """Renders the trace as a structured Markdown document."""
        lines = [
            f"# Execution Trace: `{trace.execution_id}`",
            "",
            f"**Trace ID:** {trace.trace_id}  ",
            f"**Workflow:** {trace.workflow_id or '—'}  ",
            f"**Workspace:** {trace.workspace_id or '—'}  ",
            f"**Status:** {trace.status.value}  ",
            f"**Duration:** {trace.total_duration_ms} ms  ",
            f"**Started:** {trace.started_at}  ",
            f"**Ended:** {trace.ended_at}  ",
            "",
            "## Modules Executed",
            "",
        ]
        for mod in trace.modules_executed:
            lines.append(f"- {mod}")

        lines += ["", "## Spans", ""]
        for span in trace.spans:
            status_icon = "✅" if span.status.value == "COMPLETED" else "❌"
            lines.append(
                f"- {status_icon} **{span.name}** ({span.module}) — "
                f"{span.duration_ms} ms"
            )
            if span.error:
                lines.append(f"  - ⚠ Error: {span.error}")

        if trace.reasoning_steps:
            lines += ["", "## Reasoning Steps", ""]
            for step in trace.reasoning_steps:
                lines.append(f"- [{step.confidence:.0%}] {step.description}")

        if trace.memory_accesses:
            lines += ["", "## Memory Accesses", ""]
            for acc in trace.memory_accesses:
                lines.append(f"- `{acc.operation.upper()}` {acc.namespace}/{acc.key}")

        return "\n".join(lines)

    def export_html(self, trace: ExecutionTrace) -> str:
        """Renders the trace as a self-contained HTML page."""
        span_rows = ""
        for span in trace.spans:
            status_class = "ok" if span.status.value == "COMPLETED" else "err"
            error_cell = f"<td class='err'>{span.error}</td>" if span.error else "<td>—</td>"
            span_rows += (
                f"<tr class='{status_class}'>"
                f"<td>{span.name}</td><td>{span.module}</td>"
                f"<td>{span.status.value}</td><td>{span.duration_ms} ms</td>"
                f"{error_cell}</tr>"
            )

        modules_html = "".join(f"<li>{m}</li>" for m in trace.modules_executed)
        reasoning_html = "".join(
            f"<li><b>{s.confidence:.0%}</b> — {s.description}</li>"
            for s in trace.reasoning_steps
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Execution Trace {trace.execution_id}</title>
<style>
  body {{ font-family: monospace; background:#0f0f0f; color:#e0e0e0; padding:2rem; }}
  h1 {{ color:#7dd3fc; }} h2 {{ color:#a5f3fc; border-bottom:1px solid #333; }}
  table {{ border-collapse:collapse; width:100%; margin-bottom:1.5rem; }}
  th {{ background:#1e293b; color:#94a3b8; text-align:left; padding:6px 10px; }}
  td {{ padding:6px 10px; border-bottom:1px solid #1e293b; }}
  tr.ok {{ color:#86efac; }} tr.err {{ color:#fca5a5; }}
  .meta span {{ margin-right:1.5rem; color:#64748b; }}
  .meta b {{ color:#e2e8f0; }}
  ul {{ list-style:disc; padding-left:1.5rem; }}
</style>
</head>
<body>
<h1>🔍 Execution Trace</h1>
<div class="meta">
  <span>ID: <b>{trace.execution_id}</b></span>
  <span>Status: <b>{trace.status.value}</b></span>
  <span>Duration: <b>{trace.total_duration_ms} ms</b></span>
  <span>Workflow: <b>{trace.workflow_id or '—'}</b></span>
</div>
<h2>Modules Executed</h2>
<ul>{modules_html}</ul>
<h2>Spans</h2>
<table>
  <thead><tr><th>Name</th><th>Module</th><th>Status</th><th>Duration</th><th>Error</th></tr></thead>
  <tbody>{span_rows}</tbody>
</table>
<h2>Reasoning Steps</h2>
<ul>{reasoning_html if reasoning_html else '<li>None</li>'}</ul>
</body>
</html>"""
