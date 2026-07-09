"""Documentation generator compiling developer and architecture handbooks in JSON, Markdown, and HTML formats."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from backend.architecture.models import DecisionRecord, ModuleMetadata


class DocumentationGenerator:
    """Compiles catalogs, ADRs, and diagrams into handbooks."""

    @staticmethod
    def generate_markdown_handbook(
        modules: List[ModuleMetadata],
        decisions: List[DecisionRecord],
        diagram: str,
    ) -> str:
        """Assembles a Markdown format Architecture Handbook."""
        lines = [
            "# Nexus AI Architecture & Developer Handbook\n",
            "## 1. System Components Diagram",
            "```mermaid",
            diagram,
            "```\n",
            "## 2. Intelligence Module Catalog",
        ]

        for m in modules:
            lines.extend([
                f"### Module: {m.name}",
                f"- **Purpose**: {m.purpose}",
                f"- **Owner**: {m.owner}",
                f"- **Dependencies**: {', '.join(m.dependencies)}",
                f"- **Public APIs**: {', '.join(m.public_apis)}",
                f"- **Related Tests**: {', '.join(m.related_tests)}",
                "",
            ])

        lines.append("## 3. Architecture Decision Records (ADRs)")
        for d in decisions:
            lines.extend([
                f"### {d.decision_id}: {d.title}",
                f"- **Date**: {d.date}",
                f"- **Owner**: {d.owner}",
                f"- **Reason**: {d.reason}",
                f"- **Alternatives Evaluated**: {', '.join(d.alternatives)}",
                f"- **Consequences**: {d.consequences}",
                "",
            ])

        return "\n".join(lines)

    @staticmethod
    def generate_html_handbook(markdown_content: str) -> str:
        """Converts Markdown format elements into a basic styled HTML page."""
        # Simple string replace markup formatting for local preview
        html_body = markdown_content.replace("# ", "<h1>").replace("\n", "<br>")
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Nexus AI Developer Handbook</title>
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; margin: 40px; color: #333; }}
        h1 {{ color: #007bff; }}
        h2 {{ color: #28a745; margin-top: 30px; }}
        h3 {{ color: #17a2b8; }}
        code {{ background: #f4f4f4; padding: 2px 5px; }}
    </style>
</head>
<body>
    {html_body}
</body>
</html>
"""

    @staticmethod
    def generate_json_handbook(
        modules: List[ModuleMetadata],
        decisions: List[DecisionRecord],
    ) -> str:
        """Formats details into JSON."""
        data = {
            "version": "1.0",
            "modules": [m.model_dump() for m in modules],
            "decisions": [d.model_dump() for d in decisions],
        }
        return json.dumps(data, indent=2)
DefinitionPath = "documentation_generator.py"
