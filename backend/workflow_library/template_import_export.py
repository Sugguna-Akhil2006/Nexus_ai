"""Template import export converting workflow template models from and to JSON/YAML."""

from __future__ import annotations

import json
from typing import Optional

from backend.workflow_library.models import TemplateScope, WorkflowTemplate


class TemplateImportExport:
    """Converts workflow templates into transport JSON/YAML payloads and back."""

    @staticmethod
    def export_to_json(template: WorkflowTemplate) -> str:
        """Serializes a template into JSON format."""
        return template.model_dump_json(indent=2)

    @staticmethod
    def import_from_json(json_str: str) -> Optional[WorkflowTemplate]:
        """Deserializes a template from JSON format."""
        try:
            data = json.loads(json_str)
            return WorkflowTemplate(
                template_id=data["template_id"],
                name=data["name"],
                description=data.get("description"),
                steps=data.get("steps", []),
                variables=data.get("variables", {}),
                scope=TemplateScope(data.get("scope", "private")),
                version=data.get("version", "1.0.0"),
                author=data.get("author", "System"),
                created_at=data.get("created_at", ""),
            )
        except Exception:
            return None
DefinitionPath = "template_import_export.py"
