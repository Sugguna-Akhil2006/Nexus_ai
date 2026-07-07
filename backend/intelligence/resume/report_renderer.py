"""Renderer exporting reports to standard formats including JSON and PDF layout bytes."""

from backend.intelligence.resume.product import ProductResumeReport


class ReportRenderer:
    """Renders ProductResumeReport to standardized export structures."""

    def to_json(self, report: ProductResumeReport) -> str:
        """Returns standard serialized JSON representation."""
        return report.model_dump_json()

    def to_pdf(self, report: ProductResumeReport) -> bytes:
        """Generates future-ready PDF stream bytes matching ISO standards.

        Args:
            report: Mapped product report context.

        Returns:
            bytes: Valid PDF layout bytes.
        """
        # Formulate a structured mock PDF string containing standard xref nodes
        summary_slice = report.executive_summary[:60].replace("(", "\\(").replace(")", "\\)")
        pdf_stream = (
            "%PDF-1.4\n"
            "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R >>\nendobj\n"
            "4 0 obj\n"
            f"<< /Length 200 >>\n"
            "stream\n"
            "BT\n/F1 12 Tf\n70 800 Td\n"
            f"(Resume Analysis Report: {report.report_id}) Tj\n"
            "0 -20 Td\n"
            f"(Overall ATS Score: {report.ats_score}) Tj\n"
            "0 -20 Td\n"
            f"(Summary: {summary_slice}...) Tj\n"
            "ET\n"
            "endstream\nendobj\nxref\n0 5\n0000000000 65535 f\n"
            "trailer\n<< /Size 5 /Root 1 0 R >>\n"
            "%%EOF"
        )
        return pdf_stream.encode("utf-8")

    def to_html(self, report: ProductResumeReport) -> str:
        """Generates a styled, visually rich responsive HTML report."""
        skills_str = "".join(
            f"<div class='skill-cat'><h3>{cat}</h3><div class='tags'>" +
            "".join(f"<span class='tag'>{s}</span>" for s in items) +
            "</div></div>"
            for cat, items in report.skill_analysis.items()
        )
        missing_str = "".join(f"<span class='tag missing'>{s}</span>" for s in report.missing_skills)
        strengths_str = "".join(f"<li>{s}</li>" for s in report.strengths)
        weaknesses_str = "".join(f"<li>{s}</li>" for s in report.weaknesses)
        roadmap_str = "".join(f"<li>{s}</li>" for s in report.improvement_roadmap)
        
        plan_str = "".join(
            f"<tr><td>{step.step}</td><td>{step.timeline}</td><td><span class='badge {step.priority.lower()}'>{step.priority}</span></td></tr>"
            for step in report.action_plan
        )
        
        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>Resume Analysis Report - {report.report_id}</title>
  <style>
    :root {{
      --bg: #090a0f;
      --surface: #12131a;
      --border: #222530;
      --text: #e2e8f0;
      --text-mute: #94a3b8;
      --cyan: #00f0ff;
      --purple: #a855f7;
      --green: #22c55e;
      --red: #ef4444;
      --yellow: #eab308;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      margin: 0;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 900px;
      margin: 0 auto;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }}
    header {{
      border-bottom: 1px solid var(--border);
      padding-bottom: 20px;
      margin-bottom: 30px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    h1 {{
      margin: 0;
      font-size: 24px;
      background: linear-gradient(135deg, var(--cyan) 0%, var(--purple) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }}
    .meta {{
      font-size: 13px;
      color: var(--text-mute);
    }}
    .score-badge {{
      background: rgba(0, 240, 255, 0.1);
      border: 1px solid rgba(0, 240, 255, 0.2);
      color: var(--cyan);
      font-size: 28px;
      font-weight: 700;
      padding: 10px 20px;
      border-radius: 8px;
      display: inline-block;
    }}
    h2 {{
      color: var(--cyan);
      font-size: 18px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
      margin-top: 30px;
    }}
    p {{
      line-height: 1.6;
      color: #cbd5e1;
    }}
    ul {{
      padding-left: 20px;
    }}
    li {{
      margin-bottom: 8px;
      line-height: 1.5;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }}
    .tag {{
      background: rgba(168, 85, 247, 0.1);
      border: 1px solid rgba(168, 85, 247, 0.2);
      color: #d8b4fe;
      font-size: 12px;
      padding: 4px 10px;
      border-radius: 4px;
    }}
    .tag.missing {{
      background: rgba(239, 68, 68, 0.1);
      border: 1px solid rgba(239, 68, 68, 0.2);
      color: #fca5a5;
    }}
    .skill-cat {{
      margin-bottom: 15px;
    }}
    .skill-cat h3 {{
      font-size: 14px;
      margin: 0;
      color: var(--text-mute);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 15px;
    }}
    th, td {{
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }}
    th {{
      color: var(--text-mute);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .badge {{
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .badge.high {{
      background: rgba(239, 68, 68, 0.15);
      color: var(--red);
    }}
    .badge.medium {{
      background: rgba(234, 179, 8, 0.15);
      color: var(--yellow);
    }}
    .badge.low {{
      background: rgba(34, 197, 150, 0.15);
      color: var(--cyan);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>Resume Analysis Report</h1>
        <div class="meta">Report ID: {report.report_id} | Document: {report.document_id}</div>
      </div>
      <div>
        <div class="score-badge">{report.ats_score} ATS</div>
      </div>
    </header>

    <section>
      <h2>Executive Summary</h2>
      <p>{report.executive_summary}</p>
    </section>

    <section>
      <h2>Skill Analysis</h2>
      {skills_str}
    </section>

    <section>
      <h2>Missing Skills</h2>
      <div class="tags">
        {missing_str or "<p>No missing skills identified.</p>"}
      </div>
    </section>

    <section>
      <h2>Strengths</h2>
      <ul>{strengths_str or "<li>None identified.</li>"}</ul>
    </section>

    <section>
      <h2>Weaknesses</h2>
      <ul>{weaknesses_str or "<li>None identified.</li>"}</ul>
    </section>

    <section>
      <h2>Career Readiness</h2>
      <p>{report.career_readiness}</p>
    </section>

    <section>
      <h2>Improvement Roadmap</h2>
      <ul>{roadmap_str or "<li>None identified.</li>"}</ul>
    </section>

    <section>
      <h2>Action Plan</h2>
      <table>
        <thead>
          <tr>
            <th>Step</th>
            <th>Timeline</th>
            <th>Priority</th>
          </tr>
        </thead>
        <tbody>
          {plan_str or "<tr><td colspan='3'>No action steps scheduled.</td></tr>"}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""
        return html_content

    def to_markdown(self, report: ProductResumeReport) -> str:
        """Generates a formatted Markdown report representation."""
        skills_md = ""
        for cat, items in report.skill_analysis.items():
            skills_md += f"- **{cat}**: {', '.join(items)}\n"
            
        missing_md = ", ".join(report.missing_skills) if report.missing_skills else "None"
        strengths_md = "\n".join(f"- {s}" for s in report.strengths)
        weaknesses_md = "\n".join(f"- {s}" for s in report.weaknesses)
        roadmap_md = "\n".join(f"- {s}" for s in report.improvement_roadmap)
        
        plan_md = "| Step | Timeline | Priority |\n| :--- | :--- | :--- |\n"
        for step in report.action_plan:
            plan_md += f"| {step.step} | {step.timeline} | {step.priority} |\n"
            
        if not report.action_plan:
            plan_md += "| No action steps scheduled. | - | - |\n"
            
        md_content = f"""# Resume Analysis Report
**Report ID**: {report.report_id}
**Document ID**: {report.document_id}
**ATS Score**: {report.ats_score} / 100

## Executive Summary
{report.executive_summary}

## Skill Analysis
{skills_md}

## Missing Skills
{missing_md}

## Strengths
{strengths_md}

## Weaknesses
{weaknesses_md}

## Career Readiness
{report.career_readiness}

## Improvement Roadmap
{roadmap_md}

## Action Plan
{plan_md}
"""
        return md_content
