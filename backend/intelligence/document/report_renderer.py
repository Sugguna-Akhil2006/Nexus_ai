"""Compiles report nodes and summaries into stylized HTML and Markdown layouts."""

from backend.intelligence.document.models import DocumentKnowledgeReport


class DocumentReportRenderer:
    """Renders structured DocumentKnowledgeReports into readable human-facing layouts."""

    def render_markdown(self, report: DocumentKnowledgeReport) -> str:
        """Converts knowledge report fields into a standard markdown document."""
        md = []
        md.append(f"# Document Intelligence Report: {report.report_id}")
        md.append(f"**Workspace:** {report.workspace_id}  ")
        md.append(f"**Analyzed At:** {report.analyzed_at.isoformat()}  \n")
        
        md.append("## Executive Summary")
        md.append(report.summary.executive)
        md.append("\n## Technical Summary")
        md.append(report.summary.technical)
        md.append("\n## Key Points")
        for p in report.summary.bullet:
            md.append(f"- {p}")

        md.append("\n## Extracted Entities")
        for ent in report.entities:
            md.append(f"- **{ent.name}** ({ent.category}) - Confidence: {ent.confidence:.1%}")

        md.append("\n## Classified Topics")
        for top in report.topics:
            md.append(f"- **{top.name}** (Weight: {top.weight:.2f}) - *{top.description}*")

        md.append("\n## Directed Knowledge Graph Relationships")
        for rel in report.relationships:
            md.append(f"- `{rel.source}` --({rel.relationship_type})--> `{rel.target}` (Conf: {rel.confidence:.1%})")

        md.append("\n## Extracted Knowledge & Claims")
        for obj in report.knowledge_objects:
            md.append(f"### {obj.title} (Confidence: {obj.confidence:.1%})")
            md.append(f"**Claim:** {obj.description}  ")
            md.append(f"**Evidence:** *\"{obj.evidence}\"*")
            md.append("  \n")

        return "\n".join(md)

    def render_html(self, report: DocumentKnowledgeReport) -> str:
        """Compiles knowledge fields into a responsive, premium HTML card layout."""
        html = []
        html.append("<html><head><style>")
        html.append("""
            body { font-family: 'Segoe UI', Roboto, sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 20px; }
            .card { background-color: #1e293b; border-radius: 12px; padding: 24px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); max-width: 900px; margin: auto; }
            h1 { color: #38bdf8; border-bottom: 2px solid #334155; padding-bottom: 8px; }
            h2 { color: #f43f5e; margin-top: 24px; border-bottom: 1px solid #334155; padding-bottom: 6px; }
            .badge { background: #0ea5e9; padding: 3px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
            .metric { color: #10b981; font-weight: bold; }
            ul { line-height: 1.6; }
            pre { background: #0f172a; padding: 12px; border-radius: 6px; overflow-x: auto; border: 1px solid #334155; }
        """)
        html.append("</style></head><body>")
        html.append("<div class='card'>")
        html.append(f"<h1>Document Intelligence Report</h1>")
        html.append(f"<p><strong>Report ID:</strong> <span class='badge'>{report.report_id}</span> | <strong>Workspace:</strong> {report.workspace_id}</p>")
        
        html.append(f"<h2>Executive Summary</h2><p>{report.summary.executive}</p>")
        html.append(f"<h2>Technical Overview</h2><p>{report.summary.technical}</p>")
        
        html.append("<h2>Extracted Entities</h2><ul>")
        for ent in report.entities:
            html.append(f"<li><strong>{ent.name}</strong> <span style='color: #64748b;'>[{ent.category}]</span> - <span class='metric'>{ent.confidence:.1%} confidence</span></li>")
        html.append("</ul>")

        html.append("<h2>Knowledge Graph Summary</h2><ul>")
        for rel in report.relationships:
            html.append(f"<li><code>{rel.source}</code> &rarr; <code>{rel.target}</code> <span class='badge'>{rel.relationship_type}</span> ({rel.confidence:.1%})</li>")
        html.append("</ul>")

        html.append("</div></body></html>")
        return "\n".join(html)
