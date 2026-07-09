"""FastAPI APIRouter routing workflow library CRUDs, imports, exports, and schedulers."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from backend.product.serialization import ProductResponse
from backend.workflow_library.models import TemplateScope, WorkflowTemplate
from backend.workflow_library.template_import_export import TemplateImportExport
from backend.workflow_library.template_manager import TemplateManager

router = APIRouter(prefix="/workflow-library", tags=["Workflow Templates"])

# Singleton manager
_manager = TemplateManager()


class SaveTemplatePayload(BaseModel):
    """Payload to save or update a template."""

    template_id: str
    name: str
    description: Optional[str] = None
    steps: List[str] = []
    variables: Dict[str, Any] = {}
    scope: TemplateScope = TemplateScope.PRIVATE
    version: str = "1.0.0"
    author: str = "System"
    changelog: Optional[str] = None


class ScheduleTemplatePayload(BaseModel):
    """Payload to schedule a template."""

    template_id: str
    cron_expression: str


class ExecuteTemplatePayload(BaseModel):
    """Payload to execute a template."""

    variables: Optional[Dict[str, Any]] = None


class ImportTemplatePayload(BaseModel):
    """Payload to import a template from JSON string."""

    json_str: str


@router.post("/templates", summary="Create or edit a workflow template")
def save_template(payload: SaveTemplatePayload) -> Any:
    """Saves a workflow template and commits a version snapshot record."""
    tpl = WorkflowTemplate(
        template_id=payload.template_id,
        name=payload.name,
        description=payload.description,
        steps=payload.steps,
        variables=payload.variables,
        scope=payload.scope,
        version=payload.version,
        author=payload.author,
        created_at="2026-07-07T12:00:00Z",  # static seed
    )
    _manager.save_template(tpl, payload.changelog)
    return ProductResponse.ok(data=tpl)


@router.get("/templates", summary="List stored workflow templates")
def list_templates() -> ProductResponse[List[Any]]:
    """Lists all active and seeded workflow templates."""
    templates = _manager.list_templates()
    return ProductResponse.ok(data=templates)


@router.post("/templates/{template_id}/execute", summary="Execute workflow template")
def execute_template(template_id: str, payload: ExecuteTemplatePayload) -> Any:
    """Triggers manual execution of the specified workflow template."""
    log = _manager.execute_template(template_id, payload.variables)
    if not log:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    return ProductResponse.ok(data=log)


@router.post("/templates/import", summary="Import a template from JSON")
def import_template(payload: ImportTemplatePayload) -> Any:
    """Imports a template configuration from raw JSON strings."""
    tpl = TemplateImportExport.import_from_json(payload.json_str)
    if not tpl:
        raise HTTPException(status_code=400, detail="Invalid template JSON payload structure.")
    _manager.save_template(tpl, "Imported from JSON payload")
    return ProductResponse.ok(data=tpl)


@router.get("/templates/{template_id}/export", summary="Export a template to JSON")
def export_template(template_id: str) -> Any:
    """Exports a template configuration to JSON string representation."""
    tpl = _manager.get_template(template_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found.")
    json_str = TemplateImportExport.export_to_json(tpl)
    return ProductResponse.ok(data={"json_str": json_str})


@router.post("/schedules", summary="Schedule template automation")
def schedule_template(payload: ScheduleTemplatePayload) -> Any:
    """Registers a cron trigger scheduler event for a template."""
    sched = _manager.schedule_template(payload.template_id, payload.cron_expression)
    return ProductResponse.ok(data=sched)


@router.get("/schedules", summary="List automated schedules")
def list_schedules() -> ProductResponse[List[Any]]:
    """Lists all automated cron scheduler rules registered."""
    schedules = _manager.list_schedules()
    return ProductResponse.ok(data=schedules)
