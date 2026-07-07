"""Renderer exporting GitHub reports to standard formats including PDF, HTML, and Markdown."""

from backend.intelligence.github.models import GitHubIntelligenceReport


class GitHubReportRenderer:
    """Renders GitHubIntelligenceReport to standardized export structures."""

    def to_json(self, report: GitHubIntelligenceReport) -> str:
        """Returns standard serialized JSON representation."""
        return report.model_dump_json()

    def to_pdf(self, report: GitHubIntelligenceReport) -> bytes:
        """Generates mock PDF stream bytes for the GitHub engineering report."""
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
            f"(GitHub Engineering Report: {report.report_id}) Tj\n"
            "0 -20 Td\n"
            f"(Repository: {report.repository}) Tj\n"
            "0 -20 Td\n"
            f"(Summary: {summary_slice}...) Tj\n"
            "ET\n"
            "endstream\nendobj\nxref\n0 5\n0000000000 65535 f\n"
            "trailer\n<< /Size 5 /Root 1 0 R >>\n"
            "%%EOF"
        )
        return pdf_stream.encode("utf-8")

    def to_html(self, report: GitHubIntelligenceReport) -> str:
        """Generates a premium dark-themed HTML engineering report dashboard."""
        
        # Format lists & dicts to HTML elements
        overview_rows = "".join(
            f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{val}</td></tr>"
            for key, val in report.repository_overview.items()
        )
        
        langs = report.technology_stack.get("languages", [])
        frameworks = report.technology_stack.get("frameworks", [])
        tech_tags = "".join(f"<span class='tag language'>{l}</span>" for l in langs) + \
                    "".join(f"<span class='tag framework'>{f}</span>" for f in frameworks)
                    
        quality_score = report.engineering_quality.get("maintainability_score", 90.0)
        quality_rows = "".join(
            f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{val}</td></tr>"
            for key, val in report.engineering_quality.items() if key != "improvements"
        )
        
        health_score = report.repository_health.get("overall_health_score", 90.0)
        health_rows = "".join(
            f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{val}</td></tr>"
            for key, val in report.repository_health.items() if key not in ["releases", "burst_activities", "inactive_periods", "health_scores"]
        )
        
        doc_rows = "".join(
            f"<tr><td><strong>{key.replace('_', ' ').title()}</strong></td><td>{val}</td></tr>"
            for key, val in report.documentation_quality.items()
        )
        
        strengths_list = "".join(f"<li>{s}</li>" for s in report.strengths)
        risks_list = "".join(f"<li class='risk-item'>{r}</li>" for s in report.engineering_risks)
        roadmap_list = "".join(f"<li>{r}</li>" for r in report.improvement_roadmap)
        
        skills_rows = "".join(
            f"<tr><td><strong>{s.skill_name}</strong></td><td><span class='badge {s.experience_level.lower()}'>{s.experience_level}</span></td><td>{s.evidence_description}</td></tr>"
            for s in report.developer_skill_evidence
        )

        html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>GitHub Engineering Report - {report.report_id}</title>
  <style>
    :root {{
      --bg: #0b0c10;
      --surface: #1f2833;
      --border: #45f3ff;
      --border-dark: #121a24;
      --text: #c5c6c7;
      --text-main: #ffffff;
      --cyan: #45f3ff;
      --purple: #bb86fc;
      --green: #03dac6;
      --red: #cf6679;
      --yellow: #fdd835;
    }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 40px 20px;
    }}
    .container {{
      max-width: 1000px;
      margin: 0 auto;
      background: #151b24;
      border: 1px solid var(--border-dark);
      border-radius: 12px;
      padding: 45px;
      box-shadow: 0 15px 35px rgba(0,0,0,0.6);
    }}
    header {{
      border-bottom: 2px solid var(--border-dark);
      padding-bottom: 25px;
      margin-bottom: 35px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    h1 {{
      margin: 0;
      font-size: 26px;
      color: var(--text-main);
      letter-spacing: 0.5px;
    }}
    .repo-url {{
      font-family: monospace;
      color: var(--cyan);
      font-size: 15px;
      margin-top: 5px;
    }}
    .meta-date {{
      font-size: 12px;
      color: #718096;
    }}
    .scores-container {{
      display: flex;
      gap: 15px;
    }}
    .score-card {{
      background: #1e2633;
      border: 1px solid var(--border-dark);
      border-radius: 8px;
      padding: 10px 15px;
      text-align: center;
    }}
    .score-card .val {{
      font-size: 24px;
      font-weight: 700;
      color: var(--cyan);
    }}
    .score-card.health .val {{
      color: var(--green);
    }}
    .score-card .lbl {{
      font-size: 10px;
      text-transform: uppercase;
      color: #a0aec0;
      margin-top: 4px;
    }}
    h2 {{
      color: var(--text-main);
      font-size: 19px;
      border-left: 3px solid var(--cyan);
      padding-left: 12px;
      margin-top: 35px;
      margin-bottom: 15px;
    }}
    p {{
      line-height: 1.7;
      color: #a0aec0;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 10px;
      background: #11161d;
      border-radius: 6px;
      overflow: hidden;
    }}
    th, td {{
      padding: 12px 15px;
      text-align: left;
      border-bottom: 1px solid #1c232d;
    }}
    th {{
      background: #1a202c;
      color: var(--text-main);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .tags {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .tag {{
      font-size: 11px;
      padding: 3px 9px;
      border-radius: 4px;
      font-weight: 600;
    }}
    .tag.language {{
      background: rgba(69, 243, 255, 0.1);
      border: 1px solid rgba(69, 243, 255, 0.25);
      color: var(--cyan);
    }}
    .tag.framework {{
      background: rgba(187, 134, 252, 0.1);
      border: 1px solid rgba(187, 134, 252, 0.25);
      color: var(--purple);
    }}
    ul {{
      padding-left: 20px;
    }}
    li {{
      margin-bottom: 8px;
      line-height: 1.6;
    }}
    .risk-item {{
      color: #fca5a5;
    }}
    .badge {{
      font-size: 10px;
      padding: 2px 7px;
      border-radius: 10px;
      font-weight: 600;
      text-transform: uppercase;
    }}
    .badge.expert {{
      background: rgba(3, 218, 198, 0.15);
      color: var(--green);
    }}
    .badge.intermediate {{
      background: rgba(69, 243, 255, 0.15);
      color: var(--cyan);
    }}
    .badge.beginner {{
      background: rgba(253, 216, 53, 0.15);
      color: var(--yellow);
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div>
        <h1>GitHub Repository Analysis</h1>
        <div class="repo-url">{report.repository}</div>
        <div class="meta-date">Analyzed on {report.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(report.timestamp, 'strftime') else report.timestamp} | Report ID: {report.report_id}</div>
      </div>
      <div class="scores-container">
        <div class="score-card">
          <div class="val">{quality_score}</div>
          <div class="lbl">Quality</div>
        </div>
        <div class="score-card health">
          <div class="val">{health_score}</div>
          <div class="lbl">Health</div>
        </div>
      </div>
    </header>

    <section>
      <h2>1. Executive Summary</h2>
      <p>{report.executive_summary}</p>
    </section>

    <section>
      <h2>2. Repository Overview</h2>
      <table>
        <tbody>
          {overview_rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>3. Technology Stack</h2>
      <div class="tags">
        {tech_tags}
      </div>
    </section>

    <section>
      <h2>4. Architecture Style</h2>
      <p>{report.architecture_style}</p>
    </section>

    <section>
      <h2>5. Engineering Quality Audit</h2>
      <table>
        <tbody>
          {quality_rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>6. Repository Health & Cadence</h2>
      <table>
        <tbody>
          {health_rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>7. Documentation Quality</h2>
      <table>
        <tbody>
          {doc_rows}
        </tbody>
      </table>
    </section>

    <section>
      <h2>8. Repository Key Strengths</h2>
      <ul>
        {strengths_list or "<li>No specific strengths logged.</li>"}
      </ul>
    </section>

    <section>
      <h2>9. Engineering Risks</h2>
      <ul>
        {risks_list or "<li>No security or maintainability risks identified.</li>"}
      </ul>
    </section>

    <section>
      <h2>10. Improvement Roadmap</h2>
      <ul>
        {roadmap_list or "<li>Repository structure requires no major improvements.</li>"}
      </ul>
    </section>

    <section>
      <h2>11. Developer Skill Evidence</h2>
      <table>
        <thead>
          <tr>
            <th>Skill</th>
            <th>Competency</th>
            <th>Evidence description</th>
          </tr>
        </thead>
        <tbody>
          {skills_rows or "<tr><td colspan='3'>No developer skill evidence recorded.</td></tr>"}
        </tbody>
      </table>
    </section>

    <section>
      <h2>12. Profile Updates</h2>
      <p>Knowledge profiles registered. Version: {report.knowledge_profile_version}</p>
    </section>
  </div>
</body>
</html>
"""
        return html_content

    def to_markdown(self, report: GitHubIntelligenceReport) -> str:
        """Generates a structured Markdown engineering report."""
        overview_md = "\n".join(f"- **{key.replace('_', ' ').title()}**: {val}" for key, val in report.repository_overview.items())
        
        langs = report.technology_stack.get("languages", [])
        frameworks = report.technology_stack.get("frameworks", [])
        techs_md = f"- **Languages**: {', '.join(langs)}\n- **Frameworks**: {', '.join(frameworks)}"
        
        quality_md = "\n".join(f"- **{key.replace('_', ' ').title()}**: {val}" for key, val in report.engineering_quality.items() if key != "improvements")
        health_md = "\n".join(f"- **{key.replace('_', ' ').title()}**: {val}" for key, val in report.repository_health.items() if key not in ["releases", "burst_activities", "inactive_periods", "health_scores"])
        doc_md = "\n".join(f"- **{key.replace('_', ' ').title()}**: {val}" for key, val in report.documentation_quality.items())
        
        strengths_md = "\n".join(f"- {s}" for s in report.strengths)
        risks_md = "\n".join(f"- {r}" for r in report.engineering_risks)
        roadmap_md = "\n".join(f"- {r}" for r in report.improvement_roadmap)
        
        skills_md = "| Skill | Competency | Evidence |\n| :--- | :--- | :--- |\n"
        for s in report.developer_skill_evidence:
            skills_md += f"| {s.skill_name} | {s.experience_level} | {s.evidence_description} |\n"
        if not report.developer_skill_evidence:
            skills_md += "| None | - | - |\n"

        md = f"""# GitHub Repository Engineering Report
**Repository**: {report.repository}
**Report ID**: {report.report_id}
**Analyzed at**: {report.timestamp}

## 1. Executive Summary
{report.executive_summary}

## 2. Repository Overview
{overview_md}

## 3. Technology Stack
{techs_md}

## 4. Architecture Style
{report.architecture_style}

## 5. Engineering Quality Audit
{quality_md}

## 6. Repository Health & Cadence
{health_md}

## 7. Documentation Quality
{doc_md}

## 8. Repository Key Strengths
{strengths_md}

## 9. Engineering Risks
{risks_md}

## 10. Improvement Roadmap
{roadmap_md}

## 11. Developer Skill Evidence
{skills_md}

## 12. Profile Updates
Knowledge profiles registered. Version: {report.knowledge_profile_version}
"""
        return md
