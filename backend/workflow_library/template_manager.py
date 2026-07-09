"""Template manager coordinating registries, versions, execution, and schedules."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.workflow_library.automation_scheduler import AutomationScheduler
from backend.workflow_library.models import AutomationSchedule, ExecutedTemplateLog, TemplateVersion, WorkflowTemplate
from backend.workflow_library.recommendation_engine import RecommendationEngine
from backend.workflow_library.template_executor import TemplateExecutor
from backend.workflow_library.template_import_export import TemplateImportExport
from backend.workflow_library.template_permissions import TemplatePermissions
from backend.workflow_library.template_registry import TemplateRegistry
from backend.workflow_library.template_versioning import TemplateVersioning


class TemplateManager:
    """The central manager (facade) coordinating workflow library automation."""

    _instance: Optional["TemplateManager"] = None

    def __new__(cls, *args: Any, **kwargs: Any) -> "TemplateManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, db_path: str = "nexus_ai.db") -> None:
        if getattr(self, "_initialized", False):
            return
        self.registry = TemplateRegistry(db_path)
        self.versioning = TemplateVersioning(db_path)
        self.scheduler = AutomationScheduler(db_path)
        self._initialized = True

    # ------------------------------------------------------------------
    # Facade Wrappers
    # ------------------------------------------------------------------

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """Retrieves a template by ID."""
        return self.registry.get_template(template_id)

    def list_templates(self) -> List[WorkflowTemplate]:
        """Lists all templates."""
        return self.registry.list_templates()

    def delete_template(self, template_id: str) -> None:
        """Deletes a template."""
        self.registry.delete_template(template_id)

    def save_template(self, template: WorkflowTemplate, changelog: Optional[str] = None) -> None:
        """Saves a template and logs a version snapshot."""
        self.registry.save_template(template)
        self.versioning.save_version_snapshot(template, changelog)

    def execute_template(self, template_id: str, variables: Optional[dict] = None) -> Optional[ExecutedTemplateLog]:
        """Executes the specified template using system workflow runs."""
        tpl = self.get_template(template_id)
        if tpl:
            return TemplateExecutor.execute(tpl, variables)
        return None

    def schedule_template(self, template_id: str, cron_expression: str) -> AutomationSchedule:
        """Schedules a template automation."""
        return self.scheduler.schedule_template(template_id, cron_expression)

    def list_schedules(self) -> List[AutomationSchedule]:
        """Lists all schedules."""
        return self.scheduler.list_schedules()

    def get_recommendations(self, category: str, files: List[str]) -> List[WorkflowTemplate]:
        """Recommends templates matching workspace traits."""
        return RecommendationEngine.suggest_templates(category, files)
